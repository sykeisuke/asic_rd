#!/bin/sh
# comparator: the 10-device continuous comparator re-sized with every
# L <= 0.36 um for delay from the static trip <= 12.5 ns into 10 fF and
# < 1.2 mV noise at the pins (DESIGN_RECIPE.md). Typical corner, 27 C, 3.3 V,
# ideal bias current.
#
#   ./run.sh                          phases lut verify (~10 min)
#   PHASES='lut size verify' ./run.sh  also re-run the search (~1 h) and fail if
#                                     comparator.spice differs from what it selects
#
# Phases:
#   lut     lut/build.sh: short-L pygmid tables (L 0.28..0.36 um) + device noise
#   size    size_v3.py stage A + stage B with the recorded calibration; the
#           selected netlist must equal comparator.spice
#   verify  verify_v3.py: delay over four levels, fall, noise, Monte Carlo
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-comparator}
PHASES=${PHASES:-'lut verify'}
SIGMA_GATE=${SIGMA_GATE:-}                      # unset: sigma(Vos) reported, not gated (ADR 0015)
N_MC=${N_MC:-200}
JOBS=${JOBS:-12}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"

status=0
"$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has lut; then sh lut/build.sh || echo 'FAIL: lut/build.sh'; fi
    if has size; then
        PHASE=B JOBS=$JOBS python3 -u size_v3.py || echo 'FAIL: size_v3.py'
        if cmp -s work/comparator.spice comparator.spice; then
            echo 'PASS: size: comparator.spice is what the recorded search selects'
        else
            echo 'FAIL: size: comparator.spice differs from work/comparator.spice'
        fi
    fi
    if has verify; then
        SIGMA_GATE=$SIGMA_GATE N_MC=$N_MC JOBS=$JOBS python3 -u verify_v3.py || true
    fi
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "Sizing: $BLOCK_DIR/data/sizing.json"
    printf '%s\n' "Calibration: $BLOCK_DIR/data/calibration.json"
    printf '%s\n' "Front: $BLOCK_DIR/data/stage_a_front.csv"
    printf '%s\n' "Stage B: $BLOCK_DIR/data/stage_b.csv"
    printf '%s\n' "Netlist: $BLOCK_DIR/comparator.spice"
} >"$run_dir/extra-metrics.txt"

if [ "${NO_RECORD:-0}" = 1 ]; then
    cat "$run_dir/console.log"
    rm -rf "$run_dir"
    exit "$status"
fi
awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="${ASIC_RD_CORNER:-typical_27c}" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
printf '%s\n' "Console: $run_dir/console.log"
exit "$status"
