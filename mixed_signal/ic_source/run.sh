#!/bin/sh
# ic_source: the I/C (switched-capacitor) current source that sets the ramp's
# slope as a unit-capacitor ratio (SPEC.md, DESIGN_RECIPE.md): sizing,
# schematic, the typical cell (current, headroom, output resistance, duty,
# supply, MIM corners), loop phase margin, noise through the ramp's kernel,
# 45 PVT cells, mismatch Monte Carlo.
#
#   ./run.sh                               phases size schematic op loop noise pvt mc plot check
#   PHASES='size op check' ./run.sh        a subset of: lut size schematic op loop noise pvt mc plot check
#   NMC=200 ./run.sh                       Monte Carlo draws (default 100)
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-ic-source}
PHASES=${PHASES:-'size schematic op loop noise pvt mc plot check'}
JOBS=${JOBS:-16}
NMC=${NMC:-100}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR" 2>/dev/null || true

status=0
PHASES="$PHASES" JOBS="$JOBS" NMC="$NMC" sh "$BLOCK_DIR/container.sh" 'bash phases.sh' >"$run_dir/console.log" 2>&1 || status=$?
if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi

{
    printf '%s\n' "Netlist: $BLOCK_DIR/ic_source.spice"
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
