"""Shared by the ic_source scripts: the ADC grid, the I/C principle, the ramp
contract this source feeds, the PDK model header, the gm/Id table reader, the
ngspice runner. Labels: [C] contract, [P] PDK, [M] measured, [A] assumed,
[D] derived (SPEC.md).

The I/C current source: one unit MIM (the cells' 5 um square) switched at the
20 MHz count clock between a regulated node and ground draws, on average,
I = C_UNIT x V_REF x F_CLK from that node; a folded-cascode OTA holds the node
at V_REF (a 5/33 AVDD divider tap) through a degenerated, cascoded PMOS pass
device, and a matched pass device delivers the same current to the ramp
(../ramp_simple: 83 unit MIMs, so the slope is V_REF x F_CLK / 83 and tracks
the MIM over process and temperature). No resistor, no transistor current
and no beta multiplier enters the slope.
"""
import json
import os
import re
import subprocess

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
NETLIST = os.path.join(BLOCK, "ic_source.spice")
RAMP_SIZING = os.path.join(BLOCK, "..", "ramp_simple", "data", "sizing.json")
STD_LIB = "/foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice"

# ---------------------------------------------------------------- the grid [C] / [D]
VDD = 3.3
LSB = 1.5 / 256                               # the unit this block's allocations are written in (5.86 mV, the grid
                                              # before ADR 0025; the ramp's LSB is now 6.70 mV, allocations kept in volts)
TCOUNT = 50e-9
F_CLK = 1.0 / TCOUNT                          # the one 20 MHz clock [C]
SLOPE = LSB / TCOUNT
NCNT = 256 + 20                               # the noise kernel's length, 13.8 us (the ramp now ends at 259: conservative) [D]
T_RAMP = NCNT * TCOUNT                        # 13.8 us of integration [D]
_GRID = json.load(open(RAMP_SIZING))["grid"]
V_RAMP_LO = _GRID["vr_lo"]                    # the ramp's reset level, vrlo_ref's 7/55 tap, 0.420 V [C, ramp_simple R2, ADR 0025]
V_RAMP_HI = _GRID["v_top"]                    # the ramp's end, count 259, 2.156 V [C, ramp_simple R4]
# ---------------------------------------------------------------- the I/C principle [D]
RATIO_REF = 5.0 / 33.0                        # V_REF = 5/33 AVDD = 0.5 V (as VR_LO) [D]
V_REF = VDD * RATIO_REF
N_DIV = 33                                    # divider units [D]
C_UNIT_SIDE = 5e-6                            # the cells' unit MIM, 5 um square [C]
# ---------------------------------------------------------------- the ramp contract (ramp_simple SPEC s.6)
I_BIAS = 3.25e-6                              # bias_gen's ramp sink, into this block's diode [C, Analog_top]
ROUT_MIN_GOHM = 2.0                           # 0.05 LSB bow at the typical cell [C, ramp_simple R6]
ROUT_MIN_PVT_GOHM = 0.63                      # 0.15 LSB bow at every PVT cell [C]
NOISE_MAX_LSB = 0.11                          # at code 255, from 1 Hz, by the ramp's kernel [C, ADR 0013]
I_TOL_TYP_PCT = 1.5                           # |I - C V f| at typical, after the design centre [A]
I_TOL_PVT_PCT = 1.0                           # ratiometric deviation over PVT [A]
I_TOL_MC_3SIG_PCT = 1.5                       # mismatch, 3 sigma [A]
DUTY_SENS_MAX = 0.2                           # % of I per % of clock duty [A]
RIPPLE_MAX_LSB = 0.05                         # 20 MHz ripple at the ramp node [C]
PM_MIN_DEG = 60.0                             # loop phase margin [A]
T_START_MAX = 60e-6               # R7: settled within 1 % after a cold supply [U] (silicon is powered for ms before a record; the benches wait this long)
POWER_MAX_UW = 60.0                           # AVDD + DVDD, incl. the 3.25 uA bias diode [A]

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


def resc(c):
    return {"ff": "res_ff", "ss": "res_ss"}.get(c, "res_typical")


def mimc(c):
    return c if c in ("ff", "ss") else "typical"


def head(corner="typical", rcorner="res_typical", mim="typical", temp=27, std=False, mc=False):
    h = HEAD.format(corner=corner, rcorner=rcorner, mim=mim, temp=temp)
    if mc:
        h += ".param sw_stat_mismatch=1\n"
    if std:
        h += ".include %s\n" % STD_LIB
    return h


def ramp_contract():
    """C_total of the ramp this source feeds (for the noise kernel), from ../ramp_simple's sizing record."""
    s = json.load(open(RAMP_SIZING))["predicted"]
    return dict(c_total=s["c_total_pf"] * 1e-12, i_ramp=s["i_ramp_ua"] * 1e-6, n_ramp=s["n_ramp_units"])


def sizing():
    return json.load(open(os.path.join(BLOCK, "data", "sizing.json")))


def res_unit(rcorner="res_typical", temp=27, rtype="ppolyf_u_3k"):
    """Ohms of one 1 x 20 um strip from data/res_char.csv (ohm/sq x 20)."""
    rows = list(open(os.path.join(BLOCK, "data", "res_char.csv")))
    keys = rows[0].strip().split(",")
    for line in rows[1:]:
        r = dict(zip(keys, line.strip().split(",")))
        if r["corner"] == rcorner and float(r["temp"]) == temp:
            return 20.0 * float(r[rtype])
    raise SystemExit("FAIL: no %s/%g row in data/res_char.csv" % (rcorner, temp))


class Table:
    """gm/Id table of one flavour (work/lut/<dev>.npz, lut/build.sh): [L, W, VSB, VDS, VGS]."""

    def __init__(self, dev):
        t = np.load(os.path.join(BLOCK, "work", "lut", "%s.npz" % dev))
        self.L, self.W, self.VSB, self.VDS, self.VGS = t["L"], t["W"], t["VSB"], t["VDS"], t["VGS"]
        self.t = {k: t[k] for k in ("id", "gm", "gds", "vth", "vdsat")}

    def _iw(self, L, wf):
        return int(np.argmin(abs(self.L - L * 1e-6))), int(np.argmin(abs(self.W - wf * 1e-6)))

    def at(self, key, L, wf, vgs, vds, vsb=0.0):
        il, iw = self._iw(L, wf)
        fb = float(np.clip(vsb / self.VSB[-1], 0.0, 1.0))
        j = int(np.clip(np.searchsorted(self.VDS, vds) - 1, 0, len(self.VDS) - 2))
        wd = float(np.clip((vds - self.VDS[j]) / (self.VDS[j + 1] - self.VDS[j]), 0.0, 1.0))
        out = 0.0
        for ib, wgt in ((0, 1.0 - fb), (1, fb)):
            a = self.t[key][il, iw, ib]
            col = a[j] * (1.0 - wd) + a[j + 1] * wd
            out += wgt * float(np.interp(vgs, self.VGS, col))
        return out

    def vgs_for(self, L, wf, i_f, vds, vsb=0.0):
        """VGS of one finger carrying i_f at vds (bisection on the 10 mV grid)."""
        lo, hi = 0.0, 2.2
        for _ in range(40):
            v = 0.5 * (lo + hi)
            if self.at("id", L, wf, v, vds, vsb) < i_f:
                lo = v
            else:
                hi = v
        return 0.5 * (lo + hi)


# Pelgrom pair coefficients, the PDK's mismatch model (as bias_gen reads them) [P]
PDK_MM = dict(pfet=dict(par_vth=0.00666, par_k=0.002833), nfet=dict(par_vth=0.007148, par_k=0.007008),
              par_l=0.15e-6, par_w=-0.1e-6)


def sig_dvt(flav, L, wf, nf):
    """sigma(dVt) between two devices of nf fingers each (Pelgrom, PDK pair coefficient)."""
    leff = max(L * 1e-6 - PDK_MM["par_l"], 0.05e-6)
    weff = wf * 1e-6 - PDK_MM["par_w"]
    return PDK_MM[flav]["par_vth"] * 1e-6 / np.sqrt(leff * weff) / np.sqrt(nf)


def ng(d, deck, name="d.spice", timeout=3600):
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
    m = re.search(r"^\s*%s\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)" % re.escape(key), txt, re.M | re.I)
    if m:
        return float(m.group(1))
    if default is not None:
        return default
    raise SystemExit("FAIL: no %s in the ngspice output\n%s" % (key, txt[-1500:]))


def um(x):
    return "%.3fu" % (x * 1e6)
