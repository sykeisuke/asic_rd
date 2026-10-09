"""CMOS inverter drawn with gdsfactory on the gf180mcu PDK plugin.

Same devices as ../../../spice/INV.spice -- nfet_03v3 3u/0.28u nf=2 and
pfet_03v3 6u/0.28u nf=2 -- so this cell and the cicpy-generated INV can
be compared side by side. The netlist for LVS is ../../INV_GF.spice.

The plugin draws each transistor: COMP, poly fingers with a 0.36 um
poly pad at both ends of every finger, contacts, the M1 source/drain
columns, the implant, and (pfet) the n-well. It also puts a contacted M1
pad on every poly pad. Those M1 pads sit 0.115 um beside the S/D columns
and 0.175 um above them, 0.209 um corner to corner, and gf180mcu.drc's
M1.2a is a Euclidean 0.23 um check: measured, every pad fails it and the
six pads a cell does not wire up fail M1.3 (min area) as well. Magic's
DRC, which the plugin was written against, does not measure corners.
So this file takes each transistor WITHOUT those pads (M1 and contact
beyond the COMP edge are dropped from a flattened copy; the poly pads
stay) and adds what turns two transistors into a cell:

- a poly bridge over the finger ends facing the channel, tying the two
  fingers together and reaching past the device on the left, where it
  carries the gate contact -- 0.3 um clear of the S/D columns;
- A on M1 down the left edge, joining the two gate contacts;
- Y on M1 straight up the centre, drain column to drain column;
- M1 rails, VDD above the pfet and VSS below the nfet, with a substrate
  tap (P+) resp. well tap (N+) under each, and the source columns run
  out to the rails;
- pin labels on the M1 label layer, which KLayout LVS reads.

Everything is M1 and poly; no via. Coordinates are read back from the
plugin's polygons rather than typed in, so another width or finger
count moves the routing with the devices. Rule values in comments are
gf180mcu.drc (3.3 V, LV).
"""

from __future__ import annotations

import gdsfactory as gf
from gf180mcu import LAYER
from gf180mcu.cells import nfet, pfet

# INV.spice sizes. W is the total width; the plugin's w_gate is per finger.
L_GATE = 0.28
W_N = 3.0
W_P = 6.0
NF = 2

# gf180mcu.drc numbers this file relies on (um)
GRID = 0.005            # manufacturing grid
M1_SPACE = 0.23         # M1.2a, Euclidean
CON = 0.22              # CO.1 contact size
CON_PITCH = 0.50        # CO.2 wants >= 0.25 space; roomy
CON_ENC_COMP = 0.07     # CO.3 COMP enclosure of contact (CO.4: same for poly)
CON_ENC_M1 = 0.06       # CO.6 M1 enclosure of contact, end-of-line value
IMP_ENC = 0.16          # NP.5b / PP.5b implant enclosure of COMP
NWELL_ENC = 0.43        # DF.4 n-well enclosure of P+ COMP / space to N+ COMP
POLY_COMP_SPACE = 0.10  # PL.5a poly to unrelated COMP

Box = tuple[float, float, float, float]


def _snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 3)


def _boxes(comp: gf.Component, layer_name: str) -> list[Box]:
    """Bounding boxes, in um, of every polygon on one layer of `comp`."""
    dbu = comp.kcl.dbu
    out = []
    for poly in comp.get_polygons(by="name").get(layer_name, []):
        b = poly.bbox()
        out.append((b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu))
    return out


def _union(boxes: list[Box]) -> Box:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _shift(b: Box, dy: float) -> Box:
    return (b[0], b[1] + dy, b[2], b[3] + dy)


def _rect(c: gf.Component, layer, x0: float, y0: float, x1: float, y1: float) -> None:
    x0, y0, x1, y1 = (_snap(v) for v in (x0, y0, x1, y1))
    c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)


def _without_gate_pads(fet: gf.Component) -> gf.Component:
    """The plugin transistor minus the contacted M1 pads at the finger ends.

    Every M1 or contact shape lying wholly above or below the COMP is a
    gate pad (the S/D columns end 0.01 um inside the COMP). The poly pads
    are kept; the cell contacts the gate elsewhere."""
    comp = _union(_boxes(fet, "comp"))
    dbu = fet.kcl.dbu
    flat = fet.dup()
    flat.flatten()
    out = gf.Component()
    out.name = fet.name + "_nopads"
    layout = flat.kcl.layout
    #- LAYER entries are kdb.LayerInfo in gdsfactory 9, plain tuples earlier
    ld = lambda lay: (lay.layer, lay.datatype) if hasattr(lay, "layer") else tuple(lay)  # noqa: E731
    drop = {ld(LAYER.metal1), ld(LAYER.contact)}
    for li in layout.layer_indexes():
        info = layout.get_info(li)
        is_pad_layer = (info.layer, info.datatype) in drop
        dst = out.kdb_cell.shapes(out.kcl.layer(info))
        for sh in flat.kdb_cell.shapes(li).each():
            if is_pad_layer:
                b = sh.bbox()
                if b.bottom * dbu >= comp[3] - 1e-6 or b.top * dbu <= comp[1] + 1e-6:
                    continue
            dst.insert(sh)
    return out


def _features(fet: gf.Component) -> dict:
    """Where the plugin put things, read from its polygons.

    comp:  the active area
    cols:  the M1 source/drain columns, left to right (nf + 1 of them)
    poly:  fingers and end pads together
    """
    comp = _union(_boxes(fet, "comp"))
    h = comp[3] - comp[1]
    m1 = _boxes(fet, "metal1")
    return {
        "comp": comp,
        "cols": sorted((b for b in m1 if b[3] - b[1] > 0.8 * h), key=lambda b: b[0]),
        "poly": _union(_boxes(fet, "poly2")),
    }


def _tap(c: gf.Component, implant, x0: float, y0: float, x1: float, y1: float) -> None:
    """A row of contacted COMP with its implant: substrate or well tie.

    The M1 over it is the rail, drawn by the caller."""
    _rect(c, LAYER.comp, x0, y0, x1, y1)
    _rect(c, implant, x0 - IMP_ENC, y0 - IMP_ENC, x1 + IMP_ENC, y1 + IMP_ENC)
    span = (x1 - x0) - 2 * CON_ENC_COMP
    n = int((span - CON) // CON_PITCH) + 1
    total = (n - 1) * CON_PITCH + CON
    xs = (x0 + x1) / 2 - total / 2
    yc = (y0 + y1) / 2
    for i in range(n):
        xc = xs + i * CON_PITCH + CON / 2
        _rect(c, LAYER.contact, xc - CON / 2, yc - CON / 2, xc + CON / 2, yc + CON / 2)


def _poly_contact(c: gf.Component, xc: float, yc: float) -> Box:
    """One contact on poly with its M1 landing; returns the M1 box."""
    _rect(c, LAYER.contact, xc - CON / 2, yc - CON / 2, xc + CON / 2, yc + CON / 2)
    m1 = (xc - CON / 2 - CON_ENC_M1, yc - CON / 2 - CON_ENC_M1,
          xc + CON / 2 + CON_ENC_M1, yc + CON / 2 + CON_ENC_M1)
    _rect(c, LAYER.metal1, *m1)
    return m1


_DEFAULTS = dict(w_n=W_N, w_p=W_P, l_gate=L_GATE, nf=NF, channel=1.0, rail=0.8,
                 half_width=1.6)


@gf.cell(set_name=False)
def INV_GF(
    w_n: float = 3.0,
    w_p: float = 6.0,
    l_gate: float = 0.28,
    nf: int = 2,
    channel: float = 1.0,
    rail: float = 0.8,
    half_width: float = 1.6,
) -> gf.Component:
    """CMOS inverter, pins A (M1, left edge), Y (M1, centre), VDD and VSS (M1 rails).

    With the default arguments the cell is named INV_GF, the name the
    LVS netlist and signoff use; any other argument set gets the changed
    values appended, so the two never collide in one layout.

    Args:
        w_n, w_p: total nfet / pfet width in um (INV.spice: 3 and 6).
        l_gate: gate length in um.
        nf: fingers per device; W is split evenly over them.
        channel: poly-to-poly gap between the two devices.
        rail: supply rail height.
        half_width: half the rail length; the cell is 2 * (half_width + 0.25) wide.
    """
    params = dict(w_n=w_n, w_p=w_p, l_gate=l_gate, nf=nf, channel=channel, rail=rail,
                  half_width=half_width)
    changed = [f"{k}{v}" for k, v in params.items() if v != _DEFAULTS[k]]
    c = gf.Component()
    c.name = "INV_GF" + ("_" + "_".join(changed).replace(".", "p") if changed else "")

    ncell = _without_gate_pads(nfet(w_gate=w_n / nf, l_gate=l_gate, nf=nf, grw=0))
    pcell = _without_gate_pads(pfet(w_gate=w_p / nf, l_gate=l_gate, nf=nf, grw=0))
    fn = _features(ncell)
    fp0 = _features(pcell)

    # -- place: nfet at the origin, pfet above it, `channel` of poly gap
    c << ncell
    yp = _snap(fn["poly"][3] + channel - fp0["poly"][1])
    p = c << pcell
    p.dmove((0, yp))
    fp = {k: ([_shift(b, yp) for b in v] if isinstance(v, list) else _shift(v, yp))
          for k, v in fp0.items()}

    # -- gate: a poly bridge over the finger ends facing the channel,
    #    reaching left past the S/D columns to where M1 may sit; one
    #    contact there per device; A on M1 joining the two
    x_gate = _snap(fn["cols"][0][0] - M1_SPACE - CON_ENC_M1 - CON / 2 - 0.07)
    x_poly0 = x_gate - CON / 2 - CON_ENC_COMP - 0.05
    #- the bridge is the band between COMP + PL.5a and the poly end, over
    #- the full finger pitch: exactly where the plugin's own pads sit
    nbridge = (fn["poly"][0], fn["comp"][3] + POLY_COMP_SPACE, fn["poly"][2], fn["poly"][3])
    pbridge = (fp["poly"][0], fp["poly"][1], fp["poly"][2], fp["comp"][1] - POLY_COMP_SPACE)
    _rect(c, LAYER.poly2, x_poly0, nbridge[1], nbridge[2], nbridge[3])
    _rect(c, LAYER.poly2, x_poly0, pbridge[1], pbridge[2], pbridge[3])
    na = _poly_contact(c, x_gate, (nbridge[1] + nbridge[3]) / 2)
    pa = _poly_contact(c, x_gate, (pbridge[1] + pbridge[3]) / 2)
    _rect(c, LAYER.metal1, na[0], na[1], na[2], pa[3])
    ymid = _snap((nbridge[3] + pbridge[1]) / 2)
    c.add_label("A", position=(x_gate, ymid), layer=LAYER.metal1_label)

    # -- Y: the drain columns joined straight through the channel
    ndrain, pdrain = fn["cols"][nf // 2], fp["cols"][nf // 2]
    _rect(c, LAYER.metal1, ndrain[0], ndrain[3] - 0.15, ndrain[2], pdrain[1] + 0.15)
    c.add_label("Y", position=((ndrain[0] + ndrain[2]) / 2, ymid), layer=LAYER.metal1_label)

    # -- VSS rail below the nfet with the substrate tap under it
    vss_y1 = _snap(fn["poly"][1] - 0.2)
    vss_y0 = vss_y1 - rail
    _rect(c, LAYER.metal1, -half_width, vss_y0, half_width, vss_y1)
    _tap(c, LAYER.pplus, -half_width + 0.2, vss_y0 + 0.15, half_width - 0.2, vss_y1 - 0.15)
    c.add_label("VSS", position=(0, (vss_y0 + vss_y1) / 2), layer=LAYER.metal1_label)

    # -- VDD rail above the pfet with the well tap under it, n-well extended
    vdd_y0 = _snap(fp["poly"][3] + 0.2)
    vdd_y1 = vdd_y0 + rail
    _rect(c, LAYER.metal1, -half_width, vdd_y0, half_width, vdd_y1)
    _tap(c, LAYER.nplus, -half_width + 0.2, vdd_y0 + 0.15, half_width - 0.2, vdd_y1 - 0.15)
    c.add_label("VDD", position=(0, (vdd_y0 + vdd_y1) / 2), layer=LAYER.metal1_label)
    _rect(c, LAYER.nwell, -half_width - 0.25, fp["comp"][1] - NWELL_ENC,
          half_width + 0.25, vdd_y1 - 0.15 + NWELL_ENC)

    # -- source columns run out to the rails, same width as the column
    for col in (fn["cols"][0], fn["cols"][-1]):
        _rect(c, LAYER.metal1, col[0], vss_y1, col[2], col[1] + 0.15)
    for col in (fp["cols"][0], fp["cols"][-1]):
        _rect(c, LAYER.metal1, col[0], col[3] - 0.15, col[2], vdd_y0)

    c.info["devices"] = 2
    c.info["w_n_um"] = w_n
    c.info["w_p_um"] = w_p
    c.info["l_gate_um"] = l_gate
    return c


if __name__ == "__main__":
    import gf180mcu

    gf180mcu.PDK.activate()
    INV_GF().show()
