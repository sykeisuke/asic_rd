#!/bin/sh
# The xschem drawings of midref netlist back to midref.spice: run inside
# the container by run.sh (phase schematic).
#   1. midref_sch.py draws midref_buf.sch / midref_div.sch (+ .sym) from the netlist
#   2. xschem netlists each drawing headless
#   3. check-schematic.awk compares it with that subcircuit of midref.spice:
#      ports in order, node names (the frozen set), every instance on
#      terminals, model and L / W / nf / m
#   4. the drawings are rendered to assets/ under a virtual X server
set -u
cd "$(dirname -- "$0")"
python3 midref_sch.py || { echo "FAIL: midref_sch.py"; exit 1; }
rc="$PDK_ROOT/gf180mcuD/libs.tech/xschem/xschemrc"
for name in midref_buf midref_div; do
    case $name in
        midref_buf) nodes="out vin ib vdd vss pb a b p n" ;;
        midref_div) nodes="vin vdd vss" ;;
    esac
    awk -v n="$name" '$1 == ".subckt" && $2 == n {on = 1} on {print} on && $1 ~ /^\.ends/ {exit}' \
        midref.spice > "work/ref_$name.spice"
    rm -f "work/$name.spice"
    xschem --rcfile "$rc" -b -q -n -s -o work "$name.sch" > "work/${name}_xschem.txt" 2>&1
    if [ -s "work/$name.spice" ]; then
        printf 'REPORT: schematic %s\n' "$name"
        awk -v ref="midref.spice ($name)" -v nodes="$nodes" -f check-schematic.awk \
            "work/ref_$name.spice" "work/$name.spice" | sed "s/^\(PASS\|FAIL\): /\1: $name: /"
    else
        printf 'FAIL: %s: xschem produced no netlist\n' "$name"
    fi
    rm -f "assets/$name.png"
    timeout 180 xvfb-run -a -s "-screen 0 2000x1200x24" xschem --rcfile "$rc" \
        --command "xschem zoom_full; xschem print png assets/$name.png 2400 1500; exit" \
        "$name.sch" > "work/${name}_render.txt" 2>&1
    [ -s "assets/$name.png" ] && printf 'Figure: /foss/designs/mixed_signal/midrail_ref/assets/%s.png\n' "$name"
done
