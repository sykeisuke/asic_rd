"""Aggregate the transient-noise runs, gate them against the frequency-domain
prediction, write data/trannoise_summary.json and assets/ramp_trannoise.png.

    python3 tn_reduce.py <ndisc>          (from trannoise/, container)

Cases (work/case_<c>/s<seed>/conv.csv):
  all    every group noisy
  ramp   ramp_ota + ramp_chain noisy            (b)
  bias   the ramp's own bias_gen noisy (bias_gen_r)    (c)
  cells  comparators, switches, inverters, FVF buffers and their bias_gen   (d)
  quiet  noisescale = 0, the numerical floor    (e)

Statistics: the first NDISC conversions of every seed are dropped (cold start,
the FVF divider and the generator's slow states). sigma is taken over all
remaining conversions of all seeds around one global mean; its standard
error is the spread of the per-seed sigmas / sqrt(nseed), which carries the
correlation between consecutive conversions that a chi-square interval would
not. Trip-time sigma is reported in LSB (sigma_t / TCOUNT, one count per
LSB); vramp sigma in LSB.
"""
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
DATA = os.path.join(HERE, "..", "data")
ASSETS = os.path.join(HERE, "..", "assets")
LSB = 1.5 / 256
TCOUNT = 50e-9
KS = (4, 64, 128, 192, 255)
CASES = ("all", "ramp", "bias", "cells", "quiet")
NDISC = int(sys.argv[1]) if len(sys.argv) > 1 else 6
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"

out = {"ndisc": NDISC}
lines = []


def say(s):
    lines.append(s)
    print(s)


def load(case):
    seeds = []
    for f in sorted(glob.glob(os.path.join(WORK, "case_" + case, "s*", "conv.csv"))):
        d = np.loadtxt(f, skiprows=1, delimiter=",", ndmin=2)
        d = d[d[:, 0] >= NDISC]
        if d.shape[0] >= 3:
            seeds.append(d)
    return seeds


def stat(seeds, col, scale):
    allv = np.concatenate([s[:, col] for s in seeds])
    ok = np.isfinite(allv)
    mu = np.mean(allv[ok])
    sig = np.sqrt(np.mean((allv[ok] - mu) ** 2)) / scale
    per = np.array([np.sqrt(np.nanmean((s[:, col] - mu) ** 2)) / scale for s in seeds])
    se = np.std(per, ddof=1) / np.sqrt(len(per)) if len(per) > 1 else np.nan
    nmiss = int((~ok).sum())
    return sig, se, int(ok.sum()), nmiss


res = {}
for c in CASES:
    seeds = load(c)
    if not seeds:
        say("REPORT: trannoise case %s has no conversions" % c)
        continue
    r = {"nseed": len(seeds), "nconv": int(sum(s.shape[0] for s in seeds))}
    for i in range(4):
        r["trip%d" % i] = stat(seeds, 1 + i, TCOUNT)
    for j, k in enumerate(KS):
        r["v%d" % k] = stat(seeds, 5 + j, LSB)
    # stationarity: first vs second half of every record, and the drift of the mean
    half = []
    for s in seeds:
        m = s.shape[0] // 2
        half.append((s[:m, 5 + KS.index(255)], s[m:, 5 + KS.index(255)]))
    a = np.concatenate([h[0] for h in half]); b = np.concatenate([h[1] for h in half])
    r["half_ratio_v255"] = float(np.std(b) / np.std(a)) if np.std(a) > 0 else np.nan
    nn = np.concatenate([s[:, 0] for s in seeds]); vv = np.concatenate([s[:, 5 + KS.index(255)] for s in seeds])
    slope = np.polyfit(nn, vv, 1)[0] if len(nn) > 2 else 0.0
    r["drift_v255_lsb_per_record"] = float(slope * (nn.max() - nn.min()) / LSB)
    res[c] = r
    say("tn_%s_nseed = %d" % (c, r["nseed"]))
    say("tn_%s_nconv = %d" % (c, r["nconv"]))
    for i in range(4):
        sg, se, n, nm = r["trip%d" % i]
        say("tn_%s_trip%d_lsb = %.5f" % (c, i, sg))
        say("tn_%s_trip%d_se_lsb = %.5f" % (c, i, se))
        if nm:
            say("REPORT: case %s cell %d: %d conversions with no single falling edge" % (c, i, nm))
    for k in KS:
        sg, se, n, nm = r["v%d" % k]
        say("tn_%s_vramp_k%d_lsb = %.5f" % (c, k, sg))
        say("tn_%s_vramp_k%d_se_lsb = %.5f" % (c, k, se))
    say("tn_%s_half_ratio_v255 = %.4f" % (c, r["half_ratio_v255"]))
    say("tn_%s_drift_v255_lsb = %.4f" % (c, r["drift_v255_lsb_per_record"]))

pred = json.load(open(os.path.join(WORK, "predict.json"))) if os.path.exists(os.path.join(WORK, "predict.json")) else {}
out["predict"] = pred
out["cases"] = {c: {k: (list(v) if isinstance(v, tuple) else v) for k, v in r.items()} for c, r in res.items()}

bad = False
# ---- enough independent records per case (seeds can be lost to a step collapse)
for c in CASES:
    n = res.get(c, {}).get("nseed", 0)
    ok = n >= 6
    bad |= not ok
    say("%s: case %s has %d independent seeds (>= 6)" % ("PASS" if ok else "FAIL", c, n))
# ---- the numerical floor
if "quiet" in res and "all" in res:
    worst = 0.0
    for key in ["trip%d" % i for i in range(4)] + ["v%d" % k for k in KS]:
        worst = max(worst, res["quiet"][key][0] / max(res["all"][key][0], 1e-12))
    ok = worst < 0.10
    bad |= not ok
    say("%s: numerical floor (noisescale 0, same grid) at most %.3f of the all-noise sigma (< 0.10)" % ("PASS" if ok else "FAIL", worst))
    out["floor_ratio_max"] = worst
# ---- ramp-only and bias-only against the kernel
for c, g in (("ramp", "ramp"), ("bias", "bias")):
    if c not in res or not pred:
        continue
    for k in KS:
        sg, se, n, nm = res[c]["v%d" % k]
        pv = pred["pred_%s_k%d_lsb" % (g, k)]
        pse = 0.5 * abs(pred["pred_%s_k%d_lsb_hi" % (g, k)] - pred["pred_%s_k%d_lsb_lo" % (g, k)]) / 2
        tol = max(0.25 * pv, 3 * np.hypot(se, pse))
        ok = abs(sg - pv) <= tol
        bad |= not ok
        say("%s: %s-only sigma vramp(k=%d) %.4f +- %.4f LSB vs kernel %.4f (plateau +-%.4f; ngspice PSD %.4f): |diff| %.4f <= %.4f"
            % ("PASS" if ok else "FAIL", c, k, sg, se, pv, pse, pred.get("pred_ngspice_%s_k%d_lsb" % (g, k), np.nan),
               abs(sg - pv), tol))
# ---- RSS of the three groups against all-noise
if all(c in res for c in ("all", "ramp", "bias", "cells")):
    for key in ["trip%d" % i for i in range(4)] + ["v%d" % k for k in KS]:
        s = np.sqrt(sum(res[c][key][0] ** 2 for c in ("ramp", "bias", "cells")))
        sse = np.sqrt(sum((res[c][key][0] * res[c][key][1]) ** 2 for c in ("ramp", "bias", "cells"))) / max(s, 1e-12)
        a, ase = res["all"][key][0], res["all"][key][1]
        tol = 3 * np.hypot(sse, ase)
        ok = abs(a - s) <= tol
        bad |= not ok
        say("%s: %s: all-noise %.4f +- %.4f LSB vs RSS(ramp, bias, cells) %.4f +- %.4f (3 SE %.4f)"
            % ("PASS" if ok else "FAIL", key, a, ase, s, sse, tol))
# ---- stationarity (report; the ensemble must not drift)
for c, r in res.items():
    if c == "quiet":
        continue
    say("REPORT: %s: sigma second half / first half of each record %.3f, mean drift over a record %.4f LSB at k=255"
        % (c, r["half_ratio_v255"], r["drift_v255_lsb_per_record"]))

json.dump(out, open(os.path.join(DATA, "trannoise_summary.json"), "w"), indent=1, default=float)
with open(os.path.join(DATA, "trannoise_breakdown.csv"), "w") as f:
    f.write("case,quantity,sigma_lsb,se_lsb,n\n")
    for c, r in res.items():
        for key in ["trip%d" % i for i in range(4)] + ["v%d" % k for k in KS]:
            f.write("%s,%s,%.6g,%.6g,%d\n" % (c, key, r[key][0], r[key][1], r[key][2]))

# ---- the figure
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                         "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                         "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                         "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                         "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False})
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4))
    groups = [("ramp", "ramp_gen (OTA + slope chain)"), ("bias", "the ramp's own bias_gen"), ("cells", "cells + their bias_gen (cmp, switches, refs)"),
              ("all", "everything noisy"), ("quiet", "noise off (floor)")]
    codes = (16, 80, 160, 240)
    w = 0.16
    for gi, (c, lab) in enumerate(groups):
        if c not in res:
            continue
        y = [res[c]["trip%d" % i][0] for i in range(4)]
        e = [res[c]["trip%d" % i][1] for i in range(4)]
        col = C[gi] if c != "all" else INK
        axs[0].bar(np.arange(4) + (gi - 2) * w, y, w * 0.9, yerr=e, color=col, ecolor=MUTED, capsize=2, label=lab)
    axs[0].set_xticks(range(4)); axs[0].set_xticklabels(["cell %d\ncode %d" % (i, codes[i]) for i in range(4)])
    axs[0].set_ylabel("trip-time sigma x slope (LSB rms)")
    axs[0].set_title("conversion noise by group, VACASK transient noise (%s-%s Hz)"
                     % (("%g" % pred.get("fmin", 0)), ("%g" % pred.get("fmax", 0))))
    axs[0].set_ylim(0, 0.16)
    axs[0].legend(fontsize=7.5, loc="upper left", ncol=2)
    for gi, (c, lab) in enumerate(groups[:2]):
        if c not in res:
            continue
        y = [res[c]["v%d" % k][0] for k in KS]
        e = [res[c]["v%d" % k][1] for k in KS]
        axs[1].errorbar(KS, y, yerr=e, fmt="o", ms=6, color=C[gi], capsize=3, label="%s: transient" % lab)
        if pred:
            axs[1].plot(KS, [pred["pred_%s_k%d_lsb" % (c, k)] for k in KS], "-", color=C[gi], lw=1.6,
                        label="%s: kernel (VACASK noise analysis)" % lab)
            axs[1].fill_between(KS, [pred["pred_%s_k%d_lsb_lo" % (c, k)] for k in KS],
                                [pred["pred_%s_k%d_lsb_hi" % (c, k)] for k in KS], color=C[gi], alpha=0.12, lw=0)
    axs[1].set_xlabel("count k after the ramp release"); axs[1].set_ylabel("sigma of vramp (LSB rms)")
    axs[1].set_title("ramp voltage noise vs time: transient against the exact kernel")
    axs[1].legend(fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(ASSETS, "ramp_trannoise.png"), dpi=140)
    say("PASS: figure assets/ramp_trannoise.png")
except Exception as ex:   # the figure never hides the verdict
    say("REPORT: trannoise figure failed: %s" % ex)
sys.exit(1 if bad else 0)
