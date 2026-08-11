#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/mixed_signal/four_cell_phase_sweep/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs
        analog=simulations/gf180_four_cell_wilkinson
        bridge=mixed_signal/four_cell_cosim
        sweep=mixed_signal/four_cell_phase_sweep
        controller=digital/four_cell_wilkinson_controller
        counter=digital/wilkinson_gray_counter/wilkinson_gray_counter.v

        mkdir -p "$analog/work" "$sweep/work"
        ngspice -b -o "$analog/work/four_cell_wilkinson.log" \
            "$analog/four_cell_wilkinson.spice"
        grep -E "^(time[0-3]|code[0-3])" \
            "$analog/work/four_cell_wilkinson.log" \
            > "$sweep/work/analog_measurements.txt"
        awk -f "$bridge/analog-to-verilog.awk" \
            "$sweep/work/analog_measurements.txt" \
            > "$sweep/work/analog_stimulus.vh"

        cd "$sweep"
        iverilog -g2012 -Wall -I work -o work/tb_four_cell_phase_sweep \
            ../../"$counter" \
            ../../"$controller"/four_cell_wilkinson_controller.v \
            tb_four_cell_phase_sweep.v
        : > work/phase_sweep.log
        for offset in -2000 -1000 -600 -400 0 400 600 1000 2000; do
            vvp work/tb_four_cell_phase_sweep +OFFSET_PS="$offset" \
                | tee -a work/phase_sweep.log
        done
        test "$(grep -c "^SWEEP" work/phase_sweep.log)" -eq 9
        grep "^SWEEP" work/phase_sweep.log > work/phase_sweep.csv
        grep -q "offset_ps=400 codes=16,20,27,35" work/phase_sweep.log
        grep -q "offset_ps=600 codes=16,20,28,35" work/phase_sweep.log
    '

printf '%s\n' "Sweep results: $result_dir/phase_sweep.csv"
