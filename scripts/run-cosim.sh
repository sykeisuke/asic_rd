#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/mixed_signal/wilkinson_cosim/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs

        mkdir -p simulations/gf180_wilkinson_slice/work
        printf ".param VIN_LEVEL=1.2\n" \
            > simulations/gf180_wilkinson_slice/work/vin_level.spice
        ngspice -b -o simulations/gf180_wilkinson_slice/work/wilkinson_slice.log \
            simulations/gf180_wilkinson_slice/wilkinson_slice.spice
        grep -E "^(conversion_time|output_code)" \
            simulations/gf180_wilkinson_slice/work/wilkinson_slice.log \
            > mixed_signal/wilkinson_cosim/work/analog_measurements.txt

        cd mixed_signal/wilkinson_cosim
        awk -f analog-to-verilog.awk work/analog_measurements.txt \
            > work/analog_stimulus.vh
        test -s work/analog_stimulus.vh

        iverilog -g2012 -Wall -I work -o work/tb_wilkinson_cosim \
            ../../digital/wilkinson_counter/wilkinson_counter.v \
            tb_wilkinson_cosim.v
        vvp work/tb_wilkinson_cosim | tee work/cosimulation.log
        grep -q "PASS: analog timing" work/cosimulation.log
    '

printf '%s\n' "Analog stimulus: $result_dir/analog_stimulus.vh"
printf '%s\n' "Co-verification: $result_dir/cosimulation.log"
