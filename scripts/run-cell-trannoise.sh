#!/bin/sh
# cell_trannoise: total transient noise of one Analog_top cell on
# ramp_simple_d (comparator_d, dfxtn_2 latch, real switches; ideal supplies,
# references, bias, controls and clock), VACASK, the input on a code transition
# so that noise alone decides Clk or Clk+1; per-block shares.
#
#   ./scripts/sim.sh cell-trannoise
#   ./scripts/sim.sh cell-trannoise STEPS=reduce
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/cell_trannoise"
TARGET=cell-trannoise NO_RECORD=1 sh ./run.sh
