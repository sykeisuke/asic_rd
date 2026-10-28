#!/usr/bin/env python3
"""compare_v4.py -- the v5 functional record against v4's (reported; the codes
are gated in check-func.awk's own gates, not here).

    python3 compare_v4.py

v5 removes the second VDD/2 buffer (vbl = vref, one node) and its bias
output: the trips can move by what VREF(TS_k) vs VBL(decision) now share, and
the power drops by one buffer + its bias. The timeline is v4's. Times are
compared relative to each record's own TR.
Reads data/v4_ref/func_measures.txt + func_reduce.txt (the v4 functional
record, ../Analog_top_bkp/Analog_top_v4/data at 2026-10-13) and data/func_measures.txt +
func_reduce.txt (this run). Prints REPORT lines and `cmp_v4_*` scalars.
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
    ref = os.path.join(HERE, "data", "v4_ref")
    a = load(os.path.join(ref, "func_measures.txt"), os.path.join(ref, "func_reduce.txt"))
    b = load(os.path.join(HERE, "data", "func_measures.txt"), os.path.join(HERE, "data", "func_reduce.txt"))
    nan = float("nan")
    g = lambda d, k: d.get(k, nan)
    codes4 = [int(g(a, "code%d" % k)) for k in range(4)]
    codes5 = [int(g(b, "code%d" % k)) if g(b, "code%d" % k) == g(b, "code%d" % k) else -1 for k in range(4)]
    print("REPORT: v4 compare: codes v5 %s / v4 %s (%s)" % ("/".join(map(str, codes5)), "/".join(map(str, codes4)),
                                                          "identical" if codes4 == codes5 else "DIFFERENT"))
    print("cmp_v4_codes_equal = %d" % int(codes4 == codes5))
    lsb = g(b, "p_lsb")
    T = g(b, "p_tcount")
    for k in range(4):
        dd = ((g(b, "t_dout%d" % k) - g(b, "p_tr")) - (g(a, "t_dout%d" % k) - g(a, "p_tr"))) / T
        dx = ((g(b, "t_bot%d" % k) - g(b, "p_tr")) - (g(a, "t_bot%d" % k) - g(a, "p_tr"))) / T
        print("cmp_v4_dout%d_lsb = %.6g" % (k, dd))
        print("REPORT: v4 compare: cell %d: dout (from TR) %+.4f LSB, analog crossing %+.4f LSB against v4; "
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
    print("REPORT: v4 compare (v4 -> v5): " + "; ".join(parts))
    print("REPORT: v4 compare: plate pedestal: v4 VBL(decision) - VREF(TS_k) %s mV, v5 (one node) %s mV"
          % ("/".join("%+.3f" % (g(a, "refd%d" % k) * 1e3) for k in range(4)),
             "/".join("%+.3f" % (g(b, "refd%d" % k) * 1e3) for k in range(4))))
    print("cmp_v4_vramp_tr_mv = %.6g" % ((g(b, "vramp_at_tr") - g(a, "vramp_at_tr")) * 1e3))
    print("cmp_v4_pw_total_uw = %.6g" % (g(b, "pw_total_uw") - g(a, "pw_total_uw")))
    print("cmp_v4_pw_ref_uw = %.6g" % (g(b, "pw_ref_uw") - g(a, "pw_ref_uw")))
    print("cmp_v4_pw_bg_uw = %.6g" % (g(b, "pw_bg_uw") - g(a, "pw_bg_uw")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
