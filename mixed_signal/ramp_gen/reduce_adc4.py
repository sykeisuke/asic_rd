"""Reduce the four-cell runs (work/adc4_<tag>/measures.txt) to data/adc4_levels.csv
and the scalar figures of the ramp generator in the conversion.

    python3 reduce_adc4.py data/adc4_cases.txt

data/adc4_cases.txt has one line per run: `set tag ramp_real tpre pos0 pos1 pos2 pos3`.
Sets:
  show      the showcase run (codes 16.5 80.5 160.5 240.5), real and ideal ramp
  coarse    32 levels 4.5 + 8 j over 8 runs (each run spans the range), real and ideal
  fine      127.125 .. 127.875 in quarter LSB, real and ideal
  low       the lowest codes 1.5 2.5 3.5 5.5, real and ideal
  xt        trip-kick crosstalk: cell 0 the victim at 128.5, cells 1-3 at 128.5 - d
            (they trip d LSB before the victim) or 128.5 + d (after it, the
            control: the same S1-connection charge), real ramp
  xc        S1-connection crosstalk: victims at 5.5 / 20.5 (cells 0, 1), cells 2-3
            at 0.5 or 254.5 (no charge / full-scale charge), real ramp
  pre       the coarse set again with a ramp pre-roll (TPRE), real ramp

The ramp generator's own contribution is real - ideal at the same level and
cell: same cells, same references, same timeline, only vr_cell differs.
Prints `name = value` and REPORT lines.
"""
import os
import sys

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
# ADC4_PREFIX (e.g. "simple_"): the same reduction for another DUT, names prefixed and
# data files suffixed, so the simple ramp's four-cell record sits beside ramp_gen's
PFX = os.environ.get("ADC4_PREFIX", "")
SFX = ("_" + PFX.rstrip("_")) if PFX else ""
_print = print


def print(s):
    _print(("REPORT: " + PFX.rstrip("_") + " " + s[8:]) if (PFX and s.startswith("REPORT: ")) else (PFX + s))
LSB = 1.5 / 256


def read_meas(path):
    m = {}
    if not os.path.exists(path):
        return m
    for line in open(path):
        p = line.split("=")
        if len(p) >= 2:
            try:
                m[p[0].strip()] = float(p[1].split()[0])
            except ValueError:
                pass
    return m


cases = [l.split() for l in open(sys.argv[1]) if l.strip()]
rows = []
runs = {}
for c in cases:
    st, tag, real, tpre = c[0], c[1], int(c[2]), float(c[3])
    pos = [float(x) for x in c[4:8]]
    m = read_meas(os.path.join(BLOCK, "work", "adc4_" + tag, "measures.txt"))
    runs[tag] = (st, real, tpre, pos, m)
    for i in range(4):
        e = m.get("err%d" % i)
        rows.append(dict(set=st, tag=tag, real=real, tpre=tpre, cell=i, pos=pos[i],
                         vin=0.5 + pos[i] * LSB, code=m.get("code%d" % i), code_ideal=np.floor(pos[i]),
                         err=e, t_trip=m.get("t_trip%d" % i), vr_top=m.get("vr_top%d" % i),
                         dout_tr=m.get("dout%d_tr" % i)))

with open(os.path.join(BLOCK, "data", "adc4%s_levels.csv" % SFX), "w") as f:
    keys = ["set", "tag", "real", "tpre", "cell", "pos", "vin", "code", "code_ideal", "err", "t_trip", "vr_top", "dout_tr"]
    f.write(",".join(keys) + "\n")
    for r in rows:
        f.write(",".join("" if r[k] is None else (("%.9g" % r[k]) if isinstance(r[k], float) else str(r[k]))
                         for k in keys) + "\n")

missing = [(r["tag"], r["cell"]) for r in rows if r["err"] is None]
print("adc4_runs = %d" % len(runs))
print("adc4_conversions = %d" % len(rows))
print("adc4_missing = %d" % len(missing))
for t, i in missing[:8]:
    print("REPORT: no conversion in run %s cell %d" % (t, i))


def pick(st, real, tpre=None):
    return [r for r in rows if r["set"] == st and r["real"] == real and r["err"] is not None
            and (tpre is None or r["tpre"] == tpre)]


def delta(st):
    """real - ideal error per (pos, cell)."""
    ideal = {(r["pos"], r["cell"]): r for r in pick(st, 0)}
    out = []
    for r in pick(st, 1, 0.0):
        q = ideal.get((r["pos"], r["cell"]))
        if q is not None:
            out.append((r["pos"], r["cell"], r["err"] - q["err"], r["err"], q["err"], r["code"], q["code"]))
    return sorted(out)


# ---- showcase
for r in sorted(pick("show", 1), key=lambda r: r["cell"]):
    print("show_cell%d_pos = %.4g" % (r["cell"], r["pos"]))
    print("show_cell%d_code = %d" % (r["cell"], r["code"]))
    print("show_cell%d_code_ideal = %d" % (r["cell"], r["code_ideal"]))
    print("show_cell%d_err_lsb = %.4f" % (r["cell"], r["err"]))
    print("show_cell%d_vramp_at_trip_lsb = %.4f" % (r["cell"], (r["vr_top"] - r["vin"]) / LSB))
for r in sorted(pick("show", 0), key=lambda r: r["cell"]):
    print("show_ideal_cell%d_err_lsb = %.4f" % (r["cell"], r["err"]))

# ---- coarse transfer, real and ideal, and the ramp's own part
for real, nm in ((1, "real"), (0, "ideal")):
    rr = sorted(pick("coarse", real, 0.0 if real else None), key=lambda r: r["pos"])
    if len(rr) < 4:
        continue
    pos = np.array([r["pos"] for r in rr]); err = np.array([r["err"] for r in rr])
    code = np.array([r["code"] for r in rr]); ci = np.array([r["code_ideal"] for r in rr])
    p = np.polyfit(pos, err, 1)
    print("coarse_%s_n = %d" % (nm, len(rr)))
    print("coarse_%s_err_mean_lsb = %.4f" % (nm, err.mean()))
    print("coarse_%s_err_spread_lsb = %.4f" % (nm, err.max() - err.min()))
    print("coarse_%s_gain_err_pct = %.4f" % (nm, p[0] * 100))
    print("coarse_%s_inl_lsb = %.4f" % (nm, np.max(np.abs(err - np.polyval(p, pos)))))
    print("coarse_%s_monotonic = %d" % (nm, int(np.all(np.diff(code) > 0))))
    print("coarse_%s_code_offset_min = %d" % (nm, int((code - ci).min())))
    print("coarse_%s_code_offset_max = %d" % (nm, int((code - ci).max())))
d = delta("coarse")
if d:
    pos = np.array([x[0] for x in d]); dd = np.array([x[2] for x in d])
    p = np.polyfit(pos, dd, 1)
    print("ramp_offset_lsb = %.4f" % np.polyval(p, 0.0))
    print("ramp_gain_err_pct = %.4f" % (p[0] * 100))
    print("ramp_inl_lsb = %.4f" % np.max(np.abs(dd - np.polyval(p, pos))))
    print("ramp_delta_spread_lsb = %.4f" % (dd.max() - dd.min()))
    np.savetxt(os.path.join(BLOCK, "data", "adc4%s_ramp_delta.csv" % SFX),
               np.array([x[:5] for x in d]), delimiter=",", header="pos,cell,delta_lsb,err_real,err_ideal",
               comments="", fmt="%.6g")
# ---- fine staircase and low codes: the delta
for st in ("fine", "low"):
    d = delta(st)
    for pos, cell, dd, er, ei, cr, ci in d:
        print("%s_p%s_delta_lsb = %.4f" % (st, ("%g" % pos).replace(".", "p"), dd))
        print("%s_p%s_code_real = %d" % (st, ("%g" % pos).replace(".", "p"), cr))
        print("%s_p%s_code_ideal = %d" % (st, ("%g" % pos).replace(".", "p"), ci))
# ---- trip-kick crosstalk: victim (cell 0) below/above aggressors
# xt on the real ramp is the total; xti, the same cases on the ideal ramp, is
# what the cells and the shared VBL / pbias lines carry without the ramp; the
# difference is the ramp generator's share
xt = {"xt": {}, "xti": {}}
for tag, (st, real, tpre, pos, m) in runs.items():
    if st not in xt or m.get("err0") is None:
        continue
    xt[st][pos[1] - pos[0]] = m["err0"]
for dl in sorted(k for k in xt["xt"] if k < 0):
    nm = ("%g" % -dl).replace(".", "p")
    if -dl in xt["xt"]:
        tot = xt["xt"][dl] - xt["xt"][-dl]
        print("xt_d%s_lsb = %.4f" % (nm, tot))
        if dl in xt["xti"] and -dl in xt["xti"]:
            cel = xt["xti"][dl] - xt["xti"][-dl]
            print("xti_d%s_lsb = %.4f" % (nm, cel))
            print("xtr_d%s_lsb = %.4f" % (nm, tot - cel))
# ---- S1-connection crosstalk: victims with the aggressors at 0.5 vs 254.5
xc = {}
for tag, (st, real, tpre, pos, m) in runs.items():
    if st == "xc":
        xc[pos[2]] = m
if 0.5 in xc and 254.5 in xc:
    for i, nm in ((0, "v5"), (1, "v20")):
        a, b = xc[254.5].get("err%d" % i), xc[0.5].get("err%d" % i)
        if a is not None and b is not None:
            print("xc_%s_lsb = %.4f" % (nm, a - b))
# ---- pre-roll: the same coarse set with TPRE, against the ideal ramp
pr = sorted([r for r in rows if r["set"] == "pre" and r["err"] is not None], key=lambda r: r["pos"])
ideal = {(r["pos"], r["cell"]): r for r in pick("coarse", 0)}
if pr:
    dd = np.array([r["err"] - ideal[(r["pos"], r["cell"])]["err"] for r in pr if (r["pos"], r["cell"]) in ideal])
    ps = np.array([r["pos"] for r in pr if (r["pos"], r["cell"]) in ideal])
    p = np.polyfit(ps, dd, 1)
    print("pre_tpre_ns = %.4g" % (pr[0]["tpre"] * 1e9))
    print("pre_ramp_offset_lsb = %.4f" % np.polyval(p, 0.0))
    print("pre_ramp_inl_lsb = %.4f" % np.max(np.abs(dd - np.polyval(p, ps))))
# ---- power of the ramp
pw = [m.get("p_ramp") for (st, real, tpre, pos, m) in runs.values() if real == 1 and m.get("p_ramp") is not None]
if pw:
    print("adc4_p_ramp_uw = %.4g" % (np.mean(pw) * 1e6))
pc = [m.get("p_cells") for (st, real, tpre, pos, m) in runs.values() if m.get("p_cells") is not None]
if pc:
    print("adc4_p_cells_uw = %.4g" % (np.mean(pc) * 1e6))
