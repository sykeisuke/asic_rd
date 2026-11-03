"""Benches of sample_seq, the sampling sequencer (SPEC.md Q1-Q8).

    python3 bench.py size     fit each PVT cell's gaps to a + b N (N = N_PROBE), pick
                              the smallest N with every gap >= GAP_MIN + GAP_MARGIN,
                              write data/sizing.json and sample_seq.spice
    python3 bench.py typ      the deck at typical: data/typ.csv
    python3 bench.py pvt      45 PVT cells: data/pvt.csv
    python3 bench.py duty     clock duty 30 / 70 % at three cells: data/duty.csv

One bench, tb_seq.spice (a template), rendered into work/<tag>/tb.spice. Each
run is reduced to one CSV row; check-seq.awk judges the rows.
"""
import json
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import size_seq
from seq_common import (BLOCK, CBLOCK, VDD, TCOUNT, NCELLS, GAP_MIN, GAP_MARGIN, N_PROBE, C_ROUTE,
                        PVT, DUTY_CELLS, DUTIES, SPICEINIT)

WORK = os.path.join(BLOCK, "work")
DATA = os.path.join(BLOCK, "data")
JOBS = int(os.environ.get("JOBS", "16"))
R0 = 400e-9
T_STATIC = R0 - 60e-9           # every cell tracking, acq not yet seen
T_IDLE = (220e-9, 330e-9)       # power while tracking, the clock running (gated off)
T_HOLD = (R0 + 250e-9, R0 + 400e-9)


def render(tag, corner, temp, vdd, duty=0.5, netlist=CBLOCK + "/sample_seq.spice"):
    with open(os.path.join(BLOCK, "tb_seq.spice")) as h:
        text = h.read()
    subs = {"VDD": "%g" % vdd, "TEMP": "%g" % temp, "DUTY": "%g" % duty, "NETLIST": netlist,
            "CROUTE": "%.4g" % C_ROUTE}
    for k, v in subs.items():
        text = text.replace("@%s@" % k, v)
    if re.findall(r"@[A-Z_]+@", text):
        raise SystemExit("FAIL: tb_seq.spice: unreplaced tokens")
    if corner != "typical":
        text = re.sub(r"(sm141064\.ngspice) typical\b", r"\1 " + corner, text)
    d = os.path.join(WORK, tag)
    os.makedirs(d, exist_ok=True)
    for f in ("out.csv",):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    with open(os.path.join(d, "tb.spice"), "w") as h:
        h.write(text)
    with open(os.path.join(d, ".spiceinit"), "w") as h:
        h.write(SPICEINIT)
    return d


def ngspice(d, timeout=1800):
    env = dict(os.environ, OMP_NUM_THREADS="1")
    try:
        r = subprocess.run(["ngspice", "-b", "-o", "run.log", "tb.spice"], cwd=d, env=env, timeout=timeout,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return False
    return r.returncode == 0 and os.path.exists(os.path.join(d, "out.csv"))


def load(d):
    p = os.path.join(d, "out.csv")
    with open(p) as h:
        names = [n.lower() for n in h.readline().split()]
    a = np.loadtxt(p, skiprows=1)
    cols = {n: a[:, i] for i, n in enumerate(names)}
    keep = np.concatenate(([True], np.diff(cols["time"]) > 0))
    return {k: v[keep] for k, v in cols.items()}


def crossings(t, v, level, direction):
    s = v - level
    if direction > 0:
        idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    else:
        idx = np.where((s[:-1] > 0) & (s[1:] <= 0))[0]
    return t[idx] + (t[idx + 1] - t[idx]) * (0 - s[idx]) / (s[idx + 1] - s[idx])


def first_after(x, t0):
    x = x[x > t0]
    return float(x[0]) if len(x) else float("nan")


def at(t, v, t0):
    return float(np.interp(t0, t, v))


def reduce(d, vdd):
    w = load(d)
    t = w["time"]
    h = vdd / 2
    row = {}
    t_start = R0 - 60e-9
    clk_r = crossings(t, w["v(clk)"], h, +1)
    nglitch = 0
    static_ok = 1
    g20, g01, gre, ap, sp, s0open, s21 = [], [], [], [], [], [], []
    prev = None
    for k in range(NCELLS):
        s2, s0, s1 = w["v(s2_%d)" % k], w["v(s0_%d)" % k], w["v(s1_%d)" % k]
        s0b = w["v(s0b_%d)" % k]
        # static state before the record: tracking (s2 = s0 = 1, s1 = 0)
        if not (at(t, s2, T_STATIC) > 0.9 * vdd and at(t, s0, T_STATIC) > 0.9 * vdd
                and at(t, s1, T_STATIC) < 0.1 * vdd):
            static_ok = 0
        rk = R0 + k * TCOUNT
        tclk = first_after(clk_r, rk - 5e-9)
        f2 = crossings(t, s2, h, -1); r2 = crossings(t, s2, h, +1)
        f0 = crossings(t, s0, h, -1); r0 = crossings(t, s0, h, +1)
        f1 = crossings(t, s1, h, -1); r1 = crossings(t, s1, h, +1)
        # exactly one fall and one rise of s2 / s0, one rise and one fall of s1, in the record
        for x in (f2, r2, f0, r0, f1, r1):
            nglitch += abs(int(np.sum(x > t_start)) - 1)
        e2 = first_after(f2, t_start); e0 = first_after(f0, t_start); e1 = first_after(r1, t_start)
        x1 = first_after(f1, e1); x2 = first_after(r2, e1); x0 = first_after(r0, e1)
        e0b = first_after(crossings(t, s0b, h, +1), t_start)
        row.update({"t_s2f_%d_ns" % k: (e2 - tclk) * 1e9, "g20_%d_ns" % k: (e0 - e2) * 1e9,
                    "g01_%d_ns" % k: (e1 - e0) * 1e9, "gre_%d_ns" % k: (x0 - x1) * 1e9,
                    "s2close_vs_s1open_%d_ns" % k: (x2 - x1) * 1e9,
                    "g20b_%d_ns" % k: (e0b - e2) * 1e9})
        g20.append(e0 - e2); g01.append(e1 - e0); gre.append(x0 - x1)
        ap.append(e2 - tclk); s0open.append(e0 - tclk); s21.append(e1 - e2)
        if prev is not None:
            sp.append(e2 - prev)
        prev = e2
        row["order_%d" % k] = int(e2 < e0 < e1 and x1 <= x0 + 1e-12 and x1 < x0)
    row["order_ok"] = int(all(row["order_%d" % k] for k in range(NCELLS)))
    row["static_ok"] = static_ok
    row["n_glitch"] = nglitch
    row["g20_min_ns"] = min(g20) * 1e9; row["g20_max_ns"] = max(g20) * 1e9
    row["g01_min_ns"] = min(g01) * 1e9; row["g01_max_ns"] = max(g01) * 1e9
    row["gre_min_ns"] = min(gre) * 1e9
    row["aperture_max_ns"] = max(ap) * 1e9; row["aperture_min_ns"] = min(ap) * 1e9
    row["s0open_max_ns"] = max(s0open) * 1e9
    row["s2s1_max_ns"] = max(s21) * 1e9
    row["spacing_err_max_ns"] = max(abs(x - TCOUNT) for x in sp) * 1e9
    i = -w["i(vdvdd)"]
    trapz = getattr(np, "trapezoid", None) or np.trapz
    for name, (a, b) in (("p_track_uw", T_IDLE), ("p_hold_uw", T_HOLD)):
        m = (t >= a) & (t <= b)
        row[name] = float(trapz(i[m], t[m]) / (t[m][-1] - t[m][0])) * vdd * 1e6
    # energy of one record's entry (acq falls -> last cell settled) and re-entry
    for name, (a, b) in (("e_entry_pj", (R0 - 50e-9, R0 + 250e-9)), ("e_reentry_pj", (R0 + 400e-9, R0 + 700e-9))):
        m = (t >= a) & (t <= b)
        row[name] = float(trapz(i[m], t[m])) * vdd * 1e12
    # Q7 the gated line: no edge of c0 while tracking or holding, one per active cycle
    c0r = crossings(t, w["v(xseq.c0)"], h, +1)
    row["c0_edges_track"] = int(np.sum((c0r > T_IDLE[0]) & (c0r < T_IDLE[1])))
    row["c0_edges_hold"] = int(np.sum((c0r > T_HOLD[0]) & (c0r < T_HOLD[1])))
    row["c0_edges_entry"] = int(np.sum((c0r > R0 - 50e-9) & (c0r < R0 + 300e-9)))
    row["c0_edges_reentry"] = int(np.sum((c0r > R0 + 400e-9) & (c0r < R0 + 750e-9)))
    return row


def case(tag, corner, temp, vdd, duty=0.5, netlist=CBLOCK + "/sample_seq.spice"):
    d = render(tag, corner, temp, vdd, duty, netlist)
    row = {"tag": tag, "corner": corner, "temp": temp, "vdd": vdd, "duty": duty}
    if not ngspice(d):
        row["sim_ok"] = 0
        print("FAIL: ngspice %s did not finish" % tag)
        return row
    row["sim_ok"] = 1
    try:
        row.update(reduce(d, vdd))
    except Exception as e:      # a missing edge is a failed run, judged by the checker
        row["reduce_error"] = str(e).replace(",", ";")
        row["order_ok"] = 0
    return row


def fmt(x):
    if isinstance(x, float):
        return "nan" if math.isnan(x) else "%.6g" % x
    return str(x)


def write_csv(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w") as h:
        h.write(",".join(keys) + "\n")
        for r in rows:
            h.write(",".join(fmt(r.get(k, "nan")) for k in keys) + "\n")


def parallel(fn, items):
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        return list(ex.map(fn, items))


def pvt_tag(prefix, c, t, v):
    return "%s_%s_%d_%s" % (prefix, c, t, ("%g" % v).replace(".", "p"))


# ---------------------------------------------------------------- phases
def size():
    for n in N_PROBE:
        d = os.path.join(WORK, "size_n%d" % n)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "sample_seq.spice"), "w") as h:
            h.write(size_seq.deck(n))
    jobs = [(n, p) for n in N_PROBE for p in PVT]
    rows = parallel(lambda j: case(pvt_tag("size_n%d" % j[0], *j[1]), *j[1],
                                   netlist="%s/work/size_n%d/sample_seq.spice" % (CBLOCK, j[0])), jobs)
    by = {}
    for (n, p), r in zip(jobs, rows):
        by.setdefault(p, {})[n] = r
    na, nb = N_PROBE
    need, fits = 0, []
    target = (GAP_MIN + GAP_MARGIN) * 1e9
    for p, rr in by.items():
        for g in ("g20_min_ns", "g01_min_ns", "gre_min_ns"):
            ya, yb = rr[na].get(g, float("nan")), rr[nb].get(g, float("nan"))
            if math.isnan(ya) or math.isnan(yb):
                raise SystemExit("FAIL: size: %s missing at %s" % (g, p))
            b = (yb - ya) / (nb - na)
            a = ya - b * na
            n_req = math.ceil((target - a) / b)
            need = max(need, n_req)
            fits.append({"corner": p[0], "temp": p[1], "vdd": p[2], "gap": g, "a_ns": a, "b_ns_per_cell": b,
                         "n_req": n_req})
    write_csv(os.path.join(DATA, "size_fit.csv"), fits)
    worst = max(fits, key=lambda f: f["n_req"])
    rec = {"n_stage": need, "delay_cell": "gf180mcu_as_sc_mcu7t3v3__dlybuff_2",
           "gap_min_ns": GAP_MIN * 1e9, "gap_margin_ns": GAP_MARGIN * 1e9, "n_probe": list(N_PROBE),
           "binding": {k: worst[k] for k in ("corner", "temp", "vdd", "gap", "a_ns", "b_ns_per_cell")},
           "b_ns_per_cell_range": [min(f["b_ns_per_cell"] for f in fits), max(f["b_ns_per_cell"] for f in fits)]}
    with open(os.path.join(DATA, "sizing.json"), "w") as h:
        json.dump(rec, h, indent=1)
    size_seq.write(need)
    print("REPORT: size N = %d dlybuff_2 per stage, binding %s/%d/%g %s (a %.3f ns + %.4f ns/cell), "
          "delay cell %.3f-%.3f ns over PVT" % (need, worst["corner"], worst["temp"], worst["vdd"], worst["gap"],
                                                worst["a_ns"], worst["b_ns_per_cell"], *rec["b_ns_per_cell_range"]))


def typ():
    r = case("typ", "typical", 27, VDD)
    write_csv(os.path.join(DATA, "typ.csv"), [r])
    print("REPORT: typ gaps S2->S0 %.3f-%.3f ns, S0->S1 %.3f-%.3f ns, re-entry S1->S0 %.3f ns, sampling "
          "%.3f-%.3f ns after clk, spacing err %.4f ns, power %.2f uW tracking / %.2f uW holding, "
          "%.1f pJ per entry / %.1f pJ per re-entry, gated clock edges %d entry / %d re-entry"
          % (r["g20_min_ns"], r["g20_max_ns"], r["g01_min_ns"], r["g01_max_ns"], r["gre_min_ns"],
             r["aperture_min_ns"], r["aperture_max_ns"], r["spacing_err_max_ns"], r["p_track_uw"], r["p_hold_uw"],
             r["e_entry_pj"], r["e_reentry_pj"], r["c0_edges_entry"], r["c0_edges_reentry"]))


def pvt():
    rows = parallel(lambda p: case(pvt_tag("pvt", *p), *p), PVT)
    write_csv(os.path.join(DATA, "pvt.csv"), rows)


def duty():
    jobs = [(c, du) for c in DUTY_CELLS for du in DUTIES]
    rows = parallel(lambda j: case(pvt_tag("duty%02d" % int(j[1] * 100), *j[0]), *j[0], duty=j[1]), jobs)
    write_csv(os.path.join(DATA, "duty.csv"), rows)


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    {"size": size, "typ": typ, "pvt": pvt, "duty": duty}[sys.argv[1]]()
