#!/bin/sh
set -eu

# Docker Desktop does not always add its CLI directory to non-login shells.
if [ -d /Applications/Docker.app/Contents/Resources/bin ]; then
    PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    export PATH
fi

printf 'Architecture: '
uname -m
printf 'macOS: '
sw_vers -productVersion

for tool in git docker podman klayout ngspice xschem magic netgen nix; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf '%-10s %s\n' "$tool" "$(command -v "$tool")"
    else
        printf '%-10s %s\n' "$tool" 'not found'
    fi
done

if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        printf '%-10s %s\n' 'daemon' 'running'
    else
        printf '%-10s %s\n' 'daemon' 'not reachable (start Docker Desktop)'
    fi
fi
