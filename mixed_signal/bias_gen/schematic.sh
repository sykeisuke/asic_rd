#!/bin/sh
# The xschem drawing of bias_gen netlists back to bias_gen.spice: run inside
# the container by run.sh (phase schematic).
#   1. bias_gen_sch.py draws bias_gen.sch (+ .sym) from the netlist
#   2. xschem netlists the drawing headless
#   3. check-schematic.awk compares it with the subcircuit of bias_gen.spice:
#      ports in order, node names (the frozen set), every instance on
#      terminals, model and every parameter (L / W / nf / m and the S/D geometry)
#   4. the drawing is rendered to assets/ under a virtual X server
#   5. tb_sch.py draws the testbenches tb_op/startup/mc/noise/cmp/xtalk.sch (the
#      generator as bias_gen.sym, the comparator as ../comparator/comparator.sym);
#      xschem netlists each with this folder's xschemrc (work/xtb_<tb>/), and
#      tb_sch.py check confirms every drawn instance is in the netlist on its nodes
#   6. each testbench is rendered to assets/tb_<tb>.png
#   7. xtb.py simulates every testbench netlist and the hand deck of the same
#      nominal case and compares their figures (data/xtb.csv)
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

# ---- testbench drawings (steps 5-7)
brc="$(pwd)/xschemrc"
tbs="op startup mc noise cmp xtalk"
python3 tb_sch.py || echo "FAIL: tb_sch.py"
for tb in $tbs; do
    d="work/xtb_$tb"
    mkdir -p "$d"
    rm -f "$d/tb_$tb.spice"
    xschem --rcfile "$brc" -b -q -n -s -o "$d" "tb_$tb.sch" > "$d/xschem.txt" 2>&1
done
python3 tb_sch.py check || echo "FAIL: tb_sch.py check"
for tb in $tbs; do
    rm -f "assets/tb_$tb.png"
    timeout 180 xvfb-run -a -s "-screen 0 2400x1400x24" xschem --rcfile "$brc" \
        --command "xschem zoom_full; xschem print png assets/tb_$tb.png 2800 1600; exit" \
        "tb_$tb.sch" > "work/xtb_$tb/render.txt" 2>&1
    if [ -s "assets/tb_$tb.png" ]; then
        printf 'PASS: render: assets/tb_%s.png\n' "$tb"
        printf 'Figure: /foss/designs/mixed_signal/bias_gen/assets/tb_%s.png\n' "$tb"
    else
        printf 'FAIL: render: xschem produced no png for tb_%s.sch\n' "$tb"
    fi
done
python3 xtb.py || echo "FAIL: xtb.py"
exit 0
