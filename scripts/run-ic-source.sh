#!/bin/sh
# The I/C (switched-capacitor) current source of the 8-bit ADC's ramp
# (mixed_signal/ic_source): sizing, schematic, the typical cell (current,
# headroom, output resistance, clock duty, supply, MIM corners), loop phase
# margin, noise through the ramp's kernel, 45 PVT cells, mismatch Monte Carlo.
#
#   ./scripts/sim.sh ic-source                     every phase (~30 min)
#   ./scripts/sim.sh ic-source PHASES='size op check'
#
# The block's run.sh writes the console; this wrapper exists so the target has
# the one entry point CLAUDE.md requires (sim.sh owns the record).
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/ic_source"
TARGET=ic-source PHASES="${PHASES:-size schematic op loop noise pvt mc plot check}" \
    JOBS="${JOBS:-16}" NMC="${NMC:-100}" NO_RECORD=1 ./run.sh
