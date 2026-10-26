#!/bin/sh
# The clocked latch after comparator from the frozen standard-cell library
# (mixed_signal/latch): gf180mcu_as_sc_mcu7t3v3__dfxtn_2. Buffer
# exploration, drive into 50 fF, clock edge, aperture, in-cell kick, schematic.
#
#   ./scripts/sim.sh latch
#   ./scripts/sim.sh latch PHASES='drive aperture check'
#
# Needs `make pdk-libs` once. The block's run.sh writes the console; sim.sh
# owns the record.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/latch"
TARGET=latch NO_RECORD=1 ./run.sh
