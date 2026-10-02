#!/bin/sh
# Build both unit-cell floorplans, sign them off and draw them.
#
#   ./run.sh                 # UC_MIM + UC_MOM at FS_MHZ=200, BITS=8
#   FS_MHZ=100 ./run.sh      # switch re-derived at another sampling rate
#
# Everything EDA runs in the container through container.sh; the SVG drawing
# is stdlib Python and runs on the host.  Console is reduced to PASS/FAIL by
# check-floorplan.awk; the full `name = value` list is work/floorplan.txt.
set -eu
BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$BLOCK_DIR"
./container.sh "FS_MHZ=${FS_MHZ:-200} BITS=${BITS:-8} python3 floorplan.py $*" \
    | grep -v '^\[INFO\]' | tee work/floorplan.txt
./container.sh "python3 draw_floorplan.py" | grep -v "^\[INFO\]" | tee -a work/floorplan.txt
./container.sh "python3 report.py" | grep -v "^\[INFO\]" | tee -a work/floorplan.txt
awk -f check-floorplan.awk work/floorplan.txt
