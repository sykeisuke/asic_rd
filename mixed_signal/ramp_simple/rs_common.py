"""Shared by the ramp_simple scripts: the ADC grid, the load contract, the I/C
principle that sets the ramp current, the PDK model header, the ngspice runner.
Labels: [C] contract, [P] PDK, [M] measured, [A] assumed, [D] derived (SPEC.md).

The ramp cell is the capacitor (an array of the cells' 5 um unit MIM) and the
reset switch. Its current is an IDEAL source in every bench of this block
(user, 2026-10-28); the real source is the I/C current reference designed next
(../ic_source): I = C_UNIT x V_REF x F_CLK, one unit MIM switched at the 20 MHz
clock against a 5/33 AVDD tap, so that the slope is the unit-count ratio
1 / N_RAMP x V_REF x F_CLK and tracks the MIM over process and temperature.
"""
import os
import re
import subprocess

BLOCK = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(BLOCK, "ramp_simple.spice")
VRLO_REF = "/foss/designs/mixed_signal/vrlo_ref/vrlo_ref.spice"

# ---------------------------------------------------------------- the grid [C] / [D]
VDD = 3.3
LSB_OLD = 1.5 / 256                           # the grid before ADR 0025; the offsets below were measured / allocated in it [C]
OFS_MEAN, OFS_SIG = 2.1, 4.2                  # in-cell comparator code offset, worst corner (old LSB) [M, ADR 0015, comparator-updt-v3-lin]
VRLO_ERR, VRLO_SIG = 2.0, 1.0                 # vrlo_ref's systematic and mismatch allocations (old LSB) [A, ADR 0018 / vrlo_ref vr.py]
SIG3 = 3 * (OFS_SIG ** 2 + VRLO_SIG ** 2) ** 0.5   # 12.95 old LSB: comparator and reset-level mismatch, 3 sigma [D]
V_PREROLL = (SIG3 - OFS_MEAN + 0.5 + VRLO_ERR) * LSB_OLD   # 78.2 mV below 0.5 V [D, SPEC R2, ADR 0025]
V_OFS_TOP = (OFS_MEAN + SIG3 + VRLO_ERR) * LSB_OLD         # 99.9 mV above 2.0 V [D, SPEC R3, ADR 0025]
NVALID = 255                                  # codes 0..254; 255 = timeout [C, spec s.5.3]
SLOW = 0.982                                  # the slowest ramp against the grid [D, SPEC R3]
LSB = (V_PREROLL + 1.5 + V_OFS_TOP) / (NVALID * SLOW)   # 6.70 mV: 8-bit codes cover the whole window [U, D, ADR 0025]
TCOUNT = 50e-9
SLOPE = LSB / TCOUNT
F_CLK = 1.0 / TCOUNT                          # the one 20 MHz clock [C]
PREROLL = V_PREROLL / LSB                     # 11.7 LSB [D, SPEC R2]
K_LO = int(PREROLL)                           # 11: the first count of the conversion window on the pre-roll level [D]
NCNT = 256 + 3                                # the ramp ends at the controller's overflow + DRAIN_CYCLES [C, ADR 0025]
VR_LO_MACRO = 0.5                             # the macro's vrlo_ref level until integration (5/33 AVDD) [C]
VR_LO_PRE = 0.5 - V_PREROLL                   # the pre-roll level the budget asks for, 0.4218 V [D]
VRLO_TAP = 7.0 / 55.0                         # vrlo_ref's divider tap (48 : 7 units; ../vrlo_ref/vr.py N_TOP, N_BOT) [D, ADR 0025]
VR_LO_TAP = VDD * VRLO_TAP                    # 0.4200 V: what vrlo_ref makes, 1.8 mV under VR_LO_PRE [D]
V_NEED = 0.5 + 1.5 + V_OFS_TOP                # 2.100 V: the window's top + the offset margin, reached by count 255 [D, SPEC R3/R4]
V_TOP = VR_LO_TAP + NCNT * LSB                # 2.156 V at the end of the ramp [D]
S_SRC = 0.020                                 # the source's slowest current against the design current [A, SPEC R3]
ALPHA = 0.87                                  # the cell's plate divider C_S / (C_S + C_p) [P, SPEC R4]
# ---------------------------------------------------------------- the I/C principle [D]
V_REF = VDD * 5.0 / 33.0                      # the I/C source's reference: a 5/33 AVDD tap, 0.5 V (as VR_LO) [D]
C_UNIT_SIDE = 5e-6                            # the cells' unit MIM, 5 um square (cap_mim_2f0_m4m5_noshield) [C]
# ---------------------------------------------------------------- load and references
I_VRLO = 1.528e-6                             # vrlo_ref's bias from bias_gen_s's XOL [C, Analog_top]
NCELL = 4
C_CELL = 19e-15                               # average load per cell over a conversion [M, SPEC R7]
C_EQ_S1 = 20e-15                              # S1 charge per cell = C_EQ x (VIN - VR_LO) [A, vrlo_ref's model]
Q_KICK = 0.24e-15                             # per-decision charge on vramp [M, the macro's ramp_kick]

CORNERS = ("typical", "ss", "ff", "sf", "fs")
TEMPS = (0.0, 27.0, 85.0)
VDDS = (3.0, 3.3, 3.6)
MIMS = ("typical", "ss", "ff")

HEAD = """.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {corner}
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {rcorner}
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_{mim}
.temp {temp}
"""


def head(corner="typical", rcorner="res_typical", mim="typical", temp=27):
    return HEAD.format(corner=corner, rcorner=rcorner, mim=mim, temp=temp)


def design_current():
    """The ramp current the I/C source delivers at typical (C_UNIT x V_REF x F_CLK), from data/sizing.json."""
    import json
    return json.load(open(os.path.join(BLOCK, "data", "sizing.json")))["predicted"]["i_ramp_ua"] * 1e-6


def ng(d, deck, name="d.spice", timeout=1800):
    """Run ngspice on deck text in directory d (one OpenMP thread); return its console."""
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name), "w").write(deck)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    out = name.replace(".spice", ".out")
    env = dict(os.environ, OMP_NUM_THREADS="1")
    try:
        subprocess.run(["ngspice", "-b", "-o", out, name], cwd=d, env=env, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        return open(os.path.join(d, out), errors="replace").read()
    except (subprocess.TimeoutExpired, OSError):
        return ""


def grab(txt, key, default=None):
    m = re.search(r"^\s*%s\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)" % re.escape(key), txt, re.M)
    if m:
        return float(m.group(1))
    if default is not None:
        return default
    raise SystemExit("FAIL: no %s in the ngspice output\n%s" % (key, txt[-1500:]))
