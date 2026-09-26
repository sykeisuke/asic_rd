#!/bin/bash
# In-container half of `make top-placement`. Run through container.sh:
#
#   ./container.sh 'bash build.sh macros'   # wrappers + their KLayout DRC/LVS
#   ./container.sh 'bash build.sh chip'     # LibreLane Chip flow
#   ./container.sh 'bash build.sh all'
#
# Prints `name = value` lines and artifact paths for scripts/sim.sh;
# check-top.awk turns them into the verdict.
set -euo pipefail

stage=${1:-all}
MACROS="wsa_cmp wsa_inv wsa_inv_gf"
RUN=librelane/runs/chip_top

macros() {
    rm -rf work/macros
    python3 macros.py
    for m in $MACROS; do
        gds=work/macros/$m/gds/$m.gds
        #- the PDK's own deck; density apart, as for every analog cell
        python3 ../analog_layout/signoff.py drc "$m" --gds "$gds"
        python3 ../analog_layout/signoff.py lvs "$m" \
            "work/macros/$m/spice/$m.spice" --gds "$gds"
        #- the PR boundary LibreLane's Magic.StreamOut needs, read with
        #- LibreLane's own script: 4 = llx lly urx ury all found
        n=$(_GDS_IN="$gds" _MACRO_NAME_IN="$m" \
            magic -dnull -noconsole \
                -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc \
                "$(python3 -c 'import librelane, os; print(os.path.dirname(librelane.__file__))')/scripts/magic/get_bbox.tcl" \
                </dev/null 2>/dev/null | grep -c '^%OL_METRIC_I [lu][lr][xy] ' || :)
        echo "${m}_magic_bbox_fields = ${n:-0}"
    done
}

chip() {
    rc=0
    #- LIBRELANE_TO=<step> stops early (floorplan/PDN iterations); the
    #- verdict needs the whole flow, and check-top.awk fails without it
    to=${LIBRELANE_TO:+--to $LIBRELANE_TO}
    #- always from scratch: `--from <step>` on an existing run continues
    #- from that run's LAST state, not from before <step> (measured: a
    #- rerun of GeneratePDN on an already-routed database died in pdngen)
    start="--overwrite"
    (
        cd librelane
        librelane --manual-pdk --pdk-root /foss/pdks \
            -p gf180mcuD -s gf180mcu_fd_sc_mcu7t5v0 --pad gf180mcu_fd_io \
            --run-tag chip_top $start --condensed --hide-progress-bar \
            $to slot_0p5x1.yaml macros.yaml config.yaml
    ) || rc=$?
    echo "librelane_exit = $rc"
    collect
}

#- the figures of an existing run, without running it again (a run
#- whose wrapper shell was killed still finishes inside Docker)
collect() {
    #- the flow's deferred-error summary: one line per error class
    if [ -f "$RUN/error.log" ]; then
        echo "flow_error_lines = $(grep -c . "$RUN/error.log" || :)"
        sed 's/^/REPORT: librelane deferred: /' "$RUN/error.log"
    fi
    metrics=$RUN/final/metrics.csv
    if [ -s "$metrics" ]; then
        #- aggregate figures only; per-corner names carry a ':' that
        #- the metrics record cannot hold
        #- and LibreLane writes the CSV with CRLF, which would make
        #- every value fail the metrics record's number test
        awk -F, '{ sub(/\r$/, "") }
                 NF == 2 && $1 !~ /:/ && $2 ~ /^[-+0-9.]/ {
                     print $1 " = " $2 }' "$metrics"
        echo "Metrics: /foss/designs/mixed_signal/top_placement/$metrics"
    fi
    #- which nets and pins, when Netgen disagrees; which rules and where,
    #- when KLayout DRC or the stream-out XOR does
    python3 lvs_summary.py "$RUN" || :
    python3 drc_summary.py "$RUN" || :
    gds=$RUN/final/gds/chip_top.gds
    if [ -s "$gds" ]; then
        echo "chip_gds_bytes = $(stat -c %s "$gds")"
        echo "GDS: /foss/designs/mixed_signal/top_placement/$gds"
    fi
    return 0
}

case $stage in
    macros) macros ;;
    chip)   chip ;;
    collect) collect ;;
    all)    macros; chip ;;
    *) echo "unknown stage $stage" >&2; exit 2 ;;
esac
