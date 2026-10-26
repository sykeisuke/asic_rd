#!/bin/sh
# Chip floorplan (mixed_signal/chip_floorplan): Analog_top as a hard
# macro and asic_digital_top inside the wafer.space 1x0p5 pad ring, digital
# on top. Areas and placement only; no layout.
#
#   ./scripts/sim.sh chip-floorplan
#
# Needs `make pdk-libs` once (ocd_io pad cells). The block's run.sh writes
# the console; sim.sh owns the record.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/chip_floorplan"
TARGET=chip-floorplan NO_RECORD=1 ./run.sh
