#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

if "$DOCKER_CLI" container inspect "$EDA_CONTAINER" >/dev/null 2>&1; then
    "$DOCKER_CLI" stop "$EDA_CONTAINER" >/dev/null
    printf '%s\n' "Stopped $EDA_CONTAINER"
else
    printf '%s\n' "$EDA_CONTAINER does not exist"
fi

