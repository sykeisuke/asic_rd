#!/bin/sh
# op.sh -- the `op` phase of run.sh: the in-macro operating point of analog_top
# (v5). Inside the container, cwd = mixed_signal/Analog_top.
#   1. op_bench.py: work/op/tb_op.spice = tb_analog_top.spice with tb_measure.inc
#      replaced by the generated tb_op.inc (op_devices.py: devices, resistors,
#      MIMs, the instants trk = TS0 - 10 ns and ramp = TR + 400 ns); a transient
#      to TR + 500 ns
#   2. ngspice -b in work/op/ (.spiceinit: one thread)
#   3. op_reduce.py: Id, gm, gds, gm/Id, Vov, |Vds| - Vdsat, region per device,
#      switch Ron, R = V / I, MIM C -> data/op_point.csv, data/op_rc.csv;
#      REPORT: lines (recorded), PASS:/FAIL: only on its self-consistency checks
#   3b. check_intent.py: every current written on the sheets (intent.py) within
#      5 % of this record (PASS/FAIL)
#   4. analog_top_sch.py rewrites the sheets with the table on analog_top.sch
#      (text only: the netlist is unchanged, schematic.sh would FAIL otherwise),
#      render.sh renders analog_top again
set -u
cd "$(dirname -- "$0")"
W=work/op
rm -rf "$W"
mkdir -p "$W" data
printf 'set num_threads=1\n' > "$W/.spiceinit"
python3 op_bench.py || { echo "FAIL: op: op_bench.py"; exit 1; }
t0=$(date +%s)
st=0
( cd "$W" && ngspice -b tb_op.spice > ngspice.out 2>&1 ) || st=$?
echo "op_sim_seconds = $(( $(date +%s) - t0 ))"
[ "$st" = 0 ] || echo "FAIL: op: ngspice exited with status $st"
awk 'tolower($0) ~ /(^| )(error|fatal)|undefined parameter|cannot compute|timestep too small/ { print }' \
    "$W/ngspice.out" | sort -u | head -5 | sed 's/^/FAIL: op: ngspice: /'
python3 op_reduce.py || echo "FAIL: op: op_reduce.py"
python3 check_intent.py || true          # PASS/FAIL lines: the currents on the sheets vs this record
python3 analog_top_sch.py > /dev/null || echo "FAIL: op: analog_top_sch.py (table)"
SHEETS=analog_top sh render.sh
exit 0
