#!/usr/bin/env python3
"""Annotated, to-scale floorplan drawings from the build's placement data.

    python3 draw_floorplan.py          # host or container, stdlib only

Reads work/floorplan_metrics.json (written by floorplan.py) and writes one
SVG per cell under physical/final_views/svg/.  The GDS render is the layout;
this is the floorplan: named blocks, the finger pattern of the matched
devices, well outlines, the symmetry axis, the wiring channel, the supply
rails and pins the routed cell will have, the capacitor, and the cell's
dimensions, in the same coordinates as the GDS.
"""

import json
import os

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
SVG = os.path.join(BLOCK, "physical", "final_views", "svg")

SCALE = 20.0          # px per um
PAD = 4.6             # um of margin for dimension lines, rails and pins

LABEL = {
    "PAIR": "INP / INN input pair   2 x 30.8u/0.5, 16 fingers of 3.85u + 2 dummies",
    "TAILA": "TAIL half A   45.25u/1.0, 10 fingers of 4.525u",
    "TAILB": "TAIL half B   45.25u/1.0, 10 fingers of 4.525u",
    "BUF4": "BUF4\n16u/0.28\nnf 4",
    "BUF2": "BUF2\n4.24u",
    "TGP": "TG P",
    "TGN": "TG N",
    "LOADS": "LOADD / LOADM mirror  2 x 12.4u/0.5, 6 x 4.13u + 2 dummies",
    "BUF3": "BUF3 8u",
    "BUF1": "BUF1 4u",
    "MIM": "MIM {v:.1f} fF\n{s:g} x {s:g} um FuseTop\nM4 / M5, over the tail",
    "MOMU": "MOMU\n15.6 fF\nM1-M4",
    "MOMU4x0": "4 x MOMU abutted   62.5 fF   M1-M4",
    "MOMU4x1": "4 x MOMU abutted   62.5 fF   M1-M4",
}

#- literal colours, so the file renders in any SVG viewer; the report page
#- inlines it and restyles by class for its dark theme
INK, MUTED = "#241f1b", "#6f655d"
FILL = {"pmos": "#ead0a8", "nmos": "#c8d7ec", "cap": "#b5dcc6"}
EDGE = {"pmos": "#8a4b12", "nmos": "#2b4a7a", "cap": "#1d6a44"}
RAIL = "#9a2f2f"


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def text(x, y, s, cls="lbl", anchor="middle"):
    lines = s.split("\n")
    out = []
    for i, ln in enumerate(lines):
        dy = (i - (len(lines) - 1) / 2) * 1.15
        out.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" dy="{dy:.2f}em" '
                   f'text-anchor="{anchor}">{esc(ln)}</text>')
    return "\n".join(out)


def draw(name, m):
    items = m["items"]
    nw = m["wells"]["nwell"]
    lvp = m["wells"]["lvpwell"]
    sx0 = min(nw[0], lvp[0]); sx1 = max(nw[2], lvp[2])
    sy0 = min(nw[1], lvp[1]); sy1 = max(nw[3], lvp[3])
    x0, x1, y0, y1 = sx0, sx1, sy0, sy1
    for it in items:
        x0 = min(x0, it[2]); x1 = max(x1, it[4])
        y0 = min(y0, it[3]); y1 = max(y1, it[5])
    W = (x1 - x0 + 2 * PAD) * SCALE
    H = (y1 - y0 + 2 * PAD) * SCALE

    def X(u):
        return (u - x0 + PAD) * SCALE

    def Y(u):                      # GDS y up, SVG y down
        return (y1 - u + PAD) * SCALE

    def box(bx0, by0, bx1, by1, cls, fill=None):
        f = f' fill="{fill}"' if fill else ""
        return (f'<rect class="{cls}" x="{X(bx0):.1f}" y="{Y(by1):.1f}" '
                f'width="{(bx1 - bx0) * SCALE:.1f}" height="{(by1 - by0) * SCALE:.1f}"{f}/>')

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
             f'width="{W:.0f}" height="{H:.0f}" role="img" '
             f'aria-label="{name} floorplan to scale">',
             '<style>'
             f'.well{{fill:none;stroke-width:1.5;stroke-dasharray:6 4}}'
             f'.nw{{stroke:{EDGE["pmos"]}}}.lvp{{stroke:{EDGE["nmos"]}}}'
             f'.dev{{stroke:{INK};stroke-width:1;fill-opacity:.85}}'
             f'.cap{{stroke:{EDGE["cap"]};stroke-width:1.5;fill-opacity:.6}}'
             f'.keep{{fill:none;stroke:{EDGE["cap"]};stroke-width:1;stroke-dasharray:3 3}}'
             f'.pr{{fill:none;stroke:{INK};stroke-width:1.2}}'
             f'.dim{{stroke:{MUTED};stroke-width:1}}'
             f'.axis{{stroke:{MUTED};stroke-width:1;stroke-dasharray:2 5}}'
             f'.chan{{fill:{MUTED};fill-opacity:.12}}'
             f'.rail{{fill:{RAIL};fill-opacity:.8}}'
             f'.pin{{fill:none;stroke:{INK};stroke-width:1.2}}'
             f'.lbl{{font:600 10.5px ui-sans-serif,system-ui,sans-serif;fill:{INK}}}'
             f'.sm{{font:500 9.5px ui-sans-serif,system-ui,sans-serif;fill:{INK}}}'
             f'.fing{{font:500 8.5px ui-monospace,SFMono-Regular,Menlo,monospace;fill:{INK}}}'
             f'.dimt{{font:500 10px ui-monospace,SFMono-Regular,Menlo,monospace;fill:{MUTED}}}'
             f'.wl{{font:600 9.5px ui-sans-serif,system-ui,sans-serif;letter-spacing:.06em}}'
             f'.wl.nw{{fill:{EDGE["pmos"]}}}.wl.lvp{{fill:{EDGE["nmos"]}}}'
             f'.railt{{font:600 9.5px ui-sans-serif,system-ui,sans-serif;fill:{RAIL};letter-spacing:.06em}}'
             '</style>']
    # wiring channel between the wells
    ch0, ch1 = m["channel"]
    parts.append(box(sx0, ch0, sx1, ch1, "chan"))
    parts.append(text(X(sx1) - 4, Y((ch0 + ch1) / 2) + 3,
                      f"wiring channel {ch1 - ch0:.1f} um: outa, left, tail, pbias",
                      "dimt", "end"))
    # supply rails the routed cell carries on the two well rings
    parts.append(box(sx0, sy1 - 0.45, sx1, sy1, "rail"))
    parts.append(text(X(sx0) + 4, Y(sy1) - 4, "VDD rail on the n-well ring", "railt", "start"))
    parts.append(box(sx0, sy0, sx1, sy0 + 0.45, "rail"))
    parts.append(text(X(sx0) + 4, Y(sy0) + 13, "VSS rail on the p-well ring", "railt", "start"))
    # wells
    parts.append(box(nw[0], nw[1], nw[2], nw[3], "well nw"))
    parts.append(text(X(nw[2]) - 4, Y(nw[3]) + 22, "N-WELL, one ring, bulk = vdd", "wl nw", "end"))
    parts.append(box(lvp[0], lvp[1], lvp[2], lvp[3], "well lvp"))
    parts.append(text(X(lvp[2]) - 4, Y(lvp[3]) + 12, "P-WELL, one ring, bulk = vss", "wl lvp", "end"))
    # symmetry axis
    ax = m.get("axis_x", 0.0)
    parts.append(f'<line class="axis" x1="{X(ax):.1f}" y1="{Y(sy1) - 6}" x2="{X(ax):.1f}" y2="{Y(sy0) + 6}"/>')
    parts.append(text(X(ax), Y(sy1) - 12, "symmetry axis of the matched core", "dimt"))
    # devices
    ref = {it[0]: it for it in items}
    for it in items:
        nm, kind, bx0, by0, bx1, by1 = it
        if kind == "cap":
            continue
        parts.append(box(bx0, by0, bx1, by1, "dev " + kind, FILL[kind]))
        w = (bx1 - bx0) * SCALE
        h = (by1 - by0) * SCALE
        lab = m.get("labels", {}).get(nm) or LABEL.get(nm, nm)
        if nm in ("PAIR", "LOADS"):
            pat = m["pair_pattern"] if nm == "PAIR" else m["loads_pattern"].replace("A" * (len(m["loads_pattern"]) - 2), "AB" * ((len(m["loads_pattern"]) - 2) // 2))
            parts.append(text(X((bx0 + bx1) / 2), Y(by1) + 12, lab, "lbl",
                              "middle" if nm == "PAIR" else "start").replace(
                f'x="{X((bx0 + bx1) / 2):.1f}"', f'x="{X(bx0) + 6:.1f}"') if nm == "LOADS"
                else text(X((bx0 + bx1) / 2), Y(by1) + 12, lab, "lbl"))
            n = len(pat)
            pitch = (bx1 - bx0 - 0.68) / n
            for i, ch in enumerate(pat):
                xx = bx0 + 0.34 + pitch * (i + 0.5)
                parts.append(text(X(xx), Y((by0 + by1) / 2) + 3, ch, "fing"))
            note = ("A = INP, B = INN, D = dummy tied off.  ABBA common centroid, two gate bars"
                    if nm == "PAIR" else
                    "A = LOADD (diode), B = LOADM (out), D = dummy.  One gate net; A/B is the drain strap")
            parts.append(text(X((bx0 + bx1) / 2), Y(by0) - 5, note, "dimt"))
        elif nm.startswith("TAIL"):
            parts.append(text(X(bx0) + 8, Y((by0 + by1) / 2), lab, "lbl", "start"))
        else:
            if w < 60 or h < 30:
                lab = lab.split("\n")[0].split("  ")[0]
            parts.append(text(X((bx0 + bx1) / 2), Y((by0 + by1) / 2), lab,
                              "lbl" if w > 90 else "sm"))
    # capacitor last, on top
    for it in items:
        nm, kind, bx0, by0, bx1, by1 = it
        if kind != "cap":
            continue
        parts.append(box(bx0, by0, bx1, by1, "cap", FILL["cap"]))
        lab = m.get("labels", {}).get(nm) or LABEL.get(nm, nm)
        if nm == "MIM":
            k = 1.2
            parts.append(box(bx0 - k, by0 - k, bx1 + k, by1 + k, "keep"))
            parts.append(text(X(bx1 + k) + 4, Y(by1 + k) + 9, "MIMTM.1 keep-out 1.2 um for other M4", "dimt", "start"))
            lab = lab.format(v=m["cap_value_ff"], s=m["cap_fusetop_w_um"])
        parts.append(text(X((bx0 + bx1) / 2), Y((by0 + by1) / 2), lab, "lbl"))

    # pins: input at the left by the switch, ramp to the pair, dout at the right
    def pin(x, y, label, anchor, dx):
        parts.append(f'<line class="pin" x1="{X(x):.1f}" y1="{Y(y):.1f}" x2="{X(x) + dx:.1f}" y2="{Y(y):.1f}"/>')
        parts.append(text(X(x) + dx + (4 if dx > 0 else -4), Y(y) + 3, label, "sm", anchor))
    tg = ref["TGN"]
    pin(sx0, (tg[3] + tg[5]) / 2, "vin, sampled", "end", -14)
    tgp = ref["TGP"]
    pin(sx0, (tgp[3] + tgp[5]) / 2, "clk_sample", "end", -14)
    b4 = ref["BUF4"]
    pin(sx1, (b4[3] + b4[5]) / 2, "dout", "start", 14)
    pr = ref["PAIR"]
    pin(sx1, pr[3] + 0.6, "ramp (inn)", "start", 14)
    parts.append(text(X(ax) + 8, Y(sy1) - 26, "pbias from the top edge to the tail gate bars", "dimt", "start"))
    # PR boundary and dimensions
    parts.append(box(sx0, sy0, sx1, sy1, "pr"))
    yd = Y(sy0) + 32
    parts.append(f'<line class="dim" x1="{X(sx0):.1f}" y1="{yd}" x2="{X(sx1):.1f}" y2="{yd}"/>')
    for xx in (sx0, sx1):
        parts.append(f'<line class="dim" x1="{X(xx):.1f}" y1="{yd - 5}" x2="{X(xx):.1f}" y2="{yd + 5}"/>')
    parts.append(text(X((sx0 + sx1) / 2), yd + 13, f"{sx1 - sx0:.2f} um", "dimt"))
    xd = X(sx1) + 50
    parts.append(f'<line class="dim" x1="{xd}" y1="{Y(sy1):.1f}" x2="{xd}" y2="{Y(sy0):.1f}"/>')
    for yy in (sy0, sy1):
        parts.append(f'<line class="dim" x1="{xd - 5}" y1="{Y(yy):.1f}" x2="{xd + 5}" y2="{Y(yy):.1f}"/>')
    parts.append(f'<text class="dimt" transform="translate({xd + 12:.1f},{Y((sy0 + sy1) / 2):.1f}) rotate(-90)" '
                 f'text-anchor="middle">{sy1 - sy0:.2f} um</text>')
    parts.append(text(X(sx0), Y(sy1) - 44,
                      f"{name}   {m['cell_area_um2']:.0f} um2   switch {m['sw_wn_um']:.2f}/{m['sw_wp_um']:.2f} um   "
                      f"hold {m['c_hold_ff']:.1f} fF   DRC {m['drc_violations']}",
                      "lbl", "start"))
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    os.makedirs(SVG, exist_ok=True)
    allm = json.load(open(os.path.join(WORK, "floorplan_metrics.json")))
    for name, m in allm.items():
        out = os.path.join(SVG, name + ".svg")
        with open(out, "w") as fo:
            fo.write(draw(name, m))
        print(f"{name.lower()}_svg = {os.path.relpath(out, BLOCK)}")


if __name__ == "__main__":
    main()
