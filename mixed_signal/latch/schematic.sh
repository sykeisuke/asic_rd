#!/bin/sh
# Prove latch.sch netlists back to latch.spice, and render it on white.
# Run inside the container (run.sh phase `schematic`, or ./container.sh 'sh schematic.sh').
#
#   1. xschem -n -s latch.sch   -> work/latch_sch.spice
#   2. the subcircuit's port list and its one instance line (nodes and cell
#      name) against latch.spice
#   3. xschem under Xvfb           -> assets/latch_xschem.png / .svg
set -u
cd /foss/designs/mixed_signal/latch
RC=/foss/pdks/gf180mcuD/libs.tech/xschem/xschemrc
st=0
mkdir -p work assets
rm -f work/latch.spice work/latch_sch.spice
xschem --rcfile "$RC" -b -q -n -s -o work latch.sch >work/latch_xschem.txt 2>&1
if [ -s work/latch.spice ]; then
    mv work/latch.spice work/latch_sch.spice
    # reduce both to "ports: ..." and "inst: <nodes> <cell>" (instance name and case ignored)
    red() {
        awk 'BEGIN { IGNORECASE = 1 }
             /^\.subckt/ { $1 = ""; $2 = ""; sub(/^ +/, ""); print "ports: " tolower($0) }
             /^\*\*\.subckt/ { $1 = ""; $2 = ""; sub(/^ +/, ""); print "ports: " tolower($0) }
             /^x/ { $1 = ""; sub(/^ +/, ""); print "inst: " tolower($0) }' "$1"
    }
    red latch.spice >work/ref.red
    red work/latch_sch.spice >work/sch.red
    grep '^inst:' work/ref.red >work/ref.inst; grep '^inst:' work/sch.red >work/sch.inst
    grep '^ports:' work/ref.red >work/ref.ports; grep '^ports:' work/sch.red | head -1 >work/sch.ports
    if cmp -s work/ref.inst work/sch.inst; then
        printf "PASS: schematic netlists back: latch.sch has the one instance of latch.spice (%s)\n" "$(cut -c7- work/sch.inst)"
    else
        printf "FAIL: latch.sch instance differs: deck [%s] schematic [%s]\n" "$(cat work/ref.inst)" "$(cat work/sch.inst)"; st=1
    fi
    if cmp -s work/ref.ports work/sch.ports; then
        printf "PASS: schematic ports in order: %s\n" "$(cut -c8- work/sch.ports)"
    else
        printf "REPORT: port order deck [%s] schematic [%s] (the ATOP netlist uses latch.sym's order)\n" "$(cat work/ref.ports)" "$(cat work/sch.ports)"
    fi
else
    printf "FAIL: xschem produced no netlist for latch.sch\n"; st=1
fi
for sch in latch; do
    rm -f "assets/${sch}_xschem.png" "assets/${sch}_xschem.svg"
    timeout 120 xvfb-run -a -s "-screen 0 2400x1400x24" \
        xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
        --command "xschem zoom_full; xschem print png assets/${sch}_xschem.png 2400 1400; xschem print svg assets/${sch}_xschem.svg; xschem exit closewindow force" \
        "$sch.sch" >"work/${sch}_xschem_print.txt" 2>&1
    if [ -s "assets/${sch}_xschem.png" ] && [ -s "assets/${sch}_xschem.svg" ]; then
        printf "PASS: xschem render assets/%s_xschem.svg / .png\n" "$sch"
    else
        printf "FAIL: xschem headless print produced no svg/png for %s.sch\n" "$sch"; st=1
    fi
done
exit $st
