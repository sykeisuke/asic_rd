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
        : > work/transfer_check.txt
        printf "input_v,held_v,acquisition_error_v,conversion_time_s,code,expected_code,code_error\n" \
            > work/transfer.csv

        for input in 0.4 0.6 0.8 1.0 1.2 1.4 1.5 1.6; do
            label=${input/./p}
            printf ".param VIN_LEVEL=%s\n" "$input" > work/vin_level.spice
            ngspice -b -o "work/transfer_${label}.log" wilkinson_slice.spice
            awk -v input="$input" -f extract-transfer.awk \
                "work/transfer_${label}.log" >> work/transfer.csv
        done

        cat work/transfer.csv
        awk -f check-transfer.awk work/transfer.csv | tee work/transfer_check.txt
    '

printf '%s\n' "Transfer data: $result_dir/transfer.csv"
printf '%s\n' "Transfer check: $result_dir/transfer_check.txt"
