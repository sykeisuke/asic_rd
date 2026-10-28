"""Sizing of midref_v2: the FVF class-AB VDD/2 buffer of ../midrail_ref_bkp/midrail_ref
(VREF and VBL of the 8-bit true bottom-plate cell) re-sized on 2026-10-07 with
the method of ../comparator:

  1. every L in {0.28, 0.30, 0.32, 0.34, 0.36} um (user: short L, area)
  2. one finger width per flavour in {0.5, 1, 2} um, whole fingers (user: rows)
  3. gm/Id targets drawn per device class and rounded to whole fingers; gm/Id
     then FOLLOWS from (W, L, I) through the short-L tables (user)
  4. the divider and its tap capacitor are design variables (user), and so
     is the output decoupling capacitor (it is most of the area)
  5. bias: an IDEAL current into one diode-connected NMOS bias finger, its
     current density a variable (user; the generator is designed later)
  6. VBL - VREF offset is a pedestal (user): gated on a range bound only;
     noise and settling stay hard gates
  7. power and area both minimised: the knee of the power x area front

    ./container.sh 'python3 size_v2.py'              stage A (tables) + front
    ./container.sh 'PHASE=B python3 size_v2.py'      + ngspice on front points
    ./container.sh 'PHASE=B SIZING_EMIT=1 python3 size_v2.py'   + write midref_v2.spice

Labels in comments: [U] user, [C] contract (../Analog_top_bkp/unit_cell_bps/CONTRACT.md),
[B] noise budget (../Analog_top_bkp/unit_cell_noise/NOISE_BUDGET.md), [M] measured (run
named), [P] PDK, [D] derived, [A] assumed. The simulator decides; stage A
only screens.
"""
import csv
import json
import os
import pickle
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
np.seterr(divide="ignore", invalid="ignore")
from scipy.interpolate import RegularGridInterpolator as RGI

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
DATA = os.path.join(BLOCK, "data")

# ------------------------------------------------------------ 1  requirements
VDD = 3.3
VDD_SET = (3.0, 3.3, 3.6)                      # [C] +/-10 % supply
LSB = 1.5 / 256                                # [C] 5.859 mV
ALPHA = 0.761                                  # [M] comparator in the cell (its header)
EPS = LSB / 2                                  # [C] VREF back within 1/2 LSB
TS_MAX = 250e-9                                # [C] 300 ns to TS minus 50 ns kept
Q_KICK = 82e-15                                # [M] ../midrail_ref_bkp/midrail_ref README: one cell's S2 charge
NOISE_MAX_LSB = 0.080                          # [B] item 6, VREF + VBL at the ADC input
F_LO, F_HI = 10.0, 1e9                         # [B] the band of the 0.058 LSB bound
T_DEC = (0.1e-6, 12.9e-6)                      # [C] decision after TS: TR - TS .. TE - TS
F_CMP = 22.3373e6                              # [M] comparator OTA pole (its data/sizing.json, ngspice):
#   VBL is seen through it at the decision; VREF is sampled through S2 (~500 MHz) in full [B s.4.6]
SIGMA_DIFF_MAX_LSB = 2.0                       # [A] VBL - VREF pedestal spread (see README)
VERR_MAX = 0.050                               # [A] |VDD/2 error| over PVT. Identical in VREF and VBL (same
#   design, same corner), so it cancels in the code; it only moves the comparator's common mode
#   (comparator holds its state over inn 0.15-3.27 V) and the S2 operating point
HR_MARGIN = float(os.environ.get("HR_SCREEN", "0.0"))     # table screen after the calibrated offset HR_CAL
HR_SIGMAS = float(os.environ.get("HR_SIGMAS", "0"))   # follower headroom reserved for Vt mismatch, in sigma
#   of follower + shunt (PDK Pelgrom). 3 was tried on 2026-10-07: 20 of 60000 uniform samples pass that
#   gate and none passes all gates, so the gate is the original block's (saturated at every PVT cell,
#   nominal) and verify_v2.py measures what mismatch does at the window's extremes instead (mchr)
BIAS_LO, BIAS_HI = 0.69, 1.77                  # [M] ../bias_gen_bkp/bias_gen PVT current span
KT = 1.380649e-23 * 300.0
L_CHOICES = np.array([0.28, 0.30, 0.32, 0.34, 0.36])   # [U]
W_F_CHOICES = np.array([0.5e-6, 1.0e-6, 2.0e-6])        # [U]
NF_F_MAX, NF_S_MAX, NF_B_MAX, K_MAX = 64, 48, 100, 6   # [U] nf_in 1-64 (followers), nf_ld 1-48 (shunts), 1-100 (bias)
NF_INST = 50                                   # [A] fingers per instance; above it m copies (model bins)
# area [P]: MOS footprint from gf180mcu.drc contact rules (as ../comparator)
SD_SHARED, SD_END = 0.52, 0.44
# ppolyf_u_3k [P]: rsh 3000 ohm/sq, r_dw 0.02256 um, r_dl -0.0932 um (sm141064);
# HRES.2 width >= 1 um, HRES.3 space 0.4 um -> 1.4 um pitch per folded strip
RSH, R_W, R_DW, R_DL, R_PITCH = 3000.0, 1.0e-6, 0.02256e-6, -0.0932e-6, 1.4
MIM_DENS = 2.0e-15                             # [P] cap_mim_2f0: 2 fF/um2
PDK_MM = dict(pfet=0.00666, nfet=0.007148, par_l=0.15e-6, par_w=-0.1e-6)  # [P] fets_mm (as v3)
_CAL_PATH = os.path.join(DATA, "calibration.json")
_CAL = json.load(open(_CAL_PATH)) if os.environ.get("USE_CAL", "1") == "1" and os.path.exists(_CAL_PATH) else {}
NOISE_CAL = float(_CAL.get("noise_cal", 1.0))     # ngspice / table, PHASE=CAL median
HR_CAL = float(_CAL.get("hr_cal", 0.0))           # ngspice PVT minimum - table screen minimum, PHASE=CAL median
JOBS = int(os.environ.get("JOBS", "12"))
LUT_DIR = os.path.join(WORK, "lut")
SEED = int(os.environ.get("SEED", "20261007"))


# ------------------------------------------------------------ device tables
class Dev:
    """Short-L table of one flavour (lut/build.sh): forward lookups on
    (L, VGS, VDS, VSB) and an inverse VGS(L, VDS, VSB, ln ID/W)."""

    def __init__(self, name):
        t = pickle.load(open(os.path.join(LUT_DIR, f"{name}.pkl"), "rb"))
        self.name = name
        self.ax = (t["L"], t["VGS"], t["VDS"], t["VSB"])
        w = t["W"]
        idw = np.maximum(t["ID"] / w, 1e-20)
        gm = t["GM"]
        self.f = {
            "lnI": RGI(self.ax, np.log(idw), bounds_error=False, fill_value=np.nan),
            "gmid": RGI(self.ax, gm / np.maximum(t["ID"], 1e-20), bounds_error=False, fill_value=np.nan),
            "cgg": RGI(self.ax, t["CGG"] / w, bounds_error=False, fill_value=np.nan),
            "cdd": RGI(self.ax, t["CDD"] / w, bounds_error=False, fill_value=np.nan),
        }
        self.lng = np.linspace(np.log(1e-6), np.log(300.0), 220)
        L, vg, vd, vb = self.ax
        inv = np.full((L.size, vd.size, vb.size, self.lng.size), np.nan)
        for i in range(L.size):
            for j in range(vd.size):
                for k in range(vb.size):
                    li = np.maximum.accumulate(np.log(idw[i, :, j, k]))
                    ok = np.concatenate(([True], np.diff(li) > 1e-9))
                    inv[i, j, k] = np.interp(self.lng, li[ok], vg[ok], left=np.nan, right=np.nan)
        self.inv = RGI((L, vd, vb, self.lng), inv, bounds_error=False, fill_value=np.nan)

    @staticmethod
    def _c(x, lo, hi):
        return np.clip(x, lo, hi)

    def vgs(self, idw, L, vds, vsb):
        return self.inv(np.stack([L, self._c(vds, 0.0, 3.3), self._c(vsb, 0.0, 1.2),
                                  np.log(np.maximum(idw, 1e-30))], -1))

    def diode_vgs(self, idw, L, vsb):
        v = np.full(np.shape(idw), 1.0)
        for _ in range(5):
            v = self.vgs(idw, L, v, vsb)
        return v

    def at(self, key, L, vgs, vds, vsb):
        x = np.stack([L, self._c(vgs, 0.0, 3.3), self._c(vds, 0.0, 3.3), self._c(vsb, 0.0, 1.2)], -1)
        r = self.f[key](x)
        return np.exp(r) if key == "lnI" else r

    def idw_from_gmid(self, gmid, L, vds, vsb):
        """ID/W of a device at a gm/Id target (strong-side branch), fixed VDS, VSB."""
        out = np.full(gmid.shape, np.nan)
        vg = np.arange(0.2, 2.6, 0.01)
        for lv in np.unique(L):
            m = L == lv
            x = np.stack([np.full(vg.size, lv), vg, np.full(vg.size, vds), np.full(vg.size, vsb)], -1)
            g = self.f["gmid"](x)
            i = np.exp(self.f["lnI"](x))
            k = int(np.nanargmax(g))
            gg, ii = g[k:][::-1], i[k:][::-1]          # gm/Id rising with falling VGS
            out[m] = np.interp(gmid[m], gg, ii, left=np.nan, right=np.nan)
        return out


class Noise:
    """Gate-referred noise per (flavour, L, gm/Id), as ../comparator:
    S(f) = A (f/1k)^-af + B; A stored per unit gate area, B as gamma."""

    def __init__(self, path):
        rows = list(csv.DictReader(open(path)))
        self.t = {}
        for dev in ("nfet", "pfet"):
            for L in L_CHOICES:
                r = [x for x in rows if x["dev"] == dev and abs(float(x["l_um"]) * 1e6 - L) < 1e-3]
                g = np.array([float(x["gm"]) / float(x["id"]) for x in r])
                gm = np.array([float(x["gm"]) for x in r])
                s = np.array([[float(x[k]) ** 2 for k in ("s1k", "s10k", "s100k", "s1m", "s10m", "s100m", "s1g")]
                              for x in r])
                af = np.clip(np.log10(s[:, 0] / s[:, 1]), 0.7, 1.3)
                a = s[:, 0] - s[:, 5]
                b = np.maximum(s[:, 5] - a * 1e-5 ** af, 0.3 * s[:, 5])
                gamma = b * gm / (4 * KT)
                ok = (g > 2.0) & np.isfinite(gamma) & (a > 0)
                o = np.argsort(g[ok])
                self.t[(dev, round(L, 2))] = (g[ok][o], (a * 2e-6 * L * 1e-6)[ok][o], af[ok][o], gamma[ok][o])

    def psd(self, dev, L, gmid, w, gm, f):
        """gate-referred V^2/Hz of devices (arrays, n) at frequencies f (k): n x k."""
        awl, af, gam = (np.empty(gmid.shape) for _ in range(3))
        for lv in np.unique(L):
            m = L == lv
            g, a, e, y = self.t[(dev, round(float(lv), 2))]
            gm_ = np.clip(gmid[m], g[0], g[-1])
            awl[m], af[m], gam[m] = np.interp(gm_, g, a), np.interp(gm_, g, e), np.interp(gm_, g, y)
        fl = awl[:, None] / (w * L * 1e-6)[:, None] * (f[None, :] / 1e3) ** (-af[:, None])
        return fl + (4 * KT * gam / gm)[:, None]


# ------------------------------------------------------------ geometry
def footprint(w_f, nf, L):
    """um^2: nf fingers of w_f with shared contacted S/D strips, m-split above 50."""
    m = np.ceil(nf / 50.0)
    nfi = nf / m
    return m * w_f * 1e6 * (nfi * L + (nfi - 1) * SD_SHARED + 2 * SD_END)


def qnf(nf):
    """finger count drawable as m identical instances of <= NF_INST fingers."""
    m = np.ceil(nf / NF_INST)
    return np.ceil(nf / m) * m


def r_length(r):
    """drawn ppolyf_u_3k length (m) for resistance r at W = 1 um [P]."""
    return r * (R_W - 2 * R_DW) / RSH + 2 * R_DL


def mim_side(c):
    return np.sqrt(c / MIM_DENS) * 1e-6


VARS = ("l_f", "l_s", "l_b", "w_fp", "w_fn", "nf_1", "nf_4", "k", "nf_3", "nf_6", "nf_ib",
        "i_f", "r_half", "c_tap", "c_dec", "share")


# ------------------------------------------------------------ sampling: gm/Id targets -> fingers
def sample_uniform(rng, n, P, N):
    l_f, l_s, l_b = (rng.choice(L_CHOICES, n) for _ in range(3))
    w_fp, w_fn = rng.choice(W_F_CHOICES, n), rng.choice(W_F_CHOICES, n)
    # bias finger: an NMOS diode; its gm/Id sets J_D = i_f / W_fn
    gmid_b = rng.uniform(5.0, 20.0, n)
    i_f = N.idw_from_gmid(gmid_b, l_b, 1.0, 0.0) * w_fn
    ib = np.exp(rng.uniform(np.log(0.2e-6), np.log(8e-6), n))
    nf_ib = np.clip(np.round(ib / i_f), 1, NF_B_MAX)
    ib = nf_ib * i_f
    k = rng.integers(1, K_MAX + 1, n).astype(float)
    # followers: gm/Id 8-24 S/A at their body bias (~0.8 V) [A]
    j1 = P.idw_from_gmid(rng.uniform(8.0, 24.0, n), l_f, 0.6, 0.8)
    j4 = N.idw_from_gmid(rng.uniform(8.0, 24.0, n), l_f, 0.6, 0.8)
    nf_1 = qnf(np.clip(np.round(ib / j1 / w_fp), 1, NF_F_MAX))
    nf_4 = qnf(np.clip(np.round(ib / j4 / w_fn), 1, NF_F_MAX))
    # shunts carry IB + I_out ~ (1 + k) IB: the user's "load" range 4-18 S/A (low = large VGS = headroom)
    j3 = P.idw_from_gmid(rng.uniform(4.0, 18.0, n), l_s, 0.8, 0.0)
    j6 = N.idw_from_gmid(rng.uniform(4.0, 18.0, n), l_s, 0.8, 0.0)
    nf_3 = qnf(np.clip(np.round((1 + k) * ib / j3 / w_fp), 1, NF_S_MAX))
    nf_6 = qnf(np.clip(np.round((1 + k) * ib / j6 / w_fn), 1, NF_S_MAX))
    nf_ib = qnf(nf_ib)
    r_half = np.exp(rng.uniform(np.log(0.1e6), np.log(2.0e6), n))
    c_tap = np.where(rng.random(n) < 0.3, 0.0, np.exp(rng.uniform(np.log(50e-15), np.log(2e-12), n)))
    c_dec = np.exp(rng.uniform(np.log(0.1e-12), np.log(2e-12), n))
    share = (rng.random(n) < 0.5).astype(float)
    return dict(l_f=l_f, l_s=l_s, l_b=l_b, w_fp=w_fp, w_fn=w_fn, nf_1=nf_1, nf_4=nf_4, k=k,
                nf_3=nf_3, nf_6=nf_6, nf_ib=nf_ib, i_f=i_f, r_half=r_half, c_tap=c_tap,
                c_dec=c_dec, share=share)


def sample_local(rng, parent, n):
    j = rng.integers(0, parent["nf_1"].size, n)

    def step_l(v):
        idx = np.searchsorted(L_CHOICES, v[j] - 1e-9)
        return L_CHOICES[np.clip(idx + rng.choice([-1, 0, 0, 0, 1], n), 0, L_CHOICES.size - 1)]

    def step_w(v):
        return np.where(rng.random(n) < 0.1, rng.choice(W_F_CHOICES, n), v[j])

    def step_n(v, hi):
        d = rng.integers(-2, 3, n) + np.round(rng.normal(0.0, 0.08, n) * v[j])
        return np.clip(v[j] + d, 1, hi)

    def step_x(v, s, lo, hi):
        return np.clip(v[j] * np.exp(rng.normal(0.0, s, n)), lo, hi)

    c_tap = step_x(parent["c_tap"], 0.15, 0.0, 2e-12)
    c_tap = np.where(rng.random(n) < 0.05, np.where(c_tap > 0, 0.0, 50e-15), c_tap)
    return dict(l_f=step_l(parent["l_f"]), l_s=step_l(parent["l_s"]), l_b=step_l(parent["l_b"]),
                w_fp=step_w(parent["w_fp"]), w_fn=step_w(parent["w_fn"]),
                nf_1=qnf(step_n(parent["nf_1"], NF_F_MAX)), nf_4=qnf(step_n(parent["nf_4"], NF_F_MAX)),
                k=np.clip(parent["k"][j] + rng.choice([-1, 0, 0, 0, 1], n), 1, K_MAX),
                nf_3=qnf(step_n(parent["nf_3"], NF_S_MAX)), nf_6=qnf(step_n(parent["nf_6"], NF_S_MAX)),
                nf_ib=qnf(step_n(parent["nf_ib"], NF_B_MAX)),
                i_f=step_x(parent["i_f"], 0.1, 1e-9, 1e-4),
                r_half=step_x(parent["r_half"], 0.15, 0.05e6, 4e6), c_tap=c_tap,
                c_dec=step_x(parent["c_dec"], 0.15, 0.05e-12, 4e-12),
                share=np.where(rng.random(n) < 0.1, 1 - parent["share"][j], parent["share"][j]))


# ------------------------------------------------------------ stage A model
def solve_op(s, P, N, V, bias=1.0):
    """DC of one buffer from the tables at supply V (typical): node voltages,
    branch currents, gm/Id, headroom proxies. vin = V/2 (ideal tap)."""
    n = s["nf_1"].size
    vin = np.full(n, V / 2)
    lf, ls, lb = s["l_f"], s["l_s"], s["l_b"]
    wfp, wfn = s["w_fp"], s["w_fn"]
    i_ref = bias * s["i_f"]
    vgs_bn = N.diode_vgs(i_ref / wfn, lb, np.zeros(n))
    # XMBN2 (VDS = V - VSG_bp) -> XMBP diode
    vsg_bp = np.full(n, 1.0)
    for _ in range(3):
        i_mir = i_ref * N.at("lnI", lb, vgs_bn, V - vsg_bp, 0 * vin) / N.at("lnI", lb, vgs_bn, vgs_bn, 0 * vin)
        vsg_bp = P.diode_vgs(i_mir / wfp, lb, np.zeros(n))
    b, a = np.full(n, 0.8), np.full(n, V - 0.8)
    p, nn = vin + 0.9, vin - 0.9
    i2 = s["k"] * i_ref * s["nf_ib"]
    for it in range(int(os.environ.get("OP_ITERS", "14"))):
        p0, n0_, a0, b0 = p, nn, a, b
        ibb = s["nf_ib"] * wfn * N.at("lnI", lb, vgs_bn, np.maximum(b, 0.05), 0 * vin)
        ibt = s["nf_ib"] * wfp * P.at("lnI", lb, vsg_bp, np.maximum(V - a, 0.05), 0 * vin)
        vsg1 = P.vgs(ibb / (s["nf_1"] * wfp), lf, np.maximum(p - b, 0.05), V - p)
        p = vin + vsg1
        vgs4 = N.vgs(ibt / (s["nf_4"] * wfn), lf, np.maximum(a - nn, 0.05), nn)
        nn = vin - vgs4
        # output diodes: p - VSG2(I) = n + VGS5(I)
        lo, hi = np.full(n, np.log(1e-11)), np.full(n, np.log(2e-3))
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            i = np.exp(mid)
            v2 = P.diode_vgs(i / (s["k"] * s["nf_1"] * wfp), lf, V - p)
            v5 = N.diode_vgs(i / (s["k"] * s["nf_4"] * wfn), lf, nn)
            f = (p - v2) - (nn + v5)
            f = np.where(np.isnan(f), -1.0, f)
            lo, hi = np.where(f > 0, mid, lo), np.where(f > 0, hi, mid)
        i2 = np.exp(0.5 * (lo + hi))
        v2 = P.diode_vgs(i2 / (s["k"] * s["nf_1"] * wfp), lf, V - p)
        out = p - v2
        i3 = ibb + i2
        vsg3 = P.vgs(i3 / (s["nf_3"] * wfp), ls, np.maximum(V - p, 0.02), 0 * vin)
        b = V - vsg3
        i6 = ibt + i2
        vgs6 = N.vgs(i6 / (s["nf_6"] * wfn), ls, np.maximum(nn, 0.02), 0 * vin)
        a = vgs6
        if it >= 3:                       # damped: the FVF loops oscillate near triode
            p, nn, a, b = 0.5 * (p + p0), 0.5 * (nn + n0_), 0.5 * (a + a0), 0.5 * (b + b0)
    g = {}
    g["1"] = P.at("gmid", lf, vsg1, p - b, V - p)
    g["4"] = N.at("gmid", lf, vgs4, a - nn, nn)
    g["2"] = P.at("gmid", lf, v2, v2, V - p)
    g["5"] = N.at("gmid", lf, out - nn, out - nn, nn)
    g["3"] = P.at("gmid", ls, vsg3, V - p, 0 * vin)
    g["6"] = N.at("gmid", ls, vgs6, nn, 0 * vin)
    g["ib"] = N.at("gmid", lb, vgs_bn, b, 0 * vin)
    g["it"] = P.at("gmid", lb, vsg_bp, V - a, 0 * vin)
    g["bn"] = N.at("gmid", lb, vgs_bn, vgs_bn, 0 * vin)
    g["bp"] = P.at("gmid", lb, vsg_bp, vsg_bp, 0 * vin)
    vdsat = {k: np.maximum(2.0 / v, 0.08) for k, v in g.items()}       # [A] proxy, ngspice decides
    hr = dict(m1=(p - b) - vdsat["1"], m4=(a - nn) - vdsat["4"], ib=b - vdsat["ib"],
              it=(V - a) - vdsat["it"], m3=(V - p) - vdsat["3"], m6=nn - vdsat["6"])
    c_in = (P.at("cgg", lf, vsg1, p - b, V - p) * s["nf_1"] * wfp
            + N.at("cgg", lf, vgs4, a - nn, nn) * s["nf_4"] * wfn)
    c_out = (P.at("cdd", lf, v2, v2, V - p) * s["k"] * s["nf_1"] * wfp
             + N.at("cdd", lf, out - nn, out - nn, nn) * s["k"] * s["nf_4"] * wfn)
    i_sup = i_ref + i_mir + i3 + ibt + V / (2 * s["r_half"])
    return dict(p=p, n=nn, a=a, b=b, out=out, err=out - vin, ibb=ibb, ibt=ibt, i2=i2, i3=i3, i6=i6,
                i_ref=i_ref, i_mir=i_mir, gmid=g, hr=hr, c_in=c_in, c_out=c_out, i_sup=i_sup)


def hr_sigma(s):
    """sigma of the follower headroom from local Vt mismatch: VSD1 = VSG1 + VSG3 - VDD/2
    (M1 with its shunt M3), VDS4 = VGS4 + VGS6 - VDD/2 (M4 with M6) [D, PDK fets_mm]."""
    sv = lambda dev, nf, wf, L: sigma_vt(PDK_MM[dev], nf * wf, L)
    s1 = np.hypot(sv("pfet", s["nf_1"], s["w_fp"], s["l_f"]), sv("pfet", s["nf_3"], s["w_fp"], s["l_s"]))
    s4 = np.hypot(sv("nfet", s["nf_4"], s["w_fn"], s["l_f"]), sv("nfet", s["nf_6"], s["w_fn"], s["l_s"]))
    return s1, s4


def sigma_vt(par, w, L):
    leff = np.maximum(L * 1e-6 - PDK_MM["par_l"], 0.05e-6)
    weff = np.maximum(w - PDK_MM["par_w"], 0.1e-6)
    return par * 1e-6 / np.sqrt(leff * weff)


FREQ = np.logspace(np.log10(F_LO), np.log10(F_HI), 161)


def evaluate(s, P, N, NZ, CT=None):
    """Stage-A metrics. Headroom and error on typical tables at 3.0/3.3/3.6 V and,
    when the corner tables are given (CT = {(tag): (P, N, V)}), at ff/85 C/3.6 V and
    ss/0 C/3.0 V, where the FVF's saturation window closes."""
    ops = {V: solve_op(s, P, N, V) for V in VDD_SET}
    for tag, (Pc, Nc, Vc) in (CT or {}).items():
        ops[tag] = solve_op(s, Pc, Nc, Vc)
    o = ops[VDD]
    n = s["nf_1"].size
    wfp, wfn = s["w_fp"], s["w_fn"]
    e = {}
    e["hr_f"] = np.min([np.minimum(x["hr"]["m1"], x["hr"]["m4"]) for x in ops.values()], 0)
    sg1, sg4 = hr_sigma(s)
    e["hr_sig1"], e["hr_sig4"] = sg1, sg4
    e["hr_f_mm"] = np.min([np.minimum(x["hr"]["m1"] - HR_SIGMAS * sg1, x["hr"]["m4"] - HR_SIGMAS * sg4)
                           for x in ops.values()], 0)
    e["hr_ib"] = np.min([np.minimum(x["hr"]["ib"], x["hr"]["it"]) for x in ops.values()], 0)
    e["hr_sh"] = np.min([np.minimum(x["hr"]["m3"], x["hr"]["m6"]) for x in ops.values()], 0)
    e["err_max"] = np.max([np.abs(x["err"]) for x in ops.values()], 0)
    lo = solve_op(s, P, N, VDD, BIAS_LO)
    hi = solve_op(s, P, N, VDD, BIAS_HI)
    e["hr_f_bias"] = np.min([np.minimum(x["hr"]["m1"], x["hr"]["m4"]) for x in (lo, hi)], 0)
    for k in ("ibb", "ibt", "i2", "i3", "i_sup"):
        e[k] = o[k]
    for k, v in o["gmid"].items():
        e["gmid_" + k] = v
    gm = {k: o["gmid"][k] * i for k, i in (("1", o["ibb"]), ("4", o["ibt"]), ("2", o["i2"]), ("5", o["i2"]),
                                            ("ib", o["ibb"]), ("it", o["ibt"]), ("bn", o["i_ref"]),
                                            ("bp", o["i_mir"]))}
    wp = gm["2"] / (gm["2"] + gm["5"])
    wn = 1.0 - wp
    gout = gm["2"] + gm["5"]
    c_dec_t = s["c_dec"] + o["c_out"]
    e["rout"] = 1.0 / gout
    tau = c_dec_t / gout
    dv0 = Q_KICK / c_dec_t
    e["t_settle_lin"] = tau * np.log(np.maximum(dv0 / EPS, 1.0))
    # ---- noise (gate-referred device PSDs, data/device_noise.csv)
    f = FREQ
    W = lambda nf, wf: nf * wf
    lf, lb = s["l_f"], s["l_b"]
    s1 = NZ.psd("pfet", lf, o["gmid"]["1"], W(s["nf_1"], wfp), gm["1"], f)
    s4 = NZ.psd("nfet", lf, o["gmid"]["4"], W(s["nf_4"], wfn), gm["4"], f)
    s2 = NZ.psd("pfet", lf, o["gmid"]["2"], W(s["k"] * s["nf_1"], wfp), gm["2"], f)
    s5 = NZ.psd("nfet", lf, o["gmid"]["5"], W(s["k"] * s["nf_4"], wfn), gm["5"], f)
    sib = NZ.psd("nfet", lb, o["gmid"]["ib"], W(s["nf_ib"], wfn), gm["ib"], f)
    sit = NZ.psd("pfet", lb, o["gmid"]["it"], W(s["nf_ib"], wfp), gm["it"], f)
    sbn = NZ.psd("nfet", lb, o["gmid"]["bn"], wfn, gm["bn"], f)
    sbp = NZ.psd("pfet", lb, o["gmid"]["bp"], wfp, gm["bp"], f)
    sbn2 = NZ.psd("nfet", lb, o["gmid"]["bn"], wfn, gm["bn"], f)
    r_bn = (o["gmid"]["bn"] / o["gmid"]["bp"])[:, None]
    s_ibb = (gm["ib"] ** 2)[:, None] * (sib + sbn)
    s_ibt = (gm["it"] ** 2)[:, None] * (sit + sbp + r_bn ** 2 * (sbn2 + sbn))
    s_p = s1 + s_ibb / (gm["1"] ** 2)[:, None]
    s_n = s4 + s_ibt / (gm["4"] ** 2)[:, None]
    s_dev = (wp ** 2)[:, None] * (s_p + s2) + (wn ** 2)[:, None] * (s_n + s5)
    r_tap = s["r_half"] / 2
    f_tap = 1.0 / (2 * np.pi * r_tap * (s["c_tap"] + o["c_in"]))
    s_tap = (4 * KT * r_tap)[:, None] / (1 + (f[None, :] / f_tap[:, None]) ** 2)
    h2 = 1.0 / (1 + (f[None, :] / (gout / (2 * np.pi * c_dec_t))[:, None]) ** 2)
    v_dev, v_tap = pair_variance(f, s_dev * h2, s_tap * h2, s["share"] > 0.5)
    e["noise_lsb"] = NOISE_CAL * np.sqrt(v_dev + v_tap) / ALPHA / LSB
    e["noise_dev_lsb"] = np.sqrt(v_dev) / ALPHA / LSB
    e["noise_tap_lsb"] = np.sqrt(v_tap) / ALPHA / LSB
    # ---- mismatch of one buffer's output; VBL - VREF = sqrt(2) x that [D]
    sv = lambda dev, nf, wf, L: sigma_vt(PDK_MM[dev], nf * wf, L)
    sd_ibb = o["gmid"]["ib"] * np.hypot(sv("nfet", s["nf_ib"], wfn, lb), sv("nfet", 1, wfn, lb))
    sd_ibt = o["gmid"]["it"] * np.hypot(sv("pfet", s["nf_ib"], wfp, lb), sv("pfet", 1, wfp, lb))
    var = (wp ** 2 * (sv("pfet", s["nf_1"], wfp, lf) ** 2 + (sd_ibb / o["gmid"]["1"]) ** 2
                      + sv("pfet", s["k"] * s["nf_1"], wfp, lf) ** 2)
           + wn ** 2 * (sv("nfet", s["nf_4"], wfn, lf) ** 2 + (sd_ibt / o["gmid"]["4"]) ** 2
                        + sv("nfet", s["k"] * s["nf_4"], wfn, lf) ** 2))
    e["sigma_diff_lsb"] = np.sqrt(2 * var) / ALPHA / LSB
    # ---- area and power
    fp = lambda wf, nf, L: footprint(wf, nf, L)
    e["a_mos"] = (fp(wfn, 1, lb) * 2 + fp(wfp, 1, lb) + fp(wfp, s["nf_ib"], lb) + fp(wfn, s["nf_ib"], lb)
                  + (1 + s["k"]) * fp(wfp, s["nf_1"], lf) + fp(wfp, s["nf_3"], s["l_s"])
                  + (1 + s["k"]) * fp(wfn, s["nf_4"], lf) + fp(wfn, s["nf_6"], s["l_s"]))
    div_share = np.where(s["share"] > 0.5, 0.5, 1.0)
    e["a_res"] = div_share * 2 * R_PITCH * r_length(s["r_half"]) * 1e6
    e["a_mim"] = (div_share * s["c_tap"] + s["c_dec"]) / MIM_DENS          # um2
    e["area"] = e["a_mos"] + e["a_res"] + e["a_mim"]
    i_div = VDD / (2 * s["r_half"])
    e["power"] = VDD * (o["i_sup"] - i_div + div_share * i_div)
    e["vin_err"] = o["err"]
    return e


GATES = (("hr_f", lambda e: e["hr_f_mm"] + HR_CAL >= HR_MARGIN),
         ("hr_ib", lambda e: e["hr_ib"] >= 0.0),
         ("hr_f_bias", lambda e: e["hr_f_bias"] >= HR_MARGIN),
         ("err", lambda e: e["err_max"] <= VERR_MAX),
         ("noise", lambda e: e["noise_lsb"] <= NOISE_MAX_LSB),
         ("sigma", lambda e: e["sigma_diff_lsb"] <= SIGMA_DIFF_MAX_LSB),
         ("settle", lambda e: e["t_settle_lin"] <= 2 * TS_MAX))


def feasible(e):
    ok = np.ones(e["power"].size, bool)
    for _, g in GATES:
        ok &= np.nan_to_num(g(e), nan=False).astype(bool)
    return ok & np.isfinite(e["power"]) & np.isfinite(e["area"])


def pareto_mask(c):
    n = c.shape[0]
    keep = np.ones(n, bool)
    for i in np.argsort(c[:, 0], kind="stable"):
        if keep[i]:
            dom = np.all(c[i] <= c, 1) & np.any(c[i] < c, 1)
            keep &= ~dom
    return keep


def knee(power, area):
    """front point closest to the utopia corner on log-normalised axes."""
    x, y = np.log(power), np.log(area)
    xn = (x - x.min()) / max(np.ptp(x), 1e-12)
    yn = (y - y.min()) / max(np.ptp(y), 1e-12)
    return int(np.argmin(np.hypot(xn, yn)))


def concat(a, b):
    return {k: np.concatenate([a[k], b[k]]) for k in a}


def take(s, idx):
    return {k: v[idx] for k, v in s.items()}


# ------------------------------------------------------------ netlist
def fmt_u(x):
    return ("%.4g" % (x * 1e6)) + "u"


def dev_line(name, d, g, sn, bn, kind, L, wf, nf, m=None):
    """nf fingers of wf; above NF_INST as m identical instances (qnf makes it exact)."""
    nf = int(round(nf))
    if m is None:
        m = int(np.ceil(nf / NF_INST))
        assert nf % m == 0, (name, nf)
        nf //= m
    return f"{name} {d} {g} {sn} {bn} {kind}_03v3 L={L:.2f}u W={fmt_u(wf * nf)} nf={nf} m={int(m)}"


def emit(s, header=""):
    """midref_div, midref_buf and the one-buffer wrapper midref2."""
    g = lambda k: float(np.ravel(s[k])[0])
    lr = r_length(g("r_half"))
    lines = [header,
             ".subckt midref_div vin vdd vss",
             f"XRT vdd vin vss ppolyf_u_3k r_width=1u r_length={fmt_u(lr)}",
             f"XRB vin vss vss ppolyf_u_3k r_width=1u r_length={fmt_u(lr)}"]
    if g("c_tap") > 0:
        c = mim_side(g("c_tap"))
        lines.append(f"XCT vin vss cap_mim_2f0_m4m5_noshield c_width={fmt_u(c)} c_length={fmt_u(c)}")
    lines += [".ends midref_div", "",
              ".subckt midref_buf out vin ib vdd vss"]
    wp, wn, lf, ls, lb = g("w_fp"), g("w_fn"), g("l_f"), g("l_s"), g("l_b")
    k = int(round(g("k")))
    lines += [dev_line("XMBN", "ib", "ib", "vss", "vss", "nfet", lb, wn, 1),
              dev_line("XMBN2", "pb", "ib", "vss", "vss", "nfet", lb, wn, 1),
              dev_line("XMBP", "pb", "pb", "vdd", "vdd", "pfet", lb, wp, 1),
              dev_line("XMIT", "a", "pb", "vdd", "vdd", "pfet", lb, wp, g("nf_ib")),
              dev_line("XMIB", "b", "ib", "vss", "vss", "nfet", lb, wn, g("nf_ib")),
              dev_line("XM3", "p", "b", "vdd", "vdd", "pfet", ls, wp, g("nf_3")),
              dev_line("XM1", "b", "vin", "p", "vdd", "pfet", lf, wp, g("nf_1")),
              dev_line("XM2", "out", "out", "p", "vdd", "pfet", lf, wp, g("nf_1"), m=k),
              dev_line("XM6", "n", "a", "vss", "vss", "nfet", ls, wn, g("nf_6")),
              dev_line("XM4", "a", "vin", "n", "vss", "nfet", lf, wn, g("nf_4")),
              dev_line("XM5", "out", "out", "n", "vss", "nfet", lf, wn, g("nf_4"), m=k)]
    c = mim_side(g("c_dec"))
    lines += [f"XCD out vss cap_mim_2f0_m4m5_noshield c_width={fmt_u(c)} c_length={fmt_u(c)}",
              ".ends midref_buf", "",
              ".subckt midref2 out ib vdd vss",
              "XD vin vdd vss midref_div",
              "XB out vin ib vdd vss midref_buf",
              ".ends midref2", ""]
    return "\n".join(lines)


# ------------------------------------------------------------ stage B (ngspice)
CORNERS = ("typical", "ff", "ss", "sf", "fs")
TEMPS = (0, 27, 85)


def fill(tpl, subs):
    t = open(os.path.join(BLOCK, tpl)).read()
    for k, v in subs.items():
        t = t.replace("@" + k + "@", str(v))
    left = re.findall(r"@[A-Z_]+@", t)
    assert not left, (tpl, left)
    return t


def bufs(share):
    if share:
        return ("XD vin vdd 0 midref_div\nXR vrefb vin ibr vdd 0 midref_buf\nXB vblb vin ibb vdd 0 midref_buf")
    return "XR vrefb ibr vdd 0 midref2\nXB vblb ibb vdd 0 midref2"


def ngspice(d, deck, timeout=600):
    log = os.path.join(d, deck.replace(".spice", ".log"))
    try:
        subprocess.run(["ngspice", "-b", deck], cwd=d, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                       timeout=timeout)
    except subprocess.TimeoutExpired:
        return ""
    return open(log, errors="replace").read()


NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def grab(txt):
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"^([a-z][a-z_0-9]*) = (" + NUM + r")\s*$", txt, re.M)}


def kick_subs(i_f, share, prefix, cell=("typical", 27, VDD)):
    c, t, v = cell
    return dict(IF="%.6g" % i_f, BUFS=bufs(share), P=prefix, CORNER=c,
                MIMCORNER=c if c in ("ff", "ss") else "typical", TEMP=t, VDD="%g" % v,
                TOP1="%.4f" % (v / 2 + 1.34), TOP2="%.4f" % (v / 2 + 0.10))


def stage_b_one(job):
    tag, s = job
    d = os.path.join(WORK, "b", tag)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    open(os.path.join(d, "dut.spice"), "w").write(emit(s, f"* candidate {tag}"))
    share = float(s["share"]) > 0.5
    i_f = float(s["i_f"])
    r = dict(tag=tag)
    # operating point: 5 corners x 3 temperatures x 3 supplies, and the bias span
    ops = []
    jobs = [(c, t, 1.0) for c in CORNERS for t in TEMPS] + [("typical", 27, BIAS_LO), ("typical", 27, BIAS_HI)]
    for c, t, bs in jobs:
        deck = f"op_{c}_{t}_{bs:g}.spice"
        open(os.path.join(d, deck), "w").write(fill("tb_op.spice", dict(
            CORNER=c, MIMCORNER=c if c in ("ff", "ss") else "typical", TEMP=t, IF="%.6g" % (i_f * bs),
            TAG=f"{c} {t} {bs:g}")))
        for m in re.finditer(r"^OP (\S+) (\S+) (\S+) (\S+) (.*)$", ngspice(d, deck), re.M):
            vals = [float(x) for x in m.group(5).split()]
            ops.append((m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4)), vals))
    keys = ("hr1", "hr4", "hrib", "hrit", "hr2", "hr5", "hr3", "hr6", "err", "isup")
    nominal = [o for o in ops if o[2] == 1.0]          # (corner, temp, bias, vdd, values)
    r["op_cells"] = len(nominal)
    if ops:
        A = np.array([o[4] for o in ops])
        Nm = np.array([o[4] for o in nominal]) if nominal else A
        r["hr_f_min"] = float(np.min(A[:, [0, 1]]))
        r["hr1_min"], r["hr4_min"] = float(np.min(A[:, 0])), float(np.min(A[:, 1]))
        sg1, sg4 = hr_sigma(s)
        r["hr_sig1"], r["hr_sig4"] = float(sg1), float(sg4)
        r["hr_f_mm"] = min(r["hr1_min"] - HR_SIGMAS * r["hr_sig1"], r["hr4_min"] - HR_SIGMAS * r["hr_sig4"])
        r["hr_ib_min"] = float(np.min(A[:, [2, 3]]))
        r["hr_out_min"] = float(np.min(A[:, [4, 5]]))
        r["hr_sh_min"] = float(np.min(A[:, [6, 7]]))
        r["err_max_mv"] = float(np.max(np.abs(Nm[:, 8]))) * 1e3
        typ = [o for o in ops if o[0] == "typical" and o[1] == 27 and o[2] == 1.0 and o[3] == 3.3]
        if typ:
            r["err_typ_mv"] = typ[0][4][8] * 1e3
            r["isup_typ_ua"] = typ[0][4][9] * 1e6
    # kick, both cases, nominal and low bias; VBL crosstalk
    for tagk, bs in (("k", 1.0), ("kl", BIAS_LO)):
        deck = f"kick_{tagk}.spice"
        open(os.path.join(d, deck), "w").write(fill("tb_kick.spice", kick_subs(i_f * bs, share, tagk)))
        r.update(grab(ngspice(d, deck)))
    # noise
    open(os.path.join(d, "noise.spice"), "w").write(fill("tb_noise.spice", dict(IF="%.6g" % i_f)))
    ngspice(d, "noise.spice")
    r.update(noise_from_files(d, share))
    # decision with comparator on VBL
    open(os.path.join(d, "cmp.spice"), "w").write(fill("tb_cmp.spice", dict(IF="%.6g" % i_f, BUFS=bufs(share))))
    r.update(grab(ngspice(d, "cmp.spice")))
    return r


def read_xy(path, ncol=2):
    try:
        a = np.loadtxt(path)
    except Exception:
        return None
    return a if a.ndim == 2 and a.shape[0] > 10 else None


def noise_from_files(d, share):
    out = read_xy(os.path.join(d, "nz_out.txt"))
    tap = read_xy(os.path.join(d, "nz_tap.txt"))
    ac = read_xy(os.path.join(d, "ac.txt"))
    if out is None or tap is None or ac is None:
        return {}
    ok = np.isfinite(out).all(1)
    out = out[ok]
    tap, ac = tap[np.isfinite(tap).all(1)], ac[np.isfinite(ac).all(1)]
    f = out[:, 0]
    s_out = out[:, 1] ** 2
    s_tapn = np.interp(f, tap[:, 0], tap[:, 1] ** 2)
    # ac.txt (wr_singlescale): frequency vm(out) vm(vin)
    ratio2 = np.interp(f, ac[:, 0], (ac[:, 1] / np.maximum(ac[:, 2], 1e-30)) ** 2)
    s_tap_out = np.minimum(np.nan_to_num(s_tapn * ratio2, nan=0.0, posinf=0.0), s_out)
    s_dev = s_out - s_tap_out
    v_dev, v_tap = pair_variance(f, s_dev, s_tap_out, share)
    v_dev, v_tap = float(v_dev[0]), float(v_tap[0])
    return dict(nz_out_uv=float(np.sqrt(np.trapezoid(s_out, f)) * 1e6),
                nz_tap_out_uv=float(np.sqrt(np.trapezoid(s_tap_out, f)) * 1e6),
                nz_lsb=float(np.sqrt(v_dev + v_tap) / ALPHA / LSB))


def pair_variance(f, s_dev, s_tap, share):
    """variance of VBL(t_dec) - VREF(TS) from one buffer's output PSDs (rows x f):
    VREF in full (sampled), VBL through the comparator pole F_CMP; device noise
    independent in the two buffers; the divider's share independent too, or,
    with one shared tap, the SAME noise seen at TS and at the decision, averaged
    over the decision time T_DEC. Returns (device, divider) variances."""
    s_dev, s_tap = np.atleast_2d(s_dev), np.atleast_2d(s_tap)
    hc = 1.0 / (1.0 + 1j * f / F_CMP)
    w = 2 * np.pi * f
    t1, t2 = T_DEC
    avg = (np.exp(-1j * w * t1) - np.exp(-1j * w * t2)) / (1j * w * (t2 - t1))
    k_ind = 1.0 + np.abs(hc) ** 2
    k_sh = 1.0 + np.abs(hc) ** 2 - 2.0 * np.real(hc * avg)
    v_dev = np.trapezoid(s_dev * k_ind[None, :], f, axis=1)
    share = np.broadcast_to(np.asarray(share), (s_tap.shape[0],))
    v_tap = np.where(share, np.trapezoid(s_tap * k_sh[None, :], f, axis=1),
                     np.trapezoid(s_tap * k_ind[None, :], f, axis=1))
    return v_dev, v_tap


def b_verdict(r):
    """ngspice gates; returns (pass, list of failed gate names)."""
    fails = []
    q = LSB / 4
    def chk(name, ok):
        if not ok:
            fails.append(name)
    g = lambda k, dflt=np.nan: r.get(k, dflt)
    chk("op_cells", g("op_cells", 0) == 45)
    chk("hr_f", g("hr_f_mm") >= 0)
    chk("hr_ib", g("hr_ib_min") >= 0)
    chk("hr_out", g("hr_out_min") >= 0)
    chk("err", g("err_max_mv") <= VERR_MAX * 1e3)
    for p in ("k", "kl"):
        for c in (1, 2):
            pre = f"{p}_c{c}_"
            pk = g(pre + "pkr_mv")
            ts = g(pre + "tsr_ns", 0.0 if pk == pk and pk < EPS * 1e3 else np.nan)
            chk(f"{p}{c}_ts", ts <= TS_MAX * 1e9)
            chk(f"{p}{c}_rr", max(g(pre + "rr250_mv"), g(pre + "rr300_mv")) <= EPS * 1e3)
            chk(f"{p}{c}_q", abs(g(pre + "qk_fc")) >= 50)
            if p == "k":
                chk(f"xt{c}", g(pre + "rb250_uv") <= q * 1e6)
    chk("noise", g("nz_lsb") <= NOISE_MAX_LSB)
    chk("cmp_dt", abs(g("cmp_dt_lsb")) <= 0.05)
    chk("cmp_pre", g("cmp_pkpre_uv") <= q * 1e6)
    return (not fails), fails


def stage_b(cands, tags):
    with ThreadPoolExecutor(JOBS) as ex:
        res = list(ex.map(stage_b_one, [(t, take(cands, i)) for i, t in enumerate(tags)]))
    for r in res:
        r["pass"], r["fails"] = b_verdict(r)
    return res


# ------------------------------------------------------------ main
def stage_a(rng, P, N, NZ, n0, n_local, rounds, CT=None):
    s = sample_uniform(rng, n0, P, N)
    e = evaluate(s, P, N, NZ, CT)
    for r in range(rounds):
        ok = feasible(e)
        print(f"REPORT: stage A round {r}: {ok.sum()} feasible of {ok.size}")
        if ok.sum() == 0:
            break
        idx = np.flatnonzero(ok)
        fr = idx[pareto_mask(np.stack([e["power"][idx], e["area"][idx]], 1))]
        parent = take(s, np.concatenate([fr, rng.choice(idx, min(idx.size, 200))]))
        s2 = sample_local(rng, parent, n_local)
        e2 = evaluate(s2, P, N, NZ, CT)
        s, e = concat(s, s2), concat(e, e2)
    return s, e


def write_csv(path, s, e, idx, extra=None):
    cols = list(VARS) + sorted(k for k in e if np.ndim(e[k]) == 1)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["idx"] + cols + (list(extra[0].keys()) if extra else []))
        for j, i in enumerate(idx):
            row = [i] + [float(s[k][i]) if k in s else float(e[k][i]) for k in cols]
            if extra:
                row += [extra[j][k] for k in extra[0]]
            w.writerow(row)


def main():
    os.makedirs(DATA, exist_ok=True)
    rng = np.random.default_rng(SEED)
    P, N = Dev("pfet_03v3"), Dev("nfet_03v3")
    NZ = Noise(os.path.join(DATA, "device_noise.csv"))
    if os.environ.get("PHASE") == "CHECK":
        model_check(rng, P, N, NZ)
        return 0
    CT = {"ff85": (Dev("pfet_03v3_ff85"), Dev("nfet_03v3_ff85"), 3.6),
          "ss0": (Dev("pfet_03v3_ss0"), Dev("nfet_03v3_ss0"), 3.0)}
    print(f"REPORT: calibration noise x{NOISE_CAL:.3f}, headroom {HR_CAL:+.3f} V "
          f"({'data/calibration.json' if _CAL else 'none'})")
    if os.environ.get("PHASE") == "CAL":
        return calibrate(rng, P, N, NZ, CT)
    if os.environ.get("PHASE") == "RECAL":
        return recalibrate()
    if os.environ.get("PHASE") == "EMIT":
        write_netlist(json.load(open(os.path.join(DATA, "sizing.json"))))
        return 0
    n0 = int(os.environ.get("POINTS", "40000"))
    s, e = stage_a(rng, P, N, NZ, n0, int(os.environ.get("LOCAL_POINTS", "15000")),
                   int(os.environ.get("ROUNDS", "4")), CT)
    ok = feasible(e)
    for name, g in GATES:
        print(f"REPORT: stage A gate {name}: {int(np.nan_to_num(g(e), nan=False).astype(bool).sum())} of {ok.size} pass")
    print(f"stage_a_points = {ok.size}")
    print(f"stage_a_feasible = {int(ok.sum())}")
    if ok.sum() == 0:
        print("FAIL: stage A: no design meets the table gates")
        return 1
    idx = np.flatnonzero(ok)
    fr = idx[pareto_mask(np.stack([e["power"][idx], e["area"][idx]], 1))]
    fr = fr[np.argsort(e["power"][fr])]
    write_csv(os.path.join(DATA, "stage_a_front.csv"), s, e, fr)
    k = fr[knee(e["power"][fr], e["area"][fr])]
    print(f"REPORT: stage A front {fr.size} points; table knee {e['power'][k] * 1e6:.1f} uW, "
          f"{e['area'][k]:.0f} um2 (MOS {e['a_mos'][k]:.1f}, poly {e['a_res'][k]:.0f}, MIM {e['a_mim'][k]:.0f})")
    if os.environ.get("PHASE", "A") != "B":
        return 0
    # ---- stage B: peel the front with ngspice
    tried, records = set(), []
    n_b = int(os.environ.get("N_B", "48"))
    for rnd in range(int(os.environ.get("B_ROUNDS", "4"))):
        alive = np.array([i for i in idx if i not in tried])
        if alive.size == 0:
            break
        fr = alive[pareto_mask(np.stack([e["power"][alive], e["area"][alive]], 1))]
        if fr.size > n_b:
            fr = fr[np.argsort(e["power"][fr])][np.linspace(0, fr.size - 1, n_b).round().astype(int)]
        tags = [f"r{rnd}_{i}" for i in fr]
        res = stage_b(take(s, fr), tags)
        for i, r in zip(fr, res):
            tried.add(i)
            r["idx"] = int(i)
            r.update(a_record(e, i))
            records.append(r)
        npass = sum(r["pass"] for r in res)
        fails = {}
        for r in res:
            for f_ in r["fails"]:
                fails[f_] = fails.get(f_, 0) + 1
        print(f"REPORT: stage B round {rnd}: {npass} of {len(res)} pass; failed gates {json.dumps(fails)}")
        if sum(r["pass"] for r in records) >= int(os.environ.get("B_ENOUGH", "12")):
            break
    json.dump([{k: (v if not isinstance(v, np.generic) else float(v)) for k, v in r.items()} for r in records],
              open(os.path.join(DATA, "stage_b.json"), "w"), indent=1, default=float)
    good = [r for r in records if r["pass"]]
    print(f"stage_b_simulated = {len(records)}")
    print(f"stage_b_pass = {len(good)}")
    if not good:
        print("FAIL: stage B: no front point passes in ngspice")
        return 1
    gi = np.array([r["idx"] for r in good])
    pw = np.array([b_power(r, take(s, r["idx"])) for r in good])
    ar = e["area"][gi]
    m = pareto_mask(np.stack([pw, ar], 1))
    fi = np.flatnonzero(m)
    sel = fi[knee(pw[fi], ar[fi])]
    i = gi[sel]
    best = take(s, np.array([i]))
    print(f"REPORT: stage B front {fi.size} points; selected r={good[sel]['tag']}: "
          f"{pw[sel] * 1e6:.1f} uW (ngspice), {ar[sel]:.0f} um2")
    sz = dict(design={k: float(v[0]) for k, v in best.items()},
              stage_a={k: float(e[k][i]) for k in e if np.ndim(e[k]) == 1},
              stage_b=good[sel], power_w=float(pw[sel]))
    json.dump(sz, open(os.path.join(DATA, "sizing.json"), "w"), indent=1, default=float)
    if os.environ.get("SIZING_EMIT") == "1":
        write_netlist(sz)
    return 0


def write_netlist(sz):
    sz.setdefault("power_w", b_power(sz["stage_b"], sz["design"]))
    d = {k: np.array([v]) for k, v in sz["design"].items()}
    open(os.path.join(WORK, "midref_v2.spice"), "w").write(emit(d, header_text(sz)))
    print("REPORT: wrote work/midref_v2.spice")


A_KEYS = ("noise_lsb", "noise_dev_lsb", "noise_tap_lsb", "hr_f", "hr_f_mm", "hr_ib", "err_max", "power", "area",
          "sigma_diff_lsb", "t_settle_lin")


def a_record(e, i):
    return {"a_" + k: float(e[k][i]) for k in A_KEYS}


def b_power(r, s):
    """per-buffer power from the ngspice supply current (one divider per buffer in
    tb_op); a shared tap is counted half to each buffer."""
    i = r.get("isup_typ_ua", np.nan) * 1e-6
    if float(s["share"]) > 0.5:
        i -= 0.5 * VDD / (2 * float(s["r_half"]))
    return VDD * i


def calibrate(rng, P, N, NZ, CT):
    """ngspice / table on a stratified sample of loosely-screened designs:
    noise (median ratio) and follower headroom (median offset, PVT minimum)."""
    s = sample_uniform(rng, int(os.environ.get("POINTS", "40000")), P, N)
    e = evaluate(s, P, N, NZ, CT)
    raw = e["noise_lsb"] / NOISE_CAL
    loose = (np.isfinite(e["power"]) & np.isfinite(raw) & (e["hr_f"] >= -0.25) & (e["hr_ib"] >= 0)
             & (e["err_max"] <= 0.1) & (raw <= 0.3) & (e["sigma_diff_lsb"] <= 3.0))
    idx = np.flatnonzero(loose)
    n_cal = int(os.environ.get("N_CAL", "40"))
    o = idx[np.argsort(e["power"][idx])]
    pick = o[np.linspace(0, o.size - 1, min(n_cal, o.size)).round().astype(int)]
    print(f"REPORT: calibration: {idx.size} loosely feasible of {s['nf_1'].size}; {pick.size} to ngspice")
    res = stage_b(take(s, pick), [f"cal_{i}" for i in pick])
    rows = []
    for i, r in zip(pick, res):
        if "nz_lsb" in r and "hr_f_min" in r:
            rows.append(dict(idx=int(i), noise_tab=float(raw[i]), noise_ng=r["nz_lsb"],
                             hr_tab=float(e["hr_f"][i]), hr_ng=r["hr_f_min"],
                             err_tab=float(e["err_max"][i]), err_ng=r.get("err_max_mv", np.nan) / 1e3,
                             power_tab=float(e["power"][i]), power_ng=b_power(r, take(s, i))))
    if len(rows) < 8:
        print("FAIL: calibration: fewer than 8 designs simulated")
        return 1
    with open(os.path.join(DATA, "calibration.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    q = lambda a: np.nanpercentile(a, [10, 50, 90])
    rn = q(np.array([x["noise_ng"] / x["noise_tab"] for x in rows]))
    dh = q(np.array([x["hr_ng"] - x["hr_tab"] for x in rows]))
    de = q(np.array([x["err_ng"] - x["err_tab"] for x in rows]) * 1e3)
    rp = q(np.array([x["power_ng"] / x["power_tab"] for x in rows]))
    print(f"REPORT: calibration on {len(rows)} designs (p10 / median / p90): noise ngspice/table "
          f"{rn[0]:.3f} / {rn[1]:.3f} / {rn[2]:.3f}; headroom ngspice-table {dh[0]:+.3f} / {dh[1]:+.3f} / "
          f"{dh[2]:+.3f} V; |error| ngspice-table {de[0]:+.1f} / {de[1]:+.1f} / {de[2]:+.1f} mV; "
          f"power ngspice/table {rp[0]:.3f} / {rp[1]:.3f} / {rp[2]:.3f}")
    json.dump(dict(noise_cal=float(rn[1]), hr_cal=float(dh[1]), n=len(rows),
                   noise_p10_p90=[float(rn[0]), float(rn[2])], hr_p10_p90=[float(dh[0]), float(dh[2])]),
              open(os.path.join(DATA, "calibration.json"), "w"), indent=1)
    print(f"cal_noise = {rn[1]:.4f}")
    print(f"cal_hr_v = {dh[1]:.4f}")
    return 0


def recalibrate():
    """Refine data/calibration.json from the ngspice records of a front search
    (data/stage_b.json; each record carries the table prediction a_*). Front
    designs sit on the headroom boundary, where the random-sample median of
    PHASE=CAL is too optimistic: the headroom correction becomes the p10 of
    (ngspice PVT minimum - table screen), the noise factor its median."""
    r = [x for x in json.load(open(os.path.join(DATA, "stage_b.json")))
         if x.get("op_cells") == 45 and "hr_f_min" in x and "a_hr_f" in x]
    cal = json.load(open(_CAL_PATH))
    dh = np.array([x["hr_f_min"] - x["a_hr_f"] for x in r])
    rn = np.array([x["nz_lsb"] / x["a_noise_lsb"] for x in r if np.isfinite(x.get("nz_lsb", np.nan))])
    q = lambda a: np.nanpercentile(a, [10, 50, 90])
    h, n = q(dh), q(rn)
    out = dict(noise_cal=float(cal["noise_cal"] * n[1]), hr_cal=float(h[0]), n=len(r),
               source="PHASE=RECAL on data/stage_b.json of the first front search (2026-10-07)",
               hr_p10_p50_p90=[float(x) for x in h], noise_ratio_p10_p50_p90=[float(x) for x in n],
               previous=cal)
    json.dump(out, open(_CAL_PATH, "w"), indent=1)
    print(f"REPORT: recalibration on {len(r)} front designs: headroom ngspice - table {h[0]:+.3f} / {h[1]:+.3f} / "
          f"{h[2]:+.3f} V (p10 used), noise ngspice / table {n[0]:.3f} / {n[1]:.3f} / {n[2]:.3f} (median used)")
    print(f"cal_noise = {out['noise_cal']:.4f}")
    print(f"cal_hr_v = {out['hr_cal']:.4f}")
    return 0


def header_text(sz):
    g = lambda k: float(sz["design"][k])
    a, rb, power = sz["stage_a"], sz["stage_b"], sz["power_w"]
    return "\n".join([
        "* midref_v2 -- FVF class-AB VDD/2 buffer (VREF / VBL of the 8-bit bottom-plate cell),",
        "* the topology of ../midrail_ref_bkp/midrail_ref re-sized 2026-10-07 with every L in 0.28..0.36 um,",
        "* one finger width per flavour, gm/Id-sampled whole fingers, divider + tap + output",
        "* capacitor in the search, power x area knee. GENERATED by size_v2.py; do not hand-edit.",
        "* Bias: an IDEAL current into port ib (one NMOS diode finger, XMBN).",
        f"*   i_f {g('i_f') * 1e6:.4g} uA, IB = {int(g('nf_ib'))} fingers, output ratio K {int(g('k'))}",
        f"*   area {a['area']:.0f} um2 per buffer (MOS {a['a_mos']:.1f}, poly {a['a_res']:.0f}, MIM {a['a_mim']:.0f};"
        " a shared divider counted half) [P]",
        f"*   power {power * 1e6:.1f} uW per buffer at typical/27 C/3.3 V, the shared tap counted half [M];"
        f" VREF + VBL noise {rb.get('nz_lsb', float('nan')):.4f} LSB [M]",
        f"*   divider {'shared by VREF and VBL (use midref_div + midref_buf)' if g('share') > 0.5 else 'one per buffer (midref2)'}",
        "* Ports: midref_div (vin vdd vss); midref_buf (out vin ib vdd vss); midref2 (out ib vdd vss).",
        "* The simulators are the authority, not these lines.", ""])


def model_check(rng, P, N, NZ, n=16):
    """table operating point vs ngspice op (typical, 27 C, 3.3 V) on random designs."""
    s = sample_uniform(rng, 4000, P, N)
    o = solve_op(s, P, N, VDD)
    ok = np.flatnonzero(np.isfinite(o["out"]) & np.isfinite(o["i_sup"]))
    pick = rng.choice(ok, min(n, ok.size), replace=False)
    def one(i):
        d = os.path.join(WORK, "chk", str(i))
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
        open(os.path.join(d, "dut.spice"), "w").write(emit(take(s, np.array([i]))))
        open(os.path.join(d, "op.spice"), "w").write(fill("tb_op.spice", dict(
            CORNER="typical", MIMCORNER="typical", TEMP=27, IF="%.6g" % s["i_f"][i], TAG="typical 27 1")))
        txt = ngspice(d, "op.spice")
        m = re.search(r"^OP \S+ \S+ \S+ 3.3 (.*)$", txt, re.M)
        x = re.search(r"^OPX \S+ \S+ \S+ 3.3 (.*)$", txt, re.M)
        return [float(v) for v in m.group(1).split()] + [float(v) for v in x.group(1).split()] if m and x else None
    with ThreadPoolExecutor(JOBS) as ex:
        res = list(ex.map(one, pick))
    print("CHK idx  hr1(tab/ng)  hr4(tab/ng)  err_mV(tab/ng)  isup_uA(tab/ng)")
    for i, r in zip(pick, res):
        if r is None:
            print(f"CHK {i} ngspice failed")
            continue
        print(f"CHK {i} {o['hr']['m1'][i]:+.3f}/{r[0]:+.3f}  {o['hr']['m4'][i]:+.3f}/{r[1]:+.3f}  "
              f"{o['err'][i]*1e3:+.2f}/{r[8]*1e3:+.2f}  {o['i_sup'][i]*1e6:.3f}/{r[9]*1e6:.3f}")
        print(f"CHX {i} ibb {o['ibb'][i]*1e6:.3f}/{r[10]*1e6:.3f} ibt {o['ibt'][i]*1e6:.3f}/{r[11]*1e6:.3f} "
              f"i2 {o['i2'][i]*1e6:.3f}/{r[12]*1e6:.3f} p {o['p'][i]:.3f}/{r[13]:.3f} n {o['n'][i]:.3f}/{r[14]:.3f} "
              f"tap {r[15]*1e3:+.2f} mV")


if __name__ == "__main__":
    sys.exit(main())
