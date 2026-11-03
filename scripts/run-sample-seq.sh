#!/bin/sh
# The on-chip sampling sequencer of the bottom-plate cells
# (mixed_signal/sample_seq): S2 / S0 / S1 of the four cells from the 20 MHz
# clock and the controller's acquire level, >= 5 ns between phases. Sizing of
# the delay line over 45 PVT cells, schematic, typical, PVT, clock duty.
#
#   ./scripts/sim.sh sample-seq
#   ./scripts/sim.sh sample-seq PHASES='typ check'
#
# Needs `make pdk` (the frozen standard cells). The block's run.sh writes the
# console; sim.sh owns the record.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/sample_seq"
TARGET=sample-seq PHASES="${PHASES:-size schematic typ pvt duty check}" JOBS="${JOBS:-16}" NO_RECORD=1 ./run.sh
