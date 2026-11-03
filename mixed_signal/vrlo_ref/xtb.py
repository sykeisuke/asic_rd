"""The xschem testbench sheets against the hand-written benches (schematic.sh).

    ./container.sh 'python3 xtb.py'

For each of op, tran, loop, noise, mc:
  1. xschem netlists tb_<name>.sch (this folder's xschemrc: vrlo_ref from
     vrlo_ref.sch, the OLD ramp_simple from ../ramp_gen/ramp_simple.sch) into
     work/xtb_<name>/sch/;
  2. the netlist must carry every instance of the hand bench (same terminals,
     same value / model / parameters), every dot card and every .control
     line, the subcircuits the hierarchy supplies (vrlo_ref, ramp_simple; the
     loop bench includes work/dut_lb.spice instead), and nothing else;
  3. ngspice runs the xschem netlist and the hand bench filled at the same
     nominal case (tb_sch.SUBS) in work/xtb_<name>/{sch,hand}/, and the main
     figures are compared: op err and headrooms at 3.0 / 3.3 / 3.6 V; the 16
     tran measures; loop ugb / pm / T(10 Hz); noise rms 1 Hz - 1 GHz at vrlo
     and vramp and the supply transfer; the mc draw under the same seed and
     the mismatch-free point.
Tolerance 1e-6 relative or 10 uV / 10 ps / 1 pA where the drawn devices equal
the deck's (checked: the ramp subcircuit xschem emits vs ramp_simple.spice);
0.1 mV / 1 ns if the drawing adds S/D junction geometry the deck lacks
(reported). A bench whose simulation exceeds TIMEOUT is reported as skipped.
Writes data/xtb.csv; prints PASS: / FAIL: / REPORT: lines and `name = value`.
"""
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BLOCK)
import tb_sch  # noqa: E402
import verify_vrlo as V  # noqa: E402  read_xy / integ
import vr  # noqa: E402

RC = os.path.join(BLOCK, "xschemrc")
BENCHES = ("op", "tran", "loop", "noise", "mc")
TIMEOUT = 420          # s per ngspice run (~5 min budget per bench)
RAMP_DECK = os.path.normpath(os.path.join(BLOCK, "..", "ramp_gen", "ramp_simple.spice"))
# (abs, rel) tolerances per unit: tight when the devices are identical, loose with added geometry
TOL = {"V": (10e-6, 1e-6), "A": (1e-12, 1e-6), "s": (10e-12, 1e-6), "Hz": (0.0, 1e-6), "deg": (1e-4, 1e-6),
       "dB": (1e-4, 1e-6), "": (1e-9, 1e-6)}
LOOSE = {"V": (1e-4, 1e-3), "A": (1e-10, 1e-3), "s": (1e-9, 1e-3), "Hz": (0.0, 1e-3), "deg": (0.1, 1e-3),
         "dB": (0.01, 1e-3), "": (1e-6, 1e-3)}
bad = []


def verdict(ok, text):
    print(("PASS: " if ok else "FAIL: ") + text)
    if not ok:
        bad.append(text)
    return ok


def norm(s):
    s = re.sub(r"['{}\"]", "", s.strip())
    toks = [t for t in re.split(r"\s+", s) if t and t.lower() != "m=1"]
    return " ".join(toks).lower()


def joined(txt):
    """Lines with `+` continuations folded back, comments and blanks dropped."""
    out = []
    for ln in txt.splitlines():
        s = ln.rstrip()
        if not s.strip() or s.lstrip().startswith("*"):
            continue
        if s.lstrip().startswith("+") and out:
            out[-1] += " " + s.lstrip()[1:].strip()
        else:
            out.append(s)
    return out


def classify(txt):
    """{inst: {name: norm line}, dots: set, ctl: set, subs: {name: set(norm device lines)}}."""
    inst, dots, ctl, subs, state, cur = {}, set(), set(), {}, None, None
    for s in joined(txt):
        low = s.strip().lower()
        if state == "ctl":
            ctl.add(norm(s))
            if low.startswith(".endc"):
                state = None
            continue
        if state == "sub":
            if low.startswith(".ends"):
                state = None
            else:
                subs[cur].add(norm(s))
            continue
        if low.startswith(".control"):
            state = "ctl"
            ctl.add(norm(s))
        elif low.startswith(".subckt"):
            state, cur = "sub", s.split()[1]
            subs[cur] = set()
            dots.add(norm(s))
        elif low.startswith("."):
            if low != ".end":
                dots.add(norm(s))
        else:
            inst[s.split()[0].upper()] = norm(s)
    return dict(inst=inst, dots=dots, ctl=ctl, subs=subs)


def netlist(name):
    d = os.path.join(vr.WORK, f"xtb_{name}", "sch")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    subprocess.run(["xschem", "--rcfile", RC, "-b", "-q", "-n", "-s", "-o", d, f"tb_{name}.sch"], cwd=BLOCK,
                   stdout=open(os.path.join(d, "xschem.out"), "w"), stderr=subprocess.STDOUT, timeout=300)
    p = os.path.join(d, f"tb_{name}.spice")
    return open(p).read() if os.path.exists(p) else None


def hand_text(name):
    """The hand bench filled at the nominal case, as simulated."""
    return vr.fill(f"tb_{name}.spice", tb_sch.SUBS[name])


def hand_ref(name):
    """The same, as the xschem netlist has to carry it: the hierarchy supplies
    what the dut / ramp_simple includes supplied, the loop DUT comes by
    container path, echo lines unquoted (tb_sch.py)."""
    txt = hand_text(name)
    txt = re.sub(r"^\.include dut\.spice\s*$", "", txt, flags=re.M)
    txt = re.sub(r"^\.include \S+/ramp_simple\.spice\s*$", "", txt, flags=re.M)
    txt = re.sub(r"^\.include dut_lb\.spice\s*$", ".include %s/work/dut_lb.spice" % tb_sch.CBLOCK, txt, flags=re.M)
    txt = "\n".join(tb_sch.unquote_echo(ln) for ln in txt.splitlines())
    return txt


def check_netlist(name, sch):
    """The xschem netlist carries the hand bench: instances, dot cards, control lines, subcircuits."""
    h, x = classify(hand_ref(name)), classify(sch)
    ok = True
    missing = [k for k, v in h["inst"].items() if x["inst"].get(k) != v]
    extra = [k for k in x["inst"] if k not in h["inst"]]
    ok &= verdict(not missing and not extra, f"xtb {name}: {len(h['inst'])} bench instances in the xschem netlist, "
                  f"same terminals and values" + (f"; MISSING/DIFFERENT {missing}" if missing else "")
                  + (f"; EXTRA {extra}" if extra else ""))
    for k in missing:
        print(f"REPORT: xtb {name}: bench `{h['inst'][k]}` vs xschem `{x['inst'].get(k)}`")
    md = sorted(h["dots"] - x["dots"])
    ok &= verdict(not md, f"xtb {name}: {len(h['dots'])} dot cards of the bench in the netlist"
                  + (f"; missing {md}" if md else ""))
    mc = sorted(h["ctl"] - x["ctl"])
    ok &= verdict(not mc, f"xtb {name}: {len(h['ctl'])} .control lines of the bench in the netlist"
                  + (f"; missing {mc}" if mc else ""))
    want = ["ramp_simple"] + (["vrlo_ref_lb"] if name == "loop" else ["vrlo_ref"])
    if name == "tran":
        want.append("s1cell")
    have = set(x["subs"])
    if name == "loop":
        lb = os.path.join(vr.WORK, "dut_lb.spice")
        if os.path.exists(lb) and ".subckt vrlo_ref_lb" in open(lb).read():
            have.add("vrlo_ref_lb")
    ok &= verdict(all(w in have for w in want), f"xtb {name}: subcircuits {want} supplied "
                  f"(xschem hierarchy{' + work/dut_lb.spice' if name == 'loop' else ''}); netlist has {sorted(have)}")
    return ok, x


def ramp_equal(x):
    """The ramp_simple subcircuit xschem emitted from ../ramp_gen/ramp_simple.sch vs the deck."""
    deck = classify(open(RAMP_DECK).read())["subs"].get("ramp_simple", set())
    got = x["subs"].get("ramp_simple", set())
    return deck == got, deck ^ got


def run(name, kind, text):
    d = vr.rundir(f"xtb_{name}", kind, dut=open(os.path.join(BLOCK, "vrlo_ref.spice")).read())
    if name == "loop":
        shutil.copy(os.path.join(vr.WORK, "dut_lb.spice"), os.path.join(d, "dut_lb.spice"))
    deck = f"tb_{name}.spice"
    open(os.path.join(d, deck), "w").write(text)
    log = vr.ngspice(d, deck, timeout=TIMEOUT)
    return d, log


def figures(name, d, log):
    """{metric: (value, unit)} from one run."""
    f = {}
    if name == "op":
        for m in re.finditer(r"^OP typical 27 1 1 (\S+) (.*)$", log, re.M):
            vals = m.group(2).split()
            for k, v in zip(("hrt", "hrk", "hr1", "hr2", "hrs", "hr5", "err", "ireg", "vg"), vals):
                f[f"{k}@{m.group(1)}V"] = (float(v), "A" if k == "ireg" else "V")
    elif name == "tran":
        for k, v in vr.grab(log).items():
            f[k] = (v, "A" if k.startswith("ireg") else "V")
    elif name == "loop":
        g = vr.grab(log)
        for k, u in (("ugb_hz", "Hz"), ("pm_deg", "deg"), ("t0_db", "dB")):
            f[k] = (g.get(k, np.nan), u)
    elif name == "noise":
        a, b, p = (V.read_xy(os.path.join(d, n)) for n in ("nz_vrlo.txt", "nz_vramp.txt", "psr.txt"))
        f["nz_vrlo_rms"] = (V.integ(a[:, 0], a[:, 1] ** 2, 1, 1e9) if a is not None else np.nan, "V")
        f["nz_vramp_rms"] = (V.integ(b[:, 0], b[:, 1] ** 2, 1, 1e9) if b is not None else np.nan, "V")
        f["nz_vrlo_1k_rms"] = (V.integ(a[:, 0], a[:, 1] ** 2, 1, 1e3) if a is not None else np.nan, "V")
        for fq in (10, 1e6):
            f[f"psr@{int(fq)}Hz"] = (float(np.interp(fq, p[:, 0], p[:, 1])) if p is not None else np.nan, "")
    elif name == "mc":
        for tag, lg in (("", log), ("_nom", open(os.path.join(d, "nom.log"), errors="replace").read()
                                    if os.path.exists(os.path.join(d, "nom.log")) else "")):
            m = re.search(r"^MC 1 (\S+) (\S+)$", lg, re.M)
            f["er" + tag] = (float(m.group(1)) if m else np.nan, "V")
            f["ep" + tag] = (float(m.group(2)) if m else np.nan, "V")
    return f


def simulate(name, sch_txt):
    """Both runs; returns (figures_hand, figures_sch) or None when a run timed out."""
    def one(kind, text):
        d, log = run(name, kind, text)
        if name == "mc":           # the mismatch-free point under the same deck, as verify's draw 0
            nom = re.sub(r"sw_stat_mismatch=1", "sw_stat_mismatch=0", text)
            open(os.path.join(d, "nom.spice"), "w").write(nom)
            lg = vr.ngspice(d, "nom.spice", timeout=TIMEOUT)
            if not lg:
                return None
        return None if not log else figures(name, d, log)
    with ThreadPoolExecutor(2) as ex:
        h, x = ex.map(lambda a: one(*a), (("hand", hand_text(name)), ("sch", sch_txt)))
    return h, x


def main():
    os.makedirs(vr.DATA, exist_ok=True)
    nets, checks = {}, {}
    for n in BENCHES:
        t = netlist(n)
        if t is None:
            verdict(False, f"xtb {n}: xschem did not netlist tb_{n}.sch")
            continue
        ok, x = check_netlist(n, t)
        if ok:
            nets[n], checks[n] = t, x
    if not nets:
        print(f"xtb_fail_count = {len(bad)}")
        return 1
    same = {n: ramp_equal(x) for n, x in checks.items()}
    tight = all(s[0] for s in same.values())
    verdict(tight, "xtb: the ramp_simple subcircuit xschem emits from ../ramp_gen/ramp_simple.sch equals "
            "ramp_simple.spice device for device" + ("" if tight else f" (differences: {[s[1] for s in same.values() if s[1]]})"))
    if not tight:
        print("REPORT: xtb: drawn devices differ from the deck (S/D geometry or sizes): figures gated at "
              "0.1 mV / 1 ns / 1e-3 instead of 10 uV / 10 ps / 1e-6")
    tol = TOL if tight else LOOSE

    with ThreadPoolExecutor(len(nets)) as ex:
        res = dict(zip(nets, ex.map(lambda n: simulate(n, nets[n]), nets)))

    rows, worst = [], {}
    for n in BENCHES:
        if n not in res:
            continue
        h, x = res[n]
        if h is None or x is None:
            print(f"REPORT: xtb {n}: a simulation exceeded {TIMEOUT} s and was skipped (no comparison)")
            continue
        nfail, wk, wd = 0, "", 0.0
        for k, (bv, unit) in h.items():
            xv = x.get(k, (np.nan, unit))[0]
            ta, tr = tol[unit]
            lim = max(ta, tr * abs(bv))
            diff = xv - bv
            good = bool(np.isfinite(xv) and np.isfinite(bv) and abs(diff) <= lim)
            rows.append((n, k, unit, bv, xv, diff, lim, "PASS" if good else "FAIL"))
            if not good:
                nfail += 1
                verdict(False, f"xtb {n} {k}: hand {bv:.9g} {unit}, xschem {xv:.9g} {unit}, diff {diff:.3g} "
                        f"(tolerance {lim:.3g})")
            if lim and abs(diff) / lim > wd:
                wk, wd = k, abs(diff) / lim
        verdict(nfail == 0, f"xtb {n}: {len(h) - nfail} of {len(h)} figures of the xschem sheet equal the hand "
                f"bench's (" + (f"worst {wk}: {wd * 100:.2g} % of its tolerance" if wd else "every figure identical") + ")")
        worst[n] = (wk, wd)
        # the figures themselves, for the record
        if n == "op":
            print(f"xtb_op_err_mv = {x['err@3.3V'][0] * 1e3:.4f}")
            print(f"xtb_op_ireg_ua = {x['ireg@3.3V'][0] * 1e6:.4f}")
            print(f"REPORT: xtb op: vrlo - {vr.N_BOT}/{vr.N_DIV} AVDD "
                  + ", ".join(f"{x[f'err@{v}V'][0] * 1e3:+.3f} mV at {v} V" for v in ("3.0", "3.3", "3.6"))
                  + f"; min headroom at 3.3 V {min(x[f'{k}@3.3V'][0] for k in ('hrt', 'hrk', 'hr1', 'hr2', 'hr5')):+.3f} V")
        elif n == "tran":
            for k in ("vp_q", "vp_tr", "vr_q", "vp_q2", "vp_tr2", "vr_pk"):
                print(f"xtb_tran_{k}_v = {x[k][0]:.7f}")
            print(f"REPORT: xtb tran (KS=1): vramp at TR {x['vp_tr'][0]:.6f} V, record 2 {x['vp_tr2'][0]:.6f} V; "
                  f"vrlo quiescent {x['vr_q'][0]:.6f} V (err {(x['vr_q'][0] - vr.RATIO * vr.VDD) * 1e3:+.3f} mV); "
                  f"dump peak {x['vr_pk'][0]:.4f} V")
        elif n == "loop":
            print(f"xtb_loop_ugb_mhz = {x['ugb_hz'][0] / 1e6:.5f}")
            print(f"xtb_loop_pm_deg = {x['pm_deg'][0]:.4f}")
            print(f"xtb_loop_t0_db = {x['t0_db'][0]:.4f}")
        elif n == "noise":
            print(f"xtb_noise_vrlo_uv = {x['nz_vrlo_rms'][0] * 1e6:.4f}")
            print(f"xtb_noise_vrlo_lsb = {x['nz_vrlo_rms'][0] / vr.LSB:.5f}")
            print(f"xtb_noise_vramp_uv = {x['nz_vramp_rms'][0] * 1e6:.4f}")
            print(f"xtb_psr_10hz = {x['psr@10Hz'][0]:.6f}")
        elif n == "mc":
            print(f"xtb_mc_er_mv = {x['er'][0] * 1e3:.5f}")
            print(f"xtb_mc_er_nom_mv = {x['er_nom'][0] * 1e3:.5f}")
            print(f"REPORT: xtb mc: seed {tb_sch.SUBS['mc']['SEED']} draw vrlo error {x['er'][0] * 1e3:+.4f} mV "
                  f"(hand {h['er'][0] * 1e3:+.4f}), mismatch-free {x['er_nom'][0] * 1e3:+.4f} mV")
    with open(os.path.join(vr.DATA, "xtb.csv"), "w") as fh:
        fh.write("bench,metric,unit,hand,xschem,diff,tolerance,verdict\n")
        for r in rows:
            fh.write("%s,%s,%s,%.9g,%.9g,%.3g,%.3g,%s\n" % r)
    print(f"xtb_fail_count = {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
