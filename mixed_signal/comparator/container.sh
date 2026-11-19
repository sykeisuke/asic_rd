#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container with this block
# as the working directory (as comparator_bkp/comparator_10dev/container.sh).
#
#   ./container.sh 'python3 derive.py'
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PDK=gf180mcuD \
    -e "MPLBACKEND=Agg" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc "set -euo pipefail; cd /foss/designs/mixed_signal/comparator; $*"
