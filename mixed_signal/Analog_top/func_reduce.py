#!/usr/bin/env python3
"""func_reduce.py -- reduce the functional record of analog_top to scalars.

Reads data/func_measures.txt (the ngspice measures, including the timeline
echoed as p_*) and work/func/wave.csv (tb_measure.inc's wrdata). Writes

  data/func_reduce.txt    `name = value`, read by check-func.awk
  data/func_cells.csv     one row per cell (FUNCTIONAL.md's per-cell table)
  data/func_timeline.csv  event, time, value (FUNCTIONAL.md's timeline)
  work/func/wave.npz      the waveforms for plot_func.py

and echoes every scalar as `name = value` on stdout (summarize-metrics.awk).

What is computed here and not in ngspice, and how:
  settle_<node>_ns   last time before TS0 that the node was more than 1 mV
                     from its value at TS0 (bias, references, vramp at reset)
  dev_<node>_mv      max |v - v(TE)| over [T0, TS0]: was the node already at
                     its final value while the cells tracked and sampled
  i<out>_ts0_ua      bias_gen_s output currents at TS0, read as the drain
                     current of the output devices (sinks XOC0..3 = icmp0..3,
                     XOR = iramp; sources XOV = ivref, XOL = ivrlo (v5: no XOB); XMN1 =
                     core branch); *_ramp_ua the mean over [TR, TE]
  ramp_*             vramp resampled at 5 ns on [TR+100n, TE] (the first
                     100 ns hold the reset-release transient): least-squares
                     line -> slope, gain error vs SLOPE, start; residual ->
                     INL (best-fit and end-point); slope over the first and
                     the last 1.2 us; the kick each decision leaves on vramp
  q_*                VDD/2 crossings of q_k: falls in (TR, TE+TOVR], falls
                     and rises in (TR, TSTOP], falls in the armed window
                     (TS_k+2TNOV+TCOUNT, TR]; dout's minimum over
                     [TS_k+2TNOV+20n, TR]
  latch_*            the first cnt_clk falling edge (mid-edge) after dout's
                     fall, the margin dout had before it, q's delay after it,
                     and whether q fell there (clock-to-q <= 20 ns, cmp_tspc
                     SPEC S4; an edge closer than 2 ns to dout may legally be
                     missed, then the next one counts)
  xfer_*             least-squares line through the four cells of the trip
                     count against the input position POS_k (LSB above
                     VR_LO): gain error, offset at VR_LO, max residual. Done
                     for dout's fall (gated), the analog crossing and the codes
"""
import csv
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WAVE = os.path.join(HERE, "work", "func", "wave.csv")
NPZ = os.path.join(HERE, "work", "func", "wave.npz")
MEAS = os.path.join(HERE, "data", "func_measures.txt")
OUT = os.path.join(HERE, "data", "func_reduce.txt")
CELLS = os.path.join(HERE, "data", "func_cells.csv")
TIMELINE = os.path.join(HERE, "data", "func_timeline.csv")

NAN = float("nan")
TCQ_MAX = 20e-9        # cmp_tspc SPEC S4: clock-to-q <= 20 ns
EDGE_AMBIG = 2e-9      # dout this close before an edge may be caught one edge late
SETTLE_TOL = 1e-3      # 1 mV settling band


def load_meas(path):
    m = {}
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) >= 3 and p[1] == "=":
                try:
                    m[p[0]] = float(p[2])
                except ValueError:
                    m[p[0]] = NAN
    return m


def norm(name):
    s = name.strip().lower()
    if s.startswith("i(") and s.endswith(")"):
        return "i:" + s[2:-1]
    if s.endswith("#branch"):
        return "i:" + s[: -len("#branch")]
    if s.startswith("v(") and s.endswith(")"):
        return s[2:-1]
    return s


def main():
    m = load_meas(MEAS)
    need = ["p_vdd", "p_lsb", "p_slope", "p_tcount", "p_t0", "p_ts0", "p_tr", "p_te", "p_tstop"]
    miss = [k for k in need if k not in m or math.isnan(m[k])]
    if miss:
        print("FAIL: func_reduce: timeline measures missing: " + " ".join(miss))
        return 1
    VDD, LSB, SLOPE, T = m["p_vdd"], m["p_lsb"], m["p_slope"], m["p_tcount"]
    T0, TS0, TR, TE, TSTOP = m["p_t0"], m["p_ts0"], m["p_tr"], m["p_te"], m["p_tstop"]
    TOVR, TNOV, TEDGE, VR_LO = m["p_tovr"], m["p_tnov"], m["p_tedge"], m["p_vr_lo"]
    TSPACE, TSTEP = m["p_tspace"], m["p_tstep"]
    TS = [m["p_ts%d" % k] for k in range(4)]
    POS = [m["p_pos%d" % k] for k in range(4)]
    VIN = [m["p_vin%d" % k] for k in range(4)]
    TH = VDD / 2

    df = pd.read_csv(WAVE, sep=r"\s+")
    cols = {norm(c): c for c in df.columns}
    t = df[cols["time"]].to_numpy(dtype=float)
    # ngspice repeats a time point at breakpoints; keep the last of each
    keep = np.r_[np.diff(t) > 0, True]
    t = t[keep]

    def sig(key):
        return df[cols[key]].to_numpy(dtype=float)[keep]

    S = {}
    for k in ["avdd", "dvdd", "vin", "ramp_rst", "cnt_clk", "xdut.pbias0", "xdut.pbias1", "xdut.pbias2",
              "xdut.pbias3", "xdut.pbias_r", "xdut.vmid", "xdut.vref", "xdut.vramp", "xdut.vrlo"]:
        S[k.replace("xdut.", "")] = sig(k)
    S["vbl"] = S["vref"]            # v5: one buffer, vbl IS the vref net (kept as a name for the reports)
    for c in range(4):
        S["bot%d" % c] = sig("xdut.xc%d.bot" % c)
        S["top%d" % c] = sig("xdut.xc%d.top" % c)
        S["dout%d" % c] = sig("xdut.xc%d.dout" % c)
        S["q%d" % c] = sig("q%d" % c)
        for sw in ("s0", "s1", "s2"):
            S["%s_%d" % (sw, c)] = sig("%s_%d" % (sw, c))
    for k in ["vavdd", "vdvdd", "v.xdut.vmbg", "v.xdut.vmref", "v.xdut.vmvrlo", "v.xdut.vmramp",
              "v.xdut.vmc0", "v.xdut.vmc1", "v.xdut.vmc2", "v.xdut.vmc3"]:
        S["i_" + k.split(".")[-1]] = sig("i:" + k)
    dev = {"icmp0": "xoc0", "icmp1": "xoc1", "icmp2": "xoc2", "icmp3": "xoc3",
           "iramp": "xor", "ivref": "xov", "ivrlo": "xol", "icore": "xmn1"}
    for k, d in dev.items():
        key = "@m.xdut.xbg.%s.m0[id]" % d
        S[k] = np.abs(sig(key)) if key in cols else np.full_like(t, NAN)
    np.savez(NPZ, t=t, **{k: v.astype(np.float32) for k, v in S.items()})

    out = []          # (name, value)

    def put(name, value):
        out.append((name, value))

    def at(x, t0):
        return float(np.interp(t0, t, x))

    def win(t1, t2):
        return (t >= t1) & (t <= t2)

    def uni(x, t1, t2, dt):
        tt = np.arange(t1, t2, dt)
        return tt, np.interp(tt, t, x)

    put("n_timepoints", len(t))

    # ------------------------------------------------------------ power-up
    nodes = ["pbias0", "pbias1", "pbias2", "pbias3", "pbias_r", "vmid", "vref", "vbl", "vrlo", "vramp"]
    for n in nodes:
        x = S[n]
        v0 = at(x, TS0)
        idx = np.where((t <= TS0) & (np.abs(x - v0) > SETTLE_TOL))[0]
        put("settle_%s_ns" % n, (t[idx[-1]] if len(idx) else 0.0) * 1e9)
        w = win(T0, TS0)
        fin = at(x, TR if n == "vramp" else TE)      # vramp: its reset level just before release
        put("dev_%s_mv" % n, float(np.max(np.abs(x[w] - fin))) * 1e3)
    # the ramp current's source must hold still while the ramp runs
    w = win(TR + 100e-9, TE)
    put("pbias_r_ramp_pp_uv", float(np.ptp(S["pbias_r"][w])) * 1e6)

    # ------------------------------------------- references in the sampling
    # window: the vin step at TS_k + TSTEP lands on the top plates of the
    # cells still tracking, whose bottom plates hang on VREF through S2; the
    # shared divider tap carries it to VBL. Deviation from the final value
    # at each sample instant, the peak, and when the tap is back within
    # 0.1 LSB after the last step.
    for n in ("vref", "vbl", "vmid"):
        fin = at(S[n], TE)
        for c in range(4):
            put("%s_dev_ts%d_mv" % (n, c), (at(S[n], TS[c]) - fin) * 1e3)
        w = win(TS0, TR)
        put("%s_kick_pk_mv" % n, float(np.max(np.abs(S[n][w] - fin))) * 1e3)
        idx = np.where(w & (np.abs(S[n] - fin) > 0.1 * LSB))[0]
        put("%s_recover_ns" % n, (t[idx[-1]] - (TS[3] - TSPACE + TSTEP)) * 1e9 if len(idx) else 0.0)

    # ------------------------------------------------------- bias currents
    for k in dev:
        put("%s_ts0_ua" % k, at(S[k], TS0) * 1e6)
        put("%s_ramp_ua" % k, float(np.mean(uni(S[k], TR, TE, 5e-9)[1])) * 1e6)

    # ---------------------------------------------------------------- ramp
    tt, vv = uni(S["vramp"], TR + 100e-9, TE, 5e-9)
    a, b = np.polyfit(tt - TR, vv, 1)
    put("ramp_slope_vpus", a * 1e-6)
    put("ramp_gain_err_pct", (a / SLOPE - 1) * 100)
    put("ramp_start_v", b)
    put("ramp_start_lsb", (b - VR_LO) / LSB)
    put("ramp_release_step_mv", (b - m.get("vramp_at_tr", NAN)) * 1e3)
    res = vv - (a * (tt - TR) + b)
    put("ramp_inl_bf_lsb", float(np.max(np.abs(res))) / LSB)
    ve = vv[0] + (vv[-1] - vv[0]) * (tt - tt[0]) / (tt[-1] - tt[0])
    put("ramp_inl_ep_lsb", float(np.max(np.abs(vv - ve))) / LSB)
    i_max = int(np.argmax(np.abs(res)))
    put("ramp_inl_bf_at_code", (tt[i_max] - TR) / T)
    for name, t1, t2 in (("start", TR + 100e-9, TR + 1.3e-6), ("end", TE - 1.2e-6, TE)):
        t_, v_ = uni(S["vramp"], t1, t2, 5e-9)
        put("ramp_slope_%s_vpus" % name, np.polyfit(t_, v_, 1)[0] * 1e-6)
    r_ = dict(out)
    put("ramp_bow_pct", (r_["ramp_slope_end_vpus"] / r_["ramp_slope_start_vpus"] - 1) * 100)
    # crossing count predicted by the ramp alone: (vin - start)/slope
    put("ramp_counts_to_hi", (m["p_vr_hi"] - b) / a / T)
    put("ramp_gain_xfer_pct", (SLOPE / a - 1) * 100)

    # -------------------------------------------------------------- cells
    rows = []
    edges_fall = lambda n: TR + (n + 0.5) * T + TEDGE / 2
    for c in range(4):
        q, dout = S["q%d" % c], S["dout%d" % c]
        g = lambda k_: m.get("%s%d" % (k_, c), NAN)
        # q edges after TR
        w = t > TR
        s = (q[w] > TH).astype(int)
        d = np.diff(s)
        tw = t[w][1:]
        falls_all = int(np.sum(d == -1))
        rises_all = int(np.sum(d == 1))
        falls_win = int(np.sum((d == -1) & (tw <= TE + TOVR)))
        put("q_falls%d" % c, falls_win)
        put("q_falls_all%d" % c, falls_all)
        put("q_rises_all%d" % c, rises_all)
        # armed: nothing decides between the S1 connection and TR
        t_arm = TS[c] + 2 * TNOV
        w = win(t_arm + T, TR)
        s = (q[w] > TH).astype(int)
        put("q_falls_pre%d" % c, int(np.sum(np.diff(s) == -1)))
        put("q_min_pre%d" % c, float(np.min(q[w])))
        w = win(t_arm + 20e-9, TR)
        put("dout_min_pre%d" % c, float(np.min(dout[w])))
        tq = g("t_q")
        if not math.isnan(tq):
            w = win(tq + 5e-9, TSTOP)
            put("q_max_after%d" % c, float(np.max(q[w])))
        # latch: the first falling edge after dout
        td = g("t_dout")
        if math.isnan(td) or math.isnan(tq):
            put("latch_ok%d" % c, 0)
            margin = tcq = n_e = NAN
        else:
            n_e = math.ceil((td - TR - 0.5 * T - TEDGE / 2) / T)
            te_ = edges_fall(n_e)
            margin = te_ - td
            tcq = tq - te_
            ok = 0 < tcq <= TCQ_MAX
            if not ok and margin < EDGE_AMBIG and 0 < tcq - T <= TCQ_MAX:
                ok = True
                n_e += 1
                tcq -= T
            put("latch_ok%d" % c, int(ok))
        put("latch_edge%d" % c, n_e)
        put("latch_margin%d_ns" % c, margin * 1e9)
        put("latch_tcq%d_ns" % c, tcq * 1e9)
        rows.append(dict(
            cell=c, pos_lsb=POS[c], vin_v=VIN[c],
            vtop_ts_v=g("vtop_ts"), vbot_ts_v=g("vbot_ts"), ped_bot_mv=g("ped_bot") * 1e3,
            vbot_con_v=g("vbot_con"), vtop_con_v=g("vtop_con"), vbot_tr_v=g("vbot_tr"),
            alpha=g("alpha"), t_bot_rel_ns=(g("t_bot") - TR) * 1e9, t_dout_rel_ns=(td - TR) * 1e9,
            cmp_delay_ns=g("cmp_delay") * 1e9, dout_tf_ns=g("dout_tf") * 1e9,
            t_q_rel_ns=(tq - TR) * 1e9, latch_margin_ns=margin * 1e9, latch_tcq_ns=tcq * 1e9,
            code=g("code"), code_ideal=g("code_ideal"), code_err=g("code_err"),
            err_x_lsb=g("err_x"), err_d_lsb=g("err_d"), bps_err_lsb=g("bps_err"),
            refd_mv=g("refd") * 1e3, q_falls=falls_win))

    # ramp kick left by each decision (residual step across dout's fall)
    ttr, vvr = uni(S["vramp"], TR + 100e-9, TE + TOVR, 1e-9)
    resr = vvr - (a * (ttr - TR) + b)
    for c in range(4):
        td = m.get("t_dout%d" % c, NAN)
        if math.isnan(td):
            put("ramp_kick%d_mv" % c, NAN)
            continue
        pre = resr[(ttr > td - 150e-9) & (ttr < td - 30e-9)]
        post = resr[(ttr > td + 30e-9) & (ttr < td + 150e-9)]
        put("ramp_kick%d_mv" % c, (np.mean(post) - np.mean(pre)) * 1e3 if len(pre) and len(post) else NAN)

    # VBL - VREF as the comparator sees it, per cell
    refd = [m.get("refd%d" % c, NAN) for c in range(4)]
    put("refd_spread_mv", (max(refd) - min(refd)) * 1e3)
    put("refd_mean_mv", float(np.mean(refd)) * 1e3)
    al = [m.get("alpha%d" % c, NAN) for c in range(4)]
    put("alpha_min", min(al))
    put("alpha_max", max(al))

    # transfer: trip count vs input position, four cells
    x = np.array(POS)
    for tag, key in (("d", "t_dout"), ("x", "t_bot"), ("q", "t_q")):
        y = np.array([(m.get("%s%d" % (key, c), NAN) - TR) / T for c in range(4)])
        if tag == "q":
            y = np.array([m.get("code%d" % c, NAN) for c in range(4)])
        if np.any(np.isnan(y)):
            put("xfer_%s_gain_err_pct" % tag, NAN)
            continue
        gg, oo = np.polyfit(x, y, 1)
        r = y - (gg * x + oo)
        put("xfer_%s_gain_err_pct" % tag, (gg - 1) * 100)
        put("xfer_%s_offset_lsb" % tag, oo)
        put("xfer_%s_res_max_lsb" % tag, float(np.max(np.abs(r))))
        for c in range(4):
            put("xfer_%s_res%d_lsb" % (tag, c), float(r[c]))

    # VR_LO from vrlo_ref (v4): the level against 5/33 AVDD, what the S1 charge
    # leaves on vramp at TR, and how far vrlo moves over the record
    put("vrlo_tr_v", m.get("vrlo_at_tr", NAN))
    put("vrlo_err_tr_mv", m.get("vrlo_err_tr", NAN) * 1e3)
    put("vrlo_err_tr_lsb", m.get("vrlo_err_tr", NAN) / LSB)
    put("vramp_vrlo_tr_uv", m.get("vramp_vrlo_tr", NAN) * 1e6)
    put("vramp_vrlo_tr_lsb", m.get("vramp_vrlo_tr", NAN) / LSB)
    put("vrlo_pp_conv_mv", (m.get("vrlo_max_conv", NAN) - m.get("vrlo_min_conv", NAN)) * 1e3)

    # power during the ramp, uW
    for k in ("pw_total", "pw_avdd", "pw_dvdd", "pw_bg", "pw_ref", "pw_vrlo", "pw_ramp", "pw_cells",
              "pw_c0", "pw_c1", "pw_c2", "pw_c3", "pw_avdd_idle", "pw_dvdd_idle", "pw_bg_idle",
              "pw_ref_idle", "pw_vrlo_idle", "pw_ramp_idle", "pw_cells_idle", "pw_c0_post"):
        put(k + "_uw", m.get(k, NAN) * 1e6)

    # ------------------------------------------------------------- output
    with open(OUT, "w") as f:
        for k, v in out:
            line = "%s = %s" % (k, fmt(v))
            f.write(line + "\n")
            print(line)
    with open(CELLS, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: fmt(v) for k, v in r.items()})
    ev = [("avdd at 90 %", m.get("t_avdd90", NAN), "", "supply ramp 0 -> 3.3 V in TPWR")]
    for n in nodes:
        ev.append(("%s settled to 1 mV" % n, dict(out)["settle_%s_ns" % n] * 1e-9, m.get("%s_at_ts0" % n, NAN),
                   "value at TS0"))
    ev.append(("T0", T0, "", "bias, references and ramp reset settled (tb_params.inc)"))
    for c in range(4):
        ev.append(("TS%d: S2_%d opens (sample)" % (c, c), TS[c], m.get("vbot_ts%d" % c, NAN), "bot_%d at TS" % c))
        ev.append(("S0_%d opens" % c, TS[c] + TNOV, m.get("vtop_iso%d" % c, NAN), "top_%d before S1" % c))
        ev.append(("S1_%d closes" % c, TS[c] + 2 * TNOV, m.get("vbot_con%d" % c, NAN), "bot_%d 20 ns after" % c))
    ev.append(("TR: ramp_rst falls, count 0", TR, m.get("vramp_at_tr", NAN), "vramp"))
    for c in range(4):
        ev.append(("cell %d: bot crosses vbl" % c, m.get("t_bot%d" % c, NAN), m.get("vtop_bot%d" % c, NAN), "vramp (= top)"))
        ev.append(("cell %d: dout falls" % c, m.get("t_dout%d" % c, NAN), m.get("cmp_delay%d" % c, NAN), "comparator delay"))
        ev.append(("cell %d: q falls" % c, m.get("t_q%d" % c, NAN), m.get("code%d" % c, NAN), "code"))
    ev.append(("vramp reaches VR_HI", m.get("t_ramp_hi", NAN), m.get("n_ramp_hi", NAN), "counts after TR"))
    ev.append(("TE", TE, m.get("vramp_at_te", NAN), "vramp"))
    ev.append(("TE + TOVR", TE + TOVR, m.get("vramp_at_tovr", NAN), "vramp"))
    ev.sort(key=lambda e: (e[1] if not math.isnan(e[1]) else 1e9))
    with open(TIMELINE, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["event", "t_us", "value", "comment"])
        for e in ev:
            wr.writerow([e[0], fmt(e[1] * 1e6), fmt(e[2]) if e[2] != "" else "", e[3]])
    return 0


def fmt(v):
    if isinstance(v, (int, np.integer)):
        return "%d" % v
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if math.isnan(v):
        return "nan"
    return "%.7g" % v


if __name__ == "__main__":
    sys.exit(main())
