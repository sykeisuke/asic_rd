#!/bin/sh
# Integrated 6-bit Wilkinson slice: comparator input-range sweep with a ramp window
# wide enough for inputs up to 2.2 V (the default 2.7 us reset window caps the ramp
# at ~2.0 V, so 2.0 V+ inputs could never complete in run-comparator-range.sh).
# Sweeps both input-pair variants at 0.5, 1.2, 1.8, 2.0, 2.1, 2.2 V.
set -eu
. "$(dirname -- "$0")/eda-common.sh"
result_dir="$PROJECT_ROOT/simulations/gf180_wilkinson_slice/work/range_wide"
mkdir -p "$result_dir"
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_wilkinson_slice
        for var in nmos pmos; do
            src=wilkinson_slice.spice; [ $var = pmos ] && src=wilkinson_slice_pmos.spice
            # derive: longer ramp/hold windows, longer transient, ramp-max diagnostic
            sed -E "s#work/vin_level.spice#work/range_wide/vin_level.spice#; s/^\.tran 20p 2800n/.tran 20p 3900n/; s/^(VRESET .*PULSE\(\{VDD\} 0 100n 1n 1n) 2700n 4u\)/\1 3600n 5u)/; s/^(VSAMPLE .*PULSE\(\{VDD\} 0 50n 1n 1n) 3u 4u\)/\1 4u 5u)/; s/^(VSAMPLEB .*PULSE\(0 \{VDD\} 50n 1n 1n) 3u 4u\)/\1 4u 5u)/; s/(avg_power .* TO=)2700n/\13700n/" $src > work/range_wide/$var.spice
            sed -i "0,/^\.measure/s//.measure tran ramp_max MAX v(ramp) FROM=100n TO=3.8u\n.measure/" work/range_wide/$var.spice
            grep -q "3600n 5u" work/range_wide/$var.spice
            printf "input_v,held_v,acquisition_error_v,conversion_time_s,code,expected_code,code_error,ramp_max_v,avg_power_w\n" > work/range_wide/${var}_range.csv
            for input in 0.5 1.2 1.8 2.0 2.1 2.2; do
                printf ".param VIN_LEVEL=%s\n" "$input" > work/range_wide/vin_level.spice
                ngspice -b -o work/range_wide/${var}_$input.log work/range_wide/$var.spice >/dev/null 2>&1 || true
                awk -v vin="$input" "/^held_voltage/{h=\$3} /^acquisition_error/{a=\$3} /^conversion_time/{c=\$3} /^output_code/{o=\$3} /^expected_code/{e=\$3} /^code_error/{ce=\$3} /^ramp_max/{r=\$3} /^avg_power/{p=\$3} END{printf \"%s,%s,%s,%s,%s,%s,%s,%s,%s\n\", vin,h,a,c,o,e,ce,r,p}" work/range_wide/${var}_$input.log >> work/range_wide/${var}_range.csv
            done
            echo "== $var =="; column -s, -t work/range_wide/${var}_range.csv
            # acceptance: every conversion completes and the ramp reaches >= 2.4 V
            awk -F, "NR>1 && (\$5==\"failed\" || \$8 < 2.4) {bad=1} END {exit bad}" work/range_wide/${var}_range.csv
        done
        echo "PASS: comparator input-range (wide window) sweep completed for both variants"
    '
printf '%s\n' "Results: $result_dir/{nmos,pmos}_range.csv"
