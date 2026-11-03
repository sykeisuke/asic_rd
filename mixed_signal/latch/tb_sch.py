#!/usr/bin/env python3
"""Emit the xschem testbench schematics of latch's benches.

    python3 tb_sch.py     -> tb_drive.sch, tb_aperture.sch, tb_kick.sch

Each testbench draws one bench template (tb_*.spice) at the nominal case
bench.py renders it with: typical, 27 C, 3.3 V, the nominal clock and d
edges, q into CQ. The DUT is latch.sym (xschem netlists latch.sch into it, so
the testbench exercises the drawing, not latch.spice); tb_kick places the
comparator through ../comparator/comparator.sym (xschemrc), so that
comparator.sch is what the netlist carries. A code block holds the model
lines, the library include, the parameters and the .control block with the
bench's main figures. xtb.py netlists every drawing with xschem, runs ngspice
on it and compares its figures with the hand-written bench's (data/xtb.csv).

| Testbench        | Bench it draws   | Fixed at                                              |
| tb_drive.sch     | tb_drive.spice   | clk 0.5 ns, d 10.4 ns 10-90 %, CQ 50 fF (bench.py)    |
| tb_aperture.sch  | tb_aperture.spice| the same, d's edge DT = 0 from the sampling edge      |
| tb_kick.sch      | tb_kick.spice    | VIN at code 64 (0.875 V), clock running, the `latch`  |
|                  |                  | load; the TSPC and 10 fF references stay in the deck  |

The TSPC reference (ref/tspc_dff.spice) and the LOAD variants are deck-only.
Placement is hand-authored; every value on a sheet comes from bench.py.
"""
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
sys.path.insert(0, str(BLOCK))
import bench as B  # noqa: E402  the one source of the nominal case

LIB = "/foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice"
MODELS = (".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
          ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical")
MOS_ATTR = ('ad="\'int((nf+1)/2) * W/nf * 0.18u\'"\n'
            'pd="\'2*int((nf+1)/2) * (W/nf + 0.18u)\'"\n'
            'as="\'int((nf+2)/2) * W/nf * 0.18u\'"\n'
            'ps="\'2*int((nf+2)/2) * (W/nf + 0.18u)\'"\n'
            'nrd="\'0.18u / W\'" nrs="\'0.18u / W\'"\n'
            'sa=0 sb=0 sd=0')

# the nominal case, as bench.py renders it
TCE = "%.6e" % (B.T1090_CLK_NOM / 0.8)      # clock 0-100 % edge
TDF = "%.6e" % B.TDF_SLOW                   # d 0-100 % edge (comparator's slowest dout fall)
CQ = "%gf" % (B.CQ * 1e15)
AP_DT = 0.0                                 # d's edge centred on the sampling edge
KICK_CODE = 64
KICK_VIN = B.VR_LO + KICK_CODE * B.LSB
CLK_T1090_TXT = "clk 10-90 %% %.1f ns" % (B.T1090_CLK_NOM * 1e9)
D_T1090_TXT = "d 10-90 %% %.1f ns" % (B.TDF_SLOW * 0.8e9)
CQ_TXT = "CQ = %g fF" % (B.CQ * 1e15)


def esc(s):
    return s.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


class Sch:
    # pin offsets and the direction their stub leaves in
    PINS = {
        "vsource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "isource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "capa": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "res": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "switch": {"P": (0, -30, "U"), "M": (0, 30, "D"), "CP": (-40, 0, "L"), "CM": (-40, 20, "L")},
        "mim": {"G": (0, -30, "U"), "B": (0, 30, "D")},
        "pfet": {"G": (-20, 0, "L"), "S": (20, -30, "U"), "D": (20, 30, "D"), "B": (20, 0, "R")},
        "latch": {"d": (-100, -20, "L"), "clk": (-100, 20, "L"), "q": (100, -20, "R"),
                  "vdd": (0, -80, "U"), "vss": (0, 80, "D")},
        "cmp": {"inp": (-100, -60, "L"), "inn": (-100, -30, "L"), "clk": (-100, 0, "L"), "nbias": (-100, 30, "L"),
                "pbias": (-100, 60, "L"), "dout": (100, -45, "R"), "vdd": (0, -120, "U"), "vss": (0, 120, "D")},
    }
    SYM = {"vsource": "devices/vsource.sym", "isource": "devices/isource.sym", "capa": "devices/capa.sym",
           "res": "devices/res.sym", "switch": "devices/switch_ngspice.sym",
           "mim": "symbols/cap_mim_2f0fF.sym", "pfet": "symbols/pfet_03v3.sym",
           "latch": "latch.sym", "cmp": "comparator.sym"}
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
        print("REPORT: wrote %s: %d symbols, %d wires, %d texts" % (path.name, len(self.inst) - self.n,
                                                                    len(self.wires), len(self.texts)))


def header(s, title):
    s.T(title, 60, -1360, 0.7)


def latch_dut(s, x, y, d, clk):
    """The DUT as latch.sym (xschem descends into latch.sch), q into CQ."""
    s.T("DUT", x - 140, -1292, 0.45, 4)
    s.part("latch", x, y, "name=XL", {"d": d, "clk": clk, "q": "q", "vdd": "dvdd", "vss": "0"})
    s.part("capa", x + 240, y - 20, "name=CQ value=%s m=1" % CQ, {"p": "q", "m": "0"})
    s.T(CQ_TXT, x + 280, y + 70, 0.3, 4)


def latch_params():
    return ".param VDD=%g\n.param TCOUNT=50n\n.param TCE=%s\n.param TDF=%s" % (B.VDD, TCE, TDF)


def tb_drive():
    s = Sch()
    header(s, "TB_DRIVE  -  latch alone, 20 MHz clock, d moves in both clock phases, q into 50 fF")
    s.T("SUPPLY / CLOCK / D", 40, -1292, 0.45, 4)
    s.vsrc("VDVDD", 120, -1180, "{VDD}", "dvdd")
    s.vsrc("VCLK", 360, -1180, "PULSE({VDD} 0 {TCOUNT/2-TCE/2} {TCE} {TCE} {TCOUNT/2-TCE} {TCOUNT})", "clk")
    s.T(CLK_T1090_TXT, 40, -1010, 0.3, 4)
    s.T(D_T1090_TXT, 40, -960, 0.3, 4)
    s.vsrc("VD", 120, -780, "PWL(0 {VDD} {412.5n-TDF/2} {VDD} {412.5n+TDF/2} 0 {587.5n-TDF/2} 0 {587.5n+TDF/2} {VDD} "
           "{787.5n-TDF/2} {VDD} {787.5n+TDF/2} 0 {962.5n-TDF/2} 0 {962.5n+TDF/2} {VDD})", "d")
    latch_dut(s, 1500, -1160, "d", "clk")
    code = MODELS + "\n.include " + LIB + "\n" + latch_params() + """
.param TSTOP=1100n
.temp 27
.csparam cs_vdd={VDD}
.options savecurrents reltol=1e-4
.tran 5p {TSTOP} 0 20p
.control
run
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_edge when v(clk)=$&half fall=1 td=413e-9
meas tran t_q when v(q)=$&half fall=1 td=100e-9
meas tran t_q90 when v(q)=$&hi90 fall=1 td=100e-9
meas tran t_q10 when v(q)=$&lo10 fall=1 td=100e-9
let tcq = t_q - t_edge
let q_fall = t_q10 - t_q90
set numdgt=10
echo RESULT_BEGIN
print tcq q_fall t_edge t_q
echo RESULT_END
quit
.endc"""
    s.code(60, -640, "CTL", code)
    s.write(BLOCK / "tb_drive.sch")


def tb_aperture():
    s = Sch()
    header(s, "TB_APERTURE  -  d's edge DT from the sampling edge at 125 ns, one q fall")
    s.T("SUPPLY / CLOCK / D", 40, -1292, 0.45, 4)
    s.vsrc("VDVDD", 120, -1180, "{VDD}", "dvdd")
    s.vsrc("VCLK", 360, -1180, "PULSE({VDD} 0 {TCOUNT/2-TCE/2} {TCE} {TCE} {TCOUNT/2-TCE} {TCOUNT})", "clk")
    s.T(CLK_T1090_TXT, 40, -1010, 0.3, 4)
    s.T(D_T1090_TXT, 40, -960, 0.3, 4)
    s.T("DT = %g ns" % (AP_DT * 1e9), 40, -910, 0.3, 4)
    s.vsrc("VD", 120, -780, "PWL(0 {VDD} {TE+DT-TDF/2} {VDD} {TE+DT+TDF/2} 0)", "d")
    latch_dut(s, 1500, -1160, "d", "clk")
    code = MODELS + "\n.include " + LIB + "\n" + latch_params() + """
.param TE=125n
.param DT=%.15e
.param TSTOP=240n
.temp 27
.csparam cs_vdd={VDD}
.csparam cs_te={TE}
.csparam cs_tcount={TCOUNT}
.options reltol=1e-5 abstol=1e-13 vntol=1e-7
.tran 1p {TSTOP} 0 5p
.control
run
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_q when v(q)=$&half fall=1 td=100e-9
meas tran t_q2 when v(q)=$&half fall=2 td=100e-9
meas tran t_qr when v(q)=$&half rise=1 td=100e-9
meas tran t_q90 when v(q)=$&hi90 fall=1 td=100e-9
meas tran t_q10 when v(q)=$&lo10 fall=1 td=100e-9
let t_edge = $&cs_te + floor((t_q - $&cs_te) / $&cs_tcount) * $&cs_tcount
let edge_k = (t_edge - $&cs_te) / $&cs_tcount
let tcq = t_q - t_edge
let q_fall = t_q10 - t_q90
set numdgt=10
echo RESULT_BEGIN
print tcq q_fall edge_k t_q
echo RESULT_END
quit
.endc""" % AP_DT
    s.code(60, -640, "CTL", code)
    s.write(BLOCK / "tb_aperture.sch")


def tb_kick():
    s = Sch()
    header(s, "TB_KICK  -  comparator + latch on the cell's charge path, count clock running")
    s.T("SUPPLIES / BIAS / CLOCK", 40, -1292, 0.45, 4)
    for i, (name, val, net) in enumerate([("VDD_SOURCE", "{VDD}", "vdd"), ("VDVDD", "{VDD}", "dvdd"),
                                          ("VVBL", "{VDD/2}", "vbl"), ("VVREF", "{VDD/2}", "vref")]):
        s.vsrc(name, 120 + 170 * i, -1180, val, net)
    s.vsrc("VCLK", 800, -1180, "PULSE(0 {VDD} {TCOUNT-TCE/2} {TCE} {TCE} {TCOUNT/2-TCE} {TCOUNT})", "clk")
    s.T(CLK_T1090_TXT, 760, -1010, 0.3, 4)
    s.part("isource", 120, -900, 'name=IREFP value="%s"' % esc("{IBIAS}"), {"p": "pbias", "m": "0"})
    s.mos("pfet", "REFP", 320, -900, "0.28u", "1u", "1", {"G": "pbias", "D": "pbias", "S": "vdd", "B": "vdd"})
    s.T("I_B %.2f uA" % (1.681 * 1.93077), 40, -790, 0.3, 4)
    s.vsrc("VBOT", 120, -600, "PWL(0 {VIN} {TCONN} {VIN} {TCONN+TEDGE} {VR_LO} {TR} {VR_LO} {TR+TRAMP} {VR_HI+OVR})", "bot")
    s.T("VIN = %.4g V  (code %d)" % (KICK_VIN, KICK_CODE), 40, -750, 0.3, 4)
    s.vsrc("VS2", 120, -430, "PWL(0 1 {TS} 1 {TS+TEDGE} 0)", "s2")
    s.T("CHARGE PATH", 1240, -1292, 0.45, 4)
    s.part("switch", 1400, -1140, "name=S2 model=swideal", {"P": "vref", "M": "top", "CP": "s2", "CM": "0"})
    s.part("mim", 1400, -900, "name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1",
           {"B": "top", "G": "bot"})
    s.T("C_S 54.52 fF", 1440, -840, 0.3, 4)
    s.part("res", 1560, -1010, "name=RLKT value=1e15 footprint=1206 device=resistor m=1", {"p": "top", "m": "0"})
    s.T("COMPARATOR + LATCH", 1760, -1292, 0.45, 4)
    s.part("cmp", 1900, -1000, "name=XDUT", {"inp": "vbl", "inn": "top", "clk": "0", "nbias": "0",
                                             "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("latch", 2300, -1045, "name=XL", {"d": "dout", "clk": "clk", "q": "q", "vdd": "dvdd", "vss": "0"})
    s.part("capa", 2540, -1065, "name=CQ value=%s m=1" % CQ, {"p": "q", "m": "0"})
    s.T(CQ_TXT, 2580, -995, 0.3, 4)
    code = MODELS + """
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include """ + LIB + """
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
.param VDD=%g
.param IBIAS='1.681*1.93077e-6'
.param VIN=%.12g
.param VR_LO=%g
.param VR_HI=2.0
.param LSB=%.12g
.param TCOUNT=50n
.param SLOPE='LSB/TCOUNT'
.param OVR='20*LSB'
.param TS=300n
.param TCONN=310n
.param TR=400n
.param TEDGE=100p
.param TCE=%s
.param TRAMP='(VR_HI+OVR-VR_LO)/SLOPE'
.param TSTOP='TR+(VIN-VR_LO)/SLOPE+300n'
.temp 27
.csparam cs_vdd={VDD}
.csparam cs_tr={TR}
.csparam cs_tcount={TCOUNT}
.options savecurrents reltol=1e-4 gmin=1e-15
.tran 1n {TSTOP} 0 2n
.control
run
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_cross when v(top)=v(vbl) rise=1 td=$&cs_tr
meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr
meas tran t_f90 when v(dout)=$&hi90 fall=1 td=$&cs_tr
meas tran t_f10 when v(dout)=$&lo10 fall=1 td=$&cs_tr
meas tran t_q when v(q)=$&half fall=1 td=$&cs_tr
let delay = t_dout - t_cross
let dout_fall = t_f10 - t_f90
let t_edge = $&cs_tr + $&cs_tcount/2 + floor((t_q - $&cs_tr - $&cs_tcount/2) / $&cs_tcount) * $&cs_tcount
let tcq = t_q - t_edge
let t_k = $&cs_tr + $&cs_tcount/2 + floor((t_cross - $&cs_tr - $&cs_tcount/2) / $&cs_tcount) * $&cs_tcount
let t_kc = t_k - 6e-9
let t_ka = t_k - 2e-9
let t_kb = t_k + 2e-9
meas tran v_kc find v(top) at=$&t_kc
meas tran v_ka find v(top) at=$&t_ka
meas tran v_kb find v(top) at=$&t_kb
let plate_step = (v_kb - v_ka) - (v_ka - v_kc)
set numdgt=10
echo RESULT_BEGIN
print t_cross t_dout t_q delay dout_fall tcq plate_step
echo RESULT_END
quit
.endc""" % (B.VDD, KICK_VIN, B.VR_LO, B.LSB, TCE)
    s.code(1240, -810, "CTL", code)
    s.write(BLOCK / "tb_kick.sch")


if __name__ == "__main__":
    tb_drive()
    tb_aperture()
    tb_kick()
