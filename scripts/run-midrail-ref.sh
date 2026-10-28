#!/bin/sh
# midref, the VDD/2 reference of the 8-bit true bottom-plate cell with ONE
# output (mixed_signal/midrail_ref, 2026-10-13): midref_v2's divider and one
# buffer, its output both VREF and VBL. ngspice verification (PVT operating
# point and S2 kick, noise on the one node, decision with comparator on the
# shared node incl. a neighbour's kick during the hold, Monte Carlo of the
# output, schematic).
#
#   ./scripts/sim.sh midrail-ref
#   ./scripts/sim.sh midrail-ref VPHASES='op cmp'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/midrail_ref"
TARGET=midrail-ref NO_RECORD=1 sh ./run.sh
