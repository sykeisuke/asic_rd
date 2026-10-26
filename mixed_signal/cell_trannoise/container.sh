#!/bin/sh
# Run a command inside the pinned EDA container with this block as the working
# directory. Everything in this folder goes through here, so no tool ever runs
# on the host. The latch is a gf180mcu_as_sc_mcu7t3v3 standard cell: the full
# library install of the pinned commit (make pdk-libs) is mounted at /foss/pdk_libs.
#
#   ./container.sh 'bash ct.sh'
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PDK=gf180mcuD \
    -e "MPLBACKEND=Agg" \
    -e "JOBS=${JOBS:-12}" \
    -e "FORCE=${FORCE:-0}" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -v "$PDK_LIBS_ROOT:/foss/pdk_libs:ro" \
    "$EDA_IMAGE" -lc "set -euo pipefail; cd /foss/designs/mixed_signal/cell_trannoise; $*"
