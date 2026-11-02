#!/bin/bash
# In-container half of the chip flow. Run through scripts/container.sh
# (scripts/run.sh does that for you):
#
#   scripts/container.sh 'bash scripts/build.sh macros'   # step 3: GDS -> hard macros, macro DRC
#   scripts/container.sh 'bash scripts/build.sh chip'     # steps 4-6: LibreLane Chip flow + sign-off
#   scripts/container.sh 'bash scripts/build.sh collect'  # re-read the figures of the last run
#   scripts/container.sh 'bash scripts/build.sh renders'  # the step-by-step pictures (renders/)
#   scripts/container.sh 'bash scripts/build.sh all'      # macros, chip, renders
#
# Prints `name = value` lines and REPORT lines; scripts/check-chip.awk
# turns them into the verdict.
set -euo pipefail

stage=${1:-all}
RUN=librelane/runs/chip_top
HERE=$(pwd)

macros() {
    rm -rf work/macros
    python3 scripts/macros.py analog
    python3 scripts/macro_check.py
    python3 scripts/macros.py digital
    python3 scripts/macros.py svg
}

chip() {
    rc=0
    to=${LIBRELANE_TO:+--to $LIBRELANE_TO}
    #- always from scratch: `--from` on an existing run continues from its
    #- LAST state, not from the step named
    (
        cd librelane
        librelane --manual-pdk --pdk-root /foss/pdk_libs \
            -p gf180mcuD -s gf180mcu_as_sc_mcu7t3v3 --pad gf180mcu_ocd_io \
            --run-tag chip_top --overwrite --condensed --hide-progress-bar \
            $to slot_1x0p5.yaml macros.yaml config.yaml
    ) || rc=$?
    echo "librelane_exit = $rc"
    collect
}

collect() {
    if [ -f "$RUN/error.log" ]; then
        echo "flow_error_lines = $(grep -c . "$RUN/error.log" || :)"
        sed 's/^/REPORT: librelane deferred: /' "$RUN/error.log"
    fi
    metrics=$RUN/final/metrics.csv
    if [ -s "$metrics" ]; then
        #- aggregate figures only; LibreLane writes the CSV with CRLF
        awk -F, '{ sub(/\r$/, "") }
                 NF == 2 && $1 !~ /:/ && $2 ~ /^[-+0-9.]/ {
                     print $1 " = " $2 }' "$metrics"
        echo "Metrics: $HERE/$metrics"
    fi
    #- the drawn analog / supply wires, as the PDN step reported them
    pdnlog=$(ls "$RUN"/*-openroad-generatepdn/openroad-generatepdn.log 2>/dev/null | tail -n 1 || :)
    if [ -n "$pdnlog" ]; then
        grep -h '^ws_[a-z0-9_]* = ' "$pdnlog" || :
        grep -h '^\[INFO\] ws: ' "$pdnlog" | sed 's/^\[INFO\] ws: /REPORT: drawn: /' | head -n 40 || :
    fi
    python3 scripts/lvs_summary.py "$RUN" || :
    python3 scripts/drc_summary.py "$RUN" || :
    gds=$RUN/final/gds/chip_top.gds
    if [ -s "$gds" ]; then
        echo "chip_gds_bytes = $(stat -c %s "$gds")"
        echo "GDS: $HERE/$gds"
    fi
    return 0
}

renders() {
    mkdir -p renders
    #- inputs and the final chip as KLayout sees them (real layers)
    python3 scripts/render_gds.py inputs
    #- the two macros' LEF views (step 3; needs the macros stage's LEF)
    python3 scripts/macros.py svg
    #- one picture per flow step, from the step's own OpenROAD database
    openroad -python -exit scripts/render_steps.py 2>&1 |
        grep -E '^(SVG|PNG|render_|REPORT)' || :
    if [ -s "$RUN/final/gds/chip_top.gds" ]; then
        python3 scripts/render_gds.py chip
    fi
    ls renders | sed 's/^/REPORT: render: /'
    echo "renders_files = $(ls renders | wc -l)"
}

case $stage in
    macros)  macros ;;
    chip)    chip ;;
    collect) collect ;;
    renders) renders ;;
    all)     macros; chip; renders ;;
    *) echo "unknown stage $stage" >&2; exit 2 ;;
esac
