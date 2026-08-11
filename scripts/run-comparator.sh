#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_comparator/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_comparator
        ngspice -b -o work/comparator.log comparator.spice
        test -s work/comparator.csv
        grep -E "^(crossing_delay|output_low|output_high|avg_power)" \
            work/comparator.log | tee work/measurements.txt
        awk -f check-measurements.awk work/measurements.txt
    '

printf '%s\n' "Waveform: $result_dir/comparator.csv"
printf '%s\n' "Measurements: $result_dir/measurements.txt"
