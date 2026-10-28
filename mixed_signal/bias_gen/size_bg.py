"""bias_gen sizing: gm/Id tables + Pelgrom matching (stage A), ngspice
operating points over 135 PVT x resistor cells (stage B), knee selection.

    ./container.sh 'python3 -u size_bg.py'            (run.sh phase `size`)

Writes data/stage_a.csv, data/stage_a_front.csv, data/stage_b.csv,
data/sizing.json and work/bias_gen.spice (run.sh compares it with the
checked-in bias_gen.spice). Method and rationale: DESIGN_RECIPE.md.

Topology (bg.netlist): NMOS-defined beta multiplier (XMN1 na fingers diode,
XMN2 K*na fingers on ppolyf_u), 1:1 PMOS mirror (npm fingers each); sinks
from nb (nc per comparator, nr for the ramp), sources from pb (nm per
midref buffer); PMOS-diode bleeder startup; MIM decaps. ONE L and ONE finger
width for every MOS of both rows [U].
"""
import itertools
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bg  # noqa: E402

JOBS = int(os.environ.get("JOBS", "12"))
L_CHOICES = (0.7, 0.8, 0.9)                    # [U] L below 1 um; 0.5 / 0.6 never reached a front (data/stage_a.csv, first runs)
WF_CHOICES = (2.0, 4.0)                           # one finger width for both rows [U], [A] grid
K_CHOICES = (4, 8, 16)                           # beta-multiplier ratio [A]; 8-16 minimises sigma per area (recipe s.3)
NA_CHOICES = tuple(range(2, 17, 2))           # even: every matched device splits about the row centre [U]
NR_CHOICES = tuple(range(2, 17, 2))
NPM_CHOICES = tuple(range(2, 17, 2))
GMID_CORE = (8.0, 24.0)                        # core diode window: moderate..weak inversion [A]
GMID_MIRROR_MIN = 5.0                          # PMOS mirror not deeper than gm/Id 5 (headroom) [A]
SIGMA_CMP_MAX = 0.10                           # total sigma(I)/I of a comparator output, prefilter [A]
N_SIGMA = 3.0                                  # mismatch margin on the comparator requirement [U]
S_MR = float(os.environ.get("S_MR", "0.85"))   # midref nominal scale, set by the midref benches (recipe s.6)
S_PVT_STAGE_A = 1.42                           # [M] explore/try1.py, replaced per candidate in stage B
NBL = 4                                        # bleeder diodes [M] explore/try1.py: <= 68 nA at 135 cells
P_CMP_1X = 96.9e-6                             # [C] comparator worst-state power at 1.0x (README)
V_NODE = dict(cmp=2.44, ramp=2.48, mr=0.75)    # [M] consumer diode nodes at typical (explore/try1.py)
N_FRONT = int(os.environ.get("N_FRONT", "60"))
NZ_CAL = 0.01567                               # [M] ramp-noise LSB per unit of the 1/f proxy, median fit to 40 stage-B
                                               # points (explore/nz_fit.py; -4..+47 %): a screen only, stage B measures
SIGMA_CAL = 1.06                               # [M] MC / Pelgrom ratio of the first selection (verify mc: 5.42 / 5.14 %)
NOISE_MAX = 0.9 * 0.110                        # [C] ramp-bias allocation 0.110 LSB (NOISE_BUDGET row 4), 10 % kept
                                               # for the VACASK / analysis ratio (0.087 / 0.079) [M]
NOISE_OLD = None                               # old bias_gen ramp-line noise, measured once in main()
RAMP_TOL = 0.05                                # ramp current within +-5 % of 3.1314 uA at typical: its slope is a
                                               # trim / calibration knob (ramp_gen DESIGN_RECIPE R2) and spans
                                               # ~0.75..1.5x over PVT anyway [A]
RES_SQ = None                                  # ohm/sq of RES_TYPE at typical/27 C, from data/res_char.csv


def res_sheet():
    with open(os.path.join(bg.BLOCK, "data", "res_char.csv")) as h:
        keys = h.readline().strip().split(",")
        for line in h:
            r = dict(zip(keys, line.strip().split(",")))
            if r["corner"] == "res_typical" and float(r["temp"]) == 27:
                return float(r[bg.RES_TYPE])
    raise SystemExit("FAIL: no res_typical/27 row in data/res_char.csv")


class Table:
    def __init__(self, dev):
        t = np.load(os.path.join(bg.BLOCK, "work", "lut", f"{dev}.npz"))
        self.L, self.W, self.VSB, self.VDS, self.VGS = t["L"], t["W"], t["VSB"], t["VDS"], t["VGS"]
        self.t = {k: t[k] for k in ("id", "gm", "gds", "vth", "vdsat")}

    def _iw(self, L, wf):
        return int(np.argmin(abs(self.L - L * 1e-6))), int(np.argmin(abs(self.W - wf * 1e-6)))

    def at(self, key, L, wf, vgs, vds, vsb=0.0):
        """Value at (vgs, vds, vsb) for one finger; linear in VDS and VSB, VGS on the 10 mV grid."""
        il, iw = self._iw(L, wf)
        fb = np.clip(vsb / self.VSB[-1], 0.0, 1.0)
        j = int(np.clip(np.searchsorted(self.VDS, vds) - 1, 0, len(self.VDS) - 2))
        wd = np.clip((vds - self.VDS[j]) / (self.VDS[j + 1] - self.VDS[j]), 0.0, 1.0)
        out = 0.0
        for ib, wgt in ((0, 1.0 - fb), (1, fb)):
            a = self.t[key][il, iw, ib]                       # [VDS, VGS]
            col = a[j] * (1.0 - wd) + a[j + 1] * wd
            out += wgt * np.interp(vgs, self.VGS, col)
        return out

    def diode(self, L, wf, i_f):
        """VGS of a diode finger carrying i_f (VDS = VGS)."""
        lo, hi = 0.2, 2.2
        for _ in range(40):
            v = 0.5 * (lo + hi)
            if self.at("id", L, wf, v, v) < i_f:
                lo = v
            else:
                hi = v
        return 0.5 * (lo + hi)


def sig_dvt(flav, L, wf, a, b):
    """sigma(dVt) between a devices of a fingers and b fingers (Pelgrom, PDK pair coefficient)."""
    leff = max(L * 1e-6 - bg.PDK_MM["par_l"], 0.05e-6)
    weff = wf * 1e-6 - bg.PDK_MM["par_w"]
    unit = bg.PDK_MM[flav]["par_vth"] * 1e-6 / np.sqrt(leff * weff)
    return unit * np.sqrt(0.5 * (1.0 / a + 1.0 / b))


def sig_beta(flav, L, wf, a, b):
    leff = max(L * 1e-6 - bg.PDK_MM["par_l"], 0.05e-6)
    weff = wf * 1e-6 - bg.PDK_MM["par_w"]
    unit = bg.PDK_MM[flav]["par_k"] * 1e-6 / np.sqrt(leff * weff)
    return unit * np.sqrt(0.5 * (1.0 / a + 1.0 / b))


def row_fingers(s):
    """Fingers per row before dummies: (PMOS, NMOS)."""
    p = 2 * s["npm"] + 2 * s["nm"] + s["nbl"]
    n = s["na"] + s["K"] * s["na"] + bg.N_CMP * s["nc"] + s["nr"] + 2
    return p, n


def area(s, rlen_total):
    p, n = row_fingers(s)
    nfin = max(p, n) + 4                                   # 2 dummies at each row end [A]
    length = nfin * (s["L"] + bg.FINGER_PITCH_EXTRA)
    height = 2 * (s["wf"] + bg.ROW_OVERHEAD)
    a_rows = length * height
    a_res = rlen_total * (bg.RES_W + 1.0)                 # strip + spacing [A]
    return a_rows + a_res, length, height


def stage_a(tn, tp):
    rows = []
    for L, wf, K, na, nr, npm in itertools.product(L_CHOICES, WF_CHOICES, K_CHOICES, NA_CHOICES, NR_CHOICES, NPM_CHOICES):
        # per-NMOS-finger current that makes the ramp exactly 3.1314 uA at its node
        i_f = bg.I_RAMP_NOM / nr
        vgs1 = tn.diode(L, wf, i_f)
        i_f *= i_f / tn.at("id", L, wf, vgs1, V_NODE["ramp"])           # VDS correction, one step
        vgs1 = tn.diode(L, wf, i_f)
        ic = na * i_f
        gm1 = na * tn.at("gm", L, wf, vgs1, vgs1)
        gmid1 = gm1 / ic
        if not GMID_CORE[0] <= gmid1 <= GMID_CORE[1]:
            continue
        # PMOS mirror
        vsgp = tp.diode(L, wf, ic / npm)
        gmidp = npm * tp.at("gm", L, wf, vsgp, vsgp) / ic
        if gmidp < GMID_MIRROR_MIN:
            continue
        pb = bg.VDD - vsgp
        # degenerated XMN2: find x = Ic R with K*na fingers at VGS1 - x, VSB = x
        lo, hi = 0.0, 0.6
        for _ in range(40):
            x = 0.5 * (lo + hi)
            i2 = K * na * tn.at("id", L, wf, vgs1 - x, pb - x, x)
            if i2 > ic:
                lo = x
            else:
                hi = x
        x = 0.5 * (lo + hi)
        R = x / ic
        gm2 = K * na * tn.at("gm", L, wf, vgs1 - x, pb - x, x)
        den = abs(1.0 / gm1 - 1.0 / gm2 - R)
        # mismatch: core (dVt of XMN1/XMN2 and the PMOS mirror error), per output
        s_dvt_n = sig_dvt("nfet", L, wf, na, K * na)
        s_eps = np.hypot(gmidp * sig_dvt("pfet", L, wf, npm, npm), sig_beta("pfet", L, wf, npm, npm))
        s_core = np.hypot(s_dvt_n, s_eps * ic * (1.0 / gm2 + R)) / (ic * den)
        # comparator fingers for the target scale, at the comparator node's VDS; the
        # per-finger current may float by +-RAMP_TOL (the ramp's slope tolerance)
        u_c = tn.at("id", L, wf, vgs1, V_NODE["cmp"])
        nc_prov = 1
        for nc in range(2, 61, 2):
            s_out = np.hypot(gmid1 * sig_dvt("nfet", L, wf, na, nc), sig_beta("nfet", L, wf, na, nc))
            s_tot = np.hypot(s_core, s_out)
            f_need = S_PVT_STAGE_A * (1 + N_SIGMA * s_tot) * bg.I_CMP_NOM / (nc * u_c)
            if f_need <= 1 + RAMP_TOL:
                nc_prov = nc
                f = max(f_need, 1 - RAMP_TOL)
                break
        else:
            continue
        u_c *= f
        if s_tot > SIGMA_CMP_MAX:
            continue
        # 1/f screen of the ramp line: XMN1 and the ramp sink (gm/Id^2 / area), the PMOS mirror at half weight
        nz_est = NZ_CAL * np.sqrt(gmid1 ** 2 * (1 / (na * wf * L) + 1 / (nr * wf * L)) + 0.5 * gmidp ** 2 * 2 / (npm * wf * L))
        if nz_est > NOISE_MAX:
            continue
        u_m = tp.at("id", L, wf, vsgp, bg.VDD - V_NODE["mr"])
        nm = max(2, 2 * int(round(S_MR * bg.I_MR_NOM / u_m / 2)))
        s = dict(L=L, wf=wf, K=K, na=na, npm=npm, nc=nc_prov, nr=nr, nm=nm, nbl=NBL)
        rlen = R / RES_SQ * bg.RES_W
        a, length, height = area(s, rlen)
        s_c = nc_prov * u_c / bg.I_CMP_NOM
        ic *= f
        i_sup = 2 * ic + bg.N_CMP * nc_prov * u_c + nr * i_f * f + 2 * nm * u_m
        p_sys = bg.VDD * 2 * ic + bg.N_CMP * P_CMP_1X * s_c          # what this design choice costs [A model]
        rows.append(dict(s, f=f, ic=ic,gmid_n1=gmid1, gmid_n2=gm2 / ic, gmid_p=gmidp, vgs1=vgs1, vsgp=vsgp, R=R, rlen=rlen,
                         sig_core=s_core, sig_out=s_out, sig_tot=s_tot, nz_est=nz_est, s_c=s_c, i_sup=i_sup, p_sys=p_sys,
                         area=a, length=length, height=height))
    return rows


def pareto(rows, kx, ky):
    pts = sorted(rows, key=lambda r: (r[kx], r[ky]))
    front, best = [], np.inf
    for r in pts:
        if r[ky] < best - 1e-12:
            front.append(r)
            best = r[ky]
    return front


def write_csv(path, rows, keys=None):
    keys = keys or list(rows[0].keys())
    with open(path, "w") as h:
        h.write(",".join(keys) + "\n")
        for r in rows:
            h.write(",".join(("%.6g" % r[k]) if isinstance(r[k], (float, np.floating)) else str(r[k]) for k in keys) + "\n")


# ------------------------------------------------------------ stage B
def seg_count(s, rlen_total):
    seg = 2 * (s["wf"] + bg.ROW_OVERHEAD)                  # strips as tall as the two rows [A]
    return max(2, int(np.ceil(rlen_total / seg)))


def tune(s, d, target_ramp=bg.I_RAMP_NOM):
    """Bisect/secant the per-segment length so the ramp output is exactly the
    ramp's 3.1314 uA at typical / 27 C / 3.3 V / res_typical."""
    dut = os.path.join(d, "dut.spice")

    def f(lseg):
        s["rlen"] = lseg
        open(dut, "w").write(bg.netlist(s))
        rows = bg.parse_op(bg.run(os.path.join(d, "tune"), bg.op_deck(s, ("typical", 27.0), "res_typical", dut)), s)
        r = [x for x in rows if x["vdd"] == bg.VDD]
        return (np.log(r[0]["ir"] / target_ramp), r[0]) if r else (np.nan, None)

    x0 = np.log(s["rlen"])
    f0, _ = f(np.exp(x0))
    x1 = x0 + 0.1
    f1, r = f(np.exp(x1))
    for _ in range(12):
        if not (np.isfinite(f0) and np.isfinite(f1)) or f1 == f0:
            return None
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        x0, f0 = x1, f1
        x1 = x2
        f1, r = f(np.exp(x1))
        if np.isfinite(f1) and abs(f1) < 2e-4:
            s["rlen"] = float(np.exp(x1))
            return r
    return None


def pvt_rows(s, d):
    dut = os.path.join(d, "dut.spice")
    open(dut, "w").write(bg.netlist(s))
    rows = []
    for c in bg.CORNERS:
        for t in bg.TEMPS:
            for rc in bg.RCORNERS:
                rows += bg.parse_op(bg.run(os.path.join(d, "pvt"), bg.op_deck(s, (c, t), rc, dut)), s)
    return rows


def stage_b_one(job):
    tag, a = job
    d = os.path.join(bg.BLOCK, "work", "sizeb", tag)
    os.makedirs(d, exist_ok=True)
    s = {k: a[k] for k in ("L", "wf", "K", "na", "npm", "nr", "nm", "nbl")}
    s["nc"] = s["nr"]                                  # provisional: the comparator sinks at the ramp's density
    s["rseg"] = seg_count(s, a["rlen"])
    s["rlen"] = a["rlen"] / s["rseg"]
    s["cpb"] = s["cnb"] = 0.0
    r = tune(s, d)
    if r is None:
        return tag, None
    rows = pvt_rows(s, d)
    if len(rows) != 135:
        return tag, None
    req = bg.bias_req()
    typ = r
    m = np.array([x["ic"] / typ["ic"] for x in rows])
    q = np.array([req[(x["corner"], x["temp"], x["vdd"])] for x in rows])
    k = int(np.argmax(q / m))
    s_pvt = float(q[k] / m[k])
    u_c = typ["ic"] / s["nc"]
    u_m = typ["iv"] / s["nm"]
    # comparator fingers: the smallest nc that meets s_pvt x (1 + 3 sigma) with the per-finger
    # current floated by at most +-RAMP_TOL (ramp current within tolerance); sigma re-evaluated per nc
    for nc in range(2, 81, 2):
        s_out = np.hypot(a["gmid_n1"] * sig_dvt("nfet", s["L"], s["wf"], s["na"], nc),
                         sig_beta("nfet", s["L"], s["wf"], s["na"], nc))
        s_tot = SIGMA_CAL * float(np.hypot(a["sig_core"], s_out))
        s_need = s_pvt * (1 + N_SIGMA * s_tot)
        f = s_need * bg.I_CMP_NOM / (nc * u_c)
        if f <= 1 + RAMP_TOL:
            f = max(f, 1 - RAMP_TOL)
            break
    else:
        return tag, None
    s["nc"] = nc
    r = tune(s, d, target_ramp=bg.I_RAMP_NOM * f)          # re-centre the core on the floated finger current
    if r is None:
        return tag, None
    typ = r
    u_c = typ["ic"] / nc
    nm = max(2, 2 * int(round(S_MR * bg.I_MR_NOM / u_m / 2)))
    # ramp-bias noise: the ramp's old bias_gen share scaled by the mirror-line noise ratio
    open(os.path.join(d, "dut.spice"), "w").write(bg.netlist(dict(s, nm=nm)))
    vn = bg.noise_new(os.path.join(d, "noise"), os.path.join(d, "dut.spice"))
    nz = bg.RAMP_BIAS_NOISE_OLD_LSB * vn / NOISE_OLD
    out = dict(tag=tag, L=s["L"], wf=s["wf"], K=s["K"], na=s["na"], npm=s["npm"], nr=s["nr"], nc=nc, nm=nm, nbl=s["nbl"],
               rseg=s["rseg"], rlen=s["rlen"], ic=typ["icore"], u_c=u_c, u_m=u_m, s_pvt=s_pvt, f=f,
               worst=f"{rows[k]['corner']}/{rows[k]['temp']:g}/{rows[k]['vdd']:g}/{rows[k]['rcorner']}",
               sig_core=a["sig_core"], sig_out=float(s_out), sig_tot=s_tot, s_need=s_need, s_c=typ["ic"] / bg.I_CMP_NOM,
               i_ramp=typ["ir"], s_m=nm * u_m / bg.I_MR_NOM, noise_lsb=nz, noise_ok=int(nz <= NOISE_MAX),
               m_lo=float(m.min()), m_hi=float(m.max()), hr_min=min(x["hr_min"] for x in rows),
               ibl_max=max(x["ibl"] for x in rows))
    sfin = dict(s, nc=nc, nm=nm)
    out["area"], out["length"], out["height"] = area(sfin, s["rlen"] * s["rseg"])
    out["p_sys"] = bg.VDD * 2 * typ["icore"] + bg.N_CMP * P_CMP_1X * out["s_c"]
    out["i_gen"] = 2 * typ["icore"] + bg.N_CMP * nc * u_c + s["nr"] * typ["ir"] / s["nr"] + 2 * nm * u_m
    return tag, out


def main():
    global RES_SQ
    RES_SQ = res_sheet()
    tn, tp = Table("nfet_03v3"), Table("pfet_03v3")
    rows = stage_a(tn, tp)
    print(f"stage_a_candidates = {len(rows)}")
    if not rows:
        print("FAIL: stage A: no candidate")
        return 1
    write_csv(os.path.join(bg.BLOCK, "data", "stage_a.csv"), rows)
    front = pareto(rows, "area", "p_sys")
    # thin the front to N_FRONT points spread along it
    if len(front) > N_FRONT:
        idx = np.unique(np.round(np.linspace(0, len(front) - 1, N_FRONT)).astype(int))
        front = [front[i] for i in idx]
    write_csv(os.path.join(bg.BLOCK, "data", "stage_a_front.csv"), front)
    print(f"stage_a_front = {len(front)}")
    global NOISE_OLD
    NOISE_OLD = bg.noise_old(os.path.join(bg.BLOCK, "work", "sizeb", "noise_old"))
    print(f"noise_old_line_uv = {NOISE_OLD * 1e6:.3f}")
    jobs = [(f"a{i:03d}", a) for i, a in enumerate(front)]
    with ThreadPoolExecutor(JOBS) as ex:
        res = list(ex.map(stage_b_one, jobs))
    got = [o for _, o in res if o is not None]
    print(f"stage_b_solved = {len(got)} of {len(jobs)}")
    if not got:
        print("FAIL: stage B: no candidate solved")
        return 1
    write_csv(os.path.join(bg.BLOCK, "data", "stage_b.csv"), got)
    fb = pareto([o for o in got if o["noise_ok"]], "area", "p_sys")
    print("stage_b_noise_ok = %d of %d" % (sum(o["noise_ok"] for o in got), len(got)))
    # knee (kneedle): the front point farthest below the chord joining its two ends,
    # in normalised (area, power)
    A = np.array([o["area"] for o in fb])
    P = np.array([o["p_sys"] for o in fb])
    an = (A - A.min()) / max(np.ptp(A), 1e-12)
    pn = (P - P.min()) / max(np.ptp(P), 1e-12)
    sel = fb[int(np.argmax(1.0 - an - pn))]
    for o in fb:
        print(f"REPORT: front {o['tag']} L {o['L']:g} wf {o['wf']:g} K {o['K']} na {o['na']} npm {o['npm']} nc {o['nc']} "
              f"nr {o['nr']} nm {o['nm']}: s_pvt {o['s_pvt']:.3f} (worst {o['worst']}), sigma {100 * o['sig_tot']:.2f} %, "
              f"s_c {o['s_c']:.3f}, ramp noise {o['noise_lsb']:.4f} LSB, area {o['area']:.0f} um2, p_sys {o['p_sys'] * 1e6:.1f} uW"
              + ("  <- selected" if o is sel else ""))
    json.dump(sel, open(os.path.join(bg.BLOCK, "data", "sizing.json"), "w"), indent=1, default=float)
    s = {k: sel[k] for k in ("L", "wf", "K", "na", "npm", "nc", "nr", "nm", "nbl", "rseg", "rlen")}
    s["cpb"] = float(os.environ.get("CPB_PF", "1.0"))
    s["cnb"] = float(os.environ.get("CNB_PF", "1.0"))
    a = [r for r in rows if all(r[k] == sel[k] for k in ("L", "wf", "K", "na", "npm", "nr"))][0]
    head = (
        "* bias_gen -- constant-gm (beta-multiplier) bias generator for the 8-bit\n"
        "* bottom-plate ADC: current outputs to four comparator comparators, the ramp\n"
        "* and the two midref_v2 buffers. GENERATED by size_bg.py; do not hand-edit.\n"
        "* Every MOS: one L and one finger width, PMOS row over NMOS row (floorplan.py).\n"
        f"*   L {s['L']:g} um, finger W {s['wf']:g} um, K {s['K']}, R {s['rseg']} x {s['rlen']:.3f} um {bg.RES_TYPE} (W {bg.RES_W:g} um)\n"
        f"*   core {sel['ic'] * 1e6:.4g} uA per branch, XMN1 gm/Id {a['gmid_n1']:.1f}, PMOS mirror gm/Id {a['gmid_p']:.1f} [P]\n"
        f"*   cmp sink {s['nc']} fingers: {sel['s_c']:.3f} x 1.931 uA [M]; ramp sink {s['nr']} fingers: {sel['i_ramp'] * 1e6:.4g} uA [M];\n"
        f"*   midref source {s['nm']} fingers: {sel['s_m']:.3f} x 12.36 uA [M]\n"
        f"*   135-cell requirement s_pvt {sel['s_pvt']:.3f} [M] x (1 + 3 sigma {100 * sel['sig_tot']:.2f} % [P])\n"
        f"*   decaps: pb {s['cpb']:g} pF to vdd, nb {s['cnb']:g} pF to vss (MIM over the rows)\n"
        "* Ports: vdd vss icmp0..3 (sinks, to each comparator's own pbias diode), iramp (sink,\n"
        "* to the ramp's L=1u W=20u nf=10 diode), ivref ivbl (sources, to midref_buf ib).\n"
        "* The simulators are the authority, not these lines.\n")
    os.makedirs(os.path.join(bg.BLOCK, "work"), exist_ok=True)
    with open(os.path.join(bg.BLOCK, "work", "bias_gen.spice"), "w") as h:
        h.write(head + bg.netlist(s))
    json.dump(dict(s, **{k: sel[k] for k in ("ic", "s_c", "s_m", "s_pvt", "sig_tot", "area", "p_sys")},
                   gmid_n1=a["gmid_n1"], gmid_n2=a["gmid_n2"], gmid_p=a["gmid_p"], noise_lsb=sel["noise_lsb"], sig_core=sel["sig_core"], sig_out=sel["sig_out"], i_ramp=sel["i_ramp"], f=sel["f"]),
              open(os.path.join(bg.BLOCK, "data", "sizing.json"), "w"), indent=1, default=float)
    print(f"selected = {sel['tag']}")
    print("PASS: size: knee selected, work/bias_gen.spice written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
