"""Draw sample_seq's xschem views from the deck's structure and data/sizing.json.

    python3 sample_seq_sch.py

Writes sample_seq.sch / .sym (the sequencer), seq_dly.sch / .sym (one delay
stage, N x dlybuff_2), seq_cell.sch / .sym (one cell's S2 / S0 / S1 pipeline),
the four library primitive symbols and tb_seq.sch's drawing is not made here
(the bench is the deck). Every sheet text is in this file. The schematic
phase netlists sample_seq.sch with xschem and check_sch.py compares it with
sample_seq.spice subcircuit by subcircuit.
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
    "dlybuff_2": (["VDD", "VNW", "VPW", "VSS", "Y", "A"], ["A"], ["Y"], "DLY"),
    "clkbuff_4": (["VDD", "VNW", "VPW", "VSS", "A", "Y"], ["A"], ["Y"], "CLKBUF"),
    "dfxtp_2": (["VDD", "VNW", "VPW", "VSS", "CLK", "D", "Q"], ["D", "CLK"], ["Q"], "DFF"),
    "nor2_2": (["VDD", "VNW", "VPW", "VSS", "Y", "B", "A"], ["A", "B"], ["Y"], "NOR2"),
    "xor2_2": (["VDD", "VNW", "VPW", "VSS", "B", "A", "Y"], ["A", "B"], ["Y"], "XOR2"),
    "nor3_2": (["VDD", "VNW", "VPW", "VSS", "A", "B", "C", "Y"], ["A", "B", "C"], ["Y"], "NOR3"),
    "nand4_2": (["VDD", "VNW", "VPW", "VSS", "A", "B", "C", "D", "Y"], ["A", "B", "C", "D"], ["Y"], "NAND4"),
    "and2_2": (["VDD", "VNW", "VPW", "VSS", "B", "A", "Y"], ["A", "B"], ["Y"], "AND2"),
    "dlxtn_2": (["VDD", "VNW", "VPW", "VSS", "ENA", "D", "Q"], ["D", "ENA"], ["Q"], "LATCH"),
}


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


# nor2_2 also ships with ../ic_source (its drawing places it), and both folders
# are on ../Analog_top's symbol path: the symbol written here must be that one,
# byte for byte, or xschem picks one and the other sheet's pins float
NOR2_PINS = {"B": (-80, -20), "A": (-80, 20), "Y": (80, 0), "VDD": (-20, -60), "VNW": (20, -60),
             "VSS": (-20, 60), "VPW": (20, 60)}
NOR2_TEXT = """v {xschem version=3.4.8RC file_version=1.2}
G {}
K {type=primitive
format="@name @@VDD @@VNW @@VPW @@VSS @@Y @@B @@A @symname"
template="name=X1"
}
V {}
S {}
E {}
L 4 -60 -40 60 -40 {}
L 4 60 -40 60 40 {}
L 4 60 40 -60 40 {}
L 4 -60 40 -60 -40 {}
L 4 -80 -20 -60 -20 {}
B 5 -82.5 -22.5 -77.5 -17.5 {name=B dir=in}
T {B} -54 -26 0 0 0.25 0.25 {}
L 4 -80 20 -60 20 {}
B 5 -82.5 17.5 -77.5 22.5 {name=A dir=in}
T {A} -54 14 0 0 0.25 0.25 {}
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
T {NOR2} -40 -8 0 0 0.3 0.3 {layer=13}
"""


def std_geom(cell):
    if cell == "nor2_2":
        return dict(NOR2_PINS)
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
    if cell == "nor2_2":
        with open(os.path.join(BLOCK, "%s__%s.sym" % (LIB, cell)), "w") as h:
            h.write(NOR2_TEXT)
        continue
    box_symbol(os.path.join(BLOCK, "%s__%s.sym" % (LIB, cell)), "primitive",
               "@name " + " ".join("@@" + p for p in order) + " @symname", "X1", left, right,
               ["VDD", "VNW"], ["VSS", "VPW"], label)


class Seq(Sheet):
    def std(self, cell, name, x, y, nets):
        """a library cell at (x, y); every pin labelled with its net (supplies vdd / vss)"""
        self.inst.append("C {%s__%s.sym} %d %d 0 0 {name=%s}" % (LIB, cell, x, y, name))
        nets = dict(nets, VDD="vdd", VNW="vdd", VSS="vss", VPW="vss")
        for p, (px, py) in std_geom(cell).items():
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
sub_symbol("seq_dly", ["a", "y", "vdd", "vss"], ["a"], ["y"], "D")
s = Seq()
s.T("SEQ_DLY  -  one delay stage, %d x dlybuff_2" % N, 0, -260, 0.7)
s.T("layout: one row, abutted, the same orientation", 0, -200, 0.4)
s.ports(-200, -100, [("ipin", "a"), ("opin", "y"), ("iopin", "vdd"), ("iopin", "vss")])
nodes = ["a"] + ["d%d" % i for i in range(1, N)] + ["y"]
PER = 8
for i in range(N):
    x = 100 + 280 * (i % PER)
    y = 40 + 260 * (i // PER)
    s.std("dlybuff_2", "XD%d" % (i + 1), x, y, {"A": nodes[i], "Y": nodes[i + 1]})
s.write(os.path.join(BLOCK, "seq_dly.sch"))

# ---------------------------------------------------------------- seq_cell
CELL_PORTS = ["tin", "c0", "c5", "c10", "s2", "s0", "s1", "done", "vdd", "vss"]
sub_symbol("seq_cell", CELL_PORTS, ["tin", "c0", "c5", "c10"], ["s2", "s0", "s1", "done"], "SEQ")
s = Seq()
s.T("SEQ_CELL  -  one cell's S2 / S0 / S1 phases, a flop per phase", 0, -360, 0.7)
s.T("layout: next to its cell, the three flops in one row", 0, -300, 0.4)
s.ports(-260, -140, [("ipin", n) if n in ("tin", "c0", "c5", "c10") else
                     ("opin", n) if n.startswith("s") else ("iopin", n) for n in CELL_PORTS])
s.T("S2 (sampling)", 60, -190, 0.45, 13)
s.std("dfxtp_2", "XFA", 120, 0, {"D": "tin", "CLK": "c0", "Q": "s2"})
s.T("S0", 420, -190, 0.45, 13)
s.std("dfxtp_2", "XFB", 480, 0, {"D": "s2", "CLK": "c5", "Q": "s0"})
s.T("S1", 780, -190, 0.45, 13)
s.std("dfxtp_2", "XFC", 840, 0, {"D": "s0", "CLK": "c10", "Q": "qc"})
s.std("nor2_2", "XNR", 1140, 0, {"A": "s2", "B": "qc", "Y": "s1"})
s.T("settled", 60, 110, 0.45, 13)
s.std("xor2_2", "XX1", 120, 300, {"A": "tin", "B": "s2", "Y": "x1"})
s.std("xor2_2", "XX2", 420, 300, {"A": "s2", "B": "s0", "Y": "x2"})
s.std("xor2_2", "XX3", 720, 300, {"A": "s0", "B": "qc", "Y": "x3"})
s.std("nor3_2", "XND", 1020, 300, {"A": "x1", "B": "x2", "C": "x3", "Y": "done"})
s.write(os.path.join(BLOCK, "seq_cell.sch"))

# ---------------------------------------------------------------- sample_seq
SEQ_PORTS = (["acq", "clk"] + ["s2_%d" % k for k in range(NCELLS)] + ["s0_%d" % k for k in range(NCELLS)]
             + ["s1_%d" % k for k in range(NCELLS)] + ["vdd", "vss"])
outs = [p for p in SEQ_PORTS if p.startswith("s")]
sub_symbol("sample_seq", SEQ_PORTS, ["acq", "clk"], outs, "SAMPLE SEQ")
s = Seq()
s.T("SAMPLE_SEQ  -  sampling sequencer, S2 / S0 / S1 of four cells from one clock", 0, -860, 0.7)
s.T("layout: delay line shared; each seq_cell next to its atop_cell", 0, -800, 0.4)
s.ports(-300, -560, [("ipin", "acq"), ("ipin", "clk")] + [("opin", p) for p in outs]
        + [("iopin", "vdd"), ("iopin", "vss")])
s.T("clock gate", 60, -660, 0.45, 13)
s.std("nand4_2", "XEN", 160, -440, {"A": "done_0", "B": "done_1", "C": "done_2", "D": "done_3", "Y": "en"})
s.std("dlxtn_2", "XLG", 460, -440, {"D": "en", "ENA": "clk", "Q": "en_l"})
s.std("and2_2", "XAG", 760, -440, {"A": "clk", "B": "en_l", "Y": "gclk"})
s.T("delay line, c5 = c0 + D, c10 = c5 + D", 60, -300, 0.45, 13)
s.std("clkbuff_4", "XB0", 160, -160, {"A": "gclk", "Y": "c0"})
dpins = sub_geom(["a"], ["y"])
s.sub("seq_dly", "XL1", 520, -160, dpins, {"a": "c0", "y": "c5r", "vdd": "vdd", "vss": "vss"})
s.std("clkbuff_4", "XB5", 880, -160, {"A": "c5r", "Y": "c5"})
s.sub("seq_dly", "XL2", 1240, -160, dpins, {"a": "c5", "y": "c10r", "vdd": "vdd", "vss": "vss"})
s.std("clkbuff_4", "XB10", 1600, -160, {"A": "c10r", "Y": "c10"})
s.T("cells, 50 ns apart (S2 flops are the token chain)", 60, 20, 0.45, 13)
cpins = sub_geom(["tin", "c0", "c5", "c10"], ["s2", "s0", "s1", "done"])
for k in range(NCELLS):
    nets = {"tin": "acq" if k == 0 else "s2_%d" % (k - 1), "c0": "c0", "c5": "c5", "c10": "c10",
            "s2": "s2_%d" % k, "s0": "s0_%d" % k, "s1": "s1_%d" % k, "done": "done_%d" % k,
            "vdd": "vdd", "vss": "vss"}
    s.sub("seq_cell", "XC%d" % k, 200 + 380 * k, 200, cpins, nets)
s.write(os.path.join(BLOCK, "sample_seq.sch"))
print("REPORT: sample_seq_sch.py drew sample_seq.sch, seq_dly.sch (N = %d), seq_cell.sch and the symbols" % N)
