#!/bin/sh
# comparator over PVT (45 cells, ngspice), Monte Carlo at 7 corner cells
# (ngspice + VACASK), VACASK transient noise at typical and at the worst-noise
# PVT cell (mixed_signal/comparator/run-pvt.sh).
#
#   ./scripts/sim.sh comparator-pvt
#   ./scripts/sim.sh comparator-pvt PHASES='bench mc plot'
#   ./scripts/sim.sh comparator-pvt DUT_GEOM=1 PHASES='bench plot'   (drawn S/D geometry)
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/comparator"
TARGET=comparator-pvt NO_RECORD=1 ./run-pvt.sh
