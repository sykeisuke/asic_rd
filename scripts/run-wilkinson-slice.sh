#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_wilkinson_slice/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_wilkinson_slice
        ngspice -b -o work/wilkinson_slice.log wilkinson_slice.spice
        test -s work/wilkinson_slice.csv
        grep -E "^(held_voltage|acquisition_error|conversion_time|output_code|expected_code|code_error|avg_power)" \
            work/wilkinson_slice.log | tee work/measurements.txt
        awk -f check-measurements.awk work/measurements.txt
    '

printf '%s\n' "Waveform: $result_dir/wilkinson_slice.csv"
printf '%s\n' "Measurements: $result_dir/measurements.txt"
