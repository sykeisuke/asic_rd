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

# Q2 [U] (user, 2026-11-15, replaces the 5 ns of 2026-10-30): S2 -> S0,
# S0 -> S1 and re-entry S1 -> S0 non-overlapping by "a few 50 or 100 ps,
# ideally a four-inverter delay". Gate: every gap (VDD/2 crossings) >= the
# delay of the template's own four-inverter chain (n1 -> a1, four inv_4) in the
# same run, so the gate scales with the PVT cell. Q2b: the controls really do
# not overlap: the earlier switch is fully off (10 % / 90 % of VDD, the cell's
# own complement included) before the later one starts to move.
GAP_T4INV = 1.0
# the sizer aims this factor above the four-inverter delay: route skew and
# standard-cell mismatch are not in the bench [A]
GAP_MARGIN = 1.15
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

# the delay cell and its count per stage (size_seq.py writes the deck): an
# even number of inv_2 (non-inverting), at least 2
DLY_CELL = LIB + "__inv_2"
N_PROBE = (2, 6)                # the size phase fits gap = a + b N per PVT cell
N_MIN = 2

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
