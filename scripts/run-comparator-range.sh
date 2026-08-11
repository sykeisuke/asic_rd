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
        printf "input_v,held_v,acquisition_error_v,conversion_time_s,code,expected_code,code_error\n" \
            > work/pmos_comparator_range.csv

        for input in 0.4 1.2 1.8; do
            label=${input/./p}
            printf ".param VIN_LEVEL=%s\n" "$input" > work/vin_level.spice
            ngspice -b -o "work/pmos_range_${label}.log" \
                wilkinson_slice_pmos.spice
            awk -v input="$input" -f extract-transfer.awk \
                "work/pmos_range_${label}.log" \
                >> work/pmos_comparator_range.csv
        done

        cat work/pmos_comparator_range.csv
        awk -f check-comparator-range.awk work/pmos_comparator_range.csv \
            | tee work/pmos_comparator_range_check.txt
    '

printf '%s\n' "PMOS range data: $result_dir/pmos_comparator_range.csv"
