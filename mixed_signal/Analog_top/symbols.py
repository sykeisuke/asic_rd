"""Symbols of Analog_top's sub-blocks, drawn so that a designer reads the
function from the shape (the macro analog_top.sym itself stays a rectangle):

  ramp_simple_d.sym  a sawtooth: the ramp rising from vrlo, the reset edge
  bias_gen_s.sym   a reference current source + R (constant-gm core) and one
                     current-source glyph per output, the arrow giving the
                     direction (sinks in, sources out)
  midref_div.sym     two resistors in series from vdd to vss, the mid tap with
                     its decap, VDD/2 out
  midref_buf.sym     a unity-gain follower triangle (x1), ib as the bias input
  vrlo_ref.sym       a shunt regulator: the 28 : 5 divider tap driving a
                     TL431-style shunt element from vrlo to avss
  latch.sym       a D flip-flop with a falling-edge clock (wedge + bubble)
  comparator_d.sym   a comparator triangle (+ / -)
  sw_s0/1.sym        a transmission gate (bow-tie, complementary gates, bubble
                     on ctlb); sw_s2.sym an NMOS switch blade
  atop_cell.sym      the cell's box with its signal path drawn inside:
                     S/H switch -> C_S -> comparator -> DFF

midref_div, midref_buf, vrlo_ref and latch belong to other blocks. Their
symbols here are LOCAL presentation symbols with the blocks' own names and pin
order: xschemrc puts this folder first on the symbol path, and xschem still
descends into the blocks' own .sch (none exists here), so the netlist is the
blocks' (checked by schematic.sh against their decks). Pin ORDER equals the
blocks' own symbols; pin positions are this file's.

    python3 symbols.py      (analog_top_sch.py and sw_sch.py call it too)
"""
import math
import os
import re

BLOCK = os.path.dirname(os.path.abspath(__file__))
HEAD = "v {xschem version=3.4.8RC file_version=1.2}"
# a local symbol of another block names that block's drawing explicitly: xschem
# otherwise looks for the .sch next to the .sym (this folder) and finds none.
# The bare name is resolved along the xschemrc symbol path.
SCH = "schematic=%s\n"


class Sym:
    def __init__(self, desc, template, extra_k=""):
        self.L = [HEAD, "G {}",
                  'K {type=subcircuit\nformat="@name @pinlist @symname"\n'
                  f'template="name={template}"\ndescription="{desc}"\n{extra_k}}}', "V {}", "S {}", "E {}"]

    def line(self, x1, y1, x2, y2, layer=4, attr=""):
        self.L.append(f"L {layer} {x1} {y1} {x2} {y2} {{{attr}}}")

    def poly(self, pts, layer=4, attr=""):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], layer, attr)

    def circle(self, x, y, r, layer=4, fill=False):
        self.L.append(f"A {layer} {x} {y} {r} 0 360 {{{'fill=true' if fill else ''}}}")

    def text(self, t, x, y, size=0.2, layer=None, hcenter=False):
        a = []
        if layer is not None:
            a.append(f"layer={layer}")
        if hcenter:
            a.append("hcenter=true")
        self.L.append(f"T {{{t}}} {x} {y} 0 0 {size} {size} {{{' '.join(a)}}}")

    def pin(self, name, x, y, d="inout"):
        self.L.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={name} dir={d}}}")

    def zigzag(self, x, y1, y2, amp=8, n=6, layer=4, horizontal=False):
        """A resistor: n half-waves between y1 and y2 at x (or along x at y)."""
        pts = []
        for k in range(n + 1):
            t = y1 + (y2 - y1) * k / n
            off = 0 if k in (0, n) else (amp if k % 2 else -amp)
            pts.append((t, x + off) if horizontal else (x + off, t))
        self.poly([(round(a, 2), round(b, 2)) for a, b in pts], layer)

    def arrow(self, x1, y1, x2, y2, head=5, layer=4):
        self.line(x1, y1, x2, y2, layer)
        a = math.atan2(y2 - y1, x2 - x1)
        for s in (+1, -1):
            self.line(x2, y2, round(x2 - head * math.cos(a + s * 0.5), 2), round(y2 - head * math.sin(a + s * 0.5), 2),
                      layer)

    def isrc(self, x, y, r, direction, layer=4):
        """A current-source glyph: circle with an arrow (direction 'l', 'r', 'u', 'd')."""
        self.circle(x, y, r, layer)
        d = {"l": (r * 0.6, 0, -r * 0.6, 0), "r": (-r * 0.6, 0, r * 0.6, 0),
             "u": (0, r * 0.6, 0, -r * 0.6), "d": (0, -r * 0.6, 0, r * 0.6)}[direction]
        self.arrow(x + d[0], y + d[1], x + d[2], y + d[3], head=max(3, r * 0.45), layer=layer)

    def cap(self, x, y, w=10, gap=6, layer=4, vertical=True):
        """Two plates centred at (x, y), the leads along the axis."""
        if vertical:
            self.line(x - w, y - gap / 2, x + w, y - gap / 2, layer)
            self.line(x - w, y + gap / 2, x + w, y + gap / 2, layer)
        else:
            self.line(x - gap / 2, y - w, x - gap / 2, y + w, layer)
            self.line(x + gap / 2, y - w, x + gap / 2, y + w, layer)

    def write(self, name):
        with open(os.path.join(BLOCK, name + ".sym"), "w", newline="\n") as f:
            f.write("\n".join(self.L) + "\n")


def scale_group(L, n0, k, dx, dy):
    """Scale (by k) and shift every L / A / T line of L from index n0 on."""
    out = L[:n0]
    for ln in L[n0:]:
        if ln.startswith("L "):
            t = ln.split(" ", 6)
            xs = [float(v) for v in t[2:6]]
            ln = "L %s %g %g %g %g %s" % (t[1], round(xs[0] * k + dx, 1), round(xs[1] * k + dy, 1),
                                          round(xs[2] * k + dx, 1), round(xs[3] * k + dy, 1), t[6])
        elif ln.startswith("A "):
            t = ln.split(" ", 7)
            ln = "A %s %g %g %g %s %s %s" % (t[1], round(float(t[2]) * k + dx, 1), round(float(t[3]) * k + dy, 1),
                                             round(float(t[4]) * k, 1), t[5], t[6], t[7])
        elif ln.startswith("T {"):
            m = re.match(r"T \{(.*)\} (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\{.*\})$", ln, re.S)
            if m:
                ln = "T {%s} %g %g %s %s %g %g %s" % (m.group(1), round(float(m.group(2)) * k + dx, 1),
                                                      round(float(m.group(3)) * k + dy, 1), m.group(4), m.group(5),
                                                      round(float(m.group(6)) * k, 3), round(float(m.group(7)) * k, 3),
                                                      m.group(8))
        out.append(ln)
    return out


# ------------------------------------------------------------------- ramp
def ramp_simple_d():
    s = Sym("ramp_simple_d: the shared single-slope ramp, drawn flat with its pbias diode XRD "
            "(ramp_simple_d.sch). PMOS source XPS charges the 4 pF MIM XCR; XRST holds vramp at vrlo "
            "while rst is HIGH. ibias is a CURRENT input (bias_gen_s sinks iramp). "
            "Pins: vramp rst vrlo ibias vdd vss", "XRAMP")
    s.poly([(-100, -100), (100, -100), (100, 100), (-100, 100), (-100, -100)])
    # leads
    s.line(100, 0, 120, 0); s.line(-120, 0, -100, 0); s.line(-120, -60, -100, -60); s.line(-120, 60, -100, 60)
    s.line(0, -120, 0, -100); s.line(0, 100, 0, 120)
    # axes of the waveform
    s.arrow(-56, 70, 88, 70, head=6, layer=8)            # t
    s.arrow(-56, 70, -56, -82, head=6, layer=8)          # V
    s.line(-56, 52, 84, 52, layer=8, attr="dash=3")      # the vrlo level
    s.line(-56, -60, 84, -60, layer=8, attr="dash=3")    # the top of the range
    # the sawtooth: rise (I/C), reset to vrlo, rise again
    s.poly([(-56, 52), (-40, 52), (16, -60), (16, 52), (30, 52), (84, -60)], layer=4, attr="bus=true")
    s.text("V", -76, -92, 0.22, layer=8)
    s.text("t", 82, 72, 0.22, layer=8)
    s.text("vrlo", -54, 54, 0.16, layer=8)
    s.text("dV/dt = I / C", -36, -96, 0.2, layer=13)
    s.text("rst: reset", 20, 54, 0.14, layer=8)
    for name, x, y, d in (("vramp", 120, 0, "out"), ("rst", -120, 0, "in"), ("vrlo", -120, -60, "in"),
                          ("ibias", -120, 60, "in"), ("vdd", 0, -120, "inout"), ("vss", 0, 120, "inout")):
        s.pin(name, x, y, d)
    s.text("vramp", 104, -22, 0.22)
    s.text("rst", -96, -14, 0.2)
    s.text("vrlo", -96, -74, 0.2)
    s.text("ibias", -96, 62, 0.2)
    s.text("vdd", 6, -122, 0.2)
    s.text("vss", 6, 102, 0.2)
    s.text("@name", 104, -130, 0.4)
    s.text("RAMP", -96, 104, 0.24, layer=13)
    s.text("ramp_simple_d", 36, 104, 0.18, layer=13)
    s.write("ramp_simple_d")


# ------------------------------------------------------------ bias generator
CELL_W = 170     # half-width of the atop_cell box (analog_top_sch.py spaces the cells by it)

BG_OUT = ["icmp0", "icmp1", "icmp2", "icmp3", "iramp", "ivref", "ivrlo"]
BG_SINK = {"icmp0", "icmp1", "icmp2", "icmp3", "iramp"}


def bias_gen_s():
    s = Sym("bias_gen_s: constant-gm beta-multiplier bias generator (bias_gen, ADR 0017) without the ivbl source XOB (ADR 0021), plus the "
            "source output ivrlo for vrlo_ref (XOL, ADR 0020); every output is a CURRENT: icmp0..3 and iramp "
            "SINK (arrow into the block), ivref, ivrlo SOURCE (arrow out). xschem descends into "
            "bias_gen_s.sch", "X1")
    s.poly([(-100, -100), (100, -100), (100, 140), (-100, 140), (-100, -100)])
    s.line(0, -120, 0, -100); s.line(0, 140, 0, 160)
    s.pin("vdd", 0, -120); s.pin("vss", 0, 160)
    s.text("vdd", 6, -120, 0.18); s.text("vss", 6, 142, 0.18)
    # the core: a reference current set by R (constant gm)
    s.isrc(-52, -30, 18, "d")
    s.line(-52, -12, -52, 6)
    s.zigzag(-52, 6, 66, amp=9, n=8)
    s.line(-52, 66, -52, 80)
    s.line(-66, 80, -38, 80)                              # ground-like bar (vss)
    s.text("IREF", -92, -62, 0.22, layer=13)
    s.text("R", -84, 26, 0.24, layer=13)
    s.text("const-gm", -94, 92, 0.16, layer=13)
    s.text("I ~ 1/R", -94, 110, 0.16, layer=13)
    # the mirror bus and one current-source glyph per output
    y0, dy = -80, 28
    s.line(4, y0, 4, y0 + dy * (len(BG_OUT) - 1), attr="dash=3")
    s.line(-34, -30, 4, -30, attr="dash=3")               # the reference mirrored onto the bus
    for k, p in enumerate(BG_OUT):
        y = y0 + dy * k
        s.line(4, y, 52, y)
        s.isrc(62, y, 10, "l" if p in BG_SINK else "r")
        s.line(72, y, 100, y)
        s.line(100, y, 120, y)
        s.pin(p, 120, y)
        s.text(p, 10, y - 14, 0.15)
    s.text("sink", 76, -100 + 4, 0.13, layer=8)
    s.text("source", 70, y0 + dy * 5 + 10, 0.13, layer=8)
    s.text("@name", -96, -132, 0.3)
    s.text("BIAS", -96, 144, 0.22, layer=13)
    s.text("bias_gen_s", 30, 144, 0.18, layer=13)
    s.write("bias_gen_s")


# ----------------------------------------------------------- midref divider
def midref_div():
    s = Sym("midref_div of ../midrail_ref (subckt midref_div of midref.spice): two ppolyf_u_3k "
            "resistors in series vdd -> vss, the mid tap vin = VDD/2 with its MIM decap XCT. Local symbol of "
            "Analog_top (pin order as the block's); xschem descends into ../midrail_ref/midref_div.sch", "X1",
            SCH % "midref_div.sch")
    s.line(0, -80, 0, -60)
    s.zigzag(0, -60, -10, amp=9, n=6)
    s.line(0, -10, 0, 10)
    s.circle(0, 0, 2.5, fill=True)
    s.zigzag(0, 10, 60, amp=9, n=6)
    s.line(0, 60, 0, 80)
    s.line(0, 0, 80, 0)                                   # the tap -> vin
    s.line(44, 0, 44, 16)                                 # decap from the tap
    s.cap(44, 19, w=10, gap=6)
    s.line(44, 22, 44, 66)
    s.line(44, 66, 0, 66)
    s.circle(0, 66, 2.5, fill=True)
    s.circle(44, 0, 2.5, fill=True)
    s.pin("vin", 80, 0, "out"); s.pin("vdd", 0, -80); s.pin("vss", 0, 80)
    s.text("VDD/2", 50, -18, 0.2, layer=13)
    s.text("R", 14, -44, 0.2); s.text("R", 14, 26, 0.2)
    s.text("vdd", 6, -84, 0.16); s.text("vss", 6, 70, 0.16)
    s.text("@name", -70, -84, 0.25)
    s.text("midref_div", -70, 84, 0.18, layer=13)
    s.write("midref_div")


# ------------------------------------------------------------ midref buffer
def midref_buf():
    s = Sym("midref_buf of ../midrail_ref (subckt midref_buf of midref.spice): class-AB flipped-voltage "
            "follower: VDD/2 from the divider tap in (vin), the same VDD/2 out with drive (out), drawn as a "
            "unity-gain buffer with its feedback; ib the bias current input. Local symbol of Analog_top (pin "
            "order as the block's); xschem descends into ../midrail_ref/midref_buf.sch", "X1",
            SCH % "midref_buf.sch")
    # op-amp triangle, + = vin (VDD/2 from the tap), - = out (the follower loop)
    s.poly([(-50, -45), (50, 0), (-50, 45), (-50, -45)])
    s.line(-80, 0, -50, 0)                                # vin -> +
    s.text("+", -46, -10, 0.24)
    s.line(-64, -24, -50, -24)                            # the loop into -
    s.text("-", -45, -36, 0.24)
    s.poly([(-64, -24), (-64, -56), (64, -56), (64, 0)], attr="bus=true")
    s.line(50, 0, 80, 0)                                  # out
    s.circle(64, 0, 3, fill=True)
    s.text("x1", -26, -10, 0.3, layer=13)
    # supplies and bias
    s.line(0, -70, 0, -22); s.line(0, 70, 0, 22)
    s.line(-80, 40, -50, 40); s.arrow(-76, 40, -54, 40, head=5)
    s.pin("out", 80, 0, "out"); s.pin("vin", -80, 0, "in"); s.pin("ib", -80, 40, "in")
    s.pin("vdd", 0, -70); s.pin("vss", 0, 70)
    s.text("VDD/2", -110, -20, 0.2, layer=13)
    s.text("VDD/2", 66, -20, 0.2, layer=13)
    s.text("in", -104, 4, 0.16); s.text("out", 66, 4, 0.16)
    s.text("ib", -98, 44, 0.16)
    s.text("vdd", 4, -84, 0.16); s.text("vss", 4, 58, 0.16)
    s.text("@name", -60, -100, 0.25)
    s.text("FVF buffer", -40, 50, 0.16, layer=13)
    s.write("midref_buf")


# ------------------------------------------------------------- vrlo_ref
def vrlo_ref():
    s = Sym("vrlo_ref of ../vrlo_ref (ADR 0018): VR_LO shunt regulator, 28 : 5 ppolyf_u_3k divider tap = 5/33 "
            "AVDD, an OTA driving the NMOS shunt XMS on vrlo, keep-alive source, 3.44 pF decap. ib is a CURRENT "
            "input (bias_gen_s ivrlo). Local symbol of Analog_top (pin order as the block's); xschem "
            "descends into ../vrlo_ref/vrlo_ref.sch", "X1",
            SCH % "vrlo_ref.sch")
    s.poly([(-100, -90), (110, -90), (110, 90), (-100, 90), (-100, -90)], attr="dash=4")
    # divider avdd -> tap -> avss
    s.line(0, -110, 0, -76); s.line(0, -76, -40, -76)
    s.zigzag(-40, -76, -12, amp=8, n=8)
    s.line(-40, -12, -40, 12)
    s.circle(-40, 0, 2.5, fill=True)
    s.zigzag(-40, 12, 60, amp=8, n=6)
    s.line(-40, 60, -40, 76)
    s.line(-40, 76, 40, 76); s.line(0, 76, 0, 110)
    s.circle(0, 76, 2.5, fill=True)
    s.text("28", -32, -52, 0.16); s.text("5", -32, 28, 0.16)
    # shunt element (TL431 style): cathode bar on top (vrlo), anode below (avss), ref from the tap
    s.poly([(28, 14), (52, 14), (40, -6), (28, 14)])
    s.poly([(25, -10), (28, -6), (52, -6), (55, -2)])
    s.line(-40, 0, 34, 0)                                 # ref input from the tap
    s.line(40, -6, 40, -40); s.line(40, -40, 96, -40); s.line(96, -40, 96, 0); s.line(96, 0, 130, 0)
    s.circle(96, 0, 2.5, fill=True)
    s.line(40, 14, 40, 76)
    s.circle(40, 76, 2.5, fill=True)
    s.line(96, 0, 96, 22); s.cap(96, 25, w=9, gap=6); s.line(96, 28, 96, 46); s.line(88, 46, 104, 46)
    # bias current in
    s.line(-130, 50, -96, 50)
    s.isrc(-84, 50, 10, "r")
    s.pin("vrlo", 130, 0, "out"); s.pin("ib", -130, 50, "in"); s.pin("avdd", 0, -110); s.pin("avss", 0, 110)
    s.text("vrlo", 104, -18, 0.18); s.text("ib", -124, 30, 0.18)
    s.text("avdd", 6, -112, 0.16); s.text("avss", 6, 92, 0.16)
    s.text("5/33 VDD", -94, -24, 0.16, layer=13)
    s.text("shunt", 56, 6, 0.16, layer=13)
    s.text("@name", -96, -124, 0.3)
    s.text("VR_LO  vrlo_ref", -96, -86, 0.2, layer=13)
    s.write("vrlo_ref")


# -------------------------------------------------------------- the latch
def latch():
    s = Sym("latch of ../latch (ADR 0019): one gf180mcu_as_sc_mcu7t3v3__dfxtn_2, a D flip-flop clocked "
            "on the FALLING clk edge. Local symbol of Analog_top (pin order as the block's); xschem descends "
            "into ../latch/latch.sch", "x1",
            SCH % "latch.sch")
    s.poly([(-80, -60), (80, -60), (80, 60), (-80, 60), (-80, -60)])
    s.line(-100, -20, -80, -20); s.line(-100, 20, -90, 20); s.line(80, -20, 100, -20)
    s.line(0, -80, 0, -60); s.line(0, 60, 0, 80)
    s.circle(-85, 20, 5)                                  # falling edge: bubble ...
    s.poly([(-80, 8), (-66, 20), (-80, 32)])              # ... on the clock wedge
    s.text("D", -72, -36, 0.4)
    s.text("Q", 54, -36, 0.4)
    s.text("DFF", -26, -8, 0.4, layer=13)
    s.pin("d", -100, -20, "in"); s.pin("clk", -100, 20, "in"); s.pin("q", 100, -20, "out")
    s.pin("vdd", 0, -80); s.pin("vss", 0, 80)
    s.text("clk", -60, 22, 0.18); s.text("vdd", 6, -78, 0.16); s.text("vss", 6, 62, 0.16)
    s.text("@name", -80, -96, 0.3)
    s.text("dfxtn_2", -22, 30, 0.18, layer=13)
    s.write("latch")


# ------------------------------------------------------------- comparator
def comparator_d():
    s = Sym("comparator_d: comparator (10 devices) with its own pbias PMOS diode XREFP, drawn flat in "
            "comparator_d.sch; ibias is a CURRENT input (bias_gen_s sinks icmp_k from it). "
            "Pins: inp inn ibias dout vdd vss. dout falls when inn rises through inp", "XCMP")
    s.poly([(-100, -100), (100, 0), (-100, 100), (-100, -100)])
    s.line(-120, -40, -100, -40); s.line(-120, 40, -100, 40); s.line(100, 0, 120, 0)
    s.line(-40, -120, -40, -70); s.line(20, -120, 20, -40); s.line(20, 40, 20, 120)
    s.arrow(-40, -116, -40, -76, head=6)                  # the bias current into ibias
    for name, x, y, d in (("inp", -120, -40, "in"), ("inn", -120, 40, "in"), ("ibias", -40, -120, "in"),
                          ("dout", 120, 0, "out"), ("vdd", 20, -120, "inout"), ("vss", 20, 120, "inout")):
        s.pin(name, x, y, d)
    s.text("+", -92, -62, 0.6); s.text("-", -90, 18, 0.6)
    s.text("inp", -170, -66, 0.25); s.text("inn", -170, 14, 0.25); s.text("dout", 104, -26, 0.25)
    s.text("ibias", -96, -150, 0.25); s.text("vdd", 26, -122, 0.25); s.text("vss", 26, 98, 0.25)
    s.text("@name", -160, 104, 0.4)
    # the comparator's transfer: dout HIGH while inn < inp, a step down as inn rises through inp
    s.poly([(-70, -30), (-38, -30), (-38, 14), (-6, 14)], attr="bus=true")
    s.line(-70, 26, -2, 26, layer=8)                     # the inn axis under the step
    s.text("inn", -4, 22, 0.14, layer=8)
    s.text("comparator_d", -80, 54, 0.18, layer=13)
    s.write("comparator_d")


# --------------------------------------------------------------- switches
def switch(name, desc, template, tg, sizes):
    """Pins as sw_sch.py's: a (-100, 0), b (100, 0), ctl (-20, -60), ctlb (20, -60), vdd (-20, 60), vss (20, 60)."""
    s = Sym(desc, template)
    s.line(-100, 0, -80, 0); s.line(80, 0, 100, 0)
    s.line(-20, 40, -20, 60); s.line(20, 40, 20, 60)
    if tg:
        # transmission gate: bow-tie, ctl (NMOS gate) plain, ctlb (PMOS gate) with a bubble
        s.line(-80, 0, -30, 0); s.line(30, 0, 80, 0)
        s.poly([(-30, -20), (30, 20), (30, -20), (-30, 20), (-30, -20)])
        s.line(-20, -60, -20, -40); s.line(-20, -40, -5, -40); s.line(-5, -40, -5, -14)
        s.line(20, -60, 20, -40); s.line(20, -40, 6, -40); s.line(6, -40, 6, -26)
        s.circle(6, -21, 5)
        s.text("TG", -12, 22, 0.24, layer=13)
    else:
        # NMOS switch: contacts and an open blade, ctl acting on it (ctlb unused)
        s.line(-80, 0, -30, 0); s.line(30, 0, 80, 0)
        s.circle(-30, 0, 3, fill=True); s.circle(30, 0, 3, fill=True)
        s.line(-30, 0, 22, -20)
        s.line(-20, -60, -20, -40); s.line(-20, -40, 0, -40); s.line(0, -40, 0, -12, attr="dash=3")
        s.line(20, -60, 20, -46)
        s.text("n.c.", 24, -54, 0.14, layer=8)
        s.text("NMOS", -16, 14, 0.2, layer=13)
    s.text("vdd vss: body", -40, 42, 0.13, layer=8)
    for pn, (x, y, d) in (("a", (-100, 0, "inout")), ("b", (100, 0, "inout")), ("ctl", (-20, -60, "in")),
                          ("ctlb", (20, -60, "in")), ("vdd", (-20, 60, "inout")), ("vss", (20, 60, "inout"))):
        s.pin(pn, x, y, d)
    s.text("a", -94, -16, 0.2); s.text("b", 86, -16, 0.2)
    s.text("ctl", -50, -66, 0.18); s.text("ctlb", 26, -66, 0.18)
    s.text("@name", -78, -84, 0.3)
    s.text(f"@symname  {sizes}", -76, 62, 0.15, layer=13)
    s.write(name)


# ------------------------------------------------------------------- cell
def atop_cell(ports, left, right, top, bottom):
    """The cell's box (pins as before), its signal path drawn inside."""
    w, pitch = CELL_W, 40
    h = max(pitch * (max(len(left), len(right)) + 1), 120) // 2
    s = Sym("atop_cell: one sampling / conversion cell of analog_top: S0/S2 sample vfe onto C_S (54.52 fF "
            "MIM), S1 puts vramp on the top plate, comparator_d compares the floating bot plate with vbl, the "
            "std-cell DFF latch captures dout on the falling clk; xschem descends into atop_cell.sch", "X1")
    s.poly([(-w, -h), (w, -h), (w, h), (-w, h), (-w, -h)])
    pos = {}
    for k, p in enumerate(left):
        pos[p] = (-w - 20, -h + pitch * (k + 1), "L")
    for k, p in enumerate(right):
        pos[p] = (w + 20, -h + pitch * (k + 1), "R")
    for k, p in enumerate(top):
        pos[p] = (-w // 2 + k * w, -h - 20, "T")
    for k, p in enumerate(bottom):
        pos[p] = (-w // 2 + k * w, h + 20, "B")
    for p in ports:
        x, y, side = pos[p]
        if side == "L":
            s.line(x, y, -w, y); s.text(p, -w + 6, y - 10, 0.22)
        elif side == "R":
            s.line(w, y, x, y); s.L.append(f"T {{{p}}} {w - 6} {y - 10} 0 1 0.22 0.22 {{}}")
        elif side == "T":
            s.line(x, y, x, -h); s.text(p, x + 4, -h + 4, 0.22)
        else:
            s.line(x, y, x, h); s.text(p, x + 4, h - 26, 0.22)
        s.pin(p, x, y)
    # the cell, ideal and TRUE BOTTOM-PLATE: S0 (vin) and S1 (vramp) drive the TOP
    # plate of C_S; S2 ties the BOTTOM plate to vref and opens FIRST (that edge is
    # the sample); the floating bottom plate is the comparator's - input, vbl its +;
    # the comparator feeds the DFF (falling-edge clock).
    def sw(x1, x2, y, lab, lx, ly):
        s.circle(x1, y, 2.5, fill=True); s.circle(x2, y, 2.5, fill=True)
        s.line(x1, y, x2 - 3, y - 11)
        s.text(lab, lx, ly, 0.15, layer=13)
    n0 = len(s.L)
    X, TP, BP = -14, -66, -56                             # plate column, top / bottom plate
    s.text("TRUE BOTTOM-PLATE S/H", -84, -150, 0.17, layer=13)
    # S1: vramp -> top (with a small ramp)
    s.poly([(-84, -98), (-76, -98), (-68, -112)], layer=8)
    s.line(-66, -106, -56, -106); sw(-56, -36, -106, "S1", -50, -128)
    s.line(-36, -106, X, -106); s.line(X, -106, X, -86)
    # S0: vin -> top
    s.text("vin", -84, -94, 0.14, layer=8)
    s.line(-66, -86, -56, -86); sw(-56, -36, -86, "S0", -52, -99)
    s.line(-36, -86, X, -86); s.line(X, -86, X, TP)
    s.circle(X, -86, 2.5, fill=True)
    # C_S: top plate above, bottom plate below
    s.line(X - 16, TP, X + 16, TP); s.line(X - 16, BP, X + 16, BP)
    s.text("top", X - 36, TP - 12, 0.13, layer=8); s.text("bot", X - 36, BP, 0.13, layer=8)
    s.text("C_S", X + 20, TP - 2, 0.15, layer=13)
    # bottom plate: down to the S2 node and on to the comparator's - input
    s.line(X, BP, X, -26)
    s.circle(X, -26, 2.5, fill=True)
    # S2: bottom plate -> vref, the SAMPLING switch (opens first)
    s.line(X, -26, -36, -26); sw(-36, -56, -26, "S2", -54, -50)
    s.line(-56, -26, -66, -26)
    s.text("vref", -84, -34, 0.14, layer=8)
    s.text("opens first", -86, -16, 0.13, layer=4)
    s.text("= SAMPLE", -86, -4, 0.13, layer=4)
    # comparator: - = bottom plate, + = vbl; a step inside
    CX, CY = 30, -36
    s.line(X, -26, CX, -26)
    s.line(CX - 14, -46, CX, -46); s.text("vbl", CX - 24, -58, 0.13, layer=8)
    s.poly([(CX, CY - 24), (CX + 44, CY), (CX, CY + 24), (CX, CY - 24)])
    s.text("+", CX + 2, -56, 0.15); s.text("-", CX + 2, -34, 0.15)
    s.poly([(CX + 10, CY - 6), (CX + 18, CY - 6), (CX + 18, CY + 6), (CX + 26, CY + 6)])
    # DFF, falling-edge clock
    s.line(CX + 44, CY, 84, CY)
    s.poly([(84, CY - 20), (122, CY - 20), (122, CY + 22), (84, CY + 22), (84, CY - 20)])
    s.poly([(84, CY + 6), (92, CY + 12), (84, CY + 18)]); s.circle(80, CY + 12, 4)
    s.text("D", 87, CY - 18, 0.14); s.text("Q", 110, CY - 18, 0.14)
    s.line(122, CY - 8, 128, CY - 8)
    s.text("CMP -> DFF", 46, CY + 26, 0.13, layer=13)
    # drawn at unit scale (x -86..128, y -150..-4): fill the box
    s.L = scale_group(s.L, n0, 1.3, 0, 100)
    s.text("@name", -w + 6, -h - 34, 0.3)
    s.text("UNIT CELL  atop_cell", -w + 50, h - 40, 0.22, layer=13)
    s.write("atop_cell")


def write_all(ports=None):
    ramp_simple_d()
    bias_gen_s()
    midref_div()
    midref_buf()
    vrlo_ref()
    latch()
    comparator_d()


if __name__ == "__main__":
    write_all()
