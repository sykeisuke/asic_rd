"""Draw sample_seq's xschem views from the deck's structure and data/sizing.json.

    python3 sample_seq_sch.py

Writes sample_seq.sch / .sym (the sequencer: shift register + four clock
generators), seq_clkgen.sch / .sym (one cell's EE628 non-overlapping clock
generator, ADR 0029), seq_dly.sch / .sym (one delay stage, N x inv_2, ADR 0031) and
the library primitive symbols. tb_seq has no drawing (the bench is the deck).
Every sheet text is in this file. The schematic phase netlists sample_seq.sch
with xschem and check_sch.py compares it with sample_seq.spice subcircuit by
subcircuit.
"""
import json
import os

from sch_lib import Sheet
from seq_common import BLOCK, LIB, NCELLS

HDR = "v {xschem version=3.4.8RC file_version=1.2}\nG {}"
with open(os.path.join(BLOCK, "data", "sizing.json")) as h:
    N = int(json.load(h)["n_stage"])

# library cells: subcircuit pin order (the format line) and the drawn pins
STD = {
    "dfxtp_2": (["VDD", "VNW", "VPW", "VSS", "CLK", "D", "Q"], ["D", "CLK"], ["Q"], "DFF"),
    "inv_2": (["VDD", "VNW", "VPW", "VSS", "Y", "A"], ["A"], ["Y"], "INV"),
}
# seq_clkgen is drawn with gate-shaped symbols (seq_g_*.sym, below), not boxes


def box_symbol(path, kind, fmt, template, left, right, top, bottom, label, dirs=None):
    """a rectangle with pins: left / right at x -/+ 100, top / bottom at y -/+ (h/2 + 20)"""
    dirs = dirs or {}
    n = max(len(left), len(right), 1)
    hh = 20 * n + 20
    s = [HDR, 'K {type=%s\nformat="%s"\ntemplate="name=%s"\n}' % (kind, fmt, template), "V {}", "S {}", "E {}"]
    for x1, y1, x2, y2 in ((-80, -hh, 80, -hh), (80, -hh, 80, hh), (80, hh, -80, hh), (-80, hh, -80, -hh)):
        s.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))

    def ys(k):
        return [-20 * (k - 1) + 40 * i for i in range(k)]
    for p, y in zip(left, ys(len(left))):
        s.append("L 4 -100 %d -80 %d {}" % (y, y))
        s.append("B 5 -102.5 %.1f -97.5 %.1f {name=%s dir=%s}" % (y - 2.5, y + 2.5, p, dirs.get(p, "in")))
        s.append("T {%s} -74 %d 0 0 0.28 0.28 {}" % (p, y - 8))
    for p, y in zip(right, ys(len(right))):
        s.append("L 4 80 %d 100 %d {}" % (y, y))
        s.append("B 5 97.5 %.1f 102.5 %.1f {name=%s dir=%s}" % (y - 2.5, y + 2.5, p, dirs.get(p, "out")))
        s.append("T {%s} 74 %d 0 1 0.28 0.28 {}" % (p, y - 8))
    for row, yy, sign in ((top, -hh, -1), (bottom, hh, 1)):
        xs = [-20 * (len(row) - 1) + 40 * i for i in range(len(row))]
        for p, x in zip(row, xs):
            s.append("L 4 %d %d %d %d {}" % (x, yy, x, yy + 20 * sign))
            s.append("B 5 %.1f %.1f %.1f %.1f {name=%s dir=inout}" % (x - 2.5, yy + 20 * sign - 2.5, x + 2.5,
                                                                       yy + 20 * sign + 2.5, p))
    s.append("T {@name} -80 %d 0 0 0.3 0.3 {}" % (-hh - 46))
    s.append("T {%s} -50 %d 0 0 0.3 0.3 {layer=13}" % (label, hh - 34))
    with open(path, "w") as h:
        h.write("\n".join(s) + "\n")
    return hh


# inv_2 also ships with ../ic_source (its drawing places it), and both folders
# are on ../Analog_top's symbol path: the symbol written here must be that one,
# byte for byte, or xschem picks one and the other sheet's pins float
INV2_PINS = {"A": (-80, 0), "Y": (80, 0), "VDD": (-20, -60), "VNW": (20, -60), "VSS": (-20, 60), "VPW": (20, 60)}
INV2_TEXT = """v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=primitive
format="@name @@VDD @@VNW @@VPW @@VSS @@Y @@A @symname"
template="name=X1"
}
V {}
S {}
E {}
L 4 -60 -40 60 -40 {}
L 4 60 -40 60 40 {}
L 4 60 40 -60 40 {}
L 4 -60 40 -60 -40 {}
L 4 -80 0 -60 0 {}
B 5 -82.5 -2.5 -77.5 2.5 {name=A dir=in}
T {A} -54 -6 0 0 0.25 0.25 {}
L 4 60 0 80 0 {}
B 5 77.5 -2.5 82.5 2.5 {name=Y dir=out}
T {Y} 44 -6 0 0 0.25 0.25 {}
L 4 -20 -60 -20 -40 {}
B 5 -22.5 -62.5 -17.5 -57.5 {name=VDD dir=inout}
L 4 20 -60 20 -40 {}
B 5 17.5 -62.5 22.5 -57.5 {name=VNW dir=inout}
L 4 -20 60 -20 40 {}
B 5 -22.5 57.5 -17.5 62.5 {name=VSS dir=inout}
L 4 20 60 20 40 {}
B 5 17.5 57.5 22.5 62.5 {name=VPW dir=inout}
T {@name} -60 -58 0 0 0.3 0.3 {}
T {INV} -40 -8 0 0 0.3 0.3 {layer=13}
"""


def std_geom(cell):
    if cell == "inv_2":
        return dict(INV2_PINS)
    order, left, right, _ = STD[cell]
    n = max(len(left), len(right), 1)
    hh = 20 * n + 20
    pins = {}
    for p, y in zip(left, [-20 * (len(left) - 1) + 40 * i for i in range(len(left))]):
        pins[p] = (-100, y)
    for p, y in zip(right, [-20 * (len(right) - 1) + 40 * i for i in range(len(right))]):
        pins[p] = (100, y)
    for p, x in zip(["VDD", "VNW"], (-20, 20)):
        pins[p] = (x, -hh - 20)
    for p, x in zip(["VSS", "VPW"], (-20, 20)):
        pins[p] = (x, hh + 20)
    return pins


for cell, (order, left, right, label) in STD.items():
    if cell == "inv_2":
        with open(os.path.join(BLOCK, "%s__%s.sym" % (LIB, cell)), "w") as h:
            h.write(INV2_TEXT)
        continue
    box_symbol(os.path.join(BLOCK, "%s__%s.sym" % (LIB, cell)), "primitive",
               "@name " + " ".join("@@" + p for p in order) + " @symname", "X1", left, right,
               ["VDD", "VNW"], ["VSS", "VPW"], label)


def gate_symbol(cell, b_top=False):
    """a gate-shaped symbol of one library cell (EE628 template look): inverter
    triangle + bubble, A at (-80, 0), Y at (80, 0); nand2 D-shape + bubble, A at
    (-80, -20) and B at (-80, 20) (swapped when b_top), Y at (80, 0). The four
    supply pins are not drawn: the format writes the instance attributes VDD /
    VSS (default vdd / vss, the seq_clkgen ports) on VDD VNW and VPW VSS, so the
    netlist line is the library cell's, pin for pin."""
    nand = cell.startswith("nand")
    name = "seq_g_%s%s" % (cell, "_ba" if b_top else "")
    fmt = "@name @VDD @VDD @VSS @VSS @@Y %s %s__%s" % ("@@B @@A" if nand else "@@A", LIB, cell)
    s = [HDR, 'K {type=primitive\nformat="%s"\ntemplate="name=X1 VDD=vdd VSS=vss"\n}' % fmt, "V {}", "S {}", "E {}"]
    if nand:
        ya, yb = (20, -20) if b_top else (-20, 20)
        s += ["L 4 -80 -20 -40 -20 {}", "L 4 -80 20 -40 20 {}",
              "L 4 -40 -35 -40 35 {}", "L 4 -40 -35 -5 -35 {}", "L 4 -40 35 -5 35 {}",
              "A 4 -5 0 35 270 180 {}", "A 4 37.5 0 7.5 0 360 {}", "L 4 45 0 80 0 {}",
              "B 5 -82.5 %.1f -77.5 %.1f {name=A dir=in}" % (ya - 2.5, ya + 2.5),
              "B 5 -82.5 %.1f -77.5 %.1f {name=B dir=in}" % (yb - 2.5, yb + 2.5),
              "B 5 77.5 -2.5 82.5 2.5 {name=Y dir=out}",
              "T {A} -36 %d 0 0 0.28 0.28 {}" % (ya - 9), "T {B} -36 %d 0 0 0.28 0.28 {}" % (yb - 9),
              "T {@name} -40 42 0 0 0.3 0.3 {}", "T {%s} -40 -64 0 0 0.3 0.3 {layer=13}" % cell]
    else:
        s += ["L 4 -80 0 -40 0 {}", "L 4 -40 -30 -40 30 {}", "L 4 -40 -30 20 0 {}", "L 4 -40 30 20 0 {}",
              "A 4 27.5 0 7.5 0 360 {}", "L 4 35 0 80 0 {}",
              "B 5 -82.5 -2.5 -77.5 2.5 {name=A dir=in}", "B 5 77.5 -2.5 82.5 2.5 {name=Y dir=out}",
              "T {@name} -40 36 0 0 0.3 0.3 {}", "T {%s} -40 -58 0 0 0.3 0.3 {layer=13}" % cell]
    with open(os.path.join(BLOCK, name + ".sym"), "w") as h:
        h.write("\n".join(s) + "\n")
    return name


GSYM = {c: gate_symbol(c) for c in ("inv_2", "inv_4", "inv_8", "nand2_2")}
# xschem's devices/lab_wire.sym with the text at 0.30 (its own is 0.27, under the sheet minimum)
with open(os.path.join(BLOCK, "seq_lab_wire.sym"), "w") as h:
    h.write(HDR + '\nK {type=label\nformat="*.alias @lab"\ntemplate="name=p1 sig_type=std_logic lab=xxx"\n}\n'
            "V {}\nS {}\nE {}\nB 5 -1.25 -1.25 1.25 1.25 {name=p dir=in}\n"
            "T {@lab} -2.5 -1.25 2 0 0.3 0.3 {}\n")
GSYM["nand2_2_ba"] = gate_symbol("nand2_2", b_top=True)


class Seq(Sheet):
    def gate(self, cell, name, x, y, nets, b_top=False):
        """a gate-shaped cell at (x, y); returns its pin coordinates (wired by the caller)"""
        self.inst.append("C {%s.sym} %d %d 0 0 {name=%s VDD=vdd VSS=vss}"
                         % (GSYM[cell + ("_ba" if b_top else "")], x, y, name))
        if cell.startswith("nand"):
            ya, yb = (20, -20) if b_top else (-20, 20)
            pins = {"A": (x - 80, y + ya), "B": (x - 80, y + yb), "Y": (x + 80, y)}
        else:
            pins = {"A": (x - 80, y), "Y": (x + 80, y)}
        self.pins += list(pins.values())
        return pins

    def labw(self, x, y, net):
        """net name written on a wire, ending at (x, y)"""
        self.n += 1
        self.pins.append((x, y))
        self.inst.append("C {seq_lab_wire.sym} %d %d 0 0 {name=l%d sig_type=std_logic lab=%s}"
                         % (x, y, self.n, net))

    def port1(self, kind, x, y, net, num):
        self.inst.append("C {devices/%s.sym} %d %d 0 0 {name=p_%s lab=%s sim_pinnumber=%d}"
                         % (kind, x, y, net, net, num))

    def diag(self, a, b):
        """a diagonal wire (the cross-coupling X); it meets nothing but its own ends"""
        self.wires.append((a[0], a[1], b[0], b[1]))

    def std(self, cell, name, x, y, nets):
        """a library cell at (x, y); every pin labelled with its net (supplies vdd / vss)"""
        self.inst.append("C {%s__%s.sym} %d %d 0 0 {name=%s}" % (LIB, cell, x, y, name))
        nets = dict(nets, VDD="vdd", VNW="vdd", VSS="vss", VPW="vss")
        for p, (px, py) in std_geom(cell).items():
            if cell == "inv_2" and p in ("VDD", "VNW"):
                # inv_2's own @name sits beside these pins: label them on a stub above
                self.W((x + px, y + py), (x + px, y + py - 30))
                py -= 30
            self.lab(x + px, y + py, nets[p], right=px > 0)

    def sub(self, sym, name, x, y, pins, nets):
        self.inst.append("C {%s.sym} %d %d 0 0 {name=%s}" % (sym, x, y, name))
        for p, (px, py) in pins.items():
            self.lab(x + px, y + py, nets[p], right=px > 0)

    def ports(self, x, y, plist):
        for i, (kind, net) in enumerate(plist):
            self.inst.append("C {devices/%s.sym} %d %d 0 0 {name=p_%s lab=%s sim_pinnumber=%d}"
                             % (kind, x, y + 40 * i, net, net, i + 1))


def sub_geom(left, right, top=("vdd",), bottom=("vss",)):
    n = max(len(left), len(right), 1)
    hh = 20 * n + 20
    pins = {}
    for p, y in zip(left, [-20 * (len(left) - 1) + 40 * i for i in range(len(left))]):
        pins[p] = (-100, y)
    for p, y in zip(right, [-20 * (len(right) - 1) + 40 * i for i in range(len(right))]):
        pins[p] = (100, y)
    for p in top:
        pins[p] = (0, -hh - 20)
    for p in bottom:
        pins[p] = (0, hh + 20)
    return pins


def sub_symbol(name, ports, left, right, label):
    box_symbol(os.path.join(BLOCK, name + ".sym"), "subcircuit", "@name @pinlist @symname", "X1",
               left, right, ["vdd"], ["vss"], label)
    # xschem's @pinlist follows the order of the B lines; rewrite them in the deck's port order
    p = os.path.join(BLOCK, name + ".sym")
    lines = open(p).read().splitlines()
    blines = {l.split("name=")[1].split()[0]: l for l in lines if l.startswith("B 5")}
    rest = [l for l in lines if not l.startswith("B 5")]
    k = rest.index("E {}") + 1
    out = rest[:k] + [blines[q] for q in ports] + rest[k:]
    with open(p, "w") as h:
        h.write("\n".join(out) + "\n")


# ---------------------------------------------------------------- seq_dly
sub_symbol("seq_dly", ["a", "y", "vdd", "vss"], ["a"], ["y"], "DLY")
s = Seq()
s.T("SEQ_DLY  -  one delay stage, %d x inv_2" % N, 0, -260, 0.7)
s.T("layout: one row, abutted, the same orientation", 0, -200, 0.4)
s.ports(-200, -100, [("ipin", "a"), ("opin", "y"), ("iopin", "vdd"), ("iopin", "vss")])
nodes = ["a"] + ["d%d" % i for i in range(1, N)] + ["y"]
PER = 6
for i in range(N):
    x = 100 + 380 * (i % PER)     # room for two labels between neighbours (d10 d10)
    y = 40 + 260 * (i // PER)
    s.std("inv_2", "XD%d" % (i + 1), x, y, {"A": nodes[i], "Y": nodes[i + 1]})
s.write(os.path.join(BLOCK, "seq_dly.sch"))

# ---------------------------------------------------------------- seq_clkgen
# the EE628 template_clkgen, gate for gate, with a delay stage in three paths
GEN_PORTS = ["clkin", "p1e", "p1", "p2e", "vdd", "vss"]
sub_symbol("seq_clkgen", GEN_PORTS, ["clkin"], ["p1e", "p1", "p2e"], "CLKGEN")
dpins = sub_geom(["a"], ["y"])
s = Seq()
s.T("SEQ_CLKGEN  -  two-phase non-overlapping clock generator with early phases", -200, -440, 0.7)
s.T("layout: phase-1 row over phase-2 row, the three delay stages identical", -200, -380, 0.4)
# drawn like the EE628 template_clkgen sheet: input buffers, phase 1 on the top
# row, phase 2 below, b1 / b2 fed back across to the other row's NAND through an
# X between the rows, a1 tapped forward to XN3, p1e / p2e tapped to the ports.
# Every net carries its deck name (check_sch.py and Analog_top compare names).
G = 100                     # wire between neighbouring pins (room for its label)
R1, R2 = 0, 400             # the two rows
TU, TD = 160, 240           # the feedback tracks between the rows
XC = 1500                   # where the tracks cross
XR = 3440                   # output ports
GATES = {"inv_2", "inv_4", "inv_8"}


def row(items, x_in, y, net_in):
    """place items left to right from the input pin at x_in on row y, wiring
    each output to the next input with the net's label; returns the last output
    x and a dict name -> (input x, output x)"""
    at, x, prev = {}, x_in, None
    for kind, name, out in items:
        hw = 100 if kind == "dly" else 80
        if prev is not None:
            px, pnet = prev
            s.W((px, y), (x, y))
            s.labw(x - 10, y, pnet)
        cx = x + hw
        if kind == "dly":
            # a / y wired like a gate's; only the supplies get a label
            s.inst.append("C {seq_dly.sym} %d %d 0 0 {name=%s}" % (cx, y, name))
            s.pins += [(cx - 100, y), (cx + 100, y)]
            s.lab(cx + dpins["vdd"][0], y + dpins["vdd"][1], "vdd", right=False)
            s.lab(cx + dpins["vss"][0], y + dpins["vss"][1], "vss", right=False)
        else:
            s.gate(kind, name, cx, y, {})
        at[name] = (x, cx + hw)
        prev, net_in = (cx + hw, out), out
        x = cx + hw + G
    return prev, at


# input buffers (on R1 - 20, the line of XN1's A input)
s.port1("ipin", -180, R1 - 20, "clkin", 1)
s.W((-180, R1 - 20), (-80, R1 - 20))
s.gate("inv_2", "XI1", 0, R1 - 20, {})
s.W((80, R1 - 20), (180, R1 - 20))
s.labw(170, R1 - 20, "clkinb")
s.gate("inv_2", "XI2", 260, R1 - 20, {})
s.W((340, R1 - 20), (440, R1 - 20))
s.labw(430, R1 - 20, "clkinbb")

# phase 1: XN1 (A clkinbb, B b2), four inverters to a1, XI11 to p1e, D, XI13 to b1
s.gate("nand2_2", "XN1", 520, R1, {})
(e1, _), at1 = row([("inv_4", "XI3", "m1"), ("inv_4", "XI5", "m2"), ("inv_4", "XI7", "m3"),
                    ("inv_4", "XI9", "a1"), ("inv_4", "XI11", "p1e"), ("dly", "XL1", "x1"),
                    ("inv_4", "XI13", "b1")], 600 + G, R1, "n1")
s.W((600, R1), (700, R1))
s.labw(690, R1, "n1")
# p1 = nand(a1, b1): XN3 with B on the row (b1), A from the a1 tap
xa1 = at1["XI9"][1] + G // 2            # a1 tap, between XI9 and XI11
xp1e = at1["XI11"][1] + G // 2          # p1e tap, between XI11 and XL1
xb1 = e1 + G                            # b1 drop to the feedback track
XN3 = xb1 + G + 80
s.gate("nand2_2", "XN3", XN3, R1 - 20, {})
s.W((e1, R1), (XN3 - 80, R1))
s.labw(XN3 - 90, R1, "b1")
s.W((xa1, R1), (xa1, R1 - 120), (XN3 - 140, R1 - 120), (XN3 - 140, R1 - 40), (XN3 - 80, R1 - 40))
s.labw(XN3 - 160, R1 - 120, "a1")
s.W((xp1e, R1), (xp1e, R1 - 200), (XR, R1 - 200))
s.port1("opin", XR, R1 - 200, "p1e", 2)
(e3, _), _ = row([("inv_4", "XI15", "y1b"), ("inv_8", "XI17", "p1")], XN3 + 80 + G, R1 - 20, "y1")
s.W((XN3 + 80, R1 - 20), (XN3 + 80 + G, R1 - 20))
s.labw(XN3 + 70 + G, R1 - 20, "y1")
s.W((e3, R1 - 20), (XR, R1 - 20))
s.port1("opin", XR, R1 - 20, "p1", 3)

# phase 2: XN2 (B b1 on top, A clkinb below), D, four inverters to a2, XI12 to p2e, D, XI14 to b2
s.gate("nand2_2", "XN2", 520, R2, {}, b_top=True)
s.W((120, R1 - 20), (120, R2 + 20), (440, R2 + 20))
(e2, _), at2 = row([("dly", "XL2", "n2d"), ("inv_4", "XI4", "k1"), ("inv_4", "XI6", "k2"),
                    ("inv_4", "XI8", "k3"), ("inv_4", "XI10", "a2"), ("inv_4", "XI12", "p2e"),
                    ("dly", "XL3", "x2"), ("inv_4", "XI14", "b2")], 600 + G, R2, "n2")
s.W((600, R2), (700, R2))
s.labw(690, R2, "n2")
xp2e = at2["XI12"][1] + G // 2
s.W((xp2e, R2), (xp2e, R2 + 200), (XR, R2 + 200))
s.port1("opin", XR, R2 + 200, "p2e", 4)
xb2 = e2 + G
s.W((e2, R2), (xb2, R2))
s.labw(xb2 - 10, R2, "b2")

# the cross-coupling: b1 down to XN2's B, b2 up to XN1's B, crossing at XC
s.W((xb1, R1), (xb1, TU), (XC + 40, TU))
s.diag((XC + 40, TU), (XC - 40, TD))
s.W((XC - 40, TD), (380, TD), (380, R2 - 20), (440, R2 - 20))
s.W((xb2, R2), (xb2, TD), (XC + 40, TD))
s.diag((XC + 40, TD), (XC - 40, TU))
s.W((XC - 40, TU), (380, TU), (380, R1 + 20), (440, R1 + 20))

s.port1("iopin", -180, R2 + 160, "vdd", 5)
s.port1("iopin", -180, R2 + 200, "vss", 6)
s.write(os.path.join(BLOCK, "seq_clkgen.sch"))

# ---------------------------------------------------------------- sample_seq
SEQ_PORTS = (["acq", "clk"] + ["s2_%d" % k for k in range(NCELLS)] + ["s0_%d" % k for k in range(NCELLS)]
             + ["s1_%d" % k for k in range(NCELLS)] + ["vdd", "vss"])
outs = [p for p in SEQ_PORTS if p.startswith("s")]
sub_symbol("sample_seq", SEQ_PORTS, ["acq", "clk"], outs, "SAMPLE SEQ")
s = Seq()
s.T("SAMPLE_SEQ  -  sampling sequencer, S2 / S0 / S1 of four cells from one clock", 0, -560, 0.7)
s.T("layout: shift register in one row; each seq_clkgen next to its atop_cell", 0, -500, 0.4)
s.ports(-300, -380, [("ipin", "acq"), ("ipin", "clk")] + [("opin", p) for p in outs]
        + [("iopin", "vdd"), ("iopin", "vss")])
s.T("shift register, one track level per cell", 60, -320, 0.45, 13)
tin = "acq"
for k in range(NCELLS):
    s.std("dfxtp_2", "XF%d" % k, 160 + 380 * k, -160, {"D": tin, "CLK": "clk", "Q": "t%d" % k})
    tin = "t%d" % k
s.T("clock generators", 60, 40, 0.45, 13)
gpins = sub_geom(["clkin"], ["p1e", "p1", "p2e"])
for k in range(NCELLS):
    s.sub("seq_clkgen", "XG%d" % k, 160 + 380 * k, 220, gpins,
          {"clkin": "t%d" % k, "p1e": "s2_%d" % k, "p1": "s0_%d" % k, "p2e": "s1_%d" % k,
           "vdd": "vdd", "vss": "vss"})
s.write(os.path.join(BLOCK, "sample_seq.sch"))
print("REPORT: sample_seq_sch.py drew sample_seq.sch, seq_clkgen.sch, seq_dly.sch (N = %d) and the symbols" % N)
