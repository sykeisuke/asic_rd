#!/usr/bin/env python3
"""Schematic figure of comparator.spice, drawn with schemdraw on white.

Every device name, model, W, L and nf on the drawing is parsed out of
``comparator.spice`` (or the deck named on the command line), so the picture
cannot drift from the netlist; only the placement is hand-authored. The
xschem drawing ``comparator.sch`` (emitted by ``comparator_sch.py``) is the
editable schematic that netlists back to the deck; this file is the
rendered view for the README. ``./schematic.sh`` regenerates both.

Topology: PMOS 5T (XTAIL, XINP/XINN, XLOADD/XLOADM), then the starved
first inverter (XBST from pbias, XBUF2 / XBUF1), then the output inverter
(XBUF4 / XBUF3). No clamp, no replica, no explicit capacitor.

Run:  ./container.sh 'python3 comparator_schematic.py [deck]'
Out:  assets/comparator_schematic.png
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

BLOCK = Path(__file__).resolve().parent
DECK = BLOCK / (sys.argv[1] if len(sys.argv) > 1 else "comparator.spice")
OUT = BLOCK / "assets" / "comparator_schematic.png"

INK, INK2, MUTED = "#1f2328", "#57606a", "#8c959f"
REF = "#2a78d6"
NODE = "#1baf7a"

PARAM = re.compile(r"(\w+)\s*=\s*(\{[^}]*\}|'[^']*'|[\w.]+)")
EXPECTED = ("XINP", "XINN", "XLOADD", "XLOADM", "XTAIL",
            "XBST", "XBUF1", "XBUF2", "XBUF3", "XBUF4")


def parse(path: Path):
    devices, others, ports, comments = {}, [], [], []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("*"):
            comments.append(line.lstrip("* ").rstrip())
            continue
        tok = line.split()
        head = tok[0].upper()
        if head == ".SUBCKT":
            ports = tok[2:]
        elif head.startswith("."):
            continue
        elif head.startswith("X") and len(tok) >= 6:
            p = {k.lower(): v for k, v in PARAM.findall(" ".join(tok[6:]))}
            devices[head] = {"nodes": tok[1:5], "model": tok[5], "l": p.get("l", "?"),
                             "w": p.get("w", "?"), "nf": p.get("nf", "1")}
        else:
            others.append(head)
    return devices, others, ports, comments


DEV, OTHERS, PORTS, COMMENTS = parse(DECK)
missing = [n for n in EXPECTED if n not in DEV]
extra = sorted(set(DEV) - set(EXPECTED)) + OTHERS
if missing or extra:
    raise SystemExit(f"{DECK.name}: the drawing is the 10-device topology; "
                     f"missing {missing or '-'}, not drawn {extra or '-'}")

# ------------------------------------------------------------------ helpers
RAIL_L, RAIL_R = -4.5, 19.0
GND_Y = -9.0
FS_REF, FS_NODE, FS_NOTE = 9.5, 9.5, 8.5


def text(d, xy, s, halign="left", valign="center", size=FS_NOTE, color=INK):
    d += elm.Label().at(xy).theta(0).label(s, loc="center", halign=halign, valign=valign,
                                           fontsize=size, color=color)


def wire(d, *pts):
    for a, b in zip(pts, pts[1:]):
        d += elm.Line().at(a).to(b)


def dot(d, xy):
    d += elm.Dot().at(xy).theta(0)


def fet(d, name, xy, gate_left=False, ref_at=None, halign="left"):
    """Place by the top terminal: source for a pfet, drain for an nfet.
    The gate is 1.37 to the right (or left) and 0.75 below the top terminal;
    the bottom terminal is 1.5 below the top one."""
    kind = DEV[name]["model"]
    el = elm.PFet() if kind.startswith("p") else elm.NFet()
    if gate_left:
        el = el.reverse()
    d += el.at(xy).theta(0)
    if ref_at is not None:
        text(d, ref_at, name, halign=halign, size=FS_REF, color=REF)


def terminal(d, xy, name, halign="left", dxy=(0.28, 0.0)):
    dot(d, xy)
    text(d, (xy[0] + dxy[0], xy[1] + dxy[1]), name, halign=halign, size=FS_NODE, color=NODE)


def node(d, xy, name, halign="left"):
    text(d, xy, name, halign=halign, size=FS_NODE, color=NODE)


# ------------------------------------------------------------------ drawing
d = schemdraw.Drawing(show=False)

# rails
wire(d, (RAIL_L, 0), (RAIL_R, 0))
wire(d, (RAIL_L, GND_Y), (RAIL_R, GND_Y))
d += elm.Ground().at((RAIL_L + 0.8, GND_Y)).theta(0)
node(d, (RAIL_L, 0.32), "vdd")
node(d, (RAIL_L + 1.1, GND_Y - 0.45), "vss")

# tail, its gate on the left where pbias enters
XT = 2.5
fet(d, "XTAIL", (XT, -0.9), gate_left=True, ref_at=(XT + 0.45, -1.65))
wire(d, (XT, 0), (XT, -0.9))
wire(d, (XT, -2.4), (XT, -2.8))
wire(d, (0.0, -2.8), (5.0, -2.8))
dot(d, (XT, -2.8))
node(d, (XT + 0.2, -2.55), "tail")
wire(d, (XT - 1.37, -1.65), (-2.4, -1.65))
terminal(d, (-2.4, -1.65), "pbias", halign="right", dxy=(-0.28, 0))

# input pair: inp = VBL on the left, inn = top plate on the right
fet(d, "XINP", (0.0, -3.2), gate_left=True, ref_at=(-0.2, -5.0), halign="right")
fet(d, "XINN", (5.0, -3.2), ref_at=(6.6, -4.6))
wire(d, (0.0, -2.8), (0.0, -3.2))
wire(d, (5.0, -2.8), (5.0, -3.2))
wire(d, (-1.37, -3.95), (-2.4, -3.95))
terminal(d, (-2.4, -3.95), "inp = VBL", halign="right", dxy=(-0.28, 0))
wire(d, (6.37, -3.95), (7.2, -3.95))
terminal(d, (7.2, -3.95), "inn = top plate")

# mirror load
fet(d, "XLOADD", (0.0, -6.2), ref_at=(-0.55, -6.95), halign="right")
fet(d, "XLOADM", (5.0, -6.2), gate_left=True, ref_at=(5.55, -6.95))
wire(d, (0.0, -4.7), (0.0, -6.2))
wire(d, (5.0, -4.7), (5.0, -6.2))
wire(d, (1.37, -6.95), (3.63, -6.95))
wire(d, (2.5, -6.95), (2.5, -5.6), (0.0, -5.6))
dot(d, (2.5, -6.95))
dot(d, (0.0, -5.6))
node(d, (-0.25, -5.6), "left", halign="right")
wire(d, (0.0, -7.7), (0.0, GND_Y))
wire(d, (5.0, -7.7), (5.0, GND_Y))

# outa -> starved first inverter (XBST over XBUF2 / XBUF1) -> output inverter
TAP = -5.4
X1, X2 = 11.0, 15.0
wire(d, (5.0, TAP), (X1 - 1.37, TAP))
dot(d, (5.0, TAP))
node(d, (5.2, TAP + 0.25), "outa")

fet(d, "XBST", (X1, -0.6), ref_at=(X1 - 0.55, -1.35), halign="right")
wire(d, (X1, 0), (X1, -0.6))
wire(d, (X1, -2.1), (X1, -2.4))
node(d, (X1 + 0.2, -2.25), "bst")
wire(d, (X1 + 1.37, -1.35), (X1 + 2.0, -1.35))
node(d, (X1 + 2.15, -1.35), "pbias")
fet(d, "XBUF2", (X1, -2.4), gate_left=True, ref_at=(X1 + 0.55, -3.15))
fet(d, "XBUF1", (X1, -5.3), gate_left=True, ref_at=(X1 + 0.55, -6.05))
wire(d, (X1, -3.9), (X1, -5.3))
wire(d, (X1, -6.8), (X1, GND_Y))
wire(d, (X1 - 1.37, -3.15), (X1 - 1.37, -6.05))
dot(d, (X1 - 1.37, TAP))
fet(d, "XBUF4", (X2, -2.4), gate_left=True, ref_at=(X2 + 0.55, -3.15))
fet(d, "XBUF3", (X2, -5.3), gate_left=True, ref_at=(X2 + 0.55, -6.05))
wire(d, (X2, 0), (X2, -2.4))
wire(d, (X2, -3.9), (X2, -5.3))
wire(d, (X2, -6.8), (X2, GND_Y))
wire(d, (X2 - 1.37, -3.15), (X2 - 1.37, -6.05))
OUTB = -4.6
wire(d, (X1, OUTB), (X2 - 1.37, OUTB))
dot(d, (X1, OUTB))
dot(d, (X2 - 1.37, OUTB))
node(d, (X1 + 0.2, OUTB + 0.25), "outb")
wire(d, (X2, OUTB), (RAIL_R - 1.2, OUTB))
dot(d, (X2, OUTB))
terminal(d, (RAIL_R - 1.2, OUTB), "dout")

text(d, (2.5, GND_Y + 0.6), "PMOS 5T OTA", halign="center", size=9, color=INK2)
text(d, (X1 - 2.4, GND_Y + 0.6), "starved inverter", halign="center", size=9, color=INK2)
text(d, (X2 - 2.0, GND_Y + 0.6), "output inverter", halign="center", size=9, color=INK2)

# ------------------------------------------------------------------ table
ROWS = [
    ("XINP, XINN", "input pair (wells on vdd)"), ("XLOADD, XLOADM", "mirror load"),
    ("XTAIL", "tail, pbias slave"), ("XBST", "starve current, pbias slave"),
    ("XBUF2 / XBUF1", "starved first inverter"), ("XBUF4 / XBUF3", "output inverter"),
]


def size_of(names):
    out = []
    for n in names:
        v = DEV[n]
        out.append(f"{v['model']} W={v['w']} L={v['l']}" + (f" nf={v['nf']}" if v["nf"] != "1" else ""))
    return out


y0 = GND_Y - 1.3
text(d, (RAIL_L, y0), f"{DECK.name}   .subckt cmp {' '.join(PORTS)}   (clk, nbias: no-connect)",
     size=9, color=INK)
y = y0 - 0.75
col = [RAIL_L, RAIL_L + 4.6, RAIL_L + 10.0]
for names, role in ROWS:
    devs = [n.strip() for n in re.split(r"[,/]", names)]
    sizes = size_of(devs)
    if len(set(sizes)) == 1:
        sizes = sizes[:1]
    text(d, (col[0], y), names, size=FS_NOTE, color=REF)
    text(d, (col[1], y), role, size=FS_NOTE, color=INK2)
    text(d, (col[2], y), ";  ".join(sizes), size=FS_NOTE, color=INK)
    y -= 0.62

text(d, (RAIL_L, 1.3),
     "comparator: PMOS 5T + starved inverter + output inverter for the true bottom-plate cell. "
     "inp = VBL = VDD/2, inn = the MIM top plate; dout falls when inn rises through inp.",
     size=9.5, color=INK)

OUT.parent.mkdir(exist_ok=True)
d.save(str(OUT), dpi=170)

# flatten onto an opaque white background (schemdraw may leave it transparent)
from PIL import Image  # noqa: E402

im = Image.open(OUT).convert("RGBA")
bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
bg.alpha_composite(im)
bg.convert("RGB").save(OUT)
print(f"REPORT: wrote {OUT.relative_to(BLOCK)} from {DECK.name}")
