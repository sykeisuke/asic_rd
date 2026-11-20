"""Waveform figures of the sequencer at typical (27 C, 3.3 V), for DESIGN.md.

    python3 wave.py          (run.sh phase `wave`, not in the default phases)

Renders tb_seq.spice exactly as bench.py does (work/wave_typ), adds the shift
register outputs and cell 0's clock-generator nodes to the saved vectors, runs
ngspice and draws:

  assets/wave_overview.png       clk, acq, t0..t3 and S2 / S0 / S1 of the four cells
  assets/wave_entry_cell0.png    cell 0 at its sampling edge, through the generator
  assets/wave_reentry_cell0.png  cell 0 when acq returns (S1 opens before S0 closes)
  assets/gaps_pvt.png            the three gaps at the 45 PVT cells (data/pvt.csv)

Prints REPORT lines with the edge times it reads; judges nothing (the bench
phases do).
"""
import csv
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import bench
from seq_common import BLOCK, NCELLS, TCOUNT

VDD = 3.3
R0 = bench.R0
try:
    import json
    N_STAGE = int(json.load(open(os.path.join(BLOCK, "data", "sizing.json")))["n_stage"])
except (OSError, KeyError, ValueError):
    N_STAGE = -1
ASSETS = os.path.join(BLOCK, "assets")
# categorical slots 1-3 of the reference palette, in fixed order
C_S2, C_S0, C_S1 = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#2b2b2a", "#77766f", "#e4e3de"
EXTRA = (["v(xseq.t%d)" % k for k in range(NCELLS)]
         + ["v(xseq.xg0.%s)" % n for n in ("clkinb", "clkinbb", "x1", "b1",
                                            "n2", "n2d", "a2", "x2", "b2")])


def simulate():
    d = bench.render("wave_typ", "typical", 27, VDD)
    p = os.path.join(d, "tb.spice")
    text = open(p).read()
    if "wrdata out.csv " not in text:
        raise SystemExit("FAIL: wave.py: no wrdata line in tb_seq.spice")
    text = text.replace("wrdata out.csv ", "wrdata out.csv " + " ".join(EXTRA) + " ", 1)
    open(p, "w").write(text)
    why = bench.ngspice(d)
    if why:
        print("FAIL: wave.py: ngspice wave_typ did not finish (%s)" % why)
        sys.exit(1)
    return bench.load(d)


def edge(t, v, direction, after):
    return bench.first_after(bench.crossings(t, v, VDD / 2, direction), after)


def style(ax, label, color=INK):
    ax.set_yticks([])
    ax.set_ylim(-0.25 * VDD, 1.25 * VDD)
    ax.set_ylabel(label, rotation=0, ha="right", va="center", color=INK, fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8)
    ax.grid(axis="x", color=GRID, linewidth=0.6)


def trace(ax, t, v, color=INK, lw=1.4, **kw):
    ax.plot(t, v, color=color, linewidth=lw, **kw)


def overview(w):
    t = w["time"] * 1e9
    rows = [("clk 20 MHz", "v(clk)"), ("acq", "v(acq)")] + [("t%d" % k, "v(xseq.t%d)" % k) for k in range(NCELLS)]
    fig, axes = plt.subplots(len(rows) + NCELLS, 1, figsize=(11, 9.5), sharex=True,
                             gridspec_kw={"hspace": 0.15})
    for ax, (lab, n) in zip(axes, rows):
        trace(ax, t, w[n], color=MUTED if n == "v(clk)" else INK, lw=1.0 if n == "v(clk)" else 1.4)
        style(ax, lab)
    for k in range(NCELLS):
        ax = axes[len(rows) + k]
        trace(ax, t, w["v(s2_%d)" % k], C_S2, label="S2 (HOLD_REF)")
        trace(ax, t, w["v(s0_%d)" % k], C_S0, label="S0 (SAMPLE)")
        trace(ax, t, w["v(s1_%d)" % k], C_S1, label="S1 (RAMP_CONNECT)")
        style(ax, "cell %d" % k)
    for ax in axes:
        for k in range(NCELLS):
            ax.axvline((R0 + k * TCOUNT) * 1e9, color=GRID, linewidth=1.0, linestyle=":", zorder=0)
    h, l = axes[len(rows)].get_legend_handles_labels()
    fig.legend(h, l, loc="upper left", bbox_to_anchor=(0.12, 0.955), ncol=3, frameon=False, fontsize=9)
    axes[-1].set_xlim((R0 - 120e-9) * 1e9, (R0 + 680e-9) * 1e9)
    axes[-1].set_xlabel("time (ns); dotted: the rising clock edges that sample cells 0..3", color=MUTED, fontsize=9)
    fig.suptitle("sample_seq, typical 27 C 3.3 V: acq low -> one cell sampled per clock edge, 50 ns apart; "
                 "acq high -> all four back to track", color=INK, fontsize=11, x=0.02, ha="left")
    fig.savefig(os.path.join(ASSETS, "wave_overview.png"), dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def zoom(w, name, t0, t1, rows, gaps, title):
    t = w["time"] * 1e9
    fig, axes = plt.subplots(len(rows), 1, figsize=(11, 0.62 * len(rows) + 1.2), sharex=True,
                             gridspec_kw={"hspace": 0.12})
    for ax, (lab, n, color) in zip(axes, rows):
        trace(ax, t, w[n], color)
        style(ax, lab)
    for (ia, ta), (ib, tb), text in gaps:
        for i, x in ((ia, ta), (ib, tb)):
            for ax in axes[min(ia, ib):max(ia, ib) + 1]:
                ax.axvline(x, color=MUTED, linewidth=0.7, linestyle="--", zorder=0)
        ax = axes[max(ia, ib)]
        ax.annotate("", xy=(tb, 0.5 * VDD), xytext=(ta, 0.5 * VDD),
                    arrowprops=dict(arrowstyle="<->", color=INK, linewidth=0.9))
        ax.text((ta + tb) / 2, 0.40 * VDD, text, ha="center", va="top", color=INK, fontsize=9)
    axes[-1].set_xlim(t0, t1)
    axes[-1].set_xlabel("time (ns)", color=MUTED, fontsize=9)
    fig.suptitle(title, color=INK, fontsize=11, x=0.02, ha="left")
    fig.savefig(os.path.join(ASSETS, name), dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def gaps_pvt():
    rows = list(csv.DictReader(open(os.path.join(BLOCK, "data", "pvt.csv"))))
    rows = [r for r in rows if r.get("sim_ok") == "1"]
    if not rows:
        print("REPORT: wave.py: data/pvt.csv has no finished run, gaps_pvt.png not drawn")
        return
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(11, 3.6))
    for col, color, lab in (("g20_min_ns", C_S2, "S2 open -> S0 open"), ("g01_min_ns", C_S0, "S0 open -> S1 closed"),
                            ("gre_min_ns", C_S1, "re-entry: S1 open -> S0 closed")):
        ax.plot(x, [float(r[col]) for r in rows], "o", color=color, markersize=5, label=lab)
    if "t4inv_max_ns" in rows[0]:
        ax.step(x, [float(r["t4inv_max_ns"]) for r in rows], where="mid", color=INK, linewidth=1.0,
                label="minimum: four-inverter delay of the same cell")
    corners = [r["corner"] for r in rows]
    starts = [i for i in range(len(rows)) if i == 0 or corners[i] != corners[i - 1]]
    for i in starts[1:]:
        ax.axvline(i - 0.5, color=GRID, linewidth=1.0)
    ax.set_xticks([i + 4 for i in starts])
    ax.set_xticklabels([corners[i] for i in starts])
    ax.set_ylabel("gap (ns)", color=INK, fontsize=9)
    ax.set_ylim(0, None)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
    ax.set_title("The three gaps at 45 PVT cells (per corner: 0 / 27 / 85 C x 3.0 / 3.3 / 3.6 V), "
                 "min over the four cells", color=INK, fontsize=10, loc="left")
    fig.savefig(os.path.join(ASSETS, "gaps_pvt.png"), dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    w = simulate()
    t = w["time"]
    tclk = edge(t, w["v(clk)"], +1, R0 - 5e-9)
    tt0 = edge(t, w["v(xseq.t0)"], -1, R0 - 5e-9)
    ts2 = edge(t, w["v(s2_0)"], -1, R0 - 5e-9)
    tx1 = edge(t, w["v(xseq.xg0.x1)"], -1, R0 - 5e-9)
    ts0 = edge(t, w["v(s0_0)"], -1, R0 - 5e-9)
    tn2d = edge(t, w["v(xseq.xg0.n2d)"], -1, R0 - 5e-9)
    ts1 = edge(t, w["v(s1_0)"], +1, R0 - 5e-9)
    ns = lambda x: (x - tclk) * 1e9
    print("REPORT: wave typ cell 0 entry after the clock edge: t0 %.2f, S2 open %.2f, x1 (S2 through the "
          "delay stage) %.2f, S0 open %.2f, n2d %.2f, S1 closed %.2f ns; gaps %.2f / %.2f ns"
          % (ns(tt0), ns(ts2), ns(tx1), ns(ts0), ns(tn2d), ns(ts1), (ts0 - ts2) * 1e9, (ts1 - ts0) * 1e9))
    rclk = edge(t, w["v(clk)"], +1, R0 + 450e-9 - 5e-9)
    rs1 = edge(t, w["v(s1_0)"], -1, R0 + 440e-9)
    rx2 = edge(t, w["v(xseq.xg0.x2)"], -1, R0 + 440e-9)
    rs0 = edge(t, w["v(s0_0)"], +1, R0 + 440e-9)
    rs2 = edge(t, w["v(s2_0)"], +1, R0 + 440e-9)
    print("REPORT: wave typ cell 0 re-entry after the clock edge: S1 open %.2f, x2 %.2f, S0 closed %.2f, "
          "S2 closed %.2f ns; gap %.2f ns"
          % ((rs1 - rclk) * 1e9, (rx2 - rclk) * 1e9, (rs0 - rclk) * 1e9, (rs2 - rclk) * 1e9, (rs0 - rs1) * 1e9))

    overview(w)
    e0 = tclk * 1e9
    zoom(w, "wave_entry_cell0.png", e0 - 0.5, e0 + 3,
         [("clk", "v(clk)", MUTED), ("t0 = clkin", "v(xseq.t0)", INK), ("n1", "v(xseq.xg0.n1)", MUTED),
          ("a1", "v(xseq.xg0.a1)", MUTED), ("p1e = S2", "v(s2_0)", C_S2), ("x1 (delay out)", "v(xseq.xg0.x1)", MUTED),
          ("b1", "v(xseq.xg0.b1)", MUTED), ("p1 = S0", "v(s0_0)", C_S0), ("n2", "v(xseq.xg0.n2)", MUTED),
          ("n2d (delay out)", "v(xseq.xg0.n2d)", MUTED), ("a2", "v(xseq.xg0.a2)", MUTED),
          ("p2e = S1", "v(s1_0)", C_S1)],
         [((4, ts2 * 1e9), (7, ts0 * 1e9), "%.2f ns" % ((ts0 - ts2) * 1e9)),
          ((7, ts0 * 1e9), (11, ts1 * 1e9), "%.2f ns" % ((ts1 - ts0) * 1e9))],
         "Cell 0 at its sampling edge (typical): one clock edge, then the generator orders S2, S0, S1; "
         "each gap = one short delay stage (%d inv_2) + a few gates" % N_STAGE)
    r0 = rclk * 1e9
    zoom(w, "wave_reentry_cell0.png", r0 - 0.5, r0 + 4,
         [("clk", "v(clk)", MUTED), ("t0 = clkin", "v(xseq.t0)", INK), ("a2", "v(xseq.xg0.a2)", MUTED),
          ("p2e = S1", "v(s1_0)", C_S1), ("x2 (delay out)", "v(xseq.xg0.x2)", MUTED), ("b2", "v(xseq.xg0.b2)", MUTED),
          ("a1", "v(xseq.xg0.a1)", MUTED), ("p1e = S2", "v(s2_0)", C_S2), ("p1 = S0", "v(s0_0)", C_S0)],
         [((3, rs1 * 1e9), (8, rs0 * 1e9), "%.2f ns" % ((rs0 - rs1) * 1e9))],
         "Cell 0 when acq returns (typical): S1 (ramp) opens first, S0 / S2 close one delay stage later "
         "(break before make in this direction too)")
    gaps_pvt()
    print("REPORT: wave.py drew assets/wave_overview.png, wave_entry_cell0.png, wave_reentry_cell0.png, gaps_pvt.png")


if __name__ == "__main__":
    main()
