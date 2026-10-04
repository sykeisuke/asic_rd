#!/bin/sh
# Digital-on-top experiment: LibreLane RTL-to-GDS of mixed_top (8-bit digital
# top + one analog hard macro). Requires macro/ views from make_macro.sh.
set -eu
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
. "$REPO_ROOT/scripts/eda-common.sh"
PROJECT_ROOT="$REPO_ROOT"
SCL=${SCL:-gf180mcu_as_sc_mcu7t3v3}
PDK_ROOT=${PDK_ROOT:-/foss/designs/.eda-tools/pdk}
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc "
        set -euo pipefail
        cd /foss/designs/experiments/digital_on_top
        librelane --manual-pdk --pdk-root $PDK_ROOT -p gf180mcuD -s $SCL \
            --run-tag mixed --overwrite --condensed --hide-progress-bar config.yaml
        m=runs/mixed/final/metrics.csv
        test -s runs/mixed/final/gds/mixed_top.gds
        grep -E 'route__drc_errors|design__critical_disconnected_pin__count|timing__setup_vio__count|timing__hold_vio__count|magic__drc_error__count|design__lvs_error__count|antenna__violating' \$m
    "
