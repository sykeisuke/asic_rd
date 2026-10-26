#!/usr/bin/env python3
"""plot_func.py -- figures of the analog_top functional record.

Reads work/func/wave.npz (func_reduce.py) and data/func_measures.txt and
writes:
  assets/func_overview.png   the whole record, stacked panels on one time axis
  assets/func_powerup.png    0 .. TS0: supplies, bias, references, ramp reset
  assets/func_sampling.png   TS0-30 ns .. TR+100 ns: switch controls, plates
  assets/func_trips.png      each cell +-150 ns around its crossing
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NPZ = os.path.join(HERE, "work", "func", "wave.npz")
MEAS = os.path.join(HERE, "data", "func_measures.txt")
ASSETS = os.path.join(HERE, "assets")

CELL = ["#1f5fa8", "#d1495b", "#2a9d5c", "#8a5cc2"]     # cells 0..3
C_REF, C_VBL, C_MID = "#e07b00", "#00838f", "#7a7a7a"
C_RAMP, C_VIN, C_CLK = "#222222", "#b8860b", "#9e9e9e"
C_SUP = ["#222222", "#9e9e9e"]

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 130, "savefig.bbox": "tight",
})


def load_meas():
    m = {}
    with open(MEAS) as f:
        for line in f:
            p = line.split()
            if len(p) >= 3 and p[1] == "=":
                try:
                    m[p[0]] = float(p[2])
                except ValueError:
                    pass
    return m


def marks(ax, m, tscale, which=("p_t0", "p_ts0", "p_tr", "p_te"), labels=True, offset=0.0):
    # label alignment keeps T0 / TS0 / TR (0.3 and 0.22 us apart) from overlapping
    names = {"p_t0": ("T0 ", "right"), "p_ts0": ("", "left"), "p_tr": (" TS0..TR", "left"), "p_te": (" TE", "left")}
    for k in which:
        if k in m:
            x = (m[k] - offset) * tscale
            ax.axvline(x, color="#555555", lw=0.6, ls="--", zorder=0)
            if labels:
                txt, ha = names[k]
                if len(which) == 1:
                    txt, ha = " " + txt.strip(), "left"
                ax.text(x, 1.0, txt, transform=ax.get_xaxis_transform(), va="bottom", ha=ha,
                        fontsize=7, color="#555555")


def legend(ax, **kw):
    ax.legend(loc=kw.pop("loc", "upper right"), ncol=kw.pop("ncol", 1), frameon=False, **kw)


def overview(d, m):
    t = d["t"] * 1e6
    fig, ax = plt.subplots(6, 1, figsize=(10, 12.5), sharex=True,
                           gridspec_kw={"height_ratios": [1, 1.1, 1.1, 1.3, 1.6, 1.3]})
    ax[0].plot(t, d["avdd"], color=C_SUP[0], label="avdd")
    ax[0].plot(t, d["dvdd"], color=C_SUP[1], ls="--", label="dvdd")
    ax[0].set_ylabel("supply (V)")
    legend(ax[0], loc="lower right", ncol=2)
    for k in range(4):
        ax[1].plot(t, d["pbias%d" % k], color=CELL[k], label="pbias%d" % k)
    ax[1].plot(t, d["pbias_r"], color=C_RAMP, ls="--", label="pbias_r")
    ax[1].set_ylabel("bias (V)")
    ax[1].set_ylim(2.2, 2.6)
    legend(ax[1], loc="lower right", ncol=5)
    ax[2].plot(t, (d["vref"] - 1.65) * 1e3, color=C_REF, label="vref")
    ax[2].plot(t, (d["vbl"] - 1.65) * 1e3, color=C_VBL, label="vbl")
    ax[2].plot(t, (d["vmid"] - 1.65) * 1e3, color=C_MID, ls=":", label="tap vmid")
    ax[2].set_ylabel("ref - 1.65 V (mV)")
    ax[2].set_ylim(-15, 15)
    ax[2].text(0.005, 0.04, "clipped: the vin-step kicks reach +55 mV (fig. c)", transform=ax[2].transAxes,
               fontsize=7, color="#555555")
    legend(ax[2], loc="lower right", ncol=3)
    ax[3].plot(t, d["vramp"], color=C_RAMP, label="vramp")
    ax[3].plot(t, d["vin"], color=C_VIN, label="vin")
    for k in range(4):
        ax[3].axhline(m["p_vin%d" % k], color=CELL[k], lw=0.6, ls=":")
    ax[3].set_ylabel("ramp, input (V)")
    legend(ax[3], loc="upper left", ncol=2)
    for k in range(4):
        ax[4].plot(t, d["bot%d" % k], color=CELL[k], label="bot%d" % k)
        if ("t_bot%d" % k) in m:
            ax[4].plot(m["t_bot%d" % k] * 1e6, m["vbl_bot%d" % k], "o", ms=4, color=CELL[k])
    ax[4].plot(t, d["vbl"], color=C_VBL, lw=0.8, label="vbl")
    ax[4].set_ylabel("bottom plates (V)")
    ax[4].set_ylim(0.4, 2.2)
    legend(ax[4], loc="lower right", ncol=5)
    for k in range(4):
        ax[5].plot(t, d["q%d" % k] / 3.3 * 0.8 + k, color=CELL[k])
        ax[5].text(t[-1], k + 0.4, " q%d: code %d" % (k, m.get("code%d" % k, -1)), fontsize=7, color=CELL[k],
                   va="center")
    ax[5].set_yticks([0.4, 1.4, 2.4, 3.4], ["q0", "q1", "q2", "q3"])
    ax[5].set_ylabel("latch outputs")
    ax[5].set_xlabel("time (us)")
    for a in ax:
        marks(a, m, 1e6, labels=(a is ax[0]))
    ax[0].set_title("analog_top: one record from a cold supply (typical, 27 C, 3.3 V)", loc="left", pad=14)
    fig.savefig(os.path.join(ASSETS, "func_overview.png"))
    plt.close(fig)


def powerup(d, m):
    t_end = m["p_ts0"]
    w = d["t"] <= t_end
    t = d["t"][w] * 1e6
    fig, ax = plt.subplots(5, 1, figsize=(9, 10), sharex=True)
    ax[0].plot(t, d["avdd"][w], color=C_SUP[0], label="avdd")
    ax[0].plot(t, d["dvdd"][w], color=C_SUP[1], ls="--", label="dvdd")
    ax[0].set_ylabel("supply (V)")
    legend(ax[0], loc="lower right", ncol=2)
    for k in range(4):
        ax[1].plot(t, d["pbias%d" % k][w], color=CELL[k], label="pbias%d" % k)
    ax[1].plot(t, d["pbias_r"][w], color=C_RAMP, ls="--", label="pbias_r")
    ax[1].set_ylabel("bias (V)")
    legend(ax[1], loc="lower right", ncol=5)
    ax[2].plot(t, d["vref"][w], color=C_REF, label="vref")
    ax[2].plot(t, d["vbl"][w], color=C_VBL, ls="--", label="vbl")
    ax[2].plot(t, d["vmid"][w], color=C_MID, ls=":", label="tap vmid")
    ax[2].set_ylabel("references (V)")
    legend(ax[2], loc="lower right", ncol=3)
    ax[3].plot(t, d["vramp"][w], color=C_RAMP, label="vramp (reset)")
    for k in range(4):
        ax[3].plot(t, d["bot%d" % k][w], color=CELL[k], lw=0.8, label="bot%d" % k)
    ax[3].set_ylabel("vramp, bot (V)")
    legend(ax[3], loc="lower right", ncol=5)
    ia = -d["i_vavdd"][w] * 1e6
    ax[4].plot(t, ia, color=C_SUP[0], label="AVDD total")
    ax[4].plot(t, d["i_vmbg"][w] * 1e6, color="#6d4c41", label="bias_gen")
    ax[4].plot(t, d["i_vmref"][w] * 1e6, color=C_REF, label="refs")
    ax[4].plot(t, d["i_vmramp"][w] * 1e6, color=C_RAMP, ls="--", label="ramp")
    ax[4].plot(t, sum(d["i_vmc%d" % k][w] for k in range(4)) * 1e6, color=CELL[0], label="4 cells")
    ax[4].set_ylabel("AVDD current (uA)")
    ax[4].set_ylim(-50, 1000)
    ax[4].set_xlabel("time (us, log)")
    legend(ax[4], loc="upper right", ncol=3)
    ax[4].text(0.005, 0.9, "charging spikes during the 100 ns supply ramp are clipped", transform=ax[4].transAxes,
               fontsize=7, color="#555555")
    ax[4].set_xscale("log")
    ax[4].set_xlim(5e-3, t_end * 1e6)
    for a in ax:
        marks(a, m, 1e6, which=("p_t0",), labels=(a is ax[0]))
    ax[0].set_title("power-up, 0 .. TS0 (log time: every node is settled by 0.5 us)", loc="left", pad=14)
    fig.savefig(os.path.join(ASSETS, "func_powerup.png"))
    plt.close(fig)


def sampling(d, m):
    t0, t1 = m["p_ts0"] - 30e-9, m["p_tr"] + 100e-9
    w = (d["t"] >= t0) & (d["t"] <= t1)
    t = (d["t"][w] - m["p_ts0"]) * 1e9
    fig, ax = plt.subplots(5, 1, figsize=(10, 12), sharex=True,
                           gridspec_kw={"height_ratios": [1.6, 1.3, 1.3, 1.1, 1.1]})
    for k in range(4):
        base = (3 - k) * 3.6
        for j, (sw, ls) in enumerate((("s2", "-"), ("s0", "--"), ("s1", ":"))):
            ax[0].plot(t, d["%s_%d" % (sw, k)][w] / 3.3 * 0.9 + base + j * 1.1, color=CELL[k], ls=ls)
            ax[0].text(t[0], base + j * 1.1 + 0.45, "%s_%d " % (sw, k), ha="right", va="center", fontsize=7,
                       color=CELL[k])
    ax[0].set_yticks([])
    ax[0].set_ylabel("switch controls (high = closed)")
    for k in range(4):
        ax[1].plot(t, d["bot%d" % k][w], color=CELL[k], label="bot%d" % k)
    ax[1].plot(t, d["vbl"][w], color=C_VBL, lw=0.8, ls="--", label="vbl")
    ax[1].set_ylabel("bottom plates (V)")
    legend(ax[1], loc="lower left", ncol=5)
    for k in range(4):
        ax[2].plot(t, d["top%d" % k][w], color=CELL[k], label="top%d" % k)
    ax[2].plot(t, d["vin"][w], color=C_VIN, lw=0.9, ls="--", label="vin")
    ax[2].plot(t, d["vramp"][w], color=C_RAMP, lw=0.9, ls=":", label="vramp")
    ax[2].set_ylabel("top plates (V)")
    legend(ax[2], loc="center right", ncol=3)
    ax[3].plot(t, (d["vref"][w] - 1.65) * 1e3, color=C_REF, label="vref")
    ax[3].plot(t, (d["vbl"][w] - 1.65) * 1e3, color=C_VBL, label="vbl")
    ax[3].plot(t, (d["vmid"][w] - 1.65) * 1e3, color=C_MID, ls=":", label="tap vmid")
    ax[3].set_ylabel("ref - 1.65 V (mV)")
    legend(ax[3], loc="upper right", ncol=3)
    for k in range(4):
        ax[4].plot(t, d["dout%d" % k][w] / 3.3 * 0.8 + k, color=CELL[k], lw=0.9)
        ax[4].plot(t, d["q%d" % k][w] / 3.3 * 0.8 + k, color=CELL[k], lw=0.9, ls="--")
    ax[4].set_yticks([0.4, 1.4, 2.4, 3.4], ["cell 0", "cell 1", "cell 2", "cell 3"])
    ax[4].set_ylabel("dout (solid), q (dashed)")
    ax[4].set_xlabel("time from TS0 (ns)")
    for a in ax:
        for k in range(4):
            a.axvline((m["p_ts%d" % k] - m["p_ts0"]) * 1e9, color=CELL[k], lw=0.6, ls="--", zorder=0)
        a.axvline((m["p_tr"] - m["p_ts0"]) * 1e9, color="#555555", lw=0.6, ls="--", zorder=0)
    ax[0].text((m["p_tr"] - m["p_ts0"]) * 1e9, 1.0, " TR", transform=ax[0].get_xaxis_transform(), fontsize=7,
               color="#555555", va="bottom")
    ax[0].set_title("sampling window: S2_k opens (sample), S0_k opens, S1_k closes; vin steps 20 ns after each "
                    "sample", loc="left", pad=14)
    fig.savefig(os.path.join(ASSETS, "func_sampling.png"))
    plt.close(fig)


def trips(d, m):
    fig, ax = plt.subplots(3, 4, figsize=(13, 7.5), sharex=True,
                           gridspec_kw={"height_ratios": [1.4, 1, 1]})
    for k in range(4):
        tc = m.get("t_bot%d" % k)
        if tc is None:
            continue
        w = (d["t"] >= tc - 150e-9) & (d["t"] <= tc + 150e-9)
        t = (d["t"][w] - tc) * 1e9
        a = ax[0, k]
        a.plot(t, (d["bot%d" % k][w] - d["vbl"][w]) * 1e3, color=CELL[k], label="bot - vbl")
        a.axhline(0, color=C_VBL, lw=0.8)
        a.set_ylim(-25, 25)
        a.set_title("cell %d: vin %.1f LSB -> code %d (ideal %d)" % (k, m["p_pos%d" % k], m["code%d" % k],
                                                                   m["code_ideal%d" % k]), loc="left")
        if k == 0:
            a.set_ylabel("bot - vbl (mV)")
        a = ax[1, k]
        a.plot(t, d["cnt_clk"][w], color=C_CLK, lw=0.8, label="cnt_clk")
        a.plot(t, d["dout%d" % k][w], color=CELL[k], label="dout")
        if k == 0:
            a.set_ylabel("dout, cnt_clk (V)")
            legend(a, loc="center left")
        a = ax[2, k]
        a.plot(t, d["cnt_clk"][w], color=C_CLK, lw=0.8)
        a.plot(t, d["q%d" % k][w], color=CELL[k], label="q")
        if k == 0:
            a.set_ylabel("q, cnt_clk (V)")
        a.set_xlabel("time from bot = vbl (ns)")
        for r, key in ((1, "t_dout%d" % k), (2, "t_q%d" % k)):
            if key in m:
                x = (m[key] - tc) * 1e9
                ax[r, k].axvline(x, color=CELL[k], lw=0.6, ls="--")
                ax[r, k].text(x, 1.6, " %.2f ns" % x, fontsize=7, color=CELL[k])
        ax[0, k].text(0.02, 0.92, "comparator delay %.2f ns" % (m["cmp_delay%d" % k] * 1e9), transform=ax[0, k].transAxes,
                      fontsize=7)
    fig.suptitle("the four trips: bot crosses vbl, dout falls, q falls at the next cnt_clk falling edge",
                 x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(ASSETS, "func_trips.png"))
    plt.close(fig)


def main():
    if not os.path.exists(NPZ):
        print("FAIL: plot_func: %s missing (func_reduce.py did not run)" % NPZ)
        return 1
    d = dict(np.load(NPZ))
    m = load_meas()
    os.makedirs(ASSETS, exist_ok=True)
    overview(d, m)
    powerup(d, m)
    sampling(d, m)
    trips(d, m)
    for n in ("func_overview", "func_powerup", "func_sampling", "func_trips"):
        print("Figure: %s" % os.path.join(ASSETS, n + ".png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
