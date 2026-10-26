#!/bin/sh
# analog_top v5, the analog macro of the 8-bit bottom-plate ADC with ONE VDD/2
# buffer (mixed_signal/Analog_top, 2026-10-13): Analog_top_v4 with the
# second midref_buf (XVBL) and its bias output (XBG.XOB) removed; the output of
# XVREF drives every cell's S2 level and comparator inp (midrail_ref,
# ADR 0021). Schematic netlist-back + equivalence to v4, one functional record,
# the operating point, the xschem testbench reproducing func, the power
# breakdown.
#
#   ./scripts/sim.sh analog-top
#   ./scripts/sim.sh analog-top PHASES='func'
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/Analog_top"
TARGET=analog-top NO_RECORD=1 PHASES="${PHASES:-schematic func op xtb pwr}" sh ./run.sh
