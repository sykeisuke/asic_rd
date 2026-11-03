#!/bin/sh
# ramp_simple: the shared ramp of the 8-bit bottom-plate ADC, re-derived as
# the simple current-source ramp (SPEC.md, DESIGN_RECIPE.md): sizing,
# schematic netlist-back, the ramp alone on the real bias generator and
# VR_LO reference, the trim, PVT, mismatch, the noise kernel, four cells
# converting on it.
#
#   ./run.sh                               every phase
#   PHASES='size check' ./run.sh           a subset of: size schematic ramp pvt adc4 src plot check
#   JOBS=8 ./run.sh                        fewer parallel ngspice runs
#
# Writes runs/ramp-simple/<stamp>/metrics.json and links `latest`, unless
# NO_RECORD=1 (scripts/sim.sh records the run; scripts/run-ramp-simple.sh).
# The phases themselves are phases.sh (inside the container).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-ramp-simple}
PHASES=${PHASES:-'size schematic ramp pvt adc4 src plot check'}
JOBS=${JOBS:-16}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi

status=0
PHASES="$PHASES" JOBS="$JOBS" sh "$BLOCK_DIR/container.sh" 'bash phases.sh' >"$run_dir/console.log" 2>&1 || status=$?
if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi

{
    printf '%s\n' "Netlist: $BLOCK_DIR/ramp_simple.spice"
    printf '%s\n' "Sizing: $BLOCK_DIR/data/sizing.json"
    for f in "$BLOCK_DIR"/assets/*.png; do [ -e "$f" ] && printf '%s\n' "Figure: $f"; done
} >"$run_dir/extra-metrics.txt"

if [ "${NO_RECORD:-0}" = 1 ]; then
    cat "$run_dir/console.log" "$run_dir/extra-metrics.txt"
    rm -rf "$run_dir"
    exit "$status"
fi

awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="typical_27c" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
mkdir -p "$PROJECT_ROOT/runs/$TARGET"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
printf '%s\n' "Console: $run_dir/console.log"
exit "$status"
