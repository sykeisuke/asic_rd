"""Compare ramp_gen (Miller integrator) with ramp_simple (current source + C +
switch) on the figures both went through the same benches for.

    python3 compare_ramps.py work/ph_*.txt

Reads the `name = value` lines of the phase outputs (ramp_gen's unprefixed,
the simple ramp's `simple_`), scores both against the same requirements
(DESIGN_RECIPE.md s.1), writes data/ramp_compare.csv and
assets/ramp_compare.png, and prints compare_* and REPORT lines. The simple
ramp is a baseline, not a candidate: its misses are REPORTed, never FAILed.
"""
import csv
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
W, D, A = (os.path.join(BLOCK, x) for x in ("work", "data", "assets"))
LSB = 1.5 / 256
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"

v = {}
for path in sys.argv[1:]:
    for line in open(path):
        m = re.match(r"^([a-z_0-9]+) = ([-+0-9.eE]+|nan)\s*$", line.strip())
        if m:
            v[m.group(1)] = float(m.group(2))


def g(k):
    return v.get(k, float("nan"))


def params(path):
    p = {}
    for line in open(path):
        m = re.match(r"^\.param (\w+)=([0-9.]+)(u?)", line)
        if m:
            p[m.group(1)] = float(m.group(2)) * (1e-6 if m.group(3) else 1)
    return p


# areas [um2]: MIM plates + MOS gate area (W x L x m), from the parameter files
rg = params(os.path.join(D, "ramp_gen_params.spice"))
rs = params(os.path.join(D, "ramp_simple_params.spice"))
um2 = 1e12
mim_rg = (rg["RG_CIW"] ** 2 + rg["RG_CCW"] ** 2 + rg["RG_COW"] ** 2) * um2
mos_rg = (rg["RG_LPS"] * rg["RG_WPS"] + rg["RG_LN"] * rg["RG_WNS"] * (1 + rg["RG_KD"]) + 0.28e-6 * rg["RG_WRST"]
          + 1e-6 * rg["RG_WT"] + 2 * rg["RG_L1"] * rg["RG_W1"] + 2 * rg["RG_L3"] * rg["RG_W3"]
          + rg["RG_L5"] * rg["RG_W5"] + 1e-6 * rg["RG_W6"] * rg["RG_M6"]) * um2
mim_rs = rs["RS_CW"] ** 2 * um2
mos_rs = (rs["RS_LPS"] * rs["RS_WPS"] + 0.28e-6 * rs["RS_WRST"]) * um2


def psr(pfx):
    return (g(pfx + "vhi_slope_err_pct") - g(pfx + "vlo_slope_err_pct")) / 4.0


ROWS = [
    # (group, label, ramp_gen value, simple value, limit text, test(x) -> bool or None, unit)
    ("topology", "devices (MOS / capacitors / resistors)", "11 / 3 / 1", "2 / 1 / 0", "", None, ""),
    ("topology", "MIM area", mim_rg, mim_rs, "", None, "um2"),
    ("topology", "MOS gate area", mos_rg, mos_rs, "", None, "um2"),
    ("topology", "power incl. its own bias_gen", g("adc4_p_ramp_uw"), g("simple_adc4_p_ramp_uw"), "<= 100", lambda x: x <= 100, "uW"),
    ("slope", "slope error after the trim", g("nom_slope_err_pct"), g("simple_nom_slope_err_pct"), "|x| <= 0.5", lambda x: abs(x) <= 0.5, "%"),
    ("slope", "trim the transient needed (slope / I/C)", (g("size_tran_trim") - 1) * 100, (g("simple_size_tran_trim") - 1) * 100, "", None, "%"),
    ("slope", "slope change, 16 cells vs 4", g("n16_slope_err_pct") - g("nom_slope_err_pct"),
     g("simple_n16_slope_err_pct") - g("simple_nom_slope_err_pct"), "|x| <= 0.05", lambda x: abs(x) <= 0.05, "%"),
    ("slope", "slope change, 64 cells vs 4", g("n64_slope_err_pct") - g("nom_slope_err_pct"),
     g("simple_n64_slope_err_pct") - g("simple_nom_slope_err_pct"), "|x| <= 0.05", lambda x: abs(x) <= 0.05, "%"),
    ("slope", "supply sensitivity (VDD +-2 %)", psr(""), psr("simple_"), "|x| <= 0.2", lambda x: abs(x) <= 0.2, "%/%"),
    ("linearity", "ramp INL, best line, codes 8-256", g("nom_inl_lsb"), g("simple_nom_inl_lsb"), "<= 0.05", lambda x: x <= 0.05, "LSB"),
    ("linearity", "ramp INL, end-point line", g("nom_inl_end_lsb"), g("simple_nom_inl_end_lsb"), "", None, "LSB"),
    ("linearity", "ramp INL with 64 cells", g("n64_inl_lsb"), g("simple_n64_inl_lsb"), "<= 0.05", lambda x: x <= 0.05, "LSB"),
    ("conversion", "the ramp's INL in the 4-cell conversion (real - ideal)", g("ramp_inl_lsb"), g("simple_ramp_inl_lsb"), "<= 0.1", lambda x: x <= 0.1, "LSB"),
    ("conversion", "the ramp's gain error in the conversion", g("ramp_gain_err_pct"), g("simple_ramp_gain_err_pct"), "|x| <= 0.5", lambda x: abs(x) <= 0.5, "%"),
    ("conversion", "the ramp's offset (pedestal)", g("ramp_offset_lsb"), g("simple_ramp_offset_lsb"), "|x| <= 2", lambda x: abs(x) <= 2, "LSB"),
    ("conversion", "error spread, 32 levels, real ramp", g("coarse_real_err_spread_lsb"), g("simple_coarse_real_err_spread_lsb"), "<= 0.25", lambda x: x <= 0.25, "LSB"),
    ("crosstalk", "trip kick, ramp share, aggressors 0.25 LSB before", g("xtr_d0p25_lsb"), g("simple_xtr_d0p25_lsb"), "|x| <= 0.1", lambda x: abs(x) <= 0.1, "LSB"),
    ("crosstalk", "trip kick, ramp share, 1 LSB", g("xtr_d1_lsb"), g("simple_xtr_d1_lsb"), "|x| <= 0.1", lambda x: abs(x) <= 0.1, "LSB"),
    ("crosstalk", "trip kick, ramp share, 4 LSB", g("xtr_d4_lsb"), g("simple_xtr_d4_lsb"), "|x| <= 0.1", lambda x: abs(x) <= 0.1, "LSB"),
    ("crosstalk", "trip kick, ramp share, 16 LSB", g("xtr_d16_lsb"), g("simple_xtr_d16_lsb"), "|x| <= 0.1", lambda x: abs(x) <= 0.1, "LSB"),
    ("crosstalk", "S1-connection kick, victim at code 20", g("xc_v20_lsb"), g("simple_xc_v20_lsb"), "|x| <= 0.1", lambda x: abs(x) <= 0.1, "LSB"),
    ("start", "S1 kick of 4 full-scale cells, peak", g("nom_kick_peak_mv"), g("simple_nom_kick_peak_mv"), "<= 35", lambda x: x <= 35, "mV"),
    ("start", "start deviation at code 0", g("nom_start_dev_lsb_0"), g("simple_nom_start_dev_lsb_0"), "", None, "LSB"),
    ("start", "recovery after the end-of-ramp reset", g("nom_rec_ns"), g("simple_nom_rec_ns"), "<= 1000", lambda x: x <= 1000, "ns"),
    ("noise", "own noise, code 4 (from 1 Hz)", g("noise_ramp_own_c4_lsb"), g("simple_noise_ramp_own_c4_lsb"), "", None, "LSB rms"),
    ("noise", "own noise, code 255", g("noise_ramp_own_c255_lsb"), g("simple_noise_ramp_own_c255_lsb"), "<= 0.10", lambda x: x <= 0.10, "LSB rms"),
    ("noise", "with its bias_gen, code 4", g("noise_ramp_total_c4_lsb"), g("simple_noise_ramp_total_c4_lsb"), "", None, "LSB rms"),
    ("noise", "with its bias_gen, code 255", g("noise_ramp_total_c255_lsb"), g("simple_noise_ramp_total_c255_lsb"), "<= 0.15", lambda x: x <= 0.15, "LSB rms"),
]


def fmt(x):
    if isinstance(x, str):
        return x
    if x != x:
        return "n/a"
    return "%.4g" % x


with open(os.path.join(D, "ramp_compare.csv"), "w") as f:
    w = csv.writer(f)
    w.writerow(["group", "figure", "ramp_gen", "ramp_simple", "limit", "unit", "ramp_gen_meets", "ramp_simple_meets"])
    for grp, lab, a, b, lim, test, unit in ROWS:
        ta = "" if test is None or isinstance(a, str) or a != a else ("yes" if test(a) else "no")
        tb = "" if test is None or isinstance(b, str) or b != b else ("yes" if test(b) else "no")
        w.writerow([grp, lab, fmt(a), fmt(b), lim, unit, ta, tb])
        if test is not None and not isinstance(b, str) and b == b and not test(b):
            print("REPORT: the simple ramp misses %s: %s %s (limit %s; ramp_gen %s)" % (lab, fmt(b), unit, lim, fmt(a)))
n_ok = {k: 0 for k in ("gen", "simple")}
n_all = 0
for grp, lab, a, b, lim, test, unit in ROWS:
    if test is None:
        continue
    n_all += 1
    n_ok["gen"] += int(not isinstance(a, str) and a == a and test(a))
    n_ok["simple"] += int(not isinstance(b, str) and b == b and test(b))
print("compare_requirements = %d" % n_all)
print("compare_ramp_gen_meets = %d" % n_ok["gen"])
print("compare_ramp_simple_meets = %d" % n_ok["simple"])
print("compare_mim_area_gen_um2 = %.1f" % mim_rg)
print("compare_mim_area_simple_um2 = %.1f" % mim_rs)
print("compare_mos_area_gen_um2 = %.1f" % mos_rg)
print("compare_mos_area_simple_um2 = %.1f" % mos_rs)

# ------------------------------------------------------------------ figure
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                     "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False, "lines.linewidth": 1.6})
fig, ax = plt.subplots(2, 3, figsize=(16, 8.6))
NM = (("", "ramp_gen (Miller integrator)", C[0]), ("simple_", "ramp_simple (I source + C + switch)", C[1]))
# (a) linearity
for pfx, lab, col in NM:
    p = os.path.join(W, "ramp_%snom" % pfx, "residual.csv")
    if os.path.exists(p):
        d = np.loadtxt(p, skiprows=1, delimiter=",")
        s = d[:, 0] >= 8
        ax[0, 0].plot(d[s, 0], d[s, 2], color=col, label=lab)
ax[0, 0].set_xlabel("count"); ax[0, 0].set_ylabel("vramp - best line (LSB)")
ax[0, 0].set_title("ramp linearity, 4 cells (fit on counts 8-256)"); ax[0, 0].legend(fontsize=8)
# (b) slope vs number of cells
for pfx, lab, col in NM:
    xs = [4, 16, 64]
    ys = [g(pfx + "nom_slope_err_pct"), g(pfx + "n16_slope_err_pct"), g(pfx + "n64_slope_err_pct")]
    ys = [y - ys[0] for y in ys]
    ax[0, 1].plot(xs, ys, "o-", color=col, ms=6, label=lab)
    ax[0, 1].text(64, ys[-1], "  %+.3f %%" % ys[-1], va="center", fontsize=8, color=INK2)
ax[0, 1].set_xscale("log", base=2); ax[0, 1].set_xticks([4, 16, 64]); ax[0, 1].set_xticklabels(["4", "16", "64"])
ax[0, 1].set_xlabel("cells on the ramp"); ax[0, 1].set_ylabel("slope change vs 4 cells (%)")
ax[0, 1].set_title("load dependence of the slope"); ax[0, 1].legend(fontsize=8)
# (c) the ramp's own error in the conversion
for pfx, lab, col in NM:
    p = os.path.join(D, "adc4%s_ramp_delta.csv" % ("_simple" if pfx else ""))
    if os.path.exists(p):
        d = np.loadtxt(p, skiprows=1, delimiter=",", ndmin=2)
        q = np.polyfit(d[:, 0], d[:, 2], 1)
        ax[0, 2].plot(d[:, 0], d[:, 2] - q[1], "o", ms=4, color=col,
                      label="%s: gain %+.3f %%, INL %.3f LSB" % (lab.split(" ")[0], q[0] * 100,
                                                                np.max(np.abs(d[:, 2] - np.polyval(q, d[:, 0])))))
ax[0, 2].set_xlabel("level (LSB)"); ax[0, 2].set_ylabel("real - ideal ramp, offset removed (LSB)")
ax[0, 2].set_title("what each ramp adds in the 4-cell conversion"); ax[0, 2].legend(fontsize=8)
# (d) crosstalk
cases = [("xtr_d0p25_lsb", "trip\n0.25"), ("xtr_d1_lsb", "trip\n1"), ("xtr_d4_lsb", "trip\n4"),
         ("xtr_d16_lsb", "trip\n16"), ("xc_v5_lsb", "S1\ncode 5"), ("xc_v20_lsb", "S1\ncode 20")]
x = np.arange(len(cases))
for i, (pfx, lab, col) in enumerate(NM):
    ax[1, 0].bar(x + (i - 0.5) * 0.36, [g(pfx + k) for k, _ in cases], 0.34, color=col, label=lab)
ax[1, 0].axhline(0.1, color=MUTED, ls="--", lw=1); ax[1, 0].axhline(-0.1, color=MUTED, ls="--", lw=1)
ax[1, 0].axhline(0, color=MUTED, lw=0.8)
ax[1, 0].set_xticks(x); ax[1, 0].set_xticklabels([c[1] for c in cases], fontsize=8)
ax[1, 0].set_ylabel("victim shift through the ramp (LSB)")
ax[1, 0].set_title("crosstalk (3 aggressors; trip: LSB before the victim)"); ax[1, 0].legend(fontsize=8, loc="upper left")
# (e) noise vs code
for (pfx, lab, col), fn in zip(NM, ("noise_breakdown.csv", "noise_simple_breakdown.csv")):
    p = os.path.join(D, fn)
    if not os.path.exists(p):
        continue
    rows = list(csv.DictReader(open(p)))
    codes = sorted({int(r["code"]) for r in rows})
    own = [np.sqrt(sum(float(r["var_v2"]) for r in rows if int(r["code"]) == k and r["group"] != "bias_gen")) / LSB for k in codes]
    tot = [np.sqrt(sum(float(r["var_v2"]) for r in rows if int(r["code"]) == k)) / LSB for k in codes]
    ax[1, 1].plot(codes, tot, "o-", color=col, label=lab.split(" ")[0] + ", with its bias_gen")
    ax[1, 1].plot(codes, own, "s--", color=col, ms=4, lw=1.1, label=lab.split(" ")[0] + ", own")
ax[1, 1].set_xlabel("code"); ax[1, 1].set_ylabel("rms noise at the ADC input (LSB, from 1 Hz)")
ax[1, 1].set_title("noise vs code"); ax[1, 1].legend(fontsize=8); ax[1, 1].set_ylim(bottom=0)
# (f) the S1 kick
for pfx, lab, col in NM:
    p = os.path.join(W, "ramp_%snom" % pfx, "ramp.csv")
    if os.path.exists(p):
        d = np.loadtxt(p, skiprows=1)
        t0 = 1.31e-6
        s = (d[:, 0] > t0 - 20e-9) & (d[:, 0] < t0 + 150e-9)
        ax[1, 2].plot((d[s, 0] - t0) * 1e9, (d[s, 1] - d[s, 1][0]) * 1e3, color=col, label=lab)
ax[1, 2].axvline(90, color=MUTED, ls="--", lw=1); ax[1, 2].text(92, 1, "count start", fontsize=7, color=INK2)
ax[1, 2].set_xlabel("ns after S1 closes (4 full-scale cells, 60 fC)"); ax[1, 2].set_ylabel("vramp change (mV)")
ax[1, 2].set_title("S1-connection kick (the simple ramp's vrlo is ideal)"); ax[1, 2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(A, "ramp_compare.png"), dpi=140)
print("PASS: figure assets/ramp_compare.png")
