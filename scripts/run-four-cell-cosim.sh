#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/mixed_signal/four_cell_cosim/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs
        analog=simulations/gf180_four_cell_wilkinson
        cosim=mixed_signal/four_cell_cosim
        controller=digital/four_cell_wilkinson_controller
        counter=digital/wilkinson_counter/wilkinson_counter.v

        mkdir -p "$analog/work" "$cosim/work"
        ngspice -b -o "$analog/work/four_cell_wilkinson.log" \
            "$analog/four_cell_wilkinson.spice"
        grep -E "^(time[0-3]|code[0-3])" \
            "$analog/work/four_cell_wilkinson.log" \
            > "$cosim/work/analog_measurements.txt"
        awk -f "$cosim/analog-to-verilog.awk" \
            "$cosim/work/analog_measurements.txt" \
            > "$cosim/work/analog_stimulus.vh"
        test -s "$cosim/work/analog_stimulus.vh"

        cd "$cosim"
        iverilog -g2012 -Wall -I work -o work/tb_four_cell_cosim \
            ../../"$counter" \
            ../../"$controller"/four_cell_wilkinson_controller.v \
            tb_four_cell_cosim.v
        vvp work/tb_four_cell_cosim | tee work/cosimulation.log
        grep -q "PASS: analog times captured RTL codes" \
            work/cosimulation.log
    '

printf '%s\n' "Analog stimulus: $result_dir/analog_stimulus.vh"
printf '%s\n' "Co-verification: $result_dir/cosimulation.log"
