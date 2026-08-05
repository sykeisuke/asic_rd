#!/bin/sh
set -eu

docker_cli=/Applications/Docker.app/Contents/Resources/bin/docker

if [ ! -x "$docker_cli" ]; then
    printf '%s\n' 'Docker Desktop CLI was not found.' >&2
    printf '%s\n' 'Install Docker Desktop or update scripts/docker.sh.' >&2
    exit 1
fi

exec "$docker_cli" "$@"

