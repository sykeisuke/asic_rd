#!/bin/sh
# LVS for a gdsfactory-generated cell: Magic extraction of the GDS vs a
# schematic-side SPICE subcircuit, compared with Netgen using the frozen PDK setup.
# Usage: experiments/analog_layout/lvs.sh <gds relative to this dir> <topcell> <schematic .spice> 
# Example: experiments/analog_layout/lvs.sh work/sampling_cell_tg.gds sampling_cell_tg sampling_cell_tg_sch.spice
set -eu
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
. "$REPO_ROOT/scripts/eda-common.sh"
PROJECT_ROOT="$REPO_ROOT"
gds=${1:?gds}; top=${2:?topcell}; sch=${3:?schematic spice}
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc "
        set -euo pipefail
        cd /foss/designs/experiments/analog_layout
        mkdir -p work/lvs
        export PDK_ROOT=/foss/pdks PDK=gf180mcuD
        cat > work/lvs/extract.tcl <<TCL
gds flatglob *__*
gds read $gds
load $top
select top cell
extract path work/lvs
extract no all
extract all
ext2spice lvs
ext2spice -p work/lvs -o work/lvs/${top}_layout.spice
quit -noprompt
TCL
        magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc work/lvs/extract.tcl > work/lvs/magic.log 2>&1 || true
        test -s work/lvs/${top}_layout.spice
        echo '--- extracted layout netlist (head) ---'; { grep -vE '^\*|^\s*$' work/lvs/${top}_layout.spice || true; } | head -30 || true
        echo '--- netgen ---'
        netgen -batch lvs \"work/lvs/${top}_layout.spice $top\" \"$sch $top\" \
            /foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl work/lvs/${top}_lvs.report > work/lvs/netgen.log 2>&1 || true
        grep -E 'Circuits match|Netlists do not match|uniquely|Result|mismatch|Cell .* disconnected' work/lvs/${top}_lvs.report | head -20 || tail -20 work/lvs/netgen.log
    "
