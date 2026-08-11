#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"
physical="$PROJECT_ROOT/digital/asic_digital_top/physical"

"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/digital/asic_digital_top/physical
        librelane --manual-pdk --pdk-root /foss/pdks \
            -p gf180mcuD -s gf180mcu_fd_sc_mcu7t5v0 \
            --run-tag gf180_rtl2gds --overwrite --condensed \
            --hide-progress-bar config.yaml
        metrics=runs/gf180_rtl2gds/final/metrics.csv
        test -s runs/gf180_rtl2gds/final/gds/asic_digital_top.gds
        grep -q "route__drc_errors,0" "$metrics"
        grep -q "design__critical_disconnected_pin__count,0" "$metrics"
        grep -q "timing__setup_vio__count,0" "$metrics"
        grep -q "timing__hold_vio__count,0" "$metrics"
    '

printf '%s\n' "GDS: $physical/runs/gf180_rtl2gds/final/gds/asic_digital_top.gds"
printf '%s\n' "Metrics: $physical/runs/gf180_rtl2gds/final/metrics.csv"
