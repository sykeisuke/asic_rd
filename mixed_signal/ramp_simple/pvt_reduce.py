"""Aggregate the pvt phase: every cell's reduced lines (work/ramp_pvt_*/red.txt
and meas.txt) -> pvt_* summary lines and data/pvt.csv.

    python3 pvt_reduce.py

Cells: 5 corners x 0/27/85 C x 3.0/3.3/3.6 V x MIM typical/ss/ff, the design
current from an ideal source. At the typical MIM the gates of SPEC R15: slope
within +-0.5 % (R1; only the switch's junction and the MIM's voltage
coefficient move), INL end-point <= 0.2 LSB (R6), drop at TR <= 0.5 LSB
(R8a), the start settled inside the pre-roll (<= 9 counts), the range
(vramp >= 2.088 V at count 255, R3/R4, ADR 0025). At the MIM corners the slope is
reported: the +-10 % of C that the I/C source has to track.
"""
import csv
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_common as rs  # noqa: E402

DATA = os.path.join(rs.BLOCK, "data")
GATES = {"slope_dev_pct": ("abs", 0.5), "inl_end_lsb": ("le", 0.2), "drop_tr_lsb": ("abs", 0.5),
         "start_settle_k": ("le", rs.K_LO), "vr_255_v": ("ge", rs.V_NEED)}
# the slope gate is the residual against the design slope (unit count rounded down, SPEC R1/R3)
import json as _json
SLOPE_DESIGN = _json.load(open(os.path.join(DATA, "sizing.json")))["predicted"].get("slope_err_design_pct", 0.0)


def load(path, prefix):
    v = {}
    for line in open(path):
        m = re.match(r"^\s*%s_([a-z_0-9]+)\s*=\s*([-+0-9.eE]+)" % re.escape(prefix), line)
        if m:
            v[m.group(1)] = float(m.group(2))
    return v


rows, worst, npass, ntyp = [], {}, 0, 0
mimslope = {"ss": [], "ff": []}
for red in sorted(glob.glob(os.path.join(rs.BLOCK, "work", "ramp_pvt_*", "red.txt"))):
    d = os.path.dirname(red)
    tag = os.path.basename(d)[len("ramp_"):]
    v = load(red, tag)
    v.update({k: x for k, x in load(os.path.join(d, "meas.txt"), tag).items() if k not in v})
    v["slope_dev_pct"] = v.get("slope_err_pct", float("nan")) - SLOPE_DESIGN
    mim = tag.split("_")[-1]                       # ..._<mim>
    if mim in mimslope:
        mimslope[mim].append(v.get("slope_err_pct", float("nan")))
        rows.append([tag] + [v.get(k, float("nan")) for k in GATES] + ["mim " + mim])
        continue
    ntyp += 1
    ok = True
    for key, (kind, lim) in GATES.items():
        x = v.get(key, float("nan"))
        good = {"abs": abs(x) <= lim, "le": x <= lim, "ge": x >= lim}[kind]
        ok = ok and good
        w = worst.setdefault(key, (x, tag))
        if {"abs": abs(x) > abs(w[0]), "le": x > w[0], "ge": x < w[0]}[kind]:
            worst[key] = (x, tag)
    npass += ok
    rows.append([tag] + [v.get(k, float("nan")) for k in GATES] + [int(ok)])
    if not ok:
        print("REPORT: pvt cell %s fails: %s" % (tag, ", ".join("%s=%.4g" % (k, v.get(k, float("nan"))) for k in GATES)))
print("pvt_cells = %d" % ntyp)
print("pvt_pass_cells = %d" % npass)
for key, (x, tag) in worst.items():
    print("pvt_worst_%s = %.6g" % (key, x))
    print("REPORT: pvt worst %s %.4g at %s" % (key, x, tag))
for m, vals in mimslope.items():
    if vals:
        print("pvt_mim_%s_slope_err_min_pct = %.4f" % (m, min(vals)))
        print("pvt_mim_%s_slope_err_max_pct = %.4f" % (m, max(vals)))
os.makedirs(DATA, exist_ok=True)
with open(os.path.join(DATA, "pvt.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cell"] + list(GATES) + ["pass"])
    w.writerows(rows)
