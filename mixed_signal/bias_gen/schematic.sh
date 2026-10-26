#!/bin/sh
# The xschem drawing of bias_gen netlists back to bias_gen.spice: run inside
# the container by run.sh (phase schematic).
#   1. bias_gen_sch.py draws bias_gen.sch (+ .sym) from the netlist
#   2. xschem netlists the drawing headless
#   3. check-schematic.awk compares it with the subcircuit of bias_gen.spice:
#      ports in order, node names (the frozen set), every instance on
#      terminals, model and every parameter (L / W / nf / m and the S/D geometry)
#   4. the drawing is rendered to assets/ under a virtual X server
set -u
cd "$(dirname -- "$0")"
mkdir -p work assets
python3 bias_gen_sch.py || { echo "FAIL: bias_gen_sch.py"; exit 1; }
rc="$PDK_ROOT/gf180mcuD/libs.tech/xschem/xschemrc"
name=bias_gen
awk -v n="$name" '$1 == ".subckt" && $2 == n {on = 1} on {print} on && $1 ~ /^\.ends/ {exit}' \
    bias_gen.spice > "work/ref_$name.spice"
# the frozen node set: every node the subcircuit uses (ports + internals)
nodes=$(awk 'NR == 1 {for (i = 3; i <= NF; i++) print $i; next}
             $1 !~ /^[.*]/ {n = 0; for (i = 2; i <= NF; i++) {if ($i ~ /=/) break; a[++n] = $i}
                          for (i = 1; i < n; i++) print a[i]}' "work/ref_$name.spice" | grep . | sort -u | tr '\n' ' ' | sed 's/ *$//')
rm -f "work/$name.spice"
xschem --rcfile "$rc" -b -q -n -s -o work "$name.sch" > "work/${name}_xschem.txt" 2>&1
if [ -s "work/$name.spice" ]; then
    awk -v ref="bias_gen.spice" -v nodes="$nodes" -f check-schematic.awk \
        "work/ref_$name.spice" "work/$name.spice" | sed "s/^\(PASS\|FAIL\): /\1: schematic: /"
else
    printf 'FAIL: schematic: xschem produced no netlist\n'
fi
rm -f "assets/$name.png"
timeout 180 xvfb-run -a -s "-screen 0 2400x1400x24" xschem --rcfile "$rc" \
    --command "xschem zoom_full; xschem print png assets/$name.png 2800 1600; exit" \
    "$name.sch" > "work/${name}_render.txt" 2>&1
[ -s "assets/$name.png" ] && printf 'Figure: /foss/designs/mixed_signal/bias_gen/assets/%s.png\n' "$name"
exit 0
