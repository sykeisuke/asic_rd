#!/bin/sh
# vrlo_ref, the VR_LO (0.5 V = 5/33 AVDD) shunt regulator that sinks
# ramp_simple's reset current and absorbs its end-of-ramp dump and the cells'
# S1 charge (mixed_signal/vrlo_ref, 2026-10-09): ngspice verification of the
# selected design (op / tran / loop over PVT, the real ramp, noise, Monte
# Carlo), the xschem drawing, and the analog_top macro against the ideal source.
#
#   ./scripts/sim.sh vrlo-ref
#   ./scripts/sim.sh vrlo-ref PHASES='size verify schematic macro'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/vrlo_ref"
TARGET=vrlo-ref NO_RECORD=1 sh ./run.sh
