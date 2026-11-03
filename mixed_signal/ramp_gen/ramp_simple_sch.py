#!/usr/bin/env python3
"""Emit the routed xschem drawing ramp_simple.sch and its symbol ramp_simple.sym
(the comparison baseline: current source + capacitor + reset switch).

    ./container.sh 'python3 ramp_simple_sch.py'

Sizes are the {RS_*} parameters of data/ramp_simple_params.spice
(size_simple.py). check-schematic.awk -v sub=ramp_simple proves the drawing
netlists back to ramp_simple.spice. The symbol is pin-compatible with
ramp_gen.sym, so the four-cell testbench takes either.

The text is a one-line title, the role headings, the slope current and the
capacitor value (CLAUDE.md, "Schematic drawings"); the two numbers are the
ones size_simple.py recorded in data/sizing_simple.json.
../Analog_top/analog_top_sch.py copies them onto ramp_simple_d.sch.
"""
import json
import os

from sch_lib import Sheet, ramp_symbol

BLOCK = os.path.dirname(os.path.abspath(__file__))
SZ = json.load(open(os.path.join(BLOCK, "data", "sizing_simple.json")))
PD = SZ["predicted"]
C_PF = PD["c"] * 1e12                            # PDK model value (size_simple.py, AC at 1 kHz)


s = Sheet()
s.T("RAMP_SIMPLE  -  PMOS current source + %.2f pF MIM + reset switch" % C_PF, 20, -760, 0.7)
for i, (kind, net) in enumerate((("opin", "vramp"), ("ipin", "rst"), ("ipin", "vrlo"), ("ipin", "pbias"),
                                 ("iopin", "vdd"), ("iopin", "vss"))):
    s.port(kind, 20, -480 + 40 * i, net)
s.W((320, -560), (480, -560)); s.lab(480, -560, "vdd")
t = s.mos("pfet_03v3", "XPS", 300, -440, "{RS_LPS}", "{RS_WPS}", "{RS_NFPS}")
s.W(t["s"], (320, -560)); s.lab(*t["g"], "pbias", right=False); s.lab(*t["b"], "vdd")
s.W(t["d"], (320, -300), (900, -300)); s.lab(900, -300, "vramp")
cr = s.mim("XCR", 460, -180, "{RS_CW}")
s.W(cr[0], (460, -300)); s.W(cr[1], (460, 0)); s.lab(460, 0, "vss")
t = s.mos("nfet_03v3", "XRST", 700, -180, "0.28u", "{RS_WRST}", "1")
s.W(t["d"], (720, -300)); s.lab(*t["b"], "vss")
s.W(t["s"], (720, -60)); s.lab(720, -60, "vrlo")
s.W(t["g"], (640, -180)); s.lab(640, -180, "rst", right=False)
s.T("current source", 220, -640, 0.45, 13)
s.T("integrating capacitor", 380, -380, 0.35, 13)
s.T("reset to vrlo", 680, -380, 0.35, 13)

# value tags next to the devices
s.T("%.3f uA" % (PD["i_op_mid"] * 1e6), 340, -545, 0.35, 4)
s.T("C = %.2f pF" % C_PF, 480, -140, 0.45, 4)

nseg, njun = s.write(os.path.join(BLOCK, "ramp_simple.sch"))
ramp_symbol(os.path.join(BLOCK, "ramp_simple.sym"),
            "Simple Wilkinson ramp (ramp_simple.spice): PMOS current source + 4 pF MIM + reset switch, the comparison "
            "baseline for ramp_gen. type=subcircuit: xschem descends into ramp_simple.sch.", "XRG", "I + C")
print("PASS: ramp_simple_sch.py wrote ramp_simple.sch (%d wire segments, %d junctions) and ramp_simple.sym" % (nseg, njun))
