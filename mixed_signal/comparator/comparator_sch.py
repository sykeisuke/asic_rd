#!/usr/bin/env python3
"""Emit the xschem views comparator.sch and comparator.sym from the
generated deck comparator.spice.

The topology and the placement are hand-authored here (stages 1-3 at the
positions of comparator_bkp/comparator_10dev/comparator_sch.py, so a macro generator that copies
that drawing can copy this one the same way); every device's model, W, L and
nf is parsed from the deck, so a re-derivation is one regeneration and the
drawing cannot drift from the netlist. check-schematic.awk (run by
./schematic.sh) proves the netlist xschem writes from the drawing equals the
deck device for device, ports in order.

Topology (12 devices, ports `inp inn dout clk vdd vss nbias pbias`, clk and
nbias are no-connects kept by the cell's port list):

    XTAIL                 pbias mirror, vdd -> tail
    XINP / XINN           PMOS input pair, wells on vdd: inp = the plate, inn = VREF
    XLOADD / XLOADM       NMOS mirror load; outa = drain of XINN / XLOADM
    XBST                  pbias mirror, vdd -> bst (starve current)
    XBUF2 / XBUF1         starved first inverter, outa -> outb
    XBUF4 / XBUF3         inverter, outb -> outc
    XBUF6 / XBUF5         output inverter (added), outc -> dout

The MOS instances are written in the deck's line order, so the netlist xschem
writes lists the devices in the same order as comparator.spice (ngspice
Monte Carlo draws follow the flattened device order).

Run:  ./container.sh 'python3 comparator_sch.py'
Out:  comparator.sch, comparator.sym
Everything (views + netlist-back check + renders + testbenches): ./schematic.sh
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
DECK = BLOCK / (sys.argv[1] if len(sys.argv) > 1 else "comparator.spice")
OUT = BLOCK / "comparator.sch"
OUT_SYM = BLOCK / "comparator.sym"
PORTS = ["inp", "inn", "dout", "clk", "vdd", "vss", "nbias", "pbias"]

sys.path.insert(0, str(BLOCK))
import intent as I  # noqa: E402  design-intent currents and text positions (the one source)

PARAM = re.compile(r"(\w+)\s*=\s*(\{[^}]*\}|'[^']*'|[\w.]+)")
EXPECTED = ["XTAIL", "XINP", "XINN", "XLOADD", "XLOADM", "XBST",
            "XBUF2", "XBUF1", "XBUF4", "XBUF3", "XBUF6", "XBUF5"]


def parse(path: Path):
    devs, order, others, ports = {}, [], [], None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        tok = line.split()
        head = tok[0].upper()
        if head == ".SUBCKT":
            ports = [t.lower() for t in tok[2:]]
            continue
        if head.startswith("."):
            continue
        if head.startswith("X") and len(tok) >= 6:
            p = {k.lower(): v for k, v in PARAM.findall(" ".join(tok[6:]))}
            devs[head] = {"model": tok[5], "l": p.get("l"), "w": p.get("w"),
                          "nf": p.get("nf", "1"), "m": p.get("m", "1")}
            order.append(head)
        else:
            others.append(head)
    return devs, order, others, ports


DEV, ORDER, OTHERS, DECK_PORTS = parse(DECK)
missing = [n for n in EXPECTED if n not in DEV]
extra = sorted(set(DEV) - set(EXPECTED)) + OTHERS
if missing or extra:
    raise SystemExit(f"{DECK.name}: the drawing is the 12-device topology; "
                     f"missing {missing or '-'}, not drawn {extra or '-'}")
if DECK_PORTS != PORTS:
    raise SystemExit(f"{DECK.name}: port list {DECK_PORTS} is not the drawing's {PORTS}")

# ------------------------------------------------------------------ geometry
# xschem: y grows downward; MOS symbols (gf180 pfet_03v3 / nfet_03v3) have
# G at (-20, 0), B at (+20, 0), the top terminal at (+20, -30) and the bottom
# one at (+20, +30): pfet S top / D bottom, nfet D top / S bottom. A flipped
# symbol mirrors x.
VDD_Y, VSS_Y = -880, -360
X_L, X_R = 160, 1460

wires: list[tuple[int, int, int, int]] = []
pins_at: list[tuple[int, int]] = []          # instance pin locations, for splitting
inst: list[str] = []
mos_inst: dict[str, str] = {}
texts: list[str] = []


def W(*pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        wires.append((x1, y1, x2, y2))


MOS_ATTR = ('ad="\'int((nf+1)/2) * W/nf * 0.18u\'"\n'
            'pd="\'2*int((nf+1)/2) * (W/nf + 0.18u)\'"\n'
            'as="\'int((nf+2)/2) * W/nf * 0.18u\'"\n'
            'ps="\'2*int((nf+2)/2) * (W/nf + 0.18u)\'"\n'
            'nrd="\'0.18u / W\'" nrs="\'0.18u / W\'"\n'
            'sa=0 sb=0 sd=0')


def mos(name, x, y, flip=False):
    """Place device `name` (deck name, e.g. XTAIL) with origin (x, y).
    Returns (top, gate, body, bottom) terminal coordinates."""
    d = DEV[name]
    kind = "pfet_03v3" if d["model"].startswith("p") else "nfet_03v3"
    s = -1 if flip else 1
    top, bot = (x + 20 * s, y - 30), (x + 20 * s, y + 30)
    gate, body = (x - 20 * s, y), (x + 20 * s, y)
    pins_at.extend([top, bot, gate, body])
    mos_inst[name] = (f"C {{symbols/{kind}.sym}} {x} {y} 0 {1 if flip else 0} {{name={name[1:]}\n"
                      f"L={d['l']} W={d['w']} nf={d['nf']} m={d['m']}\n{MOS_ATTR} "
                      f"model={kind} spiceprefix=X}}")
    return top, gate, body, bot


_lab = [0]


def lab(x, y, net, wire_to_right):
    """A net label whose pin is at (x, y); the wire leaves to the right
    (label text on the left) or to the left (label text on the right)."""
    _lab[0] += 1
    pins_at.append((x, y))
    inst.append(f"C {{devices/lab_pin.sym}} {x} {y} 0 {0 if wire_to_right else 1} "
                f"{{name=l{_lab[0]} sig_type=std_logic lab={net}}}")


def pin(kind, x, y, net, flip=False):
    pins_at.append((x, y))
    inst.append(f"C {{devices/{kind}.sym}} {x} {y} 0 {1 if flip else 0} {{name=p{net} lab={net}}}")


def T(s, x, y, size=0.4, layer=None):
    attr = f"layer={layer}" if layer is not None else ""
    texts.append(f"T {{{s}}} {x} {y} 0 0 {size} {size} {{{attr}}}")


# rails
W((X_L, VDD_Y), (X_R, VDD_Y))
W((X_L, VSS_Y), (X_R, VSS_Y))
pin("iopin", X_L, VDD_Y, "vdd")
pin("iopin", X_L, VSS_Y, "vss")

# ---- stage 1: PMOS 5T (as comparator_bkp/comparator_10dev/comparator_sch.py) -----------------
t_top, t_g, t_b, t_bot = mos("XTAIL", 460, -800)
W((t_top[0], VDD_Y), t_top)
W(t_bot, (480, -740))
W(t_b, (520, -800)); lab(520, -800, "vdd", False)
W((240, -800), t_g)
pin("ipin", 240, -800, "pbias")
W((360, -740), (480, -740), (580, -740))
lab(300, -740, "tail", True); W((300, -740), (360, -740))
p_top, p_g, p_b, p_bot = mos("XINP", 340, -680)
n_top, n_g, n_b, n_bot = mos("XINN", 600, -680, flip=True)
W((360, -740), p_top)
W((580, -740), n_top)
W((240, -680), p_g); pin("ipin", 240, -680, "inp")
W(n_g, (700, -680)); pin("ipin", 700, -680, "inn", flip=True)
W(p_b, (400, -680)); lab(400, -680, "vdd", False)
W(n_b, (540, -680)); lab(540, -680, "vdd", True)
ld_top, ld_g, ld_b, ld_bot = mos("XLOADD", 380, -480, flip=True)
lm_top, lm_g, lm_b, lm_bot = mos("XLOADM", 560, -480)
W(p_bot, (360, -560), ld_top)
W(n_bot, (580, -600), lm_top)
W(ld_g, (480, -480), lm_g)
W((480, -480), (480, -560), (360, -560))           # diode: gates to `left`
lab(300, -560, "left", True); W((300, -560), (360, -560))
W(ld_b, (320, -480)); lab(320, -480, "vss", True)
W(lm_b, (620, -480)); lab(620, -480, "vss", False)
W(ld_bot, (360, VSS_Y))
W(lm_bot, (580, VSS_Y))

OUTA_Y = -600
GX1 = 800
W((580, OUTA_Y), (680, OUTA_Y), (GX1, OUTA_Y))
lab(680, -640, "outa", True); W((680, -640), (680, OUTA_Y))

# ---- stage 2: starved first inverter ---------------------------------------
b_top, b_g, b_b, b_bot = mos("XBST", 840, -800)
u2_top, u2_g, u2_b, u2_bot = mos("XBUF2", 840, -680)
u1_top, u1_g, u1_b, u1_bot = mos("XBUF1", 840, -520)
W((b_top[0], VDD_Y), b_top)
W(b_bot, (860, -740), u2_top)
lab(920, -740, "bst", False); W((860, -740), (920, -740))
W((780, -800), b_g); lab(780, -800, "pbias", True)
W(b_b, (900, -800)); lab(900, -800, "vdd", False)
W(u2_b, (900, -680)); lab(900, -680, "vdd", False)
W(u1_b, (900, -520)); lab(900, -520, "vss", False)
W(u2_g, (GX1, -680), (GX1, OUTA_Y), (GX1, -520), u1_g)
W(u2_bot, (860, -600), u1_top)
W(u1_bot, (860, VSS_Y))

# ---- stage 3: inverter, outb -> outc ----------------------------------------
GX2 = 1020
o4_top, o4_g, o4_b, o4_bot = mos("XBUF4", 1060, -680)
o3_top, o3_g, o3_b, o3_bot = mos("XBUF3", 1060, -520)
W((860, -600), (960, -600), (GX2, -600))           # outb
lab(960, -640, "outb", True); W((960, -640), (960, -600))
W((GX2 + 20, -680), (GX2, -680), (GX2, -600), (GX2, -520), (GX2 + 20, -520))
W((o4_top[0], VDD_Y), o4_top)
W(o4_bot, (1080, -600), o3_top)
W(o3_bot, (1080, VSS_Y))
W(o4_b, (1120, -680)); lab(1120, -680, "vdd", False)
W(o3_b, (1120, -520)); lab(1120, -520, "vss", False)

# ---- stage 4: output inverter (added), outc -> dout -------------------------
GX3 = 1240
o6_top, o6_g, o6_b, o6_bot = mos("XBUF6", 1280, -680)
o5_top, o5_g, o5_b, o5_bot = mos("XBUF5", 1280, -520)
W((1080, -600), (1180, -600), (GX3, -600))         # outc
lab(1180, -640, "outc", True); W((1180, -640), (1180, -600))
W((GX3 + 20, -680), (GX3, -680), (GX3, -600), (GX3, -520), (GX3 + 20, -520))
W((o6_top[0], VDD_Y), o6_top)
W(o6_bot, (1300, -600), o5_top)
W(o5_bot, (1300, VSS_Y))
W(o6_b, (1340, -680)); lab(1340, -680, "vdd", False)
W(o5_b, (1340, -520)); lab(1340, -520, "vss", False)
W((1300, -600), (1420, -600)); pin("opin", 1420, -600, "dout")

# no-connect ports (the cell's port list keeps them)
pin("ipin", 240, -280, "clk")
pin("ipin", 240, -240, "nbias")

# ------------------------------------------------------------------ text
# Text only (no effect on the netlist): the title, the layout line, the
# section headings, the two net notes, the design current next to each device
# (intent.py, at the macro's bias) and the not-connected note
# (root CLAUDE.md, "Schematic drawings"). Positions are intent.py's.
T("COMPARATOR  -  continuous-time comparator, plate on inp, currents at I_B = %g uA"
  % I.MACRO_I_B_UA, *I.TITLE_XY, 0.7)
T("layout: XINP / XINN and XLOADD / XLOADM interdigitated, common centroid, dummies at both ends",
  *I.LAYOUT_XY, 0.4)
for dev, (x, y) in I.MARKER_XY.items():
    if I.drawn(dev):
        T(I.marker(dev), x, y, 0.28, 4)
T(I.NOTES[0], 150, -660, 0.3)
T(I.NOTES[1], 705, -662, 0.3)
T(I.HEADINGS[0], 320, -412, 0.4)
T(I.HEADINGS[1], 760, -412, 0.4)
T(I.HEADINGS[2], 1080, -412, 0.4)
T("clk, nbias: not connected", 290, -296, 0.35)


# ------------------------------------------------------------------ split
# xschem only connects wires at their end points: split every segment at
# any wire end point or instance pin lying strictly inside it.
def split(segs, points):
    out = []
    for x1, y1, x2, y2 in segs:
        if (x1, y1) == (x2, y2):
            continue
        cuts = {(x1, y1), (x2, y2)}
        for px, py in points:
            if x1 == x2 == px and min(y1, y2) < py < max(y1, y2):
                cuts.add((px, py))
            elif y1 == y2 == py and min(x1, x2) < px < max(x1, x2):
                cuts.add((px, py))
        if x1 != x2 and y1 != y2:
            raise SystemExit(f"diagonal wire {x1},{y1} -> {x2},{y2}")
        pts = sorted(cuts, key=lambda p: (p[0], p[1]))
        out += [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]
    return sorted(set(out))


ends = [(x, y) for s in wires for (x, y) in ((s[0], s[1]), (s[2], s[3]))]
segs = split(wires, ends + pins_at)

body = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
body += [f"N {x1} {y1} {x2} {y2} {{}}" for x1, y1, x2, y2 in segs]
body += texts
body += [mos_inst[n] for n in ORDER]          # the deck's device order
body += inst
OUT.write_text("\n".join(body) + "\n")

# ------------------------------------------------------------------ symbol
# the shape of comparator_bkp/comparator_10dev/comparator.sym: pin names, @name, @symname only
SYM_PINS = [("inp", -100, -60, "in"), ("inn", -100, -30, "in"), ("dout", 100, -45, "out"),
            ("clk", -100, 0, "in"), ("vdd", 0, -120, "inout"), ("vss", 0, 120, "inout"),
            ("nbias", -100, 30, "in"), ("pbias", -100, 60, "in")]
assert [p[0] for p in SYM_PINS] == PORTS
sym = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
       'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=x1"\n}', "V {}", "S {}", "E {}",
       "L 4 -80 -100 80 -100 {}", "L 4 80 -100 80 100 {}", "L 4 80 100 -80 100 {}", "L 4 -80 100 -80 -100 {}"]
for n, x, y, _ in SYM_PINS:
    if x < 0:
        sym.append(f"L 4 -100 {y} -80 {y} {{}}")
    elif x > 0:
        sym.append(f"L 4 80 {y} 100 {y} {{}}")
    else:
        sym.append(f"L 4 0 {y} 0 {y + 20 if y < 0 else y - 20} {{}}")
for n, x, y, d in SYM_PINS:
    sym.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={n} dir={d}}}")
for n, x, y, _ in SYM_PINS:
    tx, ty = (-74, y - 6) if x < 0 else (44, y - 6) if x > 0 else (6, y + 6 if y < 0 else y - 16)
    sym.append(f"T {{{n}}} {tx} {ty} 0 0 0.3 0.3 {{}}")
sym += ["T {@name} -80 -136 0 0 0.4 0.4 {}", "T {@symname} -70 72 0 0 0.4 0.4 {}"]
OUT_SYM.write_text("\n".join(sym) + "\n")

ntext = len(texts)
print(f"REPORT: wrote {OUT.name} and {OUT_SYM.name} from {DECK.name}: {len(DEV)} devices, "
      f"{len(segs)} wire segments, {ntext} texts")
print(f"sheet_texts = {ntext}")
