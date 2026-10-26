"""Benches of latch, the standard-cell clocked latch after comparator (SPEC.md).

    python3 bench.py explore    drive bench on every candidate of scff_variants.spice
                                at three cells: data/explore.csv
    python3 bench.py drive      the chosen latch, three cells: data/drive.csv
    python3 bench.py slew       the drive bench over clock edge times: data/slew.csv
    python3 bench.py aperture   d's crossing swept across the sampling edge, with a
                                bisection onto the decision boundary: data/aperture.csv
    python3 bench.py kick       comparator + latch on the cell's charge path, clock
                                running vs stopped; tspc_dff and 10 fF as references:
                                data/kick.csv, data/kick_runs.csv

The structure, timelines and reductions are ../latch_bkp/cmp_tspc/bench.py's (read, not
imported: that block is not touched), so the two latches are measured the same
way. Every deck is a template (tokens @NAME@) rendered into work/<tag>/tb.spice;
the deck writes out.csv (wrdata) or .meas lines, which this script reduces to
one CSV row per run. The check-*.awk scripts judge the rows.
"""
import json
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
DATA = os.path.join(BLOCK, "data")
JOBS = int(os.environ.get("JOBS", "16"))
CBLOCK = "/foss/designs/mixed_signal/latch"

VDD = 3.3
TCOUNT = 50e-9
LSB = 1.5 / 256
CQ = 50e-15                     # the load q drives (user requirement)
TDF_SLOW = 10.4e-9 / 0.8        # d 0-100 % edge: comparator's slowest dout fall over PVT,
                                # 10.4 ns 10-90 % [M] (runs/comparator-updt-v3-pvt/20261007T024232Z)
TDF_FAST = 1.0e-9 / 0.8
T1090_CLK_NOM = 0.5e-9          # nominal clock 10-90 % edge at the latch [A]
SLEW_LIST = [0.2e-9, 0.5e-9, 1e-9, 2e-9, 3e-9, 4e-9, 6e-9, 8e-9]
NETLIST = os.environ.get("NETLIST", CBLOCK + "/latch.spice")
SUBCKT = os.environ.get("SUBCKT", "latch")
VARIANTS = ["scff_bare", "scff_b2", "scff_b4"]
SPICEINIT = "set num_threads=1\nset ngbehavior=hsa\nset ng_nomodcheck\nset enable_noisy_r\n"


# ------------------------------------------------------------------ helpers
def render(template, tag, subs, corner="typical"):
    with open(os.path.join(BLOCK, template), encoding="utf-8") as h:
        text = h.read()
    for k, v in subs.items():
        text = text.replace("@%s@" % k, str(v))
    left = re.findall(r"@[A-Z_]+@", text)
    if left:
        raise SystemExit("FAIL: %s: unreplaced tokens %s" % (template, sorted(set(left))))
    if corner != "typical":
        text = re.sub(r"(sm141064\.ngspice) typical\b", r"\1 " + corner, text)
    d = os.path.join(WORK, tag)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "out.csv")
    if os.path.exists(p):
        os.remove(p)
    with open(os.path.join(d, "tb.spice"), "w", encoding="utf-8") as h:
        h.write(text)
    # one OpenMP thread per ngspice: the image's spinit sets 8, and JOBS
    # processes x 8 spinning threads stall the shared host
    with open(os.path.join(d, ".spiceinit"), "w") as h:
        h.write(SPICEINIT)
    return d


def ngspice(d, timeout=3600, expect="out.csv"):
    env = dict(os.environ, OMP_NUM_THREADS="1")
    try:
        r = subprocess.run(["ngspice", "-b", "-o", "run.log", "tb.spice"], cwd=d, env=env, timeout=timeout,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print("FAIL: ngspice timed out after %d s in %s" % (timeout, os.path.relpath(d, BLOCK)))
        return False
    return r.returncode == 0 and (expect is None or os.path.exists(os.path.join(d, expect)))


def load(d):
    p = os.path.join(d, "out.csv")
    with open(p) as h:
        names = h.readline().split()
    a = np.loadtxt(p, skiprows=1)
    cols = {n.lower(): a[:, i] for i, n in enumerate(names)}
    keep = np.concatenate(([True], np.diff(cols["time"]) > 0))
    return {k: v[keep] for k, v in cols.items()}


def crossings(t, v, level, direction):
    s = v - level
    if direction > 0:
        idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    else:
        idx = np.where((s[:-1] > 0) & (s[1:] <= 0))[0]
    return t[idx] + (t[idx + 1] - t[idx]) * (0 - s[idx]) / (s[idx + 1] - s[idx])


def window(t, v, t0, t1):
    return v[(t >= t0) & (t <= t1)]


def first_after(x, t0):
    x = x[x > t0]
    return float(x[0]) if len(x) else float("nan")


trapz = getattr(np, "trapezoid", None) or np.trapz


def integral(t, v, t0, t1):
    m = (t >= t0) & (t <= t1)
    return float(trapz(v[m], t[m]))


def fmt(x):
    if isinstance(x, float):
        return "nan" if math.isnan(x) else "%.6g" % x
    return str(x)


def write_csv(path, rows):
    keys = list(rows[0].keys())
    for r in rows[1:]:
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


# ------------------------------------------------------------ drive bench
D_EVENTS = [(412.5e-9, -1, "f1"), (587.5e-9, +1, "r0"), (787.5e-9, -1, "f0"), (962.5e-9, +1, "r1")]
GLITCH = 1.0                    # q may move at most 1.0 V from its rail in a static state [U]
CORNER_CELLS = [("typ", "typical", 27, 3.3), ("ss0", "ss", 0, 3.0), ("ff85", "ff", 85, 3.6),
                ("ss85", "ss", 85, 3.0)]


def drive_case(tag, t1090_clk=T1090_CLK_NOM, tdf=TDF_SLOW, corner="typical", temp=27, vdd=VDD, cq=CQ,
               netlist=NETLIST, subckt=SUBCKT):
    d = render("tb_drive.spice", tag, {"TCE": "%.6e" % (t1090_clk / 0.8), "TDF": "%.6e" % tdf, "CQ": "%.6e" % cq,
                                         "VDD": "%g" % vdd, "TEMP": "%g" % temp, "NETLIST": netlist,
                                         "SUBCKT": subckt}, corner)
    row = {"tag": tag, "subckt": subckt, "corner": corner, "temp": temp, "vdd": vdd,
           "clk_t1090_ns": t1090_clk * 1e9, "d_t1090_ns": tdf * 0.8e9, "cq_ff": cq * 1e15}
    if not ngspice(d):
        row["ok"] = 0
        row["pass"] = 0
        return row
    row["ok"] = 1
    row.update(drive_measure(load(d), t1090_clk, tdf, vdd))
    return row


def drive_measure(w, t1090_clk, tdf, vdd):
    row = {}
    tce = t1090_clk / 0.8
    t, clk, q, dd = w["time"], w["v(clk)"], w["v(q)"], w["v(d)"]
    half = vdd / 2
    tf = crossings(t, clk, half, -1)
    qx = sorted([(x, -1) for x in crossings(t, q, half, -1) if x > 100e-9] +
                [(x, +1) for x in crossings(t, q, half, +1) if x > 100e-9])
    row["n_qedges"] = len(qx)
    good, edges, tq = 1, [], []
    for tmid, sgn, lab in D_EVENTS:
        td = first_after(crossings(t, dd, half, sgn), tmid - tdf)
        te = first_after(tf, td)                       # the sampling edge that must see the move
        edges.append(te)
        hit = [x for x, s in qx if s == sgn and te - TCOUNT < x < te + TCOUNT]
        tqi = hit[0] if hit else float("nan")
        tq.append(tqi)
        row["tcq_%s_ns" % lab] = (tqi - te) * 1e9      # negative = q moved before its edge (a race)
        if not (te < tqi < te + TCOUNT / 2):
            good = 0
    row["edges_ok"] = int(good and len(qx) == len(D_EVENTS))
    for lab, sgn in (("f1", -1), ("f0", -1), ("r0", +1), ("r1", +1)):
        k = [e[2] for e in D_EVENTS].index(lab)
        tqi = tq[k]
        a = crossings(t, q, (0.9 if sgn < 0 else 0.1) * vdd, sgn)
        b = crossings(t, q, (0.1 if sgn < 0 else 0.9) * vdd, sgn)
        a = a[a <= tqi]
        row["q_edge_%s_ns" % lab] = (first_after(b, tqi) - (a[-1] if len(a) else float("nan"))) * 1e9
    after = [x + 5e-9 if x == x else e + TCOUNT / 2 for x, e in zip(tq, edges)]
    highs = [(100e-9, edges[0] - tce), (after[1], edges[2] - tce), (after[3], t[-1])]
    lows = [(after[0], edges[1] - tce), (after[2], edges[3] - tce)]
    row["q_min_high"] = float(min(window(t, q, a, b).min() for a, b in highs))
    row["q_max_low"] = float(max(window(t, q, a, b).max() for a, b in lows))
    row["pass"] = int(row["edges_ok"] and row["q_min_high"] >= vdd - GLITCH and row["q_max_low"] <= GLITCH)
    # input capacitance seen by dout: charge drawn from the d source over each of its moves
    cins = [abs(integral(t, w["i(vd)"], tm - tdf / 2 - 0.5e-9, tm + tdf / 2 + 2e-9)) / vdd * 1e15
            for tm, _, _ in D_EVENTS]
    for (_, _, lab), c in zip(D_EVENTS, cins):
        row["cin_%s_ff" % lab] = c
    row["cin_max_ff"] = max(cins)
    # supply energy per clock cycle in the two static states (whole periods, q static)
    idd = -w["i(vdvdd)"]
    row["e_cyc_dhigh_fj"] = vdd * integral(t, idd, 100e-9, 400e-9) / 6 * 1e15
    row["e_cyc_dlow_fj"] = vdd * integral(t, idd, 450e-9, 550e-9) / 2 * 1e15
    row["p_dhigh_uw"] = row["e_cyc_dhigh_fj"] / TCOUNT * 1e-9
    row["p_dlow_uw"] = row["e_cyc_dlow_fj"] / TCOUNT * 1e-9
    # leakage: the supply current in the quiet middle of a clock-high phase, q high
    m = (t > 300e-9 - 20e-9) & (t < 300e-9 - 5e-9)
    row["i_leak_na"] = float(np.mean(idd[m])) * 1e9
    # energy of one q fall (d falls at 412.5 ns -> q falls at 425 ns; one period
    # holding it, less a static cycle with d low)
    row["e_qfall_fj"] = vdd * integral(t, idd, 400e-9, 450e-9) * 1e15 - row["e_cyc_dlow_fj"]
    return row


def cmd_explore():
    """Every candidate of scff_variants.spice through the drive bench at the
    corner cells, and through the clock-edge sweep at typical."""
    nl = CBLOCK + "/scff_variants.spice"
    jobs = [(v, c) for v in VARIANTS for c in CORNER_CELLS]
    rows = parallel(lambda j: drive_case("x_%s_%s" % (j[0], j[1][0]), corner=j[1][1], temp=j[1][2], vdd=j[1][3],
                                         netlist=nl, subckt=j[0]), jobs)
    write_csv(os.path.join(DATA, "explore.csv"), rows)
    for r in rows:
        print("explore %-10s %-5s pass %s tcq %.2f ns, q fall %.2f ns, cin %.2f fF, %.2f uW (d high) %.2f uW (d low), "
              "q-fall energy %.0f fJ" % (r["subckt"], r["tag"].split("_")[-1], r.get("pass"), r.get("tcq_f1_ns", float("nan")),
                                         r.get("q_edge_f1_ns", float("nan")), r.get("cin_max_ff", float("nan")),
                                         r.get("p_dhigh_uw", float("nan")), r.get("p_dlow_uw", float("nan")),
                                         r.get("e_qfall_fj", float("nan"))))


def cmd_drive():
    rows = parallel(lambda c: drive_case("drive_" + c[0], corner=c[1], temp=c[2], vdd=c[3]), CORNER_CELLS)
    # the TSPC on the same bench, as the reference for power and drive (read by path)
    ref = parallel(lambda c: drive_case("tspc_" + c[0], corner=c[1], temp=c[2], vdd=c[3],
                                        netlist="/foss/designs/mixed_signal/latch/ref/tspc_dff.spice",
                                        subckt="tspc_dff"), CORNER_CELLS)
    write_csv(os.path.join(DATA, "drive.csv"), rows)
    write_csv(os.path.join(DATA, "drive_tspc.csv"), ref)
    for r in rows + ref:
        print("drive %s: %s" % (r["tag"], json.dumps({k: fmt(v) for k, v in r.items()})))


def max_passing(rows):
    out = {}
    for r in rows:
        out.setdefault((r["corner"], r["temp"], r["vdd"]), []).append((r["clk_t1090_ns"], r["pass"]))
    res = {}
    for k, v in out.items():
        best = 0.0
        for s, p in sorted(v):
            if not p:
                break
            best = s
        res[k] = best
    return res


def cmd_slew():
    jobs = [(c, s) for c in CORNER_CELLS for s in SLEW_LIST]
    rows = parallel(lambda j: drive_case("slew_%s_%03d" % (j[0][0], round(j[1] * 1e10)), t1090_clk=j[1],
                                         corner=j[0][1], temp=j[0][2], vdd=j[0][3]), jobs)
    write_csv(os.path.join(DATA, "slew.csv"), rows)
    for k, v in max_passing(rows).items():
        print("slew limit %s/%s C/%s V: every clock edge up to %.2f ns 10-90 passes" % (k[0], k[1], k[2], v))


# ---------------------------------------------------------- aperture bench
AP_TE = 125e-9
AP_CQ_MAX = 20e-9


def aperture_case(dt, tag, tdf=TDF_SLOW, t1090_clk=T1090_CLK_NOM, corner="typical", temp=27, vdd=VDD):
    d = render("tb_aperture.spice", tag, {"DT": "%.15e" % dt, "TCE": "%.6e" % (t1090_clk / 0.8),
                                            "TDF": "%.6e" % tdf, "CQ": "%.6e" % CQ, "VDD": "%g" % vdd,
                                            "TEMP": "%g" % temp, "NETLIST": NETLIST, "SUBCKT": SUBCKT}, corner)
    row = {"tag": tag, "corner": corner, "temp": temp, "vdd": vdd, "dt_s": dt, "d_t1090_ns": tdf * 0.8e9}
    if not ngspice(d):
        row["ok"] = 0
        row["pass"] = 0
        return row
    row["ok"] = 1
    row.update(aperture_measure(load(d), vdd))
    os.remove(os.path.join(d, "out.csv"))
    return row


def aperture_measure(w, vdd=VDD):
    row = {}
    t, q = w["time"], w["v(q)"]
    half = vdd / 2
    fall = crossings(t, q, half, -1)
    rise = crossings(t, q, half, +1)
    fall, rise = fall[fall > 100e-9], rise[rise > 100e-9]
    dips = crossings(t, q, vdd - GLITCH, -1)
    dips = dips[dips > 100e-9]
    row["n_fall"], row["n_rise"], row["n_dip"] = len(fall), len(rise), len(dips)
    tq = float(fall[0]) if len(fall) else float("nan")
    edge = AP_TE if tq < AP_TE + TCOUNT else AP_TE + TCOUNT
    row["edge"] = 0 if edge == AP_TE else 1
    row["tcq_ns"] = (tq - edge) * 1e9
    f90 = crossings(t, q, 0.9 * vdd, -1)
    f90 = f90[(f90 > 100e-9) & (f90 <= tq)]
    row["q_fall_ns"] = (first_after(crossings(t, q, 0.1 * vdd, -1), tq) - (f90[-1] if len(f90) else float("nan"))) * 1e9
    t90 = f90[-1] if len(f90) else tq
    pre = window(t, q, 110e-9, t90)
    row["q_min_pre"] = float(pre.min()) if len(pre) else float("nan")
    # q after its fall: it must stay low (a rise back would be a second capture edge)
    post = window(t, q, tq + 2e-9, t[-1]) if tq == tq else np.array([])
    row["q_max_post"] = float(post.max()) if len(post) else float("nan")
    row["pass"] = int(row["n_fall"] == 1 and row["n_rise"] == 0 and 0 < tq - edge <= AP_CQ_MAX)
    return row


def boundary_scan(tdf, lab, **kw):
    """Coarse grid, bisection onto the decision boundary to 1 fs, then offsets
    1e-10 .. 1e-15 s either side. Returns the rows and a summary."""
    grid = [x * 1e-9 for x in np.arange(-4.0, 4.0001, 0.25)]
    rows = parallel(lambda x: aperture_case(x, "%s_%+.3f" % (lab, x * 1e9), tdf, **kw), grid)
    dec = [(r["dt_s"], r.get("edge")) for r in rows if r["ok"]]
    lo = max([x for x, e in dec if e == 0], default=None)
    hi = min([x for x, e in dec if e == 1], default=None)
    summ = {"n_runs": len(rows), "dt0_ps": float("nan"), "tau_ps": float("nan"),
            "boundary": int(lo is not None and hi is not None and lo < hi)}
    if not summ["boundary"]:
        return dict(summ, rows=rows)
    k = 0
    while hi - lo > 1e-15 and k < 60:
        mid = 0.5 * (lo + hi)
        r = aperture_case(mid, lab + "_bis", tdf, **kw)
        if not r["ok"]:
            break
        if r["edge"] == 0:
            lo = mid
        else:
            hi = mid
        k += 1
    dt0 = 0.5 * (lo + hi)
    offs = [s * 10.0 ** -e for e in range(10, 16) for s in (-1, 1)]
    near = parallel(lambda o: aperture_case(dt0 + o, "%s_n%+.0e" % (lab, o), tdf, **kw), offs)
    for r, o in zip(near, offs):
        r["offset_s"] = o
    rows += near
    tn = [(abs(r["offset_s"]), r["tcq_ns"]) for r in near if r["ok"] and r["tcq_ns"] == r["tcq_ns"]]
    tau = -np.polyfit(np.log([a for a, _ in tn]), np.array([b for _, b in tn]) * 1e-9, 1)[0] if len(tn) >= 4 \
        else float("nan")
    summ.update({"n_runs": len(rows), "dt0_ps": dt0 * 1e12, "tau_ps": tau * 1e12,
                 "tcq_max_ns": max(r["tcq_ns"] for r in rows if r["ok"]),
                 "fall_max_ns": max(r["q_fall_ns"] for r in rows if r["ok"])})
    return dict(summ, rows=rows)


AP_CELLS = [("typ", "typical", 27, 3.3), ("ss0", "ss", 0, 3.0), ("ff85", "ff", 85, 3.6)]


def cmd_aperture():
    rows = []
    for cl in AP_CELLS:
        for tdf, lab in ((TDF_SLOW, "slow"), (TDF_FAST, "fast")):
            if cl[0] != "typ" and lab == "fast":
                continue
            s = boundary_scan(tdf, "ap_%s_%s" % (cl[0], lab), corner=cl[1], temp=cl[2], vdd=cl[3])
            rows += s.pop("rows")
            if not s["boundary"]:
                print("FAIL: aperture (%s, %s d): no clean boundary between the two edges on the coarse grid" % (cl[0], lab))
            for k, v in s.items():
                print("aperture_%s_%s_%s = %s" % (cl[0], lab, k, fmt(float(v))))
    write_csv(os.path.join(DATA, "aperture.csv"), rows)


# -------------------------------------------------------------- kick bench
KICK_CODES = [4, 64, 128, 250]
KICK_PHASES = [i / 8 for i in range(8)]
VR_LO, TR = 0.5, 400e-9
MEAS = re.compile(r"^\s*([a-z_0-9]+)\s*=\s*([-+0-9.eE]+)")


def kick_case(code, f, clk_on, load_kind="scff", t1090_clk=T1090_CLK_NOM):
    vin = VR_LO + (code + f) * LSB
    tce = t1090_clk / 0.8
    if clk_on:
        clk = "PULSE(0 %g %.6e %.6e %.6e %.6e %.6e)" % (VDD, TCOUNT - tce / 2, tce, tce, TCOUNT / 2 - tce, TCOUNT)
    else:
        clk = "DC %g" % VDD                      # stopped high: master transparent, the same input load
    load_line = {"scff": "XL dout clk q dvdd 0 %s\nCQ q 0 %.6e" % (SUBCKT, CQ),
                 "tspc": "XL dout clk q dvdd 0 tspc_dff\nCQ q 0 %.6e" % CQ,
                 "cap10": "CLOAD dout 0 10f"}[load_kind]
    tag = "kick_%s_c%03d_f%d_%s" % (load_kind, code, round(f * 8), "on" if clk_on else "off")
    row = {"tag": tag, "load": load_kind, "code": code, "phase": f, "clk_on": int(clk_on), "vin": vin}
    d = os.path.join(WORK, tag)
    if not (os.environ.get("KICK_REUSE") == "1" and os.path.exists(os.path.join(d, "run.log"))):
        d = render("tb_kick.spice", tag, {"VIN": "%.12g" % vin, "CLK": clk, "LOAD": load_line, "TCE": "%.6e" % tce,
                                            "NETLIST": NETLIST})
        ngspice(d, expect=None)      # no q (the 10 fF reference) makes ngspice exit non-zero
    m = {}
    try:
        with open(os.path.join(d, "run.log"), errors="replace") as h:
            for line in h:
                mm = MEAS.match(line)
                if mm:
                    m[mm.group(1)] = float(mm.group(2))
    except OSError:
        pass
    for k in ("t_cross", "t_dout", "t_f90", "t_f10", "t_q", "armed", "t_rerise", "t_qrerise"):
        row[k] = m.get(k, float("nan"))
    tideal = TR + (vin - VR_LO) / (LSB / TCOUNT)
    for k in ("cross", "dout", "q"):
        if "rel_" + k in m:
            row["t_" + k] = tideal + m["rel_" + k]
    row["ok"] = int(row["t_dout"] == row["t_dout"])
    row["delay_ns"] = (row["t_dout"] - row["t_cross"]) * 1e9
    row["dout_fall_ns"] = (row["t_f10"] - row["t_f90"]) * 1e9
    return row


def cmd_kick():
    jobs = [(c, f, on) for c in KICK_CODES for f in KICK_PHASES for on in (True, False)]
    rows = parallel(lambda j: kick_case(*j), jobs)
    rows += parallel(lambda j: kick_case(j[0], 0.0, False, j[1]), [(c, l) for c in KICK_CODES for l in ("tspc", "cap10")])
    by = {(r["load"], r["code"], r["phase"], r["clk_on"]): r for r in rows}
    out = []
    for c in KICK_CODES:
        dphase, dts = [], []
        for f in KICK_PHASES:
            on, off = by[("scff", c, f, 1)], by[("scff", c, f, 0)]
            if not (on["ok"] and off["ok"]):
                print("FAIL: kick %s / %s: dout did not cross (armed %s / %s V at TR)" % (
                    on["tag"], off["tag"], fmt(on["armed"]), fmt(off["armed"])))
                continue
            dt = on["t_dout"] - off["t_dout"]
            ph = ((on["t_dout"] - TR - TCOUNT / 2) / TCOUNT) % 1.0
            on["dt_kick_ps"] = dt * 1e12
            on["phase_dout"] = ph
            dphase.append(ph)
            dts.append(dt)
            m = math.ceil((on["t_dout"] - TR) / TCOUNT - 0.5)
            edge = TR + (m + 0.5) * TCOUNT
            on["edge_k"] = m
            near = min(abs(on["t_dout"] - edge), abs(on["t_dout"] - edge + TCOUNT)) < 1e-9
            on["latch_ok"] = int(near or (edge < on["t_q"] < edge + AP_CQ_MAX and on["t_qrerise"] != on["t_qrerise"]))
        order = np.argsort(dphase)
        ph = np.array(dphase)[order]
        dv = np.array(dts)[order]
        s_edge = float(np.interp(0.0, np.concatenate((ph - 1, ph, ph + 1)), np.concatenate((dv, dv, dv))))
        off0 = by[("scff", c, 0.0, 0)]
        out.append({"code": c, "kick_at_edge_ps": s_edge * 1e12, "kick_pp_ps": (dv.max() - dv.min()) * 1e12,
                    "kick_mean_ps": dv.mean() * 1e12,
                    "delay_scff_ns": off0["delay_ns"], "delay_tspc_ns": by[("tspc", c, 0.0, 0)]["delay_ns"],
                    "delay_cap10_ns": by[("cap10", c, 0.0, 0)]["delay_ns"],
                    "dout_fall_scff_ns": off0["dout_fall_ns"], "dout_fall_tspc_ns": by[("tspc", c, 0.0, 0)]["dout_fall_ns"],
                    "dout_fall_cap10_ns": by[("cap10", c, 0.0, 0)]["dout_fall_ns"],
                    "n_latch_ok": sum(by[("scff", c, f, 1)].get("latch_ok", 0) for f in KICK_PHASES),
                    "n_phases": len(KICK_PHASES),
                    "n_ok": sum(by[k]["ok"] for k in [("scff", c, f, o) for f in KICK_PHASES for o in (0, 1)] +
                                [("tspc", c, 0.0, 0), ("cap10", c, 0.0, 0)])})
    write_csv(os.path.join(DATA, "kick_runs.csv"), rows)
    write_csv(os.path.join(DATA, "kick.csv"), out)
    for o in out:
        print("kick code %d: %s" % (o["code"], json.dumps({k: fmt(v) for k, v in o.items()})))


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    cmds = {"explore": cmd_explore, "drive": cmd_drive, "slew": cmd_slew, "aperture": cmd_aperture, "kick": cmd_kick}
    for c in sys.argv[1:]:
        if c not in cmds:
            raise SystemExit("unknown command %s" % c)
        cmds[c]()
