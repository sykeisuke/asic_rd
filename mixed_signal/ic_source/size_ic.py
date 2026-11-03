#!/usr/bin/env python3
"""size_ic.py -- the I/C current source from SPEC.md's requirements to ic_source.spice.

The chain (DESIGN_RECIPE.md, every number labelled):
  1. I = C_UNIT x V_REF x F_CLK: the unit MIM read from the model card by an AC
     probe at V_REF / 2 (typical and the MIM corners), V_REF = 5/33 AVDD [D].
  2. The divider: 33 strips of ppolyf_u_3k 1 x 20 um (data/res_char.csv), taps
     for V_REF (5), the NMOS cascode bias and the PMOS cascode bias [D].
  3. The pass mirror (L 1 um, 2 um fingers): finger count and degeneration from
     the mismatch rule sigma(dI/I) = sigma(dVt) / (I/gm + I R_s) <= SIG_MIRROR
     with I R_s <= V_DEG_MAX (the output cascode's headroom at the ramp top) [D].
  4. Cascodes (L 0.5 um): the V_CAS tap from the headroom window at typical [D].
  5. The OTA: folded cascode, PMOS pair at one finger of the bias ladder; the
     pair and the fold sinks sized by Pelgrom for the loop offset budget
     SIG_OS (no chopper: the offset is a current error V_os / V_REF); the
     compensation capacitor at the gate node from the loop's unity frequency
     <= p_A / 2.5, p_A = F_CLK C_UNIT / (C_F + C_UNIT + C_par) [D].
  6. Start-up: two stacked minimum PMOS diodes pre-charge the gate node [D].
Writes ic_source.spice (numbers, no parameter file) and data/sizing.json into
IC_OUT (default: this folder); the `size` phase sets IC_OUT=work/size and
compares. Prints `size_<name> = <value>` lines and REPORT: lines.
"""
import json
import math
import os

import numpy as np

import ic_common as ic
from ic_common import C_UNIT_SIDE, F_CLK, I_BIAS, N_DIV, VDD, V_REF, V_RAMP_HI, head, grab, ng, um

OUT = os.environ.get("IC_OUT", ic.BLOCK)
WORK = os.path.join(ic.BLOCK, "work", "size")
os.makedirs(WORK, exist_ok=True)

# ---------------------------------------------------------------- fixed choices (labels in DESIGN_RECIPE.md)
L_P, WF_P = 1.0, 2.0            # pass mirror: L 1 um for matching (the recorded exception), 2 um fingers [D]
L_C, WF_C, NF_C = 0.5, 2.0, 4   # cascodes: 4 fingers keep |Vgs_c| low for the pass device's headroom at ss / 3.0 V [D]
L_B, WF_B, NF_B = 1.0, 2.0, 10  # bias diode: bias_gen's ramp sink into XRD's geometry (L 1 um, 10 x 2 um) [C]
L_I, WF_I = 1.0, 2.0            # OTA pair: L 1 um and whole 2 um fingers for matching (finger count from SIG_OS) [D]
L_N, WF_N = 1.0, 2.0            # fold sinks and their diode: L 1 um, 2 um fingers, same count as the pair [D]
L_OC, WF_OC = 0.5, 1.0          # OTA NMOS cascodes [A]
L_OL, WF_OL, NF_OL = 1.0, 2.0, 4  # OTA PMOS load: L 1 um, 4 fingers (it carries a quarter of the pair current) [D]
L_OLC = 0.5                     # its cascodes [A]
W_SW, L_SW = 0.3, 0.28          # SC switches [A]: their junctions on ct switch with C_UNIT (0.5 um gave +1.5 % of current)
SINK_RATIO = (2, 3)             # sink : diode fingers, I_sink = 2/3 of a bias finger, so the fold carries 1/6 of it [D]
WF_D1, NF_D1 = 2.0, 4           # the wide PMOS diode of the V_CASP stack (weak inversion: ~0.5 V = I R_s + V_SD margin) [D]
WF_ND2, NF_ND2 = 4.0, 1         # the wide NMOS diode of the V_CASN stack (the fold node sits one weak Vgs above avss) [D]
L_SU, W_SU = 0.36, 0.22         # start-up diodes, minimum [A]
SIG_MIRROR = 0.004              # mismatch of the pass mirror, sigma <= 0.4 % [A, SPEC R13 split]
SIG_OS = 2.0e-3                 # loop offset, sigma <= 2.0 mV = 0.4 % of V_REF [A, SPEC R13 split]
V_DEG_MAX = 0.26                # I x R_s <= 0.26 V: the pass device's headroom under the cascode at ss / 85 C / 3.0 V [D, measured -3 mV at 0.31 V]
C_F_UNITS = 4                   # filter units at node a: duty sensitivity C_UNIT / (C_F + C_UNIT) = 0.2 % per % (R9; the pair gate adds to C_F) vs loop speed [D]
C_T_UNITS = 8                   # V_REF tap capacitor [A]
C_PAR_A = 5e-15                 # junction + gate parasitics at node a [A]
PM_TARGET_RATIO = 4.4           # omega_u <= p_A / 4.4 [A]: the weak-inversion fold (0.054 uA) adds poles near 2 MHz; p_A / 2.5 gave 51 deg at ff, p_A / 4 59.8 deg
V_MARGIN = 0.05                 # headroom margin on every window edge (V) [A]
KT = 1.380649e-23 * 300.15

say_lines = []


def say(k, v, fmt="%.6g"):
    print(("size_%s = " + fmt) % (k, v))


def mim_model_c(w, vbias, mim="typical"):
    deck = (head(mim=mim) + "V1 a 0 DC %.4f AC 1\nXC a 0 cap_mim_2f0_m4m5_noshield c_width=%g c_length=%g\n"
            ".control\nac lin 1 1k 1k\nlet cm = abs(imag(i(v1)))/(2*pi*1000)\necho \"cmim = $&cm\"\nquit\n.endc\n.end\n"
            % (vbias, w, w))
    return grab(ng(os.path.join(WORK, "mim_%s" % mim), deck), "cmim")


# ---------------------------------------------------------------- 1. the current
c_unit = {m: mim_model_c(C_UNIT_SIDE, V_REF / 2, m) for m in ("typical", "ss", "ff")}
i_ref = c_unit["typical"] * V_REF * F_CLK
say("c_unit_ff", c_unit["typical"] * 1e15)
say("i_ref_ua", i_ref * 1e6)
say("i_ref_mim_ss_ua", c_unit["ss"] * V_REF * F_CLK * 1e6)
say("i_ref_mim_ff_ua", c_unit["ff"] * V_REF * F_CLK * 1e6)

# ---------------------------------------------------------------- 2. the divider
r_u = ic.res_unit()
v_unit = VDD / N_DIV
i_div = VDD / (N_DIV * r_u)
say("r_unit_kohm", r_u * 1e-3)
say("i_div_ua", i_div * 1e6)
TAP_REF = 5

# ---------------------------------------------------------------- 3. the pass mirror
P = ic.Table("pfet_03v3")
N = ic.Table("nfet_03v3")


def pass_point(nf):
    """|Vgs|, gm/I and Vdsat of one pass device of nf fingers carrying i_ref at V_SD 0.3 V."""
    i_f = i_ref / nf
    vgs = P.vgs_for(L_P, WF_P, i_f, 0.3)
    gm = P.at("gm", L_P, WF_P, vgs, 0.3)
    return vgs, gm / i_f, P.at("vdsat", L_P, WF_P, vgs, 0.3)


chosen = None
for nf in range(2, 41, 2):
    vgs1, gmid1, vdsat1 = pass_point(nf)
    rs_units = int(round(V_DEG_MAX / i_ref / r_u))
    v_deg = i_ref * rs_units * r_u
    sig = ic.sig_dvt("pfet", L_P, WF_P, nf) / (1.0 / gmid1 + v_deg)
    if sig <= SIG_MIRROR:
        chosen = (nf, rs_units, v_deg, sig, vgs1, gmid1, vdsat1)
        break
if chosen is None:
    raise SystemExit("FAIL: no pass-mirror finger count meets the mismatch rule")
NF_P, RS_UNITS, v_deg, sig_mirror, vgs1, gmid1, vdsat1 = chosen
say("pass_nf", NF_P, "%d")
say("rs_units", RS_UNITS, "%d")
say("v_deg_v", v_deg)
say("pass_vgs_v", vgs1)
say("pass_gmid", gmid1)
say("mirror_sigma_pct", 100 * sig_mirror)
gm1 = gmid1 * i_ref
gm1_eff = gm1 / (1 + gm1 * RS_UNITS * r_u)          # degenerated transconductance [D]

# ---------------------------------------------------------------- 4. the cascodes and their tap
vgs_c = P.vgs_for(L_C, WF_C, i_ref / NF_C, 0.5)
vdsat_c = P.at("vdsat", L_C, WF_C, vgs_c, 0.5)
win_lo = V_RAMP_HI + vdsat_c - vgs_c + V_MARGIN            # the output cascode saturated at the ramp top
win_hi = VDD - v_deg - vdsat1 - vgs_c - V_MARGIN            # the pass device saturated
say("casp_window_lo_v", win_lo)
say("casp_window_hi_v", win_hi)
# V_CASP from a Vgs-referenced stack (a divider tap cannot follow Vt over the corners: tap 18 put the pass
# device 0.6 V into triode at ss / 0 C / 3.0 V): AVDD - |Vgs_D1| (wide, weak) - |Vgs_D2| (the cascode's geometry)
i_b = I_BIAS / NF_B
i_sink = i_b * SINK_RATIO[0] / SINK_RATIO[1]               # the nb copies: fold sinks and the V_CASP stack's sink [D]
vgs_d1 = P.vgs_for(L_C, WF_D1, i_sink / NF_D1, 0.5)
vgs_d2 = P.vgs_for(L_C, WF_C, i_sink, 0.5)
v_casp = VDD - vgs_d1 - vgs_d2
v_sd1 = VDD - v_deg - (v_casp + vgs_c)                      # the pass device's V_SD under its cascode [D]
say("casp_v", v_casp)
say("pass_vsd_v", v_sd1)
say("pass_vsd_margin_v", v_sd1 - vdsat1)
say("ramp_top_limit_v", v_casp + vgs_c - vdsat_c)
if v_sd1 - vdsat1 < 0.05:
    print("FAIL: the pass device's V_SD margin under the Vgs-referenced cascode bias is %.3f V" % (v_sd1 - vdsat1))
if v_casp + vgs_c - vdsat_c < V_RAMP_HI:
    print("FAIL: the output cascode leaves saturation below the ramp top (%.3f V)" % (v_casp + vgs_c - vdsat_c))

# ---------------------------------------------------------------- 5. the OTA and the compensation
i_pair = i_b / 2
i_fold = i_sink - i_pair
# Offset of the folded cascode, input-referred: the pair, the sinks x gm_n / gm_in, the loads x gm_l / gm_in.
# The pair and the sinks get the same finger count, the smallest that meets SIG_OS [D].
vgs_l = P.vgs_for(L_OL, WF_OL, i_fold / NF_OL, 0.8)
gm_l = P.at("gm", L_OL, WF_OL, vgs_l, 0.8) * NF_OL
sig_l = ic.sig_dvt("pfet", L_OL, WF_OL, NF_OL)
chosen = None
for nf in range(2 * SINK_RATIO[0], 81, 2 * SINK_RATIO[0]):
    vgs_in = P.vgs_for(L_I, WF_I, i_pair / nf, 1.0)
    gm_in = P.at("gm", L_I, WF_I, vgs_in, 1.0) * nf
    vgs_nb = N.vgs_for(L_N, WF_N, i_sink / nf, 0.3)
    gm_n = N.at("gm", L_N, WF_N, vgs_nb, 0.3) * nf
    sig_p, sig_n = ic.sig_dvt("pfet", L_I, WF_I, nf), ic.sig_dvt("nfet", L_N, WF_N, nf)
    sig_os = math.sqrt(sig_p ** 2 + (gm_n / gm_in * sig_n) ** 2 + (gm_l / gm_in * sig_l) ** 2)
    if sig_os <= SIG_OS:
        chosen = (nf, vgs_in, gm_in, vgs_nb, gm_n, sig_p, sig_n, sig_os)
        break
if chosen is None:
    raise SystemExit("FAIL: no pair / sink finger count meets the offset budget")
NF_I, vgs_in, gm_in, vgs_nb, gm_n, sig_p, sig_n, sig_os = chosen
NF_N = NF_I
NF_NB = NF_N * SINK_RATIO[1] // SINK_RATIO[0]
say("ota_tail_ua", i_b * 1e6)
say("ota_sink_ua", i_sink * 1e6)
say("ota_fold_ua", i_fold * 1e6)
say("ota_pair_nf", NF_I, "%d")
say("ota_pair_gmid", gm_in / i_pair)
say("ota_gm_us", gm_in * 1e6)
say("ota_gmn_over_gmin", gm_n / gm_in)
say("ota_gml_over_gmin", gm_l / gm_in)
say("ota_offset_sigma_mv", sig_os * 1e3)
say("ota_offset_sigma_pct", 100 * sig_os / V_REF)
say("total_sigma_pct", 100 * math.hypot(sig_os / V_REF, sig_mirror))
# V_CASN from a Vgs-referenced stack: Vgs(ND1, the cascode's geometry) + Vgs(ND2, wide, weak), so the fold
# node sits ~Vgs(ND2) above avss at every corner (a divider tap put the sinks in triode at ss / 0 C / 3.0 V)
vdsat_sink = N.at("vdsat", L_N, WF_N, vgs_nb, 0.3)
vgs_nc = N.vgs_for(L_OC, WF_OC, i_fold, 0.5, vsb=0.2)
vgs_nd1 = N.vgs_for(L_OC, WF_OC, i_b, 0.5, vsb=0.5)
vgs_nd2 = N.vgs_for(L_OC, WF_ND2, i_b, 0.5)
v_casn = vgs_nd1 + vgs_nd2
say("casn_v", v_casn)
say("fold_node_v", v_casn - vgs_nc)
say("sink_vds_margin_v", v_casn - vgs_nc - vdsat_sink)
# the loop: node a pole, unity frequency, compensation units
c_f = C_F_UNITS * c_unit["typical"]
g_a = F_CLK * c_unit["typical"]
p_a = g_a / (c_f + c_unit["typical"] + C_PAR_A)           # rad/s [D]
omega_u = p_a / PM_TARGET_RATIO
c_g_units = int(math.ceil(gm_in / omega_u / c_unit["typical"]))
c_g = c_g_units * c_unit["typical"]
say("p_a_khz", p_a / 2 / math.pi * 1e-3)
say("omega_u_khz", gm_in / c_g / 2 / math.pi * 1e-3)
say("c_g_units", c_g_units, "%d")
say("c_g_pf", c_g * 1e12)
say("ripple_a_mv", 1e3 * c_unit["typical"] * V_REF / (c_f + c_unit["typical"]))
say("duty_sens_pct_per_pct", c_unit["typical"] / (c_f + c_unit["typical"]))   # dI/I (%) per 1 % of duty: ripple/V_REF x 0.01 x 100 [D]
say("loop_gain_pass", gm1_eff / g_a)

# ---------------------------------------------------------------- 6. predictions
rout_est = (1.0 / (P.at("gds", L_C, WF_C, vgs_c, 0.5) * NF_C)) * \
    (P.at("gm", L_C, WF_C, vgs_c, 0.5) * NF_C) * (1.0 / (P.at("gds", L_P, WF_P, vgs1, 0.3) * NF_P)) * (1 + gm1 * RS_UNITS * r_u)
say("rout_est_gohm", rout_est * 1e-9)
i_avdd = i_ref * 2 + i_div + I_BIAS + 3 * i_b + 3 * i_sink
say("power_avdd_est_uw", i_avdd * VDD * 1e6)
say("power_dvdd_est_uw", 26.0)            # [M] 7 cells at 20 MHz measured 26 uW
mim_units = 1 + C_F_UNITS + C_T_UNITS + c_g_units
res_units = N_DIV + 2 * RS_UNITS
say("mim_units", mim_units, "%d")
say("res_units", res_units, "%d")
say("area_est_um2", mim_units * 25 + res_units * 20 * 2.0 + 60)
say("noise_rs_thermal_pa_rthz", 1e12 * math.sqrt(2 * 4 * KT / (RS_UNITS * r_u)))

# ---------------------------------------------------------------- the netlist
L = []
L.append("* ic_source -- the I/C current source of the 8-bit ADC's ramp (SPEC.md, DESIGN_RECIPE.md).")
L.append("* I = C_UNIT x V_REF x F_CLK = %.2f fF x %.3f V x %.0f MHz = %.4f uA: one unit MIM switched at the count"
         % (c_unit["typical"] * 1e15, V_REF, F_CLK * 1e-6, i_ref * 1e6))
L.append("* clock against node a, held at V_REF (tap %d of %d) by a folded-cascode OTA through the degenerated," % (TAP_REF, N_DIV))
L.append("* cascoded pass device XM1; XMO (identical) delivers the current to the ramp. GENERATED by size_ic.py.")
L.append("* Non-overlapping phases from the frozen standard cells (the bench includes")
L.append("*   .include %s" % ic.STD_LIB)
L.append("* ); the switch drivers sit on dvdd / dvss like the cells' latches.")
L.append("* Ports: iout (to vramp), ibias (bias_gen's 3.25 uA ramp sink), clk (cnt_clk), avdd avss dvdd dvss.")
L.append(".subckt ic_source iout ibias clk avdd avss dvdd dvss")
L.append("* ---- the reference divider: %d strips (%d over vref, %d under); the cascode biases are Vgs-referenced stacks" % (N_DIV, N_DIV - TAP_REF, TAP_REF))


def chain(name, n, top, bottom, mid):
    """n identical 1 x 20 um strips in SERIES as one arrayed instance name[n-1:0] (xschem's vector instance):
    strip k has P = top (k = n-1) else mid[k], M = bottom (k = 0) else mid[k-1]; M is the first terminal."""
    for k in range(n - 1, -1, -1):
        p_ = top if k == n - 1 else "%s[%d]" % (mid, k)
        m_ = bottom if k == 0 else "%s[%d]" % (mid, k - 1)
        L.append("%s[%d] %s %s avss ppolyf_u_3k r_width=1u r_length=20u" % (name, k, m_, p_))


chain("XRU", N_DIV - TAP_REF, "avdd", "vref", "ru")      # the upper 28 strips
chain("XRL", TAP_REF, "vref", "avss", "rl")              # the lower 5 strips
L.append("XCT vref avss cap_mim_2f0_m4m5_noshield c_width=%s c_length=%s m=%d" % (um(C_UNIT_SIDE), um(C_UNIT_SIDE), C_T_UNITS))
L.append("* ---- the switched unit capacitor at node a (bottom plate on avss, as the ramp's)")
L.append("XCU ct avss cap_mim_2f0_m4m5_noshield c_width=%s c_length=%s m=1" % (um(C_UNIT_SIDE), um(C_UNIT_SIDE)))
L.append("XSA a phi1 ct avss nfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_SW * 1e-6), um(W_SW * 1e-6)))
L.append("XSG ct phi2 avss avss nfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_SW * 1e-6), um(W_SW * 1e-6)))
L.append("XCF a avss cap_mim_2f0_m4m5_noshield c_width=%s c_length=%s m=%d" % (um(C_UNIT_SIDE), um(C_UNIT_SIDE), C_F_UNITS))
L.append("* ---- non-overlapping phi1 (a <-> ct) / phi2 (ct <-> avss): phi1 = clk & !phi2, phi2 = !clk & !phi1")
L.append("XI0 dvdd dvdd dvss dvss clkb clk gf180mcu_as_sc_mcu7t3v3__inv_2")
L.append("XNR1 dvdd dvdd dvss dvss p1 phi2 clkb gf180mcu_as_sc_mcu7t3v3__nor2_2")
L.append("XNR2 dvdd dvdd dvss dvss p2 phi1 clk gf180mcu_as_sc_mcu7t3v3__nor2_2")
L.append("XI1 dvdd dvdd dvss dvss p1b p1 gf180mcu_as_sc_mcu7t3v3__inv_2")
L.append("XI2 dvdd dvdd dvss dvss phi1 p1b gf180mcu_as_sc_mcu7t3v3__inv_2")
L.append("XI3 dvdd dvdd dvss dvss p2b p2 gf180mcu_as_sc_mcu7t3v3__inv_2")
L.append("XI4 dvdd dvdd dvss dvss phi2 p2b gf180mcu_as_sc_mcu7t3v3__inv_2")
L.append("* ---- the pass mirror: %d strips of degeneration (%.2f V), %d fingers, cascoded; XM1 feeds node a, XMO the ramp"
         % (RS_UNITS, v_deg, NF_P))
chain("XRS1", RS_UNITS, "avdd", "s1", "s1r")              # RS_UNITS strips in SERIES (m= would parallel them)
L.append("XM1 d1 vg s1 avdd pfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_P * 1e-6), um(WF_P * NF_P * 1e-6), NF_P))
L.append("XM1C a vcasp d1 avdd pfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_C * 1e-6), um(WF_C * NF_C * 1e-6), NF_C))
chain("XRS2", RS_UNITS, "avdd", "s2", "s2r")
L.append("XMO d2 vg s2 avdd pfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_P * 1e-6), um(WF_P * NF_P * 1e-6), NF_P))
L.append("XMOC iout vcasp d2 avdd pfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_C * 1e-6), um(WF_C * NF_C * 1e-6), NF_C))
L.append("* ---- the gate node: compensation (%d units) and the start-up pre-charge (two stacked diodes)" % c_g_units)
L.append("XCG vg avss cap_mim_2f0_m4m5_noshield c_width=%s c_length=%s m=%d" % (um(C_UNIT_SIDE), um(C_UNIT_SIDE), c_g_units))
L.append("XSU1 su su avdd avdd pfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_SU * 1e-6), um(W_SU * 1e-6)))
L.append("XSU2 vg vg su avdd pfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_SU * 1e-6), um(W_SU * 1e-6)))
L.append("* ---- bias: ibias into a %d-finger diode (bias_gen's ramp sink, XRD's geometry); one-finger copies" % NF_B)
L.append("XPB ibias ibias avdd avdd pfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_B * 1e-6), um(WF_B * NF_B * 1e-6), NF_B))
L.append("XPT ts ibias avdd avdd pfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_B * 1e-6), um(WF_B * 1e-6)))
L.append("XPNB nb ibias avdd avdd pfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_B * 1e-6), um(WF_B * 1e-6)))
L.append("XNB nb nb avss avss nfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_N * 1e-6), um(WF_N * NF_NB * 1e-6), NF_NB))
L.append("* ---- cascode biases: vcasn = Vgs(ND1) + Vgs(ND2 wide); vcasp = avdd - |Vgs(D1 wide)| - |Vgs(D2)|")
L.append("XPNC vcasn ibias avdd avdd pfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_B * 1e-6), um(WF_B * 1e-6)))
L.append("XND1 vcasn vcasn ncm avss nfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_OC * 1e-6), um(WF_OC * 1e-6)))
L.append("XND2 ncm ncm avss avss nfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_OC * 1e-6), um(WF_ND2 * NF_ND2 * 1e-6), NF_ND2))
L.append("XPD1 pcm pcm avdd avdd pfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_C * 1e-6), um(WF_D1 * NF_D1 * 1e-6), NF_D1))
L.append("XPD2 vcasp vcasp pcm avdd pfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_C * 1e-6), um(WF_C * 1e-6)))
L.append("XNCS vcasp nb avss avss nfet_03v3 L=%s W=%s nf=%d m=1" % (um(L_N * 1e-6), um(WF_N * NF_N * 1e-6), NF_N))
L.append("* ---- folded-cascode OTA: PMOS pair (a, vref), NMOS fold sinks, cascodes, cascoded PMOS mirror load; output vg")
L.append("* ---- (no chopper: pair and sinks sized for sigma(Vos) %.2f mV = %.2f %% of I)" % (sig_os * 1e3, 100 * sig_os / V_REF))
pi_ = (um(L_I * 1e-6), um(WF_I * NF_I * 1e-6), NF_I)
pn_ = (um(L_N * 1e-6), um(WF_N * NF_N * 1e-6), NF_N)
pl_ = (um(L_OL * 1e-6), um(WF_OL * NF_OL * 1e-6), NF_OL)
pc_ = (um(L_OLC * 1e-6), um(WF_OL * 1e-6))
L.append("XIA fh1 a ts avdd pfet_03v3 L=%s W=%s nf=%d m=1" % pi_)
L.append("XIR fh2 vref ts avdd pfet_03v3 L=%s W=%s nf=%d m=1" % pi_)
L.append("XN1 fh1 nb avss avss nfet_03v3 L=%s W=%s nf=%d m=1" % pn_)
L.append("XN2 fh2 nb avss avss nfet_03v3 L=%s W=%s nf=%d m=1" % pn_)
L.append("XNC1 dl vcasn fh1 avss nfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_OC * 1e-6), um(WF_OC * 1e-6)))
L.append("XNC2 vg vcasn fh2 avss nfet_03v3 L=%s W=%s nf=1 m=1" % (um(L_OC * 1e-6), um(WF_OC * 1e-6)))
L.append("XPL1 sl1 dl avdd avdd pfet_03v3 L=%s W=%s nf=%d m=1" % pl_)
L.append("XPLC1 dl vcasp sl1 avdd pfet_03v3 L=%s W=%s nf=1 m=1" % pc_)
L.append("XPL2 sl2 dl avdd avdd pfet_03v3 L=%s W=%s nf=%d m=1" % pl_)
L.append("XPLC2 vg vcasp sl2 avdd pfet_03v3 L=%s W=%s nf=1 m=1" % pc_)
L.append(".ends ic_source")
text = "\n".join(L) + "\n"
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
open(os.path.join(OUT, "ic_source.spice"), "w").write(text)

rec = {"params": dict(nf_pass=NF_P, rs_units=RS_UNITS, c_g_units=c_g_units, c_f_units=C_F_UNITS, c_t_units=C_T_UNITS,
                      tap_ref=TAP_REF, n_div=N_DIV, l_pass_um=L_P, wf_pass_um=WF_P, w_sw_um=W_SW,
                      nf_pair=NF_I, nf_sink=NF_N, nf_nb=NF_NB, nf_load=NF_OL),
       "predicted": dict(i_ref_ua=i_ref * 1e6, c_unit_ff=c_unit["typical"] * 1e15, c_unit_ss_ff=c_unit["ss"] * 1e15,
                         c_unit_ff_ff=c_unit["ff"] * 1e15, v_ref=V_REF, r_unit_kohm=r_u * 1e-3, v_deg_v=v_deg,
                         mirror_sigma_pct=100 * sig_mirror, ota_offset_sigma_mv=sig_os * 1e3,
                         total_sigma_pct=100 * math.hypot(sig_os / V_REF, sig_mirror), i_sink_ua=i_sink * 1e6, casp_v=v_casp, casn_v=v_casn, pass_vsd_v=v_sd1,
                         p_a_khz=p_a / 2 / math.pi * 1e-3, omega_u_khz=gm_in / c_g / 2 / math.pi * 1e-3,
                         c_g_pf=c_g * 1e12, ripple_a_mv=1e3 * c_unit["typical"] * V_REF / (c_f + c_unit["typical"]),
                         rout_est_gohm=rout_est * 1e-9, power_avdd_est_uw=i_avdd * VDD * 1e6,
                         mim_units=mim_units, res_units=res_units),
       "contract": dict(v_ramp_lo=ic.V_RAMP_LO, v_ramp_hi=V_RAMP_HI, f_clk_mhz=F_CLK * 1e-6, i_bias_ua=I_BIAS * 1e6)}
json.dump(rec, open(os.path.join(OUT, "data", "sizing.json"), "w"), indent=1)
print("REPORT: ic_source sized: I = %.2f fF x %.3f V x 20 MHz = %.4f uA; pass mirror %d x %.0f um at L %.0f um on %d strips "
      "(%.2f V), V_CASP %.2f V / V_CASN %.2f V from Vgs stacks, OTA tail %.3f uA, pair / sinks %d fingers (sigma(Vos) %.2f mV), C_g %d units (%.2f pF), C_F %d units; %d MIM units, %d strips -> %s"
      % (c_unit["typical"] * 1e15, V_REF, i_ref * 1e6, NF_P, WF_P, L_P, RS_UNITS, v_deg, v_casp, v_casn,
         i_b * 1e6, NF_I, sig_os * 1e3, c_g_units, c_g * 1e12, C_F_UNITS, mim_units, res_units, os.path.join(OUT, "ic_source.spice")))
