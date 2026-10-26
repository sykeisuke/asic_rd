#!/bin/sh
# xtb.sh -- the `xtb` phase of run.sh: the xschem testbench reproduces the hand
# bench. Inside the container, cwd = mixed_signal/Analog_top.
#   1. xschem netlists tb_analog_top.sch (hierarchically: analog_top.sch,
#      atop_cell.sch and every block's drawing, the hierarchy schematic.sh
#      writes into analog_top.spice) into work/xtb/
#   2. ngspice -b runs it there (.spiceinit: one thread); tb_measure.inc is
#      included by absolute path, so the measures are the hand bench's
#   3. every measure echo -> data/xtb_measures.txt
#   4. check-xtb.awk against data/func_measures.txt (written by func.sh from
#      tb_analog_top.spice): codes identical, times <= 1 ns, voltages <= 0.5 mV,
#      ... (limits in check-xtb.awk)
# The func result must be newer than the hand bench's sources (the bench, its
# includes and the generated analog_top.spice), or the
# comparison is against a different bench (FAIL: stale).
set -u
cd "$(dirname -- "$0")"
W=work/xtb
FUNC=${FUNC_MEAS:-data/func_measures.txt}
rm -rf "$W"
mkdir -p "$W" data
printf 'set num_threads=1\n' > "$W/.spiceinit"
rm -f data/xtb_measures.txt

xschem --rcfile xschemrc -b -q -n -s -o "$W" tb_analog_top.sch > "$W/xschem.txt" 2>&1
if [ ! -s "$W/tb_analog_top.spice" ]; then
    echo "FAIL: xtb: xschem produced no netlist for tb_analog_top.sch"; exit 1
fi
echo "Netlist: /foss/designs/mixed_signal/Analog_top/$W/tb_analog_top.spice"

t0=$(date +%s)
st=0
( cd "$W" && ngspice -b tb_analog_top.spice > ngspice.out 2>&1 ) || st=$?
echo "xtb_sim_seconds = $(( $(date +%s) - t0 ))"
[ "$st" = 0 ] || echo "FAIL: xtb: ngspice exited with status $st"
awk '/^[a-z_][a-z_0-9]* +=/ { v = $3; sub(/^\+/, "", v); print $1 " = " v }' \
    "$W/ngspice.out" > data/xtb_measures.txt
echo "xtb_n_measures = $(wc -l < data/xtb_measures.txt)"
echo "Measures: /foss/designs/mixed_signal/Analog_top/data/xtb_measures.txt"

if [ ! -s "$FUNC" ]; then
    echo "FAIL: xtb: no hand-bench measures $FUNC (run the func phase first)"; exit 1
fi
for f in tb_analog_top.spice tb_params.inc tb_measure.inc analog_top.spice; do
    if [ "$f" -nt "$FUNC" ]; then
        echo "FAIL: xtb: $FUNC is older than $f: re-run the func phase"; exit 1
    fi
done
awk -f check-xtb.awk "$FUNC" data/xtb_measures.txt
exit 0
