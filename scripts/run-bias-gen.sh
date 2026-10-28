#!/bin/sh
# bias_gen, the constant-gm bias generator of the 8-bit bottom-plate ADC
# re-sized with every L below 1 um (mixed_signal/bias_gen, 2026-10-08):
# gm/Id tables + Pelgrom matching, 135-cell ngspice sizing, current outputs to
# the four comparator, the ramp and the two midref_v2 buffers; verification
# (PVT, startup, Monte Carlo, ramp noise, consumers on the real bias,
# crosstalk), common-centroid row floorplan, schematic.
#
#   ./scripts/sim.sh bias-gen
#   ./scripts/sim.sh bias-gen PHASES='lut size verify floorplan schematic'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/bias_gen"
TARGET=bias-gen NO_RECORD=1 sh ./run.sh
