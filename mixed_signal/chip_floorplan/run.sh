#!/bin/sh
# Chip floorplan: Analog_top as a hard macro and asic_digital_top inside
# the wafer.space 1x0p5 pad ring, digital on top (README.md).
#
#   ./run.sh                       every phase (under a minute)
#   PHASES='plan render check' ./run.sh
#
# Writes runs/chip-floorplan/<stamp>/metrics.json and links `latest`.
# `make chip-floorplan` calls this through scripts/run-chip-floorplan.sh.
# Needs the full library install (make pdk) for the ocd_io pad cells.
#
# Phases:
#   probe   gds_probe.py: digital top outline from its GDS, ocd_io pad and
#           corner sizes, dfxtn_2 size                -> data/gds_probe.json
#   plan    floorplan.py: block areas from the Analog_top netlist, macro
#           packing, chip placement, routes, SVGs     -> data/floorplan.json,
#           data/floorplan.txt, assets/*.svg
#   render  the SVGs to PNG (cairosvg)                -> assets/*.png
#   check   check-floorplan.awk on data/floorplan.txt
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-chip-floorplan}
PHASES=${PHASES:-'probe plan render check'}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/data" "$BLOCK_DIR/assets"

status=0
sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has probe; then python3 gds_probe.py || printf 'FAIL: gds_probe.py aborted\n'; fi
    if has plan; then python3 floorplan.py > data/floorplan.txt || printf 'FAIL: floorplan.py aborted\n'; cat data/floorplan.txt; fi
    if has render; then
        python3 -c 'import cairosvg
for n in (\"chip_floorplan\", \"analog_macro_floorplan\"):
    cairosvg.svg2png(url=\"assets/\" + n + \".svg\", write_to=\"assets/\" + n + \".png\")' || printf 'FAIL: render aborted\n'
    fi
    if has check; then awk -f check-floorplan.awk data/floorplan.txt; fi
    true
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL' "$run_dir/console.log"; then status=1; fi

{
    printf '%s\n' "Floorplan: $BLOCK_DIR/data/floorplan.json"
    printf '%s\n' "Probe: $BLOCK_DIR/data/gds_probe.json"
    printf '%s\n' "Figure: $BLOCK_DIR/assets/chip_floorplan.svg"
    printf '%s\n' "Figure: $BLOCK_DIR/assets/analog_macro_floorplan.svg"
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
