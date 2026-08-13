#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_sampling_cell/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_sampling_cell
        ngspice -b -o work/ideal_sampling_cell.log ideal_sampling_cell.spice
        test -s work/ideal_sampling_cell.csv
        grep -E "^(acquisition_error|hold_droop|clock_feedthrough)" \
            work/ideal_sampling_cell.log | tee work/ideal_measurements.txt

        ngspice -b -o work/sampling_cell.log sampling_cell.spice
        test -s work/sampling_cell.csv
        test -s work/sampling_cell.log
        grep -E "^(acquisition_error|hold_droop|clock_feedthrough)" \
            work/sampling_cell.log | tee work/measurements.txt
        awk -f check-measurements.awk work/measurements.txt

        ngspice -b -o work/transmission_gate.log transmission_gate.spice
        test -s work/transmission_gate.csv
        grep -E "^(acquisition_error|hold_droop|clock_feedthrough)" \
            work/transmission_gate.log | tee work/transmission_gate_measurements.txt
        awk -f check-measurements.awk work/transmission_gate_measurements.txt
'

printf '%s\n' "Ideal waveform: $result_dir/ideal_sampling_cell.csv"
printf '%s\n' "Ideal measurements: $result_dir/ideal_measurements.txt"
printf '%s\n' "Waveform: $result_dir/sampling_cell.csv"
printf '%s\n' "Measurements: $result_dir/measurements.txt"
printf '%s\n' "TG waveform: $result_dir/transmission_gate.csv"
printf '%s\n' "TG measurements: $result_dir/transmission_gate_measurements.txt"
