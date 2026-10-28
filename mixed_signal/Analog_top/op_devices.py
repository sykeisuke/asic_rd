"""The in-macro operating point of analog_top (v5): which devices, resistors and
MIM capacitors the `op` phase records, and at which instants. One list, read by
op_bench.py (writes the measures), op_reduce.py (gm/Id, region, Ron, R = V/I)
and analog_top_sch.py (the table on the analog_top sheet).

Paths are below the bench's macro instance XDUT, as ngspice flattens them
(lower case). Every MOS is a PDK nfet_03v3 / pfet_03v3 subcircuit whose BSIM4
instance is m0, so its operating point is @m.xdut.<path>.m0[<param>]; ngspice
returns id / gm / gds / gmbs including the instance multiplier m (checked: a
m=4 device reads 4.000 x the m=1 one, and op_reduce.py gates KCL at bias_gen's
pb node). A ppolyf_u / ppolyf_u_3k resistor is rt1 - rb - rt2 in series (PDK
sm141064.ngspice); its current is @r.xdut.<path>.rt1[i]. A
cap_mim_2f0_m4m5_noshield is c_cap (sm141064_mim.ngspice); its capacitance is
read back as @c.xdut.<path>.c_cap[capacitance].

States (instants, tb_params.inc times):
  trk   TS0 - 10 ns: every cell tracking (S0, S2 closed, S1 open), the ramp
        held at vrlo; each comparator's inn = vref and inp = vbl, so every
        comparator sits at its trip point (its balanced operating point)
  ramp  TR + 400 ns: the ramp running (8 counts in), all four cells armed
        (S1 closed, bot below vbl), before cell 0 decides (code 17)
"""

STATES = {
    "trk": ("TS0-10n", "every cell tracking; each comparator at its trip point (inn = vref, inp = vbl)"),
    "ramp": ("TR+400n", "ramp running 8 counts in, cells armed (S1 closed), before cell 0 decides"),
}

# (key, path below xdut, block, role, state shown on the sheet)
MOS = [
    # bias_gen_s: NMOS-defined beta multiplier, outputs (+ XOL for vrlo_ref), startup
    ("bg_xmn1", "xbg.xmn1", "bias_gen_s", "core NMOS diode (nb), 10 fingers", "ramp"),
    ("bg_xmn2", "xbg.xmn2", "bias_gen_s", "core NMOS, K = 8 (m 4 x 20 f), source on R", "ramp"),
    ("bg_xmp1", "xbg.xmp1", "bias_gen_s", "core PMOS mirror into nb", "ramp"),
    ("bg_xmp2", "xbg.xmp2", "bias_gen_s", "core PMOS diode (pb)", "ramp"),
    ("bg_xoc0", "xbg.xoc0", "bias_gen_s", "sink icmp0 -> cell 0 comparator diode", "ramp"),
    ("bg_xoc1", "xbg.xoc1", "bias_gen_s", "sink icmp1", "ramp"),
    ("bg_xoc2", "xbg.xoc2", "bias_gen_s", "sink icmp2", "ramp"),
    ("bg_xoc3", "xbg.xoc3", "bias_gen_s", "sink icmp3", "ramp"),
    ("bg_xor", "xbg.xor", "bias_gen_s", "sink iramp -> ramp diode XRD", "ramp"),
    ("bg_xov", "xbg.xov", "bias_gen_s", "source ivref -> XVREF ib", "ramp"),
    ("bg_xol", "xbg.xol", "bias_gen_s", "source ivrlo -> XVRLO ib (v4)", "ramp"),
    ("bg_xsu4", "xbg.xsu4", "bias_gen_s", "startup disengage (off at the op)", "ramp"),
    ("bg_xsu5", "xbg.xsu5", "bias_gen_s", "startup kick (off at the op)", "ramp"),
    ("bg_xsb1", "xbg.xsb1", "bias_gen_s", "startup bleeder PMOS diode 1", "ramp"),
    ("bg_xsb4", "xbg.xsb4", "bias_gen_s", "startup bleeder PMOS diode 4", "ramp"),
    # ramp_simple_d: ramp_simple + its own bias diode, flat
    ("rp_xrd", "xramp.xrd", "ramp_simple_d", "ramp bias PMOS diode (iramp in)", "ramp"),
    ("rp_xps", "xramp.xps", "ramp_simple_d", "ramp current source into the 4 pF MIM", "ramp"),
    ("rp_xrst", "xramp.xrst", "ramp_simple_d", "reset switch vramp -> vrlo (on in trk)", "trk"),
    # vrlo_ref XVRLO: VR_LO shunt regulator (ADR 0018); trk = the reset state,
    # the shunt sinking the keep-alive plus the ramp current through XRST
    ("vl_xmbn", "xvrlo.xmbn", "vrlo_ref XVRLO", "ib NMOS diode (ivrlo in)", "trk"),
    ("vl_xmbn2", "xvrlo.xmbn2", "vrlo_ref XVRLO", "ib mirror -> pb", "trk"),
    ("vl_xmbp", "xvrlo.xmbp", "vrlo_ref XVRLO", "PMOS diode pb", "trk"),
    ("vl_xmt", "xvrlo.xmt", "vrlo_ref XVRLO", "OTA tail PMOS", "trk"),
    ("vl_xmk", "xvrlo.xmk", "vrlo_ref XVRLO", "keep-alive PMOS into vrlo", "trk"),
    ("vl_xm1", "xvrlo.xm1", "vrlo_ref XVRLO", "input PMOS, gate vrlo", "trk"),
    ("vl_xm2", "xvrlo.xm2", "vrlo_ref XVRLO", "input PMOS, gate tap", "trk"),
    ("vl_xm3", "xvrlo.xm3", "vrlo_ref XVRLO", "NMOS load diode d1", "trk"),
    ("vl_xm4", "xvrlo.xm4", "vrlo_ref XVRLO", "NMOS mirror into g", "trk"),
    ("vl_xm5", "xvrlo.xm5", "vrlo_ref XVRLO", "g-node NMOS diode", "trk"),
    ("vl_xms", "xvrlo.xms", "vrlo_ref XVRLO", "NMOS shunt on vrlo", "trk"),
    # midref_buf XVREF (v5: the one buffer, vref = vbl)
    ("vr_xmbn", "xvref.xmbn", "midref_buf XVREF", "ib NMOS diode", "ramp"),
    ("vr_xmbn2", "xvref.xmbn2", "midref_buf XVREF", "ib mirror -> pb", "ramp"),
    ("vr_xmbp", "xvref.xmbp", "midref_buf XVREF", "PMOS diode pb", "ramp"),
    ("vr_xmit", "xvref.xmit", "midref_buf XVREF", "PMOS source into a", "ramp"),
    ("vr_xmib", "xvref.xmib", "midref_buf XVREF", "NMOS sink from b", "ramp"),
    ("vr_xm1", "xvref.xm1", "midref_buf XVREF", "PMOS input follower (vin = vmid)", "ramp"),
    ("vr_xm3", "xvref.xm3", "midref_buf XVREF", "PMOS FVF loop device (gate b)", "ramp"),
    ("vr_xm2", "xvref.xm2", "midref_buf XVREF", "PMOS output diode (out)", "ramp"),
    ("vr_xm4", "xvref.xm4", "midref_buf XVREF", "NMOS input follower (vin = vmid)", "ramp"),
    ("vr_xm6", "xvref.xm6", "midref_buf XVREF", "NMOS FVF loop device (gate a)", "ramp"),
    ("vr_xm5", "xvref.xm5", "midref_buf XVREF", "NMOS output diode (out)", "ramp"),
    # cell 0 comparator (comparator_d: comparator + its XREFP diode, flat)
    ("c0_xrefp", "xc0.xcmp.xrefp", "cell 0 comparator_d", "comparator pbias PMOS diode (icmp0 in)", "trk"),
    ("c0_xtail", "xc0.xcmp.xtail", "cell 0 comparator_d", "tail PMOS source, 11 fingers", "trk"),
    ("c0_xinp", "xc0.xcmp.xinp", "cell 0 comparator_d", "input PMOS, gate inp = vbl", "trk"),
    ("c0_xinn", "xc0.xcmp.xinn", "cell 0 comparator_d", "input PMOS, gate inn = bot plate", "trk"),
    ("c0_xloadd", "xc0.xcmp.xloadd", "cell 0 comparator_d", "NMOS load diode (left)", "trk"),
    ("c0_xloadm", "xc0.xcmp.xloadm", "cell 0 comparator_d", "NMOS load mirror (outa)", "trk"),
    ("c0_xbst", "xc0.xcmp.xbst", "cell 0 comparator_d", "boost PMOS source (starved inverter)", "trk"),
    ("c0_xbuf2", "xc0.xcmp.xbuf2", "cell 0 comparator_d", "starved inverter PMOS", "trk"),
    ("c0_xbuf1", "xc0.xcmp.xbuf1", "cell 0 comparator_d", "starved inverter NMOS", "trk"),
    ("c0_xbuf4", "xc0.xcmp.xbuf4", "cell 0 comparator_d", "output inverter PMOS (dout)", "trk"),
    ("c0_xbuf3", "xc0.xcmp.xbuf3", "cell 0 comparator_d", "output inverter NMOS (dout)", "trk"),
    # cells 1..3: the bias devices only
    ("c1_xrefp", "xc1.xcmp.xrefp", "cell 1 comparator_d", "comparator pbias diode (icmp1 in)", "trk"),
    ("c1_xtail", "xc1.xcmp.xtail", "cell 1 comparator_d", "tail PMOS source", "trk"),
    ("c2_xrefp", "xc2.xcmp.xrefp", "cell 2 comparator_d", "comparator pbias diode (icmp2 in)", "trk"),
    ("c2_xtail", "xc2.xcmp.xtail", "cell 2 comparator_d", "tail PMOS source", "trk"),
    ("c3_xrefp", "xc3.xcmp.xrefp", "cell 3 comparator_d", "comparator pbias diode (icmp3 in)", "trk"),
    ("c3_xtail", "xc3.xcmp.xtail", "cell 3 comparator_d", "tail PMOS source", "trk"),
    # cell 0 switches (Ron = 1 / sum gds while closed)
    ("c0_s0n", "xc0.xs0.xn", "cell 0 S0 (vfe -> top)", "TG NMOS", "trk"),
    ("c0_s0p", "xc0.xs0.xp", "cell 0 S0 (vfe -> top)", "TG PMOS", "trk"),
    ("c0_s1n", "xc0.xs1.xn", "cell 0 S1 (vramp -> top)", "TG NMOS", "ramp"),
    ("c0_s1p", "xc0.xs1.xp", "cell 0 S1 (vramp -> top)", "TG PMOS", "ramp"),
    ("c0_s2n", "xc0.xs2.xn", "cell 0 S2 (vref -> bot)", "single NMOS", "trk"),
]
PARAMS = ("id", "gm", "gds", "gmbs", "vgs", "vds", "vth", "vdsat")
# extra currents for the KCL gate at bias_gen_s's pb node: XMN2's drain-side
# substrate and GIDL currents (BSIM4 id is the channel current only)
KCL_EXTRA = [("xmn2_isub", "xbg.xmn2.m0[isub]"), ("xmn2_igidl", "xbg.xmn2.m0[igidl]")]

# switches: name -> (device keys, state in which the switch is closed)
SWITCHES = [
    ("S0 cell 0 (vfe -> top)", ("c0_s0n", "c0_s0p"), "trk"),
    ("S1 cell 0 (vramp -> top)", ("c0_s1n", "c0_s1p"), "ramp"),
    ("S2 cell 0 (vref -> bot)", ("c0_s2n",), "trk"),
    ("ramp reset XRST (vramp -> vrlo)", ("rp_xrst",), "trk"),
]

# resistors: (key, path below xdut, node a, node b, role); R = (v(a) - v(b)) / i(rt1)
RES = [
    ("bg_xr1", "xbg.xr1", "xdut.xbg.ns", "xdut.xbg.r1", "bias_gen_s R string 1/5 (ppolyf_u 1 x 10.73 um)"),
    ("bg_xr2", "xbg.xr2", "xdut.xbg.r1", "xdut.xbg.r2", "bias_gen_s R string 2/5"),
    ("bg_xr3", "xbg.xr3", "xdut.xbg.r2", "xdut.xbg.r3", "bias_gen_s R string 3/5"),
    ("bg_xr4", "xbg.xr4", "xdut.xbg.r3", "xdut.xbg.r4", "bias_gen_s R string 4/5"),
    ("bg_xr5", "xbg.xr5", "xdut.xbg.r4", "0", "bias_gen_s R string 5/5"),
    ("div_xrt", "xdiv.xrt", "xdut.avdd_ref", "xdut.vmid", "midref_div upper (ppolyf_u_3k 1 x 64.98 um)"),
    ("div_xrb", "xdiv.xrb", "xdut.vmid", "0", "midref_div lower (ppolyf_u_3k 1 x 64.98 um)"),
    ("vl_xr1", "xvrlo.xr1", "xdut.avdd_vrlo", "xdut.xvrlo.r1", "vrlo_ref divider top unit 1/33 (ppolyf_u_3k 1 x 20 um)"),
    ("vl_xr33", "xvrlo.xr33", "xdut.xvrlo.r32", "0", "vrlo_ref divider bottom unit 33/33"),
]

# MIM capacitors: (key, path below xdut, c_width, c_length [m], role)
# formula, PDK sm141064_mim.ngspice subckt cap_mim_2f0_m4m5_noshield, typical
# (mim_corner_2p0ff = 1, mc_c_cox_2p0ff = 0): C = 1.99e-3 * W L + 2.383e-10 * 2 (W + L)
RS_CW = 44.6e-6        # ramp_simple_d XCR (= ../ramp_gen/data/ramp_simple_params.spice RS_CW, read again by op_reduce.py)
MIM = [
    ("c0_xcs", "xc0.xcs", 5e-6, 5e-6, "hold capacitor C_S, every cell (bot = terminal 1, top = terminal 2)"),
    ("rp_xcr", "xramp.xcr", RS_CW, RS_CW, "ramp integrating capacitor (ramp_simple_d)"),
    ("bg_xcp", "xbg.xcp", 22.3607e-6, 22.3607e-6, "bias_gen_s pb decap to vdd"),
    ("bg_xcn", "xbg.xcn", 22.3607e-6, 22.3607e-6, "bias_gen_s nb decap to vss"),
    ("div_xct", "xdiv.xct", 4.423e-6, 4.423e-6, "midref_div tap decap"),
    ("vr_xcd", "xvref.xcd", 11.7e-6, 11.7e-6, "XVREF output decap"),
    ("vl_xct", "xvrlo.xct", 22.4e-6, 22.4e-6, "vrlo_ref divider tap filter"),
    ("vl_xcd", "xvrlo.xcd", 41.5e-6, 41.5e-6, "vrlo_ref vrlo decap"),
]


def mim_formula(w, l):
    return 1.99e-3 * w * l + 2.383e-10 * 2 * (w + l)
