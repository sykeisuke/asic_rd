#!/usr/bin/env python3
"""Emit the xschem schematic comparator.sch from the comparator.spice deck.

The topology and the placement are hand-authored here; every device's model,
W, L and nf is parsed from the deck, so a re-sizing is one regeneration and
the drawing cannot drift from the netlist. The terminal nets are taken from
the placement (that is what the drawing *is*) and the netlist-back check
(check-schematic.awk, run by ./schematic.sh or scripts/run-schematic.sh)
proves they match the deck device for device.

Topology (10 devices, ports `inp inn dout clk vdd vss nbias pbias`, clk and
nbias are no-connects kept by the unit-cell contract):

    XTAIL                 pbias mirror, vdd -> tail
    XINP / XINN           PMOS input pair, wells on vdd: inp = VBL, inn = top plate
    XLOADD / XLOADM       NMOS mirror load; outa = drain of XINN / XLOADM
    XBST                  pbias mirror, vdd -> bst (starve current)
    XBUF2 / XBUF1         starved first inverter, outa -> outb
    XBUF4 / XBUF3         output inverter, outb -> dout

Run:  ./container.sh 'python3 comparator_sch.py [deck]'      (deck default comparator.spice)
Out:  comparator.sch
Everything (sch + netlist-back check + xschem and schemdraw renders):
      ./schematic.sh [deck]
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
DECK = BLOCK / (sys.argv[1] if len(sys.argv) > 1 else "comparator.spice")
OUT = BLOCK / "comparator.sch"

PARAM = re.compile(r"(\w+)\s*=\s*(\{[^}]*\}|'[^']*'|[\w.]+)")
EXPECTED = ["XTAIL", "XINP", "XINN", "XLOADD", "XLOADM",
            "XBST", "XBUF2", "XBUF1", "XBUF4", "XBUF3"]


def parse(path: Path):
    devs, others = {}, []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        tok = line.split()
        head = tok[0].upper()
        if head.startswith("."):
            continue
        if head.startswith("X") and len(tok) >= 6:
            p = {k.lower(): v for k, v in PARAM.findall(" ".join(tok[6:]))}
            devs[head] = {"model": tok[5], "l": p.get("l"), "w": p.get("w"),
                          "nf": p.get("nf", "1"), "m": p.get("m", "1")}
        else:
            others.append(head)
    return devs, others


DEV, OTHERS = parse(DECK)
missing = [n for n in EXPECTED if n not in DEV]
extra = sorted(set(DEV) - set(EXPECTED)) + OTHERS
if missing or extra:
    raise SystemExit(f"{DECK.name}: the drawing is the 10-device topology; "
                     f"missing {missing or '-'}, not drawn {extra or '-'}")

# ------------------------------------------------------------------ geometry
# xschem: y grows downward; MOS symbols (gf180 pfet_03v3 / nfet_03v3) have
# G at (-20, 0), B at (+20, 0), the top terminal at (+20, -30) and the bottom
# one at (+20, +30): pfet S top / D bottom, nfet D top / S bottom. A flipped
# symbol mirrors x.
VDD_Y, VSS_Y = -880, -360
X_L, X_R = 160, 1240

wires: list[tuple[int, int, int, int]] = []
pins_at: list[tuple[int, int]] = []          # instance pin locations, for splitting
inst: list[str] = []
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
    inst.append(f"C {{symbols/{kind}.sym}} {x} {y} 0 {1 if flip else 0} {{name={name[1:]}\n"
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

# ---- stage 1: PMOS 5T ------------------------------------------------------
# tail
t_top, t_g, t_b, t_bot = mos("XTAIL", 460, -800)
W((t_top[0], VDD_Y), t_top)
W(t_bot, (480, -740))
W(t_b, (520, -800)); lab(520, -800, "vdd", False)
W((240, -800), t_g)
pin("ipin", 240, -800, "pbias")
# tail bus
W((360, -740), (480, -740), (580, -740))
lab(300, -740, "tail", True); W((300, -740), (360, -740))
# input pair
p_top, p_g, p_b, p_bot = mos("XINP", 340, -680)
n_top, n_g, n_b, n_bot = mos("XINN", 600, -680, flip=True)
W((360, -740), p_top)
W((580, -740), n_top)
W((240, -680), p_g); pin("ipin", 240, -680, "inp")
W(n_g, (700, -680)); pin("ipin", 700, -680, "inn", flip=True)
W(p_b, (400, -680)); lab(400, -680, "vdd", False)
W(n_b, (540, -680)); lab(540, -680, "vdd", True)
# mirror load
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

# outa: OTA output -> first-stage gates
OUTA_Y = -600
GX1 = 800                                          # gate column, first inverter
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

# ---- stage 3: output inverter ----------------------------------------------
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
W((1080, -600), (1200, -600)); pin("opin", 1200, -600, "dout")

# no-connect ports (contract keeps them)
pin("ipin", 240, -280, "clk")
pin("ipin", 240, -240, "nbias")

# ------------------------------------------------------------------ text
# Text only (no effect on the netlist). The operating-point figures are the
# sizing record data/sizing.json (design f003, DESIGN_RECIPE.md s.6: gm/Id
# from the gm/Id tables at the bench's ideal bias) and the ngspice record REC.
SZ = json.loads((BLOCK / "data" / "sizing.json").read_text())
sys.path.insert(0, str(BLOCK))
import intent as I  # noqa: E402  design-intent currents (the one source)
_IOP = BLOCK / "data" / "intent_op.json"
IOP = json.loads(_IOP.read_text()) if _IOP.exists() else {}


_GP = BLOCK / "data" / "gain_pvt.csv"
_GPR = list(csv.DictReader(_GP.read_text().splitlines())) if _GP.exists() else []
GAIN_PVT_MIN = min((float(r["gain_db"]) for r in _GPR), default=float("nan"))
CONV_PVT_MAX = max((float(r["p_conv_uw"]) for r in _GPR if r.get("p_conv_uw")), default=float("nan"))
REC = "runs/comparator-updt-v3/20261007T001140Z"


def box(x, y, title, lines, tsize=0.7, size=0.4):
    """A framed text block (title + body lines); the frame is layer-4 graphic lines."""
    T(title, x + 20, y + 15, tsize)
    body_y = y + 15 + int(60 * tsize)
    T("\n".join(lines), x + 20, body_y, size)
    w = int(max([len(title) * 28 * tsize] + [len(l) * 30 * size for l in lines])) + 60
    h = body_y - y + int(58 * size * len(lines)) + 32
    for x1, y1, x2, y2 in ((x, y, x + w, y), (x + w, y, x + w, y + h), (x + w, y + h, x, y + h), (x, y + h, x, y)):
        texts.append(f"L 4 {x1} {y1} {x2} {y2} {{}}")


box(140, -1330, "comparator -- continuous-time comparator of the 8-bit true bottom-plate unit cell", [
    "Function: dout falls when inn (the MIM top plate) rises through inp (VBL = VDD/2) during the single-slope ramp;",
    "   dout feeds the negative-edge TSPC latch (cmp_tspc/tspc_dff), whose q clocks the Gray-code capture.",
    "Topology: PMOS 5T OTA (XTAIL, XINP/XINN, XLOADD/XLOADM) -> current-starved inverter (XBST, XBUF2/XBUF1) -> output inverter.",
    "Pins (subckt order): inp inn dout clk vdd vss nbias pbias; clk and nbias are no-connects kept by the unit-cell contract.",
    "Supply AVDD = 3.3 V.  Bias: pbias from a current into one diode-connected 1 um / %gu tail finger; XTAIL = %d and XBST = %d copies." % (
        SZ["l_b"], SZ["nf_tail"], SZ["nf_st"]),
    "   Currents next to the devices: design values in Analog_top, I_B = %g uA (bias_gen_s, ADR 0017), as on" % I.MACRO_I_B_UA,
    "   comparator_d.sch and the CPAD slide.  This sheet's testbenches run at the sizing bias I_B = %.2f uA (box right)." % I.I_B_UA,
    "Choices: every L <= 0.36 um; one finger width per flavour (PMOS 1 um, NMOS 0.5 um); buffer NMOS = XLOADM; design f003,",
    "   the power x footprint knee at sigma(Vos) <= 2 LSB (DESIGN_RECIPE.md s.6).  ADR 0015: offset accepted as signal-independent.",
    "Recorded, ngspice typical (%s): delay from the static trip 10.59-10.60 ns (gate 12.5 ns)," % REC,
    "   dout fall 5.33 ns into 10 fF (gate 6 ns), noise 0.168 mV rms at the pins (gate 1.2 mV), OTA gain 44.5 V/V, pole 22.3 MHz,",
    "   sigma(Vos) 9.38 mV = 2.11 LSB at the ADC input (alpha 0.761, 200 MC samples).  Static power: box right.",
    "Reproduce: make comparator (benches), make comparator-schematic (this drawing, netlist-back, tb_*.sch).",
    f"Sizes parsed from {DECK.name} by comparator_sch.py -- regenerate, do not hand-edit.",
])

# design-intent current next to each device (intent.py: sizing record, whole uA)
for dev, (x, y) in I.MARKER_XY.items():
    T(I.marker(dev), x, y, 0.28, 4)
T("(VBL, VDD/2)", 150, -660, 0.3)
T("(MIM top plate)", 705, -662, 0.3)
T("PMOS 5T OTA", 320, -412, 0.4)
T("starved inverter", 760, -412, 0.4)
T("output inverter", 1000, -412, 0.4)
T("clk, nbias: no-connect (unit-cell contract port list)", 290, -296, 0.35)

box(1330, -880, "Design currents in Analog_top (I_B = %g uA)" % I.MACRO_I_B_UA, [
    "I_B %g uA into the 1 um / %gu diode: bias_gen's comparator sink, sized %.2f x the %.2f uA" % (
        I.MACRO_I_B_UA, SZ["l_b"], I.MACRO_I_B_UA / I.I_B_UA, I.I_B_UA),
    "   sizing bias for the worst PVT cell, untrimmed (ADR 0017).  Branches: data/sizing.json x the same ratio.",
    "",
    ] + ["%-16s %-22s %s" % (n, g, I.marker(d) + e) for n, g, d, e in (
        ("XTAIL", "%d x 1 um, L 0.28" % SZ["nf_tail"], "xtail", ""),
        ("XINP / XINN", "%d x 1 um, L 0.32" % SZ["nf_in"], "xinp", " each"),
        ("XLOADD / XLOADM", "1 x 0.5 um, L 0.36", "xloadd", " each"),
        ("XBST", "%d x 1 um, L 0.28" % SZ["nf_st"], "xbst", ""),
        ("XBUF4 / XBUF3", "1 x 1 / 1 x 0.5 um", "xbuf4", ""))] + [
    "   * during tracking.  XBUF4 is not a sized current: its crowbar as ngspice gives it.",
    "Static power converting (design): 3.3 V x (%g + %g) uA = %.0f uW (diode + tail)." % (
        I.MACRO_I_B_UA, I.MACRO_UA["xtail"], 3.3 * I.CONVERTING_UA),
    "",
    "At the sizing bias I_B %.2f uA (this sheet's tb_*.sch): tail %s, pair %s each, starve %s." % (
        I.I_B_UA, I.ua(I.INTENT_UA["xtail"]), I.ua(I.INTENT_UA["xinp"]), I.ua(I.INTENT_UA["xbst"])),
    "ngspice puts the tail %+.0f %% / %+.0f %% off the design at %.2f / %g uA (L 0.28 um channel-length" % (
        100 * (IOP["id_ua"]["xtail"] / I.INTENT_UA["xtail"] - 1) if IOP else float("nan"),
        100 * (IOP["macro_states_ua"]["mtrip"]["xtail"] / I.MACRO_UA["xtail"] - 1) if IOP else float("nan"),
        I.I_B_UA, I.MACRO_I_B_UA),
    "   modulation; intent_op.py reports it).",
    "Simulated, worst over bias_gen's 135 PVT cells (gain_pvt.py): gain >= %d dB (spec > 60 dB)," % int(GAIN_PVT_MIN),
    "   static power converting <= %.0f uW." % CONV_PVT_MAX,
    "No capacitor or resistor in this cell; dout load on the benches 10 fF."], tsize=0.5, size=0.35)

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
body += texts + inst
OUT.write_text("\n".join(body) + "\n")
print(f"REPORT: wrote {OUT.name} from {DECK.name}: {len(DEV)} devices, {len(segs)} wire segments")
