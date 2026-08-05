#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:ro" \
    "$EDA_IMAGE" -lc '
        cd /foss/designs
        . ./.designinit
        test "$PDK" = gf180mcuD
        test -d "$PDKPATH"
        printf "PDK=%s\nPDKPATH=%s\n" "$PDK" "$PDKPATH"
        xschem --version | head -1
        ngspice --version | sed -n "2p"
        klayout -v
        magic --version
        netgen -batch </dev/null 2>&1 | head -1 || true
    '

