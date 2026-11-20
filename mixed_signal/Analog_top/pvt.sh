#!/bin/sh
# pvt.sh -- the opt-in `pvt` phase of run.sh: the functional record (func.sh's
# bench, measures, reducer and checker, unchanged) at PVT cells.
#
#   sh pvt.sh                              inside the container, cwd = mixed_signal/Analog_top
#   (from the host: ./scripts/sim.sh analog-top-pvt [PVT_CELLS='ss_85_3.0 ...'] [JOBS=6])
#
# A cell is corner_temp_vdd (corner typical/ss/ff/sf/fs, C, V). Default: the
# 45 cells 5 corners x 0/27/85 C x 3.0/3.3/3.6 V. Resistor and MIM corners
# follow ss / ff (pvt_bench.py); the grid is ratiometric (LSB x VDD/3.3, same
# reason there). Not run by the default phases: the typical record (func) is
# untouched and keeps its own files.
#
# Steps:
#   1. pvt_bench.py: work/pvt/<cell>/ bench files and cache key
#   2. pvt_cell.sh per cell, JOBS in parallel (one ngspice each, ~1 h, T0 60 us
#      + the 13 us ramp; a finished cell with an unchanged key is re-used)
#   3. pvt_reduce.py: data/pvt_cells.csv (one row per cell: check-func.awk's
#      verdicts, codes, transfer, plate, armed margin, sequencer, plates, power),
#      REPORT lines per cell, pvt_* metrics
#   4. check-pvt.awk: one PASS:/FAIL: line per gate over all cells, worst cell named
set -eu

BLOCK=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$BLOCK"
DEFAULT=""
for c in typical ss ff sf fs; do
    for t in 0 27 85; do
        for v in 3.0 3.3 3.6; do DEFAULT="$DEFAULT ${c}_${t}_${v}"; done
    done
done
CELLS=${PVT_CELLS:-$DEFAULT}
P=${JOBS:-6}
mkdir -p work/pvt data
python3 pvt_bench.py $CELLS > work/pvt/keys.txt || { echo 'FAIL: pvt: pvt_bench.py'; exit 1; }
n=$(printf '%s\n' $CELLS | wc -l)
echo "pvt_n_cells = $n"
echo "pvt_jobs = $P"
t_start=$(date +%s)
printf '%s\n' $CELLS | xargs -P "$P" -n 1 sh pvt_cell.sh
t_end=$(date +%s)
echo "pvt_wall_seconds = $((t_end - t_start))"

status=0
python3 pvt_reduce.py $CELLS || { echo 'FAIL: pvt: pvt_reduce.py'; status=1; }
awk -F, -f check-pvt.awk data/pvt_cells.csv || status=1
echo "PVT cells: $BLOCK/data/pvt_cells.csv"
exit "$status"
