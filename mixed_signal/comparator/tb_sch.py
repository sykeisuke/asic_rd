#!/usr/bin/env python3
"""Emit the xschem testbench schematics of comparator's benches.

    python3 tb_sch.py     -> tb_delay.sch, tb_trip.sch, tb_noise.sch, tb_mc.sch

Each testbench draws one bench of the block at its nominal point (typical,
27 C, 3.3 V, the ideal bias of data/sizing.json): the sources, the
comparator as comparator.sym (xschem netlists comparator.sch into it, so
the testbench exercises the drawing, not the deck), the 10 fF load, and a
code block with the model lines and the analysis. xtb.py netlists every
drawing with xschem, runs ngspice on it and compares its figures with the
hand-written bench's (data/xtb.csv, check-xtb.awk).

| Testbench     | Bench it draws                    | Fixed at                                    |
| tb_delay.sch  | tb_sel.spice (size_v3 / verify)   | plateau level 40.5 LSB, typical bias        |
| tb_trip.sch   | tb_sel_dc.spice                   | inn swept VBL +- 50 mV                      |
| tb_noise.sch  | tb_nz.spice                       | parked at the trip through 1 TH from dout   |
| tb_mc.sch     | tb_mc.spice                       | 200 samples                                 |

Placement is hand-authored; device sizes of the bias reference and the
ideal current come from data/sizing.json.
"""
import json
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
SEL = json.loads((BLOCK / "data" / "sizing.json").read_text())
sys.path.insert(0, str(BLOCK))
import intent as I  # noqa: E402  design-intent currents (the one source)
REF_L, REF_W, REF_NF = "%gu" % SEL["l_b"], "%gu" % (SEL["w_fp"] * 1e6), "1"
IREF = "%.6g" % SEL["iref"]
MOS_ATTR = ('ad="\'int((nf+1)/2) * W/nf * 0.18u\'"\n'
            'pd="\'2*int((nf+1)/2) * (W/nf + 0.18u)\'"\n'
            'as="\'int((nf+2)/2) * W/nf * 0.18u\'"\n'
            'ps="\'2*int((nf+2)/2) * (W/nf + 0.18u)\'"\n'
            'nrd="\'0.18u / W\'" nrs="\'0.18u / W\'"\n'
            'sa=0 sb=0 sd=0')
MODELS = (".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
          ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical")
COMMON = ".param VDD=3.3\n.param IREF=%s   $ data/sizing.json iref: ideal current into one tail finger\n.temp 27" % IREF


def esc(s):
    return s.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


class Sch:
    # pin offsets and the direction their stub leaves in
    PINS = {
        "vsource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "isource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "capa": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "res": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "ind": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "switch": {"P": (0, -30, "U"), "M": (0, 30, "D"), "CP": (-40, 0, "L"), "CM": (-40, 20, "L")},
        "mim": {"G": (0, -30, "U"), "B": (0, 30, "D")},
        "pfet": {"G": (-20, 0, "L"), "S": (20, -30, "U"), "D": (20, 30, "D"), "B": (20, 0, "R")},
        "nfet": {"G": (-20, 0, "L"), "D": (20, -30, "U"), "S": (20, 30, "D"), "B": (20, 0, "R")},
        "cmp": {"inp": (-100, -60, "L"), "inn": (-100, -30, "L"), "clk": (-100, 0, "L"), "nbias": (-100, 30, "L"),
                "pbias": (-100, 60, "L"), "dout": (100, -45, "R"), "vdd": (0, -120, "U"), "vss": (0, 120, "D")},
    }
    SYM = {"vsource": "devices/vsource.sym", "isource": "devices/isource.sym", "capa": "devices/capa.sym",
           "res": "devices/res.sym", "ind": "devices/ind.sym", "switch": "devices/switch_ngspice.sym",
           "mim": "symbols/cap_mim_2f0fF.sym", "pfet": "symbols/pfet_03v3.sym", "nfet": "symbols/nfet_03v3.sym",
           "cmp": "comparator.sym"}
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
            dx, dy, d = self.PINS[kind][pin]
            px, py = x + dx, y + dy
            ex, ey = {"U": (px, py - self.STUB), "D": (px, py + self.STUB),
                      "L": (px - self.STUB, py), "R": (px + self.STUB, py)}[d]
            self.wires.append((px, py, ex, ey))
            self.label(ex, ey, net, d != "R")

    def mos(self, kind, name, x, y, l, w, nf, nets):
        attrs = "name=%s\nL=%s W=%s nf=%s m=1\n%s model=%s_03v3 spiceprefix=X" % (name, l, w, nf, MOS_ATTR, kind)
        self.part(kind, x, y, attrs, nets)

    def vsrc(self, name, x, y, value, p, m="0"):
        self.part("vsource", x, y, 'name=%s value="%s" savecurrent=false' % (name, esc(value)), {"p": p, "m": m})

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
        print("REPORT: wrote %s: %d symbols, %d wires" % (path.name, len(self.inst) - self.n, len(self.wires)))


def header(s, title):
    """The sheet's one-line title (with the bias current), above the source row
    (CLAUDE.md, "Schematic drawings": the bench's description lives in the README)."""
    s.T("%s, I_B = %.2f uA" % (title, I.I_B_UA), 60, -1330, 0.7)


def supplies_and_bias(s, y=-1180, extra=()):
    """Row 1: supplies and the decision level; row 2: the bias reference (one
    tail finger, ideal current) and the unused nbias leg the benches keep."""
    rows = [("VDD_SOURCE", "{VDD}", "vdd"), ("VDD_BIAS", "{VDD}", "vddb")] + list(extra)
    for i, (name, val, net) in enumerate(rows):
        s.vsrc(name, 120 + 170 * i, y, val, net)
    s.part("isource", 120, y + 280, 'name=IREFN value="%s"' % esc("{IREF}"), {"p": "vddb", "m": "nbias"})
    s.mos("nfet", "REFN", 320, y + 280, "1u", "20u", "10", {"G": "nbias", "D": "nbias", "S": "0", "B": "0"})
    s.part("isource", 480, y + 280, 'name=IREFP value="%s"' % esc("{IREF}"), {"p": "pbias", "m": "0"})
    s.mos("pfet", "REFP", 680, y + 280, REF_L, REF_W, REF_NF, {"G": "pbias", "D": "pbias", "S": "vddb", "B": "vddb"})


def tb_delay():
    s = Sch()
    header(s, "TB_DELAY  -  comparator delay on the cell's charge path, dout into 10 fF")
    supplies_and_bias(s, extra=[("VVBL", "{VDD/2}", "vbl"), ("VVREF", "{VDD/2}", "vref"), ("VCLK", "0", "clk")])
    for i, (name, val, net) in enumerate([
            ("VBOT", "PWL(0 {VIN} {TCONN} {VIN} {TCONN+TEDGE} {VR_LO} {TR} {VR_LO} {TR+14u} {VR_LO+14u*SLOPE})", "bot"),
            ("VS2", "PWL(0 1 {TS} 1 {TS+TEDGE} 0)", "s2")]):
        y = -620 + 170 * i
        s.vsrc(name, 120, y, val, net)
    s.part("switch", 1400, -1140, "name=S2 model=swideal", {"P": "vref", "M": "top", "CP": "s2", "CM": "0"})
    s.part("mim", 1400, -900, "name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1",
           {"B": "top", "G": "bot"})
    s.T("C_S 54.52 fF", 1440, -840, 0.3, 4)
    s.part("res", 1560, -1010, "name=RLKT value=1e15 footprint=1206 device=resistor m=1", {"p": "top", "m": "0"})
    s.part("cmp", 1900, -1000, "name=XDUT", {"inp": "vbl", "inn": "top", "clk": "clk", "nbias": "nbias",
                                             "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 2140, -1000, "name=CLOAD value=10f m=1", {"p": "dout", "m": "0"})
    code = MODELS + """
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
""" + COMMON + """
.param VTRIP=1.649611   $ replaced by xtb.py with tb_trip's result
.param VIN='VR_LO+40.5*LSB'
.param VR_LO=0.5
.param LSB=0.005859375
.param TCOUNT=50n
.param SLOPE='LSB/TCOUNT'
.param TS=300n
.param TCONN=310n
.param TR=400n
.param TEDGE=100p
.csparam cs_vdd={VDD}
.csparam cs_tr={TR}
.csparam cs_vtrip={VTRIP}
.options savecurrents reltol=1e-4 gmin=1e-15
.control
tran 0.25n 2.825u 0 0.5n
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_cross when v(top)=1.65 rise=1 td=$&cs_tr
meas tran t_cs when v(top)=$&cs_vtrip rise=1 td=$&cs_tr
meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr
meas tran t_f90 when v(dout)=$&hi90 fall=1 td=$&cs_tr
meas tran t_f10 when v(dout)=$&lo10 fall=1 td=$&cs_tr
let delay_vbl = t_dout - t_cross
let delay_dyn = t_dout - t_cs
let fall = t_f10 - t_f90
echo "RESULT_BEGIN"
print delay_vbl delay_dyn fall
echo "RESULT_END"
quit
.endc"""
    s.code(1300, -700, "CTL", code)
    s.write(BLOCK / "tb_delay.sch")


def tb_trip():
    s = Sch()
    header(s, "TB_TRIP  -  static trip of comparator, inp = VBL = VDD/2")
    supplies_and_bias(s, extra=[("VVBL", "{VDD/2}", "vbl"), ("VDC", "1.65", "vdc"), ("VCLK", "0", "clk")])
    s.part("cmp", 1300, -1000, "name=XDC", {"inp": "vbl", "inn": "vdc", "clk": "clk", "nbias": "nbias",
                                            "pbias": "pbias", "dout": "doutdc", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1540, -1000, "name=CLDC value=10f m=1", {"p": "doutdc", "m": "0"})
    code = MODELS + "\n" + COMMON + """
.control
dc VDC 1.60 1.70 25u
meas dc vtrip when v(doutdc)=1.65 fall=1
echo "RESULT_BEGIN"
print vtrip
echo "RESULT_END"
quit
.endc"""
    s.code(1000, -560, "CTL", code)
    s.write(BLOCK / "tb_trip.sch")


def tb_noise():
    s = Sch()
    header(s, "TB_NOISE  -  input-referred noise of comparator at its trip")
    supplies_and_bias(s, extra=[("VINP", "DC 1.65 AC 1", "inp"), ("VCLK", "{VDD}", "clk")])
    s.part("capa", 1100, -760, "name=CINN value=1 m=1", {"p": "inn", "m": "0"})
    s.part("ind", 1100, -1060, "name=LFB value=1T m=1", {"p": "dout", "m": "inn"})
    s.part("cmp", 1400, -1000, "name=XDUT", {"inp": "inp", "inn": "inn", "clk": "clk", "nbias": "nbias",
                                             "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1640, -1000, "name=CLOAD value=10f m=1", {"p": "dout", "m": "0"})
    code = MODELS + "\n" + COMMON + """
.options savecurrents
.control
op
ac dec 20 10 100G
meas ac ota_gain_vv find vm(xdut.outa) at=10
echo "RESULT_BEGIN"
print ota_gain_vv
set g = $&ota_gain_vv
noise v(xdut.outa) vinp dec 20 1k 10G
let nz_own_vin = onoise_total / $g
print nz_own_vin
echo "RESULT_END"
quit
.endc"""
    s.code(1000, -560, "CTL", code)
    s.write(BLOCK / "tb_noise.sch")


def tb_mc():
    s = Sch()
    header(s, "TB_MC  -  threshold spread of comparator, PDK mismatch")
    supplies_and_bias(s, extra=[("VINP", "1.65", "inp"), ("VINN", "1.65", "inn"), ("VCLK", "{VDD}", "clk")])
    s.part("cmp", 1300, -1000, "name=XDUT", {"inp": "inp", "inn": "inn", "clk": "clk", "nbias": "nbias",
                                             "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1540, -1000, "name=CLOAD value=10f m=1", {"p": "dout", "m": "0"})
    code = MODELS + "\n.param sw_stat_mismatch=1\n" + COMMON + """
.csparam cs_n=200
.control
set rndseed=20261006
let k = 0
alterparam sw_stat_mismatch=0
reset
dc vinn 1.58 1.72 0.0002
meas dc vtrip when v(dout)=1.65 fall=1
let vos_nom = vtrip - 1.65
print vos_nom
alterparam sw_stat_mismatch=1
while k < $&cs_n
  reset
  dc vinn 1.58 1.72 0.0002
  meas dc vtrip when v(dout)=1.65 fall=1
  let vos_k = vtrip - 1.65
  print vos_k
  let k = k + 1
end
quit
.endc"""
    s.code(1000, -560, "CTL", code)
    s.write(BLOCK / "tb_mc.sch")


if __name__ == "__main__":
    tb_delay()
    tb_trip()
    tb_noise()
    tb_mc()
