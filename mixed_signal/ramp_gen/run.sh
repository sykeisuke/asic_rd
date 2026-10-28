#!/bin/sh
# The shared single-slope ramp generator of the 8-bit bottom-plate ADC:
# sizing, schematic netlist-back, the ramp alone, loop gain, the noise
# breakdown, and four unit cells converting on it.
#
#   ./run.sh                               every phase (~10 min)
#   PHASES='ramp loop check' ./run.sh      a subset of: size schematic ramp loop noise trannoise adc4 simple compare plot check
#   JOBS=8 ./run.sh                        fewer parallel ngspice runs in adc4
#
# Writes runs/ramp-gen/<stamp>/metrics.json and links `latest`. Called by
# scripts/run-ramp-gen.sh (make ramp-gen) with NO_RECORD=1, which leaves the
# record to scripts/sim.sh. The phases themselves are phases.sh (container).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-ramp-gen}
PHASES=${PHASES:-'size schematic ramp loop noise trannoise adc4 simple compare plot check'}
JOBS=${JOBS:-16}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"; do mkdir -p "$d"; done
chown -R 1000:1000 "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets" 2>/dev/null || true
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"

status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks -e PDK=gf180mcuD -e MPLBACKEND=Agg \
    -e "PHASES=$PHASES" -e "JOBS=$JOBS" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc 'bash /foss/designs/mixed_signal/ramp_gen/phases.sh' \
    >"$run_dir/console.log" 2>&1 || status=$?
if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi

{
    printf '%s\n' "Netlist: $BLOCK_DIR/ramp_gen.spice"
    printf '%s\n' "Schematic: $BLOCK_DIR/ramp_gen.sch"
    printf '%s\n' "Testbench: $BLOCK_DIR/tb_ramp_adc4.sch"
    printf '%s\n' "Noise breakdown: $BLOCK_DIR/data/noise_breakdown.csv"
    printf '%s\n' "Levels: $BLOCK_DIR/data/adc4_levels.csv"
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
