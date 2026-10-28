#!/bin/sh
# The shared ramp generator of the 8-bit bottom-plate single-slope ADC
# (mixed_signal/ramp_gen): sizing, schematic, ramp, loop gain, noise
# breakdown, four unit cells converting on it.
#
#   ./scripts/sim.sh ramp-gen                     every phase
#   ./scripts/sim.sh ramp-gen PHASES='ramp check'
#
# The block's run.sh writes the console; this wrapper exists so the target has
# the one entry point CLAUDE.md requires (sim.sh owns the record).
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/ramp_gen"
TARGET=ramp-gen PHASES="${PHASES:-size schematic ramp loop noise trannoise adc4 simple compare plot check}" \
    JOBS="${JOBS:-16}" NO_RECORD=1 ./run.sh
