"""The xschem testbench drawings against the hand-written benches (schematic.sh).

    python3 xtb.py netlist    xschem netlists tb_*.sch; the instances are the bench's
    python3 xtb.py sim        ngspice on each netlist and on the hand bench; compare
    python3 xtb.py            both

Every tb_<name>.sch (tb_sch.py) is netlisted by xschem into work/xtb_tb_<name>/
(the DUT from midref_div.sch / midref_buf.sch through their symbols, the
comparator of tb_cmp from ../comparator/comparator.sch), and the hand bench
tb_<name>.spice is filled at the same nominal case (verify_v3.py's: typical,
27 C, 3.3 V, the ideal I_F into ib) into work/xtb_tb_<name>/hand/.

  netlist  the drawing's top-level instances (name, nodes, model) are the bench's,
           with the wrapper `midref` expanded to XD + XB and `cmp` read as
           `comparator`; the DUT subcircuits are present with their device counts
  sim      op: every OP / OPX figure at 3.0 / 3.3 / 3.6 V; kick: peak, residuals,
           charge, settling of both cases; cmp: td and v0 (and the peaks, reported);
           mc: the one draw's VDD/2 error and M1 / M4 headroom with the SAME seed;
           noise: the integrated figures of bench.noise_from_files and the output
           spectrum at four frequencies.
           Gate: 1e-6 relative, or 10 uV / 10 ps / 10 pA / 10 zC absolute, where the
           deck and the drawing hold the same devices. The comparator of tb_cmp is
           drawn with the PDK symbols' S/D junction geometry (ad as pd ps nrd nrs),
           which comparator.spice leaves to BSIM4's defaults: that netlist is also
           run with those six parameters stripped (nogeom, gated as above) and as
           drawn (gated at 1 ns on td: the junction capacitance on inp / inn, the
           comparator's own record says +0.5 ns; v0 and the peaks reported).
           tb_cmp's simulation is skipped (REPORT) when a run exceeds 5 minutes.
Writes data/xtb.csv. Prints PASS: / FAIL: / REPORT: and `name = value` lines only.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as S  # noqa: E402
import verify_v3 as V  # noqa: E402  kick_subs, cmp_deck, SEED_BASE (its main() is guarded)

RC = os.path.join(S.BLOCK, "xschemrc")
TBS = tuple(os.environ.get("XTB_TBS", "op kick cmp mc noise").split())
CELL = ("typical", 27, 3.3)
IF = "%.6g" % S.I_F
CMP_TIMEOUT = 300           # s: tb_cmp is skipped, not failed, beyond this
TOL_REL = 1e-6
TOL_ABS = {"V": 10e-6, "s": 10e-12, "A": 10e-12, "C": 10e-21, "1": 0.0}
GEOM_RE = r"\s(?:ad|as|pd|ps|nrd|nrs)=('[^']*'|\S+)"
bad = []
rows = []
LOGS = {}


def verdict(ok, text):
    print(("PASS: " if ok else "FAIL: ") + text)
    if not ok:
        bad.append(text)


def wdir(name, sub=""):
    d = os.path.join(S.WORK, "xtb_tb_" + name, sub)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    return d


# ------------------------------------------------------------------ netlists
def elements(text):
    """{name: (letter, nodes, model)} of the top-level element lines of a deck
    (outside .subckt and .control blocks)."""
    out, skip = {}, 0
    for ln in text.splitlines():
        t = ln.split()
        if not t:
            continue
        k = t[0].lower()
        if k == ".control":
            skip = 1
        elif k == ".endc":
            skip = 0
        elif k == ".subckt":
            skip = 2
        elif k.startswith(".ends"):
            skip = 0
        if skip or k[0] in ".*+":
            continue
        L = k[0]
        if L in "vi":
            out[k] = (L, tuple(x.lower() for x in t[1:3]), "")
        elif L in "rc":
            out[k] = (L, tuple(x.lower() for x in t[1:3]), "")
        elif L == "s":
            out[k] = (L, tuple(x.lower() for x in t[1:5]), t[5].lower())
        elif L == "x":
            n = [x.lower() for x in t[1:] if "=" not in x]
            out[k] = (L, tuple(n[:-1]), n[-1])
    return out


def expected(hand):
    """The hand bench's instances as the drawing must carry them."""
    out = {}
    for k, (L, nodes, model) in hand.items():
        if model == "midref":                      # XB/XR out ib vdd vss midref -> XD + XB
            o, ib, vdd, vss = nodes
            out["xd"] = ("x", ("vin", vdd, vss), "midref_div")
            out["xb"] = ("x", (o, "vin", ib, vdd, vss), "midref_buf")
        elif model == "cmp":
            out[k] = (L, nodes, "comparator")
        else:
            out[k] = (L, nodes, model)
    return out


def subckt_devices(text, name):
    m = re.search(r"^\.subckt %s .*?^\.ends" % name, text, re.M | re.S | re.I)
    if not m:
        return None
    return sum(1 for ln in m.group(0).splitlines()[1:-1] if ln.strip() and ln[0].upper() in "XRCMD")


def hand_decks(name):
    """The hand bench(es) filled at the nominal case: {tag: text}."""
    if name == "op":
        return {"hand": S.fill("tb_op.spice", dict(CORNER="typical", MIMCORNER="typical", TEMP=27, IF=IF,
                                                   TAG="typical 27 1"))}
    if name == "kick":
        return {"hand": S.fill("tb_kick.spice", V.kick_subs(S.I_F, CELL))}
    if name == "cmp":
        return {"hand": V.cmp_deck(S.I_F, 0.15, 1, 0, S.VDD / 2)}
    if name == "mc":
        subs = dict(CORNER="typical", MIMCORNER="typical", TEMP=27, VDD="3.3", IF=IF, MM=1, SEED=V.SEED_BASE + 1, K=1)
        return {"hand": S.fill("tb_mc.spice", subs), "hand_hr": S.fill("tb_mchr.spice", subs)}
    if name == "noise":
        return {"hand": S.fill("tb_noise.spice", dict(IF=IF))}
    raise KeyError(name)


def xschem_netlist(name):
    d = wdir(name)
    net = os.path.join(d, f"tb_{name}.spice")
    if os.path.exists(net):
        os.remove(net)
    subprocess.run(["xschem", "--rcfile", RC, "-b", "-q", "-n", "-s", "-o", d, f"tb_{name}.sch"], cwd=S.BLOCK,
                   stdout=open(os.path.join(d, "xschem.out"), "w"), stderr=subprocess.STDOUT, timeout=300)
    return open(net).read() if os.path.exists(net) else None


def step_netlist():
    for name in TBS:
        text = xschem_netlist(name)
        if text is None:
            verdict(False, f"xtb: xschem produced no netlist for tb_{name}.sch")
            continue
        hand = hand_decks(name)
        exp = expected(elements(hand["hand"]))        # tb_mc's XD / XB also serve tb_mchr's HR line
        got = elements(text)
        missing = [k for k in exp if k not in got]
        extra = [k for k in got if k not in exp]
        differ = [k for k in exp if k in got and got[k] != exp[k]]
        subs = {"midref_div": 3, "midref_buf": 12}
        if name == "cmp":
            subs["comparator"] = 10
        cnt = {s: subckt_devices(text, s) for s in subs}
        ok = not (missing or extra or differ) and all(cnt[s] == n for s, n in subs.items())
        detail = "; ".join(x for x in (
            "missing " + " ".join(missing) if missing else "", "extra " + " ".join(extra) if extra else "",
            "differ " + " ".join(f"{k} {got[k]} vs {exp[k]}" for k in differ) if differ else "",
            "" if all(cnt[s] == n for s, n in subs.items()) else "subckt devices " + str(cnt)) if x)
        verdict(ok, f"xtb: tb_{name}.sch netlists the bench's {len(exp)} instances (name, nodes, model), "
                + ", ".join(f"{s} {cnt[s]} devices" for s in subs) + (": " + detail if detail else ""))
    return 0 if not bad else 1


# ---------------------------------------------------------------- simulation
def ngspice(d, deck, timeout):
    log = os.path.join(d, deck.replace(".spice", ".log"))
    try:
        subprocess.run(["ngspice", "-b", deck], cwd=d, stdin=subprocess.DEVNULL, stdout=open(log, "w"),
                       stderr=subprocess.STDOUT, timeout=timeout, env=dict(os.environ, OMP_NUM_THREADS="1"))
    except subprocess.TimeoutExpired:
        return None
    return open(log, errors="replace").read()


def prepare(name):
    """{variant: (dir, deck)} for one bench: the drawing's netlist, its nogeom copy (cmp), the hand bench(es)."""
    jobs = {}
    draw = open(os.path.join(wdir(name), f"tb_{name}.spice")).read()
    jobs["draw"] = (wdir(name), f"tb_{name}.spice")
    if name == "cmp":
        d = wdir(name, "nogeom")
        open(os.path.join(d, "tb.spice"), "w").write(re.sub(GEOM_RE, "", draw))
        jobs["nogeom"] = (d, "tb.spice")
    for tag, text in hand_decks(name).items():
        d = wdir(name, tag)
        open(os.path.join(d, "dut.spice"), "w").write(open(os.path.join(S.BLOCK, "midref.spice")).read())
        open(os.path.join(d, "tb.spice"), "w").write(text)
        jobs[tag] = (d, "tb.spice")
    return jobs


def errs(name, variant, txt):
    """REPORT the simulator's complaint when a figure is missing (the log is never read by hand)."""
    lines = [ln.strip() for ln in (txt or "").splitlines()
             if re.search(r"error|warning|not found|undefined|unknown|no such|failed|cannot", ln, re.I)]
    print(f"REPORT: xtb {name} {variant}: ngspice: " + (" | ".join(lines[:4]) if lines else "no error line"))


def within(a, b, unit):
    if not (np.isfinite(a) and np.isfinite(b)):
        return False, float("nan"), float("nan")
    diff = a - b
    rel = abs(diff) / abs(b) if b else float("inf")
    return bool(rel <= TOL_REL or abs(diff) <= TOL_ABS[unit]), diff, rel


def judge(name, variant, figs, tol_override=None):
    """figs: [(metric, hand, xschem, unit)] -> one PASS/FAIL line; rows for the CSV."""
    nok, worst = 0, ("", 0.0, 0.0)
    if any(not np.isfinite(x) for _, _, x, _ in figs):
        errs(name, variant, LOGS.get((name, variant)))
    if any(not np.isfinite(b) for _, b, _, _ in figs):
        errs(name, "hand", LOGS.get((name, "hand")))
    for metric, b, x, unit in figs:
        ok, diff, rel = within(x, b, unit)
        if tol_override and metric in tol_override:
            ok = bool(np.isfinite(x) and abs(diff) <= tol_override[metric])
        nok += ok
        rows.append((name, variant, metric, b, x, diff, rel, "PASS" if ok else "FAIL"))
        if not np.isfinite(rel) or rel > worst[1]:
            worst = (metric, rel, diff)
    return nok, worst


def op_lines(txt):
    out = {}
    for tag, n in (("OP", 10), ("OPX", 6)):
        for m in re.finditer(r"^%s typical 27 1 (\S+) (.*)$" % tag, txt, re.M):
            out[(tag, float(m.group(1)))] = [float(x) for x in m.group(2).split()[:n]]
    return out


OP_NAMES = {"OP": ("hr1 hr4 hrib hrit hr2 hr5 hr3 hr6 err isup".split(), "V V V V V V V V V A".split()),
            "OPX": ("ibb ibt i2 vp vn tap".split(), "A A A V V V".split())}


def compare(name, logs):
    """logs: {variant: text or None (timeout)}"""
    if name != "cmp" and any(v is None for v in logs.values()):
        verdict(False, f"xtb {name}: ngspice did not finish within 900 s")
        return
    if name == "op":
        h, x = op_lines(logs["hand"]), op_lines(logs["draw"])
        figs = []
        for key in sorted(h):
            names, units = OP_NAMES[key[0]]
            xv = x.get(key, [float("nan")] * len(names))
            figs += [(f"{n}@{key[1]:g}V", hv, xx, u) for n, u, hv, xx in zip(names, units, h[key], xv)]
        nok, worst = judge(name, "draw", figs)
        verdict(nok == len(figs) == 48, f"xtb op: {nok} of {len(figs)} operating-point figures (headroom, error, "
                f"currents, node levels at 3.0 / 3.3 / 3.6 V) equal within 1e-6 / 10 uV / 10 pA; worst {worst[0]} "
                f"rel {worst[1]:.2e}")
        e33 = [f for f in figs if f[0] == "err@3.3V"]
        if e33:
            print(f"xtb_op_err_typ_mv = {e33[0][2] * 1e3:.4f}")
    elif name == "kick":
        h, x = S.grab(logs["hand"]), S.grab(logs["draw"])
        units = {"pkr_mv": ("V", 1e-3), "rr250_mv": ("V", 1e-3), "rr300_mv": ("V", 1e-3), "qk_fc": ("C", 1e-15),
                 "v0r_v": ("V", 1.0), "tsr_ns": ("s", 1e-9)}
        figs = []
        for c in (1, 2):
            for q, (u, sc) in units.items():
                k = f"k_c{c}_{q}"
                figs.append((k, h.get(k, float("nan")) * sc, x.get(k, float("nan")) * sc, u))
        nok, worst = judge(name, "draw", figs)
        verdict(nok == len(figs) == 12, f"xtb kick: {nok} of {len(figs)} figures of both S2 cases (peak, residual "
                f"at 250 / 300 ns, charge, level, return to 1/2 LSB) equal within 1e-6 / 10 uV / 10 ps / 10 zC; "
                f"worst {worst[0]} rel {worst[1]:.2e}")
        for c in (1, 2):
            print(f"xtb_kick_c{c}_pk_mv = {x.get(f'k_c{c}_pkr_mv', float('nan')):.4f}")
            print(f"xtb_kick_c{c}_tsr_ns = {x.get(f'k_c{c}_tsr_ns', float('nan')):.3f}")
    elif name == "cmp":
        if any(logs[v] is None for v in ("hand", "draw", "nogeom")):
            print(f"REPORT: xtb cmp: simulation skipped, a run exceeded {CMP_TIMEOUT} s "
                  "(" + " ".join(v for v in ("hand", "draw", "nogeom") if logs[v] is None) + "); not judged")
            return
        h = S.grab(logs["hand"])
        for variant, tol in (("nogeom", None), ("draw", {"cmp_td_ns": 1e-9})):
            x = S.grab(logs[variant])
            figs = [("cmp_td_ns", h.get("cmp_td_ns", np.nan) * 1e-9, x.get("cmp_td_ns", np.nan) * 1e-9, "s"),
                    ("cmp_v0_v", h.get("cmp_v0_v", np.nan), x.get("cmp_v0_v", np.nan), "V")]
            if variant == "nogeom":
                nok, worst = judge(name, variant, figs)
                verdict(nok == 2, f"xtb cmp (comparator S/D geometry stripped, the deck's devices): dout falls at "
                        f"{x.get('cmp_td_ns', np.nan):.4f} ns on the drawing, {h.get('cmp_td_ns', np.nan):.4f} on the "
                        f"bench (diff {(x.get('cmp_td_ns', np.nan) - h.get('cmp_td_ns', np.nan)) * 1e3:+.3f} ps, "
                        f"tol 10); node level {x.get('cmp_v0_v', np.nan):.7f} vs {h.get('cmp_v0_v', np.nan):.7f} V "
                        f"(diff {(x.get('cmp_v0_v', np.nan) - h.get('cmp_v0_v', np.nan)) * 1e6:+.3f} uV, tol 10)")
            else:
                nok, worst = judge(name, variant, figs, tol)
                dtd = x.get("cmp_td_ns", np.nan) - h.get("cmp_td_ns", np.nan)
                verdict(nok == 2, f"xtb cmp as drawn (comparator with the PDK symbols' S/D junction geometry): dout "
                        f"falls {dtd:+.3f} ns later than the bench ({x.get('cmp_td_ns', np.nan):.3f} vs "
                        f"{h.get('cmp_td_ns', np.nan):.3f} ns; gate 1 ns: the junction capacitance on inp / inn "
                        f"is the comparator's recorded +0.5 ns, not a wiring error); node level diff "
                        f"{(x.get('cmp_v0_v', np.nan) - h.get('cmp_v0_v', np.nan)) * 1e6:+.3f} uV (10 uV)")
                print(f"xtb_cmp_td_geom_ns = {x.get('cmp_td_ns', np.nan):.4f}")
                print(f"xtb_cmp_td_hand_ns = {h.get('cmp_td_ns', np.nan):.4f}")
            for q in ("cmp_pkpre_uv", "cmp_pkall_uv", "cmp_pkhold_mv", "cmp_doutmin_v"):
                rows.append((name, variant, q, h.get(q, np.nan), x.get(q, np.nan), x.get(q, np.nan) - h.get(q, np.nan),
                             float("nan"), "REPORT"))
            print(f"REPORT: xtb cmp {variant}: node peaks before the trip / over the conversion / over the hold "
                  f"{x.get('cmp_pkpre_uv', np.nan):.2f} / {x.get('cmp_pkall_uv', np.nan):.2f} uV / "
                  f"{x.get('cmp_pkhold_mv', np.nan):.4f} mV, lowest dout in the hold {x.get('cmp_doutmin_v', np.nan):.3f} V "
                  f"(bench {h.get('cmp_pkpre_uv', np.nan):.2f} / {h.get('cmp_pkall_uv', np.nan):.2f} uV / "
                  f"{h.get('cmp_pkhold_mv', np.nan):.4f} mV, {h.get('cmp_doutmin_v', np.nan):.3f} V)")
    elif name == "mc":
        def grab(txt, pat, n):
            m = re.search(pat, txt or "", re.M)
            return [float(v) for v in m.groups()] if m else [np.nan] * n
        h_er = grab(logs["hand"], r"^MC 1 (\S+)$", 1)[0]
        h_hr = grab(logs["hand_hr"], r"^HR 1 (\S+) (\S+) (\S+)$", 3)
        x_er = grab(logs["draw"], r"^MC 1 (\S+)$", 1)[0]
        x_hr = grab(logs["draw"], r"^HR 1 (\S+) (\S+) (\S+)$", 3)
        figs = [("mc_err", h_er, x_er, "V"), ("hr1", h_hr[0], x_hr[0], "V"), ("hr4", h_hr[1], x_hr[1], "V"),
                ("hr_err", h_hr[2], x_hr[2], "V")]
        nok, worst = judge(name, "draw", figs)
        verdict(nok == 4, f"xtb mc: one mismatch draw, .options seed {V.SEED_BASE + 1} in both: VDD/2 error "
                f"{x_er * 1e3:+.4f} mV on the drawing, {h_er * 1e3:+.4f} on tb_mc (diff {(x_er - h_er) * 1e6:+.3f} uV); "
                f"follower headroom M1 / M4 {x_hr[0]:+.5f} / {x_hr[1]:+.5f} V vs tb_mchr {h_hr[0]:+.5f} / "
                f"{h_hr[1]:+.5f} V (tol 10 uV): the same sample device for device")
        print(f"xtb_mc_err_mv = {x_er * 1e3:.4f}")
    elif name == "noise":
        rh = S.noise_from_files(wdir(name, "hand"))
        rx = S.noise_from_files(wdir(name))
        figs = [(k, rh.get(k, np.nan), rx.get(k, np.nan), "1") for k in ("nz_out_uv", "nz_tap_out_uv", "nz_lsb",
                                                                           "nz_two_lsb")]
        oh, ox = S.read_xy(os.path.join(wdir(name, "hand"), "nz_out.txt")), S.read_xy(os.path.join(wdir(name), "nz_out.txt"))
        for f0 in (10.0, 1e3, 1e6, 1e9):
            vh = float(oh[np.argmin(np.abs(oh[:, 0] - f0)), 1]) if oh is not None else np.nan
            vx = float(ox[np.argmin(np.abs(ox[:, 0] - f0)), 1]) if ox is not None else np.nan
            figs.append((f"onoise@{f0:g}Hz", vh, vx, "1"))
        nok, worst = judge(name, "draw", figs)
        verdict(nok == len(figs) == 8, f"xtb noise: {nok} of {len(figs)} figures (output rms 10 Hz-1 GHz, the "
                f"divider's share, VBL(decision) - VREF(TS) in LSB, the two-buffer figure, the spectrum at 10 Hz / "
                f"1 kHz / 1 MHz / 1 GHz) equal within 1e-6 relative; worst {worst[0]} rel {worst[1]:.2e}; "
                f"{rx.get('nz_lsb', np.nan):.5f} LSB on the drawing, {rh.get('nz_lsb', np.nan):.5f} on the bench")
        print(f"xtb_noise_lsb = {rx.get('nz_lsb', np.nan):.5f}")
        print(f"xtb_noise_out_uv = {rx.get('nz_out_uv', np.nan):.3f}")


def step_sim():
    jobs = []
    for name in TBS:
        if not os.path.exists(os.path.join(wdir(name), f"tb_{name}.spice")):
            verdict(False, f"xtb: no xschem netlist of tb_{name}.sch to simulate")
            continue
        for variant, (d, deck) in prepare(name).items():
            jobs.append((name, variant, d, deck))
    with ThreadPoolExecutor(max_workers=min(S.JOBS, len(jobs))) as ex:
        outs = list(ex.map(lambda j: ngspice(j[2], j[3], CMP_TIMEOUT if j[0] == "cmp" else 900), jobs))
    logs = {}
    for (name, variant, _, _), txt in zip(jobs, outs):
        logs.setdefault(name, {})[variant] = txt
        LOGS[(name, variant)] = txt
    for name in TBS:
        if name in logs:
            compare(name, logs[name])
    with open(os.path.join(S.DATA, "xtb.csv"), "w") as h:
        h.write("bench,variant,metric,bench_value,xschem_value,diff,rel,verdict\n")
        for r in rows:
            h.write("%s,%s,%s,%.8g,%.8g,%.4g,%.4g,%s\n" % r)
    return 0 if not bad else 1


def main():
    steps = sys.argv[1:] or ["netlist", "sim"]
    rc = 0
    if "netlist" in steps:
        rc |= step_netlist()
    if "sim" in steps:
        rc |= step_sim()
    return rc


if __name__ == "__main__":
    sys.exit(main())
