"""The 8-bit minimum-power comparator, drawn with gdsfactory on the gf180mcu plugin.

Circuit: ../../../../comparator_lp/cmp_lp.spice (PMOS-input 5T, clamp,
replica, starved buffer), the design sized for 8 bits over 0.5-2.0 V. The
LVS reference is generated from that file by ../../build.py, never typed:
the 13 transistors unchanged, COUTA dropped (it stands in for the routing
load this layout now provides), and the two ports the circuit does not use
(clk, nbias) left out of the layout.

Each transistor is the plugin's, without its gate-contact pads (ADR 0008,
`_without_gate_pads`). Around each one this file draws the same three
things, so every device is wired the same way:

- gate:   a poly bridge over the finger ends on the gate side, a row of
          contacts on it, and an M1 strap over them spanning the device;
- source: the even S/D columns run out on the other side to an M1 strap
          (a supply rail where the source is a supply);
- drain:  a via1 on every odd column and an M2 strap across the device at
          mid-height.

Floorplan, bottom to top (y), gate straps facing the channels:

    vdd rail (M1) over the n-well tap -------------------------------------
    P2   XRPB   XTAIL             XBST          | gates: pbias, one strap
    P1          XINP     XINN     XBUF2  XBUF4  | gates below, sources above
    N    XCLMP  XRPN  XLOADD   XLOADM   XBUF1  XBUF3  | gates above
    vss rail (M1) over the substrate tap ----------------------------------

XCLMP (body = outa) has its own n-well with an N+ tap wired to outa, 1.4 um
(NW.2b_LV) from the vdd well; the vss tap skips it. Inter-device routing is
vertical M2 (left, outa, tail, rep, bst, outb, dout) and one M3 run for
outa. The inverter pairs XBUF1/XBUF2 and XBUF3/XBUF4 share a gate through
an M1 block between their gate straps.

Pins: inp, inn, pbias on M3 at the top edge; dout on M3 at the right edge;
vdd and vss on the M1 rails.

Finger counts: the plugin's w_gate is per finger and must sit on the 5 nm
grid. cmp_lp.spice's W/nf is off grid for three devices (35.3/9, 43.7/11,
27.2/7), so those use the nearest finger count that divides W exactly
(10, 10, 8). Total W and L are the recipe's; KLayout LVS compares W and L
after combining fingers, not nf.

Rule values in comments are gf180mcu.drc (3.3 V, LV).
"""

from __future__ import annotations

import gdsfactory as gf
from gf180mcu import LAYER
from gf180mcu.cells import nfet, pfet

from .inverter import _features, _rect, _snap, _tap, _without_gate_pads

Box = tuple[float, float, float, float]

# gf180mcu.drc numbers this file relies on (um)
CON = 0.22              # CO.1
CON_PITCH = 0.50        # CO.2a 0.25 space
CON_ENC = 0.07          # CO.3 / CO.4 poly / COMP enclosure of contact
VIA = 0.26              # V1.1 / V2.1
PAD = 0.38              # via landing: 0.06 enclosure (V1.3c / V1.4b end of line)
IMP_ENC = 0.16          # NP.5b / PP.5b
NW_ENC = 0.43           # DF.4c n-well over PCOMP; also NCOMP to n-well
NW_SPACE = 1.40         # NW.2b_LV n-well to n-well, different potential

# gate side, measured from the COMP edge outward
BRIDGE = (0.10, 0.62)   # poly bridge band (PL.5a 0.1 from COMP; the plugin's pads end at 0.46)
GSTRAP = (0.25, 0.63)   # M1 gate strap: 0.26 from the S/D column ends (M1.2a 0.23)
GCON = 0.44             # contact row centre: CO.8 0.17 to COMP, 0.07 poly enclosure at 0.62
# source side
SGAP = 0.30             # S strap starts this far out: 0.31 from the D column ends
RAIL_GAP = 0.66         # a rail clears the poly ends (0.46) so its tap may sit under it
RAIL = 0.80

# internal nets the layout labels, named as in cmp_lp.spice
INTERNAL_NETS = ("left", "tail", "outa", "outb", "rep", "bst")

# (kind, total W, L, nf) -- W and L from cmp_lp.spice; nf see module docstring
DEVICES = {
    "XINP":   ("p", 49.8, 1.0, 12),
    "XINN":   ("p", 49.8, 1.0, 12),
    "XLOADD": ("n", 35.3, 0.5, 10),
    "XLOADM": ("n", 35.3, 0.5, 10),
    "XTAIL":  ("p", 43.7, 1.0, 10),
    "XRPB":   ("p", 5.5, 1.0, 1),
    "XRPN":   ("n", 8.8, 0.5, 2),
    "XCLMP":  ("p", 41.5, 0.5, 10),
    "XBST":   ("p", 27.2, 1.0, 8),
    "XBUF1":  ("n", 2.1, 0.5, 1),
    "XBUF2":  ("p", 1.0, 0.28, 1),
    "XBUF3":  ("n", 8.0, 0.28, 4),
    "XBUF4":  ("p", 16.0, 0.28, 4),
}


def _via(c: gf.Component, lower: int, x: float, y: float) -> None:
    """via1 (lower=1) or via2 (lower=2) at (x, y) with PAD landings on both metals."""
    metals = {1: (LAYER.metal1, LAYER.metal2, LAYER.via1),
              2: (LAYER.metal2, LAYER.metal3, LAYER.via2)}[lower]
    lo, hi, cut = metals
    h, p = VIA / 2, PAD / 2
    _rect(c, cut, x - h, y - h, x + h, y + h)
    _rect(c, lo, x - p, y - p, x + p, y + p)
    _rect(c, hi, x - p, y - p, x + p, y + p)


def _stack(c: gf.Component, x: float, y: float) -> None:
    """M1 to M3 at one point."""
    _via(c, 1, x, y)
    _via(c, 2, x, y)


def _hwire(c, layer, x0, x1, y, w=PAD):
    _rect(c, layer, min(x0, x1) - w / 2, y - w / 2, max(x0, x1) + w / 2, y + w / 2)


def _vwire(c, layer, x, y0, y1, w=PAD):
    _rect(c, layer, x - w / 2, min(y0, y1) - w / 2, x + w / 2, max(y0, y1) + w / 2)


_FETS: dict = {}


def _fet(kind: str, wf: float, l: float, nf: int) -> gf.Component:
    """One pad-stripped plugin transistor per size: XINP/XINN and
    XLOADD/XLOADM reference the same cell, which also keeps the stripped
    copies from colliding by name in the GDS."""
    key = (kind, wf, l, nf)
    if key not in _FETS:
        _FETS[key] = _without_gate_pads((pfet if kind == "p" else nfet)(
            w_gate=wf, l_gate=l, nf=nf, grw=0))
    return _FETS[key]


def _mos(c: gf.Component, name: str, x0: float, yb: float, gate: str,
         s_band: tuple[float, float] | None = None) -> dict:
    """Place one transistor with COMP at (x0, yb) lower left and wire it up.

    gate: 'top' or 'bottom', the side the gate strap is on; the source
    strap is on the other side, at `s_band` (absolute y0, y1) if given,
    else SGAP beyond the COMP, 0.5 um tall.

    Returns the geometry the caller routes to: comp, cols, the gate strap,
    the source strap, the drain strap (M2, None for none) and its centre y.
    """
    kind, w, l, nf = DEVICES[name]
    wf = _snap(w / nf)
    if abs(wf * nf - w) > 1e-6:
        raise ValueError(f"{name}: W={w} over nf={nf} is off the 5 nm grid")
    fet = _fet(kind, wf, l, nf)
    f0 = _features(fet)
    dx, dy = _snap(x0 - f0["comp"][0]), _snap(yb - f0["comp"][1])
    ref = c << fet
    ref.dmove((dx, dy))
    mv = lambda b: (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)  # noqa: E731
    comp = mv(f0["comp"])
    cols = [mv(b) for b in f0["cols"]]
    xl, xr = cols[0][0], cols[-1][2]

    # -- gate
    if gate == "top":
        edge, sgn = comp[3], 1
    else:
        edge, sgn = comp[1], -1
    band = lambda a, b: (min(edge + sgn * a, edge + sgn * b),  # noqa: E731
                         max(edge + sgn * a, edge + sgn * b))
    by0, by1 = band(*BRIDGE)
    _rect(c, LAYER.poly2, xl, by0, xr, by1)
    gy0, gy1 = band(*GSTRAP)
    _rect(c, LAYER.metal1, xl, gy0, xr, gy1)
    yc = edge + sgn * GCON
    span = (xr - xl) - 2 * CON_ENC
    n = int((span - CON) // CON_PITCH) + 1
    xs = (xl + xr) / 2 - ((n - 1) * CON_PITCH) / 2
    for i in range(n):
        xc = xs + i * CON_PITCH
        _rect(c, LAYER.contact, xc - CON / 2, yc - CON / 2, xc + CON / 2, yc + CON / 2)

    # -- source: even columns out to the strap on the far side
    if s_band is None:
        if gate == "top":
            s_band = (comp[1] - SGAP - 0.5, comp[1] - SGAP)
        else:
            s_band = (comp[3] + SGAP, comp[3] + SGAP + 0.5)
    sy0, sy1 = s_band
    _rect(c, LAYER.metal1, xl, sy0, xr, sy1)
    for col in cols[0::2]:
        if gate == "top":
            _rect(c, LAYER.metal1, col[0], sy0, col[2], col[1] + 0.1)
        else:
            _rect(c, LAYER.metal1, col[0], col[3] - 0.1, col[2], sy1)

    # -- drain: via1 on each odd column, M2 across at mid-height
    ymid = _snap((comp[1] + comp[3]) / 2)
    dcols = cols[1::2]
    for col in dcols:
        _via(c, 1, (col[0] + col[2]) / 2, ymid)
    dx0 = (dcols[0][0] + dcols[0][2]) / 2
    dx1 = (dcols[-1][0] + dcols[-1][2]) / 2
    _hwire(c, LAYER.metal2, dx0, dx1, ymid)

    return {"comp": comp, "cols": cols, "gate": (xl, gy0, xr, gy1),
            "gy": _snap((gy0 + gy1) / 2), "src": (xl, sy0, xr, sy1),
            "dy": ymid, "dx": (dx0, dx1), "xc": _snap((comp[0] + comp[2]) / 2)}


def _comp_width(name: str) -> float:
    _, _, l, nf = DEVICES[name]
    return round(nf * (l + 0.52) + 0.36, 3)


def _label(c, layer, text, x, y):
    c.add_label(text, position=(_snap(x), _snap(y)), layer=layer)


@gf.cell
def CMP_LP() -> gf.Component:
    """cmp_lp as a layout: pins inp, inn, pbias, dout (M3), vdd, vss (M1 rails)."""
    c = gf.Component()
    c.name = "CMP_LP"

    # ---- rows (COMP bottom edges) and rails
    y_n = 0.0
    y_p1 = 6.2      # channel: N gate straps <= 5.03, P1 gate straps >= 5.57
    y_p2 = 12.2     # P1 source straps <= 11.15, pbias strap from 11.57
    vss = (y_n - RAIL_GAP - RAIL, y_n - RAIL_GAP)
    p2_top = y_p2 + max(DEVICES[n][1] / DEVICES[n][3] for n in ("XTAIL", "XRPB", "XBST"))
    vdd = (_snap(p2_top + RAIL_GAP), _snap(p2_top + RAIL_GAP + RAIL))

    # ---- x placement (COMP left edges)
    x_tap = 0.6                                    # clamp-well N+ tap
    x_clmp = x_tap + 1.0
    nw_c = (x_tap - NW_ENC, x_clmp + _comp_width("XCLMP") + NW_ENC)
    x_inp = _snap(nw_c[1] + NW_SPACE + NW_ENC + 0.2)
    x_inn = _snap(x_inp + _comp_width("XINP") + 1.0)
    xc_inp = x_inp + _comp_width("XINP") / 2
    xc_inn = x_inn + _comp_width("XINN") / 2
    x_lod = _snap(xc_inp - _comp_width("XLOADD") / 2)
    x_lom = _snap(xc_inn - _comp_width("XLOADM") / 2)
    x_tail = _snap((x_inp + x_inn + _comp_width("XINN")) / 2 - _comp_width("XTAIL") / 2)
    x_rpb = x_inp
    x_rpn = _snap(nw_c[1] + NW_ENC + 1.0)
    x_bst = _snap(x_tail + _comp_width("XTAIL") + 1.0)
    x_b2 = _snap(x_inn + _comp_width("XINN") + 1.0)
    x_b4 = _snap(x_bst + _comp_width("XBST") + 1.0)

    # ---- devices
    d = {}
    d["XCLMP"] = _mos(c, "XCLMP", x_clmp, y_n, "top", s_band=vss)
    d["XRPN"] = _mos(c, "XRPN", x_rpn, y_n, "top", s_band=vss)
    d["XLOADD"] = _mos(c, "XLOADD", x_lod, y_n, "top", s_band=vss)
    d["XLOADM"] = _mos(c, "XLOADM", x_lom, y_n, "top", s_band=vss)
    d["XINP"] = _mos(c, "XINP", x_inp, y_p1, "bottom")
    d["XINN"] = _mos(c, "XINN", x_inn, y_p1, "bottom")
    d["XBUF2"] = _mos(c, "XBUF2", x_b2, y_p1, "bottom")
    d["XBUF4"] = _mos(c, "XBUF4", x_b4, y_p1, "bottom", s_band=vdd)
    # XBUF1 / XBUF3 under XBUF2 / XBUF4, drain column on the same x
    b2_d = d["XBUF2"]["dx"][0]
    x_b1 = _snap(b2_d - 0.18 - (DEVICES["XBUF1"][2] + 0.52))
    d["XBUF1"] = _mos(c, "XBUF1", x_b1, y_n, "top", s_band=vss)
    d["XBUF3"] = _mos(c, "XBUF3", x_b4, y_n, "top", s_band=vss)
    d["XRPB"] = _mos(c, "XRPB", x_rpb, y_p2, "bottom", s_band=vdd)
    d["XTAIL"] = _mos(c, "XTAIL", x_tail, y_p2, "bottom", s_band=vdd)
    d["XBST"] = _mos(c, "XBST", x_bst, y_p2, "bottom", s_band=vdd)

    x_right = _snap(d["XBUF4"]["comp"][2] + NW_ENC + 0.5)
    x_left = 0.0

    # ---- rails, taps, wells
    _rect(c, LAYER.metal1, x_left, vss[0], x_right, vss[1])
    _rect(c, LAYER.metal1, x_left, vdd[0], x_right, vdd[1])
    # substrate tap under vss, clear of the clamp well (P+ COMP to n-well 0.43)
    _tap(c, LAYER.pplus, nw_c[1] + NW_ENC + 0.1, vss[0] + 0.15, x_right - 0.3, vss[1] - 0.15)
    pcomps = [d[n]["comp"] for n in ("XINP", "XINN", "XBUF2", "XBUF4", "XRPB", "XTAIL", "XBST")]
    nw_x0 = min(b[0] for b in pcomps) - NW_ENC
    nw_x1 = max(b[2] for b in pcomps) + NW_ENC
    _tap(c, LAYER.nplus, nw_x0 + NW_ENC, vdd[0] + 0.15, nw_x1 - NW_ENC, vdd[1] - 0.15)
    _rect(c, LAYER.nwell, nw_x0, y_p1 - NW_ENC, nw_x1, vdd[1] - 0.15 + NW_ENC)

    # clamp well: N+ tap column at its left, wired to outa
    cc = d["XCLMP"]["comp"]
    t = (x_tap, cc[1] + 0.3, x_tap + 0.5, cc[3] - 0.3)
    _rect(c, LAYER.comp, *t)
    _rect(c, LAYER.nplus, t[0] - IMP_ENC, t[1] - IMP_ENC, t[2] + IMP_ENC, t[3] + IMP_ENC)
    xt = (t[0] + t[2]) / 2
    ncon = int(((t[3] - t[1]) - 2 * CON_ENC - CON) // CON_PITCH) + 1
    yt0 = (t[1] + t[3]) / 2 - (ncon - 1) * CON_PITCH / 2
    for i in range(ncon):
        yc = yt0 + i * CON_PITCH
        _rect(c, LAYER.contact, xt - CON / 2, yc - CON / 2, xt + CON / 2, yc + CON / 2)
    _rect(c, LAYER.metal1, xt - 0.17, t[1] + 0.01, xt + 0.17, t[3] - 0.01)
    _rect(c, LAYER.nwell, nw_c[0], cc[1] - NW_ENC, nw_c[1], cc[3] + NW_ENC)

    # ---- outa: clamp drain + well tap, XINN / XLOADM drains, XBUF1/XBUF2 gates
    cl = d["XCLMP"]
    x_cl_v2 = _snap(cl["dx"][1] + 0.54)
    _hwire(c, LAYER.metal2, xt, x_cl_v2, cl["dy"])
    _via(c, 1, xt, cl["dy"])
    _via(c, 2, x_cl_v2, cl["dy"])
    y_outa = 3.0
    x_outa = d["XINN"]["xc"]
    _vwire(c, LAYER.metal2, x_outa, d["XLOADM"]["dy"], d["XINN"]["dy"])
    _via(c, 2, x_outa, y_outa)
    # XBUF1/XBUF2 gate block and the via stack onto it
    g1, g2 = d["XBUF1"]["gate"], d["XBUF2"]["gate"]
    _rect(c, LAYER.metal1, min(g1[0], g2[0]), g1[1], max(g1[2], g2[2]), g2[3])
    x_og = _snap(min(g1[0], g2[0]) + 0.2)
    y_og = 4.0
    _stack(c, x_og, y_og)
    _vwire(c, LAYER.metal3, x_cl_v2, cl["dy"], y_outa)
    _hwire(c, LAYER.metal3, x_cl_v2, x_og, y_outa)
    _vwire(c, LAYER.metal3, x_og, y_outa, y_og)

    # ---- left: XINP drain, XLOADD drain, XLOADD / XLOADM gates
    gd, gm = d["XLOADD"]["gate"], d["XLOADM"]["gate"]
    _rect(c, LAYER.metal1, gd[0], gd[1], gm[2], gd[3])
    x_left_n = d["XINP"]["xc"]
    _vwire(c, LAYER.metal2, x_left_n, d["XLOADD"]["dy"], d["XINP"]["dy"])
    _via(c, 1, x_left_n, d["XLOADD"]["gy"])

    # ---- tail: XTAIL drain to the XINP / XINN source strap
    si, sn = d["XINP"]["src"], d["XINN"]["src"]
    _rect(c, LAYER.metal1, si[0], si[1], sn[2], si[3])
    x_tl = d["XTAIL"]["xc"]
    y_tl = _snap((si[1] + si[3]) / 2)
    _vwire(c, LAYER.metal2, x_tl, y_tl, d["XTAIL"]["dy"])
    _via(c, 1, x_tl, y_tl)

    # ---- pbias: one gate strap over XRPB, XTAIL, XBST
    gr, gb = d["XRPB"]["gate"], d["XBST"]["gate"]
    _rect(c, LAYER.metal1, gr[0], gr[1], gb[2], gr[3])

    # ---- rep: XRPB drain, XRPN drain + gate, XCLMP gate, on an M2 lane
    #      between the clamp well and the vdd well
    x_rep = _snap((nw_c[1] + nw_x0) / 2)
    rp = d["XRPB"]
    _hwire(c, LAYER.metal2, x_rep, rp["dx"][0], rp["dy"])
    rn = d["XRPN"]
    _hwire(c, LAYER.metal2, x_rep, rn["dx"][0], rn["dy"])
    _vwire(c, LAYER.metal2, x_rep, rn["dy"], rp["dy"])
    gc, gn = d["XCLMP"]["gate"], d["XRPN"]["gate"]
    _rect(c, LAYER.metal1, gc[2], gc[1], x_rep + PAD / 2, gc[3])
    _rect(c, LAYER.metal1, x_rep - PAD / 2, gn[1], gn[0], gn[3])
    _via(c, 1, x_rep, _snap((max(gc[1], gn[1]) + min(gc[3], gn[3])) / 2))

    # ---- bst: XBST drain to the XBUF2 source strap
    b2s = d["XBUF2"]["src"]
    x_bst_v = _snap((d["XBUF2"]["cols"][0][0] + d["XBUF2"]["cols"][0][2]) / 2)
    y_b2s = _snap((b2s[1] + b2s[3]) / 2)
    bs = d["XBST"]
    _hwire(c, LAYER.metal2, bs["dx"][0], x_bst_v, bs["dy"])
    _vwire(c, LAYER.metal2, x_bst_v, y_b2s, bs["dy"])
    _via(c, 1, x_bst_v, y_b2s)

    # ---- outb: XBUF1 / XBUF2 drains to the XBUF3 / XBUF4 gate block
    x_ob = b2_d
    _vwire(c, LAYER.metal2, x_ob, d["XBUF1"]["dy"], d["XBUF2"]["dy"])
    g3, g4 = d["XBUF3"]["gate"], d["XBUF4"]["gate"]
    _rect(c, LAYER.metal1, g3[0], g3[1], g3[2], g4[3])
    x_obg = _snap(g3[0] + 0.19)
    _hwire(c, LAYER.metal2, x_ob, x_obg, y_og)
    _via(c, 1, x_obg, y_og)

    # ---- dout: XBUF3 / XBUF4 drains, out on M3 at the right edge
    x_do = d["XBUF4"]["dx"][0]
    _vwire(c, LAYER.metal2, x_do, d["XBUF3"]["dy"], d["XBUF4"]["dy"])
    _via(c, 2, x_do, y_og)
    _hwire(c, LAYER.metal3, x_do, x_right - PAD / 2, y_og)
    _label(c, LAYER.metal3_label, "dout", x_right - 0.3, y_og)

    # ---- inp / inn / pbias: via stacks on the gate straps, M3 up to the top edge
    y_top = vdd[1]
    x_inp_p = _snap(d["XINP"]["xc"] - 3.9)
    x_inn_p = _snap(d["XINN"]["xc"] + 3.9)
    x_pb_p = _snap(d["XRPB"]["comp"][0] + 0.6)
    for net, x, y in (("inp", x_inp_p, d["XINP"]["gy"]),
                      ("inn", x_inn_p, d["XINN"]["gy"]),
                      ("pbias", x_pb_p, d["XRPB"]["gy"])):
        _stack(c, x, y)
        _vwire(c, LAYER.metal3, x, y, y_top - PAD / 2)
        _label(c, LAYER.metal3_label, net, x, y_top - 0.3)

    _label(c, LAYER.metal1_label, "vdd", (x_left + x_right) / 2, (vdd[0] + vdd[1]) / 2)
    _label(c, LAYER.metal1_label, "vss", (x_left + x_right) / 2, (vss[0] + vss[1]) / 2)

    # ---- internal net names, cmp_lp.spice's, so that the extracted netlist
    #      carries the nodes the benches probe (xdut.left, .tail, .outa, ...)
    y_ch = _snap((d["XLOADD"]["gate"][3] + d["XINP"]["gate"][1]) / 2)
    at = {"left": (x_left_n, y_ch), "outa": (x_outa, y_ch),
          "tail": (x_tl, _snap(y_tl + 0.6)), "rep": (x_rep, y_ch),
          "bst": (x_bst_v, _snap(y_b2s + 1.0)), "outb": (x_ob, _snap(y_og - 1.0))}
    for net in INTERNAL_NETS:
        _label(c, LAYER.metal2_label, net, *at[net])

    # ---- the two n-wells as drawn, for the well-junction diodes extraction
    #      does not produce (a clamp-well junction loads outa)
    wells = {"outa": (nw_c[0], cc[1] - NW_ENC, nw_c[1], cc[3] + NW_ENC),
             "vdd": (nw_x0, y_p1 - NW_ENC, nw_x1, vdd[1] - 0.15 + NW_ENC)}
    for net, (a, b, e, f) in wells.items():
        c.info[f"nwell_{net}_area_um2"] = round((e - a) * (f - b), 4)
        c.info[f"nwell_{net}_perim_um"] = round(2 * ((e - a) + (f - b)), 4)

    c.info["devices"] = len(DEVICES)
    c.info["pins"] = "inp inn dout vdd vss pbias"
    return c


if __name__ == "__main__":
    import gf180mcu

    gf180mcu.PDK.activate()
    CMP_LP().show()
