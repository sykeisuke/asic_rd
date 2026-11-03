#!/usr/bin/env python3
"""plot_ic.py -- figures of the I/C source record: assets/ic_op.png (the typical
set: current error per case, start-up waveform, loop gain), assets/ic_pvt.png
(45 cells), assets/ic_mc.png (mismatch draws)."""
import glob
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import ic_common as ic  # noqa: E402

CASES = os.path.join(ic.BLOCK, "work", "cases")
ASSETS = os.path.join(ic.BLOCK, "assets")
os.makedirs(ASSETS, exist_ok=True)


def red(tag):
    d = {}
    f = os.path.join(CASES, tag, "red.txt")
    if not os.path.exists(f):
        return d
    for line in open(f):
        if " = " in line:
            k, v = line.split(" = ", 1)
            try:
                d[k[len(tag) + 1:]] = float(v)
            except ValueError:
                pass
    return d


made = []
# ---- the typical set
tags = ["nom", "rlo", "rhi", "d45", "d55", "v30", "v36", "mss", "mff", "slow", "fast"]
vals = [(t, red(t)) for t in tags]
vals = [(t, d) for t, d in vals if d]
if vals:
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    ax[0].bar([t for t, _ in vals], [d["i_err_pct"] for _, d in vals], color="#4477aa")
    ax[0].axhline(0, color="k", lw=0.5)
    ax[0].set_ylabel("I - C V f  (%)"); ax[0].set_title("current error per case")
    ax[0].tick_params(axis="x", rotation=60)
    w = os.path.join(CASES, "nom", "wave.csv")
    if os.path.exists(w):
        a = np.loadtxt(w)
        ax[1].plot(a[:, 0] * 1e6, a[:, 1] * 1e6, lw=0.6, color="#4477aa")
        ax[1].set_xlabel("t (us)"); ax[1].set_ylabel("i_out (uA)"); ax[1].set_title("cold start, typical")
        ax[1].set_ylim(0, 1.2)
    lp = os.path.join(CASES, "loop", "loop.csv")
    if os.path.exists(lp):
        a = np.loadtxt(lp)
        f, m = a[:, 0], np.hypot(a[:, 1], a[:, 3])
        ph = np.degrees(np.unwrap(np.arctan2(a[:, 3], a[:, 1])))
        ax[2].semilogx(f, 20 * np.log10(m), color="#4477aa", label="|T| (dB)")
        ax2 = ax[2].twinx(); ax2.semilogx(f, ph, color="#cc6677", label="phase (deg)")
        ax[2].axhline(0, color="k", lw=0.5); ax[2].set_xlabel("f (Hz)"); ax[2].set_title("loop gain, typical")
        ax[2].set_ylabel("|T| (dB)"); ax2.set_ylabel("phase (deg)")
    fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "ic_op.png"), dpi=130); plt.close(fig)
    made.append("assets/ic_op.png")
# ---- pvt
pv = os.path.join(ic.BLOCK, "data", "pvt.csv")
if os.path.exists(pv):
    rows = [l.strip().split(",") for l in open(pv)]
    hdr, body = rows[0], rows[1:]
    ie = hdr.index("i_err_pct"); ih = hdr.index("hr_min_mv"); it = hdr.index("t_start_us")
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    x = np.arange(len(body))
    ax[0].plot(x, [float(r[ie]) for r in body], "o", ms=3); ax[0].set_title("current error (%)")
    ax[1].plot(x, [float(r[ih]) for r in body], "o", ms=3); ax[1].axhline(0, color="k", lw=0.5); ax[1].set_title("headroom min (mV)")
    ax[2].plot(x, [float(r[it]) for r in body], "o", ms=3); ax[2].axhline(10, color="k", lw=0.5); ax[2].set_title("start to 1 % (us)")
    for a in ax:
        a.set_xlabel("cell (corner, T, AVDD)")
    fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "ic_pvt.png"), dpi=130); plt.close(fig)
    made.append("assets/ic_pvt.png")
# ---- mc
mc = os.path.join(ic.BLOCK, "data", "mc.csv")
if os.path.exists(mc):
    e = np.loadtxt(mc, skiprows=1)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.hist(e, bins=20, color="#4477aa")
    ax.set_xlabel("I - C V f (%)"); ax.set_title("mismatch, %d draws: sigma %.2f %%" % (len(e), e.std(ddof=1)))
    fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "ic_mc.png"), dpi=130); plt.close(fig)
    made.append("assets/ic_mc.png")
print("REPORT: figures " + ", ".join(made) if made else "REPORT: no figures (no case data)")
