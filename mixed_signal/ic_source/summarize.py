#!/usr/bin/env python3
"""summarize.py op|pvt|mc -- aggregate the reduced case lines of work/cases/<tag>/red.txt
into the phase's `name = value` and REPORT: lines (and data/<phase>.csv)."""
import glob
import math
import os
import sys

import numpy as np

import ic_common as ic

ph = sys.argv[1]


def cases(prefix):
    out = {}
    for f in sorted(glob.glob(os.path.join(ic.BLOCK, "work", "cases", prefix + "*", "red.txt"))):
        tag = os.path.basename(os.path.dirname(f))
        d = {}
        for line in open(f):
            if " = " in line:
                k, v = line.split(" = ", 1)
                k = k[len(tag) + 1:]
                try:
                    d[k] = float(v)
                except ValueError:
                    d[k] = v.strip()
        if d:
            out[tag] = d
    return out


if ph == "op":
    c = cases("")
    c = {k: v for k, v in c.items() if k in ("nom", "rlo", "rhi", "d45", "d55", "v30", "v36", "mss", "mff", "slow", "fast",
                                              "rhis", "rhiw", "rhif")}
    g = lambda t, k: c[t][k]
    # output resistance from the three ramp levels
    i_lo, i_hi = g("rlo", "i_out_ua") * 1e-6, g("rhi", "i_out_ua") * 1e-6
    span = ic.V_RAMP_HI - ic.V_RAMP_LO
    rout = span / abs(i_lo - i_hi) if i_lo != i_hi else 1e12
    print("op_rout_gohm = %.6g" % (rout * 1e-9))
    i_mid = g("nom", "i_out_ua") * 1e-6
    bow = span / (i_mid * rout) * 256 / 8          # [D] ramp_simple R6: V_swing / (I r_out) x 32 LSB
    print("op_bow_est_lsb = %.6g" % bow)
    # headroom with the ramp at its top (ADR 0025: 2.156 V x AVDD / 3.3) at typical and three corners
    tops = [t for t in ("rhi", "rhis", "rhiw", "rhif") if t in c]
    if tops:
        wt = min(tops, key=lambda t: g(t, "hr_min_mv"))
        print("op_hr_top_min_mv = %.6g" % g(wt, "hr_min_mv"))
        print("REPORT: op headroom at the ramp top (mV): " + ", ".join("%s %.0f" % (t, g(t, "hr_min_mv")) for t in tops)
              + "; worst %s" % wt)
    print("op_duty_sens_pct_per_pct = %.6g" % ((g("d55", "i_err_pct") - g("d45", "i_err_pct")) / 10.0))
    print("op_vdd_dev_pct = %.6g" % max(abs(g("v30", "i_err_pct") - g("nom", "i_err_pct")), abs(g("v36", "i_err_pct") - g("nom", "i_err_pct"))))
    print("op_mim_track_err_pct = %.6g" % max(abs(g("mss", "i_err_pct") - g("nom", "i_err_pct")), abs(g("mff", "i_err_pct") - g("nom", "i_err_pct"))))
    print("op_ripple_ramp_lsb = %.6g" % (g("nom", "i_out_pp_na") * 1e-9 / (ic.F_CLK * ic.ramp_contract()["c_total"]) / 8 / ic.LSB))
    print("op_p_total_uw = %.6g" % (g("nom", "p_avdd_uw") + g("nom", "p_dvdd_uw")))
    print("REPORT: op current error vs C_UNIT x V_REF x F_CLK (%%): nom %+.2f, slow (ss/85/3.0) %+.2f, fast (ff/0/3.6) %+.2f, MIM ss %+.2f, ff %+.2f"
          % (g("nom", "i_err_pct"), g("slow", "i_err_pct"), g("fast", "i_err_pct"), g("mss", "i_err_pct"), g("mff", "i_err_pct")))
    print("REPORT: op start-up to 1 %% (us): nom %.2f, slow %.2f, fast %.2f; headroom min (mV): nom %.0f (%s), slow %.0f (%s), fast %.0f (%s)"
          % (g("nom", "t_start_us"), g("slow", "t_start_us"), g("fast", "t_start_us"), g("nom", "hr_min_mv"), g("nom", "hr_min_dev"),
             g("slow", "hr_min_mv"), g("slow", "hr_min_dev"), g("fast", "hr_min_mv"), g("fast", "hr_min_dev")))
    with open(os.path.join(ic.BLOCK, "data", "op.csv"), "w") as f:
        keys = sorted({k for v in c.values() for k in v})
        f.write("case," + ",".join(keys) + "\n")
        for t, v in c.items():
            f.write(t + "," + ",".join(str(v.get(k, "")) for k in keys) + "\n")

elif ph == "pvt":
    c = cases("pvt_")
    n = len(c)
    print("pvt_cells = %d" % n)
    if n:
        err = {t: v["i_err_pct"] for t, v in c.items()}
        hr = {t: v["hr_min_mv"] for t, v in c.items()}
        ts = {t: v["t_start_us"] for t, v in c.items()}
        wt = max(err, key=lambda t: abs(err[t]))
        print("pvt_i_err_max_pct = %.6g" % abs(err[wt]))
        print("pvt_i_err_spread_pct = %.6g" % (max(err.values()) - min(err.values())))
        print("pvt_i_err_mean_pct = %.6g" % np.mean(list(err.values())))
        print("pvt_i_err_min_pct = %.6g" % min(err.values()))
        print("pvt_i_err_max_signed_pct = %.6g" % max(err.values()))
        wh = min(hr, key=hr.get)
        print("pvt_hr_min_mv = %.6g" % hr[wh])
        wts = max(ts, key=ts.get)
        print("pvt_t_start_max_us = %.6g" % ts[wts])
        ok = sum(1 for t in c if abs(err[t] - np.mean(list(err.values()))) <= ic.I_TOL_PVT_PCT and hr[t] >= 0 and ts[t] <= ic.T_START_MAX * 1e6)
        print("pvt_pass = %d" % ok)
        print("REPORT: pvt current error %+.2f..%+.2f %% (mean %+.2f; worst |err| at %s), headroom min %.0f mV (%s: %s), start max %.2f us (%s)"
              % (min(err.values()), max(err.values()), np.mean(list(err.values())), wt, hr[wh], wh, c[wh]["hr_min_dev"], ts[wts], wts))
        with open(os.path.join(ic.BLOCK, "data", "pvt.csv"), "w") as f:
            keys = sorted({k for v in c.values() for k in v})
            f.write("case," + ",".join(keys) + "\n")
            for t, v in sorted(c.items()):
                f.write(t + "," + ",".join(str(v.get(k, "")) for k in keys) + "\n")

elif ph == "mc":
    c = cases("mc_")
    n = len(c)
    print("mc_draws = %d" % n)
    if n >= 2:
        e = np.array([v["i_err_pct"] for v in c.values()])
        print("mc_i_err_mean_pct = %.6g" % e.mean())
        print("mc_i_sigma_pct = %.6g" % e.std(ddof=1))
        print("mc_i_3sigma_pct = %.6g" % (3 * e.std(ddof=1)))
        print("mc_i_err_min_pct = %.6g" % e.min())
        print("mc_i_err_max_pct = %.6g" % e.max())
        ts = np.array([v["t_start_us"] for v in c.values()])
        print("mc_t_start_max_us = %.6g" % ts.max())
        print("REPORT: mc start-up to 1 %% (us): median %.1f, 90 %% %.1f, 99 %% %.1f, max %.1f; %d of %d draws over 30 us, %d over 40 us"
              % (np.median(ts), np.percentile(ts, 90), np.percentile(ts, 99), ts.max(), (ts > 30.0).sum(), n, (ts > 40.0).sum()))
        ws = sorted(c, key=lambda t: -c[t]["t_start_us"])[:3]
        print("REPORT: mc slowest starts: " + ", ".join("%s %.1f us (loop %+.2f %%, mirror %+.2f %%)"
              % (t, c[t]["t_start_us"], c[t].get("loop_err_pct", float("nan")), c[t].get("mirror_err_pct", float("nan"))) for t in ws))
        print("REPORT: mc %d draws: current error mean %+.2f %%, sigma %.2f %% (3 sigma %.2f), range %+.2f..%+.2f %%"
              % (n, e.mean(), e.std(ddof=1), 3 * e.std(ddof=1), e.min(), e.max()))
        np.savetxt(os.path.join(ic.BLOCK, "data", "mc.csv"), e, header="i_err_pct", comments="")
        for part in ("vref_err_pct", "loop_err_pct", "mirror_err_pct", "sc_err_pct"):
            if all(part in v for v in c.values()):
                x = np.array([v[part] for v in c.values()])
                print("mc_%s_sigma = %.6g" % (part.replace("_pct", ""), x.std(ddof=1)))
        parts = [p for p in ("vref_err_pct", "loop_err_pct", "mirror_err_pct", "sc_err_pct") if all(p in v for v in c.values())]
        if parts:
            print("REPORT: mc sigma by part (%%): " + ", ".join("%s %.2f" % (p.replace("_err_pct", ""), np.array([v[p] for v in c.values()]).std(ddof=1)) for p in parts))
