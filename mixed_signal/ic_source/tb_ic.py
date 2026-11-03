#!/usr/bin/env python3
"""tb_ic.py -- the benches of the I/C current source.

    python3 tb_ic.py gen <dir> <tag> [KEY=VAL ...]     write <dir>/tb.spice
    python3 tb_ic.py reduce <dir> <tag>                 print "<tag>_<name> = <value>" lines

Keys (defaults in brackets):
  KIND    tran [default] | loop | noise
  CORNER  typical | ss | ff | sf | fs [typical]; RCORNER / MIM follow the corner unless given
  TEMP    [27]      VDDX  AVDD = DVDD in volts [3.3]     VLOAD  the ramp node's level [1.2]
  DUTY    clock high fraction [0.5]      TSTOP  [70u]     MC  1 draws mismatch [0]   SEED  [1]
  NETLIST path of the cell [ic_source.spice]
tran: the real switches and standard-cell phases; the output current is the ammeter
VLD's current into the level VLOAD; cold supply (PWL 0 -> VDDX in 100 ns).
loop / noise: the switched capacitor replaced by its average conductance F_CLK x C_UNIT
as a noiseless VCCS (valid below the clock: the loop's unity frequency is ~100 kHz);
loop breaks the gate node (1 GH / 1 GF) and sweeps the loop gain; noise integrates
the output current's noise through the ramp's 13.8 us boxcar kernel.
"""
import math
import os
import re
import sys

import numpy as np

import ic_common as ic

KEY_DEVS = [("XM1", "s1", "d1"), ("XMO", "s2", "d2"), ("XM1C", "d1", "a"), ("XMOC", "d2", "iout"),
            ("XIA", "ts", "fh1"), ("XIR", "ts", "fh2"), ("XN1", "fh1", "avss"), ("XNC1", "dl", "fh1"), ("XNC2", "vg", "fh2"),
            ("XPL2", "avdd", "sl2"), ("XPLC2", "sl2", "vg"), ("XPT", "avdd", "ts"), ("XNCS", "vcasp", "avss"), ("XPNC", "avdd", "vcasn")]


def parse(args):
    k = dict(KIND="tran", CORNER="typical", RCORNER="", MIM="", TEMP="27", VDDX="3.3", VLOAD="1.2", DUTY="0.5",
             TSTOP="70u", MC="0", SEED="1", NETLIST=os.path.join(ic.BLOCK, "ic_source.spice"))
    for a in args:
        n, v = a.split("=", 1)
        k[n] = v
    k["RCORNER"] = k["RCORNER"] or ic.resc(k["CORNER"])
    k["MIM"] = k["MIM"] or ic.mimc(k["CORNER"])
    return k


def tstop_s(s):
    m = {"u": 1e-6, "n": 1e-9, "m": 1e-3}
    return float(s[:-1]) * m[s[-1]] if s[-1] in m else float(s)


def averaged_netlist(path, brk=False):
    """The cell with the SC branch and its clocks replaced by a noiseless conductance; optionally the loop broken at vg."""
    g = ic.F_CLK * ic.sizing()["predicted"]["c_unit_ff"] * 1e-15
    out = []
    for line in open(path):
        t = line.split()
        if not t or line.startswith("*"):
            continue
        n = t[0]
        if n in ("XSA", "XSG", "XCU", "XI0", "XI1", "XI2", "XI3", "XI4", "XNR1", "XNR2"):
            continue
        if brk and n in ("XM1", "XMO"):
            t[2] = "vgx"
            line = " ".join(t) + "\n"
        if n == ".ends":
            out.append("GSC a avss a avss %.6g\n" % g)
            if brk:
                out.append("LBRK vg vgx 1G\nCINJ vgx vin 1G\n")
        out.append(line)
    if brk:
        out[0] = out[0].rstrip("\n") + " vin\n"
    return "".join(out)


def gen(d, tag, k):
    vdd = float(k["VDDX"])
    tstop = tstop_s(k["TSTOP"])
    duty = float(k["DUTY"])
    hdr = ic.head(k["CORNER"], k["RCORNER"], k["MIM"], k["TEMP"], std=(k["KIND"] == "tran"), mc=(k["MC"] == "1"))
    L = ["* ic_source bench %s (%s)" % (tag, " ".join("%s=%s" % kv for kv in sorted(k.items()))), hdr]
    if k["MC"] == "1":
        L.append(".options seed=%s" % k["SEED"])
    L.append(".option gmin=1e-15 reltol=1e-4")
    if k["KIND"] == "tran":
        L.append(open(k["NETLIST"]).read())
        L.append("VDD avdd 0 PWL(0 0 100n %g)\nVDVDD dvdd 0 PWL(0 0 100n %g)" % (vdd, vdd))
        L.append("VCLK clk 0 PULSE(0 %g 150n 0.5n 0.5n %.4gn 50n)" % (vdd, 50 * duty - 0.5))
        L.append("IB ibias 0 %g" % ic.I_BIAS)
        L.append("VLD iout 0 %s" % k["VLOAD"])
        L.append("XDUT iout ibias clk avdd 0 dvdd 0 ic_source")
        saves = " ".join("@m.xdut.%s.m0[vdsat]" % dn.lower() for dn, _, _ in KEY_DEVS)
        L.append(".save all " + saves + " @m.xdut.xm1.m0[id] @m.xdut.xmo.m0[id] @m.xdut.xsa.m0[id]")
        t1, t0 = tstop, tstop - 5e-6
        c = [".control", "set num_threads=1", "tran 2n %g" % tstop,
             "meas tran i_out avg i(vld) from=%g to=%g" % (t0, t1),
             "meas tran va avg v(xdut.a) from=%g to=%g" % (t0, t1),
             "meas tran va_pp pp v(xdut.a) from=%g to=%g" % (t1 - 1e-6, t1),
             "meas tran vg avg v(xdut.vg) from=%g to=%g" % (t0, t1),
             "meas tran vg_pp pp v(xdut.vg) from=%g to=%g" % (t1 - 1e-6, t1),
             "meas tran i_out_pp pp i(vld) from=%g to=%g" % (t1 - 1e-6, t1),
             "meas tran vref avg v(xdut.vref) from=%g to=%g" % (t0, t1),
             "meas tran vcasp avg v(xdut.vcasp) from=%g to=%g" % (t0, t1),
             "meas tran vcasn avg v(xdut.vcasn) from=%g to=%g" % (t0, t1),
             "meas tran i_avdd avg i(vdd) from=%g to=%g" % (t0, t1),
             "meas tran i_m1 avg @m.xdut.xm1.m0[id] from=%g to=%g" % (t0, t1),
             "meas tran i_mo avg @m.xdut.xmo.m0[id] from=%g to=%g" % (t0, t1),
             "meas tran i_sa avg @m.xdut.xsa.m0[id] from=%g to=%g" % (t0, t1),
             "meas tran i_dvdd avg i(vdvdd) from=%g to=%g" % (t0, t1)]
        for dn, a, b in KEY_DEVS:
            va = "v(xdut.%s)" % a if a not in ("avdd", "avss") else ("v(avdd)" if a == "avdd" else "0")
            vb = "v(xdut.%s)" % b if b not in ("avdd", "avss", "iout") else ("v(avdd)" if b == "avdd" else ("0" if b == "avss" else "v(iout)"))
            c.append("let vds_%s_v = abs(%s-%s)" % (dn.lower(), va, vb))
            c.append("meas tran vds_%s avg vds_%s_v from=%g to=%g" % (dn.lower(), dn.lower(), t0, t1))
            c.append("meas tran vdsat_%s avg @m.xdut.%s.m0[vdsat] from=%g to=%g" % (dn.lower(), dn.lower(), t0, t1))
        c += ["linearize i(vld) v(xdut.a) v(xdut.vg)", "wrdata wave.csv i(vld) v(xdut.a) v(xdut.vg)", "quit", ".endc", ".end"]
        L += c
    elif k["KIND"] == "loop":
        L.append(averaged_netlist(k["NETLIST"], brk=True))
        L.append("VDD avdd 0 %g\nVDVDD dvdd 0 %g\nVCLK clk 0 0" % (vdd, vdd))
        L.append("IB ibias 0 %g\nVLD iout 0 %s\nVAC vin 0 DC 0 AC 1" % (ic.I_BIAS, k["VLOAD"]))
        L.append("XDUT iout ibias clk avdd 0 dvdd 0 vin ic_source")
        L += [".control", "set num_threads=1", "op",
              "print @m.xdut.xia.m0[gm] @m.xdut.xia.m0[id] @m.xdut.xpt.m0[id] @m.xdut.xn1.m0[id] @m.xdut.xnc1.m0[id]",
              "print @m.xdut.xm1.m0[gm] @m.xdut.xm1.m0[id] @m.xdut.xm1.m0[gmbs] @m.xdut.xm1.m0[gds] @m.xdut.xm1c.m0[gm] @m.xdut.xm1c.m0[gds]",
              "print @m.xdut.xmo.m0[id] @m.xdut.xpl2.m0[id] @m.xdut.xplc2.m0[gds] @m.xdut.xnc2.m0[gds] v(xdut.a) v(xdut.vg)",
              "ac dec 40 1 1g", "let lg = -v(xdut.vg)/v(xdut.vgx)",
              "let lgr = real(lg)", "let lgi = imag(lg)", "wrdata loop.csv lgr lgi",
              "quit", ".endc", ".end"]
    elif k["KIND"] == "noise":
        L.append(averaged_netlist(k["NETLIST"]))
        L.append("VDD avdd 0 %g AC 1\nVDVDD dvdd 0 %g\nVCLK clk 0 0" % (vdd, vdd))
        L.append("IB ibias 0 %g\nRSENSE iout iout2 1 noisy=0\nVLD iout2 0 %s" % (ic.I_BIAS, k["VLOAD"]))
        L.append("XDUT iout ibias clk avdd 0 dvdd 0 ic_source")
        L += [".control", "set num_threads=1", "op", "noise v(iout,iout2) VDD dec 20 1 100meg",
              "setplot noise1", "wrdata noise.csv onoise_spectrum", "quit", ".endc", ".end"]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "tb.spice"), "w").write("\n".join(L) + "\n")
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    open(os.path.join(d, "case.txt"), "w").write(" ".join("%s=%s" % kv for kv in sorted(k.items())) + "\n")


def meas_lines(txt):
    out = {}
    for m in re.finditer(r"^\s*([@a-z_0-9.\[\]()]+)\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)", txt, re.M | re.I):
        out[m.group(1).lower()] = float(m.group(2))
    return out


def reduce(d, tag):
    k = dict(a.split("=", 1) for a in open(os.path.join(d, "case.txt")).read().split())
    txt = open(os.path.join(d, "tb.out"), errors="replace").read()
    sz = ic.sizing()["predicted"]
    P = lambda n, v, f="%.6g": print(("%s_%s = " + f) % (tag, n, v))
    if k["KIND"] == "tran":
        m = meas_lines(txt)
        vdd = float(k["VDDX"])
        c_u = {"typical": sz["c_unit_ff"], "ss": sz["c_unit_ss_ff"], "ff": sz["c_unit_ff_ff"]}[k["MIM"]] * 1e-15
        i_ideal = c_u * vdd * ic.RATIO_REF * ic.F_CLK
        i = m["i_out"]
        P("i_out_ua", i * 1e6)
        P("i_ideal_ua", i_ideal * 1e6)
        P("i_err_pct", 100 * (i / i_ideal - 1))
        P("va_err_mv", 1e3 * (m["va"] - vdd * ic.RATIO_REF))
        P("va_pp_mv", 1e3 * m["va_pp"])
        P("vg_v", m["vg"])
        P("vg_pp_mv", 1e3 * m["vg_pp"])
        P("i_out_pp_na", 1e9 * m["i_out_pp"])
        # the error's parts: the divider (vref), the loop (va - vref), the mirror (i_out vs XM1), the rest (switch charge)
        P("vref_err_pct", 100 * (m["vref"] / (vdd * ic.RATIO_REF) - 1))
        P("loop_err_pct", 100 * (m["va"] - m["vref"]) / m["vref"])
        P("mirror_err_pct", 100 * (abs(m["i_mo"]) / abs(m["i_m1"]) - 1))
        P("sc_err_pct", 100 * (abs(m["i_m1"]) / (c_u * m["va"] * ic.F_CLK) - 1))
        P("vcasp_v", m["vcasp"])
        P("vcasn_v", m["vcasn"])
        P("p_avdd_uw", -m["i_avdd"] * vdd * 1e6)
        P("p_dvdd_uw", -m["i_dvdd"] * vdd * 1e6)
        worst = ("", 9.0)
        for dn, _, _ in KEY_DEVS:
            mg = m["vds_" + dn.lower()] - m["vdsat_" + dn.lower()]
            P("hr_%s_mv" % dn.lower(), 1e3 * mg)
            if mg < worst[1]:
                worst = (dn, mg)
        P("hr_min_mv", 1e3 * worst[1])
        print("%s_hr_min_dev = %s" % (tag, worst[0]))
        # start-up: the last time |i - i_final| exceeds 1 % of i_final
        w = np.loadtxt(os.path.join(d, "wave.csv"))
        t, iw = w[:, 0], w[:, 1]
        # one clock period's moving average (25 x 2 ns), so the 20 MHz ripple does not count as "not settled"
        n_avg = max(1, int(round(ic.TCOUNT / max(t[1] - t[0], 1e-12))))
        iw = np.convolve(iw, np.ones(n_avg) / n_avg, mode="valid")
        t = t[n_avg // 2:n_avg // 2 + len(iw)]
        i_f = np.mean(iw[t > t[-1] - 5e-6])
        bad = np.where(abs(iw - i_f) > 0.01 * abs(i_f))[0]
        P("t_start_us", 1e6 * (t[bad[-1]] if len(bad) else 0.0))
        bad5 = np.where(abs(iw - i_f) > 0.05 * abs(i_f))[0]
        P("t_start5_us", 1e6 * (t[bad5[-1]] if len(bad5) else 0.0))
    elif k["KIND"] == "loop":
        w = np.loadtxt(os.path.join(d, "loop.csv"))
        f, lr, li = w[:, 0], w[:, 1], w[:, 3]
        mag = np.hypot(lr, li)
        ph = np.degrees(np.unwrap(np.arctan2(li, lr)))
        for kk, vv in meas_lines(txt).items():
            if kk.startswith("@m.") or kk.startswith("v("):
                print("%s_op_%s = %.6g" % (tag, re.sub(r"[^a-z0-9]+", "_", kk).strip("_"), vv))
        P("loop_dc_db", 20 * math.log10(mag[0]))
        above = np.where(mag >= 1.0)[0]
        if len(above) and above[-1] + 1 < len(f):
            j = above[-1]
            fu = f[j] * (f[j + 1] / f[j]) ** ((math.log(mag[j])) / (math.log(mag[j]) - math.log(mag[j + 1])))
            phu = np.interp(math.log(fu), np.log(f), ph)
            P("f_unity_khz", fu * 1e-3)
            P("pm_deg", 180.0 + phu)
        else:
            P("f_unity_khz", 0.0)
            P("pm_deg", 180.0)
        # gain margin at the -180 crossing
        below = np.where(ph <= -180.0)[0]
        P("gm_db", -20 * math.log10(mag[below[0]]) if len(below) else 99.0)
    elif k["KIND"] == "noise":
        w = np.loadtxt(os.path.join(d, "noise.csv"))
        f, s = w[:, 0], w[:, 1] ** 2                 # onoise_spectrum is V/rtHz across the noiseless 1 ohm sense -> A^2/Hz
        rc = ic.ramp_contract()
        T, C = ic.T_RAMP, rc["c_total"]
        H2 = (T * np.sinc(f * T) / C) ** 2
        # integrate on the log grid, from 1 Hz
        var = np.trapezoid(s * H2, f)
        P("noise_code255_lsb", math.sqrt(var) / ic.LSB)
        P("noise_i_1khz_pa_rthz", 1e12 * math.sqrt(np.interp(1e3, f, s)))
        P("noise_i_1mhz_pa_rthz", 1e12 * math.sqrt(np.interp(1e6, f, s)))
        i_ref = sz["i_ref_ua"] * 1e-6
        var_lo = np.trapezoid((s * H2)[f <= 1e3], f[f <= 1e3])
        P("noise_code255_below1khz_lsb", math.sqrt(var_lo) / ic.LSB)
        P("noise_rel_rms_1hz_100khz_ppm", 1e6 * math.sqrt(np.trapezoid(s[f <= 1e5], f[f <= 1e5])) / i_ref)


if __name__ == "__main__":
    cmd, d, tag = sys.argv[1:4]
    if cmd == "gen":
        gen(d, tag, parse(sys.argv[4:]))
    else:
        reduce(d, tag)
