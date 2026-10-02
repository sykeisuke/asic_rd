#!/usr/bin/env python3
"""To-scale floorplans of the slope-ADC unit cell: switch + hold cap + comparator.

    ./container.sh 'python3 floorplan.py'                  # all four cells
    ./container.sh 'python3 floorplan.py UC_MIM UC_MOM'    # some of them

    UC_MIM      smallest MIM the PDK draws (5 x 5 um FuseTop, 54.5 fF, MIMTM.8a)
                ON TOP of the tail in M4/FuseTop/M5; switch sized for it
    UC_MOM      the characterized MOM unit (MOMU, 15.62 fF, M1-M4) BESIDE the
                transistors; minimum switch
    UC_MIM_125  125 fF MIM on top -- the hold capacitor the 12-bit target needs
                (kT/C under half an LSB12, gf180_sampling_unit_cell)
    UC_MOM_125  eight MOM units (125 fF) beside -- the same target with MOM

The comparator is cmp_p5t_8b.spice (mixed_signal/comparator), device for
device: same L, W and nf.  Layout liberties, each named where it is taken:
the tail is two nf=10 halves of the same 4.525 um finger stacked in the same
well (20 fingers either way), the matched pairs get dummy fingers, and the
input pair's fingers are interdigitated ABBA with the two gate nets on two
gate bars.

The floorplan follows the analog layout section of Pretl's "Design of Complex
ICs" (iic-jku.github.io/design-complex-ic, 4.5.1-4.5.3, 4.3.4):
  - matched devices from identical unit fingers, same orientation, same
    current direction, no mirroring: INP/INN share one diffusion row and one
    finger; LOADD/LOADM share one diffusion row and one finger;
  - "the devices are surrounded by similar structures": a dummy finger at
    each end of the pair and of the mirror, gates to be tied off;
  - common centroid for the pair: ABBA, its two gate nets on a top and a
    bottom gate bar (DCIC fig. 50/52); the mirror shares one gate net so one
    bar serves it and the A/B split is in its drain straps;
  - "avoid low-level metal routing over sensitive devices": the MIM goes
    over the tail, never over the pair, and the pair row is kept clear;
  - floor planning by pins and supplies: input (hold node) enters at the
    left, so the switch stands in the left column; the output leaves at the
    right, so the buffer inverters stand in the right column; vdd rail along
    the top of the n-well block, vss rail along the bottom of the p-well
    block, a wiring channel between the wells for the mirror and output nets.

Every transistor is the PDK's own generator (gdsfactory gf180mcu plugin, a
polygon port of Magic's gf180mcu::mos_draw) with its per-device guard ring
OFF and one guard ring per well block drawn with that generator's own ring
code, so the PMOS block shares a single n-well.  This is placement, not
routing: no signal wires are drawn, so the area here is the floor under which
a routed cell cannot go.  Signoff is KLayout's, on the PDK deck, through
analog_layout/signoff.py by path.  Every figure of merit is one
`name = value` line on stdout.
"""

import json
import math
import os
import subprocess
import sys

import gdsfactory as gf
import gf180mcu
from gf180mcu.cells import fet as F
from gf180mcu.layers import layer as L

gf180mcu.PDK.activate()

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
FINAL = os.path.join(BLOCK, "physical", "final_views")
ANALOG_LAYOUT = os.environ.get("ANALOG_LAYOUT",
                               "/foss/designs/mixed_signal/analog_layout")
sys.path.insert(0, ANALOG_LAYOUT)
import mom_cap      # noqa: E402  the MOMU drawing, reused not copied
import signoff      # noqa: E402  KLayout DRC on the PDK deck
signoff.WORK = WORK  # its reports land here, not in analog_layout/work

# ---------------------------------------------------------------------------
# Electrical inputs
# ---------------------------------------------------------------------------

#- The comparator each cell is built around.  Default: the comparator sized
#- INTO that cell's hold capacitor by ../comparator_unit_cell/size_uc.py
#- (cmp_uc_<tag>.spice, parsed device for device).  CMP_SOURCE=p5t8b builds
#- every cell around the recorded cmp_p5t_8b instead, which was sized into
#- 1 pF -- the comparison the report draws.
COMPARATOR_UC = os.environ.get(
    "COMPARATOR_UC", os.path.join(os.path.dirname(BLOCK), "comparator_unit_cell"))
COMPARATOR = os.environ.get("COMPARATOR", "/foss/designs/mixed_signal/comparator")
CMP_SOURCE = os.environ.get("CMP_SOURCE", "uc")

#- cmp_p5t_8b.spice, verbatim.  (kind, L um, W um, nf)
CMP_P5T8B = {
    "XINP":   ("pfet", 0.5,  30.8, 8),
    "XINN":   ("pfet", 0.5,  30.8, 8),
    "XLOADD": ("nfet", 0.5,  12.4, 3),
    "XLOADM": ("nfet", 0.5,  12.4, 3),
    "XTAIL":  ("pfet", 1.0,  90.5, 20),
    "XBUF1":  ("nfet", 0.28, 4.0,  4),
    "XBUF2":  ("pfet", 0.28, 4.24, 1),
    "XBUF3":  ("nfet", 0.28, 8.0,  4),
    "XBUF4":  ("pfet", 0.28, 16.0, 4),
}
COUTA_F = 20e-15   # explicit 20 fF on outa in the deck; see RESULTS.md


def parse_netlist(path):
    """X lines of an emitted comparator netlist -> {name: (kind, L, W, nf)}."""
    import re
    out = {}
    for line in open(path):
        mm = re.match(r"^(X\w+)\s+\S+\s+\S+\s+\S+\s+\S+\s+([np])fet_03v3\s+L=([\d.]+)u\s+"
                      r"W=\{?([\d.]+)u[^ ]*\s+nf=(\d+)", line)
        if mm:
            out[mm.group(1)] = (mm.group(2) + "fet", float(mm.group(3)),
                                float(mm.group(4)), int(mm.group(5)))
    if len(out) != 9:
        raise SystemExit(f"{path}: expected 9 transistors, parsed {len(out)}")
    return out


def comparator_for(tag):
    """Devices, hold-node data and switch for a cell's comparator tag."""
    if CMP_SOURCE == "p5t8b":
        return dict(CMP_P5T8B), {"tag": "p5t8b", "c_in_f": 0.0, "iref": 2.783e-6}, None
    devs = parse_netlist(os.path.join(COMPARATOR_UC, f"cmp_uc_{tag}.spice"))
    sizing = json.load(open(os.path.join(COMPARATOR_UC, "data", f"sizing_{tag}.json")))
    sw = json.load(open(os.path.join(COMPARATOR_UC, "data", "switch_sizing.json")))[tag]
    sizing["tag"] = tag
    return devs, sizing, sw

#- Switch sizing rule of simulations/gf180_sampling_unit_cell/design_cell.py:
#- tau = (T_track - T_edge) / ((N+1) ln2), Ron = tau / C, W_N = K / Ron,
#- W_P = 2 W_N, clamped at the 0.22 um minimum.  K is the MEASURED worst-case
#- Ron*W_N of the 1:2 gate over 0.5-2.0 V (tg_ron_cell.spice), not pygmid.
K_MEAS_OHM_UM = 2710.0
W_MIN_UM = 0.22
L_SW_UM = 0.28
T_EDGE = 100e-12
N_BITS = int(os.environ.get("BITS", "8"))
#- The sampling rate the switch is sized at.  Up to 100 MHz every capacitor
#- in this study clamps at the minimum gate; 200 MHz is where the MIM's
#- switch grows and the MOM's does not, so that is the rate drawn.
FS_HZ = float(os.environ.get("FS_MHZ", "200")) * 1e6

#- MIM 2.0 fF/um2 flavour: c_cox*A + c_capsw*P (cap_area_sweep method check).
MIM_CCOX = 1.99e-3
MIM_CSW = 2.383e-10
MIM_MIN_SIDE_UM = 5.0          # MIMTM.8a: 25 um2 minimum FuseTop
MIM_KEEPOUT_UM = 1.2           # other M4 to the bottom plate, MIMTM.1

#- MOMU: the 15-16 fF unit analog_layout/mom_cap.py characterizes.
MOM_CAB_F = 15.62e-15
MOM_CASUB_F = 1.40e-15
MOM_UNIT_AREA_UM2 = 27.451

#- The four cells.  (capacitor kind, size: MIM FuseTop side in um or MOM
#- units, comparator tag in comparator_unit_cell)
CELLS = {
    "UC_MIM":     ("mim", MIM_MIN_SIDE_UM, "mim55"),
    "UC_MOM":     ("mom", 1, "mom16"),
    "UC_MIM_125": ("mim", None, "mim125"),   # side solved for 125 fF below
    "UC_MOM_125": ("mom", 8, "mim125"),
}

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

GAP = 0.50       # bbox-to-bbox between devices in one well block (comp 0.28,
                 # M1 0.23; the pcell bbox is its M1, so 0.5 clears both)
ROW_GAP = 0.50
CHANNEL = 2.00   # n-well edge to p-well edge: a wiring channel of four M2
                 # tracks for the mirror, the output and the tail nets, on
                 # top of the 1.2 um the wells need anyway


def snap(v):
    """5 nm manufacturing grid.  A pcell whose bbox is asymmetric has a
    half-extent of 2.5 nm, and moving an instance by that puts every shape in
    it off grid (measured: 1424 contact_OFFGRID in one cell)."""
    return round(round(v / 0.005) * 0.005, 4)


def move_to(r, x, y):
    r.dmove((snap(x - r.dxmin), snap(y - r.dymin)))


def rect(c, lay, x0, y0, x1, y1):
    c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=lay)


def m1_shapes(c):
    idx = c.kcl.layout.layer(*L["metal1"])
    return [sh.dbbox() for sh in c.shapes(idx).each()]


_DEVICES = {}


def device(kind, l_um, w_um, nf, pattern=None):
    key = (kind, l_um, w_um, nf, pattern)
    if key not in _DEVICES:
        _DEVICES[key] = _device(kind, l_um, w_um, nf, pattern)
    return _DEVICES[key]


def gate_bar(c, xs, hl, y_act, up, tie_only=False, clear=0.24):
    """A poly bar with contacts and M1 over the fingers at `xs`, above the
    active (up=True) or below it, `clear` um from the active: 0.24 puts the
    M1 0.23 from the S/D M1 (M1.2a); a device with a second bar for the other
    net uses 0.40, so the bar is PL.3a's 0.24 from that net's finger ends,
    which the generator extends 0.22 past the active (measured: 14 PL.3a on
    the ABBA pair at 0.24).  Returns the bar's M1 bbox."""
    s = 1 if up else -1
    yb0 = F._snap(y_act + s * clear)
    yb1 = yb0 + s * 0.36                        # contact 0.22 + 2 x 0.07
    xb0 = min(xs) - hl - 0.07
    xb1 = max(xs) + hl + 0.07
    if xb1 - xb0 < 0.50:                        # M1.3 min area on the bar
        xb0, xb1 = (xb0 + xb1) / 2 - 0.25, (xb0 + xb1) / 2 + 0.25
    lo, hi = min(yb0, yb1), max(yb0, yb1)
    rect(c, L["poly2"], xb0, lo, xb1, hi)
    for x in xs:                                # fingers up to the bar
        rect(c, L["poly2"], x - hl, min(y_act, yb0 + s * 0.05),
             x + hl, max(y_act, yb0 + s * 0.05))
    n = 1 if tie_only else max(1, int((xb1 - xb0 - 0.14 - 0.22) // 0.47) + 1)
    ox = (xb0 + xb1) / 2 - ((n - 1) * 0.47 + 0.22) / 2
    for i in range(n):
        rect(c, L["contact"], snap(ox + i * 0.47), lo + 0.07,
             snap(ox + i * 0.47) + 0.22, lo + 0.29)
    rect(c, L["metal1"], xb0 - 0.01, lo + 0.01, xb1 + 0.01, hi - 0.01)
    return xb0 - 0.01, lo + 0.01, xb1 + 0.01, hi - 0.01


def _device(kind, l_um, w_um, nf, pattern):
    """One PDK transistor, per-finger width W/nf, no guard ring of its own.

    `pattern` is one letter per drawn finger: A and B the two gate nets (B
    gets the bottom gate bar), D a dummy finger with its own tie pad.  None
    means nf fingers on one net, one bar on top.  The count of A+B fingers
    must be nf, so the drawn device is the netlist's device plus dummies.

    The plugin's finger is a polygon port of Magic's gf180mcu::mos_draw and
    inherits its two M1 defects against the KLayout deck, both measured here
    on the first build (196 violations in a two-cell floorplan, all inside
    pcells): M1.3 on every poly-contact cap (0.48 x 0.23 um, under the M1
    minimum area) and M1.2a on L = 0.28 um devices (the poly-contact M1
    0.175 um from the S/D M1).  So the generator draws fingers and S/D
    contacts only (topc=botc=False) and the gate bars are drawn here.
    """
    pattern = pattern or "A" * nf
    assert sum(ch in "AB" for ch in pattern) == nf, (kind, w_um, nf, pattern)
    n_total = len(pattern)
    wf = round(w_um / nf, 4)
    rules = dict(F._RULES)
    rules["volt"] = "3.3V"
    is_n = kind == "nfet"
    c = gf.Component()
    hw = wf / 2
    hl = l_um / 2
    F._mos_draw(c, wf, l_um, n_total, rules, is_nfet=is_n, topc=False,
                botc=False, guard=False)
    geom = F._mos_geometry(wf, l_um, rules, False, False)
    dx = geom["fw"] - (2 * rules["diff_surround"] + rules["contact_size"])
    xs = [-(n_total - 1) * dx / 2 + i * dx for i in range(n_total)]
    #- the dogbone S/D pad is taller than the gate on a 0.22 um device
    act_top = max(hw, geom["cdwmin"] / 2) + rules["diff_surround"]
    xa = [x for x, ch in zip(xs, pattern) if ch == "A"]
    xb = [x for x, ch in zip(xs, pattern) if ch == "B"]
    xd = [x for x, ch in zip(xs, pattern) if ch == "D"]
    clear = 0.40 if xb else 0.24
    bars = [gate_bar(c, xa, hl, act_top, True, clear=clear)]
    if xb:
        bars.append(gate_bar(c, xb, hl, -act_top, False, clear=clear))
    for x in xd:                    # dummies: own pad, to be tied to a rail
        bars.append(gate_bar(c, [x], hl, act_top, True, tie_only=True,
                             clear=clear))
    #- S/D pads under the M1 minimum area (0.1444 um2) on a 0.22-0.44 um
    #- finger: stretch them away from the gate bar (single-bar devices only,
    #- which is all the small ones are).
    if not xb:
        for bb in m1_shapes(c):
            if bb.top < bars[0][1] and bb.area() < 0.15:
                h = 0.15 / bb.width() + 0.02
                rect(c, L["metal1"], bb.left, F._snap(bb.top - h), bb.right, bb.top)
    tag = pattern if pattern != "A" * nf else ""
    c.name = f"{kind}_L{l_um:g}_W{w_um:g}_nf{nf}{'_' + tag if tag else ''}".replace(".", "p")
    c.info["pattern"] = pattern
    return c


def size(comp):
    b = comp.dbbox()
    return b.width(), b.height()


class Placer:
    """Refs by name, with their bboxes recorded for the drawing."""

    def __init__(self, c):
        self.c = c
        self.refs = {}
        self.items = []   # (name, kind, x0, y0, x1, y1)

    def put(self, name, comp, x, y, kind):
        r = self.c.add_ref(comp)
        move_to(r, x, y)
        self.refs[name] = r
        self.items.append((name, kind, r.dxmin, r.dymin, r.dxmax, r.dymax))
        return r

    def put_centred(self, name, comp, xc, y, kind):
        w = comp.dbbox().width()
        return self.put(name, comp, xc - w / 2, y, kind)

    def extent(self, names):
        xs0 = min(self.refs[n].dxmin for n in names)
        ys0 = min(self.refs[n].dymin for n in names)
        xs1 = max(self.refs[n].dxmax for n in names)
        ys1 = max(self.refs[n].dymax for n in names)
        return xs0, ys0, xs1, ys1


def block_ring(c, x0, y0, x1, y1, is_nfet):
    """One guard ring + well around a block, with the pcell's own ring code.

    _guard_ring draws centered at the origin with gx, gy measured to contact
    centres; it is drawn into a scratch component and moved into place.  The
    ring stands diff_spacing off the block's bbox exactly as the pcell stands
    it off a single device's diffusion.  Returns the well/implant outer box.
    """
    rules = dict(F._RULES)
    rules["volt"] = "3.3V"
    gx = (x1 - x0) + 2 * (rules["diff_spacing"] + rules["diff_surround"]) \
        + rules["contact_size"]
    gy = (y1 - y0) + 2 * (rules["diff_spacing"] + rules["diff_surround"]) \
        + rules["contact_size"]
    #- a multiple of 10 nm, so the half-sizes the ring is drawn from are on
    #- the 5 nm grid; at 5 nm one bar came out 0.065 over its contacts and
    #- failed CO.4 (0.07) on one side only
    gx = round(math.ceil(gx / 0.01) * 0.01, 3)
    gy = round(math.ceil(gy / 0.01) * 0.01, 3)
    tmp = gf.Component()
    sub = F._L_LVPWELL if is_nfet else F._L_NWELL
    imp = F._L_PPLUS if is_nfet else F._L_NPLUS
    F._guard_ring(tmp, gx, gy, rules, sub, True, glc=True, grc=True,
                  gtc=True, gbc=True)
    F._guard_ring_implant(tmp, gx, gy, imp, rules)
    r = c.add_ref(tmp)
    r.dmove((snap((x0 + x1) / 2 - r.dx), snap((y0 + y1) / 2 - r.dy)))
    b = r.dbbox()
    return b.left, b.bottom, b.right, b.top


def switch_width(c_hold_f, fs_hz, bits):
    t_track = 0.5 / fs_hz
    tau = (t_track - T_EDGE) / ((bits + 1) * math.log(2))
    ron = tau / c_hold_f
    wn = K_MEAS_OHM_UM / ron
    clamped = wn < W_MIN_UM
    wn = max(wn, W_MIN_UM)
    wn = round(math.ceil(wn / 0.01) * 0.01, 2)     # 10 nm sizing grid
    return wn, 2 * wn, ron, clamped


def mim_value(side_um):
    s = side_um * 1e-6
    return MIM_CCOX * s * s + 4 * MIM_CSW * s


def mim_side_for(c_f):
    a, b = MIM_CCOX, 4 * MIM_CSW
    s = (-b + math.sqrt(b * b + 4 * a * c_f)) / (2 * a) * 1e6
    return round(math.ceil(s / 0.01) * 0.01, 2)


# ---------------------------------------------------------------------------
# The MIM, drawn from the rules
# ---------------------------------------------------------------------------
#- The plugin's cap_mim pcell ignores its metal_level argument and draws the
#- MIM-A stack (M2/Via2/M3) with a frame for a bottom plate; against the
#- gf180mcuD deck it is 37 violations (work/mim_rules.md).  gf180mcuD is
#- MIM option B: bottom plate M4, dielectric FuseTop, Via4, top wiring M5.
#- The cell is drawn here from the MIMTM rules in rule_decks/mim_b.rb:
#-   MIMTM.3  M4 overlaps FuseTop by 0.6      MIMTM.4  FuseTop encloses Via4 by 0.4
#-   MIMTM.2  M4 encloses bottom Via4 by 0.4  MIMTM.5  FuseTop to bottom Via4 0.4
#-   MIMTM.9  Via4 spacing on the plate 0.5   MIMTM.1  other M4 1.2 from the plate
#-   MIMTM.8a FuseTop area >= 25 um2          MIMTM.10 no Via3 under the plate
VIA4 = 0.26
VIA4_PITCH = VIA4 + 0.5
M5_ENC = 0.10          # M5 past a Via4 (V4.x is 0.01/0.06; 0.1 clears both)


def via_grid(c, x0, y0, x1, y1):
    """Fill [x0,x1]x[y0,y1] with a Via4 array at MIMTM.9 spacing, centred."""
    n = int((x1 - x0 - VIA4) // VIA4_PITCH) + 1
    m = int((y1 - y0 - VIA4) // VIA4_PITCH) + 1
    ox = x0 + ((x1 - x0) - ((n - 1) * VIA4_PITCH + VIA4)) / 2
    oy = y0 + ((y1 - y0) - ((m - 1) * VIA4_PITCH + VIA4)) / 2
    for i in range(n):
        for j in range(m):
            x = snap(ox + i * VIA4_PITCH)
            y = snap(oy + j * VIA4_PITCH)
            rect(c, L["via4"], x, y, x + VIA4, y + VIA4)
    return n * m


def mim_cap(side_um):
    """MIM: FuseTop side x side, plate + one bottom-contact arm.

    Returns (component, fusetop (w,h), bottom plate (w,h), full bbox (w,h)).
    The bottom plate's arm carries its Via4 column: MIMTM.10 forbids a Via3
    into the plate, so BOTH plates leave through M5 and come down to M4 at
    least MIMTM.1 = 1.2 um away.  Those landings are routing, not drawn.
    """
    c = gf.Component()
    s = side_um
    ov = 0.6                       # MIMTM.3
    rect(c, L["fusetop"], 0, 0, s, s)
    rect(c, (117, 5), -0.2, -0.2, s + 0.2, s + 0.2)       # CAP_MK, MIMTM.7
    rect(c, (117, 10), 0, 0, s, s)                         # MIM_L_MK, MIMTM.12
    n_top = via_grid(c, 0.4, 0.4, s - 0.4, s - 0.4)        # MIMTM.4
    rect(c, L["metal5"], 0.4 - M5_ENC, 0.4 - M5_ENC, s - 0.4 + M5_ENC,
         s - 0.4 + M5_ENC)
    arm_x0 = s + 0.4               # MIMTM.5: FuseTop to bottom Via4
    arm_x1 = arm_x0 + VIA4 + 0.4   # MIMTM.2: M4 past the via
    rect(c, L["metal4"], -ov, -ov, arm_x1, s + ov)
    n_bot = via_grid(c, arm_x0, -ov + 0.4, arm_x0 + VIA4, s + ov - 0.4)
    rect(c, L["metal5"], arm_x0 - M5_ENC, -ov + 0.4 - M5_ENC,
         arm_x0 + VIA4 + M5_ENC, s + ov - 0.4 + M5_ENC)
    c.info["n_via_top"] = n_top
    c.info["n_via_bot"] = n_bot
    c.name = f"MIM_{s:g}".replace(".", "p")
    b = c.dbbox()
    return c, (s, s), (arm_x1 + ov, s + 2 * ov), (b.width(), b.height())


# ---------------------------------------------------------------------------
# The unit cell
# ---------------------------------------------------------------------------

def interdigitate(nf_each):
    """Common-centroid finger order for two matched devices of nf_each
    fingers each, dummies at both ends.  Even counts: ABBA repeated (DCIC
    fig. 52 b), centroids coincide.  Odd counts cannot coincide in one row;
    the closest is ABBA... with the odd finger pair in the middle (ABB A AB
    style), which is what an odd nf gets, and the drawing says so."""
    n = 2 * nf_each
    if nf_each % 2 == 0:
        core = ("ABBA" * (n // 4 + 1))[:n]
    else:
        half = ("ABBA" * (n // 4 + 1))[: n // 2]
        core = half + half[::-1].translate(str.maketrans("AB", "BA"))
    return "D" + core + "D"


def unit_cell(name, cap_kind, cap_size, cmp_tag):
    """Place the comparator, the switch and the capacitor; return metrics."""
    c = gf.Component()
    p = Placer(c)
    m = {"cell": name, "cap": cap_kind}

    # -- the comparator this cell is built around ----------------------------
    CMP, sizing, sw = comparator_for(cmp_tag)
    m["comparator"] = sizing["tag"]
    m["c_in_ff"] = sizing.get("c_in_f", 0.0) * 1e15
    m["iref_ua"] = sizing.get("iref", 0.0) * 1e6
    m["cmp_power_uw"] = sizing.get("power", 0.0) * 1e6

    # -- capacitor value and the switch it asks for ---------------------------
    if cap_kind == "mim":
        side = cap_size if cap_size else mim_side_for(125e-15)
        c_hold = mim_value(side)
    else:
        c_hold = cap_size * (MOM_CAB_F + MOM_CASUB_F)   # what the hold node sees
    #- the node the switch drives is the capacitor plus the comparator's input
    c_node = c_hold + sizing.get("c_in_f", 0.0)
    wn, wp, ron, clamped = switch_width(c_node, FS_HZ, N_BITS)
    if sw is not None and abs(sw["drawn"]["fs_mhz"] - FS_HZ / 1e6) < 0.01 \
            and sw["drawn"]["bits"] == N_BITS:
        wn, wp = sw["drawn"]["wn_um"], sw["drawn"]["wp_um"]   # the same rule, recorded
    m.update(c_hold_ff=c_hold * 1e15, c_node_ff=c_node * 1e15, sw_wn_um=wn,
             sw_wp_um=wp, sw_ron_max_ohm=ron, sw_clamped=int(clamped))

    # -- devices -------------------------------------------------------------
    #- layout liberty, named: the sizing tool hard-codes nf = 1 on BUF2 and
    #- its width follows the sampled inverter ratio (9.9 um here).  A single
    #- 10 um finger is a 10 um tall device; it is drawn with the tool's own
    #- rule for every other device, round(W / 4 um) fingers of the same W.
    def layout_nf(kind, l_um, w_um, nf):
        if nf == 1 and w_um > 5.0:
            nf = max(2, int(round(w_um / 4.0)))
        return (kind, l_um, w_um, nf)
    CMP = {k: layout_nf(*v) for k, v in CMP.items()}
    d = {k: device(*v) for k, v in CMP.items()}
    kin, lin, win, nfin = CMP["XINP"]
    kld, lld, wld, nfld = CMP["XLOADD"]
    ktl, ltl, wtl, nftl = CMP["XTAIL"]
    #- the tail as two halves of the same finger, stacked in the well; an odd
    #- finger count splits ceil/floor
    nf_a = (nftl + 1) // 2
    nf_b = nftl - nf_a
    wf_tail = wtl / nftl
    tail_a = device(ktl, ltl, round(wf_tail * nf_a, 3), nf_a)
    tail_b = device(ktl, ltl, round(wf_tail * nf_b, 3), nf_b) if nf_b else None
    pair = device(kin, lin, 2 * win, 2 * nfin, interdigitate(nfin))
    loads = device(kld, lld, 2 * wld, 2 * nfld, "D" + "A" * (2 * nfld) + "D")
    tgn = device("nfet", L_SW_UM, wn, 1)
    tgp = device("pfet", L_SW_UM, wp, 1)
    m["pair_pattern"] = pair.info["pattern"]
    m["loads_pattern"] = loads.info["pattern"]
    m["labels"] = {
        "PAIR": f"INP / INN input pair   2 x {win:g}u/{lin:g}, {2 * nfin} fingers of {win / nfin:.3g}u + 2 dummies",
        "TAILA": f"TAIL half A   {wf_tail * nf_a:.3g}u/{ltl:g}, {nf_a} fingers of {wf_tail:.3g}u",
        "TAILB": f"TAIL half B   {wf_tail * nf_b:.3g}u/{ltl:g}, {nf_b} fingers of {wf_tail:.3g}u",
        "LOADS": f"LOADD / LOADM mirror  2 x {wld:g}u/{lld:g}, {2 * nfld} x {wld / nfld:.3g}u + 2 dummies",
        "BUF4": f"BUF4\n{CMP['XBUF4'][2]:g}u/0.28\nnf {CMP['XBUF4'][3]}",
        "BUF2": f"BUF2\n{CMP['XBUF2'][2]:g}u",
        "BUF3": f"BUF3 {CMP['XBUF3'][2]:g}u",
        "BUF1": f"BUF1 {CMP['XBUF1'][2]:g}u",
    }
    m["devices_table"] = {k: list(v) for k, v in CMP.items()}

    # -- the matched core on a vertical symmetry axis at x = 0 --------------
    #   n-well:  TAIL half B            (top)
    #            TAIL half A
    #            INP/INN  D ABBA... D    (bottom of the n-well block)
    #   channel
    #   p-well:  LOADD/LOADM  D AAAAAA D
    pw = size(pair)[0]
    xc = 0.0
    y = 0.0
    r = p.put_centred("PAIR", pair, xc, y, "pmos")
    y = r.dymax + ROW_GAP
    r = p.put_centred("TAILA", tail_a, xc, y, "pmos")
    y = r.dymax + ROW_GAP
    if tail_b is not None:
        r = p.put_centred("TAILB", tail_b, xc, y, "pmos")
    core_x0, core_x1 = -pw / 2, pw / 2

    # -- the side slack of the tail rows (15.9 um under a 19.0 um pair row)
    #    takes the two 1.5 um devices: TG P on the LEFT, the input side,
    #    where the hold node enters; BUF2, the first inverter's PMOS, on the
    #    RIGHT, the output side.  BUF4 (3.9 um) stands beside the pair row on
    #    the right, at the edge where dout leaves the cell.
    ta = p.refs["TAILA"]
    tb = p.refs.get("TAILB", ta)
    #- the side devices stand in the slack only if the tail row is narrower
    #- than the pair row; otherwise they take their own column beside it
    x_tgp = min(ta.dxmin, tb.dxmin) - GAP - size(tgp)[0]
    p.put("TGP", tgp, x_tgp, ta.dymin, "pmos")
    r2 = p.put("BUF2", d["XBUF2"], max(ta.dxmax, tb.dxmax) + GAP, tb.dymin, "pmos")
    p.put("BUF4", d["XBUF4"], max(core_x1, r2.dxmax if r2.dymin < size(pair)[1] else core_x1) + GAP,
          0.0, "pmos")
    pm_names = [n for n in ("PAIR", "TAILA", "TAILB", "TGP", "BUF2", "BUF4") if n in p.refs]
    px0, py0, px1, py1 = p.extent(pm_names)
    nw = block_ring(c, px0, py0, px1, py1, is_nfet=False)
    m["pmos_block_w_um"], m["pmos_block_h_um"] = px1 - px0, py1 - py0

    # -- p-well block under the channel ----------------------------------
    ny_top = nw[1] - CHANNEL - 0.9          # ring + lvpwell of the NMOS block
    lh = size(loads)[1]
    bufs_h = size(d["XBUF3"])[1] + ROW_GAP + size(d["XBUF1"])[1]
    nrow_h = max(lh, bufs_h, size(tgn)[1])
    ny = ny_top - nrow_h
    p.put_centred("LOADS", loads, xc, ny, "nmos")
    #- under TG P on the input side, but never into the mirror: the mirror
    #- row can be wider than the pair row with a small comparator
    p.put("TGN", tgn, min(p.refs["TGP"].dxmin,
                          p.refs["LOADS"].dxmin - GAP - size(tgn)[0]), ny, "nmos")
    r3 = p.put("BUF3", d["XBUF3"], p.refs["LOADS"].dxmax + GAP, ny, "nmos")
    p.put("BUF1", d["XBUF1"], r3.dxmin, r3.dymax + ROW_GAP, "nmos")
    nm_names = ["LOADS", "TGN", "BUF3", "BUF1"]

    # -- capacitor -----------------------------------------------------------
    if cap_kind == "mom":
        units = cap_size
        #- MOMU beside the transistors, inside the p-well ring so it rides
        #- the same substrate tie.  One unit takes the p-well row's slack if
        #- it fits inside the n-well block's width; more units go in rows of
        #- four under the NMOS row (two abutted rows of four = 22 x 10.6 um).
        nx0, ny0, nx1, ny1 = p.extent(nm_names)
        if units == 1:
            #- Two candidate spots, the cheaper one taken and the choice
            #- recorded: (a) right of the buffer NMOS in the p-well row, free
            #- if the n-well block is wider than the row; (b) a band under
            #- the row, always 5.7 um of height.
            mc, mw, mh = mom_cap.mom_cap(name="MOMU")
            grow_a = max(0.0, (nx1 + GAP + mw) - (nw[2] - 0.9)) * (nw[3] - ny0 + 2.0)
            grow_b = (mh + GAP) * (nw[2] - nw[0])
            mr = c.add_ref(mc)
            if grow_a <= grow_b:
                move_to(mr, nx1 + GAP, ny)
                m["mom_spot"] = "beside, in the p-well row"
            else:
                move_to(mr, xc - mw / 2, ny0 - GAP - mh)
                m["mom_spot"] = "band under the p-well row"
            p.items.append(("MOMU", "cap", mr.dxmin, mr.dymin, mr.dxmax, mr.dymax))
            cap_w, cap_h = mw, mh
        else:
            per_row = 4
            rows = math.ceil(units / per_row)
            mc, mw, mh = mom_cap.mom_cap(name=f"MOMU{per_row}", units=per_row)
            yy = ny - GAP - rows * mh - (rows - 1) * GAP
            for k in range(rows):
                mr = c.add_ref(mc)
                move_to(mr, xc - mw / 2, yy + k * (mh + GAP))
                p.items.append((f"MOMU{per_row}x{k}", "cap", mr.dxmin, mr.dymin,
                                mr.dxmax, mr.dymax))
            cap_w, cap_h = mw, rows * mh + (rows - 1) * GAP
        cx0 = min(i[2] for i in p.items if i[1] == "cap")
        cy0 = min(i[3] for i in p.items if i[1] == "cap")
        cx1 = max(i[4] for i in p.items if i[1] == "cap")
        cy1 = max(i[5] for i in p.items if i[1] == "cap")
        m["mim_inside_pmos_block"] = 0
        m.update(cap_w_um=cap_w, cap_h_um=cap_h,
                 cap_area_um2=units * MOM_UNIT_AREA_UM2,
                 cap_value_ff=units * MOM_CAB_F * 1e15, cap_units=units,
                 cap_footprint_um2=units * MOM_UNIT_AREA_UM2, cap_over_devices=0)
        lvp = block_ring(c, min(nx0, cx0), min(ny0, cy0), max(nx1, cx1),
                         max(ny1, cy1), is_nfet=True)
    else:
        nx0, ny0, nx1, ny1 = p.extent(nm_names)
        lvp = block_ring(c, nx0, ny0, nx1, ny1, is_nfet=True)
        #- MIM over the TAIL halves on the symmetry axis, never over the
        #- pair: "avoid low-level metal routing over sensitive devices".
        mc, ft, bot, full = mim_cap(side)
        mr = c.add_ref(mc)
        ta = p.refs["TAILA"]
        tb = p.refs.get("TAILB", ta)
        plate_cx = mr.dxmin + 0.6 + side / 2      # centre the PLATE, not the arm
        mr.dmove((snap(xc - plate_cx), snap((ta.dymin + tb.dymax) / 2 - mr.dy)))
        p.items.append(("MIM", "cap", mr.dxmin, mr.dymin, mr.dxmax, mr.dymax))
        m.update(cap_w_um=full[0], cap_h_um=full[1],
                 cap_area_um2=ft[0] * ft[1],
                 cap_value_ff=mim_value(side) * 1e15, cap_units=1,
                 cap_footprint_um2=(bot[0] + 2 * MIM_KEEPOUT_UM)
                 * (bot[1] + 2 * MIM_KEEPOUT_UM),
                 cap_fusetop_w_um=ft[0], cap_bottom_w_um=bot[0],
                 cap_over_devices=1,
                 mim_inside_pmos_block=int(mr.dxmin >= px0 and mr.dxmax <= px1
                                           and mr.dymin >= py0 and mr.dymax <= py1))

    # -- cell extent -----------------------------------------------------------
    b = c.dbbox()
    sx0 = min(nw[0], lvp[0]); sx1 = max(nw[2], lvp[2])
    sy0 = min(nw[1], lvp[1]); sy1 = max(nw[3], lvp[3])
    m.update(cell_w_um=sx1 - sx0, cell_h_um=sy1 - sy0,
             cell_area_um2=(sx1 - sx0) * (sy1 - sy0),
             bbox_w_um=b.width(), bbox_h_um=b.height(),
             bbox_area_um2=b.width() * b.height())
    m["device_area_um2"] = sum((i[4] - i[2]) * (i[5] - i[3])
                               for i in p.items if i[1] in ("pmos", "nmos"))
    m["gate_area_um2"] = sum(v[1] * v[2] for v in CMP.values()) \
        + L_SW_UM * (wn + wp)
    m["devices"] = len([i for i in p.items if i[1] in ("pmos", "nmos")])
    m["dummy_fingers"] = 4
    m["items"] = p.items
    m["wells"] = {"nwell": nw, "lvpwell": lvp}
    m["axis_x"] = xc
    m["channel"] = [lvp[3], nw[1]]
    rect(c, L["pr_bndry"], sx0, sy0, sx1, sy1)
    c.name = name
    return c, m


# ---------------------------------------------------------------------------
# Signoff, render
# ---------------------------------------------------------------------------

def drc(name, gds):
    geom, _ = signoff.drc(name, "all,-density", "drc", gds=gds)
    dens, _ = signoff.drc(name, "density", "density", gds=gds)
    return geom, dens


def render(name, gds):
    out = os.path.join(FINAL, "render", name + ".png")
    subprocess.run(["klayout", "-z", "-rd", "input=" + gds, "-rd", "out=" + out,
                    "-rd", "width=2000", "-rd", "height=1400",
                    "-r", os.path.join(ANALOG_LAYOUT, "klayout", "render.rb")],
                   cwd=WORK, text=True, stdout=open(
                       os.path.join(WORK, name + "-render.log"), "w"),
                   stderr=subprocess.STDOUT,
                   env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    return os.path.getsize(out) if os.path.exists(out) else 0


KEYS = ("comparator", "c_in_ff", "c_node_ff", "iref_ua", "cmp_power_uw", "mim_inside_pmos_block", "c_hold_ff", "sw_wn_um", "sw_wp_um", "sw_ron_max_ohm", "sw_clamped",
        "cap_value_ff", "cap_units", "cap_w_um", "cap_h_um", "cap_area_um2",
        "cap_footprint_um2", "cap_over_devices", "pmos_block_w_um",
        "pmos_block_h_um", "cell_w_um", "cell_h_um", "cell_area_um2",
        "bbox_w_um", "bbox_h_um", "bbox_area_um2", "device_area_um2",
        "gate_area_um2", "devices", "dummy_fingers", "pair_pattern",
        "drc_violations", "drc_rules", "density_rules", "render_bytes")


def main(argv):
    wanted = argv or list(CELLS)
    for dd in (WORK, os.path.join(FINAL, "gds"), os.path.join(FINAL, "render")):
        os.makedirs(dd, exist_ok=True)
    print(f"fs_mhz = {FS_HZ / 1e6:g}")
    print(f"bits = {N_BITS}")
    print(f"tg_k_meas_ohm_um = {K_MEAS_OHM_UM:g}")
    print(f"mim_side_125ff_um = {mim_side_for(125e-15):.2f}")
    allm = {}
    for name in wanted:
        kind, sz, tag = CELLS[name]
        c, m = unit_cell(name, kind, sz, tag)
        gds = os.path.join(FINAL, "gds", name + ".gds")
        c.write_gds(gds)
        geom, dens = drc(name, gds)
        m["drc_violations"] = sum(geom.values())
        m["drc_rules"] = ",".join(f"{k}:{v}" for k, v in sorted(geom.items())) or "none"
        m["density_rules"] = ",".join(sorted(dens)) or "none"
        m["render_bytes"] = render(name, gds)
        low = name.lower()
        for k in KEYS:
            v = m[k]
            print(f"{low}_{k} = {v:.3f}" if isinstance(v, float) else f"{low}_{k} = {v}")
        allm[name] = m
    with open(os.path.join(WORK, "floorplan_metrics.json"), "w") as fo:
        json.dump(allm, fo, indent=1, default=str)
    for a, b, tag in (("UC_MIM", "UC_MOM", "min"), ("UC_MIM_125", "UC_MOM_125", "125")):
        if a in allm and b in allm:
            A, B = allm[a], allm[b]
            print(f"area_ratio_mom_over_mim_{tag} = {B['cell_area_um2'] / A['cell_area_um2']:.4f}")
            print(f"area_delta_um2_{tag} = {B['cell_area_um2'] - A['cell_area_um2']:.3f}")
    print(f"cells_built = {len(allm)}")


if __name__ == "__main__":
    main(sys.argv[1:])
