"""Size the ramp generator (ramp_gen.spice) from the ADC specification.

    python3 size_ramp.py            writes data/ramp_gen_params.spice and
                                    data/sizing.json, prints name = value lines

The chain (DESIGN_RECIPE.md has the derivations; labels [D] derived,
[P] PDK tables / simulation, [A] assumed):

  1. C_INT [A, the user's 2-4 pF window]: 4 pF, the top of the window,
     because every noise term of the ramp's own current chain scales as
     1/sqrt(I_INT) and I_INT = C_INT x SLOPE.  MIM 2f0, square.
  2. I_INT = C_INT x SLOPE [D]; solved by simulation (op in reset mode, where
     the sink current is the slope current) by bisecting the pbias slave W.
  3. Sink XNS / diode XND [P]: NMOS, L = 20 um, gm/Id 6 (strong inversion:
     lowest thermal and flicker per ampere at the 0.5 V virtual ground,
     Vdsat ~0.27 V leaves > 0.2 V of margin), diode KD = 4 x the sink so the
     diode's noise enters at 1/KD.
  4. pbias slave XPS [P]: L = 4 um (16x the area of an L = 1 um slave at the
     same current: its flicker enters 1:1 in relative terms).
  5. OTA, two-stage Miller [D]: unity-gain crossover F_U = 4 MHz, so the
     velocity error S / (2 pi F_U) is 0.8 LSB and settles in ~3 counts, and
     the S1-connection kick decays by e^-2.3 before the count starts;
     CC = 0.5 pF -> gm1 = 2 pi F_U CC; input pair gm/Id 10 -> slew
     I_TAIL / CC = 5 V/us (the end-of-ramp collapse back to VR_LO);
     p2 = gm2 / C_L >= 3.0 x F_U at C_L = C_OUT + loads, Rz = 1.6 / gm2
     (zero in the left half plane): PM 65 deg measured. 2.2 and 1.2 gave
     60 deg and a 23 % undershoot after the S1 kick (explore/damp.sh).
  6. C_OUT [D]: the S1-connection kick of NCELL = 4 full-scale cells,
     4 x 10 fF x 1.5 V = 60 fC, kept <= 5 LSB (29 mV) at the reset level:
     C_OUT >= 2.0 pF, MIM (linear; the varactor cap_nmos_03v3_b, denser,
     stalls the transient at the sample edge in its behavioural model).
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
LUT = os.path.join(BLOCK, "..", "..", "simulations", "gf180_gmid_lut", "data", "gmid_curves.csv")

LSB = 1.5 / 256
SLOPE = LSB / 50e-9                 # 117187.5 V/s
IREF = 3.1314e-6                    # bias_gen fixed leg, W 20 um, L 1 um
WREF = 20e-6

C_INT_TARGET = 4.0e-12
F_U = float(os.environ.get("RG_F_U", "4.0e6"))
CC_TARGET = float(os.environ.get("RG_CC", "0.5e-12"))
GMID_IN = 10.0
GMID_LOAD = 5.0
GMID_M5 = float(os.environ.get("RG_GMID5", "12.0"))
P2_RATIO = float(os.environ.get("RG_P2", "3.0"))
C_OUT_TARGET = float(os.environ.get("RG_COUT", "2.0e-12"))
NCELL = 4
CLOAD_CELL = 10e-15
KD = 4
L1_UM = float(os.environ.get("RG_L1_UM", "4"))
L3_UM = float(os.environ.get("RG_L3_UM", "12"))


def mim_c(w):
    """cap_mim_2f0_m4m5_noshield, square plate w x w (the form tb_unit_cell_bps uses)."""
    return 1.99e-3 * w * w + 2.383e-10 * 2 * (2 * w)


def mim_model_c(w):
    """The PDK model's capacitance of a square w x w cap_mim_2f0_m4m5_noshield,
    from an ngspice AC probe at 1 kHz with 0.8 V across it (mid-ramp). The
    first sizing used mim_c() and the slope came out 0.11 % low."""
    deck = ("* mim probe\n.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
            ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical\n"
            ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical\n"
            "V1 a 0 DC 0.8 AC 1\nXC a 0 cap_mim_2f0_m4m5_noshield c_width=%g c_length=%g\n"
            ".control\nac lin 1 1k 1k\nlet cm = abs(imag(i(v1)))/(2*pi*1000)\necho \"cmim = $&cm\"\nquit\n"
            ".endc\n.end\n" % (w, w))
    with tempfile.TemporaryDirectory() as td:
        pth = os.path.join(td, "mim.spice")
        open(pth, "w").write(deck)
        r = subprocess.run(["ngspice", "-b", pth], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("cmim = "):
            return float(line.split("=")[1])
    sys.exit("FAIL: size_ramp.py: MIM probe gave no capacitance\n" + r.stdout[-1500:])


def mim_side(c):
    lo, hi = 1e-6, 100e-6
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if mim_c(mid) < c else (lo, mid)
    return round(0.5 * (lo + hi) * 1e7) / 1e7          # 0.1 um grid


lut = {}
for line in open(LUT).read().splitlines()[1:]:
    dev, l, gmid, gmgds, idw = line.split(",")[:5]
    lut.setdefault((dev, float(l)), []).append((float(gmid), float(idw), float(gmgds)))


def idw(dev, l_um, gmid):
    rows = sorted(lut[(dev, l_um)])
    g = np.array([r[0] for r in rows])
    i = np.array([r[1] for r in rows])
    return float(np.exp(np.interp(gmid, g, np.log(i))))       # A/m (= uA/um)


def idw_l(dev, l_um, gmid):
    """id/W at any L: the table up to 8 um, beyond it the 8 um row x 8 / L (id/W ~ 1/L)."""
    return idw(dev, l_um, gmid) if l_um <= 8.0 else idw(dev, 8.0, gmid) * 8.0 / l_um


def gmgds(dev, l_um, gmid):
    rows = sorted(lut[(dev, l_um)])
    return float(np.interp(gmid, [r[0] for r in rows], [r[2] for r in rows]))


def um(x):
    return "%.3fu" % (x * 1e6)


def grid(w, step=0.01e-6):
    return max(0.22e-6, round(w / step) * step)


p = {}
# 1-2. integrating capacitor and slope current
p["RG_CIW"] = mim_side(C_INT_TARGET)
c_int_formula = mim_c(p["RG_CIW"])
c_int = mim_model_c(p["RG_CIW"])        # [P] the model's value: the slope is I / this
i_int = c_int * SLOPE
# 3. sink and diode: L = 20 um; id/W at L = 20 from the L = 8 table x 8/20
#    (strong inversion, id/W ~ 1/L), refined by the bisection below
p["RG_LN"] = 20e-6
w_ns = grid(i_int / (idw("nfet_03v3", 8.0, 6.0) * 8.0 / 20.0))
p["RG_WNS"] = w_ns
p["RG_KD"] = KD
p["RG_NFND"] = 2
# 4. pbias slave, L = 4 um
p["RG_LPS"] = 4e-6
p["RG_NFPS"] = 5
# 5. OTA
gm1 = 2 * np.pi * F_U * CC_TARGET
i1 = gm1 / GMID_IN
p["RG_CCW"] = mim_side(CC_TARGET)
cc = mim_c(p["RG_CCW"])
p["RG_L1"] = L1_UM * 1e-6
p["RG_W1"] = grid(i1 / idw_l("pfet_03v3", L1_UM, GMID_IN))
p["RG_NF1"] = 4
i_tail = 2 * i1
p["RG_WT"] = grid(WREF * i_tail / IREF)
p["RG_NFT"] = 4
p["RG_L3"] = L3_UM * 1e-6
p["RG_W3"] = grid(i1 / idw_l("nfet_03v3", L3_UM, GMID_LOAD))
c_out = C_OUT_TARGET
c_load = c_out + NCELL * CLOAD_CELL
gm2 = P2_RATIO * 2 * np.pi * F_U * c_load
i2 = gm2 / GMID_M5
p["RG_L5"] = 1e-6
p["RG_W5"] = grid(i2 / idw("nfet_03v3", 1.0, GMID_M5))
p["RG_NF5"] = 2
i_out = i_int + c_load * SLOPE
w6 = WREF * (i2 + i_out) / IREF
# one instance stays inside the widest 3.3 V model bin (W < 100 um, binned on total W)
p["RG_M6"] = int(np.ceil(w6 / 95e-6))
p["RG_W6"] = grid(w6 / p["RG_M6"])
p["RG_NF6"] = 16
rz = float(os.environ.get("RG_RZK", "1.6")) / gm2
# ppolyf_u: 350 ohm/sq (res_typical), W = 1 um; the end-effect is small at
# these lengths and the AC bench measures the zero it actually places
p["RG_RZL"] = round(rz / 350.0, 1) * 1e-6
p["RG_COW"] = mim_side(c_out)
p["RG_WRST"] = 0.5e-6

# 2. bisect the slave width so that the sink carries exactly I_INT (reset op)
DECK = """* size_ramp.py bisection deck
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice moscap_typical
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice
.include {params}
.include /foss/designs/mixed_signal/ramp_gen/ramp_gen.spice
VDD vdd 0 3.3
VRLO vrlo 0 {vrlo}
VRST rst 0 3.3
XBIAS vdd 0 pbias nbias bias_gen
XRG vramp rst vrlo pbias vdd 0 ramp_gen
.options gmin=1e-15
.control
op
echo "ins = $&@m.xrg.xns.m0[id]"
echo "ips = $&@m.xrg.xps.m0[id]"
echo "im5 = $&@m.xrg.xm5.m0[id]"
echo "im6 = $&@m.xrg.xm6.m0[id]"
echo "im7 = $&@m.xrg.xm7.m0[id]"
echo "vx = $&v(xrg.vx)"
echo "vramp = $&v(vramp)"
echo "gm1 = $&@m.xrg.xm1.m0[gm]"
echo "gm5 = $&@m.xrg.xm5.m0[gm]"
echo "gm3 = $&@m.xrg.xm3.m0[gm]"
echo "nsvdsat = $&@m.xrg.xns.m0[vdsat]"
echo "nsgm = $&@m.xrg.xns.m0[gm]"
quit
.endc
.end
"""


def fmt(k, v):
    if k in ("RG_KD", "RG_NFND", "RG_NFPS", "RG_NF1", "RG_NFT", "RG_NF5", "RG_NF6", "RG_M6"):
        return "%d" % v
    return um(v)


def write_params(path, q):
    with open(path, "w") as f:
        f.write("* Written by size_ramp.py. Do not edit by hand; re-run the sizer.\n")
        f.write("* Rationale: DESIGN_RECIPE.md. Topology: ../ramp_gen.spice.\n")
        for k in sorted(q):
            f.write(".param %s=%s\n" % (k, fmt(k, q[k])))


def op(q, vrlo=0.5):
    with tempfile.TemporaryDirectory() as td:
        pp = os.path.join(td, "params.spice")
        write_params(pp, q)
        dk = os.path.join(td, "op.spice")
        open(dk, "w").write(DECK.format(params=pp, vrlo="%.6f" % vrlo))
        r = subprocess.run(["ngspice", "-b", dk], capture_output=True, text=True)
    vals = {}
    for line in r.stdout.splitlines():
        if " = " in line and line.split(" = ")[0].strip() in (
                "ins", "ips", "im5", "im6", "im7", "vx", "vramp", "gm1", "gm5", "gm3", "nsvdsat", "nsgm"):
            k, v = line.split(" = ")
            vals[k.strip()] = abs(float(v))
    if "ins" not in vals:
        sys.exit("FAIL: size_ramp.py: ngspice op gave no sink current\n" + r.stdout[-2000:] + r.stderr[-2000:])
    return vals


# The sink must carry I_INT at the virtual ground it sees WHILE RAMPING. The
# OTA's input then carries the velocity error Cc x SLOPE / gm1 (~4.6 mV), so vx
# sits that much below its reset value and the sink's V_DS with it; near its
# saturation edge that is 0.1 % of current (the first sizing, at the reset vx,
# came out 0.09-0.11 % slow). The op is therefore solved with vrlo lowered by
# the predicted velocity error, which puts vx where the ramp will hold it.
p["RG_WPS"] = 50e-6
v0 = op(p)
vel = SLOPE * cc / v0["gm1"]
def bisect(target):
    lo, hi = 10e-6, 95e-6          # the widest 3.3 V model bin ends at W = 100 um
    for _ in range(30):
        p["RG_WPS"] = 0.5 * (lo + hi)
        vv = op(p, 0.5 - vel)
        lo, hi = (p["RG_WPS"], hi) if vv["ins"] < target else (lo, p["RG_WPS"])
    p["RG_WPS"] = grid(0.5 * (lo + hi))
    return op(p, 0.5 - vel)


def tran_ratio(q):
    """The trim step. The slope current in the settled transient is not the DC
    operating point's: the bias generator's transient state sits ~70 uV of
    pbias away from its op (the slave and the sink carry 0.095 % less, measured
    with tb_ramp; the ramp's own devices are not the cause). One run of the
    ramp bench returns (mean sink current over the ramp) / (op sink current)."""
    with tempfile.TemporaryDirectory() as td:
        pp = os.path.join(td, "params.spice")
        write_params(pp, q)
        tb = open(os.path.join(BLOCK, "tb_ramp.spice")).read().replace(
            "/foss/designs/mixed_signal/ramp_gen/data/ramp_gen_params.spice", pp)
        open(os.path.join(td, "tb.spice"), "w").write(tb)
        open(os.path.join(td, "case.spice"), "w").write(
            ".param NCELL=4\n.param VKICK=2.0\n.param VDDX=1\n.param TPRE=0\n")
        r = subprocess.run(["ngspice", "-b", "tb.spice"], cwd=td, capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("i_ns "):
            return float(line.split("=")[1].split()[0])
    sys.exit("FAIL: size_ramp.py: the trim transient gave no sink current\n" + r.stdout[-1500:])


v = bisect(i_int)
trim = tran_ratio(p) / v["ins"]
v = bisect(i_int / trim)

OUT = os.path.join(BLOCK, os.environ.get("RG_OUT", "data"))
os.makedirs(OUT, exist_ok=True)
write_params(os.path.join(OUT, "ramp_gen_params.spice"), p)
pred = {
    "c_int": c_int, "c_int_formula": c_int_formula, "i_int": i_int, "tran_trim": trim, "i_ns_op": v["ins"], "slope_op": v["ins"] / c_int,
    "i_ps_op": v["ips"], "i_m5_op": v["im5"], "i_m6_op": v["im6"], "i_tail_op": v["im7"],
    "gm1_target": gm1, "gm1_op": v["gm1"], "gm5_target": gm2, "gm5_op": v["gm5"], "gm3_op": v["gm3"],
    "cc": cc, "c_out": c_out, "c_load": c_load, "rz_target": rz,
    "f_u_pred": v["gm1"] / (2 * np.pi * cc), "p2_pred": v["gm5"] / (2 * np.pi * c_load),
    "slew_pred": v["im7"] / cc, "vel_err_pred_mv": SLOPE / (v["gm1"] / cc) * 1e3,
    "vos_op_mv": (v["vx"] - (0.5 - vel)) * 1e3, "vel_err_op_mv": vel * 1e3, "ns_vdsat": v["nsvdsat"], "ns_gmid": v["nsgm"] / v["ins"],
    "i_supply_pred": v["ips"] + v["im6"] + v["im7"],
    "a1_pred": gmgds("pfet_03v3", 4.0, GMID_IN), "kick_mv_pred": NCELL * CLOAD_CELL * 1.5 / c_load * 1e3,
}
json.dump({"params": {k: (fmt(k, x)) for k, x in p.items()}, "predicted": pred},
          open(os.path.join(OUT, "sizing.json"), "w"), indent=1)
for k in sorted(pred):
    print("size_%s = %.6g" % (k, pred[k]))
print("REPORT: sized C_INT %.3f pF (MIM %s square), I_INT %.4f uA, slave W %s, F_U %.2f MHz, p2/F_U %.2f"
      % (c_int * 1e12, um(p["RG_CIW"]), i_int * 1e6, um(p["RG_WPS"]), pred["f_u_pred"] / 1e6,
         pred["p2_pred"] / pred["f_u_pred"]))
