#!/bin/sh
# The xschem views of comparator, generated and proven in one command:
#
#   ./schematic.sh                  against comparator.spice (the controlled deck)
#
# Steps, all in the pinned container:
#   1. comparator_sch.py <deck>  -> comparator.sch (placement hand-authored, sizes parsed from the deck)
#   2. xschem -n -s               -> work/comparator_sch.spice; check-schematic.awk: device for device
#                                    (terminals, model, L/W/nf/m) and the port order against the deck
#   2b. intent_op.py              -> the drawn netlist on the bench bias: every device current
#                                    within 5 % of the design value on the drawing (intent.py);
#                                    peak DC gain per stage and inn -> dout (recorded)
#   3. tb_sch.py                  -> tb_delay.sch, tb_trip.sch, tb_noise.sch, tb_mc.sch (the DUT as
#                                    comparator.sym, netlisted from comparator.sch)
#   4. xschem under Xvfb          -> assets/<sch>_xschem.png / .svg for the DUT and the four testbenches
#   5. comparator_schematic.py   -> assets/comparator_schematic.png (schemdraw)
#   6. xtb.py                     -> every testbench netlisted by xschem, simulated, compared with
#                                    its hand-written bench (data/xtb.csv)
#
# Writes runs/$TARGET/<stamp>/metrics.json and links `latest`.
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

DECK=${1:-comparator.spice}
TARGET=${TARGET:-comparator-schematic}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
mkdir -p "$run_dir" "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data"
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data"
chmod a+rw "$BLOCK_DIR"/*.sch 2>/dev/null || true
chmod a+rwx "$BLOCK_DIR"

status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks -e PDK=gf180mcuD -e MPLBACKEND=Agg \
    -e "DECK=$DECK" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -uo pipefail
        cd /foss/designs/mixed_signal/comparator
        RC=$PDK_ROOT/gf180mcuD/libs.tech/xschem/xschemrc
        st=0

        python3 comparator_sch.py "$DECK" || st=1
        rm -f work/comparator.spice work/comparator_sch.spice
        xschem --rcfile "$RC" -b -q -n -s -o work comparator.sch >work/comparator_xschem.out 2>&1
        if [ -s work/comparator.spice ]; then
            mv work/comparator.spice work/comparator_sch.spice
            awk -v ref="$DECK" -f check-schematic.awk "$DECK" work/comparator_sch.spice || st=1
        else
            printf "FAIL: xschem produced no netlist for comparator.sch\n"; st=1
        fi
        if [ -s work/comparator_sch.spice ]; then python3 intent_op.py || st=1; fi

        python3 tb_sch.py || { printf "FAIL: tb_sch.py\n"; st=1; }

        for sch in comparator tb_delay tb_trip tb_noise tb_mc; do
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

        python3 comparator_schematic.py "$DECK" || st=1
        python3 xtb.py || st=1
        exit $st
    ' >"$run_dir/console.log" 2>&1 || status=$?

grep -E "^(PASS|FAIL|REPORT):" "$run_dir/console.log" || true
{
    printf '%s\n' "Schematic: $BLOCK_DIR/comparator.sch"
    printf '%s\n' "Symbol: $BLOCK_DIR/comparator.sym"
    printf '%s\n' "Testbenches: $BLOCK_DIR/tb_delay.sch $BLOCK_DIR/tb_trip.sch $BLOCK_DIR/tb_noise.sch $BLOCK_DIR/tb_mc.sch"
    printf '%s\n' "xtb table: $BLOCK_DIR/data/xtb.csv"
} >"$run_dir/extra-metrics.txt"
awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="${ASIC_RD_CORNER:-typical_27c}" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
exit "$status"
