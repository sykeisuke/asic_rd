#!/bin/sh
# comparator's xschem views: the schematic from the deck with its
# netlist-back check, the four testbench schematics with their renders, and
# xtb.py (every testbench netlisted by xschem, simulated, compared with its
# hand-written bench) (mixed_signal/comparator/schematic.sh).
#
#   ./scripts/sim.sh comparator-schematic
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/comparator"
TARGET=comparator-schematic ./schematic.sh
