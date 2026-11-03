#!/usr/bin/env python3
"""Emit the xschem testbench drawings of the ramp-alone and loop-gain benches,
and the loop-break symbol:

    ./container.sh 'python3 tb_sch.py'
        -> tb_ramp.sch         draws tb_ramp.spice        at its nominal case (NCELL 4, VKICK 2.0, VDDX 1, TPRE 0)
        -> tb_ramp_simple.sch  draws tb_ramp_simple.spice at the same case
        -> tb_loop.sch         draws tb_loop.spice        at MODE 1 (reset), VOP 0.5, NCELL 4
        -> ramp_gen_lb.sym     primitive symbol of the loop-broken copy work/ramp_gen_lb.spice
                               (phases.sh writes that copy; ports vramp rst vrlo pbias vdd vss vx vxg)

The ramp benches take the DUT through ramp_gen.sym / ramp_simple.sym, so xschem
netlists the drawn ramp (ramp_gen.sch / ramp_simple.sch) into the bench; the
loop bench takes ramp_gen_lb.sym (type=primitive: the netlist line names the
subcircuit of work/ramp_gen_lb.spice, included by path). The old bias generator
is the primitive ../ramp_gen/ref/unit_cell_bps/bias_blk.sym (bias_gen.spice by
path), as in tb_ramp_adc4.sch. Every source carries the hand bench's expression;
the code blocks carry the model lines, the includes, the parameters at the
nominal case and the bench's .save / .measure / .control. xtb.py (phases.sh,
schematic phase) simulates the xschem netlists and compares them with the hand
benches.

Sheet text (CLAUDE.md, "Schematic drawings"): one title, short section
headings, the bench's values. Nothing else.
"""
import os

from sch_lib import Sheet

BLOCK = os.path.dirname(os.path.abspath(__file__))
RG = "/foss/designs/mixed_signal/ramp_gen"
PDK = "/foss/pdks/gf180mcuD/libs.tech/ngspice"
MODELS = (".include %s/design.ngspice\n"
          ".lib %s/sm141064.ngspice typical\n"
          ".lib %s/sm141064.ngspice res_typical\n"
          ".lib %s/sm141064.ngspice mimcap_typical\n"
          ".lib %s/sm141064.ngspice moscap_typical\n"
          ".include %s/ref/bias_gen/data/bias_gen_params.spice\n"
          ".include %s/ref/bias_gen/bias_gen.spice" % (PDK, PDK, PDK, PDK, PDK, RG, RG))
BIAS_SYM = "../ramp_gen/ref/unit_cell_bps/bias_blk.sym"

# the nominal case of the ramp benches (phases.sh ph_ramp: "nom 4 2.0 1 0")
RAMP_CASE = ".param NCELL=4\n.param VKICK=2.0\n.param VDDX=1\n.param TPRE=0"
# the timeline shared by tb_ramp.spice and tb_ramp_simple.spice
RAMP_PARAMS = """.param VDD=3.3
.param TCOUNT=50n
.param VR_LO=0.5
.param VR_HI=2.0
.param LSB='(VR_HI-VR_LO)/256'
.param TRAMP='256*TCOUNT'
.param SLOPE='(VR_HI-VR_LO)/TRAMP'
.param CLOAD_CELL=10f
%s
.param TPWR=100n
.param T0=1u
.param TS='T0+300n'
.param TCONN='TS+10n'
.param TR='T0+400n'
.param TE='TR+TRAMP'
.param TOVR='20*TCOUNT'
.param TRST2='TE+TOVR+50n'
.param TSTOP='TRST2+600n'
.param QKICK='NCELL*CLOAD_CELL*(VKICK-VR_LO)'""" % RAMP_CASE
RAMP_CTL = """.control
set num_threads=1
set wr_singlescale
set wr_vecnames
run
wrdata ramp.csv v(vramp) %s v(rst) v(pbias)
quit
.endc"""
# tb_ramp.spice: analysis, saves and measures of ramp_gen
GEN_MEAS = """.options reltol=1e-5 abstol=1e-13 vntol=1e-7 gmin=1e-15 savecurrents
.tran 0.2n {TSTOP} 0 2n
.save v(vramp) v(xrg.vx) v(rst) v(pbias) v(xrg.d2) v(xrg.nd) i(vdd_source)
.save @m.xrg.xns.m0[vds] @m.xrg.xns.m0[vdsat] @m.xrg.xps.m0[vds] @m.xrg.xps.m0[vdsat]
.save @m.xrg.xm5.m0[vds] @m.xrg.xm5.m0[vdsat] @m.xrg.xm6.m0[vds] @m.xrg.xm6.m0[vdsat]
.save @m.xrg.xm7.m0[vds] @m.xrg.xm7.m0[vdsat] @m.xrg.xm1.m0[vds] @m.xrg.xm1.m0[vdsat]
.save @m.xrg.xns.m0[id] @m.xrg.xps.m0[id] @m.xrg.xm5.m0[id] @m.xrg.xm6.m0[id] @m.xrg.xm7.m0[id]
.measure tran vr_tconn FIND v(vramp) AT={TCONN}
.measure tran vr_kick_max MAX v(vramp) FROM={TCONN} TO={TR}
.measure tran vr_tr FIND v(vramp) AT={TR}
.measure tran vx_tr FIND v(xrg.vx) AT={TR}
.measure tran vx_mid FIND v(xrg.vx) AT={TR+TRAMP/2}
.measure tran vx_te FIND v(xrg.vx) AT={TE}
.measure tran vr_te FIND v(vramp) AT={TE}
.measure tran vr_ovr FIND v(vramp) AT={TE+TOVR}
.measure tran i_ns AVG @m.xrg.xns.m0[id] FROM={TR} TO={TE}
.measure tran i_ps AVG @m.xrg.xps.m0[id] FROM={TR} TO={TE}
.measure tran i_m5 AVG @m.xrg.xm5.m0[id] FROM={TR} TO={TE}
.measure tran i_m7 AVG @m.xrg.xm7.m0[id] FROM={TR} TO={TE}
.measure tran i_total AVG i(vdd_source) FROM={TR} TO={TE}
.measure tran ns_vds_min MIN @m.xrg.xns.m0[vds] FROM={TR} TO={TE+TOVR}
.measure tran ns_vdsat FIND @m.xrg.xns.m0[vdsat] AT={TR}
.measure tran ns_margin PARAM='ns_vds_min-ns_vdsat'
.measure tran m5_vds_min MIN @m.xrg.xm5.m0[vds] FROM={TR} TO={TE+TOVR}
.measure tran m5_vdsat FIND @m.xrg.xm5.m0[vdsat] AT={TR}
.measure tran m5_margin PARAM='m5_vds_min-m5_vdsat'
.measure tran m6_vds_maxabs MIN @m.xrg.xm6.m0[vds] FROM={TR} TO={TE+TOVR}
.measure tran m6_vdsat FIND @m.xrg.xm6.m0[vdsat] AT={TE+TOVR}
.measure tran m7_vds FIND @m.xrg.xm7.m0[vds] AT={TR}
.measure tran m7_vdsat FIND @m.xrg.xm7.m0[vdsat] AT={TR}
.measure tran m1_vds FIND @m.xrg.xm1.m0[vds] AT={TR}
.measure tran m1_vdsat FIND @m.xrg.xm1.m0[vdsat] AT={TR}
.measure tran ps_vds FIND @m.xrg.xps.m0[vds] AT={TR}
.measure tran ps_vdsat FIND @m.xrg.xps.m0[vdsat] AT={TR}
.measure tran pbias_tr FIND v(pbias) AT={TR}
.measure tran pbias_min MIN v(pbias) FROM={TR} TO={TSTOP}
.measure tran pbias_max MAX v(pbias) FROM={TR} TO={TSTOP}
""" + RAMP_CTL % "v(xrg.vx)"
# tb_ramp_simple.spice: the same for ramp_simple
SIMPLE_MEAS = """.options reltol=1e-5 abstol=1e-13 vntol=1e-7 gmin=1e-15 savecurrents
.tran 0.2n {TSTOP} 0 2n
.save v(vramp) v(vrlo) v(rst) v(pbias) i(vdd_source)
.save @m.xrg.xps.m0[vds] @m.xrg.xps.m0[vdsat] @m.xrg.xps.m0[id]
.measure tran vr_tconn FIND v(vramp) AT={TCONN}
.measure tran vr_kick_max MAX v(vramp) FROM={TCONN} TO={TR}
.measure tran vr_tr FIND v(vramp) AT={TR}
.measure tran vr_te FIND v(vramp) AT={TE}
.measure tran vr_ovr FIND v(vramp) AT={TE+TOVR}
.measure tran i_ps AVG @m.xrg.xps.m0[id] FROM={TR} TO={TE}
.measure tran i_total AVG i(vdd_source) FROM={TR} TO={TE}
.measure tran ps_vds_top FIND @m.xrg.xps.m0[vds] AT={TE+TOVR}
.measure tran ps_vdsat FIND @m.xrg.xps.m0[vdsat] AT={TE+TOVR}
.measure tran ps_margin PARAM='abs(ps_vds_top)-abs(ps_vdsat)'
.measure tran pbias_tr FIND v(pbias) AT={TR}
""" + RAMP_CTL % "v(vrlo)"
# tb_loop.spice at MODE 1: op levels by let/print (xschem drops a code block's text from a `$` on)
LOOP_CODE = MODELS + """
.include %s/data/ramp_gen_params.spice
.include %s/work/ramp_gen_lb.spice
.param VDD=3.3
.param CLOAD_CELL=10f
.param MODE=1
.param VOP=0.5
.param NCELL=4
.options gmin=1e-15
.control
set num_threads=1
set wr_singlescale
set wr_vecnames
op
let op_vramp = v(vramp)
let op_vx = v(vx)
print op_vramp op_vx
ac dec 40 1k 1G
let tv = -v(vx)/v(vxg)
setplot const
alter VP acmag=0
alter IP acmag=1
ac dec 40 1k 1G
let ipr = i(vp)
let ti = -ipr/(1-ipr)
let tv = ac1.tv
let t = (tv*ti-1)/(tv+ti+2)
let tmag = db(t)
let tph = 180/pi*cph(t)
wrdata loop.csv tmag tph
quit
.endc""" % (RG, RG)


def esc(v):
    return v.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


def source(s, sym, name, x, y, value, rot=0):
    """vsource / isource / capa / res / ind: pins p (0,-30) and m (0,30) before rotation;
    returns (p, m). In the netlist p is the first node (I: current leaves at m)."""
    s.inst.append('C {devices/%s.sym} %d %d %d 0 {name=%s value="%s"%s}'
                  % (sym, x, y, rot, name, esc(value), " savecurrent=false" if sym in ("vsource", "isource") else " m=1"))
    a, b = Sheet.rot(0, -30, rot), Sheet.rot(0, 30, rot)
    p = ((x + a[0], y + a[1]), (x + b[0], y + b[1]))
    s.pins += list(p)
    return p


def code(s, name, x, y, text):
    s.inst.append('C {devices/code_shown.sym} %d %d 0 0 {name=%s only_toplevel=false value="%s"}' % (x, y, name, esc(text)))


def bias(s, x, y):
    """XBIAS, the old bias_gen as a primitive: pins vdd (0,-60) vss (0,60) pbias (80,-20) nbias (80,20)"""
    s.inst.append("C {%s} %d %d 0 0 {name=XBIAS model=bias_gen}" % (BIAS_SYM, x, y))
    s.pins += [(x, y - 60), (x, y + 60), (x + 80, y - 20), (x + 80, y + 20)]
    s.W((x, y - 60), (x, y - 100)); s.lab(x, y - 100, "vdd")
    s.W((x, y + 60), (x, y + 100)); s.lab(x, y + 100, "0")
    s.W((x + 80, y - 20), (x + 140, y - 20)); s.lab(x + 140, y - 20, "pbias")
    s.W((x + 80, y + 20), (x + 140, y + 20)); s.lab(x + 140, y + 20, "nbias")


def supply_bias_reset(s, vdd_val, rst_val, vrlo_val):
    """the left half every bench shares: supply, the bias generator, rst and vrlo"""
    s.T("supply and bias", 60, -780, 0.45, 13)
    p, m = source(s, "vsource", "VDD_SOURCE", 140, -640, vdd_val)
    s.W(p, (140, -700)); s.lab(140, -700, "vdd")
    s.W(m, (140, -580)); s.lab(140, -580, "0")
    bias(s, 560, -640)
    s.T("reset and start level", 60, -480, 0.45, 13)
    p, m = source(s, "vsource", "VRST", 140, -360, rst_val)
    s.W(p, (140, -420)); s.lab(140, -420, "rst")
    s.W(m, (140, -300)); s.lab(140, -300, "0")
    p, m = source(s, "vsource", "VRLO", 820, -360, vrlo_val)
    s.W(p, (820, -420)); s.lab(820, -420, "vrlo")
    s.W(m, (820, -300)); s.lab(820, -300, "0")


def dut(s, sym, x, y, extra_pins=()):
    """the ramp through its symbol: vramp (120,0) rst (-120,0) vrlo (-120,-60) pbias (-120,60) vdd (0,-120) vss (0,120);
    returns the vramp pin"""
    s.inst.append("C {%s} %d %d 0 0 {name=XRG%s}" % (sym, x, y, " model=ramp_gen_lb" if "lb" in sym else ""))
    s.pins += [(x + 120, y), (x - 120, y), (x - 120, y - 60), (x - 120, y + 60), (x, y - 120), (x, y + 120)]
    s.pins += list(extra_pins)
    s.W((x - 120, y - 60), (x - 180, y - 60)); s.lab(x - 180, y - 60, "vrlo", right=False)
    s.W((x - 120, y), (x - 180, y)); s.lab(x - 180, y, "rst", right=False)
    s.W((x - 120, y + 60), (x - 180, y + 60)); s.lab(x - 180, y + 60, "pbias", right=False)
    s.W((x, y - 120), (x, y - 160)); s.lab(x, y - 160, "vdd")
    s.W((x, y + 120), (x, y + 160)); s.lab(x, y + 160, "0")
    return (x + 120, y)


def tb_ramp(sub, tbn, meas, title):
    s = Sheet()
    s.T(title, 60, -900, 0.7)
    supply_bias_reset(s, "PWL(0 0 {TPWR} {VDD*VDDX} {TSTOP} {VDD*VDDX})",
                      "PWL(0 0 {TPWR} {VDD} {TR-TPRE} {VDD} {TR-TPRE+100p} 0 {TRST2} 0 {TRST2+100p} {VDD})",
                      "{VR_LO-SLOPE*TPRE}")
    s.T("ramp generator (DUT)", 820, -780, 0.45, 13)
    vr = dut(s, sub + ".sym", 1000, -560)
    s.W(vr, (2000, -560)); s.lab(1180, -560, "vramp")
    # the cells as a load and as the S1-connection charge (IKICK rotated: its value text sits to its left)
    s.T("cell load and S1 kick", 1340, -780, 0.45, 13)
    p, m = source(s, "capa", "CL", 1400, -440, "{NCELL*CLOAD_CELL+1f}")
    s.W(p, (1400, -560)); s.J(1400, -560)
    s.W(m, (1400, -340)); s.lab(1400, -340, "0")
    s.T("NCELL = 4", 1440, -545, 0.35, 4)
    s.T("10 fF per cell", 1440, -515, 0.35, 4)
    p, m = source(s, "isource", "IKICK", 2000, -440, "PULSE(0 {QKICK/1n} {TCONN} 100p 100p 0.9n 1)", rot=2)
    s.W(m, (2000, -560))
    s.W(p, (2000, -340)); s.lab(2000, -340, "0")
    s.T("VKICK 2.0 V", 2040, -460, 0.35, 4)
    # the code blocks: models and blocks by path; the timeline; the analysis and its measures
    code(s, "MODELS", 60, -160, MODELS + "\n.include %s/data/%s_params.spice" % (RG, sub))
    code(s, "PARAMS", 60, 60, RAMP_PARAMS)
    code(s, "MEASURES", 1000, -160, meas)
    nseg, njun = s.write(os.path.join(BLOCK, tbn + ".sch"))
    print("PASS: tb_sch.py wrote %s.sch (%d wire segments, %d junctions, %d texts)" % (tbn, nseg, njun, len(s.texts)))


def lb_symbol(path):
    """ramp_gen_lb: the loop-broken ramp_gen (vx the network side, vxg XM1's gate), primitive"""
    sym = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
           'K {type=primitive\nformat="@name @pinlist @model"\ntemplate="name=XRG model=ramp_gen_lb"\n'
           'description="ramp_gen with the loop broken at the OTA inverting input: vx is the network side '
           '(XCI, XNS, XRST), vxg XM1 gate. Subcircuit ramp_gen_lb of work/ramp_gen_lb.spice, written by phases.sh '
           'from ramp_gen.spice; type=primitive, included by path.\nPins in the subcircuit order: '
           'vramp rst vrlo pbias vdd vss vx vxg."\n}', "V {}", "S {}", "E {}"]
    for x1, y1, x2, y2 in ((-100, -100, 100, -100), (100, -100, 100, 100), (100, 100, -100, 100),
                           (-100, 100, -100, -100)):
        sym.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))
    for line in ("L 7 -50 40 30 -40 {}", "L 7 30 -40 30 40 {}", "L 7 30 40 50 40 {}", "L 7 -70 40 -50 40 {}"):
        sym.append(line)
    sym.append("L 4 100 0 120 0 {}")
    sym.append("B 5 117.5 -2.5 122.5 2.5 {name=vramp dir=out}")
    for p, y in (("rst", 0), ("vrlo", -60), ("pbias", 60)):
        sym.append("L 4 -120 %d -100 %d {}" % (y, y))
        sym.append("B 5 -122.5 %.1f -117.5 %.1f {name=%s dir=in}" % (y - 2.5, y + 2.5, p))
    sym.append("L 4 0 -120 0 -100 {}")
    sym.append("B 5 -2.5 -122.5 2.5 -117.5 {name=vdd dir=inout}")
    sym.append("L 4 0 100 0 120 {}")
    sym.append("B 5 -2.5 117.5 2.5 122.5 {name=vss dir=inout}")
    for p, x in (("vx", -60), ("vxg", 60)):
        sym.append("L 4 %d 100 %d 120 {}" % (x, x))
        sym.append("B 5 %.1f 117.5 %.1f 122.5 {name=%s dir=inout}" % (x - 2.5, x + 2.5, p))
    for p, x, y in (("vramp", 60, -6), ("rst", -94, -6), ("vrlo", -94, -66), ("pbias", -94, 54),
                    ("vdd", 6, -114), ("vss", 6, 104), ("vx", -70, 94), ("vxg", 46, 94)):
        sym.append("T {%s} %d %d 0 0 0.2 0.2 {}" % (p, x, y))
    sym.append("T {@name} -100 -136 0 0 0.3 0.3 {}")
    sym.append("T {loop broken} -90 76 0 0 0.22 0.22 {layer=13}")
    open(path, "w").write("\n".join(sym) + "\n")


def tb_loop():
    s = Sheet()
    s.T("TB_LOOP  -  loop gain of ramp_gen, Middlebrook double injection at the OTA input", 60, -900, 0.7)
    supply_bias_reset(s, "{VDD}", "{MODE*VDD}", "0.5")
    s.T("ramp generator, loop broken at XM1's gate", 820, -780, 0.45, 13)
    s.T("MODE = 1 (reset)", 820, -740, 0.35, 4)
    x, y = 1000, -560
    # the lb symbol adds vx (-60,120) and vxg (60,120) at the bottom of the box
    vr = dut(s, "ramp_gen_lb.sym", x, y, extra_pins=[(x - 60, y + 120), (x + 60, y + 120)])
    s.W(vr, (1900, -560)); s.lab(1180, -560, "vramp")
    # injection below the DUT: VP in series between vxg (gate, p) and vx (network, m), IP into vxg
    s.T("Middlebrook injection", 560, -240, 0.45, 13)
    s.W((940, -440), (940, -280), (970, -280)); s.lab(940, -360, "vx", right=False)
    s.W((1060, -440), (1060, -280), (1030, -280)); s.lab(1060, -300, "vxg")
    source(s, "vsource", "VP", 1000, -280, "DC 0 AC 1", rot=1)            # p right (vxg), m left (vx)
    p, m = source(s, "isource", "IP", 1160, -350, "DC 0 AC 0", rot=2)      # m top (vxg), p bottom (0)
    s.W(m, (1160, -400), (1060, -400)); s.J(1060, -400)
    s.W(p, (1160, -280)); s.lab(1160, -280, "0")
    # the load and the DC path of the ramp mode (LDC + VOP_SRC + RDCX from vramp to vx)
    s.T("load; DC path of MODE 0", 1620, -780, 0.45, 13)
    p, m = source(s, "capa", "CL", 1640, -460, "{NCELL*CLOAD_CELL+1f}")
    s.W(p, (1640, -560)); s.J(1640, -560)
    s.W(m, (1640, -380)); s.lab(1640, -380, "0")
    s.T("NCELL = 4", 1660, -700, 0.35, 4)
    p, m = source(s, "ind", "LDC", 1900, -480, "{1e9*(1-MODE)+1e-9}")
    s.W(p, (1900, -560))
    s.W(m, (1900, -420)); s.lab(1900, -420, "nl")
    p, m = source(s, "vsource", "VOP_SRC", 1900, -360, "{(VOP-0.5)*(1-MODE)}")
    s.W(p, (1900, -420))
    s.W(m, (1900, -300)); s.lab(1900, -300, "vxo")
    p, m = source(s, "res", "RDCX", 1900, -240, "{1+1e15*MODE}")
    s.W(p, (1900, -300))
    s.W(m, (1900, -180)); s.lab(1900, -180, "vx")
    code(s, "CTL", 60, -160, LOOP_CODE)
    nseg, njun = s.write(os.path.join(BLOCK, "tb_loop.sch"))
    print("PASS: tb_sch.py wrote tb_loop.sch (%d wire segments, %d junctions, %d texts)" % (nseg, njun, len(s.texts)))


if __name__ == "__main__":
    tb_ramp("ramp_gen", "tb_ramp", GEN_MEAS,
            "TB_RAMP  -  ramp_gen alone on its bias_gen, cell load and S1 kick")
    tb_ramp("ramp_simple", "tb_ramp_simple", SIMPLE_MEAS,
            "TB_RAMP_SIMPLE  -  ramp_simple alone on its bias_gen, cell load and S1 kick")
    lb_symbol(os.path.join(BLOCK, "ramp_gen_lb.sym"))
    print("PASS: tb_sch.py wrote ramp_gen_lb.sym (primitive, 8 pins)")
    tb_loop()
