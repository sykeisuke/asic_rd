#!/bin/sh
# comparator over PVT (45 cells, ngspice, the comparator and its core side by
# side), Monte
# Carlo at 7 corner cells (ngspice + VACASK), offset signal-independence at the
# same 7 cells, VACASK transient noise at typical and at the worst-noise PVT
# cell (mixed_signal/comparator/run-pvt.sh). Long: launch detached.
#
#   ./scripts/sim.sh comparator-pvt
#   ./scripts/sim.sh comparator-pvt PHASES='bench mc plot'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/comparator"
TARGET=comparator-pvt NO_RECORD=1 ./run-pvt.sh
