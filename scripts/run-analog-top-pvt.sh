#!/bin/sh
# analog_top over PVT (mixed_signal/Analog_top, phase `pvt`): the functional
# record (func.sh's bench, measures, reducer, check-func.awk, all unchanged) at
# PVT cells, judged per cell and over the set by check-pvt.awk. Slow: ~1 h per
# cell (T0 60 us + the 13 us ramp), JOBS cells in parallel (default 6; ~0.2 GB
# each with the named .save list). The typical record is `analog-top`.
#
#   ./scripts/sim.sh analog-top-pvt                                  45 cells
#   ./scripts/sim.sh analog-top-pvt PVT_CELLS='ss_85_3.0 ff_0_3.6'   a subset
# A cell finished with an unchanged macro and bench is re-used (pvt_bench.py key).
set -eu

. "$(dirname -- "$0")/eda-common.sh"

cd "$PROJECT_ROOT/mixed_signal/Analog_top"
TARGET=analog-top-pvt NO_RECORD=1 JOBS="${JOBS:-6}" PVT_CELLS="${PVT_CELLS:-}" PHASES=pvt sh ./run.sh
