#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container with this block
# as the working directory. Nothing in this folder runs on the host.
#
#   ./container.sh 'ngspice -b tb_ramp.spice'
#   ./container.sh 'python3 plot_ramp.py'
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

mkdir -p "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data"
chown -R 1000:1000 "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data" 2>/dev/null || true
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/assets" "$BLOCK_DIR/data" 2>/dev/null || true

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PDK=gf180mcuD \
    -e MPLBACKEND=Agg \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc "set -euo pipefail; cd /foss/designs/mixed_signal/ramp_gen; $*"
