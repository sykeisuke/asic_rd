#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container with this block
# as the working directory. Nothing in this folder runs on the host.
#
#   ./container.sh 'python3 floorplan.py'
#
# The image pin and the Docker CLI come from scripts/eda-common.sh, sourced by
# path. This block may live in a git worktree under the main checkout, so the
# MAIN checkout (git common dir's parent) is what gets mounted at /foss/designs:
# that is where .eda-tools (gdsfactory gf180mcu plugin, cicpy), the analog
# layout flow and the comparator netlist live. The block itself is reached at
# its path relative to that mount.
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MAIN_ROOT=$(cd -- "$BLOCK_DIR" && git rev-parse --git-common-dir)
MAIN_ROOT=$(CDPATH= cd -- "$(dirname -- "$MAIN_ROOT")" && pwd)
. "$MAIN_ROOT/scripts/eda-common.sh"
REL=${BLOCK_DIR#"$MAIN_ROOT"/}

#- the container runs as uid 1000; outputs land in these
for d in "$BLOCK_DIR/work" "$BLOCK_DIR/physical/final_views/gds" "$BLOCK_DIR/physical/final_views/svg" "$BLOCK_DIR/physical/final_views" \
         "$BLOCK_DIR/physical/final_views/render"; do
    mkdir -p "$d"; chmod 777 "$d"
done

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PYTHONUSERBASE=/foss/designs/.eda-tools \
    -e QT_QPA_PLATFORM=offscreen \
    -e MPLBACKEND=Agg \
    -e ANALOG_LAYOUT=/foss/designs/mixed_signal/analog_layout \
    -e COMPARATOR=/foss/designs/mixed_signal/comparator \
    -e "COMPARATOR_UC=/foss/designs/$(dirname "$REL")/comparator_unit_cell" \
    -v "$MAIN_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc "set -euo pipefail; export PATH=\$PYTHONUSERBASE/bin:\$PATH; cd /foss/designs/$REL; $*"
