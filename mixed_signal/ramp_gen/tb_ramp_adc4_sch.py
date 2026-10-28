#!/usr/bin/env python3
"""Emit the xschem testbench tb_ramp_adc4.sch: the ramp generator driving four
8-bit true bottom-plate unit cells.

    ./container.sh 'python3 tb_ramp_adc4_sch.py [gen|simple]'   (default gen; simple -> tb_ramp_simple_adc4.sch)

What is drawn (the circuit and every stimulus source):

  XRG     ramp_gen.sym  (descends into ramp_gen.sch: the drawn ramp is simulated)
  XBIASR  ../ramp_gen/ref/unit_cell_bps/bias_blk.sym   the ramp's own bias generator (pbias_r): never the
          comparators' pbias line, whose decision glitches the slope current would integrate
  XBIAS   ../ramp_gen/ref/unit_cell_bps/bias_blk.sym   shared constant-gm bias, pbias line
  XVREF   ../ramp_gen/ref/midrail_ref/midref_b.sym     FVF VDD/2 buffer -> vref (top plates at track)
  XVBL    ../ramp_gen/ref/midrail_ref/midref_b.sym     FVF VDD/2 buffer -> vbl  (comparator inp)
  XC0..3  ../ramp_gen/ref/unit_cell_bps/cell_bps.sym   four unit cells (switches, 54.52 fF MIM, cmp_bps)
  RREAL / RIDEAL   the ramp selector: vr_cell is the real vramp (RREAL 1 mohm,
                   RIDEAL 1 Tohm) or the ideal PWL ramp videal (the other way
                   round); RAMP_REAL in case.spice picks. The difference of the
                   two runs is what the ramp generator contributes, nothing else.
  VMRAMP / VMCELL  0 V meters splitting the supply current (ramp / cells)
  sources: VDD_SOURCE (cold start), VRLO, VRST, VIDEAL, VS0/VS1/VS2 (switch
           controls, shared), VCLK (20 MHz count clock), VIN0..3 (the levels)

Timeline, measures and analysis: tb_ramp_adc4_ctl.inc (included by the
code block). The run directory provides case.spice (levels, selector, TPRE).
run.sh netlists this drawing with xschem and simulates the netlist it wrote.
"""
import os
import sys

DUT = sys.argv[1] if len(sys.argv) > 1 else "gen"
SUB, PRM, TBN = {"gen": ("ramp_gen", "ramp_gen_params", "tb_ramp_adc4"),
                  "simple": ("ramp_simple", "ramp_simple_params", "tb_ramp_simple_adc4")}[DUT]

BLOCK = os.path.dirname(os.path.abspath(__file__))
out = []
n = [0]


def T(s, x, y, size=0.35, layer=None):
    out.append("T {%s} %d %d 0 0 %.2f %.2f %s" % (s, x, y, size, size,
                                                  "{layer=%d}" % layer if layer is not None else "{}"))


def lab(x, y, net, right=True):
    n[0] += 1
    out.append("C {devices/lab_pin.sym} %d %d 0 %d {name=l%d sig_type=std_logic lab=%s}"
               % (x, y, 1 if right else 0, n[0], net))


def esc(v):
    return v.replace("{", "\\{").replace("}", "\\}")


def vsrc(name, x, y, p, m, value):
    out.append('C {devices/vsource.sym} %d %d 0 0 {name=%s value="%s" savecurrent=false}' % (x, y, name, esc(value)))
    lab(x, y - 30, p)
    lab(x, y + 30, m)


def res(name, x, y, a, b, value):
    out.append('C {devices/res.sym} %d %d 0 0 {name=%s value="%s" footprint=1206 device=resistor m=1}'
               % (x, y, name, esc(value)))
    lab(x, y - 30, a)
    lab(x, y + 30, b)


def cap(name, x, y, a, b, value):
    out.append('C {devices/capa.sym} %d %d 0 0 {name=%s value=%s footprint=1206 device="ceramic capacitor" m=1}'
               % (x, y, name, value))
    lab(x, y - 30, a)
    lab(x, y + 30, b)


T(TBN + " -- the shared ramp generator (" + SUB + ") driving four 8-bit true bottom-plate unit cells "
  "(cell_bps: S0/S1/S2, 54.52 fF MIM, cmp_bps)\non the shared bias generator and the two FVF VDD/2 buffers. "
  "Every cell samples its own DC level vin_i at TS, connects its bottom plate to vr_cell at TCONN and "
  "converts:\ndout_i falls when the ramp passes vin_i; code_i = floor((t_dout_i - TR) / TCOUNT) against "
  "floor((vin_i - 0.5 V) / LSB), LSB = 1.5 V / 256.\nRREAL / RIDEAL select the real ramp or an ideal one "
  "(RAMP_REAL in case.spice): the difference is the ramp generator's own contribution.\n"
  "Timeline, measures, analysis: tb_ramp_adc4_ctl.inc. run.sh netlists this drawing and simulates it.",
  60, -1500, 0.32)

# code block: models and the blocks the primitive symbols name
code = ("* models (typical) and the blocks behind the primitive symbols, by path\n"
        ".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
        ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical\n"
        ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical\n"
        ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical\n"
        ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice moscap_typical\n"
        ".include /foss/designs/mixed_signal/ramp_gen/ref/comparator_updt/cmp_updt.spice\n"
        ".include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice\n"
        ".include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice\n"
        ".include /foss/designs/mixed_signal/ramp_gen/ref/midrail_ref/data/midrail_params.spice\n"
        ".include /foss/designs/mixed_signal/ramp_gen/ref/midrail_ref/ref_fvf_biased.spice\n"
        ".include /foss/designs/mixed_signal/ramp_gen/ref/unit_cell_bps/switches.spice\n"
        ".include /foss/designs/mixed_signal/ramp_gen/data/" + PRM + ".spice\n"
        "* timeline, sources' parameters, measures, analysis\n"
        ".include /foss/designs/mixed_signal/ramp_gen/tb_ramp_adc4_ctl.inc")
out.append('C {devices/code_shown.sym} 60 -1320 0 0 {name=MODELS only_toplevel=false value="%s"}' % code)

# ---- supply and meters
T("supply (cold start) and current meters", 60, -900, 0.4, 13)
vsrc("VDD_SOURCE", 100, -760, "vdd", "0", "PWL(0 0 {TPWR} {VDD} {TSTOP} {VDD})")
vsrc("VMRAMP", 260, -760, "vdd", "vdd_ramp", "0")
vsrc("VMCELL", 420, -760, "vdd", "vdd_cell", "0")
vsrc("VMBIAS", 580, -760, "vdd", "vdd_bias", "0")

# ---- bias and references
T("bias and references", 60, -560, 0.4, 13)
out.append("C {../ramp_gen/ref/unit_cell_bps/bias_blk.sym} 200 -400 0 0 {name=XBIAS model=bias_gen}")
lab(200, -460, "vdd_bias"); lab(200, -340, "0"); lab(280, -420, "pbias"); lab(280, -380, "nbias")
out.append("C {../ramp_gen/ref/midrail_ref/midref_b.sym} 520 -440 0 0 {name=XVREF model=midref_b}")
lab(600, -440, "vref"); lab(440, -440, "pbias", right=False); lab(520, -500, "vdd_bias"); lab(520, -380, "0")
out.append("C {../ramp_gen/ref/midrail_ref/midref_b.sym} 520 -240 0 0 {name=XVBL model=midref_b}")
lab(600, -240, "vbl"); lab(440, -240, "pbias", right=False); lab(520, -300, "vdd_bias"); lab(520, -180, "0")

# ---- the ramp generator and the selector
T("the ramp generator (DUT) and the real / ideal selector", 800, -900, 0.4, 13)
out.append("C {%s.sym} 1000 -700 0 0 {name=XRG}" % SUB)
lab(1120, -700, "vramp"); lab(880, -700, "rst", right=False); lab(880, -760, "vrlo", right=False)
lab(880, -640, "pbias_r", right=False); lab(1000, -820, "vdd_ramp"); lab(1000, -580, "0")
# the ramp's OWN bias generator: a comparator decision glitches the shared pbias line by
# ~0.5 mV, and on a shared line that glitch reaches the slope current and the integrator
# keeps it (0.16-0.24 LSB of crosstalk for three aggressors 1 LSB away; explore/xt_pbias.sh)
out.append("C {../ramp_gen/ref/unit_cell_bps/bias_blk.sym} 1000 -1000 0 0 {name=XBIASR model=bias_gen}")
lab(1000, -1060, "vdd_ramp"); lab(1000, -940, "0"); lab(1080, -1020, "pbias_r"); lab(1080, -980, "nbias_r")
vsrc("VRLO", 820, -460, "vrlo", "0", "{VRLO_V}")
vsrc("VRST", 940, -460, "rst", "0", "PWL(0 0 {TPWR} {VDD} {TR-TPRE} {VDD} {TR-TPRE+TEDGE} 0 {TSTOP} 0)")
vsrc("VIDEAL", 1060, -460, "videal", "0", "PWL(0 {VR_LO} {TR} {VR_LO} {TE+TOVR} {VR_OVR} {TSTOP} {VR_OVR})")
res("RREAL", 1240, -700, "vramp", "vr_cell", "{RSEL_REAL}")
res("RIDEAL", 1240, -460, "videal", "vr_cell", "{RSEL_IDEAL}")

# ---- shared switch controls and clock
T("switch controls (HIGH = closed, shared by the four cells) and the count clock", 800, -300, 0.4, 13)
vsrc("VS2", 820, -160, "s2", "0", "PWL(0 0 {TPWR} {VDD} {TS} {VDD} {TS+TEDGE} 0)")
vsrc("VS0", 940, -160, "s0", "0", "PWL(0 0 {TPWR} {VDD} {TISO} {VDD} {TISO+TEDGE} 0)")
vsrc("VS1", 1060, -160, "s1", "0", "PWL(0 0 {TCONN} 0 {TCONN+TEDGE} {VDD})")
vsrc("VCLK", 1180, -160, "clk", "0", "PULSE(0 {VDD} {TR} {TEDGE} {TEDGE} {TCOUNT/2-TEDGE} {TCOUNT})")

# ---- four cells
T("four unit cells: each samples its own level vin_i and trips when the ramp passes it", 1500, -900, 0.4, 13)
for i in range(4):
    x, y = 1700 + 520 * i, -600
    out.append("C {../ramp_gen/ref/unit_cell_bps/cell_bps.sym} %d %d 0 0 {name=XC%d}" % (x, y, i))
    for net, dy in (("vin%d" % i, -120), ("vr_cell", -90), ("s0", -60), ("s1", -30), ("s2", 0),
                    ("vref", 30), ("vbl", 60)):
        lab(x - 140, y + dy, net, right=False)
    for net, dy in (("dout%d" % i, -120), ("clk", -90), ("pbias", -30), ("nbias", 0)):
        lab(x + 140, y + dy, net)
    lab(x, y - 160, "vdd_cell"); lab(x, y + 160, "0")
    vsrc("VIN%d" % i, x - 100, y + 300, "vin%d" % i, "0", "{VIN%d}" % i)
    cap("CL%d" % i, x + 100, y + 300, "dout%d" % i, "0", "50f")

sch = "v {xschem version=3.4.8RC file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n" + "\n".join(out) + "\n"
open(os.path.join(BLOCK, TBN + ".sch"), "w").write(sch)
print("PASS: tb_ramp_adc4_sch.py wrote %s.sch (%d labels)" % (TBN, n[0]))
