#!/bin/sh
# The xschem drawings of vrlo_ref, generated and proven: run inside the
# container by run.sh (phase schematic).
#   1. vrlo_ref_sch.py draws vrlo_ref.sch (+ .sym) from the netlist
#   2. xschem netlists the drawing headless (this folder's xschemrc: the PDK
#      rc + this folder + ../ramp_gen for the benches' old ramp_simple)
#   3. check-schematic.awk compares it with vrlo_ref.spice: ports in order, node
#      names (the frozen set below), every instance on terminals, model and
#      L / W / nf / m (or r_width / r_length, c_width / c_length)
#   4. the drawing is rendered to assets/ under a virtual X server
#   5. tb_sch.py draws the five testbench sheets tb_op / tb_tran / tb_loop /
#      tb_noise / tb_mc.sch from the filled hand benches (+ vrlo_ref_lb.sym,
#      s1cell.sym, work/dut_lb.spice), each rendered to assets/tb_<name>.png
#   6. xtb.py netlists every sheet, checks it carries its bench (instances,
#      dot cards, .control, subcircuits), simulates sheet and hand bench and
#      compares the figures (data/xtb.csv)
set -u
cd "$(dirname -- "$0")"
mkdir -p work assets data
rc="$(pwd)/xschemrc"

render() {   # render <sheet> [verdict]: assets/<sheet>.png from <sheet>.sch
    rm -f "assets/$1.png"
    timeout 180 xvfb-run -a -s "-screen 0 2000x1200x24" xschem --rcfile "$rc" \
        --command "xschem zoom_full; xschem print png assets/$1.png ${3:-2600} ${4:-1500}; exit" \
        "$1.sch" > "work/$1_render.txt" 2>&1
    if [ -s "assets/$1.png" ]; then
        printf 'Figure: /foss/designs/mixed_signal/vrlo_ref/assets/%s.png\n' "$1"
        [ "${2:-}" = verdict ] && printf 'PASS: render %s.sch -> assets/%s.png\n' "$1" "$1"
    else
        printf 'FAIL: xschem headless print produced no png for %s.sch\n' "$1"
    fi
}

python3 vrlo_ref_sch.py || { echo "FAIL: vrlo_ref_sch.py"; exit 1; }
name=vrlo_ref
nodes="vrlo ib avdd avss pb ts d1 g tap"
# the divider's internal nodes r1..r<N_DIV-1> without r<N_TOP> (the tap), from vr.py
ntop=$(python3 -c "import vr; print(vr.N_TOP)"); ndiv=$(python3 -c "import vr; print(vr.N_DIV)")
for k in $(seq 1 $((ntop - 1))) $(seq $((ntop + 1)) $((ndiv - 1))); do nodes="$nodes r$k"; done
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
render "$name"

# the testbench sheets
python3 tb_sch.py || { echo "FAIL: tb_sch.py"; exit 1; }
for tb in op tran loop noise mc; do render "tb_$tb" verdict 3000 2200; done
python3 xtb.py || echo "FAIL: xtb.py (see its FAIL lines)"
exit 0
