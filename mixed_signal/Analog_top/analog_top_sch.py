"""Write the xschem views of the analog macro, v7 (v6 + the sampling
sequencer ../sample_seq, ADR 0027). They are the SOURCE of the
macro netlist: schematic.sh netlists analog_top.sch hierarchically and writes
analog_top.spice from it (GENERATED, never hand-edited).

v6 (ADR 0026) is v5 with the ramp of ADR 0025: ../ramp_simple (73 unit MIMs +
the reset switch to vrlo) fed by the I/C current source ../ic_source (one unit
MIM switched at the count clock against 5/33 AVDD; its bias input on
bias_gen_s's ramp sink, the net pbias_r; AVDD through the ammeter VMRAMP, its
phase generator on DVDD). Both are the blocks' own drawings, descended through
xschemrc like vrlo_ref; ramp_simple_d (the PMOS-mirror ramp + its diode XRD)
is gone. vrlo_ref (../vrlo_ref) now makes 7/55 AVDD = 0.420 V, the ramp's
pre-roll reset level. v5 was Analog_top_v4 with ONE VDD/2 buffer
(../midrail_ref, ADR 0021): the output of XVREF is the net vref, wired to
every cell's vref (S2 level) AND vbl (comparator inp) pin. The cells, the
bias and the references are v5's (every analog block inside, no block behind
a wrapper):

  comparator_d.sch / .sym  the comparator WITH its pbias diode, flat: the ten
                           devices of ../comparator/comparator.sch
                           (copied from that drawing, positions and S/D
                           geometry as drawn) plus XREFP (pfet 1 / 0.28 um
                           diode, drawn with the same PDK symbol format). The
                           no-connect ports clk / nbias are gone; pbias is the
                           current input ibias. Pins inp inn ibias dout vdd vss;
                           a comparator-triangle symbol
  bias_gen_s.sch / .sym  ../bias_gen/bias_gen.sch WITHOUT the ivbl source
                           XOB (and its port), plus ONE source output XOL (6
                           fingers of the 4 um / 0.9 um PMOS on pb) -> ivrlo, the
                           bias of vrlo_ref; ports bias_gen's - ivbl + ivrlo
  atop_cell.sch / .sym     one cell: S0/S1/S2 complement inverters, the three
                           switches (sw_s0/1/2.sch, drawn by sw_sch.py), the 5 x
                           5 um MIM, comparator_d, the latch ../latch/latch
                           (standard cell gf180mcu_as_sc_mcu7t3v3__dfxtn_2)
  analog_top.sch / .sym    the macro: per-block AVDD ammeters VM*, bias_gen_s |
                           midref_div + ONE midref_buf | vrlo_ref + ic_source +
                           ramp_simple | four atop_cell. vrlo is made inside
                           (vrlo_ref, ../vrlo_ref, ADR 0018) and is not a macro port.

The sheets carry a one-line title, section headings, labels and the design
currents (intent.py) only. Descriptions, operating-point tables and
provenance belong in README.md / REPORT.md and the run records, not on the
drawings (CLAUDE.md, "Schematic drawings"); text copied from a block's own
drawing is filtered the same way.

check_equiv.py proves what changed against v5 (data/v5_ref/analog_top.spice):
both macros flattened to devices, nets matched by their pin sets.

    ./container.sh 'python3 analog_top_sch.py'
"""
import os
import re

import symbols
import intent as INT  # design currents written on the sheets (check_intent.py checks them)

BLOCK = os.path.dirname(os.path.abspath(__file__))
MS = os.path.dirname(BLOCK)
SYMDIR = {  # bare symbol name -> the directory xschemrc puts on the path
    # local presentation symbols (symbols.py) of the blocks midref_div, midref_buf,
    # vrlo_ref and latch: xschem descends into the blocks' own .sch
    "midref_div.sym": "Analog_top", "midref_buf.sym": "Analog_top",
    "vrlo_ref.sym": "Analog_top", "latch.sym": "Analog_top",
    "sw_s0.sym": "Analog_top", "sw_s1.sym": "Analog_top", "sw_s2.sym": "Analog_top",
    "comparator_d.sym": "Analog_top",
    "ramp_simple.sym": "ramp_simple", "ic_source.sym": "ic_source",   # the blocks' own (v6)
    "sample_seq.sym": "sample_seq",                                     # the block's own (v7)
    "bias_gen_s.sym": "Analog_top",
    "atop_cell.sym": "Analog_top", "analog_top.sym": "Analog_top",
}
# the block drawings the derived cells come from (read, never written)
SRC_CMP = os.path.join(MS, "comparator", "comparator.sch")
SRC_BG = os.path.join(MS, "bias_gen", "bias_gen.sch")
SRC_BG_SYM = os.path.join(MS, "bias_gen", "bias_gen.sym")
# the transistor-level switch views (sw_sch.py) are verified by sw_schematic.sh
SW_DONE = os.path.join(BLOCK, "data", "sw_schematic.done")
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
.subckt analog_top vin ramp_rst cnt_clk acq q0 q1 q2 q3 avdd avss dvdd dvss
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
XIC vramp pbias_r cnt_clk avdd_ramp avss dvdd dvss ic_source
XRAMP vramp ramp_rst vrlo avss ramp_simple
XC0 vin vramp s0_0 s1_0 s2_0 vref vref pbias0 q0 cnt_clk avdd_c0 avss dvdd dvss atop_cell
XC1 vin vramp s0_1 s1_1 s2_1 vref vref pbias1 q1 cnt_clk avdd_c1 avss dvdd dvss atop_cell
XC2 vin vramp s0_2 s1_2 s2_2 vref vref pbias2 q2 cnt_clk avdd_c2 avss dvdd dvss atop_cell
XC3 vin vramp s0_3 s1_3 s2_3 vref vref pbias3 q3 cnt_clk avdd_c3 avss dvdd dvss atop_cell
XSEQ acq cnt_clk s2_0 s2_1 s2_2 s2_3 s0_0 s0_1 s0_2 s0_3 s1_0 s1_1 s1_2 s1_3 dvdd dvss sample_seq
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
TOP_PORTS = ["vin", "ramp_rst", "cnt_clk", "acq"] + [f"q{k}" for k in range(4)] + ["avdd", "avss", "dvdd", "dvss"]
SEQ_PORTS = (["acq", "clk"] + [f"s{j}_{k}" for j in (2, 0, 1) for k in range(4)] + ["vdd", "vss"])
BG_PORTS = ["vdd", "vss", "icmp0", "icmp1", "icmp2", "icmp3", "iramp", "ivref", "ivrlo"]


def write_symbols():
    """Every sub-block symbol is drawn by symbols.py (function-shaped symbols);
    only the macro's own analog_top.sym stays a rectangle."""
    symbols.write_all()
    symbols.atop_cell(CELL_PORTS, left=["vfe", "vramp", "s0", "s1", "s2", "vref", "vbl", "ibias", "clk"],
                      right=["q"], top=["vdd", "dvdd"], bottom=["vss", "dvss"])
    box_symbol(os.path.join(BLOCK, "analog_top.sym"),
               "analog_top: the analog macro of the 8-bit bottom-plate ADC (v6: every analog block inside, "
               "one VDD/2 buffer for vref = vbl, the I/C-fed ramp); xschem descends into analog_top.sch "
               "(analog_top.spice is generated from it by schematic.sh)",
               left=TOP_PORTS[:4], right=TOP_PORTS[4:8], top=["avdd", "dvdd"], bottom=["avss", "dvss"],
               order=TOP_PORTS, label="analog_top", w=130, pitch=30)


def gallery():
    """symbol_gallery.sch: every sub-block symbol once, with what it stands for
    (documentation only; never netlisted)."""
    s = Sheet("symbol_gallery")
    items = [("bias_gen_s.sym", "XBG", 200, -400, "bias_gen_s: bias generator"),
             ("midref_div.sym", "XDIV", 640, -400, "midref_div: VDD/2 divider"),
             ("midref_buf.sym", "XVREF", 960, -400, "midref_buf: VDD/2 buffer"),
             ("vrlo_ref.sym", "XVRLO", 1340, -400, "vrlo_ref: VR_LO regulator"),
             ("ic_source.sym", "XIC", 1800, -400, "ic_source: I/C ramp current"),
             ("ramp_simple.sym", "XRAMP", 2300, -400, "ramp_simple: ramp capacitor + reset"),
             ("comparator_d.sym", "XCMP", 200, 0, "comparator_d: comparator"),
             ("latch.sym", "XFF", 640, 0, "latch: D flip-flop"),
             ("sw_s0.sym", "XS0", 960, 0, "sw_s0 / sw_s1: TG switch"),
             ("sw_s2.sym", "XS2", 1300, 0, "sw_s2: NMOS switch"),
             ("atop_cell.sym", "XC0", 1860, 140, "atop_cell: unit cell")]
    for sym, name, x, y, cap in items:
        s.block_inst(sym, name, x, y)
        s.texts.append("T {%s} %d %d 0 0 0.3 0.3 {layer=13}" % (cap, x - 140, y + 180 if sym != "atop_cell.sym" else y + 260))
    s.text("ANALOG_TOP  -  SUB-BLOCK SYMBOLS", 0, -700, T_TITLE)
    s.write(os.path.join(BLOCK, "symbol_gallery.sch"), "symbol_gallery", 0, 500)


def ports_column(s, ports, kinds, y0, pitch):
    for k, p in enumerate(ports):
        y = y0 + pitch * k
        s.port(kinds.get(p, "ipin"), 40, y, p, k + 1)
        s.stub((40, y), p, dx=40)


# ------------------------------------------------- cells derived from blocks

def text_of(ch):
    """(text, x, y) of a T object, or None for any other object."""
    m = re.match(r"T \{(.*)\} (-?\d+) (-?\d+) ", ch, re.S)
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else None


# the source drawings' text kept on the derived sheets: section headings and
# role labels; everything else there (bench notes, op tables) is dropped
CMP_KEEP = {"PMOS 5T OTA", "starved inverter", "output inverter"}
BG_KEEP = {"STARTUP", "CORE", "SINKS (nb)  /  SOURCES (pb)"}
# bias_gen.sch's output current tags by position -> the design output (intent.py);
# (1348, -820) was XOB's (removed in v5)
BG_OUT_TAG = {(1028, -262): "icmp", (1188, -262): "icmp", (1348, -262): "icmp", (1508, -262): "icmp",
              (1668, -262): "iramp", (1108, -820): "ivref", (1348, -820): None}


def cmp_sheet():
    """comparator_d.sch from ../comparator/comparator.sch: every device and wire
    as drawn there, the device current markers at the macro's bias (intent.py);
    pbias -> ibias (port); the no-connect ports clk / nbias removed; XREFP added
    in the PDK symbol format the other ten devices use (so it carries the same
    S/D geometry template)."""
    out, ndrop, nmark = [], 0, 0
    xy2dev = {xy: d for d, xy in INT.CMP.MARKER_XY.items()}
    for ch in chunks(SRC_CMP):
        if ch.startswith("C {devices/ipin.sym}") and re.search(r"lab=(clk|nbias)\}", ch):
            ndrop += 1
            continue
        if ch.startswith("L 4 "):
            continue                          # the frames of the bench sheet's note boxes
        t = text_of(ch)
        if t:
            if (t[1], t[2]) in xy2dev:
                ch = T(INT.cmp_marker(xy2dev[(t[1], t[2])]), t[1], t[2], 0.28, layer=4)   # bench -> macro current
                nmark += 1
            elif t[0] not in CMP_KEEP:
                continue
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
    out.append(T("%g uA" % INT.BIAS_UA["icmp"], -120, -800, 0.28, layer=4))
    out.append(T("COMPARATOR_D  -  comparator + pbias diode XREFP (current input ibias)", 140, -1000, T_SUB * 1.2))
    with open(os.path.join(BLOCK, "comparator_d.sch"), "w", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def bg_text(ch):
    """bias_gen.sch's text as bias_gen_s.sch carries it: section headings, the
    R / C values, the output currents at their design values (intent.py) and the
    core currents; None drops it (bench notes, op tables)."""
    txt, x, y = text_of(ch)
    if (x, y) in BG_OUT_TAG:
        k = BG_OUT_TAG[(x, y)]
        return T("%g uA" % INT.BIAS_UA[k], x, y, T_NOTE, layer=4) if k else None
    if txt in BG_KEEP or txt.startswith("R = "):
        return ch
    m = re.match(r"([\d.]+) uA$", txt)
    if m and y == -770:                       # core: the block's bench current, once per branch (PMOS row)
        return T("%.2f uA" % float(m.group(1)), x, y, T_NOTE, layer=4)
    if txt.startswith("C = "):
        return T(txt, x, y, T_NOTE, layer=4)
    return None


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
    nt = sum(1 for c in out if text_of(c))
    out = [c for c in out if not c.startswith("B 4 ")]          # the bench sheet's note box
    out = [bg_text(c) if text_of(c) else c for c in out]
    out = [c for c in out if c is not None]
    assert sum(1 for c in out if text_of(c)) < nt, "bias_gen.sch text not filtered"
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
    out.append(T("%g uA" % INT.BIAS_UA["ivrlo"], x + 28, -820, T_NOTE, layer=4))
    out.append(T("BIAS_GEN_S  -  constant-gm bias generator, current outputs (bias_gen - XOB + XOL)",
                 40, -1300, T_SUB * 1.2))
    out.append(T("layout: one PMOS row over one NMOS row, even finger counts, common centroid",
                 40, -1240, T_NOTE))
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
    # values next to the devices: the hold capacitor and the comparator bias current
    s.text("C_S 54.52 fF", PX + 30, -640, T_NOTE, layer=4)
    s.text("%g uA" % INT.BIAS_UA["icmp"], cp["ibias"][0] + 10, cp["ibias"][1] - 75, T_NOTE, layer=4)
    s.text("ATOP_CELL  -  one sampling / conversion cell", 40, -1220, T_TITLE)
    s.frame(250, -1120, 640, -200, "S0/S1/S2 COMPLEMENTS")
    s.frame(700, -1120, 1360, -200, "SWITCHES + HOLD CAP")
    s.frame(1380, -1120, 2300, -200, "COMPARATOR (comparator_d) + LATCH")
    return s


# ----------------------------------------------------------------------- macro

def top_sheet(sc):
    dv = sc["dev"]
    s = Sheet("analog_top")
    kinds = {f"q{k}": "opin" for k in range(4)}
    kinds.update({p: "iopin" for p in ("avdd", "avss", "dvdd", "dvss")})
    ports_column(s, TOP_PORTS, kinds, -1240, 45)
    RAIL = -1380
    xs = {"VMBG": 520, "VMREF": 1060, "VMVRLO": 1580, "VMRAMP": 1880}
    for k in range(4):
        xs[f"VMC{k}"] = 2740 + 620 * k
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
            out = pin.rstrip("0123456789")       # icmp0..3 -> icmp: the design current on the wire
            s.text("%g uA" % INT.BIAS_UA[out], p[pin][0] + 8, p[pin][1] - 22, 0.3, layer=4)
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
    # the I/C current source (../ic_source, descended): bias_gen_s's ramp sink into its
    # bias diode, the count clock, AVDD through VMRAMP, its phase generator on DVDD
    d = dv["XIC"]
    pi = s.block_inst("ic_source.sym", "XIC", 1800, -1080)
    iout, ibias, clk, avdd_, avss_, dvdd_, dvss_ = d["nodes"]
    s.stub(pi["ibias"], ibias, dx=-60)
    s.stub(pi["clk"], clk, dx=-60)
    s.stub(pi["iout"], iout, dx=60)
    s.stub(pi["avdd"], avdd_, dx=0, dy=-40)
    s.stub(pi["dvdd"], dvdd_, dx=0, dy=-40, right=True)
    s.stub(pi["avss"], avss_, dx=0, dy=40)
    s.stub(pi["dvss"], dvss_, dx=0, dy=40, right=True)
    s.text("%g uA" % INT.RAMP_UA, pi["iout"][0] + 8, pi["iout"][1] - 22, 0.3, layer=4)
    # the ramp capacitor + reset switch (../ramp_simple, descended)
    d = dv["XRAMP"]
    pr = s.block_inst("ramp_simple.sym", "XRAMP", 2100, -760)
    vramp, rst, vrlo, vss = d["nodes"]
    s.stub(pr["rst"], rst, dx=-60)
    s.stub(pr["vrlo"], vrlo, dx=-60)
    s.stub(pr["vramp"], vramp, dx=60)
    s.stub(pr["vss"], vss, dx=0, dy=40)
    # cells
    for k in range(4):
        name = f"XC{k}"
        d = dv[name]
        x = 2740 + 620 * k
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
    # the sampling sequencer (../sample_seq, descended): the count clock and acq in,
    # the twelve switch controls out, on DVDD
    d = dv["XSEQ"]
    ps = s.block_inst("sample_seq.sym", "XSEQ", 3680, 40)
    for pin, net in zip(SEQ_PORTS, d["nodes"]):
        if pin == "vdd":
            s.stub(ps[pin], net, dx=0, dy=-40, right=True)
        elif pin == "vss":
            s.stub(ps[pin], net, dx=0, dy=40, right=True)
        elif pin in ("acq", "clk"):
            s.stub(ps[pin], net, dx=-60)
        else:
            s.stub(ps[pin], net, dx=60)
    s.frame(2480, -380, 4880, 420, "SAMPLING SEQUENCER (DVDD)")
    s.frame(320, -1300, 760, -480, "BIAS")
    s.frame(800, -1300, 1440, -480, "REF (VDD/2): vref = vbl")
    s.frame(1480, -1300, 2440, -480, "RAMP (I/C source) + VR_LO")
    s.frame(2480, -1300, 4880, -480, "FOUR CELLS")
    s.text("ANALOG_TOP  -  analog macro: four bottom-plate cells on one shared ramp", 40, -1560, T_TITLE)
    return s


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
    bg_sheet()
    cell_sheet(sc["atop_cell"]).write(os.path.join(BLOCK, "atop_cell.sch"), "atop_cell", 40, 0)
    top_sheet(sc["analog_top"]).write(os.path.join(BLOCK, "analog_top.sch"), "analog_top", 40, -120)
    print("REPORT: wrote comparator_d, bias_gen_s (derived from the block drawings), atop_cell, "
          "analog_top .sch/.sym (midref_div, midref_buf, vrlo_ref, latch, ic_source, ramp_simple, sw_s0/1/2: "
          "descended)")


if __name__ == "__main__":
    main()
