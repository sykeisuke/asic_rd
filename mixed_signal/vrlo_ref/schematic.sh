#!/bin/sh
# The xschem drawing of vrlo_ref netlists back to vrlo_ref.spice: run inside the
# container by run.sh (phase schematic).
#   1. vrlo_ref_sch.py draws vrlo_ref.sch (+ .sym) from the netlist
#   2. xschem netlists the drawing headless
#   3. check-schematic.awk compares it with vrlo_ref.spice: ports in order, node
#      names (the frozen set below), every instance on terminals, model and
#      L / W / nf / m (or r_width / r_length, c_width / c_length)
#   4. the drawing is rendered to assets/ under a virtual X server
set -u
cd "$(dirname -- "$0")"
mkdir -p work assets
python3 vrlo_ref_sch.py || { echo "FAIL: vrlo_ref_sch.py"; exit 1; }
rc="$PDK_ROOT/gf180mcuD/libs.tech/xschem/xschemrc"
name=vrlo_ref
nodes="vrlo ib avdd avss pb ts d1 g tap"
for k in $(seq 1 27) $(seq 29 32); do nodes="$nodes r$k"; done
awk -v n="$name" '$1 == ".subckt" && $2 == n {on = 1} on {print} on && $1 ~ /^\.ends/ {exit}' \
    vrlo_ref.spice > "work/ref_$name.spice"
rm -f "work/$name.spice"
xschem --rcfile "$rc" -b -q -n -s -o work "$name.sch" > "work/${name}_xschem.txt" 2>&1
if [ -s "work/$name.spice" ]; then
    printf 'REPORT: schematic %s\n' "$name"
    awk -v ref="vrlo_ref.spice ($name)" -v nodes="$nodes" -f check-schematic.awk \
        "work/ref_$name.spice" "work/$name.spice" | sed "s/^\(PASS\|FAIL\): /\1: $name: /"
else
    printf 'FAIL: %s: xschem produced no netlist\n' "$name"
fi
rm -f "assets/$name.png"
timeout 180 xvfb-run -a -s "-screen 0 2000x1200x24" xschem --rcfile "$rc" \
    --command "xschem zoom_full; xschem print png assets/$name.png 2600 1500; exit" \
    "$name.sch" > "work/${name}_render.txt" 2>&1
[ -s "assets/$name.png" ] && printf 'Figure: /foss/designs/mixed_signal/vrlo_ref/assets/%s.png\n' "$name"
exit 0
