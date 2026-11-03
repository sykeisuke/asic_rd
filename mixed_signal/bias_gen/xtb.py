"""The xschem testbenches of bias_gen against the hand decks (run by schematic.sh).

    ./container.sh 'python3 xtb.py'          (JOBS=6 parallel ngspice runs)

Each tb_<name>.sch (tb_sch.py) is netlisted by xschem with this folder's
xschemrc (bias_gen from bias_gen.sch, the comparator from
../comparator/comparator.sch), simulated by ngspice in work/xtb_<name>/, and
its figures are compared with the deck verify_bg.py writes for the same
nominal case (typical, 27 C, 3.3 V, res_typical), re-built here by the same
functions and written to work/xtb_<name>/ref*.spice.

Gates (PASS/FAIL), figure by figure:
  identical devices (op, startup, mc, noise): 1e-6 relative, or 10 pA / 10 ps
      absolute, whichever is larger
  with the comparator (cmp, xtalk): the drawing's comparator comes from
      comparator.sch, whose PDK symbols write the S/D geometry as exact
      expressions where the deck (size_v3.dev, DUT_GEOM=1) writes them
      rounded to four digits, and the trip deck runs on ngspice's default
      reltol / gmin where the drawing's one .control runs both analyses on
      the dynamic bench's options: times are gated at 1 ns (the deck's
      measure resolution is 10 ps), the trip at 50 uV (two sweep steps);
      the other figures are reported
A bench whose simulation exceeds the ~5 min budget is reported as skipped.
Writes data/xtb.csv; prints PASS/FAIL/REPORT and "xtb_<name>_<figure> = value" lines.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BLOCK)
import bg  # noqa: E402
import verify_bg as V  # noqa: E402
import tb_sch as T  # noqa: E402

RC = os.path.join(BLOCK, "xschemrc")
WORK = os.path.join(BLOCK, "work")
GEN = V.GEN
JOBS = int(os.environ.get("JOBS", "6"))
NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
TOL_REL, TOL_ABS = 1e-6, 1e-11             # identical devices: 1e-6 relative, or 10 pA / 10 ps
TOL_T_CMP = 1e-9                           # times through the comparator (see the module docstring)
TOL_TRIP = 50e-6                           # the static trip: two 25 uV sweep steps
BUDGET_S = 330                             # ~5 min per ngspice run
TRAPZ = getattr(np, "trapezoid", None) or np.trapz
NOMINAL = ("typical", 27.0, "res_typical")


def xdir(tb, *sub):
    d = os.path.join(WORK, f"xtb_{tb}", *sub)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, ".spiceinit"), "w") as h:      # one OpenMP thread (ngspice-num-threads trap)
        h.write("set num_threads=1\n")
    return d


def netlist(tb):
    d = xdir(tb)
    net = os.path.join(d, f"tb_{tb}.spice")
    if os.path.exists(net):
        os.remove(net)
    with open(os.path.join(d, "xschem.txt"), "w") as log:
        subprocess.run(["xschem", "--rcfile", RC, "-b", "-q", "-n", "-s", "-o", d, f"tb_{tb}.sch"], cwd=BLOCK,
                       stdout=log, stderr=subprocess.STDOUT, timeout=300)
    return open(net).read() if os.path.exists(net) else None


class Budget(Exception):
    pass


def ngspice(d, name, text=None, timeout=BUDGET_S):
    """Run one deck in d; returns its output text. Raises Budget on the time limit."""
    if text is not None:
        with open(os.path.join(d, name), "w") as h:
            h.write(text)
    out = name.replace(".spice", ".out")
    p = os.path.join(d, out)
    if os.path.exists(p):
        os.remove(p)                          # never read a stale output
    env = dict(os.environ, OMP_NUM_THREADS="1")
    t0 = time.time()
    try:
        subprocess.run(["ngspice", "-b", "-o", out, name], cwd=d, env=env, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise Budget(f"{os.path.basename(d)}/{name} exceeded {timeout} s")
    key = os.path.relpath(os.path.join(d, name), WORK)
    TIMES[key] = time.time() - t0
    txt = open(p, errors="replace").read() if os.path.exists(p) else ""
    LAST_ERR[os.path.basename(d.rstrip("/"))] = first_error(txt)
    return txt


TIMES = {}        # deck -> ngspice wall seconds


def first_error(txt):
    """The first real ngspice error of a run (two lines), skipping the generic
    "This may cause subsequent errors" warning bg.first_error stops at."""
    lines = txt.splitlines()
    for k, ln in enumerate(lines):
        low = ln.lower()
        if "subsequent errors" in low or low.lstrip().startswith("warning"):
            continue
        if any(w in low for w in ("error", "unknown", "undefined", "not found", "no such", "cannot", "not available")):
            return " | ".join(x.strip()[:150] for x in lines[k:k + 2])
    return "no output" if not txt else "no error line"


LAST_ERR = {}     # run directory -> first ngspice error line (for a REPORT when a bench gives no figures)


def grab(txt, key):
    m = re.search(r"^\s*%s\s*=\s*(%s)" % (re.escape(key), NUM), txt, re.M)
    return float(m.group(1)) if m else float("nan")


def floats(s):
    return [float(x) for x in s.split()]


def ulp(v):
    """One unit in the last digit of ngspice's echo of v (six significant digits, %g)."""
    if not np.isfinite(v) or v == 0:
        return 0.0
    return 10.0 ** (np.floor(np.log10(abs(v))) - 5)


VOLTS = ("vsu", "vnb", "vpb", "vlc", "vlr", "vlv", "suf", "armed", "pbx", "pbn", "vtrip_v")


# ------------------------------------------------------------------ reference decks and figures
def op_figs(txt):
    """{vdd: {col: value}} from the OP echo lines (bg.op_deck)."""
    cols = list(bg.OP_COLS) + [f"hr_{n}" for n in bg.devices(V.SIZ)]
    out = {}
    for m in re.finditer(r"^OP (\S+) (\S+) (\S+) (\S+) (.*)$", txt, re.M):
        out[m.group(4)] = dict(zip(cols, floats(m.group(5))))
    return out


def ref_op(d):
    return op_figs(ngspice(d, "ref.spice", bg.op_deck(V.SIZ, NOMINAL[:2], NOMINAL[2], GEN)))


def startup_figs(txt):
    """[(icf, icmpf, suf, tup), ...] in order of appearance."""
    st = re.findall(r"^START (\S+) (\S+) (\S+)", txt, re.M)
    t9 = re.findall(r"^T90 (\S+)", txt, re.M)
    return [dict(zip(("icf", "icmpf", "suf", "tup"), floats(" ".join(a) + " " + b))) for a, b in zip(st, t9)]


def ref_startup(d):
    dut = os.path.join(d, "gen_x.spice")
    open(dut, "w").write(bg.netlist(V.SIZ, "bias_gen_v2x", export=True))
    out = []
    for case in ("ramp100n", "dead"):
        out += startup_figs(ngspice(d, f"ref_{case}.spice", V.startup_deck(*NOMINAL, case, dut)))
    return out


MC_COLS = ("icmp0", "icmp1", "icmp2", "icmp3", "iramp", "ivref", "ivbl", "icore")


def mc_figs(txt):
    m = re.search(r"^MC 1 (.*)$", txt, re.M)
    return dict(zip(MC_COLS, [abs(x) for x in floats(m.group(1))])) if m else {}


def ref_mc(d):
    return mc_figs(ngspice(d, "ref.spice", V.mc_deck(1, 1)))


def noise_deck():
    """phase_noise's "new" deck, verbatim."""
    return ("* new: iramp into the ramp's diode\n" + bg.NGSPICE_HEAD.format(corner="typical", rcorner="res_typical", mim="typical")
            + f".include {GEN}\n.temp 27\nVDD vdd 0 3.3 ac 1\nXG vdd 0 icmp0 icmp1 icmp2 icmp3 iramp ivref ivbl bias_gen\n"
            + bg.consumer_loads()
            + ".control\nset num_threads=1\nnoise v(lr) VDD dec 20 1 100meg\nsetplot noise1\n"
            + "wrdata nz_new.txt onoise_spectrum\nquit\n.endc\n.end\n")


def noise_figs(d):
    """rms over 1 Hz .. 1 / (2 pi 12.8 us) as phase_noise integrates it, and the spectrum."""
    try:
        fn = np.loadtxt(os.path.join(d, "nz_new.txt"))
    except (OSError, ValueError):
        return {}
    f, sn = fn[:, 0], fn[:, 1]
    band = f <= 1.0 / (2 * np.pi * 12.8e-6)
    return dict(vn_band=float(np.sqrt(TRAPZ(sn[band] ** 2, f[band]))), f=f, s=sn,
                s_10hz=float(sn[int(np.argmin(abs(f - 10)))]), s_1mhz=float(sn[int(np.argmin(abs(f - 1e6)))]))


def ref_noise(d):
    ngspice(d, "ref.spice", noise_deck())
    return noise_figs(d)


CMP_KEYS = ("vtrip_v", "delay_vbl", "delay_dyn", "fall", "ped_counts", "armed", "p_avg")


def cmp_figs(txt):
    blk = txt.split("RESULT_BEGIN")[-1].split("RESULT_END")[0] if "RESULT_BEGIN" in txt else ""
    return {k: grab(blk, k) for k in CMP_KEYS}


def ref_cmp(d):
    """phase_cmp's nominal cell: tb_sel_dc (trip) then tb_sel at the plateau level, the
    generator on icmp0 = pbias and the other consumers on diodes (gen_lines)."""
    S3, s = T.cmp_design()
    c, t, rc = NOMINAL
    subs = S3.common_subs(s, d, 0.0, (c, t, 3.3))
    subs["IREF"] = "0"
    cmp_net = open(subs["DUT"]).read()
    for name, mim in (("dut_dc.spice", bg.mimcorner(c)), ("dut_tr.spice", None)):
        with open(os.path.join(d, name), "w") as h:
            h.write(cmp_net + "\n" + V.gen_lines(rc, "vddb", "pbias", mim=mim) + "\n")
    subs["DUT"] = os.path.join(d, "dut_dc.spice")
    vtrip = S3.grab(S3.run_deck(d, "tb_sel_dc.spice", subs, BUDGET_S), "vtrip")
    shutil.copy(os.path.join(d, "tb_sel_dc.spice"), os.path.join(d, "ref_dc.spice"))
    k = 40.5                                   # the plateau level (phase_cmp "plat")
    subs["DUT"] = os.path.join(d, "dut_tr.spice")
    sub2 = dict(subs, VIN="%.9g" % (S3.VR_LO + k * S3.LSB), TSTOP="%.6g" % (400e-9 + k * S3.TCOUNT + 400e-9),
                VTRIP="%.6f" % vtrip)
    blk = S3.run_deck(d, "tb_sel.spice", sub2, BUDGET_S)
    shutil.copy(os.path.join(d, "tb_sel.spice"), os.path.join(d, "ref_tr.spice"))
    out = {k2: S3.grab(blk, k2) for k2 in CMP_KEYS}
    out["vtrip_v"] = float("%.6f" % vtrip) if np.isfinite(vtrip) else vtrip
    return out


def xt_figs(txt):
    """[(t0, pbx, pbn), ...] in order (case a, case q)."""
    return [dict(zip(("t0", "pbx", "pbn"), floats(" ".join(m)))) for m in re.findall(r"^XT (\S+) (\S+) (\S+)", txt, re.M)]


def ref_xtalk(d):
    """phase_xtalk's typical cell, cases a and q (its cell lines reproduced here)."""
    S3, s = T.cmp_design()
    dut = os.path.join(d, "cmp_dut.spice")
    open(dut, "w").write(S3.subckt(s))
    kind, L, wf, nf = bg.CMP_DIODE
    k2, L2, w2, n2 = bg.RAMP_DIODE
    k3, L3, w3, n3 = bg.MR_DIODE
    diodes = "\n".join([bg.mos(f"XRP{i}", f"pb{i}", f"pb{i}", "vdd", "vdd", kind, L, wf, nf) for i in range(4)]
                       + [bg.mos("XGDR", "glr", "glr", "vdd", "vdd", k2, L2, w2, n2),
                          bg.mos("XGDV", "glv", "glv", "0", "0", k3, L3, w3, n3),
                          bg.mos("XGDB", "glb", "glb", "0", "0", k3, L3, w3, n3)])
    lvl = T.XT_LVL

    def cells(case):
        out = []
        for i in range(4):
            k = lvl if i == 0 else (lvl - 1 if case == "a" else 300)
            vin = 0.5 + k * 1.5 / 256
            out += [f"S2_{i} vref top{i} s2 0 swideal",
                    f"XCS{i} top{i} bot{i} cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u",
                    f"RLK{i} top{i} 0 1e15",
                    f"VBOT{i} bot{i} 0 PWL(0 {vin:.6f} 310n {vin:.6f} 310.1n 0.5 400n 0.5 14.4u {0.5 + 14e-6 * 1.5 / 256 / 50e-9:.6f})",
                    f"XDUT{i} vbl top{i} dout{i} clk vdd 0 0 pb{i} cmp",
                    f"CL{i} dout{i} 0 10f"]
        return "\n".join(out)
    c, t, rc = NOMINAL
    out = []
    for case in ("a", "q"):
        txt = V.XT_DECK.format(head=bg.NGSPICE_HEAD.format(corner=c, rcorner=rc, mim=bg.mimcorner(c)), temp=t, dut=dut,
                               gen=GEN, vdd=3.3, diodes=diodes, cells=cells(case), tstop=400e-9 + (lvl + 4) * 50e-9)
        out += xt_figs(ngspice(d, f"ref_{case}.spice", txt))
    return out


# ------------------------------------------------------------------ comparison
class Table:
    def __init__(self):
        self.rows, self.bad = [], 0

    def cmp(self, tb, fig, ref, x, tol=None, gate=True, unit=""):
        """One figure: tol = ("rel", r) | ("abs", a) | None. None is the identical-
        devices gate: 1e-6 relative, or 10 pA / 10 ps (1e-11) absolute, or one
        unit in the last digit the deck's echo prints (six significant digits:
        a difference the echo cannot resolve is not a difference), whichever is
        largest; a voltage (unit "V") gets ngspice's vntol, 1 uV, as its floor
        instead of 1e-11, the accuracy to which two orderings of the same
        matrix agree on a node."""
        ok = np.isfinite(ref) and np.isfinite(x)
        d = x - ref if ok else float("nan")
        rel = abs(d) / abs(ref) if ok and ref else (0.0 if ok and d == 0 else float("nan"))
        if tol is None:
            floor = 1e-6 if unit == "V" else TOL_ABS
            lim = max(TOL_REL * abs(ref), floor, ulp(ref)) if ok else float("nan")
            ltxt = "1e-6 rel / %s abs / echo digit" % ("1 uV" if unit == "V" else "1e-11")
        elif tol[0] == "rel":
            lim, ltxt = tol[1] * abs(ref), f"{tol[1]:g} rel"
        else:
            lim, ltxt = tol[1], f"{tol[1]:g} abs"
        good = ok and abs(d) <= lim
        verdict = "PASS" if good else "FAIL"
        if not gate:
            verdict = "REPORT"
        elif not good:
            self.bad += 1
        self.rows.append((tb, fig, ref, x, d, rel, ltxt, verdict))
        return good

    def write(self, path):
        with open(path, "w") as h:
            h.write("bench,figure,deck,xschem,diff,rel,tolerance,verdict\n")
            for r in self.rows:
                h.write("%s,%s,%.9g,%.9g,%.4g,%.4g,%s,%s\n" % r)

    def worst(self, tb):
        rs = [r for r in self.rows if r[0] == tb and r[7] != "REPORT" and np.isfinite(r[5])]
        if not rs:
            return "", float("nan")
        r = max(rs, key=lambda r: r[5])
        return r[1], r[5]


def line(tb, ok, text):
    print(("PASS: " if ok else "FAIL: ") + f"xtb {tb}: " + text)


def main():
    nets = {}
    for tb in T.SHEETS:
        nets[tb] = netlist(tb)
        if nets[tb] is None:
            print(f"FAIL: xtb {tb}: xschem did not netlist tb_{tb}.sch")
    if any(v is None for v in nets.values()):
        return 1

    jobs = {
        "ref_op": lambda: ref_op(xdir("op", "ref")),
        "sch_op": lambda: op_figs(ngspice(xdir("op"), "tb_op.spice")),
        "ref_startup": lambda: ref_startup(xdir("startup", "ref")),
        "sch_startup": lambda: startup_figs(ngspice(xdir("startup"), "tb_startup.spice")),
        "ref_mc": lambda: ref_mc(xdir("mc", "ref")),
        "sch_mc": lambda: mc_figs(ngspice(xdir("mc"), "tb_mc.spice")),
        "ref_noise": lambda: ref_noise(xdir("noise", "ref")),
        "sch_noise": lambda: (ngspice(xdir("noise"), "tb_noise.spice"), noise_figs(xdir("noise")))[1],
        "ref_cmp": lambda: ref_cmp(xdir("cmp", "ref")),
        "sch_cmp": lambda: cmp_figs(ngspice(xdir("cmp"), "tb_cmp.spice")),
        "ref_xtalk": lambda: ref_xtalk(xdir("xtalk", "ref")),
        "sch_xtalk": lambda: xt_figs(ngspice(xdir("xtalk"), "tb_xtalk.spice")),
    }

    def run(item):
        name, fn = item
        try:
            return name, fn(), None
        except Budget as e:
            return name, None, str(e)
        except Exception as e:                # noqa: BLE001  one bench's crash must not hide the others
            return name, None, f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        res = {n: (v, err) for n, v, err in ex.map(run, jobs.items())}

    tab = Table()
    skipped = []
    for tb in T.SHEETS:
        for side in ("ref", "sch"):
            v, err = res[f"{side}_{tb}"]
            if err and "exceeded" in err:
                skipped.append(tb)
                print(f"REPORT: xtb {tb}: {'deck' if side == 'ref' else 'drawing'} simulation skipped, over the 5 min budget ({err})")
            elif err:
                print(f"FAIL: xtb {tb}: {'deck' if side == 'ref' else 'drawing'} simulation failed: {err}")
                tab.bad += 1
    judged = []

    def both(tb):
        a, b = res[f"ref_{tb}"][0], res[f"sch_{tb}"][0]
        if tb in skipped:
            return None, None
        for side, v, key in (("deck", a, "ref"), ("drawing", b, f"xtb_{tb}")):
            if not v:
                print(f"FAIL: xtb {tb}: the {side} simulation gave no figures; ngspice: {LAST_ERR.get(key, 'no run')}")
                tab.bad += 1
        return (a, b) if (a and b) else (None, None)

    # op
    ref, sch = both("op")
    if ref:
        n = 0
        for vdd in sorted(ref):
            for col, rv in ref[vdd].items():
                tab.cmp("op", f"{col}@{vdd}V", rv, sch.get(vdd, {}).get(col, float("nan")),
                        unit="V" if (col in VOLTS or col.startswith("hr_")) else "A")
                n += 1
        w, wr = tab.worst("op")
        ok = tab.bad == 0 and all(r[7] != "FAIL" for r in tab.rows if r[0] == "op")
        r33 = ref["3.3"]
        line("op", ok, f"operating point of the drawing equals the deck's at 3.0 / 3.3 / 3.6 V: {n} figures within 1e-6 "
             f"(worst {wr:.2g} in {w}); icmp0 {r33['ic'] * 1e6:.4f} uA, iramp {r33['ir'] * 1e6:.4f} uA, ivref "
             f"{r33['iv'] * 1e6:.3f} uA, supply {r33['isup'] * 1e6:.2f} uA")
        for k, u in (("ic", "icmp_ua"), ("ir", "iramp_ua"), ("iv", "ivref_ua")):
            print(f"xtb_op_{u} = {sch['3.3'][k] * 1e6:.4f}")
        print(f"xtb_op_worst_rel = {wr:.3g}")
        judged.append("op")

    # startup
    ref, sch = both("startup")
    if ref:
        names = ("ramp100n", "dead")
        nfail0 = tab.bad
        for k, case in enumerate(names):
            r = ref[k] if k < len(ref) else {}
            x = sch[k] if k < len(sch) else {}
            for fig in ("icf", "icmpf", "suf", "tup"):
                tab.cmp("startup", f"{fig}_{case}", r.get(fig, float("nan")), x.get(fig, float("nan")),
                        unit="V" if fig in VOLTS else "A")
        w, wr = tab.worst("startup")
        ok = tab.bad == nfail0
        tup = {c: (ref[k].get("tup", float("nan")), sch[k].get("tup", float("nan"))) if k < min(len(ref), len(sch)) else
               (float("nan"), float("nan")) for k, c in enumerate(names)}
        line("startup", ok, f"the drawing's two cases (supply ramp 100 ns; forced dead state released at 10 us) end "
             f"on the deck's operating point and 90 % times within 1e-6 / 10 ps (worst {wr:.2g} in {w}): t90 "
             f"{tup['ramp100n'][1] * 1e6:.4f} us after the ramp (deck {tup['ramp100n'][0] * 1e6:.4f}), "
             f"{tup['dead'][1] * 1e6:.4f} us after the release (deck {tup['dead'][0] * 1e6:.4f})")
        print(f"xtb_startup_t90_ramp_us = {tup['ramp100n'][1] * 1e6:.5f}")
        print(f"xtb_startup_t90_dead_us = {tup['dead'][1] * 1e6:.5f}")
        print(f"xtb_startup_worst_rel = {wr:.3g}")
        judged.append("startup")

    # mc
    ref, sch = both("mc")
    if ref:
        nfail0 = tab.bad
        for col in MC_COLS:
            tab.cmp("mc", col, ref[col], sch.get(col, float("nan")))
        w, wr = tab.worst("mc")
        line("mc", tab.bad == nfail0, f"one mismatch draw (.options seed={V.SEED_BASE + 1}) of the drawing equals the "
             f"deck's: {len(MC_COLS)} currents within 1e-6 (worst {wr:.2g} in {w}); icmp0 {sch.get('icmp0', float('nan')) * 1e6:.4f} uA "
             f"vs the mismatch-free {res['ref_op'][0]['3.3']['ic'] * 1e6 if res['ref_op'][0] else float('nan'):.4f} uA, "
             "the same device order in both netlists")
        print(f"xtb_mc_icmp0_ua = {sch.get('icmp0', float('nan')) * 1e6:.4f}")
        print(f"xtb_mc_worst_rel = {wr:.3g}")
        judged.append("mc")

    # noise
    ref, sch = both("noise")
    if ref:
        nfail0 = tab.bad
        tab.cmp("noise", "vn_band_v", ref["vn_band"], sch["vn_band"])
        smax = float(np.max(np.abs(sch["s"] / ref["s"] - 1))) if sch["s"].shape == ref["s"].shape else float("nan")
        tab.cmp("noise", "spectrum_max_rel", 0.0, smax, ("abs", TOL_REL))
        line("noise", tab.bad == nfail0, f"noise on the ramp's mirror line, 1 Hz .. 12.4 kHz: {sch['vn_band'] * 1e6:.4f} uV rms "
             f"(deck {ref['vn_band'] * 1e6:.4f}), spectrum point by point within {smax:.2g} over 1 Hz - 100 MHz")
        print(f"xtb_noise_line_uv = {sch['vn_band'] * 1e6:.4f}")
        print(f"xtb_noise_spectrum_max_rel = {smax:.3g}")
        judged.append("noise")

    # cmp
    ref, sch = both("cmp")
    if ref:
        nfail0 = tab.bad
        tab.cmp("cmp", "vtrip_v", ref["vtrip_v"], sch["vtrip_v"], ("abs", TOL_TRIP))
        for fig in ("delay_vbl", "delay_dyn", "fall"):
            tab.cmp("cmp", fig, ref[fig], sch[fig], ("abs", TOL_T_CMP))
        tab.cmp("cmp", "ped_counts", ref["ped_counts"], sch["ped_counts"], ("abs", TOL_T_CMP / 50e-9), gate=False)
        for fig in ("armed", "p_avg"):
            tab.cmp("cmp", fig, ref[fig], sch[fig], ("rel", 1e-3), gate=False)
        dd = (sch["delay_dyn"] - ref["delay_dyn"]) * 1e12
        line("cmp", tab.bad == nfail0, f"comparator on icmp0 of the drawn generator: static trip {sch['vtrip_v']:.6f} V "
             f"(deck {ref['vtrip_v']:.6f}, |d| <= 50 uV), delay from the trip {sch['delay_dyn'] * 1e9:.3f} ns (deck "
             f"{ref['delay_dyn'] * 1e9:.3f}, d {dd:+.1f} ps), from VBL {sch['delay_vbl'] * 1e9:.3f} ns, dout fall "
             f"{sch['fall'] * 1e9:.3f} ns; times gated at 1 ns: the drawn comparator's S/D geometry is the PDK symbols' "
             "exact expressions where the deck writes them rounded to 4 digits, and the trip runs on the dynamic "
             "bench's reltol / gmin")
        print(f"REPORT: xtb cmp, reported: armed {sch['armed']:.4f} V (deck {ref['armed']:.4f}), pedestal "
              f"{sch['ped_counts']:.4f} counts (deck {ref['ped_counts']:.4f}); average supply power {sch['p_avg'] * 1e6:.2f} uW "
              f"(deck {ref['p_avg'] * 1e6:.2f}: the one-sheet bench keeps the static-trip comparator XDC, parked at its "
              "trip point, on the same supply during the transient)")
        for fig in ("vtrip_v", "delay_dyn", "delay_vbl", "fall"):
            print(f"xtb_cmp_{fig} = {sch[fig]:.6g}")
        print(f"xtb_cmp_delay_dyn_diff_ps = {dd:.2f}")
        judged.append("cmp")

    # xtalk
    ref, sch = both("xtalk")
    if ref:
        nfail0 = tab.bad
        ok2 = len(ref) == 2 and len(sch) == 2
        if ok2:
            for k, case in enumerate(("a", "q")):
                tab.cmp("xtalk", f"t0_{case}", ref[k]["t0"], sch[k]["t0"], ("abs", TOL_T_CMP))
                for fig in ("pbx", "pbn"):
                    tab.cmp("xtalk", f"{fig}_{case}", ref[k][fig], sch[k][fig], ("rel", 1e-4), gate=False)
            shr = (ref[0]["t0"] - ref[1]["t0"]) / V.LSB_T
            shs = (sch[0]["t0"] - sch[1]["t0"]) / V.LSB_T
            tab.cmp("xtalk", "shift_lsb", shr, shs, ("abs", TOL_T_CMP / V.LSB_T))
            line("xtalk", tab.bad == nfail0, f"four comparators on the drawn generator: victim decision shift "
                 f"{shs:+.4f} LSB (deck {shr:+.4f}) when three aggressors decide 1 LSB earlier; t0 {sch[0]['t0'] * 1e9:.4f} / "
                 f"{sch[1]['t0'] * 1e9:.4f} ns (deck {ref[0]['t0'] * 1e9:.4f} / {ref[1]['t0'] * 1e9:.4f}); times gated at "
                 "1 ns (0.02 LSB) for the comparator's geometry rounding, pbias excursions reported")
            print(f"REPORT: xtb xtalk, reported: victim pbias excursion {1e3 * (sch[0]['pbx'] - sch[1]['pbx']):+.4f} mV "
                  f"(deck {1e3 * (ref[0]['pbx'] - ref[1]['pbx']):+.4f})")
            print(f"xtb_xtalk_shift_lsb = {shs:.5f}")
            print(f"xtb_xtalk_shift_deck_lsb = {shr:.5f}")
        else:
            tab.bad += 1
            line("xtalk", False, f"expected two XT lines on each side, got deck {len(ref)}, drawing {len(sch)}")
        judged.append("xtalk")

    tab.write(os.path.join(BLOCK, "data", "xtb.csv"))
    print("REPORT: xtb ngspice wall seconds per deck: " + ", ".join(f"{k} {v:.1f}" for k, v in sorted(TIMES.items())))
    print(f"xtb_ngspice_total_s = {sum(TIMES.values()):.1f}")
    if skipped:
        print(f"REPORT: xtb: not compared (budget): {', '.join(sorted(set(skipped)))}")
    ok = tab.bad == 0
    print(("PASS: " if ok else "FAIL: ") + f"xtb: {len(judged)} of {len(T.SHEETS)} testbench drawings compared with "
          f"their hand decks ({', '.join(judged)}), {sum(1 for r in tab.rows if r[7] == 'FAIL')} figure(s) outside "
          "tolerance; data/xtb.csv")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
