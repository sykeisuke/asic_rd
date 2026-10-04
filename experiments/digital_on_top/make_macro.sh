#!/bin/sh
# Build the hard-macro views of the minimum comparator (experiments/analog_layout,
# cmp_min) for LibreLane digital-on-top integration:
#   macro/comparator_min.gds   layout (gdsfactory generator, DRC/LVS clean)
#   macro/comparator_min.lef   abstract: pins + obstructions (Magic "lef write -hide")
#   macro/comparator_min.lib   timing-less Liberty stub (pins only) for OpenSTA linking
#   macro/comparator_min.v     Verilog blackbox
#   macro/comparator_min.spice LVS reference subcircuit
set -eu
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
. "$REPO_ROOT/scripts/eda-common.sh"
PROJECT_ROOT="$REPO_ROOT"
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc '
        set -euo pipefail
        export PYTHONUSERBASE=/foss/designs/.eda-tools
        cd /foss/designs/experiments/analog_layout
        mkdir -p work
        python3 comparator.py min
        cd ../digital_on_top
        cp ../analog_layout/work/comparator_min.gds macro/comparator_min.gds
        cp ../analog_layout/comparator_min_sch.spice macro/comparator_min.spice
        klayout -b -r add_pr_boundary.py
        magic -dnull -noconsole -rcfile /foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc <<MAGIC >/dev/null 2>&1
gds read macro/comparator_min.gds
load comparator_min
select top cell
port makeall
lef write macro/comparator_min_raw -hide
quit
MAGIC
        python3 make_macro_views.py
        rm -f macro/comparator_min_raw.lef
        ls -la macro
    '
