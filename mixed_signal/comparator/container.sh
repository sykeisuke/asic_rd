#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container with this block
# as the working directory. Everything in this folder goes through here, so
# no tool ever runs on the host.
#
#   ./container.sh 'python3 size_v3.py'
#   ./container.sh 'ngspice -b -o work/x.log tb_offset.spice'
#
# The image pin and the Docker CLI come from scripts/eda-common.sh, which is
# sourced by path rather than copied. That script derives PROJECT_ROOT from
# $0, which is this file when sourced, so PROJECT_ROOT is recomputed here.
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
