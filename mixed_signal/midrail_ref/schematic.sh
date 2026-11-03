#!/bin/sh
# The xschem drawings of midref netlist back to midref.spice, and the
# testbench drawings reproduce the hand-written benches: run inside the
# container by run.sh (phase schematic).
#   1. midref_sch.py draws midref_buf.sch / midref_div.sch (+ .sym) from the netlist
#   2. xschem netlists each drawing headless
#   3. check-schematic.awk compares it with that subcircuit of midref.spice:
#      ports in order, node names (the frozen set), every instance on
#      terminals, model and L / W / nf / m
#   4. the drawings are rendered to assets/ under a virtual X server
#   5. tb_sch.py draws tb_op / tb_kick / tb_cmp / tb_mc / tb_noise .sch (the DUT
#      as midref_div.sym + midref_buf.sym, the comparator of tb_cmp from
#      ../comparator through xschemrc)
#   6. xtb.py netlist: xschem netlists each tb_*.sch; its instances are the bench's
#   7. each tb_*.sch is rendered to assets/<tb>.png
#   8. xtb.py sim: ngspice on each xschem netlist and on the hand bench at the same
#      nominal case; the figures compared (data/xtb.csv)
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

# the testbench drawings: this folder's xschemrc puts the DUT symbols and ../comparator on the path
python3 tb_sch.py || echo "FAIL: tb_sch.py"
python3 xtb.py netlist
trc="$PWD/xschemrc"
for name in tb_op tb_kick tb_cmp tb_mc tb_noise; do
    case $name in
        tb_cmp) size="3600 1500" ;;
        tb_kick) size="3200 1500" ;;
        *) size="2400 1500" ;;
    esac
    rm -f "assets/$name.png"
    # the virtual screen has the print's aspect: zoom_full fits the window, the print keeps the view
    timeout 180 xvfb-run -a -s "-screen 0 $(echo $size | tr ' ' x)x24" xschem --rcfile "$trc" \
        --command "xschem zoom_full; xschem print png assets/$name.png $size; exit" \
        "$name.sch" > "work/${name}_render.txt" 2>&1
    if [ -s "assets/$name.png" ]; then
        printf 'PASS: render %s.sch -> assets/%s.png\n' "$name" "$name"
        printf 'Figure: /foss/designs/mixed_signal/midrail_ref/assets/%s.png\n' "$name"
    else
        printf 'FAIL: %s: xschem headless print produced no png\n' "$name"
    fi
done
python3 xtb.py sim
