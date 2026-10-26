#!/bin/sh
# Transistor-level xschem views of the unit-cell switches netlist back to
# their deck: run inside the container, cwd = this block.
#
#   ./container.sh 'sh sw_schematic.sh'
#
#   1. sw_sch.py draws sw_s0/1/2.sch and .sym from ref/switches.spice
#   2. xschem netlists each sw_sN.sch headless (work/sw/); its subcircuit is
#      compared with the deck's (check-sw.awk: name, ports in order, every
#      device on terminals, model and every parameter incl. ad/as/pd/ps;
#      a parameter on one side only fails)
#   3. checker self-test: the first netlist with one width changed must be
#      rejected (REPORT line; a FAIL line if the checker accepts it)
#   4. each drawing is rendered to assets/sw_sN.png under a virtual X server
# One PASS:/FAIL: line per switch. On success data/sw_schematic.done holds
# the date.
set -u
cd "$(dirname -- "$0")"
mkdir -p work/sw assets data
RC=xschemrc
DECK=ref/switches.spice
SWS="sw_s0 sw_s1 sw_s2"
rm -f data/sw_schematic.done
ok=1

python3 sw_sch.py || { echo "FAIL: schematic: sw_sch.py"; exit 1; }

# one subcircuit (header through .ends, commented xschem header accepted)
getsub() {
    awk -v n="$1" '{ l = $0; sub(/^\*+/, "", l); split(tolower(l), t, /[ \t]+/) }
        !on && t[1] == ".subckt" && t[2] == tolower(n) { on = 1 }
        on { print }
        on && t[1] ~ /^\.ends/ { exit }' "$2"
}

for n in $SWS; do
    rm -f "work/sw/$n.spice"
    xschem --rcfile "$RC" -b -q -n -s -o work/sw "$n.sch" > "work/sw/${n}_xschem.txt" 2>&1
    if [ ! -s "work/sw/$n.spice" ]; then
        echo "FAIL: schematic: $n: xschem produced no netlist for $n.sch"; ok=0; continue
    fi
    getsub "$n" "$DECK" > "work/sw/ref_$n.spice"
    getsub "$n" "work/sw/$n.spice" > "work/sw/cut_$n.spice"
    awk -v label="$n.sch vs switches.spice" -f check-sw.awk \
        "work/sw/ref_$n.spice" "work/sw/cut_$n.spice" || ok=0
done

# checker self-test on a mutated copy (first W= of sw_s0 + 0.01 um)
if [ -s work/sw/cut_sw_s0.spice ]; then
    awk '!done && match($0, /W=[0-9.]+u/) {
            w = substr($0, RSTART + 2, RLENGTH - 3)
            $0 = substr($0, 1, RSTART - 1) "W=" sprintf("%.2f", w + 0.01) "u" substr($0, RSTART + RLENGTH)
            done = 1 }
        { print }' work/sw/cut_sw_s0.spice > work/sw/mut_sw_s0.spice
    if awk -v label="mutated sw_s0" -f check-sw.awk work/sw/ref_sw_s0.spice work/sw/mut_sw_s0.spice > work/sw/mut_check.txt; then
        echo "FAIL: schematic: check-sw.awk accepted sw_s0 with one width changed"; ok=0
    else
        echo "REPORT: schematic: checker self-test: sw_s0 with one width +0.01 um rejected ($(grep -c '^REPORT' work/sw/mut_check.txt) mismatch line(s))"
    fi
fi

for n in $SWS; do
    rm -f "assets/$n.png"
    timeout 180 xvfb-run -a -s "-screen 0 1600x1000x24" xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
        --command "xschem zoom_full; xschem print png assets/$n.png 1600 1000; xschem exit closewindow force" \
        "$n.sch" > "work/sw/${n}_render.txt" 2>&1
    if [ -s "assets/$n.png" ]; then
        printf 'Figure: /foss/designs/mixed_signal/Analog_top/assets/%s.png\n' "$n"
    else
        echo "FAIL: schematic: no render of $n.sch"; ok=0
    fi
done

[ "$ok" = 1 ] && date -u +%Y-%m-%dT%H:%M:%SZ > data/sw_schematic.done
exit 0
