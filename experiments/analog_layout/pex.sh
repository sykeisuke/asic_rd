#!/bin/sh
# Parasitic extraction (Magic, R + C) of a gdsfactory cell and a pre- vs post-layout
# ngspice comparison of the sampling-cell measures.
# Usage: experiments/analog_layout/pex.sh   (sampling cell; extend for other cells)
set -eu
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
. "$REPO_ROOT/scripts/eda-common.sh"
PROJECT_ROOT="$REPO_ROOT"
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/experiments/analog_layout
        mkdir -p work/pex
        cat > work/pex/pex.tcl <<TCL
gds read work/sampling_cell_tg.gds
load sampling_cell_tg
select top cell
extract path work/pex
extract do capacitance
extract do coupling
extract do resistance
extract all
ext2spice subcircuit top on
ext2spice cthresh 0 rthresh 0
ext2spice extresist on
extresist all
ext2spice -p work/pex -o work/pex/sampling_cell_tg_pex.spice
quit -noprompt
TCL
        export PDK_ROOT=/foss/pdks PDK=gf180mcuD
        magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc work/pex/pex.tcl > work/pex/magic.log 2>&1 || true
        cd work/pex
        # Magic writes MIM plate dimensions in its internal units; the PDK model wants lengths.
        sed -E "s/c_width=([0-9.]+) c_length=([0-9.]+)/c_width=22.4u c_length=22.4u/" sampling_cell_tg_pex.spice > sampling_cell_tg_pex_sim.spice
        cp ../../pex_tb_common.inc tb_common.inc
        cat > tb_pre.spice <<SP
* pre-layout: schematic devices (transmission_gate.spice)
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include tb_common.inc
XSWN in sample hold 0 nfet_03v3 L=0.28u W=10u nf=10 m=1
XSWP in sample_b hold vdd pfet_03v3 L=0.28u W=20u nf=10 m=1
CHOLD hold 0 1p
.control
run
quit
.endc
.end
SP
        cat > tb_pex.spice <<SP
* post-layout: Magic-extracted sampling cell with parasitic R and C (MIM-B model cap)
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include tb_common.inc
.include sampling_cell_tg_pex_sim.spice
XCELL sample sample_b in hold 0 vdd sampling_cell_tg
.control
run
quit
.endc
.end
SP
        echo "parasitics: C=$(grep -cE "^C[0-9]" sampling_cell_tg_pex_sim.spice) R=$(grep -cE "^R[0-9]" sampling_cell_tg_pex_sim.spice)"
        for tb in pre pex; do
            ngspice -b tb_$tb.spice > run_$tb.log 2>&1
            printf "%-4s " $tb; grep -E "^(acquisition_error|clock_feedthrough|hold_droop)\s" run_$tb.log | sort -u | awk "{printf \"%s=%s  \", \$1, \$3}"; echo
        done
    '
