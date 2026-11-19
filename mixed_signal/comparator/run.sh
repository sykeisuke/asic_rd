#!/bin/sh
# comparator: the sized core comparator_core (10 devices, size.py) plus one more
# output inverter (derive.py), used with the plate on inp and VREF on inn; dout
# falls at the decision. Typical characterization against ADR 0015's gates, with
# the core in its sizing hookup (`base`: plate on inn) through the same benches.
#
#   ./run.sh                              phases derive verify lin bias (~1 h at JOBS=8)
#   PHASES='derive verify' ./run.sh       typical only (~5 min)
#   PHASES='lut size derive verify' ./run.sh   also rebuild the gm/Id tables and
#                                         re-emit the core from the sizing record
#
# Phases:
#   lut     lut/build.sh: short-L pygmid tables (L 0.28..0.36 um) + device noise
#   size    size.py PHASE=SELECT: the core netlist from the recorded search
#           (data/stage_b.csv); comparator_core.spice must equal it. The full
#           search (~1 h) is PHASE=B, see DESIGN_RECIPE.md
#   derive  derive.py --check: comparator(.spice, _d.spice) are what derive.py
#           makes from comparator_core.spice
#   verify  bench.py PHASE=verify: delay over four levels, polarity over the whole
#           conversion, noise, Monte Carlo; base / sw / sw_noinv side by side
#   lin     bench.py PHASE=lin: offset signal-independence (30 samples x 4 levels x
#           typical/27/3.3, ss/85/3.0, ff/85/3.6), sw and base
#   bias    bench.py PHASE=bias: bias multiple for 12.5 ns, sw at all 45 PVT cells (data/bias_req.csv, read by ../bias_gen), base at typical and ss/85
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-comparator}
PHASES=${PHASES:-'derive verify lin bias'}
N_MC=${N_MC:-200}
JOBS=${JOBS:-8}
LIN_SAMPLES=${LIN_SAMPLES:-30}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data"
for p in verify lin bias; do
    case " $PHASES " in *" $p "*) rm -f "$BLOCK_DIR/data/values_$p.txt";; esac
done

status=0
"$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has lut; then sh lut/build.sh || echo 'FAIL: lut/build.sh'; fi
    if has size; then
        cp data/sizing.json work/sizing.json.keep
        PHASE=SELECT python3 -u size.py || echo 'FAIL: size.py'
        if cmp -s work/comparator_core.spice comparator_core.spice; then
            echo 'PASS: size: comparator_core.spice is what the sizing record selects'
        else
            echo 'FAIL: size: comparator_core.spice differs from work/comparator_core.spice'
        fi
        if cmp -s work/sizing.json.keep data/sizing.json; then
            echo 'PASS: size: data/sizing.json unchanged by the re-selection'
        else
            echo 'FAIL: size: data/sizing.json changed by the re-selection'
        fi
    fi
    if has derive; then python3 -u derive.py --check || echo 'FAIL: derive.py --check'; fi
    if has verify; then PHASE=verify N_MC=$N_MC JOBS=$JOBS python3 -u bench.py || echo 'FAIL: bench.py verify'; fi
    if has lin; then PHASE=lin LIN_SAMPLES=$LIN_SAMPLES JOBS=$JOBS python3 -u bench.py || echo 'FAIL: bench.py lin'; fi
    if has bias; then PHASE=bias JOBS=$JOBS python3 -u bench.py || echo 'FAIL: bench.py bias'; fi
" >"$run_dir/console.log" 2>&1 || status=$?

# the gates (check-comparator.awk) on this run's values
vals=""
for p in verify lin bias; do
    case " $PHASES " in *" $p "*) vals="$vals $BLOCK_DIR/data/values_$p.txt"; touch "$BLOCK_DIR/data/values_$p.txt";; esac
done
if [ -n "$vals" ]; then
    # shellcheck disable=SC2086
    awk -v phases="$PHASES" -f "$BLOCK_DIR/check-comparator.awk" $vals >>"$run_dir/console.log" 2>&1 || status=1
fi

if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "Netlist: $BLOCK_DIR/comparator.spice"
    printf '%s\n' "Macro netlist: $BLOCK_DIR/comparator_d.spice"
    for p in verify lin bias; do
        [ -s "$BLOCK_DIR/data/values_$p.txt" ] && printf '%s\n' "Values $p: $BLOCK_DIR/data/values_$p.txt"
    done
    [ -s "$BLOCK_DIR/data/offset_lin.csv" ] && printf '%s\n' "Offset lin: $BLOCK_DIR/data/offset_lin.csv"
    [ -s "$BLOCK_DIR/data/bias_req.csv" ] && printf '%s\n' "Bias requirement: $BLOCK_DIR/data/bias_req.csv"
    true
} >"$run_dir/extra-metrics.txt"

if [ "${NO_RECORD:-0}" = 1 ]; then
    cat "$run_dir/console.log" "$run_dir/extra-metrics.txt"
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
