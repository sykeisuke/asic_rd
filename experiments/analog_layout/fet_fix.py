"""DRC-clean 3.3 V fets for gf180mcuD built from the gf180mcu plugin cells.

Plugin nfet/pfet fail two metal1 rules on the Run 3 deck for any parameters:
the gate-contact metal1 pad is 0.34 x 0.23 um (M1.3 min area 0.1444 um^2) and
its corners are ~0.21 um from the S/D metal1 straps (M1.2a spacing 0.23 um).
The pad cannot grow because the plugin's COMP body ring starts 0.11 um above
the gate poly head.

Fix (geometry surgery after flattening the plugin cell):
  1. remove the plugin's body ring (COMP/implant/contact/metal1 outside the
     device core) -- body ties are drawn separately per cell row;
  2. delete the gate contacts and pads, extend the poly head by 0.04 um, and
     redraw the contact 0.04 um further out with a 0.34 x 0.50 um metal1 pad:
     area 0.17 um^2, diagonal clearance to the S/D straps ~0.244 um,
     CO.6 enclosure 0.06/0.06/0.005 satisfied, CO.3 poly overlap 0.07 kept.

Run: experiments/analog_layout/run.sh experiments/analog_layout/fet_fix.py fet_fix
"""
import gdsfactory as gf
import gf180mcu
import klayout.db as db

PDK = gf180mcu.PDK; PDK.activate()
L = {"comp": (22, 0), "poly2": (30, 0), "pplus": (31, 0), "nplus": (32, 0),
     "contact": (33, 0), "metal1": (34, 0)}
CORE_X = 0.85                         # plugin ring lies outside |x| > CORE_X ...
CORE_Y_MARGIN = 0.50                  # ... and |y| > w_gate/2 + margin (gate head ends at w/2+0.46)
SHIFT = 0.04                          # move gate contact outward by this much
PAD_W, PAD_H = 0.34, 0.50             # new gate metal1 pad
CON = 0.22

def _shapes(c, layer):
    ly = c.kcl.layout; return ly, ly.cell(c.name).shapes(ly.layer(*layer))

def _surgery(c: gf.Component, w_gate: float, kind: str) -> dict:
    ly = c.kcl.layout; dbu = ly.dbu
    core_y = w_gate / 2 + CORE_Y_MARGIN
    stats = {"ring_shapes_removed": 0, "gate_pads_moved": 0}
    # 1) drop the body ring
    for lname in ("comp", "pplus", "nplus", "contact", "metal1"):
        _, sh = _shapes(c, L[lname])
        for s in list(sh.each()):
            b = s.bbox()
            cx, cy = (b.left + b.right) / 2 * dbu, (b.bottom + b.top) / 2 * dbu
            outside = abs(cx) > CORE_X or abs(cy) > core_y
            # flatten() merges the ring into one polygon (with a hole) whose bbox
            # encloses the core: catch that too
            encloses = (b.left * dbu < -CORE_X and b.right * dbu > CORE_X
                        and b.bottom * dbu < -core_y and b.top * dbu > core_y)
            if outside or encloses:
                sh.erase(s); stats["ring_shapes_removed"] += 1
    # 1b) redraw the ring's two side legs as body taps (they never conflicted with
    #     the gate pad; only the top/bottom bars did). Geometry mirrors the plugin ring.
    rect = lambda layer, x0, y0, x1, y1: c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)
    hl = w_gate / 2 + 0.415                        # leg half-length (plugin: 1.415 for w=2)
    implant = L["pplus"] if kind == "nfet" else L["nplus"]
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.91, sx * 1.27))
        rect(L["comp"], x0, -hl, x1, hl)
        # implant: 0.16 um enclosure of the tap COMP (NP/PP.5d), width >= 0.4 (NP/PP.1);
        # on the device side stop at the S/D implant edge so the two implants butt cleanly
        enc = 0.16
        ix0, ix1 = x0 - enc, x1 + enc
        rect(implant, ix0, -hl - enc, ix1, hl + enc)
        rect(L["metal1"], x0 + 0.065, -(hl - 0.01), x1 - 0.065, hl - 0.01)
        y = -(hl - 0.30)
        while y + CON <= hl - 0.30 + 1e-6:
            rect(L["contact"], x0 + 0.07, y, x0 + 0.07 + CON, y + CON); y += 0.50
            stats["tap_contacts"] = stats.get("tap_contacts", 0) + 1
    # 2) rebuild gate contacts: find plugin gate contacts (0.22 squares on the gate axis)
    _, con = _shapes(c, L["contact"])
    gate_cons = []
    for s in list(con.each()):
        b = s.bbox()
        if abs(b.width() * dbu - CON) < 1e-3 and abs((b.left + b.right) / 2 * dbu) < 0.15:
            gate_cons.append((b.bottom * dbu, b.top * dbu, b.bottom > 0)); con.erase(s)
    _, m1 = _shapes(c, L["metal1"])
    for s in list(m1.each()):                      # plugin gate pads: 0.34 x 0.23 on the axis
        b = s.bbox()
        if abs(b.width() * dbu - 0.34) < 1e-3 and abs(b.height() * dbu - 0.23) < 1e-3 and abs((b.left + b.right) / 2 * dbu) < 0.15:
            m1.erase(s)
    _, poly = _shapes(c, L["poly2"])
    # gate-axis poly extent (after flatten the gate and its heads may be one polygon)
    axis = [s.bbox() for s in poly.each() if abs((s.bbox().left + s.bbox().right) / 2 * dbu) < 0.15]
    poly_top = max(b.top for b in axis) * dbu; poly_bot = min(b.bottom for b in axis) * dbu
    rect = lambda layer, x0, y0, x1, y1: c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)
    for (y0, y1, up) in gate_cons:
        sgn = 1 if up else -1
        ny0, ny1 = y0 + sgn * SHIFT, y1 + sgn * SHIFT
        rect(L["contact"], -CON / 2, min(ny0, ny1), CON / 2, max(ny0, ny1))
        # poly head extension so CO.3 (0.07 poly overlap) holds
        hy = poly_top if up else poly_bot
        rect(L["poly2"], -0.18, min(hy, hy + sgn * SHIFT), 0.18, max(hy, hy + sgn * SHIFT))
        # metal1 pad: 0.005 enclosure on the inner end, long on the outer end
        inner = (ny0 - 0.005) if up else (ny1 + 0.005)
        outer = inner + sgn * PAD_H
        rect(L["metal1"], -PAD_W / 2, min(inner, outer), PAD_W / 2, max(inner, outer))
        stats["gate_pads_moved"] += 1
    return stats

def _fixed(kind: str, w_gate: float, l_gate: float, **kw) -> gf.Component:
    c = gf.Component()
    c << PDK.get_component(kind, l_gate=l_gate, w_gate=w_gate, volt="3.3V", bulk="None", **kw)
    c.flatten()
    c.info.update(_surgery(c, w_gate, kind))
    return c

@gf.cell
def nfet_fixed(w_gate: float = 2.0, l_gate: float = 0.28, **kw) -> gf.Component:
    return _fixed("nfet", w_gate, l_gate, **kw)

@gf.cell
def pfet_fixed(w_gate: float = 4.0, l_gate: float = 0.28, **kw) -> gf.Component:
    return _fixed("pfet", w_gate, l_gate, **kw)

if __name__ == "__main__":
    t = gf.Component()
    n = t << nfet_fixed(); p = t << pfet_fixed()
    p.dmovex(n.dxmax - p.dxmin + 2.0)
    print("nfet:", dict(nfet_fixed().info), " pfet:", dict(pfet_fixed().info))
    t.write_gds("work/fet_fix.gds"); print("wrote work/fet_fix.gds")
