#!/bin/sh
# schematic phase of sample_seq (inside the container): draw the sheets from
# data/sizing.json, netlist sample_seq.sch with xschem, compare it with the
# deck (check_sch.py), render the sheets to assets/*.png.
set -u
cd /foss/designs/mixed_signal/sample_seq
RC=/foss/designs/mixed_signal/sample_seq/xschemrc
python3 sample_seq_sch.py || { echo "FAIL: sample_seq_sch.py"; exit 1; }
rm -f work/sample_seq.spice work/sample_seq_sch.spice
xschem --rcfile "$RC" -b -q -n -s -o work sample_seq.sch > work/xschem_sample_seq.txt 2>&1
if [ -s work/sample_seq.spice ]; then
    mv work/sample_seq.spice work/sample_seq_sch.spice
    python3 check_sch.py sample_seq.spice work/sample_seq_sch.spice
else
    echo "FAIL: xschem produced no netlist for sample_seq.sch"
fi
mkdir -p work/render
for n in sample_seq seq_cell seq_dly; do
    rm -f "assets/$n.png"
    timeout 240 xvfb-run -a -s "-screen 0 3200x2000x24" xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
        --command "xschem zoom_full; xschem print png assets/$n.png 3200 2000; xschem exit closewindow force" \
        "$n.sch" > "work/render/$n.txt" 2>&1
    if [ -s "assets/$n.png" ]; then
        printf 'Figure: /foss/designs/mixed_signal/sample_seq/assets/%s.png\n' "$n"
    else
        echo "FAIL: render: no png of $n.sch"
    fi
done
exit 0
