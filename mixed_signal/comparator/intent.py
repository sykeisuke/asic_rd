"""intent.py -- the design currents of comparator: the ONE source for every
current written on the drawings (comparator.sch, tb_*.sch, the copies in
../Analog_top and the CPAD slide).

They are the numbers the design was chosen with, not simulation readings:

- the comparator was sized (size_v3.py, data/sizing.json) at I_B = iref
  1.93 uA into its 1 um / 0.28 um reference finger: tail i_tail 19.7 uA, each
  pair / load branch id_branch 9.9 uA, starve i_st 9.6 uA;
- in Analog_top bias_gen feeds it 1.68 x I_B = 3.25 uA by design: its
  8-finger sink was sized for the comparator's worst PVT cell, untrimmed
  (../bias_gen/data/sizing.json s_c, ADR 0017). The branches scale with it.

Drawn values are rounded to two figures (the pair is half the tail). ngspice
on the drawing (intent_op.py) gives less in the tail and the pair: at L 0.28 um
the tail sits at a lower V_SD than the sizing model took and channel-length
modulation copies ~9 x I_B, not the model's 10.2 x. That deviation is reported,
not designed in; TOL is only a sanity bound that catches a marker no longer
describing the circuit.

The output inverter was not sized for a current. Its tracking crowbar is
drawn as ngspice gives it at each bias (intent_op.py, trip point, typical).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SZ = json.loads((HERE / "data" / "sizing.json").read_text())
BG = json.loads((HERE / ".." / "bias_gen" / "data" / "sizing.json").read_text())

I_B_UA = round(SZ["iref"] * 1e6, 2)               # 1.93 uA: the sizing bias
I_CMP_NOM_UA = 1.931                               # bias_gen/bg.py I_CMP_NOM: s_c is relative to it
MACRO_I_B_UA = round(BG["s_c"] * I_CMP_NOM_UA, 2)  # 3.25 uA in Analog_top (8-finger sink, 1.681 x 1.931)
K_MACRO = MACRO_I_B_UA / I_B_UA                    # the branches scale with the bias
TOL = 0.20                                         # sanity bound |ngspice / design - 1| (intent_op.py)


def _two(v):
    """Two significant figures: 19.73 -> 20, 33.16 -> 33, 9.626 -> 9.6."""
    return float("%.2g" % v)


def _alloc(k, xbuf4):
    tail = _two(SZ["i_tail"] * 1e6 * k)
    return {"xtail": tail, "xinp": tail / 2, "xinn": tail / 2, "xloadd": tail / 2, "xloadm": tail / 2,
            "xbst": _two(SZ["i_st"] * 1e6 * k),    # starved inverter: tracking only
            "xbuf4": xbuf4}                        # output inverter crowbar: tracking only (ngspice)


INTENT_UA = _alloc(1.0, 5.3)                       # at I_B 1.93 uA: the testbenches' bias
MACRO_UA = _alloc(K_MACRO, 37)                     # at 3.25 uA: drawn on every sheet and slide
SIZED = ("xtail", "xinp", "xinn", "xloadd", "xloadm", "xbst")   # from the sizing record
TRACKING_ONLY = ("xbst", "xbuf4")                  # ~0 uA once dout has settled (converting)
CONVERTING_UA = MACRO_I_B_UA + MACRO_UA["xtail"]   # diode + tail: the static current while converting

# where comparator_sch.py writes each device's marker (the copy in
# ../Analog_top finds them by these coordinates)
MARKER_XY = {"xtail": (235, -850), "xbst": (615, -850), "xinp": (130, -630),
             "xinn": (625, -722), "xloadd": (150, -452), "xloadm": (600, -452),
             "xbuf4": (1100, -760)}


def ua(v):
    """33 -> '33 uA', 16.5 -> '16.5 uA'."""
    return ("%g uA" % v)


def marker(dev):
    """The text next to a device (the macro allocation; * = during tracking)."""
    return ua(MACRO_UA[dev]) + ("*" if dev in TRACKING_ONLY else "")
