#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

mkdir -p "$PROJECT_ROOT/simulations/gf180_nmos_width_experiment/work"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_nmos_width_experiment
        # xschem returns 10 in batch netlist mode even on success; the
        # test -s below is the real check.
        xschem -n -q -x \
            --rcfile /foss/pdks/gf180mcuD/libs.tech/xschem/xschemrc \
            -o work -N nmos_dc_xschem.spice nmos_dc.sch || true
        test -s work/nmos_dc_xschem.spice
        grep -q "W=5u" work/nmos_dc_xschem.spice
        grep -q "W=5u" nmos_dc.spice
        cd work
        ngspice -b nmos_dc_xschem.spice
        test -s nmos_dc.raw
        cd ..
        ngspice -b nmos_dc.spice
        test -s work/nmos_id_vds.csv
        printf "Result: %s rows\n" "$(wc -l < work/nmos_id_vds.csv)"
        printf "Peak drain current: %s A\n" \
            "$(awk "NR>1 && \$2>m {m=\$2} END {print m}" work/nmos_id_vds.csv)"
    '
