"""Size ramp_simple.spice from SPEC.md: the ramp capacitor as an array of the
cells' unit MIM, the reset switch, and the current the (ideal, for now) I/C
source delivers.

    python3 size_simple.py            (inside the container, from this block)
        writes ramp_simple.spice and data/sizing.json; RS_OUT=<dir> writes
        both there instead (the `size` phase, which must reproduce the block's)

The chain (DESIGN_RECIPE.md carries the same steps with their labels):

  1. The grid (ADR 0025): LSB = (64.5 mV + 1.5 V + 87.9 mV) / (255 x 0.982),
     SLOPE, the pre-roll reset level VR_LO = 0.5 V - 64.5 mV, the level the
     ramp must reach by count 255 (2.088 V) and its top at count 259 (SPEC
     R1-R4).
  2. The current from the I/C principle [D]: I = C_UNIT x V_REF x F_CLK with
     the cells' 5 um unit MIM (its model value at V_REF [P]), V_REF = 5/33
     AVDD = 0.5 V and the 20 MHz clock: 0.545 uA. It tracks the MIM corner
     (reported at ss / ff) and the supply (ratiometric, as VR_LO and VREF).
  3. The ramp capacitor as N_RAMP units of the same MIM [D]: the slope is then
     the unit-count ratio, I / (N C_UNIT + C_load) = SLOPE, so
     N = (I / SLOPE - NCELL x C_CELL - C_RST) / C_UNIT, rounded (84); the
     residual gain error at typical is reported and calibrated. The C sweep
     of the earlier recipe (2..5 pF) is kept as the record of the knee.
  4. The reset switch W_RST [D, SPEC R8]: Ron from an ngspice probe at typical
     and at ss / 85 C / 3.0 V; the smallest 0.1 um step with
     1.1 x I x Ron_ss <= 0.5 LSB and Ron_ss x C_total <= 30 ns.
  5. Reported for the I/C source (SPEC s.6): the current at the MIM corners,
     the output resistance a bow of 0.05 / 0.15 LSB needs, the noise
     allocation; and for the record: the reset kT/C, the per-decision kick,
     the area.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rs_common import (BLOCK, VDD, LSB, SLOPE, F_CLK, PREROLL, NCNT, VR_LO_TAP as VR_LO, VR_LO_PRE, K_LO, V_TOP, V_NEED,  # noqa: E402
                       NVALID, S_SRC, SLOW, ALPHA, V_REF, C_UNIT_SIDE, NCELL, C_CELL, Q_KICK, head, ng, grab)

OUT = os.path.join(BLOCK, os.environ.get("RS_OUT", ""))
V_MID = 0.5 * (VR_LO + V_TOP)
V_SWING = V_TOP - VR_LO
C_CELL_NEAR = 34e-15                          # a cell within a few LSB of its trip [D, SPEC R7]
I_ACC = 0.10                                  # the current source's accuracy band the switch is sized for [A]
TAU_MAX = 30e-9                               # SPEC R8b
DROP_MAX = 0.5 * LSB                          # SPEC R8a
K_B, T_K = 1.380649e-23, 300.15
CJ_N = 1.02e-15 / 1e-6                        # NMOS drain junction per um of W at 0.5 V [P]
CJ_N_TOP = 0.81e-15 / 1e-6                    # ... at 2.0 V [P]
out_lines = []


def say(key, val, fmt="%.6g"):
    out_lines.append(("size_%s = " + fmt) % (key, val))
    print(out_lines[-1])


def run(deck, tag):
    return ng(os.path.join(BLOCK, "work", "size", tag), deck)


def um(x):
    return "%.3fu" % (x * 1e6)


# ---------------------------------------------------------------- the MIM
def mim_c(w):
    return 1.99e-3 * w * w + 2.383e-10 * 2 * (2 * w)


def mim_side(c):
    lo, hi = 1e-6, 100e-6
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if mim_c(mid) < c else (lo, mid)
    return round(0.5 * (lo + hi) * 1e7) / 1e7


def mim_model_c(w, vbias, mim="typical"):
    deck = (head(mim=mim) + "V1 a 0 DC %.4f AC 1\nXC a 0 cap_mim_2f0_m4m5_noshield c_width=%g c_length=%g\n"
            ".control\nac lin 1 1k 1k\nlet cm = abs(imag(i(v1)))/(2*pi*1000)\necho \"cmim = $&cm\"\nquit\n.endc\n.end\n"
            % (vbias, w, w))
    return grab(run(deck, "mim_%s_%g_%g" % (mim, w * 1e6, vbias)), "cmim")


def ron_probe(w, corner="typical", rcorner="res_typical", temp=27, vdd=VDD):
    """Ron of the reset switch in reset: gate at vdd, source at VR_LO, 1 uA through it."""
    deck = (head(corner, rcorner, "typical", temp) +
            "VG g 0 %g\nVS s 0 %.6f\nIT 0 d 1u\nXS d g s 0 nfet_03v3 L=0.28u W=%s nf=1 m=1\n"
            ".control\nop\nlet ron = (v(d) - v(s)) / 1e-6\necho \"ron = $&ron\"\nquit\n.endc\n.end\n"
            % (vdd, VR_LO, um(w)))
    return grab(run(deck, "ron_%s_%g_%g" % (corner, w * 1e6, temp)), "ron")


# ---------------------------------------------------------------- the netlist
def netlist(n_ramp, c_ramp, i_ramp, w_rst, header=True):
    lines = []
    if header:
        lines += ["* ramp_simple -- the shared ramp of the 8-bit bottom-plate ADC: the ramp capacitor",
                  "* (an array of the cells' 5 um unit MIM) and its reset switch to VR_LO. The ramp",
                  "* current I = C_UNIT x V_REF x F_CLK = %.4f uA enters at vramp from the I/C current" % (i_ramp * 1e6),
                  "* source (../ic_source; an ideal source in this block's benches), so the slope is",
                  "* the unit ratio 1/%d x V_REF x F_CLK and tracks the MIM. GENERATED by size_simple.py" % n_ramp,
                  "* (SPEC.md, DESIGN_RECIPE.md); do not hand-edit.",
                  "*   slope %.2f mV/us on %d x %.2f fF + %d cells x %.0f fF + the switch's junction"
                  % (SLOPE * 1e-3, n_ramp, c_ramp / n_ramp * 1e15, NCELL, C_CELL * 1e15),
                  "*   LSB %.3f mV; reset level VR_LO = %.4f V (vrlo_ref's 7/55 tap; the pre-roll budget asks"
                  % (LSB * 1e3, VR_LO),
                  "*   0.5 V - %.2f LSB = %.4f V); top %.3f V" % (PREROLL, VR_LO_PRE, V_TOP),
                  "* Ports: vramp rst vrlo vss; rst HIGH = reset (vramp held at vrlo).",
                  "* The simulators are the authority, not these lines."]
    lines += [".subckt ramp_simple vramp rst vrlo vss",
              "* ---- the ramp capacitor: %d unit MIMs (M4-M5, 5 um square, as the cells' hold capacitor" % n_ramp,
              "*      and the I/C source's reference capacitor); plate c0 on vramp",
              "XCR vramp vss cap_mim_2f0_m4m5_noshield c_width=%s c_length=%s m=%d" % (um(C_UNIT_SIDE), um(C_UNIT_SIDE), n_ramp),
              "* ---- the reset switch to VR_LO",
              "XRST vramp rst vrlo vss nfet_03v3 L=0.28u W=%s nf=1 m=1" % um(w_rst),
              ".ends ramp_simple"]
    return "\n".join(lines) + "\n"


# ================================================================== the chain
say("lsb_mv", LSB * 1e3)
say("slope_mv_us", SLOPE * 1e-3)
say("vr_lo_v", VR_LO)
say("preroll_lsb", PREROLL)
say("k_lo", K_LO, "%d")
say("vr_lo_pre_v", VR_LO_PRE)
say("v_need_v", V_NEED)
say("v_top_v", V_TOP)
say("v_swing_v", V_SWING)
say("window_codes", 1.5 / LSB)
say("node_max_v", VDD / 2 + ALPHA * (V_TOP - 0.5))        # SPEC R4: VREF + alpha (top - VIN_min), the sensed node

# ---- 2. the current from the I/C principle
c_unit = {m: mim_model_c(C_UNIT_SIDE, V_REF, m) for m in ("typical", "ss", "ff")}
i_ramp = c_unit["typical"] * V_REF * F_CLK
say("v_ref_v", V_REF)
say("f_clk_mhz", F_CLK * 1e-6)
say("c_unit_ff", c_unit["typical"] * 1e15)
say("c_unit_ss_ff", c_unit["ss"] * 1e15)
say("c_unit_ff_ff", c_unit["ff"] * 1e15)
say("i_ramp_ua", i_ramp * 1e6)

# ---- the C sweep (the record of the knee; the C-dependent terms fall as 1/C)
for c_pf in (2.0, 3.0, 4.0, 5.0):
    c = c_pf * 1e-12 + NCELL * C_CELL
    tag = "c%gpf" % c_pf
    say(tag + "_i_ua", c * SLOPE * 1e6)
    say(tag + "_ktc_reset_lsb", np.sqrt(K_B * T_K / c) / LSB)
    say(tag + "_kick3_lsb", 3 * Q_KICK / c / LSB)
    say(tag + "_near_trip_excursion_pct", 100 * (C_CELL_NEAR - C_CELL) / c)
    say(tag + "_mim_area_um2", mim_side(c_pf * 1e-12) ** 2 * 1e12)
    say(tag + "_dump_pc", c_pf * 1e-12 * V_SWING * 1e12)

# ---- 4. the reset switch (W from the drop and the tau at the worst cell)
c_guess = i_ramp / SLOPE
w_rst = 0.5e-6
for w in np.arange(0.5e-6, 4.01e-6, 0.1e-6):
    w = round(w * 1e7) / 1e7
    ron_s = ron_probe(w, "ss", "res_ss", 85, 3.0)
    if (1 + I_ACC) * i_ramp * ron_s <= DROP_MAX and ron_s * c_guess <= TAU_MAX:
        w_rst = w
        break
c_rst = w_rst * CJ_N
# ---- 3. the ramp capacitor as unit MIMs: the slope is the unit ratio
# rounded DOWN: R3 forbids a slow ramp, so the unit rounding leaves the slope on the fast side [D]
n_ramp = int(np.floor((i_ramp / SLOPE - NCELL * C_CELL - c_rst) / c_unit["typical"]))
c_ramp = n_ramp * mim_model_c(C_UNIT_SIDE, V_MID)        # at the mid-ramp voltage [P]
c_tot = c_ramp + NCELL * C_CELL + c_rst
say("n_ramp_units", n_ramp, "%d")
say("c_ramp_pf", c_ramp * 1e12)
say("c_total_pf", c_tot * 1e12)
say("slope_err_design_pct", 100 * (i_ramp / c_tot / SLOPE - 1))
# R3: the source at its slowest (1 - S_SRC) on the fast design slope, against the grid's 0.982
say("slope_slowest_vs_grid", (1 - S_SRC) * i_ramp / c_tot / SLOPE)
say("slow_margin_cell_pct", 100 * ((1 - S_SRC) * i_ramp / c_tot / SLOPE - SLOW))
say("lsb_design_mv", i_ramp / c_tot * 50e-9 * 1e3)
ron_t, ron_s = ron_probe(w_rst), ron_probe(w_rst, "ss", "res_ss", 85, 3.0)
say("w_rst_um", w_rst * 1e6)
say("rst_ron_typ_ohm", ron_t)
say("rst_ron_ss85_3p0_ohm", ron_s)
say("rst_drop_typ_lsb", i_ramp * ron_t / LSB)
say("rst_drop_worst_lsb", (1 + I_ACC) * i_ramp * ron_s / LSB)
say("rst_tau_typ_ns", ron_t * c_tot * 1e9)
say("rst_tau_worst_ns", ron_s * c_tot * 1e9)
say("rst_injection_mv", 0.5 * w_rst * 0.28e-6 * 4.9e-3 * (VDD - VR_LO - 0.7) / c_tot * 1e3)
say("rst_junction_ff", c_rst * 1e15)
say("rst_junction_inl_est_lsb", w_rst * (CJ_N - CJ_N_TOP) / c_tot * 32)

# ---- 5. what the I/C source must deliver (SPEC s.6), and the record
say("src_i_ua", i_ramp * 1e6)
say("src_i_at_mim_ss_ua", c_unit["ss"] * V_REF * F_CLK * 1e6)
say("src_i_at_mim_ff_ua", c_unit["ff"] * V_REF * F_CLK * 1e6)
say("src_rout_for_0p05lsb_gohm", V_SWING * 32 / 0.05 / i_ramp * 1e-9)       # rout = V_A / I, V_A = V_swing x 32 / INL
say("src_rout_for_0p15lsb_gohm", V_SWING * 32 / 0.15 / i_ramp * 1e-9)
say("src_noise_alloc_lsb", 0.11)
say("ktc_reset_lsb", np.sqrt(K_B * T_K / c_tot) / LSB)
say("kick_per_decision_lsb", Q_KICK / c_tot / LSB)
say("area_mim_um2", n_ramp * (C_UNIT_SIDE * 1e6) ** 2)
say("area_mos_gate_um2", w_rst * 0.28e-6 * 1e12)

# ---- write
text = netlist(n_ramp, c_ramp, i_ramp, w_rst)
os.makedirs(os.path.join(OUT, "data") if not os.environ.get("RS_OUT") else OUT, exist_ok=True)
nl = os.path.join(OUT, "ramp_simple.spice")
sz = os.path.join(OUT, "data", "sizing.json") if not os.environ.get("RS_OUT") else os.path.join(OUT, "sizing.json")
open(nl, "w").write(text)
rec = {"params": {"n_ramp_units": n_ramp, "c_unit_side_um": C_UNIT_SIDE * 1e6, "w_rst_um": w_rst * 1e6},
       "grid": {"lsb": LSB, "slope": SLOPE, "vr_lo": VR_LO, "vr_lo_pre": VR_LO_PRE, "v_top": V_TOP, "v_need": V_NEED, "preroll_lsb": PREROLL,
                "ncnt": NCNT, "nvalid": NVALID, "slow": SLOW, "s_src": S_SRC, "v_ref": V_REF, "f_clk": F_CLK},
       "predicted": {k: float(v) for k, v in (ln.split(" = ") for ln in [x[5:] for x in out_lines])}}
json.dump(rec, open(sz, "w"), indent=1)
print("REPORT: ramp_simple sized: %d units of %.2f fF = %.3f pF, C_total %.3f pF, I = C_unit x %.3f V x %g MHz = %.4f uA "
      "(ideal source for now), XRST %.1f um -> %s"
      % (n_ramp, c_unit["typical"] * 1e15, c_ramp * 1e12, c_tot * 1e12, V_REF, F_CLK * 1e-6, i_ramp * 1e6, w_rst * 1e6, nl))
