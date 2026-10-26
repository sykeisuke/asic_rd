"""Figures of the ramp_gen block (assets/), from the phase outputs.

    python3 plot_ramp.py

  ramp_adc4_trip.png   the showcase: the real ramp driving four cells, each
                       cell's trip against the intended 8-bit code grid
  ramp_transfer.png    error vs level on the real and the ideal ramp, the
                       ramp's own part (real - ideal), crosstalk
  ramp_alone.png       residual from the line, start transient, S1 kick, loop gain
  ramp_noise.png       noise breakdown vs code, top contributors, PSDs
Missing inputs skip their panel and print a REPORT line.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
W, D, A = (os.path.join(BLOCK, x) for x in ("work", "data", "assets"))
os.makedirs(A, exist_ok=True)
LSB, TCOUNT, VR_LO = 1.5 / 256, 50e-9, 0.5
T0 = 7e-6
TR = T0 + 400e-9
# reference palette (dataviz references/palette.md), fixed order, light mode
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
                     "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False,
                     "lines.linewidth": 1.6})


def load_csv(path):
    if not os.path.exists(path):
        print("REPORT: plot input missing: %s" % os.path.relpath(path, BLOCK))
        return None
    with open(path) as f:
        head = f.readline().replace(",", " ").split()
    d = np.loadtxt(path, skiprows=1, delimiter="," if "," in open(path).readline() else None)
    return head, d


def measures(tag):
    m = {}
    p = os.path.join(W, "adc4_" + tag, "measures.txt")
    if os.path.exists(p):
        for line in open(p):
            s = line.split("=")
            try:
                m[s[0].strip()] = float(s[1].split()[0])
            except (IndexError, ValueError):
                pass
    return m


# ------------------------------------------------------------ 1. the showcase
def fig_trip():
    r = load_csv(os.path.join(W, "adc4_s_r", "wave.csv"))
    if r is None:
        return
    head, d = r
    col = {n: i for i, n in enumerate(head)}
    t = d[:, 0]
    m = measures("s_r")
    mi = measures("s_i")
    sel = (t > TR - 300e-9) & (t < TR + 14.0e-6)
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(3, 4, height_ratios=[2.2, 0.8, 1.6], hspace=0.45, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    tt = (t[sel] - TR) / TCOUNT
    ax.plot(tt, d[sel, col["v(vr_cell)"]], color=INK, lw=1.4, label="vramp (ramp_gen, as the cells see it)")
    ax.plot(tt, VR_LO + tt * LSB, color=MUTED, lw=1.0, ls="--", label="intended ramp: 0.5 V + 1 LSB per count")
    for k in range(0, 257, 32):
        ax.axhline(VR_LO + k * LSB, color=GRID, lw=0.6, zorder=0)
    for i in range(4):
        vin = m.get("vin%d" % i)
        tr = m.get("t_trip%d" % i)
        if vin is None or tr is None:
            continue
        ax.axhline(vin, color=C[i], lw=0.9, ls=":")
        ax.plot([tr / TCOUNT], [vin], "o", ms=8, color=C[i], mec=SURF, mew=1.5, zorder=5)
        ax.annotate("cell %d: vin %.4f V\ncode %d (ideal %d), %+.2f LSB" %
                    (i, vin, m["code%d" % i], int((vin - VR_LO) / LSB), m["err%d" % i]),
                    (tr / TCOUNT, vin), xytext=(10, -26 if i < 3 else -34), textcoords="offset points",
                    fontsize=8.5, color=INK)
    ax.set_xlim(-6, 280)
    ax.set_ylim(0.42, 2.2)
    ax.set_xlabel("time after count start TR (counts of 50 ns)")
    ax.set_ylabel("V")
    ax.set_title("ramp_gen driving four 8-bit unit cells: each cell trips when the ramp passes its sampled level")
    ax.legend(loc="upper left")
    # dout traces
    ax2 = fig.add_subplot(gs[1, :], sharex=ax)
    for i in range(4):
        ax2.plot(tt, d[sel, col["v(dout%d)" % i]] / 3.3 * 0.8 + i, color=C[i], lw=1.2)
        ax2.text(-5, i + 0.35, "dout%d" % i, fontsize=8, color=INK2)
    ax2.set_yticks([])
    ax2.set_xlabel("time after TR (counts)")
    ax2.set_title("comparator outputs (HIGH before the crossing, falling edge = the capture)")
    # zooms
    for i in range(4):
        axz = fig.add_subplot(gs[2, i])
        vin, tr = m.get("vin%d" % i), m.get("t_trip%d" % i)
        if vin is None or tr is None:
            continue
        kc = (vin - VR_LO) / LSB
        w = (tt > kc - 4) & (tt < kc + 5)
        axz.plot(tt[w], (d[sel, col["v(vr_cell)"]][w] - VR_LO) / LSB, color=INK, lw=1.3, label="vramp")
        for k in range(int(kc) - 4, int(kc) + 6):
            axz.axvline(k, color=GRID, lw=0.8, zorder=0)
            axz.axhline(k, color=GRID, lw=0.8, zorder=0)
        axz.axhline(kc, color=C[i], ls=":", lw=1.0)
        axz.axvspan(np.floor(kc), np.floor(kc) + 1, color=C[i], alpha=0.10, lw=0)
        axz.axvline(kc, color=MUTED, ls="--", lw=1.0)
        axz.axvline(tr / TCOUNT, color=C[i], lw=2.0)
        if mi.get("t_trip%d" % i) is not None:
            axz.axvline(mi["t_trip%d" % i] / TCOUNT, color=C[i], lw=1.0, ls="-.")
        axz.set_xlim(kc - 4, kc + 5)
        axz.set_ylim(kc - 4, kc + 5)
        axz.set_xlabel("counts after TR")
        if i == 0:
            axz.set_ylabel("(vramp - 0.5 V) / LSB")
        axz.set_title("cell %d: code %d, ideal %d" % (i, m["code%d" % i], int(np.floor(kc))), fontsize=9)
        axz.text(0.03, 0.97, "dashed: ideal crossing\nsolid: dout falls (real ramp)\ndash-dot: same cell, ideal ramp\n"
                 "shaded: the intended code bin\nerror %+.2f LSB (ideal ramp %+.2f)" %
                 (m["err%d" % i], mi.get("err%d" % i, np.nan)), transform=axz.transAxes, va="top", fontsize=7,
                 color=INK2)
    fig.savefig(os.path.join(A, "ramp_adc4_trip.png"), dpi=140, bbox_inches="tight")
    plt.close(fig)
    print("PASS: figure assets/ramp_adc4_trip.png")


# ------------------------------------------------------- 2. transfer / xtalk
def fig_transfer():
    p = os.path.join(D, "adc4_levels.csv")
    if not os.path.exists(p):
        print("REPORT: plot input missing: data/adc4_levels.csv")
        return
    rows = list(csv.DictReader(open(p)))
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    for real, nm, c in ((1, "real ramp (ramp_gen)", C[0]), (0, "ideal ramp", C[1])):
        rr = sorted([r for r in rows if r["set"] == "coarse" and int(r["real"]) == real and r["err"]],
                    key=lambda r: float(r["pos"]))
        axs[0].plot([float(r["pos"]) for r in rr], [float(r["err"]) for r in rr], "o-", ms=4, color=c, label=nm)
    axs[0].set_xlabel("level (LSB above 0.5 V)")
    axs[0].set_ylabel("conversion error (LSB)")
    axs[0].set_title("32 levels, four cells: error = pedestal + linearity")
    axs[0].legend()
    dp = os.path.join(D, "adc4_ramp_delta.csv")
    if os.path.exists(dp):
        dd = np.loadtxt(dp, skiprows=1, delimiter=",", ndmin=2)
        for cell in range(4):
            s = dd[:, 1] == cell
            axs[1].plot(dd[s, 0], dd[s, 2], "o", ms=6, color=C[cell], mec=SURF, label="cell %d" % cell)
        q = np.polyfit(dd[:, 0], dd[:, 2], 1)
        x = np.array([0, 256])
        axs[1].plot(x, np.polyval(q, x), color=MUTED, lw=1, ls="--", label="line: %+.3f LSB %+.3f %%" % (q[1], q[0] * 100))
        axs[1].set_xlabel("level (LSB)")
        axs[1].set_ylabel("real - ideal (LSB)")
        axs[1].set_title("what the ramp generator itself adds")
        axs[1].legend(fontsize=8)
    # crosstalk
    xt = []
    lines = open(os.path.join(W, "ph_adc4.txt")).read().splitlines() if os.path.exists(os.path.join(W, "ph_adc4.txt")) else []
    vals = {l.split(" = ")[0]: float(l.split(" = ")[1]) for l in lines if " = " in l}
    cases = (("d0p25", "trip kick\n0.25 LSB"), ("d1", "trip kick\n1 LSB"), ("d4", "trip kick\n4 LSB"),
             ("d16", "trip kick\n16 LSB"))
    x = 0
    ticks, tl = [], []
    for k, lab in cases:
        tot, cel = vals.get("xt_%s_lsb" % k), vals.get("xti_%s_lsb" % k)
        if tot is None:
            continue
        axs[2].bar(x - 0.18, tot, width=0.34, color=C[0], label="total (real ramp)" if x == 0 else None)
        if cel is not None:
            axs[2].bar(x + 0.18, cel, width=0.34, color=C[1], label="without the ramp (ideal ramp)" if x == 0 else None)
            axs[2].text(x, max(tot, cel, 0) + 0.004, "ramp %+.3f" % (tot - cel), ha="center", fontsize=7, color=INK2)
        ticks.append(x); tl.append(lab); x += 1
    for k, lab in (("xc_v5_lsb", "S1 kick\ncode 5"), ("xc_v20_lsb", "S1 kick\ncode 20")):
        if k in vals:
            axs[2].bar(x, vals[k], width=0.34, color=C[0])
            axs[2].text(x, max(vals[k], 0) + 0.004, "%+.3f" % vals[k], ha="center", fontsize=7, color=INK2)
            ticks.append(x); tl.append(lab); x += 1
    if ticks:
        axs[2].axhline(0.1, color=MUTED, ls="--", lw=1); axs[2].axhline(-0.1, color=MUTED, ls="--", lw=1)
        axs[2].axhline(0, color=MUTED, lw=0.8)
        axs[2].set_xticks(ticks); axs[2].set_xticklabels(tl, fontsize=8)
        axs[2].set_ylabel("victim shift (LSB)")
        axs[2].set_title("crosstalk: 3 aggressors vs one victim (gate +-0.1)")
        axs[2].legend(fontsize=7.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(A, "ramp_transfer.png"), dpi=140)
    plt.close(fig)
    print("PASS: figure assets/ramp_transfer.png")


# ------------------------------------------------------------- 3. the ramp
def fig_alone():
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.8))
    for c, (tag, lab) in enumerate((("nom", "4 cells"), ("n64", "64 cells"), ("pre", "4 cells, 300 ns pre-roll"))):
        r = os.path.join(W, "ramp_" + tag, "residual.csv")
        if not os.path.exists(r):
            continue
        d = np.loadtxt(r, skiprows=1, delimiter=",")
        axs[0].plot(d[:, 0], d[:, 2], color=C[c], lw=1.4, label=lab)
        axs[1].plot(d[:, 0], d[:, 2], "o-", color=C[c], ms=4, lw=1.2, label=lab)
    axs[0].set_xlabel("count k"); axs[0].set_ylabel("vramp - best line (LSB)")
    axs[0].set_title("ramp linearity (line fit on k = 8..256)"); axs[0].set_ylim(-0.01, 0.01); axs[0].set_xlim(8, 277)
    axs[0].legend(fontsize=8)
    axs[1].set_xlim(-0.5, 12); axs[1].set_ylim(-1, 1); axs[1].set_xlabel("count k")
    axs[1].set_title("start of the ramp"); axs[1].legend(fontsize=8)
    for c, tag in enumerate(("nom", "nokick", "n64")):
        r = os.path.join(W, "ramp_" + tag, "ramp.csv")
        if not os.path.exists(r):
            continue
        d = np.loadtxt(r, skiprows=1)
        t0 = 1.31e-6
        s = (d[:, 0] > t0 - 20e-9) & (d[:, 0] < t0 + 300e-9)
        axs[2].plot((d[s, 0] - t0) * 1e9, (d[s, 1] - VR_LO) * 1e3, color=C[c], lw=1.4,
                    label={"nom": "4 full-scale cells", "nokick": "no charge", "n64": "64 full-scale cells"}[tag])
    axs[2].axvline(90, color=MUTED, ls="--", lw=1); axs[2].text(92, 0, "count start", fontsize=7, color=INK2)
    axs[2].set_xlim(-20, 150)
    axs[2].set_xlabel("ns after S1 closes"); axs[2].set_ylabel("vramp - 0.5 V (mV)")
    axs[2].set_title("S1-connection kick (reset held)"); axs[2].legend(fontsize=8)
    axs[2].set_yscale("symlog", linthresh=1)
    for c, tag in enumerate(("rst", "r1p25")):
        r = os.path.join(W, "loop_" + tag, "loop.csv")
        if not os.path.exists(r):
            continue
        d = np.loadtxt(r, skiprows=1)
        axs[3].semilogx(d[:, 0], d[:, 1], color=C[c], lw=1.5, label={"rst": "reset (follower)", "r1p25": "ramping, vramp 1.25 V"}[tag])
    axs[3].axhline(0, color=MUTED, lw=1)
    axs[3].set_xlabel("Hz"); axs[3].set_ylabel("|T| (dB)"); axs[3].set_title("loop gain (Middlebrook)")
    axs[3].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(A, "ramp_alone.png"), dpi=140)
    plt.close(fig)
    print("PASS: figure assets/ramp_alone.png")


# ------------------------------------------------------------- 4. the noise
def fig_noise():
    p = os.path.join(D, "noise_breakdown.csv")
    if not os.path.exists(p):
        print("REPORT: plot input missing: data/noise_breakdown.csv")
        return
    rows = list(csv.DictReader(open(p)))
    codes = sorted({int(r["code"]) for r in rows})
    groups = [("bias_gen", "shared bias_gen (pbias line)"), ("ramp_chain", "ramp slope current XPS/XND/XNS"),
              ("ramp_ota", "ramp OTA (stationary)"), ("ramp_reset", "reset kT/C on C_INT")]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
    tot = np.zeros(len(codes))
    for gi, (g, lab) in enumerate(groups):
        y = np.array([np.sqrt(sum(float(r["var_v2"]) for r in rows if r["group"] == g and int(r["code"]) == k)) / LSB
                      for k in codes])
        tot += (y * LSB) ** 2
        axs[0].plot(codes, y, "o-", color=C[gi], ms=5, label=lab)
    ramp = np.sqrt(tot) / LSB
    axs[0].plot(codes, ramp, "o-", color=INK, ms=5, lw=2, label="ramp total")
    ch = np.sqrt(ramp ** 2 + 0.051 ** 2 + 0.024 ** 2)
    axs[0].plot(codes, ch, "s--", color=C[6], ms=4, lw=1.2, label="channel: ramp + kT/C 0.051 + cmp 0.024")
    axs[0].axhline(0.25, color=MUTED, ls="--", lw=1)
    axs[0].text(codes[-1], 0.255, "contract budget 0.25 LSB", fontsize=7, color=INK2, ha="right")
    axs[0].set_xlabel("code"); axs[0].set_ylabel("rms noise at the ADC input (LSB)")
    axs[0].set_title("noise breakdown vs code (from 1 Hz)"); axs[0].legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0, 0.93))
    axs[0].set_ylim(0, 0.3)
    # top contributors at code 255
    k = max(codes)
    by = {}
    for r in rows:
        if int(r["code"]) == k:
            key = "%s %s" % (r["device"].replace("xrg.", "").replace("xbias.", "bias:"), r["kind"])
            by[key] = by.get(key, 0) + float(r["var_v2"])
    top = sorted(by.items(), key=lambda kv: -kv[1])[:12]
    names = [t[0] for t in top][::-1]
    vals = [np.sqrt(t[1]) / LSB for t in top][::-1]
    axs[1].barh(range(len(vals)), vals, color=C[0], height=0.6)
    axs[1].set_yticks(range(len(vals))); axs[1].set_yticklabels(names, fontsize=7.5)
    for i, v in enumerate(vals):
        axs[1].text(v, i, " %.4f" % v, va="center", fontsize=7)
    axs[1].set_xlabel("LSB rms at code %d" % k); axs[1].set_title("largest single contributors (code %d)" % k)
    # PSDs of the current chain (as current) - the slope noise sources
    q = load_csv(os.path.join(D, "noise_psd.csv"))
    if q is not None:
        head, d = q
        f = d[:, 0]
        sums = {}
        for i, n in enumerate(head[1:], 1):
            if n.startswith("ota:"):
                continue
            g = "bias_gen" if n.startswith("xbias.") else "ramp chain"
            kind = n.split(":")[-1]
            sums.setdefault("%s %s" % (g, kind), np.zeros_like(f))
            sums["%s %s" % (g, kind)] += d[:, i]
        for ci, (n, s) in enumerate(sorted(sums.items())):
            axs[2].loglog(f, np.sqrt(np.maximum(s, 1e-60)), color=C[ci], lw=1.4, label=n)
        axs[2].set_xlim(1, 1e8)
        axs[2].set_xlabel("Hz"); axs[2].set_ylabel("A/sqrt(Hz) into the virtual ground")
        axs[2].set_title("slope-current noise density"); axs[2].legend(fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(A, "ramp_noise.png"), dpi=140)
    plt.close(fig)
    print("PASS: figure assets/ramp_noise.png")


for fn in (fig_trip, fig_transfer, fig_alone, fig_noise):
    try:
        fn()
    except Exception as e:          # a figure must never hide the flow's verdict
        print("REPORT: %s failed: %s" % (fn.__name__, e))
