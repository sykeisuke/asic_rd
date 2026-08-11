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
        ngspice -b -o work/four_cell_array.log four_cell_array.spice
        test -s work/four_cell_array.csv
        grep -E "^hold[0-3]_(value|error)" work/four_cell_array.log \
            | tee work/measurements.txt
        awk -f check-measurements.awk work/measurements.txt
    '

printf '%s\n' "Waveform: $result_dir/four_cell_array.csv"
printf '%s\n' "Measurements: $result_dir/measurements.txt"
