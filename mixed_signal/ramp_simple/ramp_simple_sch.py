#!/usr/bin/env python3
"""Emit the xschem drawings of the ramp block from the controlled netlist and
the sizing record: ramp_simple.sch (the cell: capacitor + reset switch), its
symbol ramp_simple.sym, and tb_ramp.sch (the ramp alone on an ideal current,
the `level` case of tb_ramp.py: ideal VR_LO at the pre-roll level, 4 cells of
load, the S1 charge at TCONN).

    ./container.sh 'python3 ramp_simple_sch.py'

The cell drawing netlists back to ramp_simple.spice device for device
(check-schematic.awk); the testbench drawing is checked for the cell, the
current source and the three voltage sources. Text per root CLAUDE.md
("Schematic drawings"): a title, one `layout:` line, headings, values.
"""
import json
import os

import sch_lib
from sch_lib import Sheet

BLOCK = os.path.dirname(os.path.abspath(__file__))
SZ = json.load(open(os.path.join(BLOCK, "data", "sizing.json")))
PD, GRID = SZ["predicted"], SZ["grid"]
PORTS = ["vramp", "rst", "vrlo", "vss"]


def devices():
    out = {}
    for line in open(os.path.join(BLOCK, "ramp_simple.spice")):
        if not line.startswith("X"):
            continue
        t = line.split()
        name, rest = t[0], t[1:]
        i = next(j for j, s in enumerate(rest) if "=" in s)
        out[name] = (rest[i - 1], rest[:i - 1], dict(s.split("=", 1) for s in rest[i:]))
    return out


D = devices()


def source(s, sym, name, x, y, value, rot=0):
    """vsource / isource / capa: pins p (0,-30) and m (0,30); returns (p, m)."""
    s.inst.append('C {devices/%s.sym} %d %d %d 0 {name=%s value="%s" savecurrent=false}' % (sym, x, y, rot, name, value))
    a, b = Sheet.rot(0, -30, rot), Sheet.rot(0, 30, rot)
    p = ((x + a[0], y + a[1]), (x + b[0], y + b[1]))
    s.pins += list(p)
    return p


# =========================================================== the cell
s = Sheet()
s.T("RAMP_SIMPLE  -  ramp capacitor + reset switch to VR_LO; the current from the I/C source", 60, -500, 0.7)
s.T("layout: MIM (M4-M5) beside the cells' vramp bus, the reset switch at the vrlo end", 60, -460, 0.35)
# the vramp rail: the reset switch at the vrlo end (left), the capacitor array to the right
s.W((300, -300), (1300, -300))
s.port("opin", 1300, -300, "vramp")
s.W((300, -40), (1300, -40))
s.port("iopin", 1300, -40, "vss")
# the reset switch, vramp -> vrlo, gate rst, body wired to the vss rail
m, _, p = D["XRST"]
t = s.mos(m, "XRST", 480, -180, p["L"], p["W"], p["nf"], p.get("m", "1"))
s.W(t["d"], (500, -300))
s.W(t["s"], (500, -120), (300, -120))
s.port("ipin", 300, -120, "vrlo")
s.W(t["g"], (300, -180))
s.port("ipin", 300, -180, "rst")
s.W(t["b"], (640, -180), (640, -40))
s.J(640, -40)
s.T("reset to VR_LO", 400, -370, 0.45, 13)
# the capacitor array, vramp -> vss (the PDK symbol annotates to its right; the value beyond it)
m, _, p = D["XCR"]
top, bot = s.mim("XCR", 880, -180, p["c_width"])
s.inst[-1] = s.inst[-1].replace("m=1}", "m=%s}" % p.get("m", "1"))      # the unit array
s.W(top, (880, -300))
s.W(bot, (880, -40))
s.T("C = %d x %.2f fF = %.2f pF" % (int(p.get("m", "1")), PD["c_unit_ff"], PD["c_ramp_pf"]), 1000, -110, 0.45, 4)
s.T("ramp capacitor", 800, -370, 0.45, 13)
s.T("I = %.3f uA" % PD["i_ramp_ua"], 1080, -340, 0.45, 4)
nseg, njun = s.write(os.path.join(BLOCK, "ramp_simple.sch"))


# =========================================================== the symbol
def symbol(path):
    hdr = "v {xschem version=3.4.8RC file_version=1.2}\nG {}"
    sym = [hdr, 'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=XRG"\n'
           'description="The ramp capacitor and its reset switch (ramp_simple.spice); the ramp current enters at '
           'vramp from the I/C source. Pins in the subcircuit order: %s."\n}' % " ".join(PORTS),
           "V {}", "S {}", "E {}"]
    for x1, y1, x2, y2 in ((-120, -100, 120, -100), (120, -100, 120, 100), (120, 100, -120, 100), (-120, 100, -120, -100)):
        sym.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))
    # a capacitor glyph and a ramp
    for line in ("L 7 -20 -40 -20 10 {}", "L 7 -40 10 0 10 {}", "L 7 -40 25 0 25 {}", "L 7 -20 25 -20 60 {}",
                 "L 7 30 50 90 -40 {}", "L 7 90 -40 90 50 {}"):
        sym.append(line)
    sym.append("L 4 120 -40 140 -40 {}")
    sym.append("B 5 137.5 -42.5 142.5 -37.5 {name=vramp dir=out}")
    for pin, y in (("rst", -40), ("vrlo", 40)):
        sym.append("L 4 -140 %d -120 %d {}" % (y, y))
        sym.append("B 5 -142.5 %.1f -137.5 %.1f {name=%s dir=in}" % (y - 2.5, y + 2.5, pin))
    sym.append("L 4 0 100 0 120 {}")
    sym.append("B 5 -2.5 117.5 2.5 122.5 {name=vss dir=inout}")
    sym.append("T {vramp} 60 -46 0 0 0.2 0.2 {}")
    sym.append("T {rst} -114 -46 0 0 0.2 0.2 {}")
    sym.append("T {vrlo} -114 34 0 0 0.2 0.2 {}")
    sym.append("T {vss} 6 104 0 0 0.2 0.2 {}")
    sym.append("T {@name} -120 -116 0 0 0.3 0.3 {}")
    sym.append("T {C + reset} -112 70 0 0 0.22 0.22 {layer=13}")
    open(path, "w").write("\n".join(sym) + "\n")


symbol(os.path.join(BLOCK, "ramp_simple.sym"))


# =========================================================== the testbench (the `level` case)
import tb_ramp  # noqa: E402
import rs_common as rs  # noqa: E402

tconn, tr, te, trst2, tstop = tb_ramp.timeline()
i_ramp = PD["i_ramp_ua"] * 1e-6
qkick = rs.NCELL * rs.C_EQ_S1 * (2.0 - rs.VR_LO_TAP)
cl = rs.NCELL * rs.C_CELL + 1e-15
b = Sheet()
b.T("TB_RAMP  -  the ramp alone: ideal %.3f uA into the cell, 4 cells of load, S1 charge at TCONN, VR_LO %.4f V"
    % (i_ramp * 1e6, rs.VR_LO_TAP), 60, -760, 0.7)
# supply and the ideal ramp current
p, mm = source(b, "vsource", "VDD_SOURCE", 200, -520, "PWL(0 0 %.4g %g %.6g %g)" % (tb_ramp.TPWR, rs.VDD, tstop, rs.VDD))
b.W(p, (200, -600)); b.lab(200, -600, "vdd")
b.W(mm, (200, -440)); b.lab(200, -440, "0")
b.T("supply", 140, -640, 0.45, 13)
p, mm = source(b, "isource", "IRAMP", 760, -520, "PWL(0 0 %.4g %.6g)" % (tb_ramp.TPWR, i_ramp))
b.W(p, (760, -600)); b.lab(760, -600, "vdd")
b.W(mm, (760, -400)); b.lab(760, -400, "vramp")
b.T("ramp current (the I/C source's place)", 640, -640, 0.45, 13)
b.T("%.3f uA" % (i_ramp * 1e6), 800, -470, 0.35, 4)
# rst pulse and VR_LO (left column)
p, mm = source(b, "vsource", "VRST", 400, -300,
               "PWL(0 0 %.4g %g %.9g %g %.9g 0 %.9g 0 %.9g %g)" % (tb_ramp.TPWR, rs.VDD, tr, rs.VDD, tr + 100e-12, trst2, trst2 + 100e-12, rs.VDD))
b.W(p, (400, -380)); b.lab(400, -380, "rst")
b.W(mm, (400, -220)); b.lab(400, -220, "0")
b.T("reset", 360, -420, 0.45, 13)
p, mm = source(b, "vsource", "VRLO", 400, -60, "%.6f" % rs.VR_LO_TAP)
b.W(p, (400, -140)); b.lab(400, -140, "vrlo")
b.W(mm, (400, 20)); b.lab(400, 20, "0")
b.T("VR_LO (pre-roll level)", 320, -180, 0.45, 13)
# the cell, its inputs by net labels, its output on a vramp rail to the loads
b.inst.append("C {ramp_simple.sym} 1060 -300 0 0 {name=XRG}")
b.pins += [(1200, -340), (920, -340), (920, -260), (1060, -180)]
b.W((920, -340), (860, -340)); b.lab(860, -340, "rst", right=False)
b.W((920, -260), (860, -260)); b.lab(860, -260, "vrlo", right=False)
b.W((1060, -180), (1060, -120)); b.lab(1060, -120, "0")
b.W((1200, -340), (1900, -340))
b.lab(1260, -340, "vramp")
b.J(1260, -340)
# the cells' load and S1 charge on vramp
p, mm = source(b, "capa", "CL", 1480, -220, "%.6g" % cl)
b.W(p, (1480, -340)); b.J(1480, -340)
b.W(mm, (1480, -120)); b.lab(1480, -120, "0")
b.T("C_L = 4 x %.0f fF" % (rs.C_CELL * 1e15), 1320, -200, 0.35, 4)
p, mm = source(b, "isource", "IKICK", 1900, -220, "PULSE(0 %.6g %.9g 100p 100p 0.9n 1)" % (qkick / 1e-9, tconn), rot=2)
b.W(p, (1900, -340))
b.W(mm, (1900, -120)); b.lab(1900, -120, "0")
b.T("S1 charge", 1860, -100, 0.35, 4)
b.T("cells: load and S1 charge", 1460, -420, 0.45, 13)
b.inst.append('C {devices/code_shown.sym} 1000 60 0 0 {name=MODELS only_toplevel=false value="'
              + rs.head().strip().replace("{", "\\{").replace("}", "\\}") + '"}')
nseg2, njun2 = b.write(os.path.join(BLOCK, "tb_ramp.sch"))
print("PASS: ramp_simple_sch.py wrote ramp_simple.sch (%d devices, %d wire segments), ramp_simple.sym and tb_ramp.sch (%d segments)"
      % (len(D), nseg, nseg2))
