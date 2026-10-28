#!/bin/sh
# vrlo_ref: the VR_LO supplier of ramp_simple's reset switch, a shunt regulator
# (PMOS-input OTA, NMOS shunt, keep-alive source, decap) on a 5/33 AVDD tap,
# replacing the ideal 0.5 V VVRLO of the Analog_top benches (README.md).
# Ideal bias current.
#
#   ./run.sh                          phases verify schematic macro (~15 min)
#   PHASES='size verify schematic macro' ./run.sh
#                                     also re-run the search (~15 min) and fail
#                                     if vrlo_ref.spice differs from what it selects
#
# Phases:
#   size       size_vrlo.py stage A (typical + ss/85/3.0) + stage B (PVT
#              extremes, bias / ramp-current spans); the selected netlist must
#              equal vrlo_ref.spice
#   verify     verify_vrlo.py: op, tran, loop at 45 PVT cells + spans; the real
#              13.8 us ramp at three cells; noise; Monte Carlo
#   schematic  the xschem drawing netlists back to vrlo_ref.spice
#   macro      macro/macro.py: in analog_top against the ideal source, one
#              record (Analog_top's own bench) and two records (reset dump)
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-vrlo-ref}
PHASES=${PHASES:-'verify schematic macro'}
JOBS=${JOBS:-12}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)        # scripts/sim.sh records the run
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"
# the schematic phase (re)writes vrlo_ref.sch/.sym here as the container user
chmod a+rwX "$BLOCK_DIR"; chmod a+rw "$BLOCK_DIR"/*.sch "$BLOCK_DIR"/*.sym 2>/dev/null || true

status=0
sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has size; then
        JOBS=$JOBS python3 -u size_vrlo.py || echo 'FAIL: size_vrlo.py'
        if cmp -s work/vrlo_ref.spice vrlo_ref.spice; then
            echo 'PASS: size: vrlo_ref.spice is what the recorded search selects'
        else
            echo 'FAIL: size: vrlo_ref.spice differs from work/vrlo_ref.spice'
        fi
    fi
    # verify_vrlo.py / macro.py print a FAIL: line per failed gate and per phase that
    # raises; a missing final count means the script itself died
    if has verify; then JOBS=$JOBS python3 -u verify_vrlo.py > work/verify.out 2>&1 || true; cat work/verify.out
        grep -q '^verify_fail_count' work/verify.out || echo 'FAIL: verify_vrlo.py did not complete'; fi
    if has schematic; then sh schematic.sh || echo 'FAIL: schematic.sh'; fi
    if has macro; then python3 -u macro/macro.py > work/macro.out 2>&1 || true; cat work/macro.out
        grep -q '^macro_fail_count' work/macro.out || echo 'FAIL: macro/macro.py did not complete'; fi
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "Netlist: $BLOCK_DIR/vrlo_ref.spice"
    printf '%s\n' "Sizing: $BLOCK_DIR/data/sizing.json"
    printf '%s\n' "Stage A: $BLOCK_DIR/data/stage_a.csv"
    printf '%s\n' "Stage B: $BLOCK_DIR/data/stage_b.json"
    printf '%s\n' "Macro: $BLOCK_DIR/data/macro.json"
    printf '%s\n' "Report: $BLOCK_DIR/README.md"
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
exit "$status"
