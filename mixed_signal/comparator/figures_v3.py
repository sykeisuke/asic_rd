"""The REPORT.md figures of comparator that report_data.py does not draw.

    ./container.sh 'python3 figures_v3.py'

From the recorded data (no re-sizing):
  fig_gmid_sizing.png      short-L gm/Id curves (ID/W, gm/gds) with the selected devices' operating points
  fig_device_noise.png     the device noise characterization behind the noise model (1/f area-normalised, gamma)
  fig_delay_power.png      delay from the trip against power: feasible, fails-only-delay, ngspice front points
  fig_mc.png               sigma(Vos) per corner (ngspice, VACASK), the typical sample histogram, the in-cell code offset
  fig_offset_lin.png       per-sample code offset against the input level at three cells
  fig_bias_req.png         delay against bias scale at the ss cells, deck and drawn geometry
Two small simulations, run only when their data are missing:
  fig_waveforms.png        top, outa, bst, outb, dout through the decision (tb_sel at 40.5 LSB)  -> data/waveform.csv
  (MC samples)             the typical 200-sample ngspice MC with its samples kept             -> data/mc_samples_typ.csv
"""
import csv
import json
import os
import subprocess
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import size_v3 as S  # noqa: E402

B = S.BLOCK
D = lambda *p: os.path.join(B, "data", *p)
A = lambda n: os.path.join(B, "assets", n)
BLUE, ORANGE, AQUA, VIOLET, RED, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7", "#e34948", "#b9b8b2"
LSHADE = {0.28: "#cde2fb", 0.30: "#9ec5f4", 0.32: "#5598e7", 0.34: "#256abf", 0.36: "#0d366b"}
SEL = json.load(open(D("sizing.json")))
ALPHA = SEL["alpha"]


def rows(name):
    p = D(name)
    if not os.path.exists(p):
        return []
    out = []
    for r in csv.DictReader(open(p)):
        rr = {}
        for k, v in r.items():
            try:
                rr[k] = float(v)
            except ValueError:
                rr[k] = v
        out.append(rr)
    return out


def tidy(ax, title, xl, yl):
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_xlabel(xl, fontsize=9)
    ax.set_ylabel(yl, fontsize=9)
    ax.grid(alpha=0.3, which="both")
    ax.tick_params(labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(A(name), dpi=140)
    plt.close(fig)
    print(f"INFO: wrote assets/{name}")


def design():
    s = {k: SEL[k] for k in S.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    return s


# ------------------------------------------------------------------ gm/Id sizing
def fig_gmid():
    from pygmid import Lookup as lk
    p, n = lk(S.LUT_DIR + "/pfet_03v3.pkl"), lk(S.LUT_DIR + "/nfet_03v3.pkl")
    g = np.linspace(4, 24, 81)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    for tbl, ls, name in ((p, "-", "pfet"), (n, "--", "nfet")):
        for L in S.L_CHOICES:
            vds = 1.0 if name == "pfet" else 0.8
            j = np.asarray(tbl.look_up("ID_W", GM_ID=g, L=L, VDS=vds, VSB=0.0)).ravel()
            a = np.asarray(tbl.look_up("GM_GDS", GM_ID=g, L=L, VDS=vds, VSB=0.0)).ravel()
            lab = f"{name} L {L:g} um" if name == "pfet" or L in (0.28, 0.36) else None
            axs[0].semilogy(g, j, ls, c=LSHADE[round(L, 2)], lw=1.4, label=lab)
            axs[1].plot(g, a, ls, c=LSHADE[round(L, 2)], lw=1.4, label=lab)
    # the selected devices' operating points
    pts = [("pair (pfet, L %.2f)" % SEL["l_in"], SEL["gmid_in"], SEL["id_branch"] / (SEL["nf_in"] * SEL["w_fp"]), p, SEL["l_in"], ORANGE, "o"),
           ("load / XBUF1,3 (nfet, L %.2f)" % SEL["l_ld"], SEL["gmid_ld"], SEL["id_branch"] / (SEL["nf_ld"] * SEL["w_fn"]), n, SEL["l_ld"], AQUA, "s"),
           ("tail / starve / ref (pfet, L %.2f)" % SEL["l_b"], SEL["gmid_b"], SEL["j_b"], p, SEL["l_b"], VIOLET, "D")]
    for lab, gm, j, tbl, L, c, mk in pts:
        a = float(np.asarray(tbl.look_up("GM_GDS", GM_ID=np.array([gm]), L=L, VDS=1.0, VSB=0.0)).ravel()[0])
        axs[0].scatter([gm], [j], s=90, c=c, marker=mk, edgecolors="k", zorder=5, label=lab)
        axs[1].scatter([gm], [a], s=90, c=c, marker=mk, edgecolors="k", zorder=5)
        axs[0].annotate("%.1f S/A\n%.2f A/m" % (gm, j), (gm, j), textcoords="offset points", xytext=(8, 6), fontsize=7.5)
    tidy(axs[0], "Current density against gm/Id (short-L tables, lut/)", "gm/Id [S/A]", "ID/W [A/m]")
    tidy(axs[1], "Intrinsic gain against gm/Id", "gm/Id [S/A]", "gm/gds [V/V]")
    axs[0].legend(fontsize=7, ncol=2)
    save(fig, "fig_gmid_sizing.png")


def fig_noise_dev():
    r = rows("device_noise.csv")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.0))
    for dev, mk in (("nfet", "s"), ("pfet", "o")):
        for L in S.L_CHOICES:
            rr = [x for x in r if x["dev"] == dev and abs(x["l_um"] * 1e6 - L) < 1e-3 and x["gm"] / x["id"] > 2]
            gm_id = np.array([x["gm"] / x["id"] for x in rr])
            s1k = np.array([x["s1k"] ** 2 - x["s100m"] ** 2 for x in rr]) * 2e-6 * L * 1e-6   # V^2/Hz * m^2
            gam = np.array([x["s100m"] ** 2 * x["gm"] / (4 * S.KT) for x in rr])
            o = np.argsort(gm_id)
            axs[0].semilogy(gm_id[o], np.sqrt(s1k[o]) * 1e6 * 1e6, marker=mk, ms=3, lw=1, c=LSHADE[round(L, 2)],
                            label=f"{dev} L {L:g}" if L in (0.28, 0.36) else None)
            axs[1].plot(gm_id[o], gam[o], marker=mk, ms=3, lw=1, c=LSHADE[round(L, 2)])
    tidy(axs[0], "1/f: gate-referred density at 1 kHz x sqrt(W L) (ngspice .noise, W = 2 um)", "gm/Id [S/A]",
         "sqrt(S_vg(1 kHz) W L) [uV um / rtHz]")
    tidy(axs[1], "Thermal: gamma = S_vg gm / 4kT (100 MHz, flicker removed)", "gm/Id [S/A]", "gamma")
    axs[0].legend(fontsize=7)
    axs[1].set_ylim(0, 2)
    save(fig, "fig_device_noise.png")


def fig_delay_power():
    feas, fdel, stb = rows("stage_a_feasible.csv"), rows("stage_a_fails_only_delay.csv"), rows("stage_b.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    c = lambda rs, k, s=1.0: np.array([x[k] * s for x in rs])
    ax.scatter(c(fdel, "power", 1e6), c(fdel, "delay_c", 1e9), s=4, c="#efb5b3", label="meets all but the delay (calibrated model)")
    ax.scatter(c(feas, "power", 1e6), c(feas, "delay_c", 1e9), s=4, c=GREY, label="feasible (calibrated model)")
    ax.scatter(c(stb, "power", 1e6), c(stb, "plat_delay_dyn", 1e9), s=36, marker="^", c=BLUE, label="ngspice, front points")
    ax.scatter([SEL["power"] * 1e6], [SEL["spice_plat_delay_dyn"] * 1e9], s=220, marker="*", c=ORANGE, edgecolors="k",
               label="selected f003", zorder=5)
    ax.axhline(12.5, c="k", ls="--", lw=1)
    ax.text(42, 12.8, "1/4 count = 12.5 ns", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(40, 340)
    ax.set_ylim(0, 30)
    tidy(ax, "Delay from the static trip against power", "power, worst static state [uW]", "delay [ns]")
    ax.legend(fontsize=7.5)
    save(fig, "fig_delay_power.png")


# ------------------------------------------------------------------ waveforms (one ngspice run)
def waveform():
    if os.path.exists(D("waveform.csv")):
        return
    d = os.path.join(B, "work", "wave")
    os.makedirs(d, exist_ok=True)
    c = S.common_subs(design(), d)
    lvl = 40.5
    c.update(VIN="%.9g" % (S.VR_LO + lvl * S.LSB), TSTOP="%.6g" % (400e-9 + lvl * S.TCOUNT + 400e-9), VTRIP="%.6f" % SEL["spice_plat_vtrip_v"])
    text = open(os.path.join(B, "tb_sel.spice")).read()
    for k, v in c.items():
        text = text.replace(f"@{k}@", v)
    text = text.replace("let hi90 = ", "wrdata wave.csv v(top) v(xdut.outa) v(xdut.bst) v(xdut.outb) v(dout) i(vdd_source)\nlet hi90 = ", 1)
    text = text.replace("set wr_singlescale", "set wr_singlescale\nset wr_vecnames", 1)
    open(os.path.join(d, "tb.spice"), "w").write(text)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    subprocess.run(["ngspice", "-b", "-o", "tb.out", "tb.spice"], cwd=d, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    raw = np.loadtxt(os.path.join(d, "wave.csv"), skiprows=1)
    np.savetxt(D("waveform.csv"), raw[::4], delimiter=",", header="t,top,outa,bst,outb,dout,i_vdd", comments="", fmt="%.6g")
    print("INFO: wrote data/waveform.csv")


def fig_waveforms():
    w = np.loadtxt(D("waveform.csv"), delimiter=",", skiprows=1)
    t, top, outa, bst, outb, dout, ivdd = w.T
    after = t > 400e-9                            # the ramp starts at TR; before TS the top plate sits at VREF = VBL
    tc = t[after][np.argmax(top[after] >= S.VDD / 2)]   # top crosses VBL
    x = (t - tc) * 1e9
    m = (x > -400) & (x < 60)
    fig, axs = plt.subplots(2, 1, figsize=(9.5, 6.4), sharex=True, gridspec_kw=dict(height_ratios=[1, 2]))
    axs[0].plot(x[m], (top[m] - S.VDD / 2) * 1e3, c=BLUE, lw=1.5)
    axs[0].axhline(0, c="k", lw=0.6)
    axs[0].axhline((SEL["spice_plat_vtrip_v"] - S.VDD / 2) * 1e3, c=ORANGE, lw=1, ls="--")
    axs[0].text(-395, (SEL["spice_plat_vtrip_v"] - S.VDD / 2) * 1e3 + 0.5, "static trip", fontsize=8, color=ORANGE)
    tidy(axs[0], "Top plate against VBL (the attenuated 8-bit ramp), 40.5 LSB, typical", "", "top - VBL [mV]")
    axs[0].set_ylim(-25, 10)
    for y, c, lab in ((outa, ORANGE, "outa (OTA)"), (bst, VIOLET, "bst (starve node)"), (outb, AQUA, "outb (starved inverter)"),
                      (dout, BLUE, "dout (into 10 fF)")):
        axs[1].plot(x[m], y[m], c=c, lw=1.6, label=lab)
    axs[1].axvline(0, c="k", lw=0.6)
    axs[1].axvline(SEL["spice_plat_delay_vbl"] * 1e9, c=GREY, lw=1, ls=":")
    tidy(axs[1], "Internal nodes through the decision (t = 0: top crosses VBL)", "time from the VBL crossing [ns]", "V")
    axs[1].legend(fontsize=8, loc="center left")
    save(fig, "fig_waveforms.png")


# ------------------------------------------------------------------ Monte Carlo
def mc_samples():
    if os.path.exists(D("mc_samples_typ.csv")):
        return
    import verify_v3 as V
    V.N_MC = 200
    nom, ks = V.mc(design())
    np.savetxt(D("mc_samples_typ.csv"), ks, header="vos_v", comments="", fmt="%.6g")
    print(f"INFO: wrote data/mc_samples_typ.csv ({ks.size} samples, sigma {np.std(ks, ddof=1)*1e3:.3f} mV)")


def fig_mc():
    ng, va = rows("mc_pvt.csv"), rows("vmc.csv")
    ks = np.loadtxt(D("mc_samples_typ.csv"), skiprows=1)
    lin = [r for r in rows("offset_lin.csv") if r["sample"] > 0 and np.isfinite(r["code_offset_lsb"])]
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    tags = [r["tag"] for r in ng]
    x = np.arange(len(tags))
    vs = []
    for t in tags:
        c, tt, v = t.split("_")
        m = [r for r in va if r["corner"] == c and r["temp"] == float(tt) and r["vdd"] == float(v)]
        vs.append(m[0]["vos_sigma_v"] / ALPHA / S.LSB if m else np.nan)
    axs[0].bar(x - 0.2, [r["sigma_lsb"] for r in ng], 0.38, color=BLUE, label="ngspice, 100 / cell")
    axs[0].bar(x + 0.2, vs, 0.38, color=ORANGE, label="VACASK, 500 / cell")
    axs[0].axhline(4 / 3, c="k", ls="--", lw=1)
    axs[0].text(-0.4, 4 / 3 + 0.05, "contract 4/3 LSB (accepted above it, ADR 0015)", fontsize=7.5)
    axs[0].set_xticks(x)
    axs[0].set_xticklabels([t.replace("_", "\n") for t in tags], fontsize=7)
    tidy(axs[0], "sigma(Vos) at the ADC input, 7 corner cells", "", "LSB")
    axs[0].legend(fontsize=7.5, loc="lower right")
    axs[0].set_ylim(0, 2.6)
    v = ks / ALPHA / S.LSB
    axs[1].hist(v, bins=25, color=BLUE, alpha=0.85)
    xs = np.linspace(v.min(), v.max(), 200)
    sd = np.std(v, ddof=1)
    axs[1].plot(xs, len(v) * (v.max() - v.min()) / 25 * np.exp(-0.5 * ((xs - v.mean()) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)),
                c=ORANGE, lw=1.5)
    tidy(axs[1], "Static Vos, typical, %d samples: sigma %.2f LSB" % (len(v), sd), "Vos / alpha [LSB]", "samples")
    for cell, c in (("typical_27_3.3", BLUE), ("ss_85_3", ORANGE), ("ff_85_3.6", AQUA)):
        off = {}
        for r in lin:
            if r["cell"] == cell:
                off.setdefault(int(r["sample"]), []).append(r["code_offset_lsb"])
        means = np.array([np.mean(o) for o in off.values()])
        axs[2].hist(means, bins=np.arange(-6, 14, 1.0), histtype="step", lw=1.8, color=c,
                    label="%s: mean %+.1f, sigma %.1f" % (cell, means.mean(), np.std(means, ddof=1)))
    tidy(axs[2], "In-cell code offset (charge path, 30 samples / cell)", "code offset [LSB]", "samples")
    axs[2].legend(fontsize=7)
    save(fig, "fig_mc.png")


def fig_offset_lin():
    lin = [r for r in rows("offset_lin.csv") if np.isfinite(r["code_offset_lsb"])]
    cells = ["typical_27_3.3", "ss_85_3", "ff_85_3.6"]
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.0), sharey=True)
    for ax, cell in zip(axs, cells):
        by = {}
        for r in lin:
            if r["cell"] == cell:
                by.setdefault(int(r["sample"]), []).append((r["level_lsb"], r["code_offset_lsb"]))
        worst = 0
        for k, pts in by.items():
            pts.sort()
            lv, of = zip(*pts)
            worst = max(worst, max(of) - min(of)) if k else worst
            ax.plot(lv, of, "-o", ms=3, lw=1.2, c=ORANGE if k == 0 else BLUE, alpha=1 if k == 0 else 0.55, zorder=5 if k == 0 else 1)
        ax.set_xscale("log")
        tidy(ax, "%s: worst level dependence %.4f LSB" % (cell, worst), "input level above VR_LO [LSB]",
             "code offset [LSB]" if cell == cells[0] else "")
    axs[0].plot([], [], c=BLUE, label="one mismatch sample (same draw at every level)")
    axs[0].plot([], [], c=ORANGE, label="nominal (no mismatch)")
    axs[0].legend(fontsize=7.5, loc="upper left")
    save(fig, "fig_offset_lin.png")


def fig_bias_req():
    br = rows("bias_req.csv")
    scales = sorted(float(k.split("_x")[1]) for k in br[0] if k.startswith("delay_x"))
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, geom in zip(axs, (0, 1)):
        for r in br:
            if r["geom"] != geom:
                continue
            d = [r["delay_x%g" % s] * 1e9 for s in scales]
            ss = r["tag"].startswith("ss")
            ax.plot(scales, d, "-", lw=1.6 if ss else 0.8, c=ORANGE if ss else GREY, alpha=1 if ss else 0.6,
                    label=None)
        ax.axhline(12.5, c="k", ls="--", lw=1)
        ax.axvline(1.0, c=GREY, ls=":", lw=1)
        req = max(r["req_scale"] for r in br if r["geom"] == geom)
        ax.axvline(req, c=ORANGE, ls="--", lw=1)
        ax.text(req + 0.01, 15.5, "needs %.2fx at ss / 85 C" % req, fontsize=8, color=ORANGE)
        tidy(ax, "Delay against bias, 45 PVT cells, " + ("drawn S/D geometry" if geom else "controlled deck"),
             "bias current / nominal 1.931 uA per finger", "delay from the trip [ns]" if not geom else "")
    axs[0].plot([], [], c=ORANGE, lw=1.6, label="ss cells")
    axs[0].plot([], [], c=GREY, lw=0.8, label="other cells")
    axs[0].legend(fontsize=8)
    axs[0].set_ylim(6, 16)
    save(fig, "fig_bias_req.png")


def main():
    fig_gmid()
    fig_noise_dev()
    fig_delay_power()
    waveform()
    fig_waveforms()
    mc_samples()
    fig_mc()
    fig_offset_lin()
    fig_bias_req()
    print("PASS: figures_v3 complete")


if __name__ == "__main__":
    main()
