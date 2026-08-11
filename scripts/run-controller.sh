#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/digital/four_cell_wilkinson_controller/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/digital/four_cell_wilkinson_controller
        counter=../wilkinson_counter/wilkinson_counter.v
        iverilog -g2012 -Wall -o work/tb_four_cell_wilkinson_controller \
            "$counter" four_cell_wilkinson_controller.v \
            tb_four_cell_wilkinson_controller.v
        vvp work/tb_four_cell_wilkinson_controller | tee work/simulation.log
        grep -q "PASS: four-cell Wilkinson controller" work/simulation.log

        liberty=/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__tt_025C_3v30.lib
        yosys -Q -T -l work/gf180_synthesis.log -p "
            read_liberty -lib $liberty;
            read_verilog $counter four_cell_wilkinson_controller.v;
            synth -top four_cell_wilkinson_controller -noabc;
            dfflibmap -liberty $liberty;
            abc -liberty $liberty;
            clean;
            stat -liberty $liberty;
            write_verilog -noattr work/four_cell_wilkinson_controller_mapped.v
        " >/dev/null
        test -s work/four_cell_wilkinson_controller_mapped.v
        grep -q "gf180mcu_fd_sc_mcu7t5v0" \
            work/four_cell_wilkinson_controller_mapped.v
    '

printf '%s\n' "Simulation: $result_dir/simulation.log"
printf '%s\n' "GF180 synthesis: $result_dir/gf180_synthesis.log"
