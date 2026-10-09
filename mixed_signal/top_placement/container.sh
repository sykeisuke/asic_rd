#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container with this block
# as the working directory. Nothing in this folder runs on the host.
#
#   ./container.sh 'python3 macros.py'
#   LIBRELANE_TO=OpenROAD.GeneratePDN ./container.sh 'bash build.sh chip'
#
# The image pin and the Docker CLI come from scripts/eda-common.sh.
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
#- eda-common.sh derives PROJECT_ROOT from $0, which is this file here
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)
REL=${BLOCK_DIR#"$PROJECT_ROOT"/}

#- the container runs as uid 1000; outputs land in these
for d in "$BLOCK_DIR/work" "$BLOCK_DIR/work/macros" "$BLOCK_DIR/librelane" \
         "$BLOCK_DIR/physical/final_views" \
         "$PROJECT_ROOT/mixed_signal/analog_layout/work"; do
    mkdir -p "$d"; chmod 777 "$d"
done

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PDK=gf180mcuD \
    -e QT_QPA_PLATFORM=offscreen \
    -e "LIBRELANE_TO=${LIBRELANE_TO:-}" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc "set -euo pipefail; cd /foss/designs/$REL; $*"
