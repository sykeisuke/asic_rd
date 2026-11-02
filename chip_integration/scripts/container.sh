#!/bin/sh
# Run one command inside the pinned IIC-OSIC-TOOLS container, with
# chip_integration/ as the working directory. No EDA tool runs on the host.
#
#   scripts/container.sh 'python3 scripts/macros.py'
#   LIBRELANE_TO=OpenROAD.GeneratePDN scripts/container.sh 'bash scripts/build.sh chip'
#
# The image pin and the Docker CLI come from ../scripts/eda-common.sh. The
# frozen library set (gf180mcu_as_sc_mcu7t3v3, gf180mcu_ocd_io; `make pdk`)
# is mounted read-only at /foss/pdk_libs, the PDK itself is the image's
# /foss/pdks.
set -eu

FLOW_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$FLOW_DIR/../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$FLOW_DIR/.." && pwd)
REL=${FLOW_DIR#"$PROJECT_ROOT"/}

#- the container runs as uid 1000; outputs land in these
for d in "$FLOW_DIR/work" "$FLOW_DIR/work/macros" "$FLOW_DIR/librelane" \
         "$FLOW_DIR/renders"; do
    mkdir -p "$d"; chmod 777 "$d"
done

exec "$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -e PDK_ROOT=/foss/pdks \
    -e PDK=gf180mcuD \
    -e QT_QPA_PLATFORM=offscreen \
    -e "LIBRELANE_TO=${LIBRELANE_TO:-}" \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -v "$PDK_LIBS_ROOT:/foss/pdk_libs:ro" \
    "$EDA_IMAGE" -lc "set -euo pipefail; cd /foss/designs/$REL; $*"
