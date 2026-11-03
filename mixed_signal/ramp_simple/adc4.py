"""Four cells converting on the ramp: the analog macro's own functional bench
(the v5 macro as frozen in ref/analog_top_v5: its timeline and measures),
with the macro's ramp replaced by this block's ramp_simple (REAL=1) or by an
ideal ramp (REAL=0), and optionally vrlo_ref replaced by an ideal VR_LO at the
pre-roll level (LEVEL=ideal). The ramp's own contribution to a conversion is
always real minus ideal, with the same cells, references and timeline.

    python3 adc4.py gen <dir> TAG=<tag> REAL=1 LEVEL=real POS0=.. POS1=.. POS2=.. POS3=.. [CODE=7]
    python3 adc4.py reduce <cases.txt>      -> adc4_* lines, data/adc4_levels.csv, data/adc4_ramp_delta.csv

Each case directory gets analog_top_case.spice (the macro netlist with the
XRAMP / XVRLO lines substituted), tb_params_case.inc (POS and VR_LO overrides)
and tb.spice (the macro bench pointed at them). The measures of interest come
from the bench's own tb_measure.inc: code_k, err_d_k (dout's continuous trip
count minus POS_k: the input-referred error), t_dout_k, vramp_at_tr, the ramp
slope / INL from wave.csv.
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_common as rs  # noqa: E402

# the v5 macro and its bench, frozen (ref/analog_top_v5, 2026-10-30): the live ../Analog_top now
# carries this ramp and ../ic_source itself (ADR 0026), so the substitution needs the macro before it
AT = "/foss/designs/mixed_signal/ramp_simple/ref/analog_top_v5"
WORK = os.path.join(rs.BLOCK, "work", "adc4")
DATA = os.path.join(rs.BLOCK, "data")
XRAMP = "XRAMP vramp ramp_rst vrlo pbias_r avdd_ramp avss ramp_simple_d"
XVRLO = "XVRLO vrlo ivrlo avdd_vrlo avss vrlo_ref"
IC_NETLIST = "/foss/designs/mixed_signal/ic_source/ic_source.spice"
T0_IC = "60u"                # the macro's power-up wait with the real I/C source (ic_source R7, ADR 0025)


def gen(d, kv):
    real, level = int(kv.get("REAL", 1)), kv.get("LEVEL", "real")
    ki = float(kv.get("I", 1.0))
    src = kv.get("SRC", "ideal")
    net = open(os.path.join(AT, "analog_top.spice")).read()
    assert XRAMP in net and XVRLO in net, "the macro's XRAMP / XVRLO lines changed"
    # bias_gen's ramp sink keeps its diode load (the old ramp's XRD) in both variants, so the
    # bias generator sees the same consumers; the ramp current itself is an ideal source
    # (the I/C source's place) from the ramp's supply ammeter node into vramp
    diode = "XRDI pbias_r pbias_r avdd_ramp avdd_ramp pfet_03v3 L=1u W=20u nf=10 m=1"
    if real and src == "ic":
        # the real I/C source (../ic_source) on bias_gen's ramp sink (its own bias diode replaces
        # XRDI), the count clock and DVDD; it needs ~25-50 us to start (ic_source R7): T0 = 60 us
        new = "XRAMP vramp ramp_rst vrlo avss ramp_simple\nXIC vramp pbias_r cnt_clk avdd_ramp avss dvdd dvss ic_source"
    elif real:
        new = ("XRAMP vramp ramp_rst vrlo avss ramp_simple\nIRAMP avdd_ramp vramp PWL(0 0 {TPWR} %.6g)\n%s"
               % (ki * rs.design_current(), diode))
    else:
        # an ideal ramp: held at VR_LO, released at TR at the exact slope
        new = "VRAMPI vramp avss PWL(0 {VR_LO} {TR} {VR_LO} {TSTOP} {VR_LO+SLOPE*(TSTOP-TR)})\n" + diode
    net = net.replace(XRAMP, new)
    if level == "ideal":
        net = net.replace(XVRLO, "VVRLO vrlo avss {VR_LO}\nXRDV ivrlo lvr avdd_vrlo avdd_vrlo pfet_03v3 L=0.5u W=4u nf=1 m=1\n"
                          "XLVR lvr lvr avss avss nfet_03v3 L=0.34u W=0.5u nf=1 m=1")
    os.makedirs(d, exist_ok=True)
    inc = ".include %s\n" % rs.NETLIST + (".include %s\n" % IC_NETLIST if src == "ic" else "")
    open(os.path.join(d, "analog_top_case.spice"), "w").write(inc + net)
    par = open(os.path.join(AT, "tb_params.inc")).read()
    for k in range(4):
        par, n = re.subn(r"^\.param POS%d=.*$" % k, ".param POS%d=%s" % (k, kv["POS%d" % k]), par, flags=re.M)
        assert n == 1
    if level == "ideal":
        # the pre-roll reset level
        par, n = re.subn(r"^\.param VR_LO=.*$", ".param VR_LO=%.6f" % rs.VR_LO_TAP, par, flags=re.M)
        assert n == 1
    # the grid of ADR 0025: LSB and SLOPE in tb_params.inc are (VR_HI - VR_LO) / 256, so VR_HI
    # carries this block's LSB; the ramp ends at the overflow + DRAIN (3 counts), not 20
    par, n = re.subn(r"^\.param VR_HI=.*$", ".param VR_HI='VR_LO+%.9g'" % (256 * rs.LSB), par, flags=re.M)
    assert n == 1
    par, n = re.subn(r"^\.param TOVR=.*$", ".param TOVR='%d*TCOUNT'" % (rs.NCNT - 256), par, flags=re.M)
    assert n == 1
    if src == "ic" or kv.get("T0"):
        par, n = re.subn(r"^\.param T0=.*$", ".param T0=%s" % kv.get("T0", T0_IC), par, flags=re.M)
        assert n == 1
    open(os.path.join(d, "tb_params_case.inc"), "w").write(par)
    tb = open(os.path.join(AT, "tb_analog_top.spice")).read()
    tb = tb.replace(".include %s/analog_top.spice" % AT, ".include analog_top_case.spice")
    tb = tb.replace(".include %s/tb_params.inc" % AT, ".include tb_params_case.inc")
    assert "analog_top_case.spice" in tb and "tb_params_case.inc" in tb
    open(os.path.join(d, "tb.spice"), "w").write(tb)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")


def load_meas(path):
    v = {}
    for line in open(path, errors="replace"):
        m = re.match(r"^\s*([a-z_][a-z_0-9]*)\s*=\s*([-+0-9.eE]+)", line)
        if m:
            v[m.group(1)] = float(m.group(2))
    return v


def ramp_from_wave(d, m):
    """slope and INL of v(xdut.vramp) at the count boundaries, from wave.csv."""
    p = os.path.join(d, "wave.csv")
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        hdr = f.readline().split()
    col = [i for i, h in enumerate(hdr) if h.lower() in ("v(xdut.vramp)", "xdut.vramp")]
    if not col:
        return {}
    w = np.loadtxt(p, skiprows=1, usecols=(0, col[0]))
    TR, T, LSB, VRL = m["p_tr"], m["p_tcount"], m["p_lsb"], m["p_vr_lo"]
    k = np.arange(0, rs.NCNT + 1)
    vk = np.interp(TR + k * T, w[:, 0], w[:, 1])
    klo = 0 if abs(VRL - 0.5) < 1e-3 else rs.K_LO
    fit = (k >= klo + (4 if klo == 0 else 0)) & (k <= rs.NVALID)
    pl = np.polyfit(k[fit], vk[fit], 1)
    res = (vk - np.polyval(pl, k)) / LSB
    pe = np.polyfit([k[fit][0], k[fit][-1]], [vk[fit][0], vk[fit][-1]], 1)
    return {"ramp_slope_err_pct": (pl[0] / T / rs.SLOPE - 1) * 100, "ramp_inl_bf_lsb": float(np.max(np.abs(res[fit]))),
            "ramp_inl_ep_lsb": float(np.max(np.abs((vk[fit] - np.polyval(pe, k[fit])) / LSB))),
            "ramp_start_lsb": float((vk[0] - VRL) / LSB)}


def reduce(cases_path):
    os.makedirs(DATA, exist_ok=True)
    cases = [ln.split() for ln in open(cases_path) if ln.strip()]
    R = {}
    missing = 0
    for c in cases:
        kind, tag = c[0], c[1]
        d = os.path.join(WORK, tag)
        mp = os.path.join(d, "meas.txt")
        if not os.path.exists(mp):
            missing += 1
            continue
        m = load_meas(mp)
        if not all("code%d" % k in m and "err_d%d" % k in m for k in range(4)):
            missing += 1
            print("REPORT: adc4 case %s incomplete (%d measures)" % (tag, len(m)))
            continue
        m.update(ramp_from_wave(d, m))
        R[tag] = (kind, dict((k.split("=")[0], k.split("=")[1]) for k in c[2:]), m)
    print("adc4_cases = %d" % len(cases))
    print("adc4_missing = %d" % missing)

    def pos(tag):
        return [float(R[tag][1]["POS%d" % k]) for k in range(4)]

    def err(tag):
        return [R[tag][2]["err_d%d" % k] for k in range(4)]

    def codes(tag):
        return [int(R[tag][2]["code%d" % k]) for k in range(4)]

    # show: the four mid-codes, real vs ideal
    for tag in ("show_r", "show_i", "showp_r", "showp_i", "lowp_r", "lowp_i", "showp_s", "lowp_s"):
        if tag in R:
            print("adc4_%s_codes = %d %d %d %d" % tuple([tag] + codes(tag)))
            for k in range(4):
                print("adc4_%s_code%d = %d" % (tag, k, codes(tag)[k]))
                print("adc4_%s_err_d%d_lsb = %.4f" % (tag, k, err(tag)[k]))
            for key in ("ramp_slope_err_pct", "ramp_inl_bf_lsb", "ramp_inl_ep_lsb", "ramp_start_lsb", "vramp_vrlo_tr"):
                if key in R[tag][2]:
                    print("adc4_%s_%s = %.6g" % (tag, key, R[tag][2][key]))
    # coarse transfer: 32 levels, real and ideal, the ramp's share = real - ideal
    lv = []
    for r in range(8):
        tr, ti = "c%d_r" % r, "c%d_i" % r
        if tr in R and ti in R:
            for k in range(4):
                lv.append((pos(tr)[k], err(tr)[k], err(ti)[k], codes(tr)[k], codes(ti)[k]))
    if lv:
        lv.sort()
        P = np.array([x[0] for x in lv]); er = np.array([x[1] for x in lv]); ei = np.array([x[2] for x in lv])
        cr = np.array([x[3] for x in lv])
        print("adc4_coarse_levels = %d" % len(lv))
        print("adc4_coarse_real_err_spread_lsb = %.4f" % (er.max() - er.min()))
        print("adc4_coarse_ideal_err_spread_lsb = %.4f" % (ei.max() - ei.min()))
        print("adc4_coarse_real_monotonic = %d" % int(np.all(np.diff(cr) >= 0)))
        dlt = er - ei
        pl = np.polyfit(P, dlt, 1)
        resid = dlt - np.polyval(pl, P)
        print("adc4_ramp_gain_err_pct = %.4f" % (pl[0] * 100))
        print("adc4_ramp_offset_lsb = %.4f" % pl[1])
        print("adc4_ramp_inl_lsb = %.4f" % np.max(np.abs(resid)))
        with open(os.path.join(DATA, "adc4_levels.csv"), "w") as fo:
            fo.write("pos,err_real_lsb,err_ideal_lsb,code_real,code_ideal,ramp_delta_lsb,ramp_resid_lsb\n")
            for x, dd, rr in zip(lv, dlt, resid):
                fo.write("%.4f,%.6f,%.6f,%d,%d,%.6f,%.6f\n" % (x[0], x[1], x[2], x[3], x[4], dd, rr))
    # the real I/C source: the same 32 levels on the pre-roll level against the ideal ramp there
    ls = []
    for r in range(8):
        ts, ti = "c%d_s" % r, "c%d_pi" % r
        if ts in R and ti in R:
            for k in range(4):
                ls.append((pos(ts)[k], err(ts)[k], err(ti)[k], codes(ts)[k]))
    if ls:
        ls.sort()
        P = np.array([x[0] for x in ls]); er = np.array([x[1] for x in ls]); ei = np.array([x[2] for x in ls])
        print("adc4_src_levels = %d" % len(ls))
        print("adc4_src_monotonic = %d" % int(np.all(np.diff([x[3] for x in ls]) >= 0)))
        dlt = er - ei
        pl = np.polyfit(P, dlt, 1)
        print("adc4_src_gain_err_pct = %.4f" % (pl[0] * 100))
        print("adc4_src_offset_lsb = %.4f" % pl[1])
        print("adc4_src_inl_lsb = %.4f" % np.max(np.abs(dlt - np.polyval(pl, P))))
    # fine staircase and the lowest codes
    for tag in ("fine_r", "fine_i", "low_r", "low_i", "fine_s"):
        if tag in R:
            print("adc4_%s_codes = %d %d %d %d" % tuple([tag] + codes(tag)))
            print("adc4_%s_err_spread_lsb = %.4f" % (tag, max(err(tag)) - min(err(tag))))
            for k in range(4):
                print("adc4_%s_code%d = %d" % (tag, k, codes(tag)[k]))
    # trip-kick crosstalk: the victim is cell 0 at 128.5; three aggressors d LSB below (m) or above (p)
    for dtag in ("0p25", "1", "4", "16", "24", "32", "64"):
        for pol in ("m", "p"):
            tr, ti = "xt%s%s_r" % (pol, dtag), "xt%s%s_i" % (pol, dtag)
            if tr in R and ti in R:
                print("adc4_xt%s%s_total_lsb = %.4f" % (pol, dtag, err(tr)[0]))
                print("adc4_xt%s%s_ideal_lsb = %.4f" % (pol, dtag, err(ti)[0]))
        if "xtm%s_r" % dtag in R and "xtp%s_r" % dtag in R and "xtm%s_i" % dtag in R and "xtp%s_i" % dtag in R:
            # the victim's shift from aggressors below minus above, real minus ideal: the ramp's share
            share = (err("xtm%s_r" % dtag)[0] - err("xtp%s_r" % dtag)[0]) - (err("xtm%s_i" % dtag)[0] - err("xtp%s_i" % dtag)[0])
            print("adc4_xtr_d%s_lsb = %.4f" % (dtag, share))
            print("adc4_xti_d%s_lsb = %.4f" % (dtag, err("xtm%s_i" % dtag)[0] - err("xtp%s_i" % dtag)[0]))
    # the same crosstalk with the real source (pre-roll level), against its own ideal-ramp pair
    for dtag in ("24",):
        tags = ["xt%s%s_%s" % (pol, dtag, k) for k in ("s", "pi") for pol in ("m", "p")]
        if all(t in R for t in tags):
            share = (err("xtm%s_s" % dtag)[0] - err("xtp%s_s" % dtag)[0]) - (err("xtm%s_pi" % dtag)[0] - err("xtp%s_pi" % dtag)[0])
            print("adc4_xts_d%s_lsb = %.4f" % (dtag, share))
    # S1-connection crosstalk: cell 1 at 20.5 with cells 2/3 at 0.5 (x0) vs 254.5 (x1)
    if "x0_r" in R and "x1_r" in R:
        print("adc4_xc_v20_lsb = %.4f" % (err("x1_r")[1] - err("x0_r")[1]))
        print("adc4_xc_v5_lsb = %.4f" % (err("x1_r")[0] - err("x0_r")[0]))
    # per-decision kick on vramp (the macro's measure, if the bench echoes it) is reported from show_r
    for key in ("ramp_kick0_mv", "ramp_kick1_mv", "ramp_kick2_mv", "ramp_kick3_mv"):
        if "show_r" in R and key in R["show_r"][2]:
            print("adc4_show_r_%s = %.4f" % (key, R["show_r"][2][key]))


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        kv = dict(a.split("=", 1) for a in sys.argv[3:])
        gen(sys.argv[2], kv)
    else:
        reduce(sys.argv[2])
