"""Reduce the cell_trannoise runs (ct.sh) to metrics and figures.

    python3 ct_reduce.py      (container, from this block) -> stdout `name = value`,
                              data/ct_summary.json, data/ct_noise.npz,
                              assets/ct_noise.png/.svg, assets/ct_groups.png/.svg

Everything is referred to the ADC input in LSB through the count: a decision
instant moved by dt is dt / TCOUNT LSB (the ramp moves 1 LSB per count).
Per level (c16, c240; POS aligned by ct_align.py so that the noiseless decision
sits on the falling clock edge k = "Clk"):

  sigma       std over every noisy conversion of td (dout's VDD/2 fall), / TCOUNT:
              the total transient noise the conversion sees
  capture     q fell on Clk (code k) or on Clk+1 (code k+1); any other edge is a FAIL.
              frac_clk1 = share on Clk+1; predicted from dout alone = share of td
              after Clk's midpoint, and from the Gaussian 1 - Phi((t_Clk - mean)/sigma)
  match       per conversion: dout fell before Clk's midpoint <=> q fell on Clk.
              A mismatch is possible only inside the latch's aperture (setup); the
              gate counts mismatches with |td - t_Clk| > APERTURE_NS; the best
              boundary (fewest mismatches) is reported as the latch's sampling
              instant on dout's VDD/2 crossing, relative to Clk's midpoint
  groups      the same sigma with one block alone noisy (ramp, cmp, ff, sw); their
              root-sum-square against the total (independent sources add in power)
  plate, ramp diagnostics as ../cell_trannoise_bkp/cell_trannoise (not shares of sigma)
  floor       std of td over the noiseless records / TCOUNT
  xchk        noiseless VACASK against ngspice on the same bench
"""
import glob
import json
import os
import sys
from math import erf, sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ct_common import load_params, fall_edge  # noqa: E402

WORK = os.path.join(HERE, "work")
P0 = load_params()
TC, LSB, VDD = P0["TCOUNT"], P0["LSB"], P0["VDD"]
LEVELS = (("c16", 16.5), ("c240", 240.5))
GROUPS = ("ramp", "cmp", "ff", "sw")
APERTURE_NS = 1.0
SHARE = 0.25
NWAVE_PLOT = 48             # every record of seed 0 (one simulation run)
out = []
summary = {}


def put(key, value, fmt="%.6g"):
    out.append(("%s = " + fmt) % (key, value))
    summary[key] = float(value)


def load(path):
    return np.atleast_1d(np.genfromtxt(path, delimiter=",", names=True))


def seeds(case):
    return sorted(glob.glob(os.path.join(WORK, case, "s*", "r.csv")),
                  key=lambda p: int(os.path.basename(os.path.dirname(p))[1:]))


def Phi(z):
    return 0.5 * (1 + erf(z / sqrt(2)))


def align():
    a = {}
    for line in open(os.path.join(WORK, "align.txt")):
        t, pos, k = line.split()
        a[t] = (float(pos), int(k))
    return a


def good_rows(rows):
    """A conversion counts if dout and q were high at TR, q fell exactly once and
    dout fell (td finite). dout may chatter (noise at the slow crossing); td is its first fall."""
    return (rows["nq"] == 1) & np.isfinite(rows["td"]) & np.isfinite(rows["tq"]) & \
           (rows["d0"] > VDD / 2) & (rows["q0"] > VDD / 2)


def sigma_of(case):
    files = seeds(case)
    if not files:
        return None
    per = [load(f) for f in files]
    rows = np.concatenate(per)
    g = good_rows(rows)
    td = rows["td"][g]
    if td.size < 3:
        return None
    s = float(np.std(td, ddof=1) / TC)
    return {"per": per, "rows": rows, "good": g, "td": td, "sigma": s, "m": int(td.size),
            "se": s / np.sqrt(2 * (td.size - 1)), "seeds": len(per)}


def level(tag, pos0, pos, k):
    P = load_params({"POS": pos})
    tclk = fall_edge(P, k)
    res = {"tag": tag, "pos": pos, "k": k, "tclk": tclk, "ti": (P["VIN"] - P["VR_LO"]) / P["SLOPE"]}
    put("ct_%s_pos" % tag, pos)
    put("ct_%s_pos_shift_lsb" % tag, pos - pos0, "%+.4f")
    put("ct_%s_clk_edge" % tag, k, "%d")
    # ----- noiseless references: ngspice vs VACASK, finger expansion, alignment
    ng, q, q1 = (os.path.join(WORK, c) for c in ("ng_%s/r.csv" % tag, "q_%s/s0/r.csv" % tag, "q1_%s/s0/r.csv" % tag))
    if all(os.path.exists(p) for p in (ng, q, q1)):
        ng, q, q1 = load(ng), load(q), load(q1)
        n = min(ng.size, q.size)
        put("ct_%s_xchk_records" % tag, n, "%d")
        unexplained = 0
        for a, b in zip(ng[:n], q[:n]):
            if a["kq"] == b["kq"]:
                continue
            lo, hi = sorted((a["td"], b["td"]))
            edges = np.array([fall_edge(P, j) for j in range(int(b["kq"]) - 3, int(b["kq"]) + 4)])
            unexplained += int(not np.any((edges > lo - APERTURE_NS * 1e-9) & (edges <= hi + APERTURE_NS * 1e-9)))
        put("ct_%s_xchk_codes_differ" % tag, int(np.sum(ng["kq"][:n] != q["kq"][:n])), "%d")
        put("ct_%s_xchk_codes_unexplained" % tag, unexplained, "%d")
        put("ct_%s_xchk_dtd_lsb" % tag, np.mean(q["td"][:n] - ng["td"][:n]) / TC)
        put("ct_%s_xchk_dtm_mv" % tag, np.mean(q["tm"][:n] - ng["tm"][:n]) * 1e3)
        put("ct_%s_xchk_dslope_pct" % tag, 100 * np.mean(q["slope"][:n] / ng["slope"][:n] - 1))
        put("ct_%s_nf1_dtd_lsb" % tag, np.mean(q1["td"] - q["td"]) / TC)
        put("ct_%s_quiet_td_minus_clk_ns" % tag, (np.mean(q["td"]) - tclk) * 1e9, "%+.4f")
        put("ct_%s_quiet_td_minus_ideal_ns" % tag, (np.mean(q["td"]) - res["ti"]) * 1e9, "%+.4f")
        put("ct_%s_quiet_tx_minus_ideal_ns" % tag, (np.nanmean(q["tx"]) - res["ti"]) * 1e9, "%+.4f")
        put("ct_%s_quiet_code" % tag, q["kq"][0], "%d")
        put("ct_%s_quiet_cq_ns" % tag, np.mean(q["cq"]) * 1e9)
        res["floor"] = float(np.std(q["td"], ddof=1) / TC)
        res["q_td"] = float(np.mean(q["td"]))
        put("ct_%s_floor_lsb" % tag, res["floor"])
    else:
        print("FAIL: %s: missing a noiseless run (ngspice / q / q1)" % tag)
    # ----- noisy runs, every group
    s = sigma_of("n_" + tag)
    if s is None:
        print("FAIL: %s: no noisy runs" % tag)
        return res
    rows, g, td = s["rows"], s["good"], s["td"]
    put("ct_%s_seeds" % tag, s["seeds"], "%d")
    put("ct_%s_conversions" % tag, rows.size, "%d")
    put("ct_%s_bad_conversions" % tag, int((~g).sum()), "%d")
    put("ct_%s_dout_chatter" % tag, int(np.sum(rows["nd"][g] > 1)), "%d")
    put("ct_%s_sigma_lsb" % tag, s["sigma"])
    put("ct_%s_sigma_ci95_lsb" % tag, 1.96 * s["se"])
    put("ct_%s_jitter_ns" % tag, s["sigma"] * TC * 1e9)
    put("ct_%s_sigma_se_seed_lsb" % tag,
        np.std([np.std(r["td"][good_rows(r)], ddof=1) / TC for r in s["per"]], ddof=1) / np.sqrt(len(s["per"])))
    fast = np.concatenate([np.diff(r["td"][good_rows(r)]) for r in s["per"]])
    put("ct_%s_sigma_conv2conv_lsb" % tag, np.std(fast, ddof=1) / np.sqrt(2) / TC)
    put("ct_%s_td_minus_ideal_ns" % tag, (td.mean() - res["ti"]) * 1e9, "%+.4f")
    put("ct_%s_td_minus_clk_ns" % tag, (td.mean() - tclk) * 1e9, "%+.4f")
    if "q_td" in res:
        put("ct_%s_noisy_minus_quiet_lsb" % tag, (td.mean() - res["q_td"]) / TC, "%+.5f")
        put("ct_%s_floor_over_sigma" % tag, res["floor"] / s["sigma"])
    # ----- capture: Clk or Clk+1, and dout <-> q per conversion
    kq = rows["kq"][g]
    on_clk, on_clk1 = kq == k, kq == k + 1
    put("ct_%s_q_on_clk" % tag, int(on_clk.sum()), "%d")
    put("ct_%s_q_on_clk1" % tag, int(on_clk1.sum()), "%d")
    put("ct_%s_q_other_edge" % tag, int((~on_clk & ~on_clk1).sum()), "%d")
    m = td.size
    f1 = on_clk1.mean()
    put("ct_%s_frac_clk1" % tag, f1)
    put("ct_%s_frac_clk1_se" % tag, sqrt(max(f1 * (1 - f1), 1.0 / m) / m))
    put("ct_%s_frac_clk1_dout" % tag, np.mean(td > tclk))
    put("ct_%s_frac_clk1_gauss" % tag, 1 - Phi((tclk - td.mean()) / (s["sigma"] * TC)))
    early = td < tclk
    mism = early != on_clk
    near = np.abs(td - tclk) <= APERTURE_NS * 1e-9
    put("ct_%s_match_mismatch" % tag, int(mism.sum()), "%d")
    put("ct_%s_match_mismatch_outside" % tag, int((mism & ~near).sum()), "%d")
    put("ct_%s_match_near_edge" % tag, int(near.sum()), "%d")
    cand = np.linspace(tclk - 3e-9, tclk + 3e-9, 601)
    nm = np.array([np.sum((td < c) != on_clk) for c in cand])
    best = cand[nm == nm.min()]
    put("ct_%s_match_boundary_ns" % tag, (np.mean(best) - tclk) * 1e9, "%+.4f")
    put("ct_%s_match_boundary_mismatch" % tag, int(nm.min()), "%d")
    put("ct_%s_cq_mean_ns" % tag, np.mean(rows["cq"][g]) * 1e9)
    put("ct_%s_cq_std_ps" % tag, np.std(rows["cq"][g], ddof=1) * 1e12)
    # ----- diagnostics
    alpha = float(np.nanmean(rows["at"][g]))
    put("ct_%s_alpha_trip" % tag, alpha)
    put("ct_%s_plate_tm_uv" % tag, np.std(rows["tm"][g], ddof=1) * 1e6)
    put("ct_%s_plate_diag_lsb" % tag, np.std(rows["tm"][g], ddof=1) / (alpha * LSB))
    put("ct_%s_ramp_diag_lsb" % tag, np.std(rows["vr"][g], ddof=1) / LSB)
    put("ct_%s_ramp_slope_err_pct" % tag, 100 * (np.mean(rows["slope"][g]) / P["SLOPE"] - 1))
    # ----- one group alone noisy
    var = 0.0
    var_se = 0.0
    res["groups"] = {}
    for grp in GROUPS:
        gs = sigma_of("g_%s_%s" % (grp, tag))
        if gs is None:
            print("FAIL: %s: no runs with %s alone noisy" % (tag, grp))
            continue
        put("ct_%s_g_%s_sigma_lsb" % (tag, grp), gs["sigma"])
        put("ct_%s_g_%s_sigma_se_lsb" % (tag, grp), gs["se"])
        put("ct_%s_g_%s_conversions" % (tag, grp), gs["m"], "%d")
        put("ct_%s_g_%s_bad" % (tag, grp), int((~gs["good"]).sum()), "%d")
        put("ct_%s_g_%s_power_share" % (tag, grp), gs["sigma"] ** 2 / s["sigma"] ** 2)
        if "q_td" in res:      # a floating-plate charge leak would move the mean (LOOSE_G groups: reltol 1e-5)
            put("ct_%s_g_%s_dmean_lsb" % (tag, grp), (gs["td"].mean() - res["q_td"]) / TC, "%+.5f")
        res["groups"][grp] = (gs["sigma"], gs["se"])
        var += gs["sigma"] ** 2
        var_se += (2 * gs["sigma"] * gs["se"]) ** 2
    if len(res["groups"]) == len(GROUPS):
        rss = sqrt(var)
        ratio = rss / s["sigma"]
        # se of the ratio: the RSS (power sum) and the total, independent runs
        r_se = ratio * sqrt((sqrt(var_se) / (2 * var)) ** 2 + (s["se"] / s["sigma"]) ** 2)
        put("ct_%s_groups_rss_lsb" % tag, rss)
        put("ct_%s_groups_rss_over_total" % tag, ratio)
        put("ct_%s_groups_rss_over_total_tol" % tag, 3 * r_se)
    res.update(s=s, kq=kq, on_clk1=on_clk1, td=td, rows=rows, good=g)
    return res


def band(r16):
    b = sigma_of("b6_c16")
    if b is None or "s" not in r16:
        print("FAIL: band check: no 6 GHz runs")
        return
    s = r16["s"]
    tol = 3 * np.sqrt(1 / (2 * (b["m"] - 1)) + 1 / (2 * (s["m"] - 1)))
    put("ct_band_conversions", b["m"], "%d")
    put("ct_band_sigma_6g_lsb", b["sigma"])
    put("ct_band_sigma_ratio", b["sigma"] / s["sigma"])
    put("ct_band_tm_ratio", np.std(b["rows"]["tm"][b["good"]], ddof=1) / np.std(s["rows"]["tm"][s["good"]], ddof=1))
    put("ct_band_ratio_tol", tol)


def tol(r240):
    t = sigma_of("tt_c240")
    if t is None or "s" not in r240:
        print("FAIL: reltol check: no reltol 2e-7 runs")
        return
    s = r240["s"]
    put("ct_tol_seeds", t["seeds"], "%d")
    put("ct_tol_conversions", t["m"], "%d")
    put("ct_tol_dmean_lsb", (t["td"].mean() - s["td"].mean()) / TC)
    put("ct_tol_dmean_tol_lsb", 3 * np.hypot(t["sigma"] / np.sqrt(t["m"]), s["sigma"] / np.sqrt(s["m"])))
    put("ct_tol_sigma_ratio", t["sigma"] / s["sigma"])
    put("ct_tol_ratio_tol", 3 * np.sqrt(1 / (2 * (t["m"] - 1)) + 1 / (2 * (s["m"] - 1))))


# ------------------------------------------------------------------------- figures
def figures(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 13,
                         "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "path",
                         "figure.facecolor": "white", "savefig.facecolor": "white"})
    INK, GREY, RED = "#000000", "#7F7F7F", "#C00000"
    C0, C1 = "#0070C0", "#E36C09"          # q on Clk / q on Clk+1
    FS, FS_S, FS_T = 14, 12.5, 11
    r = res["c16"]
    if "s" not in r:
        return
    w = np.load(os.path.join(WORK, "n_c16", "s0", "r.csv.waves.npz"))
    rows0 = r["s"]["per"][0]
    nw = min(NWAVE_PLOT, w["waves"].shape[0], rows0.size)
    good0 = good_rows(rows0)[:nw]
    cls = rows0["kq"][:nw] == r["k"] + 1
    x = (w["grid"] - r["tclk"]) * 1e9
    qw = np.load(os.path.join(WORK, "q_c16", "s0", "r.csv.waves.npz"))
    xq = (qw["grid"] - r["tclk"]) * 1e9
    xi = (r["ti"] - r["tclk"]) * 1e9
    td0 = (rows0["td"][:nw] - r["tclk"]) * 1e9
    # the two conversions closest to the edge on either side: drawn bold
    idx = np.arange(nw)
    pick = []
    for c in (False, True):
        cand = idx[good0 & (cls == c)]
        if cand.size:
            pick.append(int(cand[np.argmin(np.abs(td0[cand]))]))

    fig = plt.figure(figsize=(15.5, 8.2))
    gs = GridSpec(4, 2, figure=fig, width_ratios=[1.75, 1], height_ratios=[1.5, 0.55, 1, 1],
                  hspace=0.13, wspace=0.2)
    XL = (-75, 110)
    ap = fig.add_subplot(gs[0, 0])
    ac = fig.add_subplot(gs[1, 0], sharex=ap)
    ad = fig.add_subplot(gs[2, 0], sharex=ap)
    aq = fig.add_subplot(gs[3, 0], sharex=ap)
    for i in range(nw):
        if not good0[i]:
            continue
        col = C1 if cls[i] else C0
        bold = i in pick
        ap.plot(x, w["waves"][i, 3] * 1e3, color=col, lw=0.35, alpha=0.16)
        ad.plot(x, w["waves"][i, 1], color=col, lw=2.2 if bold else 0.7, alpha=1 if bold else 0.45, zorder=3 if bold else 2)
        aq.plot(x, w["waves"][i, 0], color=col, lw=2.2 if bold else 0.9, alpha=1 if bold else 0.6, zorder=3 if bold else 2)
        ad.plot([td0[i]], [VDD / 2], "o", ms=3.2, color=col, zorder=4)
    ap.plot(xq, qw["waves"][0, 3] * 1e3, color=INK, lw=1.4, ls="--", label="noise off")
    ad.plot(xq, qw["waves"][0, 1], color=INK, lw=1.3, ls="--")
    ac.plot(x, w["waves"][0, 2], color=INK, lw=1.2)
    for a in (ap, ac, ad, aq):
        a.axvline(0, color=C0, lw=1.0, ls=":")
        a.axvline(50, color=C1, lw=1.0, ls=":")
        a.axvline(xi, color=GREY, lw=0.9)
        a.set_xlim(*XL)
        a.tick_params(labelsize=FS_T)
        a.grid(True, color="#E6E6E6", lw=0.7)
    for a in (ap, ac, ad):
        plt.setp(a.get_xticklabels(), visible=False)
    ap.axhline(0, color=GREY, lw=0.7)
    ap.set_ylim(-4.5, 4.5)
    ap.set_ylabel("plate $-$ $V_{REF}$\n(mV)", fontsize=FS_S)
    ap.legend(fontsize=FS_T, frameon=False, loc="upper left")
    ap.text(xi + 1.5, -4.1, "ideal crossing\n$V_{RAMP} = V_{IN}$", fontsize=FS_T, color=GREY, va="bottom")
    ap.text(XL[1] - 2, -4.1, "%d noisy conversions of one input (seed 0)" % int(good0.sum()), ha="right",
            fontsize=FS_T, color=INK)
    ac.set_ylim(-0.4, 3.9)
    ac.set_yticks([0, 3.3])
    ac.set_ylabel("clk (V)", fontsize=FS_S)
    ac.annotate("Clk (edge %d)" % r["k"], xy=(0, 1.65), xytext=(4, 2.6), fontsize=FS_T, color=C0,
                arrowprops=dict(arrowstyle="-", color=C0, lw=0.8))
    ac.annotate("Clk+1", xy=(50, 1.65), xytext=(54, 2.6), fontsize=FS_T, color=C1,
                arrowprops=dict(arrowstyle="-", color=C1, lw=0.8))
    ad.set_ylim(-0.3, 3.6)
    ad.set_ylabel("$D_{OUT}$ (V)", fontsize=FS_S)
    ad.axhline(VDD / 2, color=GREY, lw=0.6, ls="--")
    aq.set_ylim(-0.3, 3.6)
    aq.set_ylabel("latch $Q$ (V)", fontsize=FS_S)
    aq.set_xlabel("$t - t_{Clk}$  (ns);   1 count = 50 ns = 1 LSB", fontsize=FS_S)
    n0, n1 = int(np.sum(good0 & ~cls)), int(np.sum(good0 & cls))          # by the edge that captured
    nd0, nd1 = int(np.sum(good0 & (td0 < 0))), int(np.sum(good0 & (td0 >= 0)))   # by where dout crossed
    ad.text(XL[0] + 2, 0.35, "dout crossed $V_{DD}/2$ (dot, coloured by the edge that captured)\n"
            "before Clk: %d   after Clk: %d   (the latch needs ~%.1f ns before Clk)"
            % (nd0, nd1, -summary["ct_c16_match_boundary_ns"]), fontsize=FS_T, va="bottom")
    aq.text(-2, 1.65, "q falls on Clk\ncode %d  (%d)" % (r["k"], n0), ha="right", va="center", fontsize=FS_T, color=C0)
    aq.text(48, 1.65, "q falls on Clk+1\ncode %d  (%d)" % (r["k"] + 1, n1), ha="right", va="center", fontsize=FS_T, color=C1)
    fig.text(0.125, 0.935, "(a) one input on a code transition: plate, clock, comparator and latch", fontsize=FS)
    fig.text(0.655, 0.935, "(b) where the decision lands, and which edge captures it", fontsize=FS)

    # (b) histograms, one per level, split by the capturing edge
    xs = np.linspace(-0.6, 0.6, 600)
    gr = gs[:, 1].subgridspec(2, 1, hspace=0.32)    # own spacing: the two histograms' axes must not touch
    for row, tag in ((0, "c16"), (1, "c240")):
        rr = res[tag]
        if "s" not in rr:
            continue
        ah = fig.add_subplot(gr[row, 0])
        v = (rr["td"] - rr["tclk"]) / TC
        mu = float(v.mean())
        sg = rr["s"]["sigma"]
        bins = np.linspace(-0.45, 0.45, 37)
        ah.hist([v[~rr["on_clk1"]], v[rr["on_clk1"]]], bins=bins, density=True, stacked=True, color=[C0, C1],
                alpha=0.55, edgecolor="white", lw=0.4, label=["q on Clk (code %d)" % rr["k"], "q on Clk+1 (code %d)" % (rr["k"] + 1)])
        ah.plot(xs, np.exp(-0.5 * ((xs - mu) / sg) ** 2) / (sg * np.sqrt(2 * np.pi)), color=INK, lw=1.8,
                label="Gaussian, $\\sigma$ = %.3f LSB" % sg)
        ah.plot(xs, np.exp(-0.5 * ((xs - mu) / SHARE) ** 2) / (SHARE * np.sqrt(2 * np.pi)), color=RED, lw=1.4,
                ls="--", label="noise share, $\\sigma$ = 0.25 LSB")
        ah.axvline(0, color=INK, lw=0.9, ls=":")
        ah.set_xlim(-0.6, 0.6)
        ah.set_ylim(0, 8.6)          # head room: the legend sits above the Gaussian
        ah.set_yticks([])
        ah.spines["left"].set_visible(False)
        ah.tick_params(labelsize=FS_T)
        if row == 0:             # ns scale once, on top; LSB scale on both
            top = ah.secondary_xaxis("top", functions=(lambda u: u * 50, lambda t: t / 50))
            top.tick_params(labelsize=FS_T)
            top.set_xlabel("ns", fontsize=FS_T, loc="right", labelpad=1)
        else:
            ah.set_xlabel("decision instant $-$ $t_{Clk}$  (LSB)", fontsize=FS_S)
        ah.legend(fontsize=FS_T - 1, frameon=False, loc="upper left", bbox_to_anchor=(-0.02, 1.0))
        f1 = summary["ct_%s_frac_clk1" % tag]
        fd = summary["ct_%s_frac_clk1_dout" % tag]
        ah.text(0.59, 3.6, "mid-code %g, %d conv.\n$\\sigma$ = %.3f LSB = %.1f ns\non Clk+1: %.1f %%\n(dout after Clk: %.1f %%)"
                % ({"c16": 16.5, "c240": 240.5}[tag], v.size, sg, sg * 50, 100 * f1, 100 * fd),
                ha="right", va="center", fontsize=FS_T + 0.5)
    fig.text(0.06, 0.01, "One Analog_top cell (S0/S1/S2 + inverters, 54.5 fF MIM, comparator_d, dfxtn_2 latch) on ramp_simple_d; "
             "VREF = VBL, VR_LO, bias currents, supplies, controls and clock ideal. VACASK transient noise, every device "
             "source (thermal + flicker), 1 kHz-%g GHz, reltol %g, %d seeds."
             % (summary.get("ct_fmax_ghz", 2), summary.get("ct_reltol", 1e-6), int(summary.get("ct_c16_seeds", 0))),
             fontsize=FS_T - 1, color=GREY)
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "assets", "ct_noise." + ext), dpi=200, bbox_inches="tight")
    plt.close(fig)

    # per-block breakdown
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    labels = ["ramp\n(ramp_simple_d)", "comparator\n(comparator_d)", "latch\n(dfxtn_2)", "switches\n+ inverters",
              "RSS of\nthe four", "all on\n(total)"]
    for j, (tag, col) in enumerate((("c16", "#0070C0"), ("c240", "#E36C09"))):
        rr = res[tag]
        if len(rr.get("groups", {})) != len(GROUPS):
            continue
        vals = [rr["groups"][g][0] for g in GROUPS] + [summary["ct_%s_groups_rss_lsb" % tag], rr["s"]["sigma"]]
        errs = [1.96 * rr["groups"][g][1] for g in GROUPS] + [0, 1.96 * rr["s"]["se"]]
        xp = np.arange(len(vals)) + (j - 0.5) * 0.36
        ax.bar(xp, vals, width=0.34, color=col, alpha=0.75, yerr=errs, capsize=3,
               label="mid-code %g" % {"c16": 16.5, "c240": 240.5}[tag])
    ax.axhline(SHARE, color="#C00000", ls="--", lw=1.2, label="noise share 0.25 LSB")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, fontsize=FS_T)
    ax.set_ylabel("$\\sigma$ of the decision (LSB)", fontsize=FS_S)
    ax.legend(fontsize=FS_T, frameon=False)
    ax.grid(True, axis="y", color="#E6E6E6", lw=0.7)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "assets", "ct_groups." + ext), dpi=200, bbox_inches="tight")
    plt.close(fig)

    # the data behind the figure (for ../cpad_talk), decimated waves
    d = {"grid_minus_tclk": (w["grid"][::2] - r["tclk"]).astype(np.float64),
         "waves": w["waves"][:nw, :, ::2].astype(np.float32), "waves_class_clk1": cls,
         "waves_good": good0, "qwave": qw["waves"][0, :, ::2].astype(np.float32),
         "qgrid_minus_tclk": (qw["grid"][::2] - r["tclk"]).astype(np.float64), "ti_minus_tclk": r["ti"] - r["tclk"]}
    for tag in ("c16", "c240"):
        rr = res[tag]
        if "s" in rr:
            d["td_minus_tclk_" + tag] = rr["td"] - rr["tclk"]
            d["clk1_" + tag] = rr["on_clk1"]
            d["k_" + tag] = rr["k"]
    np.savez_compressed(os.path.join(HERE, "data", "ct_noise.npz"), **d)


def main():
    a = align()
    summary["ct_fmax_ghz"] = float(os.environ.get("FMAX", "2e9")) / 1e9
    summary["ct_reltol"] = float(os.environ.get("RELTOL", "1e-6"))
    res = {}
    for tag, pos0 in LEVELS:
        if tag not in a:
            print("FAIL: %s: not aligned" % tag)
            continue
        res[tag] = level(tag, pos0, *a[tag])
    band(res.get("c16", {}))
    tol(res.get("c240", {}))
    put("ct_noise_share_lsb", SHARE)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    for line in out:
        print(line)
    json.dump(summary, open(os.path.join(HERE, "data", "ct_summary.json"), "w"), indent=1, sort_keys=True)
    try:
        figures(res)
        print("REPORT: figures assets/ct_noise.png/.svg, assets/ct_groups.png/.svg")
    except Exception as e:        # a figure must not hide the numbers
        print("FAIL: figures: %s" % e)


if __name__ == "__main__":
    main()
