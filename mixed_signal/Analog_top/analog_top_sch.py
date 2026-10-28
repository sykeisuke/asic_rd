"""Write the xschem views of the analog macro, v5. They are the SOURCE of the
macro netlist: schematic.sh netlists analog_top.sch hierarchically and writes
analog_top.spice from it (GENERATED, never hand-edited).

v5 is Analog_top_v4 with ONE VDD/2 buffer (../midrail_ref, ADR 0021): the
output of XVREF is the net vref, wired to every cell's vref (S2 level) AND vbl
(comparator inp) pin; XVBL and the bias output that fed it (XBG.XOB, port
ivbl) are gone. Everything else is v4's (every analog block inside, no block
behind a wrapper):

  comparator_d.sch / .sym  the comparator WITH its pbias diode, flat: the ten
                           devices of ../comparator/comparator.sch
                           (copied from that drawing, positions and S/D
                           geometry as drawn) plus XREFP (pfet 1 / 0.28 um
                           diode, drawn with the same PDK symbol format). The
                           no-connect ports clk / nbias are gone; pbias is the
                           current input ibias. Pins inp inn ibias dout vdd vss;
                           a comparator-triangle symbol
  ramp_simple_d.sch / .sym the ramp WITH its pbias diode, flat: the three devices
                           of ../ramp_gen/ramp_simple.sch with the sizes WRITTEN
                           AS NUMBERS (read once from
                           ../ramp_gen/data/ramp_simple_params.spice, no {RS_*}
                           left) plus XRD (pfet 20 / 1 um, nf 10, diode).
                           Pins vramp rst vrlo ibias vdd vss
  bias_gen_s.sch / .sym  ../bias_gen/bias_gen.sch WITHOUT the ivbl source
                           XOB (and its port), plus ONE source output XOL (6
                           fingers of the 4 um / 0.9 um PMOS on pb) -> ivrlo, the
                           bias of vrlo_ref; ports bias_gen's - ivbl + ivrlo
  atop_cell.sch / .sym     one cell: S0/S1/S2 complement inverters, the three
                           switches (sw_s0/1/2.sch, drawn by sw_sch.py), the 5 x
                           5 um MIM, comparator_d, the latch ../latch/latch
                           (standard cell gf180mcu_as_sc_mcu7t3v3__dfxtn_2)
  analog_top.sch / .sym    the macro: per-block AVDD ammeters VM*, bias_gen_s |
                           midref_div + ONE midref_buf | vrlo_ref + ramp_simple_d |
                           four atop_cell. vrlo is now made inside (vrlo_ref,
                           ../vrlo_ref, ADR 0018) and is no longer a macro port.
                           The in-macro operating-point table is written on it
                           from data/op_point.csv + data/op_rc.csv (op phase)

check_equiv.py proves what changed against v4 (data/v4_ref/analog_top.spice):
both macros flattened to devices, nets matched by their pin sets.

    ./container.sh 'python3 analog_top_sch.py'
"""
import csv
import math
import os
import re

import symbols
from op_devices import MOS as OP_MOS, STATES as OP_STATES
import intent as INT  # design currents written on the sheets (check_intent.py checks them)

BLOCK = os.path.dirname(os.path.abspath(__file__))
MS = os.path.dirname(BLOCK)
SYMDIR = {  # bare symbol name -> the directory xschemrc puts on the path
    # local presentation symbols (symbols.py) of the blocks midref_div, midref_buf,
    # vrlo_ref and latch: xschem descends into the blocks' own .sch
    "midref_div.sym": "Analog_top", "midref_buf.sym": "Analog_top",
    "vrlo_ref.sym": "Analog_top", "latch.sym": "Analog_top",
    "sw_s0.sym": "Analog_top", "sw_s1.sym": "Analog_top", "sw_s2.sym": "Analog_top",
    "comparator_d.sym": "Analog_top", "ramp_simple_d.sym": "Analog_top",
    "bias_gen_s.sym": "Analog_top",
    "atop_cell.sym": "Analog_top", "analog_top.sym": "Analog_top",
}
# the block drawings the v4 cells are derived from (read, never written)
SRC_CMP = os.path.join(MS, "comparator", "comparator.sch")
SRC_RAMP = os.path.join(MS, "ramp_gen", "ramp_simple.sch")
SRC_RAMP_PAR = os.path.join(MS, "ramp_gen", "data", "ramp_simple_params.spice")
SRC_BG = os.path.join(MS, "bias_gen", "bias_gen.sch")
SRC_BG_SYM = os.path.join(MS, "bias_gen", "bias_gen.sym")
# the transistor-level switch views (sw_sch.py) are verified by sw_schematic.sh
SW_DONE = os.path.join(BLOCK, "data", "sw_schematic.done")
OP_CSV = os.path.join(BLOCK, "data", "op_point.csv")
OP_RC = os.path.join(BLOCK, "data", "op_rc.csv")
MOSFMT = 'format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"'
PIN = {
    "pfet": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "nfet": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "mim": {"G": (0, -30), "B": (0, 30)},
    "res": {"P": (0, -30), "M": (0, 30)},
    "vsrc": {"p": (0, -30), "m": (0, 30)},
}
HEAD = "v {xschem version=3.4.8RC file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n"
# text sizes on every v4 sheet
T_TITLE, T_SUB, T_BODY, T_NOTE, T_TABLE = 0.8, 0.5, 0.42, 0.36, 0.4

# the vrlo_ref bias output added to bias_gen: 6 of bias_gen's 4 um x 0.9 um
# PMOS fingers on pb. bias_gen sources 11.17 uA from 44 fingers (XOV / XOB,
# ../bias_gen/README.md), so 6 fingers give ~1.52 uA = 1.11 x vrlo_ref's
# 1.37 uA design bias, inside the 0.69-1.77 x span vrlo_ref is verified over
# (../vrlo_ref/README.md R13). Even finger count, as every bias_gen device.
# S/D geometry by bias_gen's own rule (W/nf = 4 um, 0.18 um S/D):
#   ad = int((nf+1)/2) W/nf 0.18u, as = int((nf+2)/2) W/nf 0.18u,
#   pd = 2 int((nf+1)/2) (W/nf + 0.18u), ps = 2 int((nf+2)/2) (W/nf + 0.18u), nrd = nrs = 0.18u / W
XOL_NF = 6
XOL = dict(L="0.9u", W="%gu" % (4 * XOL_NF), nf=str(XOL_NF), m="1",
           ad="%gp" % round(((XOL_NF + 1) // 2) * 4 * 0.18, 6), pd="%gu" % round(2 * ((XOL_NF + 1) // 2) * 4.18, 6),
           **{"as": "%gp" % round(((XOL_NF + 2) // 2) * 4 * 0.18, 6)},
           ps="%gu" % round(2 * ((XOL_NF + 2) // 2) * 4.18, 6),
           nrd="%.4g" % (0.18 / (4 * XOL_NF)), nrs="%.4g" % (0.18 / (4 * XOL_NF)))

# What the drawings draw at the macro and cell level (v5). The derived cells'
# contents are checked by schematic.sh against their source decks.
TOPOLOGY = """
.subckt atop_cell vfe vramp s0 s1 s2 vref vbl ibias q clk vdd vss dvdd dvss
XI0N s0b s0 vss vss nfet_03v3 L=0.28u W=0.44u nf=1 m=1
XI0P s0b s0 vdd vdd pfet_03v3 L=0.28u W=0.88u nf=1 m=1
XI1N s1b s1 vss vss nfet_03v3 L=0.28u W=0.44u nf=1 m=1
XI1P s1b s1 vdd vdd pfet_03v3 L=0.28u W=0.88u nf=1 m=1
XI2N s2b s2 vss vss nfet_03v3 L=0.28u W=0.44u nf=1 m=1
XI2P s2b s2 vdd vdd pfet_03v3 L=0.28u W=0.88u nf=1 m=1
XS2 vref bot s2 s2b vdd vss sw_s2
XS0 vfe top s0 s0b vdd vss sw_s0
XS1 vramp top s1 s1b vdd vss sw_s1
XCS bot top cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u
XCMP vbl bot ibias dout vdd vss comparator_d
XFF dout clk q dvdd dvss latch
.ends atop_cell
.subckt analog_top vin ramp_rst cnt_clk s0_0 s0_1 s0_2 s0_3 s1_0 s1_1 s1_2 s1_3
+ s2_0 s2_1 s2_2 s2_3 q0 q1 q2 q3 avdd avss dvdd dvss
VMBG avdd avdd_bg 0
VMREF avdd avdd_ref 0
VMVRLO avdd avdd_vrlo 0
VMRAMP avdd avdd_ramp 0
VMC0 avdd avdd_c0 0
VMC1 avdd avdd_c1 0
VMC2 avdd avdd_c2 0
VMC3 avdd avdd_c3 0
XBG avdd_bg avss pbias0 pbias1 pbias2 pbias3 pbias_r ivref ivrlo bias_gen_s
XDIV vmid avdd_ref avss midref_div
XVREF vref vmid ivref avdd_ref avss midref_buf
XVRLO vrlo ivrlo avdd_vrlo avss vrlo_ref
XRAMP vramp ramp_rst vrlo pbias_r avdd_ramp avss ramp_simple_d
XC0 vin vramp s0_0 s1_0 s2_0 vref vref pbias0 q0 cnt_clk avdd_c0 avss dvdd dvss atop_cell
XC1 vin vramp s0_1 s1_1 s2_1 vref vref pbias1 q1 cnt_clk avdd_c1 avss dvdd dvss atop_cell
XC2 vin vramp s0_2 s1_2 s2_2 vref vref pbias2 q2 cnt_clk avdd_c2 avss dvdd dvss atop_cell
XC3 vin vramp s0_3 s1_3 s2_3 vref vref pbias3 q3 cnt_clk avdd_c3 avss dvdd dvss atop_cell
.ends analog_top
"""


def subckts(text):
    """{name: {ports: [...], dev: {inst: {nodes, model, params}}}} from netlist text."""
    out, cur, lines = {}, None, []
    for ln in text.splitlines():
        if ln.startswith("+") and lines:
            lines[-1] += " " + ln[1:]
        else:
            lines.append(ln)
    for ln in lines:
        t = ln.split()
        if not t or t[0].startswith("*"):
            continue
        if t[0].lower() == ".subckt":
            cur = t[1]
            out[cur] = dict(ports=t[2:], dev={}, order=[])
        elif t[0].lower().startswith(".ends"):
            cur = None
        elif cur:
            kv = dict(x.split("=", 1) for x in t if "=" in x)
            pos = [x for x in t[1:] if "=" not in x]
            if t[0][0].upper() in "XC":
                d = dict(nodes=pos[:-1], model=pos[-1], params=kv)
            else:  # V / R: two nodes and a value
                d = dict(nodes=pos[:2], model=None, value=" ".join(pos[2:]), params=kv)
            out[cur]["dev"][t[0]] = d
            out[cur]["order"].append(t[0])
    return out


def sym_pins(name):
    """Pin name -> (x, y) centre, in file order, from a symbol on the xschemrc path."""
    path = os.path.join(MS, SYMDIR[name], name)
    pins = {}
    for ln in open(path):
        m = re.match(r"B 5 (\S+) (\S+) (\S+) (\S+) \{name=(\w+)", ln)
        if m:
            x1, y1, x2, y2 = (float(v) for v in m.groups()[:4])
            pins[m.group(5)] = (int(round((x1 + x2) / 2)), int(round((y1 + y2) / 2)))
    return pins


def ramp_params():
    """{RS_NAME: value string} from ../ramp_gen/data/ramp_simple_params.spice."""
    out = {}
    for ln in open(SRC_RAMP_PAR):
        m = re.match(r"\s*\.param\s+(RS_\w+)\s*=\s*(\S+)", ln)
        if m:
            out[m.group(1)] = m.group(2)
    assert set(out) >= {"RS_CW", "RS_LPS", "RS_NFPS", "RS_WPS", "RS_WRST"}, out
    return out


def pretty(v):
    """23.910u -> 23.91u, 8.000u -> 8u, 3 -> 3 (the value is unchanged)."""
    m = re.fullmatch(r"([\d.]+)([a-z]?)", v)
    return ("%g" % float(m.group(1))) + m.group(2) if m else v


class Sheet:
    """Instances, wires (split at every pin / wire end on them), labels, text."""

    def __init__(self, block):
        self.block = block
        self.inst, self.points, self.wires, self.texts, self.nl = [], [], [], [], 0

    def add(self, sym, x, y, props, pins, rot=0, flip=0):
        self.inst.append(f"C {{{sym}}} {x} {y} {rot} {flip} {{{props}}}")
        out = {}
        for k, (px, py) in pins.items():
            if flip:
                px = -px
            for _ in range(rot):
                px, py = -py, px
            out[k] = (x + px, y + py)
        self.points += list(out.values())
        return out

    def block_inst(self, sym, name, x, y, extra=""):
        return self.add(sym, x, y, f"name={name}{(' ' + extra) if extra else ''}", sym_pins(sym))

    def mos(self, d, name, x, y, flip=0):
        kind = "pfet" if d["model"].startswith("pfet") else "nfet"
        p = d["params"]
        props = (f"name={name}\nL={p['L']}\nW={p['W']}\nnf={p['nf']}\nm={p.get('m', '1')}\n"
                 f"model={d['model']}\nspiceprefix=\"\"\n{MOSFMT}")
        return self.add(f"symbols/{d['model']}.sym", x, y, props, PIN[kind], flip=flip)

    def mim(self, d, name, x, y, rot=0):
        p = d["params"]
        props = (f"name={name} W={p['c_width']} L={p['c_length']} model={d['model']} "
                 f"spiceprefix=\"\" m=1")
        return self.add("symbols/cap_mim_2f0fF.sym", x, y, props, PIN["mim"], rot=rot)

    def vsrc(self, name, x, y, value, ammeter=False):
        if ammeter:
            return self.add("devices/ammeter.sym", x, y, f"name={name} savecurrent=false", PIN["vsrc"])
        return self.add("devices/vsource.sym", x, y, f"name={name} value=\"{value}\" savecurrent=false",
                        PIN["vsrc"])

    def lab(self, x, y, net, right=False):
        self.nl += 1
        self.inst.append(f"C {{devices/lab_pin.sym}} {x} {y} 0 {1 if right else 0} "
                         f"{{name=l{self.nl} sig_type=std_logic lab={net}}}")
        self.points.append((x, y))

    def port(self, kind, x, y, net, num):
        # ipin / opin / iopin with the wire leaving to the right
        self.inst.append(f"C {{devices/{kind}.sym}} {x} {y} 0 {0 if kind == 'ipin' else 1} "
                         f"{{name=p_{net} lab={net} sim_pinnumber={num}}}")
        self.points.append((x, y))

    def wire(self, net, *pts):
        self.wires.append((list(pts), net))
        self.points += [pts[0], pts[-1]]

    def stub(self, p, net, dx=40, dy=0, right=None):
        """A short wire off a pin ending in a net label."""
        e = (p[0] + dx, p[1] + dy)
        self.wire(net, p, e)
        self.lab(*e, net, right=(dx > 0) if right is None else right)

    def text(self, t, x, y, size=T_BODY, layer=None, mono=False):
        t = t.replace("{", "\\{").replace("}", "\\}")
        prop = []
        if layer is not None:
            prop.append(f"layer={layer}")
        if mono:
            prop.append("font=Monospace")
        self.texts.append(f"T {{{t}}} {x} {y} 0 0 {size} {size} {{{' '.join(prop)}}}")

    def frame(self, x1, y1, x2, y2, title):
        for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
            self.texts.append(f"L 4 {a[0]} {a[1]} {b[0]} {b[1]} {{dash=6}}")
        self.text(title, x1 + 10, y1 + 8, T_SUB, layer=4)

    def write(self, path, title, tx=0, ty=200):
        segs = [(a, b, n) for pts, n in self.wires for a, b in zip(pts, pts[1:])]
        pset = set(self.points) | {p for a, b, _ in segs for p in (a, b)}
        out = []
        for (x1, y1), (x2, y2), net in segs:
            assert x1 == x2 or y1 == y2, (x1, y1, x2, y2)
            if x1 == x2:
                cut = sorted({y1, y2} | {py for px, py in pset if px == x1 and min(y1, y2) < py < max(y1, y2)})
                pts = [(x1, y) for y in cut]
            else:
                cut = sorted({x1, x2} | {px for px, py in pset if py == y1 and min(x1, x2) < px < max(x1, x2)})
                pts = [(x, y1) for x in cut]
            out += [f"N {p[0]} {p[1]} {q[0]} {q[1]} {{lab={net}}}" for p, q in zip(pts, pts[1:])]
        tl = (f'C {{devices/title.sym}} {tx} {ty} 0 0 {{name=l999 author="ASIC R&D - mixed_signal/Analog_top - '
              + title + '"}')
        with open(path, "w", newline="\n") as f:
            f.write(HEAD + "\n".join(self.texts) + "\n" + "\n".join(out) + "\n"
                    + "\n".join(self.inst) + "\n" + tl + "\n")


def esc(t):
    return t.replace("{", "\\{").replace("}", "\\}")


def T(t, x, y, size, layer=None):
    return f"T {{{esc(t)}}} {x} {y} 0 0 {size} {size} {{{'layer=%d' % layer if layer is not None else ''}}}"


def diode_wiring(x, y, net):
    """Wires and labels of a PMOS diode drawn at (x, y): drain and gate joined
    below the device (label net), source up and bulk right to vdd labels."""
    return [f"N {x + 20} {y + 30} {x + 20} {y + 60} {{lab={net}}}",
            f"N {x - 20} {y} {x - 40} {y} {{lab={net}}}",
            f"N {x - 40} {y} {x - 40} {y + 60} {{lab={net}}}",
            f"N {x - 40} {y + 60} {x + 20} {y + 60} {{lab={net}}}",
            lab_line(x - 40, y + 60, net, False, 1),
            f"N {x + 20} {y - 30} {x + 20} {y - 60} {{lab=vdd}}",
            lab_line(x + 20, y - 60, "vdd", True, 2),
            f"N {x + 20} {y} {x + 60} {y} {{lab=vdd}}",
            lab_line(x + 60, y, "vdd", True, 3)]


def lab_line(x, y, net, right, n):
    return f"C {{devices/lab_pin.sym}} {x} {y} 0 {1 if right else 0} {{name=lv4_{n} sig_type=std_logic lab={net}}}"


def chunks(path):
    """An xschem file as a list of objects (an object runs until its braces close)."""
    out, cur, depth = [], [], 0
    for ln in open(path):
        cur.append(ln.rstrip("\n"))
        i = 0
        while i < len(ln):
            c = ln[i]
            if c == "\\":
                i += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        if depth == 0:
            out.append("\n".join(cur))
            cur = []
    assert not cur, path
    return out


# --------------------------------------------------------------------- symbols

def sym_head(desc, template):
    return [HEAD.split("\n")[0], "G {}",
            'K {type=subcircuit\nformat="@name @pinlist @symname"\n'
            f'template="name={template}"\ndescription="{desc}"\n}}', "V {}", "S {}", "E {}"]


def box_symbol(path, desc, left, right, top, bottom, order, label, w=100, pitch=40):
    """type=subcircuit symbol, pins in subcircuit port order (order)."""
    nl = max(len(left), len(right))
    h = max(pitch * (nl + 1), 120) // 2
    pos = {}
    for k, p in enumerate(left):
        pos[p] = (-w - 20, -h + pitch * (k + 1), "L")
    for k, p in enumerate(right):
        pos[p] = (w + 20, -h + pitch * (k + 1), "R")
    for k, p in enumerate(top):
        pos[p] = (-w // 2 + k * w, -h - 20, "T")
    for k, p in enumerate(bottom):
        pos[p] = (-w // 2 + k * w, h + 20, "B")
    L = sym_head(desc, "X1") + [f"L 4 {-w} {-h} {w} {-h} {{}}", f"L 4 {w} {-h} {w} {h} {{}}",
                                f"L 4 {w} {h} {-w} {h} {{}}", f"L 4 {-w} {h} {-w} {-h} {{}}"]
    for p in order:
        x, y, side = pos[p]
        if side == "L":
            L.append(f"L 4 {x} {y} {-w} {y} {{}}")
            L.append(f"T {{{p}}} {-w + 6} {y - 10} 0 0 0.25 0.25 {{}}")
        elif side == "R":
            L.append(f"L 4 {w} {y} {x} {y} {{}}")
            L.append(f"T {{{p}}} {w - 6} {y - 10} 0 1 0.25 0.25 {{}}")
        elif side == "T":
            L.append(f"L 4 {x} {y} {x} {-h} {{}}")
            L.append(f"T {{{p}}} {x + 4} {-h + 4} 0 0 0.25 0.25 {{}}")
        else:
            L.append(f"L 4 {x} {y} {x} {h} {{}}")
            L.append(f"T {{{p}}} {x + 4} {h - 28} 0 0 0.25 0.25 {{}}")
        L.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={p} dir=inout}}")
    L += [f"T {{@name}} {-w + 6} {-h + 4} 0 0 0.3 0.3 {{}}",
          f"T {{{label}}} {-w // 2 - 10} {-12} 0 0 0.35 0.35 {{layer=13}}"]
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(L) + "\n")


CELL_PORTS = ["vfe", "vramp", "s0", "s1", "s2", "vref", "vbl", "ibias", "q", "clk", "vdd", "vss", "dvdd", "dvss"]
TOP_PORTS = (["vin", "ramp_rst", "cnt_clk"] + [f"s{j}_{k}" for j in range(3) for k in range(4)]
             + [f"q{k}" for k in range(4)] + ["avdd", "avss", "dvdd", "dvss"])
BG_PORTS = ["vdd", "vss", "icmp0", "icmp1", "icmp2", "icmp3", "iramp", "ivref", "ivrlo"]


def write_symbols():
    """Every sub-block symbol is drawn by symbols.py (function-shaped symbols);
    only the macro's own analog_top.sym stays a rectangle."""
    symbols.write_all()
    symbols.atop_cell(CELL_PORTS, left=["vfe", "vramp", "s0", "s1", "s2", "vref", "vbl", "ibias", "clk"],
                      right=["q"], top=["vdd", "dvdd"], bottom=["vss", "dvss"])
    box_symbol(os.path.join(BLOCK, "analog_top.sym"),
               "analog_top: the analog macro of the 8-bit bottom-plate ADC (v5: every analog block inside, "
               "one VDD/2 buffer for vref = vbl); xschem descends into analog_top.sch (analog_top.spice is generated "
               "from it by schematic.sh)",
               left=TOP_PORTS[:15], right=TOP_PORTS[15:19], top=["avdd", "dvdd"], bottom=["avss", "dvss"],
               order=TOP_PORTS, label="analog_top", w=130, pitch=30)


def gallery():
    """symbol_gallery.sch: every sub-block symbol once, with what it stands for
    (documentation only; never netlisted)."""
    s = Sheet("symbol_gallery")
    items = [("bias_gen_s.sym", "XBG", 200, -400, "bias_gen_s: constant-gm reference;\none current-source glyph per output\n(arrow in = sink, out = source)"),
             ("midref_div.sym", "XDIV", 640, -400, "midref_div: R + R from vdd,\nmid tap VDD/2 with decap"),
             ("midref_buf.sym", "XVREF", 960, -400, "midref_buf: unity-gain\nfollower (x1), ib = bias"),
             ("vrlo_ref.sym", "XVRLO", 1340, -400, "vrlo_ref: 5/33 tap driving a\nshunt regulator on vrlo"),
             ("ramp_simple_d.sym", "XRAMP", 1800, -400, "ramp_simple_d: sawtooth,\nI / C from vrlo, rst = reset"),
             ("comparator_d.sym", "XCMP", 200, 0, "comparator_d: comparator,\nbias diode inside"),
             ("latch.sym", "XFF", 640, 0, "latch: D flip-flop,\nfalling-edge clock"),
             ("sw_s0.sym", "XS0", 960, 0, "sw_s0 / sw_s1: transmission\ngate (bubble = ctlb)"),
             ("sw_s2.sym", "XS2", 1300, 0, "sw_s2: NMOS switch"),
             ("atop_cell.sym", "XC0", 1860, 140, "atop_cell: unit cell box with its\nS/H -> C -> CMP -> DFF path")]
    for sym, name, x, y, cap in items:
        s.block_inst(sym, name, x, y)
        s.texts.append("T {%s} %d %d 0 0 0.3 0.3 {layer=13}" % (cap, x - 140, y + 180 if sym != "atop_cell.sym" else y + 260))
    s.text("ANALOG_TOP_V5  -  SUB-BLOCK SYMBOLS (symbols.py; analog_top.sym itself stays a rectangle)", 0, -700, T_TITLE)
    s.write(os.path.join(BLOCK, "symbol_gallery.sch"), "symbol_gallery", 0, 500)


def ports_column(s, ports, kinds, y0, pitch):
    for k, p in enumerate(ports):
        y = y0 + pitch * k
        s.port(kinds.get(p, "ipin"), 40, y, p, k + 1)
        s.stub((40, y), p, dx=40)


# ------------------------------------------------- cells derived from blocks

def pwr_lines():
    """One comparator's static AVDD power, simulated: in this macro from the pwr record
    (data/pwr_windows.csv, cell 0, typical; tracking = window `track`, converting =
    `hold` / `end`) and its worst over bias_gen's 135 PVT cells (the comparator's
    gain_pvt.py, data/gain_pvt.csv)."""
    f = os.path.join(BLOCK, "data", "pwr_windows.csv")
    if not os.path.exists(f):
        return ["Static power: run PHASES=pwr"]
    w = {}
    with open(f) as fh:
        rd = csv.reader(ln for ln in fh if not ln.startswith("#"))
        hdr = next(rd)
        for r in rd:
            w[r[0]] = dict(zip(hdr[1:], map(float, r[1:])))
    conv = sorted(3.3 * w["amm_c0"][k] for k in ("hold", "end"))
    with open(os.path.join(MS, "comparator", "data", "gain_pvt.csv")) as fh:
        pmax = max(float(r["p_conv_uw"]) for r in csv.DictReader(fh))
    return ["Simulated static power: converting %.0f-%.0f uW, tracking %.0f uW in this macro (pwr record, typical);"
            % (conv[0], conv[1], 3.3 * w["amm_c0"]["track"]),
            "   converting <= %.0f uW over bias_gen's 135 PVT cells (comparator/gain_pvt.py)." % pmax]


def cmp_macro_box(x, y):
    """The current box of comparator_d.sch: the comparator's devices at the macro's
    bias (intent.py; check_intent.py compares them with the op record)."""
    c = INT.CMP_UA
    lines = ["I_B = icmp_k = %g uA into XREFP: bias_gen_s's comparator sink, sized %.2f x the comparator's"
             % (INT.BIAS_UA["icmp"], INT.BIAS_UA["icmp"] / INT.CMP.I_B_UA),
             "   %.2f uA sizing bias for its worst untrimmed PVT cell (ADR 0017).  Branches: the comparator's sizing"
             % INT.CMP.I_B_UA,
             "   record x the same ratio (../comparator/intent.py), as on comparator.sch and the CPAD slide.",
             "",
             "XTAIL            11 x 1 um, L 0.28      %g uA" % c["xtail"],
             "XINP / XINN      12 x 1 um, L 0.32      %g uA each" % c["xinp"],
             "XLOADD / XLOADM  1 x 0.5 um, L 0.36     %g uA each" % c["xloadd"],
             "XBST             5 x 1 um, L 0.28       %s  (starved inverter)" % INT.cmp_marker("xbst"),
             "XBUF4 / XBUF3    1 x 1 / 1 x 0.5 um     %s  (output inverter)" % INT.cmp_marker("xbuf4"),
             "   * during tracking.  XBUF4 is not a sized current: its crowbar as ngspice gives it.",
             "Static power converting (design): 3.3 V x (%g + %g) uA = %.0f uW (diode + tail)."
             % (INT.BIAS_UA["icmp"], c["xtail"], 3.3 * (INT.BIAS_UA["icmp"] + c["xtail"])),
             ""] + pwr_lines() + [
             "The op record puts the tail ~10 % under the design (L 0.28 um channel-length modulation;",
             "   check_intent.py reports it; gm/Id, gds, Vds - Vdsat per device: the op table on analog_top.sch)."]
    out = [T("Design currents in this macro (I_B = %g uA)" % INT.BIAS_UA["icmp"], x + 20, y + 15, 0.5),
           T("\n".join(lines), x + 20, y + 50, 0.35)]
    w = int(max(len(ln) for ln in lines) * 30 * 0.35) + 60
    h = 50 + int(58 * 0.35 * len(lines)) + 32
    for x1, y1, x2, y2 in ((x, y, x + w, y), (x + w, y, x + w, y + h), (x + w, y + h, x, y + h), (x, y + h, x, y)):
        out.append(f"L 4 {x1} {y1} {x2} {y2} {{}}")
    return out


def cmp_sheet():
    """comparator_d.sch from ../comparator/comparator.sch: every device,
    wire and operating-point note as drawn there; pbias -> ibias (port); the
    no-connect ports clk / nbias removed; XREFP added in the PDK symbol format the
    other ten devices use (so it carries the same S/D geometry template)."""
    out, ndrop, nmark = [], 0, 0
    xy2dev = {xy: d for d, xy in INT.CMP.MARKER_XY.items()}
    for ch in chunks(SRC_CMP):
        if ch.startswith("C {devices/ipin.sym}") and re.search(r"lab=(clk|nbias)\}", ch):
            ndrop += 1
            continue
        if ch.startswith("T {comparator -- ") or ch.startswith("T {Function:") \
                or ch.startswith("T {clk, nbias: no-connect"):
            continue                          # replaced by the v4 description below
        if ch.startswith("L 4 "):
            continue                          # the frames of the two replaced boxes (the bench sheet has no other)
        if ch.startswith("T {Design currents") or ch.startswith("T {Currents as used") or ch.startswith("T {I_B "):
            continue                          # the bench's current box: replaced by cmp_macro_box below
        mk = re.match(r"T \{.*\} (-?\d+) (-?\d+) 0 0 0\.28 0\.28 \{layer=4\}$", ch, re.S)
        if mk and (int(mk.group(1)), int(mk.group(2))) in xy2dev:
            xy = (int(mk.group(1)), int(mk.group(2)))
            ch = T(INT.cmp_marker(xy2dev[xy]), xy[0], xy[1], 0.28, layer=4)   # bench current -> macro current
            nmark += 1
        ch = ch.replace("lab=pbias", "lab=ibias").replace("name=ppbias", "name=pibias")
        out.append(ch)
    assert ndrop == 2, "clk / nbias pins not found in " + SRC_CMP
    assert nmark == len(INT.CMP.MARKER_XY), "expected the device current markers in %s, found %d" % (SRC_CMP, nmark)
    # XREFP: drain = gate = ibias, source = bulk = vdd; labels on its pins
    x, y = 20, -760
    out.append("C {symbols/pfet_03v3.sym} %d %d 0 0 {name=REFP\nL=0.28u W=1u nf=1 m=1\n"
               "ad=\"'int((nf+1)/2) * W/nf * 0.18u'\"\npd=\"'2*int((nf+1)/2) * (W/nf + 0.18u)'\"\n"
               "as=\"'int((nf+2)/2) * W/nf * 0.18u'\"\nps=\"'2*int((nf+2)/2) * (W/nf + 0.18u)'\"\n"
               "nrd=\"'0.18u / W'\" nrs=\"'0.18u / W'\"\nsa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}" % (x, y))
    out += diode_wiring(x, y, "ibias")
    out.append(T("XREFP  pbias diode  1 / 0.28 um\n(current in: icmp_k from\nbias_gen_v2s, %g uA design)"
                 % INT.BIAS_UA["icmp"], -170, -660, 0.3, layer=13))
    out.append(T("CMP_UPDT_V3D  -  comparator with its own pbias diode (Analog_top)", 140, -1315, 0.7))
    out.append(T("The ten devices, wires and bench notes of ../comparator/comparator.sch (ADR 0015), copied by\n"
                 "analog_top_sch.py, plus XREFP: PMOS diode W/L = 1 / 0.28 um, drain = gate = ibias. bias_gen_s SINKS\n"
                 "icmp_k from ibias, so ibias is a CURRENT input; its diode voltage biases XTAIL (11 fingers) and XBST (5).\n"
                 "Pins (subckt order, = the symbol's): inp inn ibias dout vdd vss. The old no-connect ports clk / nbias are gone.\n"
                 "dout is HIGH while inn < inp and falls when inn (the cell's bot plate) rises through inp (vbl).\n"
                 "Every MOS here, XREFP included, uses the PDK symbol's S/D junction geometry template.\n"
                 "Currents next to the devices: design values in THIS macro, I_B = icmp_k = %g uA (1.68 x the comparator's\n"
                 "%.2f uA sizing bias, ADR 0017), the same as on ../comparator/comparator.sch (* during tracking)."
                 % (INT.BIAS_UA["icmp"], INT.CMP.I_B_UA), 160, -1240, 0.4))
    out += cmp_macro_box(1330, -880)
    with open(os.path.join(BLOCK, "comparator_d.sch"), "w", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def ramp_sheet():
    """ramp_simple_d.sch from ../ramp_gen/ramp_simple.sch: the {RS_*} sizes replaced by
    their numbers, pbias -> ibias (port), XRD added (format of the other devices)."""
    rp = ramp_params()
    out, nsub = [], 0
    for ch in chunks(SRC_RAMP):
        if ch.startswith("T {ramp_simple -- ") or ch.startswith("T {Function:"):
            continue                          # replaced by the v4 description below
        if re.match(r"L 4 (0 -1060 1745 -1060|1745 -1060 1745 -693|1745 -693 0 -693|0 -693 0 -1060) ", ch):
            continue
        for k, v in rp.items():
            pat = '"\\{%s\\}"' % k
            if pat in ch:
                nsub += ch.count(pat)
                ch = ch.replace(pat, pretty(v))
        ch = ch.replace("lab=pbias", "lab=ibias").replace("name=p_pbias", "name=p_ibias")
        ch = ch.replace("(data/ramp_simple_params.spice)", "(numbers from data/ramp_simple_params.spice)")
        out.append(ch)
    assert nsub == 6, "expected 6 {RS_*} values in %s, replaced %d" % (SRC_RAMP, nsub)
    assert "RS_" not in "\n".join(c for c in out if c.startswith("C ")), "an {RS_*} value is left"
    x, y = -220, -440
    out.append("C {symbols/pfet_03v3.sym} %d %d 0 0 {name=XRD\nL=1u\nW=20u\nnf=10\nm=1\nmodel=pfet_03v3\n"
               "spiceprefix=\"\"\n%s}" % (x, y, MOSFMT.replace("@spiceprefix@name", "@name")))
    out += diode_wiring(x, y, "ibias")
    out.append(T("XRD  pbias diode\n20 / 1 um, nf 10\n(current in: iramp from\nbias_gen_v2s, %g uA design)" % INT.BIAS_UA["iramp"],
                 -380, -330, 0.3, layer=13))
    out.append(T("RAMP_SIMPLE_D  -  the shared ramp with its own pbias diode, sizes as numbers (Analog_top)",
                 20, -1045, 0.7))
    out.append(T("The three devices, wires and notes of ../ramp_gen/ramp_simple.sch, copied by analog_top_sch.py with every\n"
                 "{RS_*} parameter replaced by its value from ../ramp_gen/data/ramp_simple_params.spice: XPS L %s W %s nf %s,\n"
                 "XCR %s x %s MIM (4.00 pF), XRST W %s L 0.28u. Plus XRD: PMOS diode W/L = 20 / 1 um, nf 10, drain = gate = ibias.\n"
                 "bias_gen_s SINKS iramp from ibias (a CURRENT input); XPS mirrors the diode by (23.91/8) : (20/1) = 0.15x.\n"
                 "Pins (subckt order): vramp rst vrlo ibias vdd vss. vrlo comes from vrlo_ref (5/33 AVDD, ADR 0018).\n"
                 "vramp = vrlo + I t / C: 0.5 -> 2.0 V in 256 counts of 50 ns. rst HIGH holds vramp at vrlo through XRST.\n"
                 "The operating-point notes below are the block's OWN bench (bias_gen); in the macro: the op table on analog_top.sch."
                 % tuple(pretty(rp[k]) for k in ("RS_LPS", "RS_WPS", "RS_NFPS", "RS_CW", "RS_CW", "RS_WRST")),
                 20, -990, 0.4))
    with open(os.path.join(BLOCK, "ramp_simple_d.sch"), "w", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def bg_sheet():
    """bias_gen_s.sch = ../bias_gen/bias_gen.sch - the source XOB (ivbl)
    + the source XOL -> ivrlo."""
    out = chunks(SRC_BG)
    assert any("name=XOB" in c for c in out) and not any("ivrlo" in c for c in out)
    # v5: XOB (the ivbl source), its pin, wires and labels go; the vdd rail stays
    drop = {"N 1340 -830 1340 -720 {lab=ivbl}", "N 1260 -860 1300 -860 {lab=pb}",
            "N 1340 -980 1340 -890 {lab=vdd}", "N 1340 -860 1380 -860 {lab=vdd}"}
    n0 = len(out)
    out = [c for c in out if c not in drop and "name=XOB" not in c and "name=pivbl " not in c
           and not c.startswith("C {devices/lab_pin.sym} 1260 -860 ")
           and not c.startswith("C {devices/lab_pin.sym} 1380 -860 ")]
    assert n0 - len(out) == 8, n0 - len(out)
    assert not any("lab=ivbl" in c for c in out)
    out = [c.replace("      ivref, ivbl: SOURCE 11.17 uA each, into midref_buf ib (0.90 x its 12.36 uA bench current).",
                     "      ivref: SOURCE %g uA into midref_buf ib (0.90 x its 12.36 uA bench current); ivbl / XOB removed (v5)."
                     % INT.BIAS_UA["ivref"])
            .replace("XOV, XOB\n", "XOV\n")
            .replace("icmp0..3: SINK 3.245 uA each, into each comparator's own pbias diode (1.68 x its 1.931 uA bench current).",
                     "icmp0..3: SINK %g uA each, into each comparator's own pbias diode (1.68 x its %.2f uA design bias, ADR 0017)."
                     % (INT.BIAS_UA["icmp"], INT.CMP.I_B_UA)) for c in out]
    assert not any("3.245 uA" in c or "11.17 uA" in c for c in out), "bias_gen.sch output notes changed: update the replaces"
    x, y = 1560, -860                         # right of XOB (1320, -860), same row
    p = XOL
    out.append("C {symbols/pfet_03v3.sym} %d %d 0 0 {name=XOL\nL=%s\nW=%s\nnf=%s\nm=%s\nad=%s\npd=%s\nas=%s\nps=%s\n"
               "nrd=%s\nnrs=%s\nmodel=pfet_03v3\nspiceprefix=\"\"\n"
               "format=\"@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs\"}"
               % (x, y, p["L"], p["W"], p["nf"], p["m"], p["ad"], p["pd"], p["as"], p["ps"], p["nrd"], p["nrs"]))
    out.append(lab_line(x - 20, y, "pb", False, 1))
    out.append(f"N {x + 20} {y - 30} {x + 20} {y - 60} {{lab=vdd}}")
    out.append(lab_line(x + 20, y - 60, "vdd", True, 2))
    out.append(f"N {x + 20} {y} {x + 60} {y} {{lab=vdd}}")
    out.append(lab_line(x + 60, y, "vdd", True, 3))
    out.append(f"N {x + 20} {y + 30} {x + 20} -720 {{lab=ivrlo}}")
    out.append(f"C {{devices/iopin.sym}} {x + 20} -720 0 0 {{name=pivrlo lab=ivrlo sim_pinnumber=9}}")
    out.append(T("XOL  (Analog_top_v4)\nsource ivrlo -> vrlo_ref ib\n6 x 4 um, L 0.9 um\n%g uA = 6/44 x %g uA\n(XOB, left, removed in v5)"
                 % (INT.BIAS_UA["ivrlo"], INT.BIAS_UA["ivref"]),
                 x - 120, -690, 0.32, layer=13))
    out.append(T("BIAS_GEN_V2S = bias_gen (this sheet, ../bias_gen/bias_gen.sch, ADR 0017) WITHOUT XOB / ivbl (the second\n"
                 "VDD/2 buffer's bias, gone with that buffer in Analog_top, ADR 0021) + ONE output added in Analog_top_v4: XOL, 6 fingers of the 4 um x 0.9 um PMOS on pb, SOURCES ivrlo into vrlo_ref's NMOS diode\n"
                 "(its ib, 1.37 uA design bias; 6/44 of ivref = %g uA = %.2fx, inside vrlo_ref's verified 0.69-1.77x span).\n"
                 % (INT.BIAS_UA["ivrlo"], INT.BIAS_UA["ivrlo"] / 1.37) +
                 "Ports: bias_gen's - ivbl + ivrlo (9th). Every other device, value and note on this sheet is bias_gen's;\n"
                 "the floorplan's PMOS row (120 of 136 fingers used) has room for the 6 fingers. Drawn by analog_top_sch.py.",
                 40, -1220, 0.42, layer=4))
    with open(os.path.join(BLOCK, "bias_gen_s.sch"), "w", newline="\n") as f:
        f.write("\n".join(out) + "\n")


# ------------------------------------------------------------------------ cell

def cell_sheet(sc):
    dv = sc["dev"]
    s = Sheet("atop_cell")
    kinds = {"q": "opin", "vdd": "iopin", "vss": "iopin", "dvdd": "iopin", "dvss": "iopin"}
    ports_column(s, CELL_PORTS, kinds, -1000, 50)
    # complement inverters
    X = 380
    for k in range(3):
        Y = -1020 + 300 * k
        pp = s.mos(dv[f"XI{k}P"], f"XI{k}P", X, Y)
        nn = s.mos(dv[f"XI{k}N"], f"XI{k}N", X, Y + 120)
        sb = f"s{k}b"
        s.wire(sb, pp["D"], nn["D"])
        s.stub((X + 20, Y + 60), sb, dx=60)
        s.wire(f"s{k}", pp["G"], (X - 40, Y), (X - 40, Y + 120), nn["G"])
        s.stub((X - 40, Y + 60), f"s{k}", dx=-40)
        s.stub(pp["S"], "vdd", dx=0, dy=-20)
        s.stub(pp["B"], "vdd", dx=30)
        s.stub(nn["S"], "vss", dx=0, dy=20)
        s.stub(nn["B"], "vss", dx=30)
    # switches: a = driving side (left), b = plate side (right); S0, S1 drive
    # the top plate (upper), S2 the bottom plate (lower)
    sw = {}
    for name, (x, y) in (("XS2", (900, -420)), ("XS0", (900, -940)), ("XS1", (900, -720))):
        d = dv[name]
        a, b, ctl, ctlb, vdd, vss = d["nodes"]
        p = s.block_inst(d["model"] + ".sym", name, x, y)
        s.stub(p["a"], a, dx=-50)
        s.stub(p["ctl"], ctl, dx=0, dy=-30)
        s.stub(p["ctlb"], ctlb, dx=0, dy=-30, right=True)
        s.stub(p["vdd"], vdd, dx=0, dy=30)
        s.stub(p["vss"], vss, dx=0, dy=30, right=True)
        sw[name] = p
    # the hold capacitor, rotated: terminal 1 (bot) below, terminal 2 (top) above
    PX = 1120
    cs = s.mim(dv["XCS"], "XCS", PX, -620, rot=2)
    assert cs["G"][1] > cs["B"][1]
    s.wire("top", sw["XS0"]["b"], (PX, sw["XS0"]["b"][1]), cs["B"])
    s.wire("top", sw["XS1"]["b"], (PX, sw["XS1"]["b"][1]))
    s.wire("bot", cs["G"], (PX, sw["XS2"]["b"][1]), sw["XS2"]["b"])
    # comparator with its bias diode inside (comparator_d.sym, descended): inn on the bot line
    d = dv["XCMP"]
    inp, inn, ibias, dout, vdd, vss = d["nodes"]
    BY = -500
    cx, cy = 1620, BY - 40                            # inn pin (-120, 40) lands on BY
    cp = s.block_inst(d["model"] + ".sym", "XCMP", cx, cy)
    assert cp["inn"][1] == BY
    s.wire(inn, (PX, BY), cp["inn"])
    s.stub(cp["inp"], inp, dx=-60)
    s.stub(cp["ibias"], ibias, dx=0, dy=-60)
    s.stub(cp["vdd"], vdd, dx=0, dy=-30)
    s.stub(cp["vss"], vss, dx=0, dy=30)
    # clocked latch (../latch/latch.sym, descended to the dfxtn_2 cell): d on the dout line
    d = dv["XFF"]
    dd, clk2, q, fvdd, fvss = d["nodes"]
    fx = 2060
    fy = cp["dout"][1] + 20                           # d pin (-100, -20)
    fp = s.block_inst(d["model"] + ".sym", "XFF", fx, fy)
    s.wire(dout, cp["dout"], fp["d"])
    s.lab(cp["dout"][0] + 60, cp["dout"][1], dout, right=True)
    s.stub(fp["clk"], clk2, dx=-50)
    s.stub(fp["q"], q, dx=60)
    s.stub(fp["vdd"], fvdd, dx=0, dy=-30)
    s.stub(fp["vss"], fvss, dx=0, dy=30)
    # node names on the plates
    s.lab(PX, sw["XS0"]["b"][1], "top", right=True)
    s.lab(PX, sw["XS2"]["b"][1], "bot", right=True)
    # annotation next to the devices
    s.text("top plate: S0 / S1 side\n(driven: vfe, then vramp)", PX + 30, -900, T_NOTE, layer=13)
    s.text("XCS  MIM 5 x 5 um\n54.52 fF = 1.99 fF/um2 x 25 um2\n+ 0.238 fF/um x 20 um fringe\n"
           "(PDK formula, typical)", PX + 30, -700, T_NOTE, layer=13)
    s.text("bot plate: S2 + comparator inn\n(floats from S2 opening to the\nend of conversion)",
           PX + 30, -470, T_NOTE, layer=13)
    s.text("ibias: icmp_k from bias_gen_s\n(%g uA sink, design) into the\ndiode XREFP inside comparator_d"
           % INT.BIAS_UA["icmp"],
           cx + 80, -790, T_NOTE, layer=13)
    s.text("std-cell flip-flop dfxtn_2 (as_sc_mcu7t3v3)\non dvdd: q falls at the first FALLING\nclk edge after dout falls", fx - 120, -400,
           T_NOTE, layer=13)
    s.text("complements s0b / s1b / s2b:\nP 0.88 / N 0.44 um, L 0.28 um", 250, -170, T_NOTE, layer=13)
    # title and function
    s.text("ATOP_CELL  -  one sampling / conversion cell of analog_top (8-bit true bottom-plate single-slope ADC)",
           40, -1560, T_TITLE)
    s.text("TRACK    S0 and S2 closed: top = vfe (the input), bot = vref (VDD/2). The comparator sits at its trip point.\n"
           "SAMPLE   S2 opens at TS_k: the charge on C_S is frozen (the sampling instant, the bottom-plate edge).\n"
           "         S0 opens TNOV = 5 ns later (top isolated), S1 closes after another 5 ns: top = vramp = vrlo.\n"
           "CONVERT  vramp rises 0.5 -> 2.0 V in 12.8 us; bot follows top by alpha = C_S / (C_S + C_bot) and crosses\n"
           "         vbl when vramp = vin: dout falls (comparator delay ~6.5 ns), q falls at the next falling cnt_clk edge.\n"
           "Switches (sw_sN.sch, = ref/switches.spice): S0, S1 TG N 0.5 / P 1.0 um, S2 NMOS 0.36 um, L 0.28 um.",
           40, -1480, T_BODY)
    s.frame(250, -1120, 640, -200, "S0/S1/S2 COMPLEMENTS")
    s.frame(700, -1120, 1360, -200, "SWITCHES + HOLD CAP")
    s.frame(1380, -1120, 2300, -200, "COMPARATOR (comparator_d) + LATCH")
    return s


# ----------------------------------------------------------------------- macro

def fmt_si(v, unit, digits=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    a = abs(v)
    if 0 < a < 1e-15:
        return f"{v:.1e} {unit}"
    for scale, pre in ((1e-15, "f"), (1e-12, "p"), (1e-9, "n"), (1e-6, "u"), (1e-3, "m"), (1, ""),
                       (1e3, "k"), (1e6, "M"), (1e9, "G")):
        if a < scale * 1000 or pre == "G":
            return f"{v / scale:.{digits}g} {pre}{unit}"
    return f"{v:g} {unit}"


def func_record():
    """data/func_reduce.txt (func phase) as {name: float}, or {} before the first run."""
    out = {}
    p = os.path.join(BLOCK, "data", "func_reduce.txt")
    if os.path.exists(p):
        for ln in open(p):
            t = ln.split()
            if len(t) >= 3 and t[1] == "=":
                try:
                    out[t[0]] = float(t[2])
                except ValueError:
                    pass
    return out


def op_table():
    """The in-macro operating point as text lines, from the op phase's CSVs."""
    if not (os.path.exists(OP_CSV) and os.path.exists(OP_RC)):
        return [["(no data/op_point.csv yet: run ./scripts/sim.sh analog-top PHASES=op)"], [], []], ""
    rows = {}
    stamp = ""
    with open(OP_CSV) as f:
        first = f.readline()
        if first.startswith("#"):
            stamp = first.strip("# \n")
        else:
            f.seek(0)
        for r in csv.DictReader(f):
            rows[(r["key"], r["state"])] = r
    # three columns: devices | devices | switches, R, C. Cells 1..3 (= cell 0) are
    # left to the CSV
    hdr = (f"{'device  role':<36}{'state':<6}{'Id':>9}{'gm':>9}{'gm/Id':>7}{'gds':>9}"
           f"{'Vov':>8}{'Vds-Vdsat':>11}  region")
    dev, last = [], None
    for key, path, blk, role, st in OP_MOS:
        if key[:3] in ("c1_", "c2_", "c3_"):
            continue
        r = rows.get((key, st))
        if r is None:
            continue
        if blk != last:
            dev.append(f"-- {blk}")
            last = blk
        f_ = lambda k: float(r[k])
        dev.append(f"{path.split('.')[-1] + '  ' + role[:26]:<36}{st:<6}"
                   f"{fmt_si(abs(f_('id')), 'A'):>9}{fmt_si(f_('gm'), 'S'):>9}{f_('gm_id'):>7.1f}"
                   f"{fmt_si(f_('gds'), 'S'):>9}{f_('vov') * 1e3:>6.0f}mV{f_('vds_vdsat') * 1e3:>9.0f}mV  "
                   f"{r['region']}")
    dev.append("-- cells 1..3 = cell 0: data/op_point.csv")
    half = (len(dev) + 1) // 2
    while half < len(dev) - 1 and not dev[half].startswith("--"):     # break at a block heading
        half += 1
    left, right = [hdr] + dev[:half], [hdr] + dev[half:]
    with open(OP_RC) as f:
        rc = [r for r in csv.DictReader(f)]
    rcl = ["-- switches while closed: Ron = 1 / sum gds, Vds ~ 0"]
    for r in rc:
        if r["kind"] == "ron":
            rcl.append(f"   {r['name']:<34} {r['state']:<5} Ron = {fmt_si(float(r['value']), 'ohm', 4)}")
    rcl += ["", "-- resistors, R = V / I (ramp state)"]
    for r in rc:
        if r["kind"] == "res":
            rcl.append(f"   {r['name']:<10} R = {fmt_si(float(r['value']), 'ohm', 5):>11}  V = {float(r['v']) * 1e3:7.2f} mV"
                       f"  I = {fmt_si(float(r['i']), 'A', 4)}")
    rcl += ["   (bias_gen_s XR1..5: ppolyf_u 1 x 10.73 um, 350 ohm/sq + heads;",
            "    midref_div XRT / XRB: ppolyf_u_3k 1 x 64.98 um, 3 kohm/sq;",
            "    vrlo_ref XR1..33: ppolyf_u_3k 1 x 20 um each, 28 : 5)",
            "", "-- MIM capacitors: model readback (PDK formula)"]
    for r in rc:
        if r["kind"] == "cap":
            rcl.append(f"   {r['name']:<14} C = {fmt_si(float(r['value']), 'F', 5):>10}  "
                       f"({fmt_si(float(r['formula']), 'F', 5)})  {r['role'][:30]}")
    rcl += ["   formula: 1.99 fF/um2 x area + 0.2383 fF/um x perimeter",
            "   (sm141064_mim.ngspice cap_mim_2f0_m4m5_noshield, typical)"]
    return [left, right, rcl], stamp


def top_sheet(sc):
    dv = sc["dev"]
    s = Sheet("analog_top")
    kinds = {f"q{k}": "opin" for k in range(4)}
    kinds.update({p: "iopin" for p in ("avdd", "avss", "dvdd", "dvss")})
    ports_column(s, TOP_PORTS, kinds, -1240, 45)
    RAIL = -1380
    xs = {"VMBG": 520, "VMREF": 1060, "VMVRLO": 1580, "VMRAMP": 1880}
    for k in range(4):
        xs[f"VMC{k}"] = 2420 + 620 * k
    s.wire("avdd", (300, RAIL), (xs["VMC3"], RAIL))
    s.lab(300, RAIL, "avdd")
    for name, x in xs.items():
        d = dv[name]
        p = s.vsrc(name, x, RAIL + 60, "0", ammeter=True)
        s.wire(d["nodes"][0], (x, RAIL), p["p"])
        s.stub(p["m"], d["nodes"][1], dx=0, dy=30)
    # bias
    d = dv["XBG"]
    p = s.block_inst("bias_gen_s.sym", "XBG", 520, -900)
    for pin, net in zip(BG_PORTS, d["nodes"]):
        if pin == "vdd":
            s.stub(p[pin], net, dx=0, dy=-40)
        elif pin == "vss":
            s.stub(p[pin], net, dx=0, dy=40)
        else:
            s.stub(p[pin], net, dx=60)
    # references
    d = dv["XDIV"]
    pv = s.block_inst("midref_div.sym", "XDIV", 920, -1000)
    vmid, dvdd_, dvss_ = d["nodes"]
    s.stub(pv["vdd"], dvdd_, dx=0, dy=-40)
    s.stub(pv["vss"], dvss_, dx=0, dy=40)
    # v5: ONE buffer; its output net vref goes to every cell's vref AND vbl pin
    d = dv["XVREF"]
    out, vin, ib, vdd, vss = d["nodes"]
    pb = s.block_inst("midref_buf.sym", "XVREF", 1200, -1000)
    s.stub(pb["out"], out, dx=60)
    s.stub(pb["ib"], ib, dx=-40)
    s.stub(pb["vdd"], vdd, dx=0, dy=-40)
    s.stub(pb["vss"], vss, dx=0, dy=40)
    s.wire(vmid, pv["vin"], pb["vin"])
    assert pv["vin"][1] == pb["vin"][1]
    s.lab((pv["vin"][0] + pb["vin"][0]) // 2, pv["vin"][1], vmid)     # names the tap net (v4 named it on XVBL's branch)
    # VR_LO shunt regulator (../vrlo_ref, descended), below the ramp
    d = dv["XVRLO"]
    vrlo_n, ib, vdd, vss = d["nodes"]
    pz = s.block_inst("vrlo_ref.sym", "XVRLO", 1700, -665)
    s.stub(pz["vrlo"], vrlo_n, dx=60)
    s.stub(pz["ib"], ib, dx=-60)
    s.stub(pz["avdd"], vdd, dx=0, dy=-40)
    s.stub(pz["avss"], vss, dx=0, dy=40)
    # the ramp with its bias diode inside (ramp_simple_d.sym, descended)
    d = dv["XRAMP"]
    pr = s.block_inst("ramp_simple_d.sym", "XRAMP", 1880, -940)
    vramp, rst, vrlo, ibias, vdd, vss = d["nodes"]
    s.stub(pr["ibias"], ibias, dx=-60)
    s.stub(pr["rst"], rst, dx=-60)
    s.stub(pr["vrlo"], vrlo, dx=-60)
    s.stub(pr["vramp"], vramp, dx=60)
    s.stub(pr["vdd"], vdd, dx=0, dy=-40)
    s.stub(pr["vss"], vss, dx=0, dy=40)
    # cells
    for k in range(4):
        name = f"XC{k}"
        d = dv[name]
        x = 2420 + 620 * k
        pc = s.block_inst("atop_cell.sym", name, x, -800)
        for pin, net in zip(CELL_PORTS, d["nodes"]):
            if pin in ("vdd", "dvdd"):
                s.stub(pc[pin], net, dx=0, dy=-40)
            elif pin in ("vss", "dvss"):
                s.stub(pc[pin], net, dx=0, dy=40)
            elif pin == "q":
                s.stub(pc[pin], net, dx=60)
            else:
                s.stub(pc[pin], net, dx=-60)
    s.frame(320, -1300, 760, -480, "BIAS")
    s.frame(800, -1300, 1440, -480, "REF (VDD/2): vref = vbl")
    s.frame(1480, -1300, 2120, -480, "RAMP + VR_LO")
    s.frame(2160, -1300, 4560, -480, "FOUR CELLS")
    # ---- title, signal flow
    s.text("ANALOG_TOP (v5)  -  analog macro of the 8-bit true bottom-plate single-slope ADC: four cells on one shared ramp",
           40, -1800, T_TITLE)
    s.text("SIGNAL FLOW  vin -> S0 -> top plate of C_S (54.52 fF) in each cell; S2 opening at TS_k freezes the sample "
           "(cells 50 ns apart = 20 MSa/s).\n"
           "             After sampling S1 puts vramp on the top plate; the shared ramp (vrlo -> 2.0 V, 12.8 us) "
           "lifts the floating bottom plate, the comparator\n"
           "             fires when it crosses vref (its inp, = vbl), and the std-cell latch turns that into one falling q per conversion: "
           "code = floor((t_q - TR) / 50 ns), 8 bits + 20 overrun.\n"
           "TIMING       20 MHz cnt_clk (TCOUNT 50 ns); ramp_rst HIGH holds vramp at vrlo = 5/33 AVDD (vrlo_ref); "
           "the ramp is released >= 300 ns after the last S1 closes (ADR 0018).\n"
           "SUPPLIES     avdd 3.3 V: bias, references, VR_LO, ramp, cells (split per block by the 0 V ammeters VM*); "
           "dvdd 3.3 V: the four latches only.\n"
           "v5           ONE VDD/2 buffer: vref is both the S2 level of every bottom plate and every comparator's inp "
           "(midrail_ref, ADR 0021); every analog block inside, no ideal source in the analog path.",
           40, -1720, T_BODY)
    # ---- per-block notes under the frames
    fr = func_record()
    g = lambda k, f="%.3g": (f % fr[k]) if k in fr else "?"
    src = "func record" if fr else "func not yet run"
    s.text("XBG bias_gen_s (ADR 0017) =\nbias_gen_v2 - XOB + XOL (ivrlo)\nL 0.9 um, 4 um fingers, R 5 x\n"
           f"10.73 um ppolyf_u, 1 pF decaps.\nCURRENT outputs (design):\n"
           f" icmp0..3 sinks {INT.BIAS_UA['icmp']:g} uA each\n   (1.68 x {INT.CMP.I_B_UA:.2f} uA)\n"
           f" iramp sink {INT.BIAS_UA['iramp']:g} uA\n"
           f" ivref source {INT.BIAS_UA['ivref']:g} uA\n ivrlo source {INT.BIAS_UA['ivrlo']:g} uA\n"
           f"op record within {100 * INT.TOL:.0f} % (check_intent)\n"
           f"core {g('icore_ts0_ua', '%.2g')} uA per branch, {g('pw_bg_uw', '%.0f')} uW\n({src})",
           330, -440, T_NOTE)
    s.text("XDIV midref_div: 2 x ppolyf_u_3k\n1 x 64.98 um + MIM tap decap\n-> vmid = VDD/2 (R, C below)\n"
           "XVREF midref_buf (ADR 0016, 0021):\nONE class-AB flipped-voltage follower,\n"
           "ib diode inside, 11.7 um MIM on out.\nvref: S2 track level of every bot\nplate AND every comparator's inp\n"
           f"refs power {g('pw_ref_uw')} uW",
           810, -440, T_NOTE)
    s.text("XVRLO vrlo_ref (ADR 0018): shunt regulator\non a 28 : 5 ppolyf_u_3k tap = 5/33 AVDD,\n"
           "3.44 pF decap; ib = ivrlo from XBG.\n"
           f"vrlo at TR {g('vrlo_tr_v', '%.5f')} V, {g('pw_vrlo_uw')} uW.\n"
           "XRAMP ramp_simple_d: PMOS source XPS\n(L 8, W 23.91 um, nf 3) into a 44.6 um\n"
           "MIM (4.0 pF), reset NMOS to vrlo,\nown pbias diode XRD inside.\n"
           f"slope {g('ramp_slope_vpus', '%.4f')} V/us (ideal 0.1172),\nINL {g('ramp_inl_bf_lsb', '%.3f')} LSB; "
           f"{g('pw_ramp_uw')} uW.",
           1490, -440, T_NOTE)
    s.text("XC0..XC3 atop_cell (atop_cell.sch): S0/S1/S2 (sw_sN.sch), 54.52 fF MIM, comparator_d (comparator + its pbias "
           "diode,\ncurrent input ibias = icmp_k), latch (std cell dfxtn_2) on dvdd; tb: 40 fF on every q (digital capture pins + wire).\n"
           "Each cell has its own s0_k / s1_k / s2_k: the sampling instant of cell k is the fall of s2_k.",
           2170, -440, T_NOTE)
    s.text("VMBG / VMREF / VMVRLO / VMRAMP / VMC0..3: 0 V ammeters splitting the avdd current per block (i(v.xdut.vmbg) ...), "
           "measurement only.   Drawing generated by analog_top_sch.py; schematic.sh netlists it, every block below "
           "it included, into analog_top.spice (GENERATED).", 330, -1460, T_NOTE)
    # ---- the in-macro operating point
    lines, stamp = op_table()
    s.text("IN-MACRO OPERATING POINT  (op phase, ngspice, typical 27 C, 3.3 V; " + (stamp or "not yet run") + ")",
           330, -120, T_SUB, layer=4)
    s.text("States: " + "; ".join(f"{k} = {v[0]}: {v[1]}" for k, v in OP_STATES.items()) + ".\n"
           "Region: sat if |Vds| > Vdsat (inversion by gm/Id: weak > 20, moderate 10-20, strong < 10 /V), else triode; "
           "off if Vov <= 0 and |Id| < 1 pA. Vov = |Vgs| - |Vth|. Full table: data/op_point.csv, data/op_rc.csv.",
           330, -70, T_NOTE)
    for col, x in zip(lines, (330, 1720, 3110)):
        if col:
            s.text("\n".join(col), x, 20, T_TABLE, mono=True)
    return s, max(len(c) for c in lines)


def main():
    sc = subckts(TOPOLOGY)
    assert sc["atop_cell"]["ports"] == CELL_PORTS, sc["atop_cell"]["ports"]
    assert sc["analog_top"]["ports"] == TOP_PORTS, sc["analog_top"]["ports"]
    if not os.path.exists(SW_DONE):
        print("REPORT: analog_top_sch: data/sw_schematic.done absent: sw_s0/1/2.sym placed, their "
              "drawings not yet verified by sw_schematic.sh")
    write_symbols()
    gallery()
    cmp_sheet()
    ramp_sheet()
    bg_sheet()
    cell_sheet(sc["atop_cell"]).write(os.path.join(BLOCK, "atop_cell.sch"), "atop_cell", 40, 0)
    top, nrows = top_sheet(sc["analog_top"])
    top.write(os.path.join(BLOCK, "analog_top.sch"), "analog_top", 40, 120 + 25 * nrows + 150)
    print("REPORT: wrote comparator_d, ramp_simple_d, bias_gen_s (derived from the block drawings), atop_cell, "
          "analog_top .sch/.sym (midref_div, midref_buf, vrlo_ref, latch, sw_s0/1/2: descended); op table %d lines"
          % nrows)


if __name__ == "__main__":
    main()
