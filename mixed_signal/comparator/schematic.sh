#!/bin/sh
# The xschem views of comparator, generated and proven in one command
# (the shape of comparator_bkp/comparator_10dev/schematic.sh):
#
#   ./scripts/sim.sh comparator-schematic      (the one entry point; writes metrics.json)
#
# Steps, all in the pinned container:
#   1. comparator_sch.py      -> comparator.sch / .sym (placement hand-authored, sizes parsed
#                                   from comparator.spice)
#   2. xschem -n -s              -> work/comparator_sch.spice; check-schematic.awk: device for
#                                   device (terminals, model, L/W/nf/m), device order and port order
#                                   against comparator.spice
#   2b. intent_op.py             -> the drawn netlist in its tracking state: every current written on
#                                   the sheet within intent.TOL of ngspice (data/intent_op.json)
#   3. tb_sch.py                 -> tb_tran.sch, tb_dc.sch, tb_nz.sch, tb_mc.sch (the DUT as
#                                   comparator.sym, netlisted from comparator.sch)
#   4. xschem under Xvfb         -> assets/<sch>_xschem.png / .svg for the cell and the four testbenches
#   5. xtb.py                    -> every testbench netlisted by xschem: its elements equal the bench
#                                   template filled for sw at the nominal point, and its simulation
#                                   reproduces data/values_verify.txt (data/xtb.csv)
#
# Prints PASS / FAIL / REPORT, name = value and artifact lines on stdout (sim.sh
# turns them into metrics.json); the full container output is
# work/schematic_console.log (never read; the lines above are the summary).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

mkdir -p "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data"
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data"
chmod a+rw "$BLOCK_DIR"/*.sch "$BLOCK_DIR"/*.sym 2>/dev/null || true
chmod a+rwx "$BLOCK_DIR"
log="$BLOCK_DIR/work/schematic_console.log"

status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks -e PDK=gf180mcuD -e MPLBACKEND=Agg \
    -e "XTB_JOBS=${XTB_JOBS:-4}" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -uo pipefail
        cd /foss/designs/mixed_signal/comparator
        RC=$PDK_ROOT/gf180mcuD/libs.tech/xschem/xschemrc
        st=0

        python3 comparator_sch.py || st=1
        rm -f work/comparator.spice work/comparator_sch.spice
        xschem --rcfile "$RC" -b -q -n -s -o work comparator.sch >work/comparator_xschem.out 2>&1
        if [ -s work/comparator.spice ]; then
            mv work/comparator.spice work/comparator_sch.spice
            awk -v ref=comparator.spice -f check-schematic.awk comparator.spice work/comparator_sch.spice || st=1
        else
            printf "FAIL: xschem produced no netlist for comparator.sch\n"; st=1
        fi
        if [ -s work/comparator_sch.spice ]; then python3 intent_op.py || st=1; fi

        python3 tb_sch.py || { printf "FAIL: tb_sch.py\n"; st=1; }

        for sch in comparator tb_tran tb_dc tb_nz tb_mc; do
            rm -f "assets/${sch}_xschem.png" "assets/${sch}_xschem.svg"
            timeout 120 xvfb-run -a -s "-screen 0 2400x1400x24" \
                xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
                --command "xschem zoom_full; xschem print png assets/${sch}_xschem.png 2400 1400; xschem print svg assets/${sch}_xschem.svg; xschem exit closewindow force" \
                "$sch.sch" >"work/${sch}_xschem_print.out" 2>&1
            if [ -s "assets/${sch}_xschem.png" ] && [ -s "assets/${sch}_xschem.svg" ]; then
                printf "PASS: xschem render assets/%s_xschem.png / .svg\n" "$sch"
            else
                printf "FAIL: xschem headless print produced no png/svg for %s.sch\n" "$sch"; st=1
            fi
        done

        python3 xtb.py || st=1
        exit $st
    ' >"$log" 2>&1 || status=$?

grep -E "^(PASS|FAIL|REPORT):|^[A-Za-z][A-Za-z0-9_]* = [-+0-9.]" "$log" || true
if [ "$status" -ne 0 ] && ! grep -q '^FAIL:' "$log"; then
    printf 'FAIL: schematic flow exited %s without a FAIL line\n' "$status"
fi
printf '%s\n' "Schematic: $BLOCK_DIR/comparator.sch"
printf '%s\n' "Symbol: $BLOCK_DIR/comparator.sym"
printf '%s\n' "Testbenches: $BLOCK_DIR/tb_tran.sch $BLOCK_DIR/tb_dc.sch $BLOCK_DIR/tb_nz.sch $BLOCK_DIR/tb_mc.sch"
printf '%s\n' "Renders: $BLOCK_DIR/assets"
printf '%s\n' "Intent record: $BLOCK_DIR/data/intent_op.json"
printf '%s\n' "xtb table: $BLOCK_DIR/data/xtb.csv"
exit "$status"
