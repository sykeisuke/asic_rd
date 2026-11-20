#!/usr/bin/env python3
"""compare_prev.py -- the functional record against the previous version's
(reported; the codes are gated in check-func.awk's own gates, not here).

    python3 compare_prev.py

The previous record is data/prev_ref (runs/analog-top/20261116T085301Z, before the
comparator swap); the comparator
is ../comparator with the plate on inp; its delay from the plate crossing
changes, the analog crossing should not. Per cell the comparator delay
(t_dout - t_bot) of both records and its difference in counts are printed
(cmp_prev_delay<k>_ns), so a code shift can be traced to it.
Earlier comparisons (archived): the sequencer (ADR 0027) against the record before it; before that (ADR 0026) the ramp ramp_simple fed by ic_source on the
ADR 0025 grid (LSB 6.70 mV instead of 5.86 mV, reset level 7/55 AVDD =
0.420 V instead of 0.5 V, T0 60 us, the ramp ends 3 counts after count 256).
The input POSITIONS (LSB above VR_LO) are v5's, so the codes are comparable;
the input voltages and times are not. Times are compared relative to each
record's own TR, in counts. Reads data/prev_ref/func_measures.txt +
func_reduce.txt (the previous functional record) and data/func_measures.txt +
func_reduce.txt (this run). Prints REPORT lines and `cmp_prev_*` scalars.
(Until v5 this was compare_v4.py.)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(*paths):
    out = {}
    for p in paths:
        for ln in open(p):
            t = ln.split()
            if len(t) >= 3 and t[1] == "=":
                try:
                    out[t[0]] = float(t[2])
                except ValueError:
                    pass
    return out


def main():
    ref = os.path.join(HERE, "data", "prev_ref")
    a = load(os.path.join(ref, "func_measures.txt"), os.path.join(ref, "func_reduce.txt"))
    b = load(os.path.join(HERE, "data", "func_measures.txt"), os.path.join(HERE, "data", "func_reduce.txt"))
    nan = float("nan")
    g = lambda d, k: d.get(k, nan)
    codes4 = [int(g(a, "code%d" % k)) for k in range(4)]
    codes5 = [int(g(b, "code%d" % k)) if g(b, "code%d" % k) == g(b, "code%d" % k) else -1 for k in range(4)]
    print("REPORT: prev compare: codes current %s / previous %s (%s)" % ("/".join(map(str, codes5)), "/".join(map(str, codes4)),
                                                          "identical" if codes4 == codes5 else "DIFFERENT"))
    print("cmp_prev_codes_equal = %d" % int(codes4 == codes5))
    lsb = g(b, "p_lsb")
    T = g(b, "p_tcount")
    for k in range(4):
        dd = ((g(b, "t_dout%d" % k) - g(b, "p_tr")) - (g(a, "t_dout%d" % k) - g(a, "p_tr"))) / T
        dx = ((g(b, "t_bot%d" % k) - g(b, "p_tr")) - (g(a, "t_bot%d" % k) - g(a, "p_tr"))) / T
        print("cmp_prev_dout%d_lsb = %.6g" % (k, dd))
        print("cmp_prev_xing%d_lsb = %.6g" % (k, dx))
        da, db = g(a, "cmp_delay%d" % k), g(b, "cmp_delay%d" % k)
        print("cmp_prev_delay%d_ns = %.6g" % (k, (db - da) * 1e9))
        print("REPORT: prev compare: cell %d: comparator delay from the plate crossing previous %.3f ns -> current %.3f ns "
              "(%+.3f ns = %+.4f counts); code previous %s -> current %s" % (k, da * 1e9, db * 1e9, (db - da) * 1e9, (db - da) / T,
                                                                  codes4[k], codes5[k]))
        print("REPORT: prev compare: cell %d: dout (from TR) %+.4f counts, analog crossing %+.4f counts against previous; "
              "plate error %+.4f -> %+.4f LSB" % (k, dd, dx, g(a, "bps_err%d" % k), g(b, "bps_err%d" % k)))
    rows = [("vramp at TR (V)", "vramp_at_tr", 1, "%.6f"), ("ramp slope (V/us)", "ramp_slope_vpus", 1, "%.6f"),
            ("ramp INL best fit (LSB)", "ramp_inl_bf_lsb", 1, "%.4f"),
            ("transfer offset (LSB)", "xfer_d_offset_lsb", 1, "%.4f"),
            ("transfer gain error (%)", "xfer_d_gain_err_pct", 1, "%.4f"),
            ("iramp at TS0 (uA)", "iramp_ts0_ua", 1, "%.5f"), ("icmp0 at TS0 (uA)", "icmp0_ts0_ua", 1, "%.5f"),
            ("ivref at TS0 (uA)", "ivref_ts0_ua", 1, "%.5f"), ("core (uA)", "icore_ts0_ua", 1, "%.5f"),
            ("refs power (uW)", "pw_ref_uw", 1, "%.2f"),
            ("power over the ramp (uW)", "pw_total_uw", 1, "%.2f"), ("bias_gen power (uW)", "pw_bg_uw", 1, "%.2f"),
            ("ramp power (uW)", "pw_ramp_uw", 1, "%.2f"), ("tracking AVDD (uW)", "pw_avdd_idle_uw", 1, "%.2f")]
    parts = []
    for label, k, _, f in rows:
        parts.append(("%s " + f + " -> " + f) % (label, g(a, k), g(b, k)))
    print("REPORT: prev compare (previous -> current): " + "; ".join(parts))
    print("REPORT: prev compare: VREF(decision) - VREF(TS_k): previous %s mV, current %s mV"
          % ("/".join("%+.3f" % (g(a, "refd%d" % k) * 1e3) for k in range(4)),
             "/".join("%+.3f" % (g(b, "refd%d" % k) * 1e3) for k in range(4))))
    print("cmp_prev_vramp_tr_mv = %.6g" % ((g(b, "vramp_at_tr") - g(a, "vramp_at_tr")) * 1e3))
    print("cmp_prev_pw_total_uw = %.6g" % (g(b, "pw_total_uw") - g(a, "pw_total_uw")))
    print("cmp_prev_pw_ramp_uw = %.6g" % (g(b, "pw_ramp_uw") - g(a, "pw_ramp_uw")))
    print("cmp_prev_pw_dvdd_uw = %.6g" % (g(b, "pw_dvdd_uw") - g(a, "pw_dvdd_uw")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
