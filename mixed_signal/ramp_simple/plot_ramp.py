"""The block's figures, from the data the phases wrote (assets/*.png).

    python3 plot_ramp.py        (inside the container, from this block)

  ramp_residual.png   the ramp alone against its best line over the conversion window:
                      the pre-roll level, vrlo_ref's level, 16 and 64 cells, the MIM corners
  pvt.png             slope error and INL over the PVT cells (data/pvt.csv)
  adc4.png            four cells on the ramp with the ideal current and on the ideal ramp:
                      the ramp's share per level (data/adc4_levels.csv)
"""
import csv
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLOCK = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BLOCK, "assets")
DATA = os.path.join(BLOCK, "data")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
os.makedirs(ASSETS, exist_ok=True)
made = []


def save(fig, name):
    fig.savefig(os.path.join(ASSETS, name), dpi=160, bbox_inches="tight")
    plt.close(fig)
    made.append(name)


fig, ax = plt.subplots(figsize=(8, 3.6))
for tag, lab in (("level", "ideal pre-roll level 0.42 V, 4 cells"), ("nom", "vrlo_ref (7/55 AVDD), 4 cells"),
                 ("n16", "16 cells"), ("n64", "64 cells"), ("mimss", "MIM ss"), ("mimff", "MIM ff")):
    p = os.path.join(BLOCK, "work", "ramp_" + tag, "residual.csv")
    if os.path.exists(p):
        d = np.loadtxt(p, delimiter=",", skiprows=1)
        ax.plot(d[:, 0], d[:, 2], lw=1.2, label=lab)
ax.axhline(0, color="k", lw=0.6)
ax.set_xlabel("count after the release")
ax.set_ylabel("residual from the best line (LSB)")
ax.legend(frameon=False, fontsize=9)
ax.set_title("the ramp alone on an ideal current: residual over the 259 counts", fontsize=10)
save(fig, "ramp_residual.png")

p = os.path.join(DATA, "pvt.csv")
if os.path.exists(p):
    rows = [r for r in csv.DictReader(open(p)) if r["pass"] in ("0", "1")]
    if rows:
        fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
        x = np.arange(len(rows))
        axs[0].plot(x, [float(r.get("slope_dev_pct", r.get("slope_err_pct", "nan"))) for r in rows], ".", ms=4)
        axs[0].axhline(0.5, color="r", lw=0.8, ls="--"); axs[0].axhline(-0.5, color="r", lw=0.8, ls="--")
        axs[0].set_ylabel("slope vs design (%)"); axs[0].set_xlabel("cell (corner x T x AVDD), MIM typical")
        axs[1].plot(x, [float(r["inl_end_lsb"]) for r in rows], ".", ms=4)
        axs[1].axhline(0.2, color="r", lw=0.8, ls="--")
        axs[1].set_ylabel("INL end-point (LSB)"); axs[1].set_xlabel("cell")
        save(fig, "pvt.png")

p = os.path.join(DATA, "adc4_levels.csv")
if os.path.exists(p):
    d = np.loadtxt(p, delimiter=",", skiprows=1)
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    axs[0].plot(d[:, 0], d[:, 1], "o", ms=3, label="the ramp cell, ideal current")
    axs[0].plot(d[:, 0], d[:, 2], "s", ms=3, label="ideal ramp")
    axs[0].set_xlabel("input level (LSB above the reset level)"); axs[0].set_ylabel("input-referred error (LSB)")
    axs[0].legend(frameon=False, fontsize=9)
    axs[1].plot(d[:, 0], d[:, 5], "o", ms=3, label="real - ideal")
    axs[1].plot(d[:, 0], d[:, 6], "x", ms=4, label="after the line")
    axs[1].axhline(0, color="k", lw=0.6)
    axs[1].set_xlabel("input level (LSB)"); axs[1].set_ylabel("the ramp's share (LSB)")
    axs[1].legend(frameon=False, fontsize=9)
    save(fig, "adc4.png")

print("REPORT: figures " + ", ".join("assets/" + m for m in made))
