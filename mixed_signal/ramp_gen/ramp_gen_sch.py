#!/usr/bin/env python3
"""Emit the routed xschem drawing ramp_gen.sch and its symbol ramp_gen.sym.

    ./container.sh 'python3 ramp_gen_sch.py'

Placement and wiring are hand-authored here (sch_lib.py does the geometry);
device sizes are the {RG_*} parameters of data/ramp_gen_params.spice, exactly
as ramp_gen.spice writes them, so a re-sizing never touches the drawing.
Every signal net is a wire; only the bodies, pbias, vrlo and rst are joined by
label. check-schematic.awk (run.sh phase schematic) proves that xschem
netlists the drawing back to ramp_gen.spice device by device, terminal by
terminal, parameter by parameter, ports in order.

Layout (y grows downwards): vdd rail on top, vss rail at the bottom.
  left    the slope current: XPS (pbias slave) -> nd -> XND diode / XNS sink
  middle  the integrator: XCI and XRST from the vramp feedback line down to vx
  right   the OTA: XM7 tail, XM1/XM2 pair, XM3/XM4 mirror, XM6/XM5 second
          stage, XRZ + XCC Miller compensation, XCO on the output
"""
import os

from sch_lib import Sheet, ramp_symbol

BLOCK = os.path.dirname(os.path.abspath(__file__))
s = Sheet()
N, P = "nfet_03v3", "pfet_03v3"

s.T("ramp_gen -- shared single-slope ramp for the 8-bit true bottom-plate cells (.subckt ramp_gen, ramp_gen.spice)\n"
    "MILLER INTEGRATOR: the slope current I_INT = C_INT x SLOPE (0.469 uA into 4.0 pF -> 117.19 mV/us) is pulled out of the\n"
    "virtual ground vx, which the OTA holds at vrlo = 0.5 V. vramp = vx + Q/C_INT rises linearly; the cells hang on the driven\n"
    "output. rst high: XRST shorts XCI, vramp = vx = vrlo. pbias: the ramp's OWN bias_gen (ADR 0012). Sizes: data/ramp_gen_params.spice.",
    40, -1460, 0.32)
s.T("slope current", 220, -1180, 0.4, 13)
s.T("integrator + reset", 640, -1180, 0.4, 13)
s.T("OTA stage 1", 1250, -1180, 0.4, 13)
s.T("stage 2, compensation, output", 1700, -1180, 0.4, 13)
s.T("feedback: vramp -> XCI / XRST -> vx", 980, -1080, 0.25, 4)

for i, (kind, net) in enumerate((("opin", "vramp"), ("ipin", "rst"), ("ipin", "vrlo"), ("ipin", "pbias"),
                                 ("iopin", "vdd"), ("iopin", "vss"))):
    s.port(kind, 40, -900 + 40 * i, net)

# rails
s.W((320, -1100), (1920, -1100)); s.lab(320, -1100, "vdd", right=False)
s.W((320, 0), (2150, 0)); s.lab(320, 0, "vss", right=False)

# ---- slope current
t = s.mos(P, "XPS", 300, -980, "{RG_LPS}", "{RG_WPS}", "{RG_NFPS}")
s.W(t["s"], (320, -1100)); s.lab(*t["g"], "pbias", right=False); s.lab(*t["b"], "vdd")
s.W(t["d"], (320, -150))
t = s.mos(N, "XND", 300, -120, "{RG_LN}", "{RG_KD*RG_WNS}", "{RG_NFND}")
s.W(t["s"], (320, 0)); s.lab(*t["b"], "vss")
s.W(t["g"], (250, -120), (250, -200), (410, -200), (410, -120), (440, -120)); s.J(320, -200)
t = s.mos(N, "XNS", 460, -120, "{RG_LN}", "{RG_WNS}", "1")
s.W(t["s"], (480, 0)); s.lab(*t["b"], "vss")
s.lab(320, -560, "nd")
# vx: the sink's drain to the OTA's inverting input
s.W(t["d"], (480, -600), (1230, -600), (1230, -840), (1280, -840))
s.lab(560, -600, "vx")

# ---- integrator and reset, hung from the feedback line
s.W((700, -1050), (2000, -1050), (2000, -700))
ci = s.mim("XCI", 700, -680, "{RG_CIW}")
s.W(ci[0], (700, -1050)); s.W(ci[1], (700, -600))
t = s.mos(N, "XRST", 1000, -680, "0.28u", "{RG_WRST}", "1")
s.W(t["d"], (1020, -1050)); s.W(t["s"], (1020, -600)); s.lab(*t["b"], "vss")
s.W(t["g"], (930, -680)); s.lab(930, -680, "rst", right=False)

# ---- OTA stage 1
t = s.mos(P, "XM7", 1430, -980, "1u", "{RG_WT}", "{RG_NFT}")
s.W(t["s"], (1450, -1100)); s.lab(*t["g"], "pbias", right=False); s.lab(*t["b"], "vdd")
s.W(t["d"], (1450, -900))
s.W((1320, -900), (1580, -900)); s.lab(1380, -900, "tail")
t = s.mos(P, "XM1", 1300, -840, "{RG_L1}", "{RG_W1}", "{RG_NF1}")
s.W(t["s"], (1320, -900)); s.lab(*t["b"], "vdd"); s.W(t["d"], (1320, -330))
t = s.mos(P, "XM2", 1560, -840, "{RG_L1}", "{RG_W1}", "{RG_NF1}")
s.W(t["s"], (1580, -900)); s.lab(*t["b"], "vdd"); s.W(t["d"], (1580, -330))
s.W(t["g"], (1510, -840)); s.lab(1510, -840, "vrlo", right=False)
s.lab(1320, -640, "d1"); s.lab(1580, -700, "d2")
t = s.mos(N, "XM3", 1300, -300, "{RG_L3}", "{RG_W3}", "1")
s.W(t["s"], (1320, 0)); s.lab(*t["b"], "vss")
s.W(t["g"], (1250, -300), (1250, -380), (1510, -380), (1510, -300), (1540, -300)); s.J(1320, -380)
t = s.mos(N, "XM4", 1560, -300, "{RG_L3}", "{RG_W3}", "1")
s.W(t["s"], (1580, 0)); s.lab(*t["b"], "vss")

# ---- stage 2, compensation, output
t = s.mos(P, "XM6", 1900, -980, "1u", "{RG_W6}", "{RG_NF6}", "{RG_M6}")
s.W(t["s"], (1920, -1100)); s.lab(*t["g"], "pbias", right=False); s.lab(*t["b"], "vdd")
s.W(t["d"], (1920, -330))
t = s.mos(N, "XM5", 1900, -300, "{RG_L5}", "{RG_W5}", "{RG_NF5}")
s.W(t["s"], (1920, 0)); s.lab(*t["b"], "vss")
s.W((1580, -460), (1850, -460), (1850, -300), t["g"])
rz = s.res("XRZ", 1680, -600, "1u", "{RG_RZL}", r=3)          # P (d2) left, M (cz) right
s.W((1580, -600), rz[1]); s.lab(*rz[2], "vss")
cc = s.mim("XCC", 1800, -600, "{RG_CCW}", r=1)                 # cz left, vramp right
s.W(rz[0], cc[1]); s.W(cc[0], (1920, -600)); s.lab(1740, -600, "cz")
s.W((1920, -700), (2300, -700)); s.lab(2300, -700, "vramp")
co = s.mim("XCO", 2150, -400, "{RG_COW}")
s.W(co[0], (2150, -700)); s.W(co[1], (2150, 0))

nseg, njun = s.write(os.path.join(BLOCK, "ramp_gen.sch"))
ramp_symbol(os.path.join(BLOCK, "ramp_gen.sym"),
            "Shared single-slope ramp (ramp_gen.spice, .subckt ramp_gen): Miller integrator, 0.5 V -> 2.117 V at "
            "117.19 mV/us. type=subcircuit: xschem descends into ramp_gen.sch; check-schematic.awk compares it with "
            "the deck. pbias: the ramp's own bias_gen.", "XRG", "integrator")
print("PASS: ramp_gen_sch.py wrote ramp_gen.sch (%d wire segments, %d junctions) and ramp_gen.sym" % (nseg, njun))
