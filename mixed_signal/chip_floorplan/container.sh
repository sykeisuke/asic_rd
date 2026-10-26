#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container with this block
# as the working directory, the full library install (PDK_LIBS_ROOT, `make
# pdk`) mounted read-only at /foss/pdk_libs.
#
#   ./container.sh 'python3 floorplan.py'
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

if [ ! -f "$PDK_LIBS_ROOT/gf180mcuD/libs.ref/gf180mcu_ocd_io/gds/gf180mcu_ocd_io.gds" ]; then
    printf 'FAIL: gf180mcu_ocd_io not installed in %s; run make pdk\n' "$PDK_LIBS_ROOT"
    exit 1
fi

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PDK=gf180mcuD \
    -e QT_QPA_PLATFORM=offscreen \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -v "$PDK_LIBS_ROOT:/foss/pdk_libs:ro" \
    "$EDA_IMAGE" -lc "set -euo pipefail; cd /foss/designs/mixed_signal/chip_floorplan; $*"
