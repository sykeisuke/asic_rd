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
        printf "common_mode_v,trip_diff_v\n" > work/nmos_offset.csv
        printf "common_mode_v,trip_diff_v\n" > work/pmos_offset.csv

        for common_mode in 0.4 1.2 1.8; do
            label=${common_mode/./p}
            printf ".param VCM_LEVEL=%s\n" "$common_mode" \
                > work/common_mode.spice

            ngspice -b -o "work/nmos_offset_${label}.log" \
                comparator_offset_nmos.spice
            awk -v common_mode="$common_mode" -f extract-offset.awk \
                "work/nmos_offset_${label}.log" >> work/nmos_offset.csv

            ngspice -b -o "work/pmos_offset_${label}.log" \
                comparator_offset_pmos.spice
            awk -v common_mode="$common_mode" -f extract-offset.awk \
                "work/pmos_offset_${label}.log" >> work/pmos_offset.csv
        done

        cat work/nmos_offset.csv
        cat work/pmos_offset.csv
    '

printf '%s\n' "NMOS offset: $result_dir/nmos_offset.csv"
printf '%s\n' "PMOS offset: $result_dir/pmos_offset.csv"
