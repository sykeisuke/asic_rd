"""Shared constants of sample_seq, the on-chip sampling sequencer (SPEC.md).

One 20 MHz clock (ADR 0024) and the controller's `acquire` level in; the
twelve switch controls of the four bottom-plate cells out. Every number a
gate or the sizer uses lives here.
"""
import os

BLOCK = os.path.dirname(os.path.abspath(__file__))
CBLOCK = "/foss/designs/mixed_signal/sample_seq"
STD_LIB = "/foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice"
LIB = "gf180mcu_as_sc_mcu7t3v3"

VDD = 3.3
TCOUNT = 50e-9                  # one 20 MHz period: the cell spacing (ADR 0024)
NCELLS = 4

# Q2 [U] (user, 2026-10-30): S2 -> S0 and S0 -> S1 at least 5 ns apart.
GAP_MIN = 5.0e-9
# the sizer aims this far above GAP_MIN at the fastest PVT cell: the route
# and clock-tree skew of the layout are not in the bench [A]
GAP_MARGIN = 0.25e-9
# Q3 [A]: the top plate is isolated (S0 open) well before the input may move
# (the macro bench steps vin TSTEP = 20 ns after the sampling edge), and the
# whole sequence ends inside half a period
S0_OPEN_MAX = 15e-9
S2_S1_MAX = 25e-9
# Q4 [A]: the four sampling instants one period apart; the bench has no route
# skew, so the flops' own spread is the measure
SPACING_TOL = 0.05e-9
# Q5 [A]: sampling instant after the clock's rising edge (clock buffer + flop)
APERTURE_MAX = 2.0e-9

# the delay cell and its count per stage (size_seq.py writes the deck)
DLY_CELL = LIB + "__dlybuff_2"
N_PROBE = (8, 24)               # the size phase fits gap = a + b N per PVT cell

# load on every control net in the bench: atop_cell's input stage (its
# inverter, the switch gates) plus a route to a cell [A]
C_ROUTE = 20e-15

CORNERS = ["typical", "ff", "ss", "fs", "sf"]
TEMPS = [0, 27, 85]
VDDS = [3.0, 3.3, 3.6]
PVT = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]
DUTY_CELLS = [("typical", 27, 3.3), ("ff", 0, 3.6), ("ss", 85, 3.0)]
DUTIES = [0.3, 0.7]

SPICEINIT = "set num_threads=1\nset ngbehavior=hsa\nset ng_nomodcheck\n"
