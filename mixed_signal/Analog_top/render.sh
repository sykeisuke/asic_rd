#!/bin/sh
# render.sh -- every v5 sheet to assets/<sheet>.png and <sheet>.svg (this
# folder), under a virtual X server. Inside the container, cwd = this block.
# Called by schematic.sh and, after the op table is written onto
# analog_top.sch, by op.sh.
#   SHEETS='analog_top atop_cell' sh render.sh     a subset
set -u
cd "$(dirname -- "$0")"
mkdir -p assets work/render
RC=xschemrc
SHEETS=${SHEETS:-'analog_top atop_cell comparator_d ramp_simple_d bias_gen_s sw_s0 sw_s1 sw_s2 tb_analog_top symbol_gallery'}
for n in $SHEETS; do
    src="$n.sch"
    rm -f "assets/$n.png" "$n.svg"
    timeout 240 xvfb-run -a -s "-screen 0 3200x2000x24" xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
        --command "xschem zoom_full; xschem print png assets/$n.png 3200 2000; xschem print svg $n.svg; xschem exit closewindow force" \
        "$src" > "work/render/$n.txt" 2>&1
    if [ -s "assets/$n.png" ]; then
        printf 'Figure: /foss/designs/mixed_signal/Analog_top/assets/%s.png\n' "$n"
    else
        echo "FAIL: render: no png of $src"
    fi
    if [ -s "$n.svg" ]; then
        printf 'Figure: /foss/designs/mixed_signal/Analog_top/%s.svg\n' "$n"
    else
        echo "FAIL: render: no svg of $src"
    fi
done
exit 0
