#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_four_cell_array/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_four_cell_array
        ngspice -b -o work/four_cell_mux.log four_cell_mux.spice
        test -s work/four_cell_mux.csv
        grep -E "^(mux[0-3]_(value|error)|hold[0-3]_disturb)" \
            work/four_cell_mux.log | tee work/mux_measurements.txt
        awk -f check-mux-measurements.awk work/mux_measurements.txt
    '

printf '%s\n' "Waveform: $result_dir/four_cell_mux.csv"
printf '%s\n' "Measurements: $result_dir/mux_measurements.txt"
