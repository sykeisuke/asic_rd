#!/bin/sh
# KLayout signoff DRC on a generated cell's GDS.
#
#   ./scripts/run-drc.sh [CELL ...]
#
# Deck: the PDK's own gf180mcu.drc, unmodified. Density rules are run
# separately and reported rather than judged; see signoff.py.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

block="$PROJECT_ROOT/mixed_signal/analog_layout"
mkdir -p "$block/work"
chmod 777 "$block/work"

if [ "$#" -eq 0 ]; then
    set -- $(cd "$block/physical/final_views/gds" 2>/dev/null &&
             ls *.gds 2>/dev/null | sed 's/\.gds$//')
fi
if [ "$#" -eq 0 ]; then
    printf '%s\n' 'No GDS to check. Run: make layout' >&2
    exit 1
fi

status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -e PYTHONUSERBASE=/foss/designs/.eda-tools \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/mixed_signal/analog_layout
        : > work/drc.txt
        for cell in "$@"; do
            python3 signoff.py drc "$cell" | tee -a work/drc.txt
        done
        awk -f check-drc.awk work/drc.txt
    ' -- "$@" || status=$?

printf '%s\n' "Results: $block/work/drc.txt"
for cell in "$@"; do
    r="$block/work/$cell-drc.lyrdb"
    [ -f "$r" ] && printf '%s\n' "Report: $r"
done

exit "$status"
