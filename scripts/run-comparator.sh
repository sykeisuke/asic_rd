#!/bin/sh
# comparator, the comparator of the 8-bit true bottom-plate unit cell re-sized
# with every L <= 0.36 um (mixed_signal/comparator, 2026-10-06):
# short-L gm/Id tables, then ngspice verification of the selected design
# (delay from the static trip over four levels, dout fall into 10 fF, noise at
# the pins, Monte Carlo sigma(Vos)).
#
#   ./scripts/sim.sh comparator
#   ./scripts/sim.sh comparator PHASES='lut size verify'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/comparator"
TARGET=comparator NO_RECORD=1 ./run.sh
