#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/digital/legacy/wilkinson_counter/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/digital/legacy/wilkinson_counter
        iverilog -g2012 -Wall -o work/tb_wilkinson_counter \
            wilkinson_counter.v tb_wilkinson_counter.v
        vvp work/tb_wilkinson_counter | tee work/simulation.log
        grep -q "PASS: wilkinson_counter self-check" work/simulation.log
        yosys -Q -T -l work/synthesis.log \
            -p "read_verilog wilkinson_counter.v; synth -top wilkinson_counter; stat" \
            >/dev/null
        liberty=/foss/designs/.eda-tools/pdk/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/lib/gf180mcu_as_sc_mcu7t3v3__tt_025C_3v30.lib
        yosys -Q -T -l work/gf180_synthesis.log -p "
            read_liberty -lib $liberty;
            read_verilog wilkinson_counter.v;
            synth -top wilkinson_counter -noabc;
            dfflibmap -liberty $liberty;
            abc -liberty $liberty;
            clean;
            stat -liberty $liberty;
            write_verilog -noattr work/wilkinson_counter_mapped.v
        " >/dev/null
        test -s work/synthesis.log
        test -s work/gf180_synthesis.log
        grep -q "gf180mcu_as_sc_mcu7t3v3" work/wilkinson_counter_mapped.v
    '

printf '%s\n' "Simulation: $result_dir/simulation.log"
printf '%s\n' "Synthesis: $result_dir/synthesis.log"
printf '%s\n' "GF180 synthesis: $result_dir/gf180_synthesis.log"
