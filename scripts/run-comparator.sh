#!/bin/sh
# comparator: the cell comparator (mixed_signal/comparator) -- the sized core
# comparator_core (10 devices) plus one output inverter (derive.py), used with
# the floating plate on inp and VREF on inn; dout falls at the decision.
# Typical delay / polarity / noise / MC, offset signal-independence and the bias
# requirement, side by side with the core in its sizing hookup (plate on inn).
#
#   ./scripts/sim.sh comparator
#   ./scripts/sim.sh comparator PHASES='derive verify'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/comparator"
TARGET=comparator NO_RECORD=1 ./run.sh
