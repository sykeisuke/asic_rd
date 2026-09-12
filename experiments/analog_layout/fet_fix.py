"""DRC-clean 3.3 V fets for gf180mcuD built from the gf180mcu plugin cells
(single- or multi-finger).

Plugin nfet/pfet fail two metal1 rules on the Run 3 deck for any parameters:
the gate-contact metal1 pad is 0.34 x 0.23 um (M1.3 min area 0.1444 um^2) and
its corners are ~0.21 um from the S/D metal1 straps (M1.2a spacing 0.23 um).
The pad cannot grow because the plugin's COMP body ring starts 0.11 um above
the gate poly head.

Fix (geometry surgery after flattening the plugin cell):
  1. remove the plugin's body ring (everything not overlapping the device core);
  2. redraw the ring's two side legs as in-well body taps (DF.13/14: tap within
     20 um) with 0.16 um implant enclosure (NP/PP.1, NP/PP.5d);
  3. for every gate contact: delete it and its pad, extend the poly head by
     0.04 um, redraw the contact 0.04 um further out under a 0.34 x 0.50 um
     metal1 pad (area 0.17 um^2, ~0.244 um to the S/D straps, CO.6 enclosure
     0.06/0.06/0.005, CO.3 poly overlap 0.07 kept).

Run: experiments/analog_layout/run.sh experiments/analog_layout/fet_fix.py fet_fix
"""
import gdsfactory as gf
import gf180mcu
import klayout.db as db

PDK = gf180mcu.PDK; PDK.activate()
L = {"comp": (22, 0), "poly2": (30, 0), "pplus": (31, 0), "nplus": (32, 0),
     "contact": (33, 0), "metal1": (34, 0)}
SHIFT = 0.04                          # move gate contacts outward by this much
PAD_W, PAD_H = 0.34, 0.50             # new gate metal1 pad
CON = 0.22
LEG_GAP, LEG_W = 0.33, 0.36           # tap leg placement mirrors the plugin ring
IMPL_ENC = 0.16

def _shapes(c, layer):
    ly = c.kcl.layout; return ly, ly.cell(c.name).shapes(ly.layer(*layer))

def _bbox_um(b, dbu):
    return b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu

def _surgery(c: gf.Component, w_gate: float, kind: str) -> dict:
    ly = c.kcl.layout; dbu = ly.dbu
    stats = {"ring_shapes_removed": 0, "gate_pads_moved": 0, "tap_contacts": 0}
    rect = lambda layer, x0, y0, x1, y1: c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)

    # --- device core = union bbox of the gate poly fingers ---------------------------
    _, poly = _shapes(c, L["poly2"])
    pb = [_bbox_um(s.bbox(), dbu) for s in poly.each()]
    px0 = min(b[0] for b in pb); px1 = max(b[2] for b in pb)
    py0 = min(b[1] for b in pb); py1 = max(b[3] for b in pb)
    # S/D COMP: comp shapes overlapping the poly x-span -> core x extent
    _, comp = _shapes(c, L["comp"])
    core = [_bbox_um(s.bbox(), dbu) for s in comp.each()]
    sd = [b for b in core if b[2] > px0 - 0.5 and b[0] < px1 + 0.5 and b[3] - b[1] <= w_gate + 1e-3]
    cx0 = min(b[0] for b in sd); cx1 = max(b[2] for b in sd)
    core_x0, core_x1 = cx0 - 0.1, cx1 + 0.1
    core_y = w_gate / 2 + 0.50                        # poly heads end at w/2 + 0.46

    # 1) drop the body ring: shapes outside the core, or enclosing it (merged ring polygon)
    for lname in ("comp", "pplus", "nplus", "contact", "metal1"):
        _, sh = _shapes(c, L[lname])
        for s in list(sh.each()):
            x0, y0, x1, y1 = _bbox_um(s.bbox(), dbu)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            outside = cx < core_x0 or cx > core_x1 or abs(cy) > core_y
            encloses = x0 < core_x0 and x1 > core_x1 and y0 < -core_y and y1 > core_y
            if outside or encloses:
                sh.erase(s); stats["ring_shapes_removed"] += 1

    # 2) side-leg body taps inside the well
    hl = w_gate / 2 + 0.415
    implant = L["pplus"] if kind == "nfet" else L["nplus"]
    for (lx0, lx1) in ((cx0 - LEG_GAP - LEG_W, cx0 - LEG_GAP), (cx1 + LEG_GAP, cx1 + LEG_GAP + LEG_W)):
        rect(L["comp"], lx0, -hl, lx1, hl)
        rect(implant, lx0 - IMPL_ENC, -hl - IMPL_ENC, lx1 + IMPL_ENC, hl + IMPL_ENC)
        rect(L["metal1"], lx0 + 0.065, -(hl - 0.01), lx1 - 0.065, hl - 0.01)
        y = -(hl - 0.30)
        while y + CON <= hl - 0.30 + 1e-6:
            rect(L["contact"], lx0 + 0.07, y, lx0 + 0.07 + CON, y + CON); y += 0.50
            stats["tap_contacts"] += 1

    # 3) gate contacts: 0.22 squares lying beyond the active (|y| > w/2)
    _, con = _shapes(c, L["contact"])
    gate_cons = []
    for s in list(con.each()):
        x0, y0, x1, y1 = _bbox_um(s.bbox(), dbu)
        gx = (x0 + x1) / 2
        on_finger = any(b[0] - 0.02 <= gx <= b[2] + 0.02 for b in pb)
        if abs((x1 - x0) - CON) < 1e-3 and abs((y0 + y1) / 2) > w_gate / 2 and on_finger:
            gate_cons.append((gx, y0, y1, y0 > 0)); con.erase(s)
        elif abs((y0 + y1) / 2) > w_gate / 2 and not on_finger:
            con.erase(s); stats["ring_shapes_removed"] += 1      # stray ring contact
    stats["core_x"] = (round(core_x0, 3), round(core_x1, 3))
    _, m1 = _shapes(c, L["metal1"])
    for s in list(m1.each()):                       # plugin gate pads: 0.34 x 0.23
        x0, y0, x1, y1 = _bbox_um(s.bbox(), dbu)
        if abs((x1 - x0) - 0.34) < 1e-3 and abs((y1 - y0) - 0.23) < 1e-3:
            m1.erase(s)
    for (gx, y0, y1, up) in gate_cons:
        sgn = 1 if up else -1
        ny0, ny1 = y0 + sgn * SHIFT, y1 + sgn * SHIFT
        rect(L["contact"], gx - CON / 2, min(ny0, ny1), gx + CON / 2, max(ny0, ny1))
        # poly head under this contact: extend outward by SHIFT so CO.3 (0.07) holds
        heads = [b for b in pb if b[0] - 0.2 <= gx <= b[2] + 0.2 and ((b[3] > 0) if up else (b[1] < 0))]
        if heads:
            hy = max(b[3] for b in heads) if up else min(b[1] for b in heads)
        else:                                       # fall back to the global poly extent
            hy = py1 if up else py0
        rect(L["poly2"], gx - 0.18, min(hy, hy + sgn * SHIFT), gx + 0.18, max(hy, hy + sgn * SHIFT))
        inner = (ny0 - 0.005) if up else (ny1 + 0.005)
        outer = inner + sgn * PAD_H
        rect(L["metal1"], gx - PAD_W / 2, min(inner, outer), gx + PAD_W / 2, max(inner, outer))
        stats["gate_pads_moved"] += 1
    return stats

def _fixed(kind: str, w_gate: float, l_gate: float, nf: int, **kw) -> gf.Component:
    c = gf.Component()
    c << PDK.get_component(kind, l_gate=l_gate, w_gate=w_gate, nf=nf, volt="3.3V", bulk="None", **kw)
    c.flatten()
    c.info.update(_surgery(c, w_gate, kind))
    c.info.update(dict(w_finger_um=w_gate, nf=nf, w_total_um=w_gate * nf, l_um=l_gate))
    return c

@gf.cell
def nfet_fixed(w_gate: float = 1.0, l_gate: float = 0.28, nf: int = 10, **kw) -> gf.Component:
    """w_gate is the per-finger width (plugin convention); total W = w_gate * nf."""
    return _fixed("nfet", w_gate, l_gate, nf, **kw)

@gf.cell
def pfet_fixed(w_gate: float = 2.0, l_gate: float = 0.28, nf: int = 10, **kw) -> gf.Component:
    return _fixed("pfet", w_gate, l_gate, nf, **kw)

if __name__ == "__main__":
    t = gf.Component()
    n = t << nfet_fixed(); p = t << pfet_fixed()
    p.dmovex(n.dxmax - p.dxmin + 2.0)
    for nm, cell in (("nfet", nfet_fixed()), ("pfet", pfet_fixed())):
        b = cell.dbbox(); print(f"{nm}: {dict(cell.info)}  size {b.width():.2f} x {b.height():.2f} um")
    t.write_gds("work/fet_fix.gds"); print("wrote work/fet_fix.gds")
