#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_ramp_generator/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_ramp_generator
        ngspice -b -o work/ramp_generator.log ramp_generator.spice
        test -s work/ramp_generator.csv
        grep -E "^(reset_level|slope_average|slope_mismatch|avg_power)" \
            work/ramp_generator.log | tee work/measurements.txt
        awk -f check-measurements.awk work/measurements.txt
    '

printf '%s\n' "Waveform: $result_dir/ramp_generator.csv"
printf '%s\n' "Measurements: $result_dir/measurements.txt"
