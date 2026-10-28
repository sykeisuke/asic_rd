"""vr.py -- what size_vrlo.py and verify_vrlo.py share: the requirements (with
their source), the PVT grid, the netlist writer, the template filler and the
ngspice runner. Nothing here runs a simulation by itself.

Requirement numbers (README.md s.1 holds the derivation):
  D  derived from the macro timeline / ramp / cell records
  A  assumed (an allocation chosen here, labelled so)
"""
import os
import re
import subprocess
import threading

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
DATA = os.path.join(BLOCK, "data")
JOBS = int(os.environ.get("JOBS", "12"))

VDD = 3.3
RATIO = 5.0 / 33.0                 # D: 0.5 V at AVDD 3.3 V, 5 of 33 unit resistors
LSB = 1.5 / 256                    # D: 8-bit over 0.5-2.0 V (ADR 0011)
EPS = 0.05 * LSB                   # D: 0.293 mV, ramp_gen/COMPARISON.md s.4.3: the reference's
                                   #    allocation at TR. At the macro's 90 ns from the last S1
                                   #    to TR ramp_simple's reset switch alone leaves 0.048 LSB
                                   #    (ss/85/3.0); with TGAP = 300 ns (user decision
                                   #    2026-10-10, tb_tran.spice) it leaves ~0 and the total
                                   #    residual is gated
T0 = 3.0e-6                        # D: Analog_top tb_params.inc, settled-by time
TREC = 1.0e-6                      # A: end-of-ramp reset to the next record's first S1
VTOP = 2.1618                      # D: vramp at TE+TOVR, runs/analog-top/20261009T020546Z
IRAMP_DIODE = 3.2512e-6            # D: bias_gen's typical ramp output (iramp_ts0_ua)
IRS_SPAN = (0.74, 1.62)            # D: ramp current over PVT, untrimmed (ADR 0017)
IBS_SPAN = (0.69, 1.77)            # A: the bias span midref_v2 used for its ideal bias
C_EQ = 40e-15                      # A: bottom-plate charge per cell seen from vramp,
                                   #    C_S(1-alpha_min) 33 fF + bottom parasitics, rounded up.
                                   #    Checked end to end by macro/macro.py: the block kick
                                   #    must not be smaller than the real cells' in analog_top
VERR_MAX = 2.0 * LSB               # A: |vrlo - 5/33 AVDD| systematic, every PVT cell: half
                                   #    the ~4 overrun counts left after the in-cell offset
                                   #    mean + 3 sigma (15 of 19, comparator record).
                                   #    First set at 1 LSB; the 85 C mirror imbalance (1-4 mV)
                                   #    failed most designs there (README.md s.1, s.3)
SIGMA_MAX_LSB = 1.0                # A: MC sigma(vrlo) <= 1 LSB (vs ~4 LSB in-cell comparator offset)
NOISE_MAX_LSB = 0.04               # A: vrlo noise sampled at TR, 1 Hz-1 GHz (ramp share 0.07,
                                   #    ramp own 0.043 measured: rss 0.059)
PM_MIN = 45.0                      # A: loop phase margin, both reset states

CORNERS = ("typical", "ff", "ss", "fs", "sf")
TEMPS = (0, 27, 85)
VDD_SET = (3.0, 3.3, 3.6)
WN, WP = 1.0, 2.0                  # one finger width per flavour (um)


def mimc(c):
    return c if c in ("ff", "ss") else "typical"


def resc(c):
    return {"ff": "res_ff", "ss": "res_ss"}.get(c, "res_typical")


def netlist(s, name="vrlo_ref", header=""):
    """Numeric subcircuit `name vrlo ib avdd avss` from a sizing dict s."""
    L = []
    L.append(f".subckt {name} vrlo ib avdd avss")
    # divider: 28 + 5 identical ppolyf_u_3k units, tap after unit 28
    nodes = ["avdd"] + [f"r{k}" for k in range(1, 28)] + ["tap"] + [f"r{k}" for k in range(29, 33)] + ["avss"]
    for k in range(33):
        L.append(f"XR{k + 1} {nodes[k]} {nodes[k + 1]} avss ppolyf_u_3k r_width=1u r_length={s['LRU']:g}u")
    L.append(f"XCT tap avss cap_mim_2f0_m4m5_noshield c_width={s['CTW']:g}u c_length={s['CTW']:g}u")

    def mos(n, d, g, src, b, typ, l, nf):
        w = (WN if typ == "nfet_03v3" else WP) * nf
        L.append(f"{n} {d} {g} {src} {b} {typ} L={l:g}u W={w:g}u nf={nf:d} m=1")
    LB = s["LB"]
    mos("XMBN", "ib", "ib", "avss", "avss", "nfet_03v3", LB, 1)
    mos("XMBN2", "pb", "ib", "avss", "avss", "nfet_03v3", LB, 1)
    mos("XMBP", "pb", "pb", "avdd", "avdd", "pfet_03v3", LB, 1)
    mos("XMT", "ts", "pb", "avdd", "avdd", "pfet_03v3", LB, s["NT"])
    mos("XMK", "vrlo", "pb", "avdd", "avdd", "pfet_03v3", LB, s["NK"])
    mos("XM1", "d1", "vrlo", "ts", "avdd", "pfet_03v3", s["LI"], s["NI"])
    mos("XM2", "g", "tap", "ts", "avdd", "pfet_03v3", s["LI"], s["NI"])
    mos("XM3", "d1", "d1", "avss", "avss", "nfet_03v3", s["LL"], s["N3"])
    mos("XM4", "g", "d1", "avss", "avss", "nfet_03v3", s["LL"], s["N3"] - s["N5"])
    mos("XM5", "g", "g", "avss", "avss", "nfet_03v3", s["LL"], s["N5"])
    mos("XMS", "vrlo", "g", "avss", "avss", "nfet_03v3", s["LL"], s["NS"])
    L.append(f"XCD vrlo avss cap_mim_2f0_m4m5_noshield c_width={s['CDW']:g}u c_length={s['CDW']:g}u")
    L.append(f".ends {name}")
    return header + "\n".join(L) + "\n"


def loop_variant(txt):
    """The same netlist with the OTA's sense input on its own port fb (XM1's
    gate), for the Middlebrook voltage injection in tb_loop.spice: vrlo is a
    decap node (low Z), XM1's gate a few fF (high Z)."""
    txt = txt.replace(".subckt vrlo_ref vrlo ib avdd avss", ".subckt vrlo_ref_lb vrlo fb ib avdd avss")
    txt = txt.replace(".ends vrlo_ref", ".ends vrlo_ref_lb")
    return re.sub(r"^XM1 d1 vrlo ts", "XM1 d1 fb ts", txt, flags=re.M)


def area_um2(s):
    """Drawn-device area [P]: MOS W x L, poly W x L, MIM side^2 (no spacing)."""
    mos = (s["LB"] * (2 * WN + WP * (1 + s["NT"] + s["NK"]))
           + 2 * s["LI"] * WP * s["NI"] + s["LL"] * WN * (2 * s["N3"] + s["NS"]))
    poly = 33 * 1.0 * s["LRU"]
    mim = s["CDW"] ** 2 + s["CTW"] ** 2
    return mos + poly + mim, mos, poly, mim


def fill(tpl, subs):
    t = open(os.path.join(BLOCK, tpl)).read()
    for k, v in subs.items():
        t = t.replace("@" + k + "@", str(v))
    left = re.findall(r"@[A-Z_0-9]+@", t)
    assert not left, (tpl, left)
    return t


def ngspice(d, deck, timeout=900):
    log = os.path.join(d, deck.replace(".spice", ".log"))
    try:
        subprocess.run(["ngspice", "-b", deck], cwd=d, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                       timeout=timeout)
    except subprocess.TimeoutExpired:
        return ""
    return open(log, errors="replace").read()


NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def grab(txt):
    """ngspice .measure echoes `name = value [at=..]` and echo lines `name = value`."""
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r"^([a-z][a-z_0-9]*)\s+=\s+(" + NUM + r")", txt, re.M)}


def rundir(*parts, dut=None):
    d = os.path.join(WORK, *parts)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    if dut is not None:
        open(os.path.join(d, "dut.spice"), "w").write(dut)
    return d


def tran_subs(cell=("typical", 27, VDD), ibs=1.0, irs=1.0, ib=1e-6, ks=1, real_ramp=False):
    c, t, v = cell
    return dict(CORNER=c, MIMCORNER=mimc(c), RESCORNER=resc(c), TEMP=t, VDD="%g" % v,
                IB="%.6g" % (ib * ibs), IRD="%.6g" % (IRAMP_DIODE * irs), KS=ks, CEQ="%.4g" % C_EQ,
                VTOP="%.4f" % VTOP, TREC="%.4g" % TREC, RATIO="%.10f" % RATIO,
                TRUN="13.8u" if real_ramp else "1.5u", FRCV=0 if real_ramp else 3.3)


def tran_pair(d0, s_txt, cell, ibs=1.0, irs=1.0, ib=1e-6, tag="t", real_ramp=False):
    """tb_tran at KS=1 (full-scale cells) and KS=0 (all at VR_LO): returns the
    KS=1 measures plus kick = vp_tr(KS=1) - vp_tr(KS=0). real_ramp: the
    13.8 us ramp instead of the forced end of ramp."""
    out = {}
    for ks in (1, 0):
        d = rundir(d0, f"{tag}_ks{ks}", dut=s_txt)
        open(os.path.join(d, "tran.spice"), "w").write(
            fill("tb_tran.spice", tran_subs(cell, ibs, irs, ib, ks, real_ramp)))
        r = grab(ngspice(d, "tran.spice"))
        if ks == 1:
            out = r
        else:
            out["vp_tr_ks0"] = r.get("vp_tr", np.nan)
    out["kick"] = out.get("vp_tr", np.nan) - out.get("vp_tr_ks0", np.nan)
    if s_txt is not IDEAL_DUT:
        out["kick_ideal"] = ideal_kick(tuple(cell), irs, real_ramp)
    return out


# The same benches with an IDEAL vrlo (a 5/33 AVDD source): what ramp_simple's own
# reset switch leaves at TR (XRST Ron x 4 pF), which no regulator can remove. The
# regulator's kick gate is its increment over this (README.md s.1).
IDEAL_DUT = ".subckt vrlo_ref vrlo ib avdd avss\nRB ib avss 1meg\nEV vrlo avss avdd avss %.10f\n.ends vrlo_ref\n" % RATIO
_ideal_cache = {}
_ideal_lock = threading.Lock()


def ideal_kick(cell, irs=1.0, real_ramp=False):
    key = (cell, irs, real_ramp)
    with _ideal_lock:
        if key in _ideal_cache:
            return _ideal_cache[key]
    r = tran_pair(os.path.join("ideal", "%s_%g_%g_%g_%d" % (cell + (irs, real_ramp))), IDEAL_DUT, cell, 1.0, irs,
                  1e-6, real_ramp=real_ramp)
    with _ideal_lock:
        _ideal_cache[key] = r["kick"]
    return r["kick"]


def tran_gates(r, vdd=VDD):
    """Block gates on one tb_tran pair. Returns {name: (ok, value)}."""
    g = {}
    nan = np.nan
    g["start"] = abs(r.get("vp_t0", nan) - r.get("vp_q", nan))
    g["kick"] = abs(r.get("kick", nan))
    g["rec"] = abs(r.get("vp_q2", nan) - r.get("vp_q", nan))
    g["rep"] = abs(r.get("vp_tr2", nan) - r.get("vp_tr", nan))
    g["err"] = abs(r.get("vr_q", nan) - RATIO * vdd)
    lim = dict(start=EPS, kick=EPS, rec=EPS, rep=EPS, err=VERR_MAX)
    return {k: (bool(np.isfinite(v) and v <= lim[k]), v) for k, v in g.items()}


def loop(d0, s_txt, cell=("typical", 27, VDD), ibs=1.0, irs=1.0, ib=1e-6, rst=1, tag="l"):
    """tb_loop at one cell and reset state: {ugb_hz, pm_deg, t0_db}."""
    c, t, v = cell
    d = rundir(d0, f"{tag}_rst{rst}")
    open(os.path.join(d, "dut_lb.spice"), "w").write(loop_variant(s_txt))
    open(os.path.join(d, "loop.spice"), "w").write(fill("tb_loop.spice", dict(
        CORNER=c, MIMCORNER=mimc(c), RESCORNER=resc(c), TEMP=t, VDD="%g" % v, IB="%.6g" % (ib * ibs),
        IRD="%.6g" % (IRAMP_DIODE * irs), RST=rst, CEQ="%.4g" % C_EQ)))
    return grab(ngspice(d, "loop.spice"))
