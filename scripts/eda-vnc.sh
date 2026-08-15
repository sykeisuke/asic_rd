#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

if "$DOCKER_CLI" container inspect "$EDA_CONTAINER" >/dev/null 2>&1; then
    if [ "$("$DOCKER_CLI" inspect -f '{{.State.Running}}' "$EDA_CONTAINER")" != true ]; then
        "$DOCKER_CLI" start "$EDA_CONTAINER" >/dev/null
    fi
else
    if [ -z "${ASIC_RD_VNC_PASSWORD:-}" ]; then
        printf '%s\n' 'Set ASIC_RD_VNC_PASSWORD in .env before creating the VNC container.' >&2
        exit 1
    fi
    "$DOCKER_CLI" run -d \
        --name "$EDA_CONTAINER" \
        --user 1000:1000 \
        --security-opt seccomp=unconfined \
        -e XKB_KEYBOARD_LAYOUT=us \
        -e VNC_PW="$ASIC_RD_VNC_PASSWORD" \
        -p 127.0.0.1:8080:80 \
        -p 127.0.0.1:5901:5901 \
        -v "$PROJECT_ROOT:/foss/designs:rw" \
        "$EDA_IMAGE" >/dev/null
fi

printf '%s\n' 'EDA desktop: http://localhost:8080/'
