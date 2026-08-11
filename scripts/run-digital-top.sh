#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"
result_dir="$PROJECT_ROOT/digital/asic_digital_top/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/digital/asic_digital_top
        gray=../wilkinson_gray_counter/wilkinson_gray_counter.v
        controller=../four_cell_wilkinson_controller/four_cell_wilkinson_controller.v
        sources="$gray $controller serial_readout.v asic_digital_top.v"
        iverilog -g2012 -Wall -o work/tb $sources tb_asic_digital_top.v
        vvp work/tb | tee work/simulation.log
        grep -q "PASS: sample-to-serial" work/simulation.log
        liberty=/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__tt_025C_3v30.lib
        yosys -Q -T -l work/gf180_synthesis.log -p "
            read_liberty -lib $liberty;
            read_verilog $sources;
            synth -top asic_digital_top -noabc;
            dfflibmap -liberty $liberty;
            abc -liberty $liberty;
            clean;
            stat -liberty $liberty;
            write_verilog -noattr work/asic_digital_top_mapped.v
        " >/dev/null
        test -s work/asic_digital_top_mapped.v
        grep -q "gf180mcu_fd_sc_mcu7t5v0" work/asic_digital_top_mapped.v
        sta -exit sta.tcl > work/sta.log 2>&1
        grep -q "tns max 0.00" work/sta.log
        grep -q "wns max 0.00" work/sta.log
    '

printf '%s\n' "Simulation: $result_dir/simulation.log"
printf '%s\n' "GF180 synthesis: $result_dir/gf180_synthesis.log"
printf '%s\n' "Static timing: $result_dir/sta.log"
