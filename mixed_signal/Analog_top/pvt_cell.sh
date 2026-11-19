#!/bin/sh
# pvt_cell.sh -- one PVT cell of the `pvt` phase (pvt.sh runs it in parallel).
#
#   sh pvt_cell.sh <cell>     inside the container, cwd = mixed_signal/Analog_top,
#                             after pvt_bench.py wrote work/pvt/<cell>/
#
# 1. ngspice -b tb.spice in work/pvt/<cell>/, unless the cell finished before
#    with the same key (pvt_bench.py: macro + bench files + cell)
# 2. the measures as `name = value` -> func_measures.txt (func.sh's awk)
# 3. func_reduce.py on this folder (FUNC_WORK / FUNC_DATA) -> func_reduce.txt,
#    wave.npz; wave.csv is deleted afterwards (~140 MB per cell)
# 4. check-func.awk, unchanged, on the two files -> check.txt
# Always exits 0: pvt_reduce.py and check-pvt.awk judge the set.
set -u
BLOCK=$(pwd)
cell=$1
d="$BLOCK/work/pvt/$cell"
cd "$d" || exit 0
key=$(cat key)
if [ "$(cat done 2>/dev/null)" != "$key" ] || [ ! -s func_measures.txt ]; then
    rm -f done wave.csv wave.npz func_measures.txt func_reduce.txt func_cells.csv func_timeline.csv check.txt reduce.out
    t0=$(date +%s)
    st=0
    timeout "${PVT_TIMEOUT:-28800}" ngspice -b tb.spice > ngspice.out 2>&1 || st=$?
    t1=$(date +%s)
    printf 'sim_seconds = %s\nsim_status = %s\n' "$((t1 - t0))" "$st" > sim.txt
    awk '/^[a-z_][a-z_0-9]* +=/ { v = $3; sub(/^\+/, "", v); print $1 " = " v }' ngspice.out > func_measures.txt
    awk 'tolower($0) ~ /(^| )(error|fatal)|undefined parameter|cannot compute|timestep too small/ \
         && tolower($0) !~ /meas/ { print }' ngspice.out | head -3 > errors.txt
    if [ -s wave.csv ]; then
        FUNC_WORK="$d" FUNC_DATA="$d" python3 "$BLOCK/func_reduce.py" > reduce.out 2>&1 || echo 'reduce_status = 1' >> sim.txt
        rm -f wave.csv
    fi
    [ "$st" = 0 ] && [ -s func_reduce.txt ] && echo "$key" > done
fi
awk -f "$BLOCK/check-func.awk" func_measures.txt func_reduce.txt > check.txt 2>&1 || true
echo "pvt cell $cell finished"
exit 0
