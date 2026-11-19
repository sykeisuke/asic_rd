"""intent.py -- the design currents of comparator: the ONE source for every
current written on its drawings (comparator.sch, tb_*.sch, and any copy a
macro generator makes of comparator.sch).

comparator is comparator_core's ten sized devices plus one inverter
(XBUF5 / XBUF6, copies of XBUF3 / XBUF4). The ten devices carry the same
currents as there, so their allocation is intent_core.py's, read
at run time (never copied):

- sized at I_B = 1.93 uA into one tail finger: tail 20 uA, each pair / load
  branch 9.9 uA, starve 9.6 uA;
- in Analog_top bias_gen feeds 3.25 uA (1.68 x I_B, ADR 0017): every branch
  scales with it (tail 33, pair 16.5, starve 16 uA).

The two output inverters were not sized for a current. Their crowbar while
the cell tracks (plate = VREF: inp = inn) is drawn as ngspice gives it on the
drawing (intent_op.py, typical, 27 C): XBUF4 is the base's output inverter in
the same state, XBUF6 the added one. TOL is only a sanity bound that catches a
marker no longer describing the circuit.

For a generator that copies comparator.sch onto a macro sheet (as
../Analog_top/analog_top_sch.py copies this folder's comparator.sch):
  MARKER_XY   where each device current is written (find them by position)
  HEADINGS    the section headings (the whitelist of text to keep)
  NOTES       the two net notes next to inp / inn (keep or drop)
  NC_PORTS    the ipin labels of the not-connected ports (drop them)
  TITLE_XY, LAYOUT_XY  the title and the layout line (replace / drop)
"""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cmp_base_intent", HERE / "intent_core.py")
BASE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BASE)

I_B_UA = BASE.I_B_UA                    # 1.93 uA: the benches' ideal bias (one tail finger)
MACRO_I_B_UA = BASE.MACRO_I_B_UA        # 3.25 uA in Analog_top
K_MACRO = BASE.K_MACRO
TOL = BASE.TOL                          # sanity bound |ngspice / design - 1| (intent_op.py)

# ngspice on the drawing at inp = inn = VDD/2 (intent_op.py, data/intent_op.json),
# two significant figures; the crowbar of the two output inverters while tracking
XBUF_IB_UA = {"xbuf4": 5.3, "xbuf6": 0.0}       # at I_B 1.93 uA
XBUF_MACRO_UA = {"xbuf4": 37, "xbuf6": 0.0}     # at 3.25 uA

SIZED = BASE.SIZED                      # from the sizing record, data/sizing.json
INTENT_UA = {**{d: BASE.INTENT_UA[d] for d in SIZED}, **XBUF_IB_UA}
MACRO_UA = {**{d: BASE.MACRO_UA[d] for d in SIZED}, **XBUF_MACRO_UA}
TRACKING_ONLY = ("xbst", "xbuf4", "xbuf6")      # ~0 uA once dout has settled (converting)
CONVERTING_UA = MACRO_I_B_UA + MACRO_UA["xtail"]   # diode + tail: the static current while converting

# where comparator_sch.py writes each device's marker (the base's positions,
# plus XBUF6 on the added inverter); a device with no marker is drawn without one
MARKER_XY = {"xtail": (235, -850), "xbst": (615, -850), "xinp": (130, -630),
             "xinn": (625, -722), "xloadd": (150, -452), "xloadm": (600, -452),
             "xbuf4": (1100, -760), "xbuf6": (1320, -760)}
HEADINGS = ("PMOS 5T OTA", "starved inverter", "output inverters")
NOTES = ("(plate VBOT)", "(VREF, VDD/2)")
NC_PORTS = ("clk", "nbias")
TITLE_XY = (160, -1000)
LAYOUT_XY = (160, -950)


def ua(v):
    """33 -> '33 uA', 16.5 -> '16.5 uA'."""
    return "%g uA" % v


def marker(dev):
    """The text next to a device (the macro allocation; * = during tracking)."""
    return ua(MACRO_UA[dev]) + ("*" if dev in TRACKING_ONLY else "")


def drawn(dev):
    """A marker is drawn for every device with a design current above 0.1 uA."""
    return dev in MARKER_XY and MACRO_UA[dev] > 0.1
