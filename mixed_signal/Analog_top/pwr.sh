#!/bin/sh
# pwr.sh -- the `pwr` phase of run.sh: where the macro's supply current goes,
# branch by branch and phase by phase. Inside the container, cwd =
# mixed_signal/Analog_top.
#   1. pwr_bench.py: work/pwr/tb_pwr.spice = tb_analog_top.spice with
#      tb_measure.inc replaced by the generated tb_pwr.inc (the same transient;
#      saves every AVDD branch, the block ammeters, the supplies, dout)
#   2. ngspice -b in work/pwr/ (.spiceinit: one thread)
#   3. pwr_reduce.py: window averages per branch -> data/pwr_windows.csv,
#      data/pwr_branches.csv, assets/pwr_profile.png; REPORT: lines, PASS:/FAIL:
#      only on the closure checks (ammeters = supply, branches = ammeter)
set -u
cd "$(dirname -- "$0")"
W=work/pwr
rm -rf "$W"
mkdir -p "$W" data assets
printf 'set num_threads=1\n' > "$W/.spiceinit"
python3 pwr_bench.py || { echo "FAIL: pwr: pwr_bench.py"; exit 1; }
t0=$(date +%s)
st=0
( cd "$W" && ngspice -b tb_pwr.spice > ngspice.out 2>&1 ) || st=$?
echo "pwr_sim_seconds = $(( $(date +%s) - t0 ))"
[ "$st" = 0 ] || echo "FAIL: pwr: ngspice exited with status $st"
awk 'tolower($0) ~ /(^| )(error|fatal)|undefined parameter|cannot compute|timestep too small/ { print }' \
    "$W/ngspice.out" | sort -u | head -5 | sed 's/^/FAIL: pwr: ngspice: /'
python3 pwr_reduce.py || echo "FAIL: pwr: pwr_reduce.py"
exit 0
