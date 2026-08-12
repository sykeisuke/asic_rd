#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

mkdir -p "$PROJECT_ROOT/simulations/gf180_nmos_dc/work"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        cd /foss/designs/simulations/gf180_nmos_dc
        xschem -n -q -x \
            --rcfile /foss/pdks/gf180mcuD/libs.tech/xschem/xschemrc \
            -o work -N nmos_dc_xschem.spice nmos_dc.sch
        test -s work/nmos_dc_xschem.spice
        cd work
        ngspice -b nmos_dc_xschem.spice
        test -s nmos_dc.raw
        cd ..
        ngspice -b nmos_dc.spice
        test -s work/nmos_id_vds.csv
        printf "Result: %s rows\n" "$(wc -l < work/nmos_id_vds.csv)"
        sed -n "1,6p" work/nmos_id_vds.csv
    '
