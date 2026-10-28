"""Sizing of comparator: the 10-device continuous comparator of the 8-bit
true bottom-plate cell (PMOS 5T OTA -> starved inverter -> output inverter,
the topology of ../comparator_bkp/comparator_updt_v2) re-sized on 2026-10-06 for:

  1. delay from the STATIC TRIP to dout <= 1/4 count = 12.5 ns (20 MHz count
     clock); the VBL-referenced delay is reported (user decision 2026-10-06)
  2. dout drives 10 fF (the TSPC latch plus wire; user)
  3. input-referred noise at the comparator pins, thermal + 1/f from 1 kHz
     over the comparator's own band, < 1.2 mV rms (user)
  4. every L <= 0.36 um (user: long devices cost area)
  5. pbias from an IDEAL current into a diode copy of the tail finger; the
     bias finger's current density J_D is a design variable (user)
  6. power and area minimised; the finger conventions of v2 kept: one
     finger width per flavour, buffer NMOS = XLOADM, identical buffers,
     buffer PMOS = 2 x W(XLOADM) in whole PMOS fingers

    ./container.sh 'python3 size_v3.py'               stage A (tables) + Pareto
    ./container.sh 'PHASE=B python3 size_v3.py'       + ngspice timing of front points
    ./container.sh 'PHASE=B SIZING_EMIT=1 python3 size_v3.py'   + rewrite comparator.spice

Stage A (tables only, no simulator): random search over (L, finger width,
finger counts, J_D) with gm/Id FOLLOWING from (W, L, I) through the short-L
pygmid tables built by lut/build.sh (L = 0.28..0.36 um). Noise comes from
data/device_noise.csv (ngspice .noise on single devices, same L grid).
Stage B (ngspice): front points timed in the cell's charge path (tb_sel),
static trip (tb_sel_dc) and noise (tb_nz). The simulator decides.
"""
import csv
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from pygmid import Lookup as lk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # size_p5t.py: copied in from the 6-bit comparator block
from size_p5t import grouped, grouped_at_vgs, grouped_vgs, pareto_mask, operating_point, VSB_GRID, VDS_BIN  # noqa: E402

BLOCK = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------ 1  requirements
VDD = 3.3
NBITS = 8
VR_LO, VR_HI = 0.5, 2.0                        # contract: the ramp on the bottom plate
LSB = (VR_HI - VR_LO) / 2 ** NBITS             # 5.859 mV  [D]
TCOUNT = 50e-9                                 # 20 MHz count clock [contract]
SLOPE = LSB / TCOUNT                           # 117.2 mV/us [D]
KT = 1.380649e-23 * 300.0
VCM_DEC = VDD / 2.0                            # inp = VBL = VDD/2 [D]
C_S = 54.52e-15                                # PDK: 5 x 5 um MIM
C_TOP_EXTRA = 0.63e-15 + 1.0e-15               # S2 [M] + wire [A]
DELAY_MAX = 0.25 * TCOUNT                      # USER: 12.5 ns, from the static trip
LOWEND_SPREAD_MAX = 0.1 * TCOUNT               # SPEC item 10
FALL_MAX = 6.0e-9                              # [M] slowest d edge the TSPC latch was verified with
C_LOAD_DOUT = 10e-15                           # USER: the TSPC latch + wire
NOISE_MAX_V = 1.2e-3                           # USER: rms at the comparator pins
F_NOISE_LO = 1e3                               # USER choice: band starts at 1 kHz
SIGMA_IN_BUDGET_LSB = 4.0 / 3.0                # contract (at the ADC input)
SIGMA_GATE_LSB = float(os.environ.get("SIGMA_GATE_LSB", 0.95 * SIGMA_IN_BUDGET_LSB))   # model gate
PEDESTAL_BUDGET_LSB = 8.0                      # contract
OVERRUN_COUNTS = 20.0                          # contract
S2_INJ_LSB = 1.2                               # [M] runs/unit-cell-bps/20261002T000647Z
K_DEAD_BUDGET_LSB = 1.0                        # contract
T_ARM = 90e-9                                  # contract
T_TRACK = 300e-9                               # contract
BIAS_SCALE_HI, BIAS_SCALE_LO = 1.77, 0.69      # [M] ../bias_gen_bkp/bias_gen PVT span: robustness gates on headroom only
VDD_MIN = 3.0                                  # [A]
HEADROOM_MARGIN = 0.20                         # [A]
C_WIRE_OUTA, C_WIRE_OUTB = 5e-15, 2e-15        # [A] PEX replaces
VDS_STARVE = 1.0                               # [A] XBST's VDS when it conducts
# PDK DRC (gf180mcu.drc contact.rb): CO.1 0.22 um contact, CO.4 0.07 COMP
# enclosure, CO.7 0.15 contact-to-poly -> a shared contacted S/D strip is
# 0.52 um, an end strip 0.44 um. Footprint of a device = W_f x (nf L + (nf-1) 0.52 + 2 x 0.44)
SD_SHARED, SD_END = 0.52, 0.44
L_CHOICES = np.array([0.28, 0.30, 0.32, 0.34, 0.36])   # USER: L <= 0.36 um; the table grid
W_F_CHOICES = np.array([0.5e-6, 1.0e-6, 2.0e-6])        # one finger width per flavour
NF_IN_MAX, NF_LD_MAX, NF_B_MAX = 64, 48, 100
NF_REF = 1                                     # the bias reference diode: one tail finger [A]
W_BIN_MAX = 100e-6
PDK_MM = dict(pfet=dict(par_vth=0.00666, par_k=0.002833),
              nfet=dict(par_vth=0.007148, par_k=0.007008), par_l=0.15e-6, par_w=-0.1e-6)
VARS = ("l_in", "l_ld", "l_b", "w_fp", "w_fn", "nf_in", "nf_ld", "nf_tail", "nf_st", "i_f")
GMID_GRID = np.linspace(3.0, 26.0, 116)
VGS_GRID = np.arange(0.30, 2.60, 0.0125)
LUT_DIR = os.environ.get("GMID_LUT_DIR", os.path.join(BLOCK, "work", "lut"))
JOBS = int(os.environ.get("JOBS", "12"))
LEVELS = (("c4", 4.5, 1.0), ("plat", 40.5, 1.0))
LEVELS_REPORT = (("plo", 40.5, BIAS_SCALE_LO), ("phi", 40.5, BIAS_SCALE_HI))
# Calibration of the table transient against ngspice (PHASE=CAL writes data/calibration.json):
# the medians of ngspice / model for the delay from the static trip and the dout fall.
_CAL_PATH = os.path.join(BLOCK, "data", "calibration.json")
_CAL = json.load(open(_CAL_PATH)) if os.environ.get("USE_CAL", "1") == "1" and os.path.exists(_CAL_PATH) else {}
DELAY_CAL = float(os.environ.get("DELAY_CAL", _CAL.get("delay_cal", 1.0)))
FALL_CAL = float(os.environ.get("FALL_CAL", _CAL.get("fall_cal", 1.0)))


# ------------------------------------------------------------ device noise (data/device_noise.csv)
class Noise:
    """Gate-referred noise per (flavour, L, gm/Id) from ngspice .noise on one
    W = 2 um device. S(f) = A (f/1k)^-af + B: A and af from the 1k/10k/100k
    points, B (thermal) from 100 MHz minus the flicker tail. Stored per unit
    area (A W L) and as gamma = B gm / 4kT, so a device of any W, L and
    current reads A/(W L) and 4 kT gamma / gm."""

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

    def get(self, dev, L, gmid):
        out = [np.empty(gmid.shape) for _ in range(3)]
        for lv in np.unique(L):
            m = L == lv
            g, awl, af, gam = self.t[(dev, round(float(lv), 2))]
            for j, col in enumerate((awl, af, gam)):
                out[j][m] = np.interp(gmid[m], g, col)
        return out          # A x W x L [V^2/Hz m^2 at 1 kHz], af, gamma


def flicker_int(a, af, f_lo, f_hi):
    """integral of a (f/1k)^-af df from f_lo to f_hi (closed form)."""
    x0, x1 = f_lo / 1e3, np.maximum(f_hi, f_lo * 1.0001) / 1e3
    e = 1.0 - af
    near = np.abs(e) < 1e-3
    pw = np.where(near, 0.0, (x1 ** np.where(near, 1.0, e) - x0 ** np.where(near, 1.0, e)) / np.where(near, 1.0, e))
    return a * 1e3 * np.where(near, np.log(x1 / x0), pw)


# ------------------------------------------------------------ table helpers
def _keys(L, vds, vsb):
    vds_b = np.round(np.clip(vds, 0.05, 3.3) / VDS_BIN) * VDS_BIN
    vsb_b = VSB_GRID[np.abs(np.asarray(vsb)[:, None] - VSB_GRID[None, :]).argmin(1)]
    return vds_b, vsb_b, (L * 1e4).astype(np.int64) * 10_000_000 + (vds_b * 1e4).astype(np.int64) * 1000 \
        + (vsb_b * 1e4).astype(np.int64)


def gmid_from_idw(table, idw, L, vds, vsb):
    """gm/Id of a device whose current density is imposed (W, I given)."""
    out = np.full(idw.shape, np.nan)
    vds_b, vsb_b, key = _keys(L, vds, vsb)
    for k in np.unique(key):
        m = key == k
        g = np.asarray(table.look_up("ID_W", GM_ID=GMID_GRID, L=float(L[m][0]),
                                     VDS=float(vds_b[m][0]), VSB=float(vsb_b[m][0]))).ravel()
        ok = np.isfinite(g) & (g > 0)
        if ok.sum() < 4:
            continue
        gg, gm = g[ok], GMID_GRID[ok]
        o = np.argsort(gg)
        out[m] = np.interp(idw[m], gg[o], gm[o], left=np.nan, right=np.nan)
    return out


class PerL:
    """XBUF1's VGS(ID/W) at VDS = VDD/2, |VT_p|, and the buffer inverter
    (W_p = 2 W_n, same L) per metre of W_n, cached per L."""

    def __init__(self, nfet, pfet):
        self.nfet, self.pfet, self.c = nfet, pfet, {}

    def get(self, L):
        L = round(float(L), 2)
        if L in self.c:
            return self.c[L]
        n, p = self.nfet, self.pfet
        look = lambda t, out, vgs, vds: float(np.asarray(t.look_up(out, VGS=vgs, L=L, VDS=vds, VSB=0.0)).ravel()[0])
        idw_n = np.array([look(n, "ID_W", v, VDD / 2) for v in VGS_GRID])
        vg = np.arange(0.4, 2.9, 0.0125)
        i_n = np.array([look(n, "ID_W", g, VDD / 2) for g in vg])
        i_p = np.array([2.0 * look(p, "ID_W", VDD - g, VDD / 2) for g in vg])
        v_m = float(np.interp(0.0, i_n - i_p, vg))
        gm_n = look(n, "ID_W", v_m, VDD / 2) * look(n, "GM_ID", v_m, VDD / 2)
        gm_p = 2.0 * look(p, "ID_W", VDD - v_m, VDD / 2) * look(p, "GM_ID", VDD - v_m, VDD / 2)
        gds_n = gm_n / look(n, "GM_GDS", v_m, VDD / 2)
        gds_p = gm_p / look(p, "GM_GDS", VDD - v_m, VDD / 2)
        r = dict(idw_n=idw_n,
                 vthp=abs(float(np.asarray(p.look_up("VT", VGS=1.0, L=L, VDS=1.65, VSB=0.0)).ravel()[0])),
                 v_m=v_m, a_inv=(gm_n + gm_p) / (gds_n + gds_p),
                 c_in=look(n, "CGG_W", v_m, VDD / 2) + 2.0 * look(p, "CGG_W", VDD - v_m, VDD / 2),
                 c_out=look(n, "CDD_W", 0.0, VDD / 2) + 2.0 * look(p, "CDD_W", 0.0, VDD / 2),
                 i_on=look(n, "ID_W", VDD, VDD / 2),
                 cgd_n=look(n, "CGD_W", v_m, VDD / 2), cgd_p=look(p, "CGD_W", VDD - v_m, VDD / 2))
        self.c[L] = r
        return r

    def column(self, L, key):
        return np.array([self.get(x)[key] for x in L])

    def vgs_n1(self, L, idw):
        out = np.full(idw.shape, np.nan)
        for lv in np.unique(L):
            m = L == lv
            out[m] = np.interp(idw[m], self.get(lv)["idw_n"], VGS_GRID, left=np.nan, right=np.nan)
        return out


def sigma_pair(par, w_m, l_um):
    leff = np.maximum(l_um * 1e-6 - PDK_MM["par_l"], 0.05e-6)
    weff = np.maximum(w_m - PDK_MM["par_w"], 0.1e-6)
    return par * 1e-6 / np.sqrt(leff * weff)


def plateau_trip(v_bal, v_pre, v_trip, a_s, tau):
    """One pole driven by the attenuated ramp, released from V_pre (input
    crosses VBL at t = 0); time at which v(t) reaches V_trip."""
    t0 = -(v_pre - v_bal) / a_s
    vt = lambda t: v_bal + a_s * (tau - t) - a_s * tau * np.exp(-(t - t0) / tau)
    lo, hi = t0.copy(), np.abs(t0) + 20.0 * tau + v_pre / a_s
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        above = vt(mid) > v_trip
        lo, hi = np.where(above, mid, lo), np.where(above, hi, mid)
    return 0.5 * (lo + hi)


def starve_time(T, k):
    """Solve u - (1 - exp(-k u))/k = T: the starved node charges with
    I_st (1 - exp(-k u)) as XBUF1 is turned off by outa falling at a_s
    (k = gm/Id_n1 x a_s); T = C_outb V_m / I_st."""
    u = T + 1.0 / k
    for _ in range(30):
        f = u - (1.0 - np.exp(-k * u)) / k - T
        u = np.maximum(u - f / (1.0 - np.exp(-k * u) + 1e-12), 1e-15)
    return u


def footprint(w_f, nf, L):
    """um^2: nf fingers of w_f, shared contacted S/D strips (PDK DRC), m-split above 50."""
    m = np.ceil(nf / 50.0)
    nfi = nf / m
    return m * w_f * 1e6 * (nfi * L + (nfi - 1) * SD_SHARED + 2 * SD_END)


# ------------------------------------------------------------ sampling: gm/Id targets -> integer fingers
def sample_uniform(rng, n, tabs):
    pfet, nfet = tabs
    l_in, l_ld, l_b = (rng.choice(L_CHOICES, n) for _ in range(3))
    w_fp, w_fn = rng.choice(W_F_CHOICES, n), rng.choice(W_F_CHOICES, n)
    # bias finger: its gm/Id sets J_D (diode, VDS = VSG)
    gmid_b = rng.uniform(5.0, 20.0, n)
    vsg = np.full(n, 1.0)
    for _ in range(2):
        vsg = grouped_vgs(pfet, gmid_b, l_b, vsg, np.zeros(n))
    i_f = grouped(pfet, "ID_W", gmid_b, l_b, vsg, np.zeros(n)) * w_fp
    i_tail = np.exp(rng.uniform(np.log(1e-6), np.log(80e-6), n))
    k_st = np.exp(rng.uniform(np.log(0.6), np.log(5.0), n))
    nf_tail = np.clip(np.round(i_tail / i_f), 1, NF_B_MAX)
    nf_st = np.clip(np.round(k_st * nf_tail * i_f / 2 / i_f), 1, NF_B_MAX)
    ib = nf_tail * i_f / 2
    gi = rng.uniform(8.0, 24.0, n)
    gl = rng.uniform(4.0, 18.0, n)
    j_in = grouped(pfet, "ID_W", gi, l_in, np.full(n, 1.0), np.full(n, 0.2))
    j_ld = grouped(nfet, "ID_W", gl, l_ld, np.full(n, 0.8), np.zeros(n))
    nf_in = np.clip(np.round(ib / j_in / w_fp), 1, NF_IN_MAX)
    nf_ld = np.clip(np.round(ib / j_ld / w_fn), 1, NF_LD_MAX)
    return dict(l_in=l_in, l_ld=l_ld, l_b=l_b, w_fp=w_fp, w_fn=w_fn, nf_in=nf_in, nf_ld=nf_ld,
                nf_tail=nf_tail, nf_st=nf_st, i_f=i_f)


def sample_local(rng, parent, n):
    k = rng.integers(0, parent["nf_in"].size, n)

    def step_l(v):
        idx = np.searchsorted(L_CHOICES, v[k] - 1e-9)
        return L_CHOICES[np.clip(idx + rng.choice([-1, 0, 0, 0, 1], n), 0, L_CHOICES.size - 1)]

    def step_w(v):
        return np.where(rng.random(n) < 0.1, rng.choice(W_F_CHOICES, n), v[k])

    def step_n(v, hi):
        d = rng.integers(-2, 3, n) + np.round(rng.normal(0.0, 0.08, n) * v[k])
        return np.clip(v[k] + d, 1, hi)

    return dict(l_in=step_l(parent["l_in"]), l_ld=step_l(parent["l_ld"]), l_b=step_l(parent["l_b"]),
                w_fp=step_w(parent["w_fp"]), w_fn=step_w(parent["w_fn"]),
                nf_in=step_n(parent["nf_in"], NF_IN_MAX), nf_ld=step_n(parent["nf_ld"], NF_LD_MAX),
                nf_tail=step_n(parent["nf_tail"], NF_B_MAX), nf_st=step_n(parent["nf_st"], NF_B_MAX),
                i_f=parent["i_f"][k] * np.exp(rng.normal(0.0, 0.1, n)))


# ------------------------------------------------------------ stage A model
def evaluate(v, pfet, nfet, perl, nz):
    n = v["nf_in"].size
    z = np.zeros(n)
    l_in, l_ld, l_b = (v[k].astype(float) for k in ("l_in", "l_ld", "l_b"))
    w_fp, w_fn, i_f = (v[k].astype(float) for k in ("w_fp", "w_fn", "i_f"))
    nf_in, nf_ld, nf_tail, nf_st = (v[k].astype(float) for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"))
    w_in, w_ld = nf_in * w_fp, nf_ld * w_fn
    w_pb = 2.0 * w_ld
    nf_pb = w_pb / w_fp
    j_b = i_f / w_fp
    # the reference diode (ideal current i_f into one tail finger): its VSG
    gmid_b = gmid_from_idw(pfet, j_b, l_b, np.full(n, 1.0), z)
    vsg_b = np.full(n, 1.0)
    for _ in range(3):
        gmid_b = gmid_from_idw(pfet, j_b, l_b, vsg_b, z)
        vsg_b = grouped_vgs(pfet, np.where(np.isfinite(gmid_b), gmid_b, 10.0), l_b, vsg_b, z)
    # tail: its current at its OWN VDS (short-L mirror; the VDS error is real)
    i_tail = nf_tail * i_f
    vds_in, vsb_in, v_left = np.full(n, 1.5), np.full(n, 0.3), np.full(n, 0.8)
    gi = gl = np.full(n, 10.0)
    for _ in range(4):
        id_branch = i_tail / 2.0
        gmid_in = gmid_from_idw(pfet, id_branch / w_in, l_in, vds_in, vsb_in)
        gmid_ld = gmid_from_idw(nfet, id_branch / w_ld, l_ld, v_left, z)
        ok_g = np.isfinite(gmid_in) & np.isfinite(gmid_ld) & np.isfinite(gmid_b)
        gi, gl = np.where(ok_g, gmid_in, 10.0), np.where(ok_g, gmid_ld, 10.0)
        op = operating_point(pfet, nfet, gi, l_in, gl, l_ld, gi, l_b, id_branch, VCM_DEC, np.zeros(n, dtype=bool))
        vds_in, vsb_in, v_left = op["vds_in"], op["vsb_in"], op["v_left"]
        headroom = VDD - op["v_tail"]
        i_tail = nf_tail * w_fp * grouped_at_vgs(pfet, "ID_W", vsg_b, l_b, np.clip(headroom, 0.05, 3.3), 0.0)
    gmid_in, gmid_ld = gi, gl
    id_branch = i_tail / 2.0
    v_tail = op["v_tail"]
    mirror_err = i_tail / (nf_tail * i_f) - 1.0
    i_st = nf_st * w_fp * grouped_at_vgs(pfet, "ID_W", vsg_b, l_b, np.full(n, VDS_STARVE), 0.0)
    v_trip = perl.vgs_n1(l_ld, i_st / w_ld)
    ok_trip = np.isfinite(v_trip)
    v_trip = np.where(ok_trip, v_trip, v_left)
    dv_trip = v_trip - v_left
    vdsat_b = 2.0 / np.where(np.isfinite(gmid_b), gmid_b, 10.0)

    gds_id_in = gmid_in / grouped(pfet, "GM_GDS", gmid_in, l_in, vds_in, vsb_in)
    gds_id_ld = gmid_ld / grouped(nfet, "GM_GDS", gmid_ld, l_ld, v_left, z)
    gain_ota = gmid_in / (gds_id_in + gds_id_ld)
    offset_static = dv_trip / gain_ota
    gm_in = gmid_in * id_branch
    gm_ld = gmid_ld * id_branch
    gds_out = (gds_id_in + gds_id_ld) * id_branch
    gmid_n1 = grouped_at_vgs(nfet, "GM_ID", v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    gds_id_n1 = gmid_n1 / grouped_at_vgs(nfet, "GM_GDS", v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    gain_st = gmid_n1 / (2.0 * gds_id_n1)

    cdd_in = grouped(pfet, "CDD_W", gmid_in, l_in, vds_in, vsb_in)
    cdd_ld = grouped(nfet, "CDD_W", gmid_ld, l_ld, v_left, z)
    cgg_n1 = grouped_at_vgs(nfet, "CGG_W", v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    cgg_p2 = grouped_at_vgs(pfet, "CGG_W", VDD - v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    c_outa = w_in * cdd_in + w_ld * cdd_ld + w_ld * cgg_n1 + w_pb * cgg_p2 + C_WIRE_OUTA
    tau = c_outa / gds_out
    cdd_n1 = grouped_at_vgs(nfet, "CDD_W", v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    cdd_p2 = grouped_at_vgs(pfet, "CDD_W", VDD - v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    # gate-drain overlap of the buffers: the Miller couplings outa-outb (XBUF1/2) and outb-dout (XBUF3/4)
    c_m2 = w_ld * grouped_at_vgs(nfet, "CGD_W", v_trip, l_ld, np.full(n, VDD / 2), 0.0) \
        + w_pb * grouped_at_vgs(pfet, "CGD_W", VDD - v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    c_m3 = w_ld * perl.column(l_ld, "cgd_n") + w_pb * perl.column(l_ld, "cgd_p")
    # the starve node bst: XBST's drain + XBUF2's source
    c_bst = nf_st * w_fp * grouped_at_vgs(pfet, "CDD_W", vsg_b, l_b, np.full(n, VDS_STARVE), 0.0) \
        + w_pb * grouped_at_vgs(pfet, "CSS_W", VDD - v_trip, l_ld, np.full(n, VDD / 2), 0.0)
    oi_cin, oi_cout = perl.column(l_ld, "c_in") * w_ld, perl.column(l_ld, "c_out") * w_ld
    oi_ion, oi_vm, oi_a = perl.column(l_ld, "i_on") * w_ld, perl.column(l_ld, "v_m"), perl.column(l_ld, "a_inv")
    c_outb = oi_cin + w_ld * cdd_n1 + w_pb * cdd_p2 + C_WIRE_OUTB

    cgg_w = grouped(pfet, "CGG_W", gmid_in, l_in, vds_in, vsb_in)
    cgd_w = grouped(pfet, "CGD_W", gmid_in, l_in, vds_in, vsb_in)
    c_gg_in, c_gd_in = w_in * cgg_w, w_in * cgd_w
    alpha = C_S / (C_S + c_gg_in + C_TOP_EXTRA)

    # ---- closed-form delay (from the static trip): OTA lag + starved edge + half the dout fall.
    # A SCREEN only: against ngspice it read 2.4x slow on delay and up to 2x fast on the
    # fall (smoke run 2026-10-06); transient() below replaces both for the survivors.
    a_s = gain_ota * alpha * SLOPE                    # outa's slew under the attenuated ramp
    v_pre = v_tail
    t_ota = plateau_trip(v_left, v_pre, v_trip, a_s, tau)
    t_static = -dv_trip / a_s
    u_st = starve_time(c_outb * oi_vm / i_st, gmid_n1 * a_s)
    s_b = i_st * (1.0 - np.exp(-gmid_n1 * a_s * u_st)) / c_outb
    fall_cf = 0.8 * VDD / (oi_a * s_b) + 0.8 * VDD * (C_LOAD_DOUT + oi_cout) / oi_ion
    delay_cf = (t_ota - t_static) + u_st + 0.5 * fall_cf
    delay_dyn, delay_vbl, t_fall = (np.full(n, np.inf) for _ in range(3))

    # ---- noise at the pins: thermal + 1/f, 1 kHz .. the OTA's own pole
    a_in, af_in, gam_in = nz.get("pfet", l_in, gmid_in)
    a_ld, af_ld, gam_ld = nz.get("nfet", l_ld, gmid_ld)
    f_p = 1.0 / (2 * np.pi * tau)
    r_ld = (gm_ld / gm_in) ** 2
    s_th = 2.0 * 4 * KT * (gam_in / gm_in + r_ld * gam_ld / gm_ld)
    v2_th = s_th * (np.pi / 2 * f_p - F_NOISE_LO)
    v2_fl = 2.0 * (flicker_int(a_in / (w_in * l_in * 1e-6), af_in, F_NOISE_LO, f_p)
                   + r_ld * flicker_int(a_ld / (w_ld * l_ld * 1e-6), af_ld, F_NOISE_LO, f_p))
    noise_v = np.sqrt(v2_th + v2_fl)
    noise_th_v, noise_fl_v = np.sqrt(v2_th), np.sqrt(v2_fl)

    # ---- mismatch, pedestal, dead zone (formulas of ../comparator_bkp/comparator_updt_v2, recipe s.3)
    s_vt_in = sigma_pair(PDK_MM["pfet"]["par_vth"], w_in, l_in)
    s_k_in = sigma_pair(PDK_MM["pfet"]["par_k"], w_in, l_in)
    s_vt_ld = sigma_pair(PDK_MM["nfet"]["par_vth"], w_ld, l_ld)
    s_k_ld = sigma_pair(PDK_MM["nfet"]["par_k"], w_ld, l_ld)
    sigma_vos = np.sqrt(s_vt_in ** 2 + (s_k_in / gmid_in) ** 2 + (s_vt_ld * gmid_ld / gmid_in) ** 2
                        + (s_k_ld / gmid_in) ** 2)
    sigma_in_lsb = sigma_vos / alpha / LSB
    offset_in_lsb = offset_static / alpha / LSB
    gain_min = VDD / (alpha * 0.25 * LSB)
    v_cross = np.minimum(v_left + a_s * tau * (1.0 - np.exp(-(v_pre - v_left) / a_s / tau)), v_pre)
    offset_bps_lsb = c_gd_in * np.maximum(v_cross - v_left, 0.0) / C_S / LSB
    ped_base = np.abs(offset_in_lsb) + offset_bps_lsb + S2_INJ_LSB
    pedestal_lsb = ped_base + np.abs(delay_cf + t_static) / TCOUNT          # re-read after transient()
    window_counts = pedestal_lsb + 3.0 * sigma_in_lsb
    dvp = np.maximum(dv_trip, 0.0)
    k_dead = dvp / (gain_ota * (1.0 - np.exp(-T_ARM / tau))) / (alpha * LSB) + c_gd_in * dvp / C_S / LSB

    # ---- headroom at 1x, and at the bias generator's 1.77x end (also at 3.0 V): robustness
    j_hi = BIAS_SCALE_HI * id_branch / w_in
    gmid_in_hi = gmid_from_idw(pfet, j_hi, l_in, vds_in, vsb_in)
    vsg_in_hi = grouped_vgs(pfet, np.where(np.isfinite(gmid_in_hi), gmid_in_hi, 6.0), l_in, vds_in, vsb_in)
    gmid_b_hi = gmid_from_idw(pfet, BIAS_SCALE_HI * j_b, l_b, vsg_b, z)
    vdsat_b_hi = 2.0 / np.where(np.isfinite(gmid_b_hi), gmid_b_hi, 6.0)
    headroom_hi = VDD - (VCM_DEC + vsg_in_hi)
    headroom_hi_vmin = VDD_MIN / 2.0 - vsg_in_hi

    power = VDD * (2.0 * id_branch + i_st)
    area = (2 * footprint(w_fp, nf_in, l_in) + 4 * footprint(w_fn, nf_ld, l_ld) + footprint(w_fp, nf_tail, l_b)
            + footprint(w_fp, nf_st, l_b) + 2 * footprint(w_fp, nf_pb, l_ld))
    gate_area = (2 * w_in * l_in + 4 * w_ld * l_ld + (nf_tail + nf_st) * w_fp * l_b + 2 * w_pb * l_ld) * 1e6
    e = {k: np.asarray(x) for k, x in v.items()}
    e.update(w_in=w_in, w_ld=w_ld, w_pb=w_pb, nf_pb=nf_pb, j_b=j_b, gmid_b=gmid_b, vsg_b=vsg_b, i_tail=i_tail,
             id_branch=id_branch, i_st=i_st, k_st=i_st / id_branch, mirror_err=mirror_err, gmid_in=gmid_in,
             gmid_ld=gmid_ld, ok_g=ok_g, ok_trip=ok_trip, v_left=v_left, v_tail=v_tail, v_trip=v_trip,
             dv_trip=dv_trip, headroom=headroom, vdsat_b=vdsat_b, gain_ota=gain_ota, gain_st=gain_st,
             gmid_n1=gmid_n1, gm_in=gm_in, c_outa=c_outa, c_outb=c_outb, tau=tau, f_p=f_p, c_gg_in=c_gg_in,
             c_gd_in=c_gd_in, alpha=alpha, a_s=a_s, t_ota=t_ota, t_static=t_static, u_st=u_st, t_fall=t_fall,
             delay_cf=delay_cf, fall_cf=fall_cf, ped_base=ped_base, v_pre=v_pre, gds_out=gds_out, c_d=C_LOAD_DOUT + oi_cout,
             gm_ld=gm_ld, oi_vm=oi_vm, c_m2=c_m2, c_m3=c_m3, c_bst=c_bst, sim=np.zeros(n, dtype=bool),
             delay_c=np.full(n, np.inf), fall_c=np.full(n, np.inf),
             delay_dyn=delay_dyn, delay_vbl=delay_vbl, noise_v=noise_v, noise_th_v=noise_th_v,
             noise_fl_v=noise_fl_v, noise_adc_lsb=noise_v / alpha / LSB, sigma_vos=sigma_vos,
             sigma_in_lsb=sigma_in_lsb, offset_in_lsb=offset_in_lsb, gain_min=gain_min,
             pedestal_lsb=pedestal_lsb, window_counts=window_counts, k_dead=k_dead,
             headroom_1p77=headroom_hi, headroom_1p77_vmin=headroom_hi_vmin, vdsat_b_1p77=vdsat_b_hi,
             power=power, area=area, gate_area=gate_area, gain_oi=oi_a)
    return e


class IV:
    """ID/W(VGS, VDS) at VSB = 0 per L straight from the short-L tables
    (25 mV grid), bilinear, vectorised: the large-signal device curves the
    transient needs. pfet axes are magnitudes (VSG, VSD)."""

    def __init__(self, lut_dir):
        import pickle
        self.t, self.L = {}, None
        for dev in ("nfet", "pfet"):
            d = pickle.load(open(os.path.join(lut_dir, f"{dev}_03v3.pkl"), "rb"))
            self.t[dev] = np.ascontiguousarray(d["ID"][:, :, :, 0] / d["W"])
            self.L = np.asarray(d["L"], dtype=float)
            self.step = float(d["VGS"][1] - d["VGS"][0])
        self.n = self.t["nfet"].shape[1]

    def il(self, L):
        return np.abs(np.asarray(L)[:, None] - self.L[None, :]).argmin(1)

    def __call__(self, dev, il, vgs, vds):
        t = self.t[dev]
        x = np.clip(vgs / self.step, 0.0, self.n - 1.001)
        y = np.clip(vds / self.step, 0.0, self.n - 1.001)
        i, j = x.astype(np.int64), y.astype(np.int64)
        fx, fy = x - i, y - j
        return ((t[il, i, j] * (1 - fx) + t[il, i + 1, j] * fx) * (1 - fy)
                + (t[il, i, j + 1] * (1 - fx) + t[il, i + 1, j + 1] * fx) * fy)



def transient(e, idx, iv, dt=50e-12, newton=2, t_after=60e-9):
    """Behavioural transient of the plateau case for the designs `idx`, on
    the tables only (no simulator). Four nodes:
      outa: C_outa, g_out, driven by the 5T OTA's large-signal output current
            -I_tail tanh(gm v_d / I_tail), v_d = alpha SLOPE t (t = 0 when the
            top plate crosses VBL); clipped to [0, V_tail]
      bst:  XBST (gate at the reference's VSG, finite r_o from the table) into XBUF2
      outb: XBUF2 (gate outa, source bst) against XBUF1 (gate outa)
      dout: XBUF4 against XBUF3 (gate outb) into 10 fF + drains
    The buffers' gate-drain overlaps couple outa-outb and outb-dout (Miller).
    Backward Euler with Newton on the coupled nodes (they are stiff). The
    static trip is the DC point where outb sits at the output inverter's
    threshold. Returns delay_dyn, delay_vbl, the 10-90 % dout fall, outa's trip."""
    g = lambda k: e[k][idx].astype(float)
    n = len(idx)
    il_d = iv.il(g("l_ld"))
    il_b = iv.il(g("l_b"))
    w_ld, w_pb, w_st = g("w_ld"), g("w_pb"), g("nf_st") * g("w_fp")
    i_tail, gm, gds, c_a = 2 * g("id_branch"), g("gm_in"), g("gds_out"), g("c_outa")
    c_b, c_d, c_bst, vsg_b = g("c_outb"), g("c_d"), g("c_bst"), g("vsg_b")
    v_left, v_pre, alpha, tau, vm = g("v_left"), g("v_pre"), g("alpha"), g("tau"), g("oi_vm")

    def i_st(bst):                       # XBST, out of bst's node
        return w_st * iv("pfet", il_b, vsg_b, np.maximum(VDD - bst, 0.0))

    def i_p2(oa, bst, ob):               # XBUF2, bst -> outb
        return w_pb * iv("pfet", il_d, np.maximum(bst - oa, 0.0), np.maximum(bst - ob, 0.0))

    def i_n1(oa, ob):
        return w_ld * iv("nfet", il_d, oa, ob)

    def i_dout(ob, d):
        return w_pb * iv("pfet", il_d, VDD - ob, np.maximum(VDD - d, 0.0)) - w_ld * iv("nfet", il_d, ob, d)

    def bisect(fun, lo, hi, it=40):
        """root of a function decreasing in its argument on [lo, hi]."""
        for _ in range(it):
            mid = 0.5 * (lo + hi)
            pos = fun(mid) > 0
            lo, hi = np.where(pos, mid, lo), np.where(pos, hi, mid)
        return 0.5 * (lo + hi)

    def bst_dc(oa, ob):
        return bisect(lambda b: i_st(b) - i_p2(oa, b, ob), ob, np.full(n, VDD), 30)

    def up_dc(oa, ob):
        return i_st(bst_dc(oa, ob))

    # static trip: outa at which outb sits at the inverter threshold, then the input that holds it
    v_s = bisect(lambda oa: up_dc(oa, vm) - i_n1(oa, vm), np.zeros(n), v_pre.copy())
    x = np.clip(-gds * (v_s - v_left) / i_tail, -0.999999, 0.999999)
    t_cs = (i_tail / gm) * np.arctanh(x) / (alpha * SLOPE)
    # window: from before the static crossing to t_after past it (slower designs fail the 12.5 ns gate anyway)
    t0 = t_cs - (5.0 * np.minimum(tau, 15e-9) + 20e-9)
    steps = int(np.ceil((5.0 * np.minimum(tau, 15e-9).max() + 20e-9 + t_after) / dt))
    t = t0.copy()
    oa = np.clip(v_left - i_tail * np.tanh(gm * alpha * SLOPE * t / i_tail) / gds, 0.0, v_pre)
    ob = bisect(lambda o: up_dc(oa, o) - i_n1(oa, o), np.zeros(n), np.full(n, VDD), 30)
    bs = bst_dc(oa, ob)
    d = bisect(lambda dd: i_dout(ob, dd), np.zeros(n), np.full(n, VDD))
    t90, t50, t10 = (np.full(n, np.nan) for _ in range(3))
    # capacitance matrix of (outa, bst, outb, dout): ground parts plus the Miller couplings
    # (c_outa, c_outb and c_dout already contain the overlaps, so they come off the ground part)
    cm2, cm3 = g("c_m2"), g("c_m3")
    cag = np.maximum(c_a - cm2, 0.2e-15)
    cbg = np.maximum(c_b - cm2 - cm3, 0.2e-15)
    cdg = np.maximum(c_d - cm3, 0.2e-15)
    M = np.zeros((n, 4, 4))
    M[:, 0, 0], M[:, 0, 2] = cag + cm2, -cm2
    M[:, 1, 1] = c_bst
    M[:, 2, 0], M[:, 2, 2], M[:, 2, 3] = -cm2, cbg + cm2 + cm3, -cm3
    M[:, 3, 2], M[:, 3, 3] = -cm3, cdg + cm3
    Md = M / dt
    h = 1e-3

    def currents(i_ota, x):
        oa_, b_, ob_, d_ = x[:, 0], x[:, 1], x[:, 2], x[:, 3]
        ip2 = i_p2(oa_, b_, ob_)
        return np.stack([i_ota + gds * (v_left - oa_), i_st(b_) - ip2, ip2 - i_n1(oa_, ob_), i_dout(ob_, d_)], axis=1)

    hi_clip = np.stack([v_pre, np.full(n, VDD), np.full(n, VDD), np.full(n, VDD)], axis=1)
    x = np.stack([oa, bs, ob, d], axis=1)
    if os.environ.get("TDEBUG"):
        print("TDEBUG start", x[:5], "v_s", v_s[:5], "t_cs", t_cs[:5], "t0", t0[:5], "vm", vm[:5])
    for _ in range(steps):
        t = t + dt
        i_ota = -i_tail * np.tanh(gm * alpha * SLOPE * t / i_tail)
        x0 = x.copy()
        for _ in range(newton):
            fi = currents(i_ota, x)
            J = np.empty((n, 4, 4))
            for k in range(4):
                xp = x.copy()
                xp[:, k] += h
                J[:, :, k] = (currents(i_ota, xp) - fi) / h
            F = np.einsum("nij,nj->ni", Md, x - x0) - fi
            x = np.clip(x - np.linalg.solve(Md - J, F[:, :, None])[:, :, 0], 0.0, hi_clip)
        d0, d = x0[:, 3], x[:, 3]
        for lvl, arr in ((0.9, t90), (0.5, t50), (0.1, t10)):
            hit = np.isnan(arr) & (d <= lvl * VDD) & (d0 > lvl * VDD)
            arr[hit] = (t - dt + dt * (d0 - lvl * VDD) / np.maximum(d0 - d, 1e-12))[hit]
        if np.all(np.isfinite(t10)):
            break
    if os.environ.get("TDEBUG"):
        print("TDEBUG end", x[:5], "t", t[:5])
    delay_vbl = np.where(np.isfinite(t50), t50, np.inf)
    return delay_vbl - t_cs, delay_vbl, np.where(np.isfinite(t10) & np.isfinite(t90), t10 - t90, np.inf), v_s


def refine(e, mask, iv, chunk=4000):
    """Run transient() on the designs in `mask` and write delay_dyn, delay_vbl,
    t_fall and the pedestal back into e."""
    idx = np.flatnonzero(mask & ~e["sim"])
    for c0 in range(0, idx.size, chunk):
        ii = idx[c0:c0 + chunk]
        dd, dv, fl, vs = transient(e, ii, iv)
        e["delay_dyn"][ii], e["delay_vbl"][ii], e["t_fall"][ii] = dd, dv, fl
        e["delay_c"][ii] = DELAY_CAL * dd                       # calibrated against ngspice
        e["fall_c"][ii] = fall_factor({"l_ld": e["l_ld"][ii]}) * fl
        e["pedestal_lsb"][ii] = e["ped_base"][ii] + np.abs(dv) / TCOUNT
        e["window_counts"][ii] = e["pedestal_lsb"][ii] + 3.0 * e["sigma_in_lsb"][ii]
        e["sim"][ii] = True
    return idx.size


def prefilter(e):
    """Designs worth a transient: every static constraint met and the closed-form
    delay within 4x the requirement (it read 2.4x slow against ngspice)."""
    c = constraints(e)
    return all_of(c, skip=("delay", "fall", "pedestal", "pedestal_window", "sigma_in")) & (e["delay_cf"] <= 3.0 * DELAY_MAX)


def constraints(e, delay_cal=1.0):
    return {
        "tables": e["ok_g"] & e["ok_trip"],
        "headroom": e["headroom"] >= e["vdsat_b"] + HEADROOM_MARGIN,
        "headroom_1p77x": e["headroom_1p77"] >= e["vdsat_b_1p77"] + HEADROOM_MARGIN,
        "headroom_1p77x_vddmin": e["headroom_1p77_vmin"] >= e["vdsat_b_1p77"] + HEADROOM_MARGIN,
        "gain": e["gain_ota"] * e["gain_st"] * e["gain_oi"] >= e["gain_min"],
        "noise": e["noise_v"] <= NOISE_MAX_V,
        "sigma_in": e["sigma_in_lsb"] <= SIGMA_GATE_LSB,
        "pedestal": e["pedestal_lsb"] <= PEDESTAL_BUDGET_LSB,
        "pedestal_window": e["window_counts"] <= OVERRUN_COUNTS - 1.0,
        "dead_zone": e["k_dead"] <= K_DEAD_BUDGET_LSB,
        "delay": DELAY_CAL * e["delay_dyn"] <= DELAY_MAX,
        "fall": fall_factor(e) * e["t_fall"] <= FALL_MAX,
        "fingers": (np.abs(e["nf_pb"] - np.round(e["nf_pb"])) < 1e-6) & (e["nf_pb"] >= 1)
                   & (e["nf_tail"] % np.ceil(e["nf_tail"] / 50.0) == 0) & (e["nf_st"] % np.ceil(e["nf_st"] / 50.0) == 0),
        "widths": (e["w_in"] <= W_BIN_MAX) & (e["w_ld"] <= W_BIN_MAX),
    }


def all_of(cons, skip=()):
    f = np.ones(next(iter(cons.values())).size, dtype=bool)
    for k, m in cons.items():
        if k not in skip:
            f &= m
    return f


def concat(a, b):
    return {k: np.concatenate([a[k], b[k]]) for k in a}


# ------------------------------------------------------------ netlist
def fmt_um(x):
    return ("%.3f" % (x * 1e6)).rstrip("0").rstrip(".")


def dev(name, d, g, s, b, kind, L, w_finger, nf):
    nf = int(round(nf))
    m = -(-nf // 50)
    nfi = nf // m
    line = f"{name} {d} {g} {s} {b} {kind} L={L:g}u W={fmt_um(nfi * w_finger)}u nf={nfi} m={m}"
    if os.environ.get("DUT_GEOM") == "1":
        # the drain/source geometry the PDK's xschem MOS symbols write (0.18 um
        # diffusion extension), which the controlled deck leaves to BSIM4's defaults
        w = nfi * w_finger
        nd, ns = (nfi + 1) // 2, (nfi + 2) // 2
        line += (f" ad={nd * w / nfi * 0.18e-6:.4g} pd={2 * nd * (w / nfi + 0.18e-6):.4g}"
                 f" as={ns * w / nfi * 0.18e-6:.4g} ps={2 * ns * (w / nfi + 0.18e-6):.4g}"
                 f" nrd={0.18e-6 / w:.4g} nrs={0.18e-6 / w:.4g}")
    return line


def nf_pb_of(s):
    return int(round(2.0 * s["w_fn"] * s["nf_ld"] / s["w_fp"]))


def subckt(s):
    p = s["w_fp"]
    return ".subckt cmp inp inn dout clk vdd vss nbias pbias\n" + "\n".join([
        dev("XINP", "left", "inp", "tail", "vdd", "pfet_03v3", s["l_in"], p, s["nf_in"]),
        dev("XINN", "outa", "inn", "tail", "vdd", "pfet_03v3", s["l_in"], p, s["nf_in"]),
        dev("XLOADD", "left", "left", "vss", "vss", "nfet_03v3", s["l_ld"], s["w_fn"], s["nf_ld"]),
        dev("XLOADM", "outa", "left", "vss", "vss", "nfet_03v3", s["l_ld"], s["w_fn"], s["nf_ld"]),
        dev("XTAIL", "tail", "pbias", "vdd", "vdd", "pfet_03v3", s["l_b"], p, s["nf_tail"]),
        dev("XBST", "bst", "pbias", "vdd", "vdd", "pfet_03v3", s["l_b"], p, s["nf_st"]),
        dev("XBUF1", "outb", "outa", "vss", "vss", "nfet_03v3", s["l_ld"], s["w_fn"], s["nf_ld"]),
        dev("XBUF2", "outb", "outa", "bst", "vdd", "pfet_03v3", s["l_ld"], p, nf_pb_of(s)),
        dev("XBUF3", "dout", "outb", "vss", "vss", "nfet_03v3", s["l_ld"], s["w_fn"], s["nf_ld"]),
        dev("XBUF4", "dout", "outb", "vdd", "vdd", "pfet_03v3", s["l_ld"], p, nf_pb_of(s)),
    ]) + "\n.ends cmp\n"


def ref_line(s, scale=1.0):
    """The bias reference of the benches: one tail finger, diode-connected (the
    bias generator replaces it later); IREF = scale x i_f."""
    return (dev("XREFP", "pbias", "pbias", "vddb", "vddb", "pfet_03v3", s["l_b"], s["w_fp"], NF_REF),
            "%.6g" % (s["i_f"] * NF_REF * scale))


# ------------------------------------------------------------ stage B (ngspice)
RESULT_KEYS = ("vtrip_v", "delay_vbl", "delay_dyn", "fall", "ped_counts", "armed", "p_avg")


def run_deck(d, deck, subs, timeout):
    with open(os.path.join(BLOCK, deck)) as h:
        text = h.read()
    for key, val in subs.items():
        text = text.replace(f"@{key}@", val)
    deck = os.path.basename(deck)
    with open(os.path.join(d, deck), "w") as h:
        h.write(text)
    out_name = deck.replace(".spice", ".out")
    with open(os.path.join(d, ".spiceinit"), "w") as h:     # one OpenMP thread (see ../comparator_bkp/comparator_updt_v2 recipe s.4)
        h.write("set num_threads=1\n")
    env = dict(os.environ, OMP_NUM_THREADS="1")
    try:
        subprocess.run(["ngspice", "-b", "-o", out_name, deck], cwd=d, env=env, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        with open(os.path.join(d, out_name), errors="replace") as h:
            out = h.read()
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return out.split("RESULT_BEGIN")[-1].split("RESULT_END")[0] if "RESULT_BEGIN" in out else ""


def grab(blk, key):
    m = re.search(r"^\s*%s\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)" % key, blk, re.M)
    return float(m.group(1)) if m else float("nan")


NOMINAL_CELL = ("typical", 27.0, VDD)


def cell_subs(cell=NOMINAL_CELL):
    """Corner, temperature and supply of a bench. The MIM model has typical, ff
    and ss sections only, so the sf/fs MOS corners keep the typical MIM."""
    corner, temp, vdd = cell
    vcm = vdd / 2.0
    return {"CORNER": corner, "MIMCORNER": corner if corner in ("ff", "ss") else "typical",
            "TEMP": "%g" % temp, "VDD": "%g" % vdd, "VCM": "%.6g" % vcm,
            "VLO50": "%.6g" % (vcm - 0.05), "VHI50": "%.6g" % (vcm + 0.05),
            "VLO70": "%.6g" % (vcm - 0.07), "VHI70": "%.6g" % (vcm + 0.07)}


def common_subs(s, d, scale=1.0, cell=NOMINAL_CELL):
    dut = os.path.join(d, "dut.spice")
    with open(dut, "w") as h:
        h.write(subckt(s))
    ref, iref = ref_line(s, scale)
    return dict(cell_subs(cell), DUT=dut, CLOAD="%.4g" % C_LOAD_DOUT, IREF=iref, REFP=ref)


def spice_level(job):
    tag, s, lt, k, scale = job[:5]
    cell = job[5] if len(job) > 5 else NOMINAL_CELL
    d = os.path.join(BLOCK, "work", job[6] if len(job) > 6 else "sel", f"{tag}_{lt}")
    os.makedirs(d, exist_ok=True)
    c = common_subs(s, d, scale, cell)
    res = {key: float("nan") for key in RESULT_KEYS}
    vtrip = grab(run_deck(d, "tb_sel_dc.spice", c, 120), "vtrip")
    res["vtrip_v"] = vtrip
    if not np.isfinite(vtrip):
        return tag, lt, res
    vin = VR_LO + k * LSB
    tstop = 400e-9 + k * TCOUNT + 400e-9
    blk = run_deck(d, "tb_sel.spice", dict(c, VIN="%.9g" % vin, TSTOP="%.6g" % tstop, VTRIP="%.6f" % vtrip), 600)
    for key in RESULT_KEYS[1:]:
        res[key] = grab(blk, key)
    return tag, lt, res


NZ_KEYS = ("ota_gain_vv", "ota_pole_hz", "nz_own_vin", "nz_lo_vin", "nz_ugb_vin", "op_i_vdd")


def spice_noise(job):
    tag, s = job[:2]
    cell = job[2] if len(job) > 2 else NOMINAL_CELL
    d = os.path.join(BLOCK, "work", job[3] if len(job) > 3 else "sel", f"{tag}_nz")
    os.makedirs(d, exist_ok=True)
    blk = run_deck(d, "tb_nz.spice", common_subs(s, d, 1.0, cell), 300)
    return tag, "nz", {k: grab(blk, k) for k in NZ_KEYS}


def spice_stage(cands, levels=LEVELS, noise=True):
    jobs = [(tag, s, lt, k, sc) for tag, s in cands for lt, k, sc in levels]
    out = {}
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        futs = [ex.submit(spice_level, j) for j in jobs]
        if noise:
            futs += [ex.submit(spice_noise, (tag, s)) for tag, s in cands]
        for f in futs:
            tag, lt, res = f.result()
            out.setdefault(tag, {})[lt] = res
    return out


def spice_verdict(r):
    rs = [r.get(lt, {}) for lt, _, _ in LEVELS]
    if not all(np.isfinite(x.get(k, np.nan)) for x in rs for k in RESULT_KEYS):
        return False, "no result"
    if min(x["armed"] for x in rs) < 0.9 * VDD:
        return False, "not armed"
    if max(x["delay_dyn"] for x in rs) > DELAY_MAX:
        return False, "delay"
    if abs(r["c4"]["delay_dyn"] - r["plat"]["delay_dyn"]) > LOWEND_SPREAD_MAX:
        return False, "low-end spread"
    if max(x["fall"] for x in rs) > FALL_MAX:
        return False, "fall"
    nzv = r.get("nz", {}).get("nz_own_vin", np.nan)
    if not np.isfinite(nzv) or nzv > NOISE_MAX_V:
        return False, "noise"
    return True, "pass"


# ------------------------------------------------------------ main
def design(e, i):
    return {k: (float(e[k][i]) if k in ("l_in", "l_ld", "l_b", "w_fp", "w_fn", "i_f") else int(round(e[k][i])))
            for k in VARS}


def stage_a(rng, ev, points, local_points, rounds, delay_cal):
    e = ev(sample_uniform(rng, points, ev.tabs))
    cons = constraints(e, delay_cal)
    feas = all_of(cons)
    for name, m in sorted(cons.items()):
        print(f"pass_{name} = {int(m.sum())}")
        print(f"relaxing_{name} = {int(all_of(cons, skip=(name,)).sum())}")
    print(f"feasible_stage_a_uniform = {int(feas.sum())}")
    if feas.sum() < 3:
        return e, feas
    for rnd in range(rounds):
        # local rounds around the current power x area front and a random feasible subset
        idx = np.flatnonzero(feas)
        front = idx[pareto_mask(np.column_stack([e["power"][idx], e["area"][idx]]))]
        pick = np.concatenate([front, rng.choice(idx, min(idx.size, 400), replace=False)])
        e = concat(e, ev(sample_local(rng, {k: e[k][pick] for k in VARS}, local_points)))
        feas = all_of(constraints(e, delay_cal))
        print(f"feasible_stage_a_round{rnd + 1} = {int(feas.sum())}")
    return e, feas


def unique_idx(e, feas):
    key = np.stack([np.round(e[k].astype(float), 12 if k == "i_f" else 6) for k in VARS], axis=1)
    idx_f = np.flatnonzero(feas)
    _, first = np.unique(key[idx_f], axis=0, return_index=True)
    return idx_f[np.sort(first)]


def knee(p, a):
    """The front point nearest the utopia point in log-normalised (power, area)."""
    lp, la = np.log(p), np.log(a)
    d = ((lp - lp.min()) / max(np.ptp(lp), 1e-12)) ** 2 + ((la - la.min()) / max(np.ptp(la), 1e-12)) ** 2
    return int(np.argmin(d))


DUMP_COLS = list(VARS) + ["power", "area", "gate_area", "delay_dyn", "delay_vbl", "delay_cf", "fall_cf", "delay_c", "fall_c", "noise_v", "noise_th_v",
                          "noise_fl_v", "noise_adc_lsb", "sigma_in_lsb", "alpha", "gain_ota", "gain_st", "tau",
                          "f_p", "k_dead", "dv_trip", "id_branch", "i_st", "i_tail", "gmid_in", "gmid_ld", "gmid_b",
                          "j_b", "vsg_b", "mirror_err", "c_outa", "c_outb", "t_fall", "pedestal_lsb",
                          "window_counts", "headroom", "nf_pb"]


def dump(path, e, idx, extra=None):
    with open(path, "w") as h:
        cols = DUMP_COLS + (list(extra[0].keys()) if extra else [])
        h.write(",".join(cols) + "\n")
        for n, i in enumerate(idx):
            row = ["%.6g" % float(e[c][i]) for c in DUMP_COLS]
            if extra:
                row += [str(x) if isinstance(x, str) else "%.6g" % x for x in extra[n].values()]
            h.write(",".join(row) + "\n")


def main():
    if os.environ.get("PHASE", "A") == "SELECT":
        return select_from_records(os.environ.get("SELECT_SIGMA", "2"))
    if os.environ.get("PHASE", "A") == "CALFIT":
        return fit_calibration()
    seed = int(os.environ.get("PARETO_SEED", 20261006))
    points = int(os.environ.get("PARETO_POINTS", 200000))
    local_points = int(os.environ.get("LOCAL_POINTS", 40000))
    rounds = int(os.environ.get("ROUNDS", 4))
    delay_cal = DELAY_CAL
    n_front_b = int(os.environ.get("N_FRONT_B", 24))
    rng = np.random.default_rng(seed)
    pfet = lk(f"{LUT_DIR}/pfet_03v3.pkl")
    nfet = lk(f"{LUT_DIR}/nfet_03v3.pkl")
    perl = PerL(nfet, pfet)
    nz = Noise(os.path.join(BLOCK, "data", "device_noise.csv"))

    iv = IV(LUT_DIR)

    def ev(v):
        e = evaluate(v, pfet, nfet, perl, nz)
        print(f"transient_runs = {refine(e, prefilter(e), iv)}")
        return e
    ev.tabs = (pfet, nfet)
    print("INFO: --- comparator: short-L (<= 0.36 um) gm/Id search, ideal pbias, 10 fF dout ---")
    for k, x in (("lsb_v", LSB), ("slope_v_per_s", SLOPE), ("delay_max_s", DELAY_MAX), ("c_load_dout_f", C_LOAD_DOUT),
                 ("noise_max_v", NOISE_MAX_V), ("f_noise_lo_hz", F_NOISE_LO), ("delay_cal", DELAY_CAL), ("fall_cal", FALL_CAL)):
        print(f"{k} = {x:.6g}")

    e, feas = stage_a(rng, ev, points, local_points, rounds, delay_cal)
    if feas.sum() < 3:
        print("FAIL: fewer than 3 stage-A designs meet every constraint")
        return 1
    os.makedirs(os.path.join(BLOCK, "data"), exist_ok=True)
    idx_u = unique_idx(e, feas)
    print(f"stage_a_unique_designs = {idx_u.size}")
    front = idx_u[pareto_mask(np.column_stack([e["power"][idx_u], e["area"][idx_u]]))]
    front = front[np.argsort(e["power"][front])]
    print(f"stage_a_front_points = {front.size}")
    k = knee(e["power"][front], e["area"][front])
    print(f"stage_a_knee_power_w = {e['power'][front[k]]:.6g}")
    print(f"stage_a_knee_area_um2 = {e['area'][front[k]]:.6g}")
    # cloud for the plots: every feasible design (subsampled) and, for the
    # trade-off views, designs failing ONLY delay or ONLY noise/sigma
    cons = constraints(e, delay_cal)
    relax = {}
    for name in ("delay", "noise", "sigma_in"):
        m = all_of(cons, skip=(name,)) & ~cons[name]
        relax[name] = np.flatnonzero(m)
    tag = os.environ.get("TAG", "")
    sub = rng.choice(idx_u, min(idx_u.size, 6000), replace=False)
    dump(os.path.join(BLOCK, "data", f"stage_a_feasible{tag}.csv"), e, sub)
    dump(os.path.join(BLOCK, "data", f"stage_a_front{tag}.csv"), e, front)
    for name, m in relax.items():
        dump(os.path.join(BLOCK, "data", f"stage_a_fails_only_{name}{tag}.csv"), e,
             rng.choice(m, min(m.size, 3000), replace=False) if m.size else m)
    if os.environ.get("PHASE", "A") == "CAL":
        return calibrate(e, rng)
    if os.environ.get("PHASE", "A") != "B":
        print("PASS: stage A done (tables only)")
        return 0

    # ---------------- stage B: time the front at each sigma(Vos) cap in ngspice
    # sigma(Vos) <= 4/3 LSB is a contract value marked "assumed" (../comparator_bkp/comparator_updt/SPEC.md
    # item 7); with L <= 0.36 um it costs power and area, so the front is shown and timed
    # at several caps and the choice is made on the table of results.
    caps = [float(x) for x in os.environ.get("SIGMA_CAPS", "1.3333,1.6,2.0,2.5,99").split(",")]
    fronts, order = {}, []
    for cap in caps:
        m = idx_u[e["sigma_in_lsb"][idx_u] <= cap]
        print(f"stage_a_feasible_sigma_le_{cap:g} = {m.size}")
        if m.size == 0:
            continue
        fr = m[pareto_mask(np.column_stack([e["power"][m], e["area"][m]]))]
        fr = fr[np.argsort(e["power"][fr])]
        fronts[cap] = fr
        dump(os.path.join(BLOCK, "data", f"stage_a_front_s{cap:g}{tag}.csv"), e, fr)
        kk_ = knee(e["power"][fr], e["area"][fr])
        print(f"REPORT: tables, sigma <= {cap:g} LSB: {fr.size} front points, knee {e['power'][fr[kk_]]*1e6:.1f} uW "
              f"{e['area'][fr[kk_]]:.1f} um2 (sigma {e['sigma_in_lsb'][fr[kk_]]:.2f} LSB)")
        p = np.unique(np.round(np.linspace(0, fr.size - 1, min(n_front_b, fr.size))).astype(int))
        order += [int(fr[j]) for j in sorted(set(p.tolist()) | {kk_})]
    order = list(dict.fromkeys(order))
    tags = {f"f{n:03d}": i for n, i in enumerate(order)}
    res = spice_stage([(t, design(e, i)) for t, i in tags.items()])
    rows = []
    for t, i in tags.items():
        ok, why = spice_verdict(res[t])
        rows.append((t, i, ok, why))
        r = res[t]
        print(f"REPORT: {t} P {e['power'][i]*1e6:.1f} uW A {e['area'][i]:.1f} um2 sigma {e['sigma_in_lsb'][i]:.2f} LSB: "
              f"delay model {e['delay_c'][i]*1e9:.2f} ngspice c4/plat {r['c4']['delay_dyn']*1e9:.2f}/"
              f"{r['plat']['delay_dyn']*1e9:.2f} ns; fall model {e['fall_c'][i]*1e9:.2f} ngspice {r['plat']['fall']*1e9:.2f} ns; "
              f"noise model {e['noise_v'][i]*1e3:.3f} ngspice {r['nz']['nz_own_vin']*1e3:.3f} mV -> {why}")
    extra = [dict(tag=t, spice_pass=int(ok), why=why,
                  **{f"{lt}_{kk}": res[t][lt][kk] for lt, _, _ in LEVELS for kk in RESULT_KEYS},
                  **{f"nz_{kk}": res[t]["nz"][kk] for kk in NZ_KEYS}) for t, i, ok, why in rows]
    dump(os.path.join(BLOCK, "data", f"stage_b{tag}.csv"), e, [r[1] for r in rows], extra)
    good = [r for r in rows if r[2]]
    print(f"stage_b_timed = {len(rows)}")
    print(f"stage_b_pass = {len(good)}")
    for why in ("no result", "not armed", "delay", "low-end spread", "fall", "noise"):
        print(f"stage_b_fail_{why.replace(' ', '_').replace('-', '_')} = {sum(1 for r in rows if r[3] == why)}")
    per_cap = {}
    for cap in caps:
        gi = np.array([r[1] for r in good if e["sigma_in_lsb"][r[1]] <= cap])
        if gi.size == 0:
            print(f"REPORT: ngspice, sigma <= {cap:g} LSB: no passing design")
            continue
        fm = pareto_mask(np.column_stack([e["power"][gi], e["area"][gi]]))
        gf = gi[fm][np.argsort(e["power"][gi[fm]])]
        b = int(gf[knee(e["power"][gf], e["area"][gf])])
        bt = [r[0] for r in good if r[1] == b][0]
        per_cap[f"{cap:g}"] = dict(tag=bt, power=float(e["power"][b]), area=float(e["area"][b]),
                                   sigma_in_lsb=float(e["sigma_in_lsb"][b]), delay=res[bt]["plat"]["delay_dyn"],
                                   fall=res[bt]["plat"]["fall"], noise=res[bt]["nz"]["nz_own_vin"],
                                   front=[r[0] for r in good if r[1] in set(gf.tolist())])
        print(f"REPORT: ngspice, sigma <= {cap:g} LSB: knee {bt} {e['power'][b]*1e6:.1f} uW {e['area'][b]:.1f} um2 "
              f"sigma {e['sigma_in_lsb'][b]:.2f} LSB, delay {res[bt]['plat']['delay_dyn']*1e9:.2f} ns, fall "
              f"{res[bt]['plat']['fall']*1e9:.2f} ns, noise {res[bt]['nz']['nz_own_vin']*1e3:.3f} mV")
    with open(os.path.join(BLOCK, "data", f"stage_b_caps{tag}.json"), "w") as h:
        json.dump(per_cap, h, indent=2)
    sel_cap = os.environ.get("SELECT_SIGMA", "2")
    if sel_cap not in per_cap:
        print(f"FAIL: no ngspice-passing design at the selection cap SELECT_SIGMA={sel_cap!r} (have {list(per_cap)})")
        return 1
    best = [r[1] for r in good if r[0] == per_cap[sel_cap]["tag"]][0]
    btag = [r[0] for r in good if r[1] == best][0]
    sel = {kk: float(e[kk][best]) for kk in DUMP_COLS}
    sel.update(design(e, best))
    sel["nf_pb"] = nf_pb_of(sel)
    sel["tag"] = btag
    for lt, _, _ in LEVELS:
        for kk in RESULT_KEYS:
            sel[f"spice_{lt}_{kk}"] = res[btag][lt][kk]
    for kk in NZ_KEYS:
        sel[f"spice_{kk}"] = res[btag]["nz"][kk]
    sel.update(seed=seed, points=points, local_points=local_points, rounds=rounds, delay_cal=delay_cal,
               c_load_dout=C_LOAD_DOUT, iref=sel["i_f"] * NF_REF, nf_ref=NF_REF)
    for kk in sorted(sel):
        if isinstance(sel[kk], (int, float)):
            print(f"sel_{kk} = {sel[kk]:.6g}")
    with open(os.path.join(BLOCK, "data", f"sizing{tag}.json"), "w") as h:
        json.dump(sel, h, indent=2, sort_keys=True)
    netlist = emit_netlist(sel)
    os.makedirs(os.path.join(BLOCK, "work"), exist_ok=True)
    with open(os.path.join(BLOCK, "work", "comparator.spice"), "w") as h:
        h.write(netlist)
    if os.environ.get("SIZING_EMIT") == "1":
        with open(os.path.join(BLOCK, "comparator.spice"), "w") as h:
            h.write(netlist)
        print("INFO: emitted comparator.spice")
    print(f"REPORT: selected {btag}: {sel['power']*1e6:.1f} uW, {sel['area']:.1f} um2 footprint")
    print("PASS: short-L front timed in ngspice, power x area knee selected")
    return 0


def select_from_records(cap):
    """Selection from the recorded stage B (data/stage_b.csv, data/stage_b_caps.json):
    the ngspice power x area knee at sigma(Vos) <= cap. Writes data/sizing.json and
    work/comparator.spice (comparator.spice too with SIZING_EMIT=1)."""
    caps = json.load(open(os.path.join(BLOCK, "data", "stage_b_caps.json")))
    if cap not in caps:
        print(f"FAIL: no ngspice-passing design recorded at sigma <= {cap} LSB (have {list(caps)})")
        return 1
    tag = caps[cap]["tag"]
    row = [r for r in csv.DictReader(open(os.path.join(BLOCK, "data", "stage_b.csv"))) if r["tag"] == tag][0]
    num = lambda v: float(v) if v not in ("", "nan") else float("nan")
    sel = {k: num(v) for k, v in row.items() if k not in ("tag", "why")}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st", "nf_pb"):
        sel[k] = int(round(sel[k]))
    for lt, _, _ in LEVELS:
        for kk in RESULT_KEYS:
            sel[f"spice_{lt}_{kk}"] = sel.pop(f"{lt}_{kk}")
    for kk in NZ_KEYS:
        sel[f"spice_{kk}"] = sel.pop(f"nz_{kk}")
    sel.update(tag=tag, sigma_cap_lsb=float(cap), seed=int(os.environ.get("PARETO_SEED", 20261006)),
               c_load_dout=C_LOAD_DOUT, iref=sel["i_f"] * NF_REF, nf_ref=NF_REF, delay_cal=DELAY_CAL,
               fall_cal_a=_CAL.get("fall_cal_a"), fall_cal_b=_CAL.get("fall_cal_b"))
    with open(os.path.join(BLOCK, "data", "sizing.json"), "w") as h:
        json.dump(sel, h, indent=2, sort_keys=True)
    netlist = emit_netlist(sel)
    os.makedirs(os.path.join(BLOCK, "work"), exist_ok=True)
    with open(os.path.join(BLOCK, "work", "comparator.spice"), "w") as h:
        h.write(netlist)
    if os.environ.get("SIZING_EMIT") == "1":
        with open(os.path.join(BLOCK, "comparator.spice"), "w") as h:
            h.write(netlist)
        print("INFO: emitted comparator.spice")
    for kk in sorted(sel):
        if isinstance(sel[kk], (int, float)):
            print(f"sel_{kk} = {sel[kk]:.6g}")
    print(f"REPORT: selected {tag} (sigma cap {cap} LSB): {sel['power']*1e6:.1f} uW, {sel['area']:.1f} um2 footprint")
    print("PASS: selection written")
    return 0


def calibrate(e, rng, n_cal=None):
    """Time a stratified set of transient-simulated designs in ngspice (plateau
    level, typical bias, and the noise bench) and write the medians of
    ngspice / model to data/calibration.json. The designs meet every static
    constraint; their modelled delay and fall span 0.3-3x the gates, and they
    are spread over log power."""
    n_cal = n_cal or int(os.environ.get("N_CAL", 40))
    c = constraints(e)
    m = (e["sim"] & all_of(c, skip=("delay", "fall", "pedestal", "pedestal_window", "sigma_in"))
         & (e["delay_dyn"] < 3 * DELAY_MAX) & (e["delay_dyn"] > 0.3 * DELAY_MAX)
         & (e["t_fall"] < 3 * FALL_MAX) & (e["t_fall"] > 0.3 * FALL_MAX))
    idx = unique_idx(e, m)
    lp = np.log(e["power"][idx])
    edges = np.linspace(lp.min(), lp.max() + 1e-9, n_cal + 1)
    pick = []
    for a, b in zip(edges[:-1], edges[1:]):
        inb = idx[(lp >= a) & (lp < b)]
        if inb.size:
            pick.append(int(rng.choice(inb)))
    print(f"calibration_designs = {len(pick)}")
    cands = [(f"c{j:03d}", design(e, i)) for j, i in enumerate(pick)]
    res = spice_stage(cands, levels=(("plat", 40.5, 1.0),), noise=True)
    rd, rf, rn, rv = [], [], [], []
    extra = []
    for (t, s), i in zip(cands, pick):
        r = res[t]["plat"]
        q = res[t]["nz"]
        rd.append(r["delay_dyn"] / e["delay_dyn"][i])
        rf.append(r["fall"] / e["t_fall"][i])
        rn.append(q["nz_own_vin"] / e["noise_v"][i])
        rv.append(r["delay_vbl"] - e["delay_vbl"][i])
        extra.append(dict(tag=t, **{f"plat_{k}": r[k] for k in RESULT_KEYS}, **{f"nz_{k}": q[k] for k in NZ_KEYS}))
    dump(os.path.join(BLOCK, "data", "calibration.csv"), e, pick, extra)
    return fit_calibration()


def fit_calibration():
    """Calibration from data/calibration.csv (written by calibrate()): medians of
    ngspice / model for delay and noise; for the dout fall, log(ratio) linear in
    the buffer L (the ratio rises from ~1.0 at 0.28 um to ~1.7 at 0.36 um)."""
    rs = list(csv.DictReader(open(os.path.join(BLOCK, "data", "calibration.csv"))))
    f = lambda k: np.array([float(r[k]) for r in rs])
    rd = f("plat_delay_dyn") / f("delay_dyn")
    rf = f("plat_fall") / f("t_fall")
    rn = f("nz_nz_own_vin") / f("noise_v")
    lld = f("l_ld")
    ok = np.isfinite(rd) & np.isfinite(rf) & np.isfinite(rn) & (rd > 0) & (rf > 0)
    b, a = np.polyfit(lld[ok] - 0.32, np.log(rf[ok]), 1)
    resid = np.log(rf[ok]) - (a + b * (lld[ok] - 0.32))
    out = dict(n=int(ok.sum()), delay_cal=float(np.median(rd[ok])), fall_cal=float(np.median(rf[ok])),
               fall_cal_a=float(a), fall_cal_b=float(b), fall_fit_resid_sigma=float(np.std(resid)),
               noise_cal=float(np.median(rn[ok])),
               delay_ratio_p10=float(np.percentile(rd[ok], 10)), delay_ratio_p90=float(np.percentile(rd[ok], 90)),
               fall_ratio_p10=float(np.percentile(rf[ok], 10)), fall_ratio_p90=float(np.percentile(rf[ok], 90)),
               noise_ratio_p10=float(np.percentile(rn[ok], 10)), noise_ratio_p90=float(np.percentile(rn[ok], 90)),
               vbl_diff_median_s=float(np.median((f("plat_delay_vbl") - f("delay_vbl"))[ok])))
    for k, v in out.items():
        print(f"cal_{k} = {v:.6g}")
    with open(_CAL_PATH, "w") as h:
        json.dump(out, h, indent=2, sort_keys=True)
    print("PASS: calibration written to data/calibration.json")
    return 0


def fall_factor(e):
    """ngspice / model for the dout fall, per design (fit_calibration)."""
    if "fall_cal_a" in _CAL and "FALL_CAL" not in os.environ:
        return np.exp(_CAL["fall_cal_a"] + _CAL["fall_cal_b"] * (e["l_ld"].astype(float) - 0.32))
    return FALL_CAL




def emit_netlist(s):
    ref, iref = ref_line(s)
    return f"""* comparator -- continuous comparator for the TRUE BOTTOM-PLATE 8-bit cell:
* PMOS 5T OTA -> starved inverter -> output inverter (10 devices), the topology
* of ../comparator_bkp/comparator_updt_v2 re-sized on 2026-10-06 with every L <= 0.36 um for:
* delay from the static trip <= 1/4 count (12.5 ns), dout into 10 fF, noise
* at the pins (thermal + 1/f from 1 kHz, own band) < 1.2 mV. inp = VBL,
* inn = the MIM top plate; dout FALLS when inn rises through inp.
* clk and nbias are NO-CONNECTS (the cell's port list).
*
* GENERATED by size_v3.py (seed {s['seed']}). Do not hand-edit. Recipe: DESIGN_RECIPE.md.
* Bias: pbias from an ideal {float(iref)*1e6:.4g} uA into one tail finger, diode-connected
* (in the benches: {ref}).
* Labels: [P] PDK tables (stage A), [M] ngspice (stage B, {s['tag']}).
*   pair    {s['nf_in']} x {s['w_fp']*1e6:g} um, L {s['l_in']:g} um: gm/Id {s['gmid_in']:.1f} S/A [P]
*   load    {s['nf_ld']} x {s['w_fn']*1e6:g} um, L {s['l_ld']:g} um: gm/Id {s['gmid_ld']:.1f} S/A [P]
*   tail    {s['nf_tail']} x {s['w_fp']*1e6:g} um, L {s['l_b']:g} um: {s['i_tail']*1e6:.3f} uA; J_D {s['j_b']:.3g} A/m, gm/Id {s['gmid_b']:.1f} [P]
*   starve  {s['nf_st']} x {s['w_fp']*1e6:g} um, L {s['l_b']:g} um: {s['i_st']*1e6:.3f} uA [P]
*   buffers N = XLOADM, P {s['nf_pb']} x {s['w_fp']*1e6:g} um, L {s['l_ld']:g} um
*   alpha {s['alpha']:.3f}; sigma(Vos) at the ADC input {s['sigma_in_lsb']:.2f} LSB [P]
*   delay from the static trip: c4 {s['spice_c4_delay_dyn']*1e9:.2f} ns, plateau {s['spice_plat_delay_dyn']*1e9:.2f} ns [M]
*   noise at the pins {s['spice_nz_own_vin']*1e3:.3f} mV rms [M]; power {s['power']*1e6:.1f} uW worst state [P]
* The simulators are the authority, not these lines.
""" + subckt(s)


if __name__ == "__main__":
    sys.exit(main())
