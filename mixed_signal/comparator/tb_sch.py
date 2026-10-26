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


def header(s, title, lines, bottom=-1290, size=0.4, tsize=0.7):
    """The sheet's summary box: title + body lines, framed (layer-4 graphic lines),
    its bottom edge at y = bottom (above the source row)."""
    h = 15 + int(60 * tsize) + int(58 * size * len(lines)) + 32
    y0 = bottom - h
    s.T(title, 60, y0 + 15, tsize)
    s.T("\n".join(lines), 60, y0 + 15 + int(60 * tsize), size)
    w = int(max([len(title) * 28 * tsize] + [len(l) * 30 * size for l in lines])) + 60
    for x1, y1, x2, y2 in ((40, y0, 40 + w, y0), (40 + w, y0, 40 + w, bottom), (40 + w, bottom, 40, bottom),
                           (40, bottom, 40, y0)):
        s.texts.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))


def supplies_and_bias(s, y=-1180, extra=()):
    """Row 1: supplies and the decision level; row 2: the bias reference (one
    tail finger, ideal current) and the unused nbias leg the benches keep."""
    rows = [("VDD_SOURCE", "{VDD}", "vdd"), ("VDD_BIAS", "{VDD}", "vddb")] + list(extra)
    for i, (name, val, net) in enumerate(rows):
        s.vsrc(name, 120 + 170 * i, y, val, net)
    s.T("AVDD (comparator) and the bias supply; " + ", ".join("%s = %s" % (n, v) for n, v, _ in extra), 60, y + 100, 0.32, 4)
    s.part("isource", 120, y + 280, 'name=IREFN value="%s"' % esc("{IREF}"), {"p": "vddb", "m": "nbias"})
    s.mos("nfet", "REFN", 320, y + 280, "1u", "20u", "10", {"G": "nbias", "D": "nbias", "S": "0", "B": "0"})
    s.part("isource", 480, y + 280, 'name=IREFP value="%s"' % esc("{IREF}"), {"p": "pbias", "m": "0"})
    s.mos("pfet", "REFP", 680, y + 280, REF_L, REF_W, REF_NF, {"G": "pbias", "D": "pbias", "S": "vddb", "B": "vddb"})
    s.T("pbias: I_B = %.2f uA design (.param IREF = %s A, data/sizing.json) into one tail finger (L %s, W %s), diode-connected:"
        " tail %g uA, pair %g uA each, starve %g uA design (intent.py); nbias leg (REFN, L 1u W 20u nf 10) unused: no-connect port"
        % (I.I_B_UA, IREF, REF_L, REF_W, I.INTENT_UA["xtail"], I.INTENT_UA["xinp"], I.INTENT_UA["xbst"]), 60, y + 380, 0.32, 4)


def tb_delay():
    s = Sch()
    header(s, "tb_delay: comparator on the unit cell's charge path (plateau level 40.5 LSB), dout into 10 fF",
           ["S2 resets the top plate of the 54.52 fF MIM to VREF and opens at TS = 300 ns (the sample); the bottom plate goes",
            "from VIN to VR_LO at TCONN and ramps at the 8-bit slope (5.859 mV per 50 ns) from TR = 400 ns. The bench is tb_sel.spice.",
            "Measures: delay_dyn = t(dout falls through VDD/2) - t(top crosses VTRIP), VTRIP = tb_trip's result (xtb.py writes it in);",
            "   delay_vbl = the same from top = VBL; fall = dout 90 -> 10 %.",
            "Gates: block (make comparator): delay from the trip <= 12.5 ns, dout fall <= 6 ns.  This drawing (xtb.py):",
            "   equal to the bench within 0.1 ns (delays) and 2 % (fall).",
            "Recorded (runs/comparator-updt-v3-schematic/20261007T232627Z): drawing 10.61 ns / 5.32 ns, bench 10.59 / 5.32 ns;",
            "   with the PDK symbols' drawn S/D junction geometry 11.30 ns / 5.38 ns.  Typical 27 C, 3.3 V, ideal bias.",
            "Values: C_S = 54.52 fF MIM 5 x 5 um (PDK model, cap-characterization c_mim2f0_a0025; 1.99 fF/um2 x A + 0.238 fF/um x P",
            "   = 54.5 fF); CLOAD 10 fF = TSPC latch + wire; RLKT 1e15 ohm = DC path for the floating top plate (numerical, not a",
            "   device); S2 ideal switch 100 ohm on / 1e16 ohm off.  Reproduce: make comparator-schematic."])
    supplies_and_bias(s, extra=[("VVBL", "{VDD/2}", "vbl"), ("VVREF", "{VDD/2}", "vref"), ("VCLK", "0", "clk")])
    for i, (name, val, net, note) in enumerate([
            ("VBOT", "PWL(0 {VIN} {TCONN} {VIN} {TCONN+TEDGE} {VR_LO} {TR} {VR_LO} {TR+14u} {VR_LO+14u*SLOPE})", "bot",
             "bottom plate: VIN until TCONN, then VR_LO, ramp from TR at LSB / TCOUNT"),
            ("VS2", "PWL(0 1 {TS} 1 {TS+TEDGE} 0)", "s2", "S2 control: opens at TS (the sample)")]):
        y = -620 + 170 * i
        s.vsrc(name, 120, y, val, net)
        s.T(note, 180, y - 70, 0.32, 4)
    s.part("switch", 1400, -1140, "name=S2 model=swideal", {"P": "vref", "M": "top", "CP": "s2", "CM": "0"})
    s.part("mim", 1400, -900, "name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1",
           {"B": "top", "G": "bot"})
    s.T("C_S 54.52 fF MIM, top = comparator side", 1440, -840, 0.3)
    s.part("res", 1560, -1010, "name=RLKT value=1e15 footprint=1206 device=resistor m=1", {"p": "top", "m": "0"})
    s.part("cmp", 1900, -1000, "name=XDUT", {"inp": "vbl", "inn": "top", "clk": "clk", "nbias": "nbias",
                                             "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 2140, -1000, "name=CLOAD value=10f m=1", {"p": "dout", "m": "0"})
    s.T("dout: 10 fF (TSPC latch + wire)", 2080, -900, 0.32)
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
    header(s, "tb_trip: static trip of comparator with inp = VBL = VDD/2 (the tb_sel_dc bench)",
           ["inn is swept 1.60 .. 1.70 V in 25 uV steps; the trip is where dout crosses VDD/2 falling.",
            "Its difference from VBL is the static offset at the pins; tb_delay measures its delay from this level.",
            "Measures: vtrip (V).  Gate: no specification gate (it feeds tb_delay's VTRIP); this drawing must equal",
            "   tb_sel_dc.spice within 50 uV (xtb.py).",
            "Recorded (runs/comparator-updt-v3-schematic/20261007T232627Z): vtrip 1.64961 V = -0.39 mV from VBL,",
            "   drawing = bench (diff 1 uV).  Typical 27 C, 3.3 V, ideal bias; dout load CLDC 10 fF.",
            "Reproduce: make comparator-schematic."])
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
    header(s, "tb_noise: input-referred noise of comparator at its decision point (the tb_nz bench)",
           ["dout is fed back to inn through 1 TH, which parks the OTA at its own trip; CINN (1 F) AC-grounds inn.",
            "nz_own_vin: output noise on outa from 1 kHz to 10 GHz divided by the DC gain (thermal + 1/f, own band); gate < 1.2 mV.",
            "Measures: ota_gain_vv (|outa / inp| at 10 Hz), nz_own_vin (V rms at the pins).  Gates: block < 1.2 mV rms",
            "   (= 0.25 LSB at the ADC input); this drawing equal to tb_nz.spice within 1 % (xtb.py).",
            "Recorded (runs/comparator-updt-v3-schematic/20261007T232627Z): gain 44.52 V/V, noise 0.168 mV, drawing = bench",
            "   (rel 2e-6); with drawn S/D geometry 0.163 mV.  Typical 27 C, 3.3 V, ideal bias.",
            "Values: LFB 1 TH (DC feedback only, open at AC), CINN 1 F (AC ground of inn), CLOAD 10 fF.",
            "Reproduce: make comparator-schematic."])
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
    header(s, "tb_mc: threshold spread of comparator, PDK mismatch (sw_stat_mismatch), the tb_mc bench",
           ["Pass 0 is the mismatch-free trip; then N passes with mismatch on, each sweeping inn through VBL +- 70 mV.",
            "rndseed is set, but a run is not shown to repeat (DESIGN_RECIPE.md s.7 note); each run is an independent estimate, so the drawing's samples differ",
            "from the deck's: the nominal trip must match, the spread must agree statistically.",
            "Measures: vos_nom (mismatch off) and 200 mismatch draws of vtrip - VBL -> sigma(Vos).  Gates (xtb.py): vos_nom",
            "   within 0.1 mV of tb_mc.spice, sigma within 20 %.  Block: the 4/3 LSB contract is replaced by ADR 0015",
            "   (offset accepted as signal-independent; covered by ramp pre-roll and pedestal calibration).",
            "Recorded (runs/comparator-updt-v3-schematic/20261007T232627Z): vos_nom -0.341 mV; sigma 8.59 mV drawing,",
            "   9.38 mV bench (runs/comparator-updt-v3/20261007T001140Z) = 2.11 LSB at the ADC input (alpha 0.761).",
            "Reproduce: make comparator-schematic."])
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
