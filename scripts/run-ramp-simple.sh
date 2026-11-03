#!/bin/sh
# The shared ramp of the 8-bit bottom-plate ADC re-derived as the simple
# current-source ramp (mixed_signal/ramp_simple): sizing, schematic, the ramp
# alone on an ideal current (the I/C source's place) and the real VR_LO
# reference, PVT, four cells converting on it.
#
#   ./scripts/sim.sh ramp-simple                     every phase
#   ./scripts/sim.sh ramp-simple PHASES='size check'
#
# The block's run.sh writes the console; this wrapper exists so the target has
# the one entry point CLAUDE.md requires (sim.sh owns the record).
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/ramp_simple"
TARGET=ramp-simple PHASES="${PHASES:-size schematic ramp pvt adc4 plot check}" \
    JOBS="${JOBS:-16}" NO_RECORD=1 ./run.sh
