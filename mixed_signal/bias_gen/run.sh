#!/bin/sh
# bias_gen: the constant-gm (beta-multiplier) bias generator of the 8-bit
# bottom-plate ADC re-sized with every L below 1 um, one finger width for
# both rows, gm/Id + Pelgrom sizing, current outputs to the four comparator,
# the ramp and the two midref_v2 buffers (README.md, DESIGN_RECIPE.md).
#
#   ./run.sh                              phases lut verify floorplan schematic (~25 min)
#   PHASES='lut size verify floorplan schematic' ./run.sh
#                                         also re-run the search (~10 min) and fail
#                                         if bias_gen.spice differs from what it selects
#
# Phases:
#   lut        lut/build.sh: gm/Id tables (L 0.4..0.9 um, finger W 1/2/4 um) and
#              the PDK resistor characterisation
#   size       size_bg.py stage A (tables, Pelgrom) + stage B (ngspice, 135 cells,
#              ramp noise); the selected netlist must equal bias_gen.spice
#   verify     verify_bg.py: 135-cell operating point and the comparator requirement,
#              startup, Monte Carlo, ramp-line noise, comparator delay at 135 cells,
#              four-comparator crosstalk, midref_v2 headroom and S2 kick
#   floorplan  floorplan.py: one PMOS row over one NMOS row, common centroid
#   schematic  the xschem drawing netlists back to bias_gen.spice
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-bias-gen}
PHASES=${PHASES:-'lut verify floorplan schematic'}
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
# the schematic phase (re)writes bias_gen.sch/.sym here as the container user
chmod a+rwX "$BLOCK_DIR"; chmod a+rw "$BLOCK_DIR"/*.sch "$BLOCK_DIR"/*.sym 2>/dev/null || true

status=0
sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has lut; then sh lut/build.sh || echo 'FAIL: lut/build.sh'; fi
    if has size; then
        JOBS=$JOBS python3 -u size_bg.py || echo 'FAIL: size_bg.py'
        if cmp -s work/bias_gen.spice bias_gen.spice; then
            echo 'PASS: size: bias_gen.spice is what the recorded search selects'
        else
            echo 'FAIL: size: bias_gen.spice differs from work/bias_gen.spice'
        fi
    fi
    if has verify; then JOBS=$JOBS python3 -u verify_bg.py || echo 'FAIL: verify_bg.py'; fi
    if has floorplan; then python3 floorplan.py || true; fi
    if has schematic; then sh schematic.sh || echo 'FAIL: schematic.sh'; fi
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "Netlist: $BLOCK_DIR/bias_gen.spice"
    printf '%s\n' "Sizing: $BLOCK_DIR/data/sizing.json"
    printf '%s\n' "Front: $BLOCK_DIR/data/stage_b.csv"
    printf '%s\n' "Floorplan: $BLOCK_DIR/data/rows.txt"
    printf '%s\n' "Figure: $BLOCK_DIR/assets/floorplan.png"
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
