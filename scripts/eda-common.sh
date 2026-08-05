#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(dirname -- "$script_dir")
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

export PROJECT_ROOT EDA_IMAGE EDA_CONTAINER DOCKER_CLI

