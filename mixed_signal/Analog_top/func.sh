#!/bin/sh
# func.sh -- the `func` phase of run.sh: one functional record of analog_top (v5)
# from a cold supply (power-up, four samples 50 ns apart, the shared ramp,
# four trips), reduced to scalars and judged.
#
#   sh func.sh            inside the container, cwd = mixed_signal/Analog_top
#   (from the host: ./run.sh with PHASES=func, or ./scripts/sim.sh analog-top PHASES=func)
#
# Steps:
#   1. ngspice -b tb_analog_top.spice in work/func/ (.spiceinit: one thread);
#      tb_measure.inc holds the measures and writes work/func/wave.csv
#   2. every measure as `name = value` -> data/func_measures.txt (xtb.sh
#      compares the xschem testbench against this file: keep path and format)
#   3. func_reduce.py: settling, bias currents, ramp slope / gain / INL, q edge
#      counts, latch timing, the transfer fit -> data/func_reduce.txt,
#      data/func_cells.csv, data/func_timeline.csv
#   4. plot_func.py: assets/func_*.png
#   5. check-func.awk: one PASS:/FAIL: line per gate, REPORT: lines
#   6. compare_v4.py: the codes and the key scalars against the v4 record
#      (data/v4_ref/), REPORT lines: v5 has one VDD/2 buffer (vbl = vref)
# Every scalar is echoed to stdout as `name = value` for summarize-metrics.awk.
set -eu

BLOCK=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$BLOCK"
W=work/func
rm -rf "$W"
mkdir -p "$W" data assets
printf 'set num_threads=1\n' > "$W/.spiceinit"
rm -f data/func_measures.txt data/func_reduce.txt data/func_cells.csv data/func_timeline.csv

t_start=$(date +%s)
st=0
( cd "$W" && ngspice -b ../../tb_analog_top.spice > ngspice.out 2>&1 ) || st=$?
t_end=$(date +%s)
echo "func_sim_seconds = $((t_end - t_start))"
[ "$st" = 0 ] || echo "FAIL: func: ngspice exited with status $st"

# measure echoes: `name = value [from= ... to= ...]`
awk '/^[a-z_][a-z_0-9]* +=/ { v = $3; sub(/^\+/, "", v); print $1 " = " v }' \
    "$W/ngspice.out" > data/func_measures.txt
# measures that were not taken, and simulator errors
awk 'tolower($0) ~ /meas/ && tolower($0) ~ /(error|fail)/ { print }' "$W/ngspice.out" \
    | sort -u | head -20 > "$W/measfail.txt"
if [ -s "$W/measfail.txt" ]; then
    m=$(sed -nE 's/.*meas[a-z]* +(tran +)?([a-z_0-9]+).*/\2/Ip' "$W/measfail.txt" | sort -u | tr '\n' ' ')
    echo "REPORT: func: measure(s) not taken, the event never happened: $m"
fi
awk 'tolower($0) ~ /(^| )(error|fatal)|undefined parameter|cannot compute|timestep too small/ \
     && tolower($0) !~ /meas/ { print }' "$W/ngspice.out" | head -3 > "$W/errors.txt"
if [ -s "$W/errors.txt" ]; then sed 's/^/FAIL: func: ngspice: /' "$W/errors.txt"; fi
[ -s data/func_measures.txt ] || echo "FAIL: func: no measures in the ngspice output"
[ -s "$W/wave.csv" ] || echo "FAIL: func: ngspice wrote no wave.csv"
n_meas=$(wc -l < data/func_measures.txt)
echo "func_n_measures = $n_meas"
cat data/func_measures.txt
echo "Measures: $BLOCK/data/func_measures.txt"

status=0
python3 func_reduce.py || { echo "FAIL: func: func_reduce.py"; status=1; }
python3 plot_func.py || echo "FAIL: func: plot_func.py"
awk -f check-func.awk data/func_measures.txt data/func_reduce.txt || status=1
# 6. v5 against the v4 record (reported, not gated)
python3 compare_v4.py || echo 'FAIL: func: compare_v4.py'
exit "$status"
