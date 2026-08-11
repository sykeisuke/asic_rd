#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"
result_dir="$PROJECT_ROOT/digital/wilkinson_gray_counter/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/digital/wilkinson_gray_counter
        iverilog -g2012 -Wall -o work/tb wilkinson_gray_counter.v \
            tb_wilkinson_gray_counter.v
        vvp work/tb | tee work/simulation.log
        grep -q "PASS: Gray counter" work/simulation.log
        liberty=/foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0/lib/gf180mcu_fd_sc_mcu7t5v0__tt_025C_3v30.lib
        yosys -Q -T -l work/gf180_synthesis.log -p "
            read_liberty -lib $liberty;
            read_verilog wilkinson_gray_counter.v;
            synth -top wilkinson_gray_counter -noabc;
            dfflibmap -liberty $liberty;
            abc -liberty $liberty;
            clean;
            stat -liberty $liberty;
            write_verilog -noattr work/wilkinson_gray_counter_mapped.v
        " >/dev/null
        test -s work/wilkinson_gray_counter_mapped.v
        grep -q "gf180mcu_fd_sc_mcu7t5v0" work/wilkinson_gray_counter_mapped.v
    '

printf '%s\n' "Simulation: $result_dir/simulation.log"
printf '%s\n' "GF180 synthesis: $result_dir/gf180_synthesis.log"
