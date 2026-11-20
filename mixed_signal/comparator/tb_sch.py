#!/usr/bin/env python3
"""Emit the xschem testbench schematics of comparator's benches.

    python3 tb_sch.py     -> tb_tran.sch, tb_dc.sch, tb_nz.sch, tb_mc.sch

Each testbench draws one bench template of bench.py (tb_<name>.spice) filled
for the `sw` variant at the nominal point (typical, 27 C, 3.3 V, the ideal
bias 1.93077 uA into one tail finger, 10 fF on dout, ADR 0025 grid): the
sources, the comparator as comparator.sym (xschem netlists
comparator.sch into it, so the testbench exercises the drawing, not the
deck) and a code block with the model lines and the analysis. The values are
written with bench.py's own formats. xtb.py netlists every drawing, runs
ngspice on it and compares its figures with the bench's record
(data/values_verify.txt).

| Testbench   | Template      | Fixed at                                          |
| tb_tran.sch | tb_tran.spice | 40.5 LSB, the whole conversion (TR .. count 260)  |
| tb_dc.sch   | tb_dc.spice   | the plate pin inp swept VDD/2 +- 50 mV            |
| tb_nz.sch   | tb_nz.spice   | parked at the trip through 1 TH from dout to inp  |
| tb_mc.sch   | tb_mc.spice   | 200 samples, seed 20261117                        |

Parts are placed in the template's line order (ngspice Monte Carlo draws
follow the device order). Placement is hand-authored.
"""
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
sys.path.insert(0, str(BLOCK))
import intent as I  # noqa: E402  design-intent currents (the one source)

# the nominal `sw` point, in bench.py's formats (bench.py: I_F, LSB_GRID, C_LOAD, REFP, cell_subs, level)
VDD = 3.3
I_F = 1.93077e-6
LSB = 6.701613e-3 * VDD / 3.3
VRLO = 7.0 / 55.0 * VDD
LEVEL = 40.5
TCOUNT = 50e-9
IREF = "%.6g" % I_F
VCM = "%.6g" % (VDD / 2)
TSTOP = "%.6g" % (400e-9 + 260 * TCOUNT)
VTRIP0 = 1.65039                       # replaced by xtb.py with tb_dc's result
N_MC, SEED = 200, 20261117

MOS_ATTR = ('ad="\'int((nf+1)/2) * W/nf * 0.18u\'"\n'
            'pd="\'2*int((nf+1)/2) * (W/nf + 0.18u)\'"\n'
            'as="\'int((nf+2)/2) * W/nf * 0.18u\'"\n'
            'ps="\'2*int((nf+2)/2) * (W/nf + 0.18u)\'"\n'
            'nrd="\'0.18u / W\'" nrs="\'0.18u / W\'"\n'
            'sa=0 sb=0 sd=0')
MODELS = (".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
          ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical")
COMMON = ".param VDD=%g\n.temp 27\n.param IREF=%s" % (VDD, IREF)


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

    def cmp(self, name, x, y, nets):
        self.part("cmp", x, y, "name=%s" % name, nets)

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
        print("REPORT: wrote %s: %d symbols, %d wires, %d texts"
              % (path.name, len(self.inst) - self.n, len(self.wires), len(self.texts)))


def header(s, title):
    """The sheet's one-line title (with the bias current) above the source rows."""
    s.T("%s, I_B = %.2f uA" % (title, I.I_B_UA), 60, -1330, 0.7)


def supplies_and_bias(s, extra=(), y=-1180):
    """The templates' first lines: the supplies, the bias reference (one tail
    finger, ideal current) and the unused nbias leg; then `extra` sources in
    row 1 after the supplies (the template's next lines)."""
    s.vsrc("VDD_SOURCE", 120, y, "{VDD}", "vdd")
    s.vsrc("VDD_BIAS", 290, y, "{VDD}", "vddb")
    s.part("isource", 120, y + 280, 'name=IREFN value="%s"' % esc("{IREF}"), {"p": "vddb", "m": "nbias"})
    s.mos("nfet", "REFN", 320, y + 280, "1u", "20u", "10", {"G": "nbias", "D": "nbias", "S": "0", "B": "0"})
    s.part("isource", 480, y + 280, 'name=IREFP value="%s"' % esc("{IREF}"), {"p": "pbias", "m": "0"})
    s.mos("pfet", "REFP", 680, y + 280, "0.28u", "1u", "1", {"G": "pbias", "D": "pbias", "S": "vddb", "B": "vddb"})
    for i, (name, val, net) in enumerate(extra):
        s.vsrc(name, 460 + 170 * i, y, val, net)


def tb_tran():
    s = Sch()
    header(s, "TB_TRAN  -  delay and polarity of comparator on the cell's charge path")
    supplies_and_bias(s, extra=[("VCLK", "0", "clk"), ("VVREF", "{VDD/2}", "vref")])
    s.vsrc("VDRV", 120, -620, "PWL(0 {VIN} {TCONN} {VIN} {TCONN+TEDGE} {VR_LO} {TR} {VR_LO} {TR+20u} "
                              "{VR_LO+20u*SLOPE})", "drv")
    s.vsrc("VS2", 120, -450, "PWL(0 1 {TS} 1 {TS+TEDGE} 0)", "s2")
    s.part("switch", 1400, -1140, "name=S2 model=swideal", {"P": "vref", "M": "plate", "CP": "s2", "CM": "0"})
    s.part("mim", 1400, -900, "name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1",
           {"G": "plate", "B": "drv"})          # xschem lists G first: XCS plate drv, as the deck
    s.T("C_S 54.52 fF", 1440, -840, 0.3, 4)
    s.part("res", 1560, -1010, "name=RLKT value=1e15 footprint=1206 device=resistor m=1", {"p": "plate", "m": "0"})
    s.cmp("XDUT", 1900, -1000, {"inp": "plate", "inn": "vref", "clk": "clk", "nbias": "nbias",
                                "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 2140, -1000, "name=CLOAD value=%.4g m=1" % 10e-15, {"p": "dout", "m": "0"})
    code = MODELS + """
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
""" + COMMON + """
.param VIN=%.9g
.param VR_LO=%.9g
.param LSB=%.9g
.param TCOUNT=50n
.param SLOPE='LSB/TCOUNT'
.param TS=300n
.param TCONN=310n
.param TR=400n
.param TEDGE=100p
.csparam cs_vdd={VDD}
.csparam cs_tr={TR}
.csparam cs_tconn={TCONN}
.csparam cs_tideal={TR+(VIN-VR_LO)/SLOPE}
.options savecurrents reltol=1e-4 gmin=1e-15
.control
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
let lvla = hi90
let lvlb = lo10
set vtrip_s = "%.6f"
tran 0.25n %s 0 0.5n
meas tran t_cross when v(plate)=%s rise=1 td=$&cs_tr
meas tran t_cs when v(plate)=$vtrip_s rise=1 td=$&cs_tr
meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr
meas tran t_ea when v(dout)=$&lvla fall=1 td=$&cs_tr
meas tran t_eb when v(dout)=$&lvlb fall=1 td=$&cs_tr
meas tran armed find v(dout) at=$&cs_tr
meas tran vplate_tr find v(plate) at=$&cs_tr
meas tran i_avg avg i(vdd_source) from=$&cs_tconn to=$&t_cross
let delay_vref = t_dout - t_cross
let delay_dyn = t_dout - t_cs
let edge = t_eb - t_ea
let ped_counts = (t_dout - $&cs_tideal) / 50e-9
let p_avg = -$&cs_vdd * i_avg
echo "RESULT_BEGIN"
print delay_vref
print delay_dyn
print edge
print ped_counts
print armed
print p_avg
print vplate_tr
print t_dout
echo "RESULT_END"
quit
.endc""" % (VRLO + LEVEL * LSB, VRLO, LSB, VTRIP0, TSTOP, VCM)
    s.code(1300, -700, "CTL", code)
    s.write(BLOCK / "tb_tran.sch")


def tb_dc():
    s = Sch()
    header(s, "TB_DC  -  static trip of comparator, inn = VREF = VDD/2")
    supplies_and_bias(s, extra=[("VCLK", "0", "clk"), ("VVREF", "{VDD/2}", "vref"), ("VDC", VCM, "vdc")])
    s.cmp("XDC", 1300, -1000, {"inp": "vdc", "inn": "vref", "clk": "clk", "nbias": "nbias",
                               "pbias": "pbias", "dout": "doutdc", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1540, -1000, "name=CLDC value=%.4g m=1" % 10e-15, {"p": "doutdc", "m": "0"})
    code = MODELS + "\n" + COMMON + """
.control
dc VDC %s %s 25u
meas dc vtrip when v(doutdc)=%s fall=1
echo "RESULT_BEGIN"
print vtrip
echo "RESULT_END"
quit
.endc""" % ("%.6g" % (VDD / 2 - 0.05), "%.6g" % (VDD / 2 + 0.05), VCM)
    s.code(1000, -560, "CTL", code)
    s.write(BLOCK / "tb_dc.sch")


def tb_nz():
    s = Sch()
    header(s, "TB_NZ  -  input-referred noise of comparator at its trip")
    supplies_and_bias(s, extra=[("VCLK", "{VDD}", "clk"), ("VSIG", "DC %s AC 1" % VCM, "inn")])
    s.part("capa", 1100, -760, "name=CFB value=1 m=1", {"p": "inp", "m": "0"})
    s.part("ind", 1100, -1060, "name=LFB value=1T m=1", {"p": "dout", "m": "inp"})
    s.cmp("XDUT", 1400, -1000, {"inp": "inp", "inn": "inn", "clk": "clk", "nbias": "nbias",
                                "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1640, -1000, "name=CLOAD value=%.4g m=1" % 10e-15, {"p": "dout", "m": "0"})
    code = MODELS + "\n" + COMMON + """
.options savecurrents
.control
op
let op_i_vdd = -i(vdd_source)
echo "RESULT_BEGIN"
print op_i_vdd
ac dec 20 10 100G
meas ac ota_gain_vv find vm(xdut.outa) at=10
let g3 = ota_gain_vv / sqrt(2)
meas ac ota_pole_hz when vm(xdut.outa)=$&g3 fall=1
meas ac ota_ugbw_hz when vm(xdut.outa)=1 fall=1
print ota_gain_vv
print ota_pole_hz
set g = $&ota_gain_vv
set ugb = $&ota_ugbw_hz
noise v(xdut.outa) vsig dec 20 1k 10G
let nz_own_vin = onoise_total / $g
print nz_own_vin
noise v(xdut.outa) vsig dec 20 1k 100k
let nz_lo_vin = onoise_total / $g
print nz_lo_vin
noise v(xdut.outa) vsig dec 20 1k $ugb
let nz_ugb_vin = inoise_total
print nz_ugb_vin
echo "RESULT_END"
quit
.endc"""
    s.code(1000, -560, "CTL", code)
    s.write(BLOCK / "tb_nz.sch")


def tb_mc():
    s = Sch()
    header(s, "TB_MC  -  threshold spread of comparator, PDK mismatch")
    supplies_and_bias(s, extra=[("VCLK", "{VDD}", "clk"), ("VREFX", VCM, "vrefx"), ("VSW", VCM, "vsw")])
    s.cmp("XDUT", 1300, -1000, {"inp": "vsw", "inn": "vrefx", "clk": "clk", "nbias": "nbias",
                                "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1540, -1000, "name=CLOAD value=%.4g m=1" % 10e-15, {"p": "dout", "m": "0"})
    lo, hi = "%.6g" % (VDD / 2 - 0.07), "%.6g" % (VDD / 2 + 0.07)
    code = MODELS + "\n.param sw_stat_mismatch=1\n" + COMMON + """
.csparam cs_n=%d
.control
set rndseed=%d
let k = 0
alterparam sw_stat_mismatch=0
reset
dc vsw %s %s 0.0002
meas dc vtrip when v(dout)=%s fall=1
let vos_nom = vtrip - %s
print vos_nom
alterparam sw_stat_mismatch=1
while k < $&cs_n
  reset
  dc vsw %s %s 0.0002
  meas dc vtrip when v(dout)=%s fall=1
  let vos_k = vtrip - %s
  print vos_k
  let k = k + 1
end
quit
.endc""" % (N_MC, SEED, lo, hi, VCM, VCM, lo, hi, VCM, VCM)
    s.code(1000, -560, "CTL", code)
    s.write(BLOCK / "tb_mc.sch")


if __name__ == "__main__":
    tb_tran()
    tb_dc()
    tb_nz()
    tb_mc()
