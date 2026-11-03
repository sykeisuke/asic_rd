#!/usr/bin/env python3
"""Emit the xschem testbench drawings of midref's benches.

    python3 tb_sch.py   -> tb_op.sch, tb_kick.sch, tb_cmp.sch, tb_mc.sch, tb_noise.sch

Each drawing is one bench of verify_v3.py at its nominal case (typical, 27 C,
3.3 V, the ideal bias I_F of data/sizing_v2.json into ib): every source with
its expression, the loads and switch models, the DUT as midref_div.sym +
midref_buf.sym wired as the wrapper `midref` of midref.spice (XD, XB: xschem
descends into midref_div.sch / midref_buf.sch, so the testbench exercises
the drawings, not the deck), and one code block with the PDK model lines,
the .params, .temp, .options and the bench's .control. The device paths of
the .control lines follow the drawn hierarchy (xb.xm1, not xb.xb.xm1).

| Drawing      | Bench                      | Fixed at                                           |
| tb_op.sch    | tb_op.spice                | typical / 27 C, VDD looped 3.0 / 3.3 / 3.6 V        |
| tb_kick.sch  | tb_kick.spice              | typical / 27 C / 3.3 V, both S2 charge directions  |
| tb_cmp.sch   | tb_cmp.spice run A         | buffer drives the node, VDROP 0.15 V, no neighbour  |
| tb_mc.sch    | tb_mc.spice + tb_mchr.spice | one mismatch draw, seed SEED_BASE + 1 (MC and HR)  |
| tb_noise.sch | tb_noise.spice             | typical / 27 C / 3.3 V, 10 Hz - 1 GHz               |

Sheet text (root CLAUDE.md, "Schematic drawings"): one title, short section
headings, the bench's parameter values. xtb.py netlists every drawing with
xschem, simulates it and compares it with the hand-written bench
(data/xtb.csv). Placement is hand-authored.
"""
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
sys.path.insert(0, str(BLOCK))
import bench as B  # noqa: E402  I_F, SEED (verify_v3.py's SEED_BASE)

IF = "%.6g" % B.I_F
IB_TXT = "I_B = %.2f uA" % (B.I_F * 1e6)
SEED_BASE = 20261007          # verify_v3.py; draw 1 of the record is seed + 1
MODELS = (".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
          ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical\n"
          ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical\n"
          ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical")
# echo lines go unquoted: a quoted "$&x" in a code block makes ngspice lose the .endc
# the PDK MOS symbols write S/D geometry by default; the benches' bias diodes are
# drawn as the deck has them (L W nf m only), as midref_sch.py does
MOS_FMT = 'format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"'


def esc(s):
    return s.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


class Sch:
    # pin offsets (symbol coordinates), the direction the stub leaves in, and an optional
    # stub length where the default (STUB) would put two labels on top of each other
    PINS = {
        "vsource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "isource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "capa": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "res": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "switch": {"P": (0, -30, "U"), "M": (0, 30, "D"), "CP": (-40, 0, "L"), "CM": (-40, 20, "L")},
        # cap_mim_2f0fF: @pinlist follows the symbol's pin order, G (y -30) then B (y +30)
        "mim": {"G": (0, -30, "U"), "B": (0, 30, "D")},
        "pfet": {"G": (-20, 0, "L"), "S": (20, -30, "U"), "D": (20, 30, "D"), "B": (20, 0, "R", 110)},
        "nfet": {"G": (-20, 0, "L"), "D": (20, -30, "U"), "S": (20, 30, "D"), "B": (20, 0, "R", 110)},
        "mdiv": {"vin": (80, 0, "R"), "vdd": (0, -60, "U"), "vss": (0, 60, "D")},
        "mbuf": {"out": (80, 0, "R"), "vin": (-80, 0, "L", 130), "ib": (-80, 20, "L"), "vdd": (0, -60, "U"),
                 "vss": (0, 60, "D")},
        "cmp": {"inp": (-100, -60, "L"), "inn": (-100, -30, "L"), "clk": (-100, 0, "L"), "nbias": (-100, 30, "L"),
                "pbias": (-100, 60, "L"), "dout": (100, -45, "R"), "vdd": (0, -120, "U"), "vss": (0, 120, "D")},
    }
    SYM = {"vsource": "devices/vsource.sym", "isource": "devices/isource.sym", "capa": "devices/capa.sym",
           "res": "devices/res.sym", "switch": "devices/switch_ngspice.sym", "mim": "symbols/cap_mim_2f0fF.sym",
           "pfet": "symbols/pfet_03v3.sym", "nfet": "symbols/nfet_03v3.sym",
           "mdiv": "midref_div.sym", "mbuf": "midref_buf.sym", "cmp": "comparator.sym"}
    STUB = 40

    def __init__(self):
        self.wires, self.inst, self.texts, self.n = [], [], [], 0

    def label(self, x, y, net, text_left):
        self.n += 1
        self.inst.append("C {devices/lab_pin.sym} %d %d 0 %d {name=l%d sig_type=std_logic lab=%s}"
                         % (x, y, 0 if text_left else 1, self.n, net))

    def part(self, kind, x, y, attrs, nets):
        self.inst.append("C {%s} %d %d 0 0 {%s}" % (self.SYM[kind], x, y, attrs))
        for pin, net in nets.items():
            dx, dy, d, *st = self.PINS[kind][pin]
            px, py = x + dx, y + dy
            L = st[0] if st else self.STUB
            ex, ey = {"U": (px, py - L), "D": (px, py + L), "L": (px - L, py), "R": (px + L, py)}[d]
            self.wires.append((px, py, ex, ey))
            self.label(ex, ey, net, d != "R")

    def mos(self, kind, name, x, y, l, w, nf, nets):
        attrs = "name=%s\nL=%s W=%s nf=%s m=1\nmodel=%s_03v3 spiceprefix=\"\"\n%s" % (name, l, w, nf, kind, MOS_FMT)
        self.part(kind, x, y, attrs, nets)

    def vsrc(self, name, x, y, value, p, m="0"):
        self.part("vsource", x, y, 'name=%s value="%s" savecurrent=false' % (name, esc(value)), {"p": p, "m": m})

    def isrc(self, name, x, y, value, p, m):
        self.part("isource", x, y, 'name=%s value="%s"' % (name, esc(value)), {"p": p, "m": m})

    def sw(self, name, x, y, model, p, m, cp, cm="0"):
        self.part("switch", x, y, "name=%s model=%s" % (name, model), {"P": p, "M": m, "CP": cp, "CM": cm})

    def mim(self, name, x, y, first, second):
        """the deck's `name first second cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u`"""
        self.part("mim", x, y, 'name=%s W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1' % name,
                  {"G": first, "B": second})

    def cap(self, name, x, y, value, p, m="0"):
        self.part("capa", x, y, 'name=%s value="%s" m=1' % (name, esc(value)), {"p": p, "m": m})

    def res(self, name, x, y, value, p, m="0"):
        self.part("res", x, y, 'name=%s value="%s" footprint=1206 device=resistor m=1' % (name, esc(value)),
                  {"p": p, "m": m})

    def dut(self, x, y, out, vss="0"):
        """midref (midref.spice wrapper) as drawn: XD vin vdd vss midref_div, XB out vin ib vdd vss midref_buf.
        XD before XB, as the wrapper expands: the PDK mismatch draws follow the instance order."""
        self.part("mdiv", x, y, "name=XD", {"vin": "vin", "vdd": "vdd", "vss": vss})
        self.part("mbuf", x + 480, y, "name=XB", {"out": out, "vin": "vin", "ib": "ib", "vdd": "vdd", "vss": vss})

    def code(self, x, y, name, text):
        self.inst.append('C {devices/code_shown.sym} %d %d 0 0 {name=%s only_toplevel=false value="%s"}'
                         % (x, y, name, esc(text)))

    def T(self, s, x, y, size=0.4, layer=None):
        self.texts.append("T {%s} %d %d 0 0 %s %s {%s}" % (s, x, y, size, size, "layer=%d" % layer if layer else ""))

    def write(self, path):
        body = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        body += ["N %d %d %d %d {}" % w for w in self.wires]
        body += self.texts + self.inst
        path.write_text("\n".join(body) + "\n")
        print("REPORT: wrote %s: %d symbols, %d wires, %d texts" % (path.name, len(self.inst) - self.n,
                                                                      len(self.wires), len(self.texts)))


def header(s, title):
    s.T(title, 60, -1330, 0.7)


def supply_and_bias(s, vdd_value, y=-1130, extra=()):
    """VDD_SOURCE and the ideal bias current IREF into ib (as every bench), then any
    other short source in the same row."""
    s.vsrc("VDD_SOURCE", 120, y, vdd_value, "vdd")
    s.isrc("IREF", 290, y, "{IF}", "vdd", "ib")
    for i, (name, val, net) in enumerate(extra):
        s.vsrc(name, 460 + 170 * i, y, val, net)
    s.T("SUPPLY + BIAS", 60, -1260)
    s.T(IB_TXT, 250, -1010, 0.3, 4)


def tb_op():
    s = Sch()
    header(s, "TB_OP  -  operating point and headroom of midref, VDD 3.0 / 3.3 / 3.6 V")
    supply_and_bias(s, "3.3")
    s.T("DUT", 800, -1260)
    s.dut(900, -1100, "out")
    code = MODELS + """
.temp 27
.param IF=%s
.control
set num_threads=1
foreach v 3.0 3.3 3.6
  alter VDD_SOURCE dc = $v
  op
  let hr1 = abs(@m.xb.xm1.m0[vds]) - abs(@m.xb.xm1.m0[vdsat])
  let hr4 = abs(@m.xb.xm4.m0[vds]) - abs(@m.xb.xm4.m0[vdsat])
  let hrib = abs(@m.xb.xmib.m0[vds]) - abs(@m.xb.xmib.m0[vdsat])
  let hrit = abs(@m.xb.xmit.m0[vds]) - abs(@m.xb.xmit.m0[vdsat])
  let hr2 = abs(@m.xb.xm2.m0[vds]) - abs(@m.xb.xm2.m0[vdsat])
  let hr5 = abs(@m.xb.xm5.m0[vds]) - abs(@m.xb.xm5.m0[vdsat])
  let hr3 = abs(@m.xb.xm3.m0[vds]) - abs(@m.xb.xm3.m0[vdsat])
  let hr6 = abs(@m.xb.xm6.m0[vds]) - abs(@m.xb.xm6.m0[vdsat])
  let err = v(out) - $v / 2
  let isup = -i(VDD_SOURCE)
  echo OP typical 27 1 $v $&hr1 $&hr4 $&hrib $&hrit $&hr2 $&hr5 $&hr3 $&hr6 $&err $&isup
  let ibb = abs(@m.xb.xmib.m0[id])
  let ibt = abs(@m.xb.xmit.m0[id])
  let i2 = abs(@m.xb.xm2.m0[id])
  let vp = v(xb.p)
  let vn = v(xb.n)
  let tap = v(vin) - $v / 2
  echo OPX typical 27 1 $v $&ibb $&ibt $&i2 $&vp $&vn $&tap
end
quit
.endc""" % IF
    s.code(800, -900, "CTL", code)
    s.write(BLOCK / "tb_op.sch")


def tb_kick():
    s = Sch()
    header(s, "TB_KICK  -  S2 event of one cell on the one output (vref = vbl), both charge directions")
    supply_and_bias(s, "{VDD}", extra=[("VTOP0", "{TOP0}", "vtop0")])
    s.vsrc("VSNS", 630, -1130, "0", "vref", "vrefs")
    s.T("SWITCH CONTROLS", 60, -990)
    for i, (name, val, net) in enumerate([
            ("VSPRE", "PWL(0 2 {TK-5n} 2 {TK-4n} 0)", "spre"),
            ("VS2", "PWL(0 0 {TK} 0 {TK+0.1n} 2)", "s2"),
            ("VBOT", "PWL(0 {VBOT0} {TK} {VBOT0} {TK+0.1n} {VFE1})", "bots")]):
        s.vsrc(name, 120, -860 + 170 * i, val, net)
    s.T("DUT", 900, -1260)
    s.dut(1000, -1100, "vref")
    s.T("CELL: S2 + S0 + C_S", 1820, -1260)
    s.sw("S2", 1900, -1100, "sws2", "vrefs", "top", "s2")
    s.sw("SPRE", 1900, -850, "swpre", "top", "vtop0", "spre")
    s.mim("XCS", 2150, -1000, "top", "bot")
    s.T("C_S 54.52 fF", 2190, -900, 0.3, 4)
    s.cap("CTOPP", 2450, -1000, "{CTOP}", "top")
    s.res("RLKT", 2700, -1000, "1e15", "top")
    s.res("RS0", 2150, -760, "{RS0}", "bots", "bot")
    code = MODELS + """
.temp 27
.param IF=%s
.param VDD=3.3
.param CS_W=5u
.param CS_L=5u
.param CTOP=17.12f
.param RS2=1k
.param RS0=100
.param EPS=2.9297m
.param TK=1u
.param VBOT0=2.117
.param TOP0=2.9900
.param VFE1=2.0
.csparam cs_eps={EPS}
.model swpre sw vt=1 vh=0.1 ron=100 roff=1e14
.model sws2 sw vt=1 vh=0.1 ron={RS2} roff=1e14
.control
set num_threads=1
tran 0.1n 2.0u 0 1n
meas tran v0r avg v(vref) from=0.8u to=0.99u
let devr = abs(v(vref) - v0r)
meas tran pkr max devr from=1u to=2u
meas tran rr250 find devr at=1.25u
meas tran rr300 find devr at=1.3u
meas tran qk integ i(vsns) from=0.99u to=1.3u
let k_c1_pkr_mv = pkr * 1e3
let k_c1_rr250_mv = rr250 * 1e3
let k_c1_rr300_mv = rr300 * 1e3
let k_c1_qk_fc = qk * 1e15
let k_c1_v0r_v = v0r
print k_c1_pkr_mv
print k_c1_rr250_mv
print k_c1_rr300_mv
print k_c1_qk_fc
print k_c1_v0r_v
meas tran tsra when devr=$&cs_eps cross=last from=1u to=1.999u
let k_c1_tsr_ns = (tsra - 1u) * 1e9
print k_c1_tsr_ns
alterparam TOP0=1.7500
alterparam VFE1=0.5
reset
tran 0.1n 2.0u 0 1n
meas tran v0r avg v(vref) from=0.8u to=0.99u
let devr = abs(v(vref) - v0r)
meas tran pkr max devr from=1u to=2u
meas tran rr250 find devr at=1.25u
meas tran rr300 find devr at=1.3u
meas tran qk integ i(vsns) from=0.99u to=1.3u
let k_c2_pkr_mv = pkr * 1e3
let k_c2_rr250_mv = rr250 * 1e3
let k_c2_rr300_mv = rr300 * 1e3
let k_c2_qk_fc = qk * 1e15
let k_c2_v0r_v = v0r
print k_c2_pkr_mv
print k_c2_rr250_mv
print k_c2_rr300_mv
print k_c2_qk_fc
print k_c2_v0r_v
meas tran tsra when devr=$&cs_eps cross=last from=1u to=1.999u
let k_c2_tsr_ns = (tsra - 1u) * 1e9
print k_c2_tsr_ns
quit
.endc""" % IF
    s.code(2950, -1330, "CTL", code)
    s.write(BLOCK / "tb_kick.sch")


def tb_cmp():
    s = Sch()
    header(s, "TB_CMP  -  the one output as S2 level and comparator threshold through one decision")
    supply_and_bias(s, "{VDD}", extra=[("VDD_BIAS", "{VDD}", "vddb"), ("VCLK", "0", "clk"), ("VCB", "2", "cb"),
                                      ("VCI", "0", "ci"), ("VREFI", "1.65", "vrefi"),
                                      ("VTOPA0", "{TOPA0}", "vtopa0")])
    # the comparator's bias as its own benches: ideal current into one tail finger
    s.isrc("IREFN", 120, -880, "{IREFC}", "vddb", "nbias")
    s.mos("nfet", "XREFN", 320, -880, "1u", "20u", "10", {"G": "nbias", "D": "nbias", "S": "0", "B": "0"})
    s.isrc("IREFP", 560, -880, "{IREFC}", "pbias", "0")
    s.mos("pfet", "XREFP", 760, -880, "0.28u", "1u", "1", {"G": "pbias", "D": "pbias", "S": "vddb", "B": "vddb"})
    s.T("CONTROLS", 60, -740)
    for i, (name, val, net) in enumerate([
            ("VS2", "PWL(0 {VDD} {TS} {VDD} {TS+0.1n} 0)", "s2"),
            ("VBOT", "PWL(0 {VDD/2} {TDROP} {VDD/2} {TDROP+0.1n} {VDD/2-VDROP} {TR} {VDD/2-VDROP} "
                     "{TSTOP} {VDD/2-VDROP+SLOPE*(TSTOP-TR)})", "bot"),
            ("VSPREA", "PWL(0 2 {TK-5n} 2 {TK-4n} 0)", "sprea"),
            ("VS2A", "PWL(0 0 {TK} 0 {TK+0.1n} {2*AGGON})", "s2a"),
            ("VBOTA", "PWL(0 {VBOT0} {TK} {VBOT0} {TK+0.1n} {VFEA1})", "botsa")]):
        s.vsrc(name, 120, -620 + 170 * i, val, net)
    s.T("DUT + NODE SELECT", 1500, -1260)
    s.dut(1600, -1100, "vrefb")
    s.sw("SWB", 2450, -1160, "swsel", "vref", "vrefb", "cb")
    s.sw("SWI", 2450, -960, "swsel", "vref", "vrefi", "ci")
    s.T("CELL + COMPARATOR", 1500, -820)
    s.sw("S2", 1600, -700, "sws2", "vref", "top", "s2")
    s.mim("XCS", 1850, -650, "top", "bot")
    s.T("C_S 54.52 fF", 1890, -550, 0.3, 4)
    s.res("RLKT", 2150, -650, "1e15", "top")
    s.part("cmp", 2500, -600, "name=XCMP", {"inp": "vref", "inn": "top", "clk": "clk", "nbias": "nbias",
                                            "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.cap("CLOAD", 2750, -600, "10f", "dout")
    s.T("NEIGHBOUR: S2 closes at TK (agg 0: never)", 1500, -400)
    s.sw("SPREA", 1600, -280, "swpre", "topa", "vtopa0", "sprea")
    s.sw("S2A", 1600, -60, "sws2a", "vref", "topa", "s2a")
    s.mim("XCSA", 1850, -200, "topa", "bota")
    s.cap("CTOPPA", 2150, -200, "{CTOP}", "topa")
    s.res("RLKTA", 2400, -200, "1e15", "topa")
    s.res("RS0A", 2650, -200, "{RS0}", "botsa", "bota")
    code = MODELS + """
.include /foss/designs/mixed_signal/comparator/comparator.spice
.temp 27
.param IF=%s
.param VDD=3.3
.param CS_W=5u
.param CS_L=5u
.param TCOUNT=50n
.param SLOPE=117187.5
.param TS=0.5u
.param TDROP=0.51u
.param VDROP=0.15
.param TK=0.55u
.param TR=0.85u
.param TSTOP=2.6u
.param RS2=1k
.param IREFC=1.931u
.param CTOP=17.12f
.param RS0=100
.param VBOT0=2.117
.param AGGON=0
.param TOPA0=2.9900
.param VFEA1=2
.options savecurrents reltol=1e-4 gmin=1e-15
.model swsel sw vt=1 vh=0 ron=1 roff=1e14
.model sws2 sw vt={VDD/2} vh=0.05 ron={RS2} roff=1e14
.model swpre sw vt=1 vh=0.1 ron=100 roff=1e14
.model sws2a sw vt=1 vh=0.1 ron={RS2} roff=1e14
.control
set num_threads=1
tran 0.1n 2.6u 0 1n
meas tran v0 avg v(vref) from=0.3u to=0.45u
meas tran td when v(dout)=1.65 fall=1 from=0.85u
let dev = abs(v(vref) - v0)
let tpre = td - 200n
meas tran pkpre max dev from=$&tpre to=$&td
meas tran pkall max dev from=0.5u to=2.6u
meas tran pkhold max dev from=0.54u to=0.85u
meas tran doutmin min v(dout) from=0.54u to=0.85u
let cmp_v0_v = v0
let cmp_td_ns = td * 1e9
let cmp_pkpre_uv = pkpre * 1e6
let cmp_pkall_uv = pkall * 1e6
let cmp_pkhold_mv = pkhold * 1e3
let cmp_doutmin_v = doutmin
print cmp_v0_v
print cmp_td_ns
print cmp_pkpre_uv
print cmp_pkall_uv
print cmp_pkhold_mv
print cmp_doutmin_v
quit
.endc""" % IF
    s.code(3000, -1330, "CTL", code)
    s.write(BLOCK / "tb_cmp.sch")


def tb_mc():
    s = Sch()
    header(s, "TB_MC  -  VDD/2 offset and follower headroom of midref under PDK mismatch, one draw")
    supply_and_bias(s, "3.3")
    s.T("DUT", 800, -1260)
    s.dut(900, -1100, "vref")
    code = MODELS + """
.param sw_stat_mismatch=1
.temp 27
.param IF=%s
.options seed=%d
.control
set num_threads=1
op
let er = v(vref) - 3.3 / 2
echo MC 1 $&er
let hr1 = abs(@m.xb.xm1.m0[vds]) - abs(@m.xb.xm1.m0[vdsat])
let hr4 = abs(@m.xb.xm4.m0[vds]) - abs(@m.xb.xm4.m0[vdsat])
echo HR 1 $&hr1 $&hr4 $&er
quit
.endc""" % (IF, SEED_BASE + 1)
    s.code(800, -900, "CTL", code)
    s.write(BLOCK / "tb_mc.sch")


def tb_noise():
    s = Sch()
    header(s, "TB_NOISE  -  output noise of midref, 10 Hz - 1 GHz, and the tap-to-output transfer")
    supply_and_bias(s, "3.3", extra=[("VNIN", "DC 0 AC 1", "nin")])
    s.res("RNIN", 630, -1130, "1g", "nin")
    s.isrc("IINJ", 800, -1130, "DC 0 AC 1", "0", "vin")
    s.T("DUT", 1000, -1260)
    s.dut(1100, -1100, "out")
    code = MODELS + """
.temp 27
.param IF=%s
.control
set num_threads=1
set wr_singlescale
noise v(out) VNIN dec 20 10 1g
setplot noise1
wrdata nz_out.txt onoise_spectrum
setplot const
noise v(vin) VNIN dec 20 10 1g
setplot noise3
wrdata nz_tap.txt onoise_spectrum
setplot const
ac dec 20 10 1g
wrdata ac.txt vm(out) vm(vin)
quit
.endc""" % IF
    s.code(800, -900, "CTL", code)
    s.write(BLOCK / "tb_noise.sch")


if __name__ == "__main__":
    tb_op()
    tb_kick()
    tb_cmp()
    tb_mc()
    tb_noise()
