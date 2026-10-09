#!/bin/sh
# Generate analog cell layout with cicpy: GDS, a KLayout render of that
# GDS, and cicpy's SVG view.
#
#   ./scripts/run-layout.sh [CELL ...]
#
# With no argument every netlist in mixed_signal/analog_layout/spice/ is
# built. Signoff is separate: run-drc.sh and run-lvs.sh.
#
# Needs the cicpy add-on: run `make tools` once per checkout.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

block="$PROJECT_ROOT/mixed_signal/analog_layout"
final="$block/physical/final_views"
#- the container runs as uid 1000 and these are created on the host as
#- root; the build writes into all of them
for d in "$block/work" "$final/gds" "$final/render" "$final/svg"; do
    mkdir -p "$d"
    chmod 777 "$d"
done

if [ ! -x "$EDA_TOOLS_DIR/bin/cicpy" ]; then
    printf '%s\n' 'cicpy is not installed. Run: make tools' >&2
    exit 1
fi

status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -e PYTHONUSERBASE=/foss/designs/.eda-tools \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        export PATH=$PYTHONUSERBASE/bin:$PATH
        cd /foss/designs/mixed_signal/analog_layout
        python3 layout.py "$@" | tee work/layout.txt
        awk -f check-layout.awk work/layout.txt
    ' -- "$@" || status=$?

printf '%s\n' "Results: $block/work/layout.txt"
#- only what this run built, so `make layout CELL=INV` does not report
#- a CMP artifact it never touched
built=$*
if [ -z "$built" ]; then
    built=$(ls "$block/spice"/*.spice 2>/dev/null |
            sed 's#.*/##; s/\.spice$//')
fi
for cell in $built; do
    for f in "$final/gds/$cell.gds" "$final/render/$cell.png" \
             "$final/svg/$cell.svg"; do
        [ -f "$f" ] && printf '%s\n' "Layout: $f"
    done
done

exit "$status"
