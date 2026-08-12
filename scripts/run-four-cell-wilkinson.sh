#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_four_cell_wilkinson/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_four_cell_wilkinson
        ngspice -b -o work/four_cell_wilkinson.log four_cell_wilkinson.spice
        test -s work/four_cell_wilkinson.csv
        test -s work/four_cell_wilkinson.raw
        grep -E "^(time[0-3]|code[0-3]|mux[0-3]|avg_power)" \
            work/four_cell_wilkinson.log | tee work/measurements.txt
        awk -f check-measurements.awk work/measurements.txt
    '

printf '%s\n' "Waveform: $result_dir/four_cell_wilkinson.csv"
printf '%s\n' "GUI waveform: $result_dir/four_cell_wilkinson.raw"
printf '%s\n' "Measurements: $result_dir/measurements.txt"
