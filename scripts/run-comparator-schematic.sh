#!/bin/sh
# comparator's xschem views: the cell drawing and symbol from the deck with
# their netlist-back check (device for device, device order, ports in order),
# the drawn currents against ngspice, the four testbench schematics with their
# renders, and xtb.py (every testbench equal to its bench template and
# reproducing the bench record) (mixed_signal/comparator/schematic.sh).
#
#   ./scripts/sim.sh comparator-schematic
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/comparator"
./schematic.sh
