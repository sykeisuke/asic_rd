#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(dirname -- "$script_dir")

if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    . "$PROJECT_ROOT/.env"
    set +a
fi

EDA_IMAGE='docker.io/hpretl/iic-osic-tools:2026.07@sha256:5d6adf1f437cd0f2f8f8614488ec3c247ba8c768f4663a25d5e997b30ccb13b0'
EDA_CONTAINER='asic-rd-gf180-vnc'

if command -v docker >/dev/null 2>&1; then
    DOCKER_CLI=$(command -v docker)
elif [ -x /Applications/Docker.app/Contents/Resources/bin/docker ]; then
    DOCKER_CLI=/Applications/Docker.app/Contents/Resources/bin/docker
else
    printf '%s\n' 'Docker CLI was not found.' >&2
    exit 1
fi

# Repository-local, git-ignored user site for pinned Python EDA add-ons
# (gdsfactory PDK plugin etc.). Populate with: make tools
EDA_TOOLS_DIR="$PROJECT_ROOT/.eda-tools"

# The image's /foss/pdks carries the pinned gf180mcuD commit but only the fd_*
# libraries. The frozen gf180mcu_as_sc_mcu7t3v3 / gf180mcu_ocd_io views come
# from a full Ciel install of the SAME commit, outside the repository and
# outside the image: `make pdk-libs` (scripts/run-pdk-libs.sh). Blocks that
# need it mount it read-only at /foss/pdk_libs.
if [ -z "${PDK_LIBS_ROOT:-}" ]; then
    if [ -d "$EDA_TOOLS_DIR/pdk/gf180mcuD" ]; then PDK_LIBS_ROOT="$EDA_TOOLS_DIR/pdk"; else PDK_LIBS_ROOT="$HOME/pdks"; fi
fi
PDK_COMMIT='f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7'

export PROJECT_ROOT EDA_IMAGE EDA_CONTAINER DOCKER_CLI EDA_TOOLS_DIR PDK_LIBS_ROOT PDK_COMMIT
