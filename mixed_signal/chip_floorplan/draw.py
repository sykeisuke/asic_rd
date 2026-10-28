"""SVG drawings of the floorplan in data/floorplan.json (called by floorplan.py).

chip_svg:  the whole 1x0p5 die to scale: pad ring with every pad named and
           typed, the AVDD pair, the analog macro and the digital region, the
           four analog pad wires and the AVDD/AVSS straps, a zoom of the
           analog + digital corner, and the area table.
macro_svg: Analog_top as a hard macro to scale, every block with its size,
           the bus channel, the ring, the west (pad) and south (digital) pins.
           Planned pins (spec s.7.3 test access, no circuit yet) are dashed.
"""
from xml.sax.saxutils import escape

PAD_FILL = {
    "bidir": "#3b82f6", "input": "#1a9e75", "bi_a": "#d9531e", "asig_5p0": "#f0a07a",
    "iopwr": "#9a9a9a", "corepwr": "#4b4b4b", "avdd": "#e53935", "avss": "#b71c1c",
}
PAD_LEGEND = [
    ("bidir", "Bidirectional bi_24t"), ("input", "Input (inputs[0-3], clk, rst_n)"),
    ("bi_a", "Analog bi_a"), ("asig_5p0", "Analog asig_5p0"), ("iopwr", "I/O power DVDD/DVSS"),
    ("corepwr", "Core VDD/VSS"), ("avdd", "AVDD pair (re-typed bidir[45:44])"),
]
BLK = {
    "cell": ("#f6c49b", "#b5651d"), "reserved": ("#f3f3f3", "#888888"), "ref": ("#bcd7ef", "#2f6db5"),
    "ramp": ("#d9c4e6", "#7b4fa0"), "bias": ("#c6e2b3", "#4b8b2b"), "decap": ("#ecebe7", "#a8a49a"),
    "channel": ("#fff4c9", "#c9a227"),
}
ANALOG = ("#fde3d3", "#c2410c")
DIGITAL = ("#dbe8f6", "#1d5fae")
WIRE = {"VIN": "#c2410c", "EXT_RAMP": "#d97706", "AMON": "#9333ea", "CMP_OUT": "#475569"}
FONT = "Helvetica, Arial, sans-serif"


def t(x, y, s, size=10, anchor="start", weight="normal", fill="#222", rot=None, italic=False):
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}"{st}{tr}>{escape(s)}</text>')


def rect(x, y, w, h, fill, stroke="none", sw=1, dash=None, extra=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}{extra}/>')


def defs():
    return ('<defs>'
            '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="6" height="6" fill="#f6f6f6"/><line x1="0" y1="0" x2="0" y2="6" stroke="#bdbdbd" stroke-width="2"/></pattern>'
            '<pattern id="dots" width="5" height="5" patternUnits="userSpaceOnUse">'
            '<rect width="5" height="5" fill="#efeeea"/><circle cx="2.5" cy="2.5" r="0.8" fill="#b9b5aa"/></pattern>'
            '<pattern id="free" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="10" height="10" fill="#fbfaf7"/><line x1="0" y1="0" x2="0" y2="10" stroke="#efece4" stroke-width="1"/></pattern>'
            '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker>'
            '</defs>')


def blk_fill(kind):
    if kind == "reserved":
        return "url(#hatch)"
    if kind == "decap":
        return "url(#dots)"
    return BLK[kind][0]


def fmt(v):
    return f"{v:,.0f}"


# --------------------------------------------------------------------- chip
def chip_svg(fp, path):
    DW, DH = fp["die"]
    cx0, cy0, cx1, cy1 = fp["core"]
    S = 0.30                      # px per um
    OX, OY = 150, 92              # die origin on the canvas (top-left)
    W = 1480
    die_w, die_h = DW * S, DH * S

    def X(x):
        return OX + x * S

    def Y(y):                     # die y is north-up
        return OY + (DH - y) * S

    out = []
    a = fp["areas"]
    mac = next(b for b in fp["chip"] if b["key"] == "macro")
    dig = next(b for b in fp["chip"] if b["key"] == "digital")

    # ---------------------------------------------------- title
    out.append(t(OX, 34, "Chip floorplan: Analog_top + asic_digital_top in the wafer.space 1x0p5 pad ring (digital on top)",
                 18, weight="bold"))
    out.append(t(OX, 56, f"Die {DW/1000:.3f} x {DH/1000:.3f} mm, core {(cx1-cx0)/1000:.3f} x {(cy1-cy0)/1000:.3f} mm, "
                 f"{len(fp['pads'])} pads. Drawn to scale ({S} px/um). Pads: gf180mcu_ocd_io, measured "
                 f"{fp['pad_cell'][0]:.2f} x {fp['pad_cell'][1]:.0f} um, corners {fp['corner']:.0f} um.", 11, fill="#555"))
    out.append(t(OX, 72, "Areas are estimates from the netlist (no analog layout exists); the digital outline is its GDS bounding box.",
                 11, fill="#555", italic=True))

    # ---------------------------------------------------- die, ring band, core
    out.append(rect(OX, OY, die_w, die_h, "#f4f2ec", "#8a8578", 1.5, extra=' rx="6"'))
    out.append(rect(X(fp["pad_cell"][1]), Y(DH - fp["pad_cell"][1]), (DW - 2 * fp["pad_cell"][1]) * S,
                    (DH - 2 * fp["pad_cell"][1]) * S, "#ebe7dc", "none"))
    out.append(rect(X(cx0), Y(cy1), (cx1 - cx0) * S, (cy1 - cy0) * S, "url(#free)", "#a29d90", 1.2, dash="6 4"))
    for (x, y) in ((0, 0), (DW - fp["corner"], 0), (0, DH - fp["corner"]), (DW - fp["corner"], DH - fp["corner"])):
        out.append(rect(X(x), Y(y + fp["corner"]), fp["corner"] * S, fp["corner"] * S, "none", "#c8c3b6", 0.8, dash="3 3"))
    out.append(t(X(DW - fp["corner"] / 2), Y(fp["corner"] / 2) + 3, "corner", 8, "middle", fill="#a8a296"))

    # ---------------------------------------------------- pads
    for p in fp["pads"]:
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        fill = PAD_FILL[p["type"]]
        big = p["type"] in ("bi_a", "asig_5p0", "avdd", "avss")
        out.append(rect(X(x), Y(y + h), w * S, h * S, fill, "#1f2937" if big else "#ffffff", 1.4 if big else 0.6,
                        extra=' rx="1.5"'))
        lab = p["label"].replace("inputs", "in").replace("bidir", "bd")
        if p["type"] in ("avdd", "avss"):
            lab = p["label"] + " (" + p["name"].replace("bidir", "bd") + ")"
        col = "#111" if p["type"] in ("asig_5p0",) else "#ffffff"
        if p["side"] in ("S", "N"):
            xc = X(x + w / 2) + 3
            yc = Y(y + h / 2)
            out.append(t(xc, yc, lab, 8, "middle", fill=col, rot=-90, weight="bold" if big else "normal"))
        else:
            out.append(t(X(x + w / 2), Y(y + h / 2) + 3, lab, 8, "middle", fill=col, weight="bold" if big else "normal"))

    # side group labels (outside the die), as in the ring drawing
    out.append(t(X(DW / 2), OY - 6, "north: AVDD pair, bidir[43:26], 2 x DVDD/DVSS", 10, "middle", fill="#444"))
    out.append(t(X(DW / 2), Y(0) + 16, "south: clk, rst_n, bidir[0:17], 2 x DVDD/DVSS", 10, "middle", fill="#444"))
    out.append(t(X(DW) + 10, Y(DH / 2), "east: bidir[18:25]", 10, fill="#444"))
    out.append(t(X(DW) + 10, Y(DH / 2) + 13, "2 x DVDD/DVSS", 10, fill="#444"))

    # analog pad call-outs on the left of the die
    pads = {p["name"]: p for p in fp["pads"]}
    for an in ("analog[0]", "analog[1]", "analog[2]", "analog[3]"):
        p = pads[an]
        y = Y(p["c"])
        col = WIRE[p["signal"]]
        out.append(f'<line x1="{OX - 4:.1f}" y1="{y:.1f}" x2="{OX - 16:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="2"/>')
        out.append(t(OX - 20, y - 2, p["signal"], 10, "end", "bold", col))
        out.append(t(OX - 20, y + 10, f"{an} · {p['type']}", 9, "end", fill="#555"))
    out.append(t(OX - 20, Y(pads["inputs[1]"]["c"]), "inputs[0-3]", 10, "end", fill="#1a9e75"))
    out.append(t(OX - 20, Y(pads["vdd[0]"]["c"]) + 8, "VDD/VSS[0] (core)", 10, "end", fill="#4b4b4b"))

    # ---------------------------------------------------- straps and analog wires
    for lab, s in fp["straps"].items():
        pts = " ".join(f"{X(px):.1f},{Y(py):.1f}" for px, py in s["pts"])
        out.append(f'<polyline points="{pts}" fill="none" stroke="{PAD_FILL["avdd"] if lab == "AVDD" else "#7f1d1d"}" '
                   f'stroke-width="2.4" stroke-linejoin="round" opacity="0.85"/>')
    for pin, w in fp["wires"].items():
        pts = " ".join(f"{X(px):.1f},{Y(py):.1f}" for px, py in w["pts"])
        out.append(f'<polyline points="{pts}" fill="none" stroke="{WIRE[pin]}" stroke-width="1.8" stroke-linejoin="round"/>')

    # ---------------------------------------------------- blocks
    for b in fp["chip"]:
        if b["kind"] == "cdm":
            out.append(rect(X(b["x"]), Y(b["y"] + b["h"]), b["w"] * S, b["h"] * S, "#fde68a", "#b45309", 0.8))
    out.append(rect(X(dig["x"]), Y(dig["y"] + dig["h"]), dig["w"] * S, dig["h"] * S, DIGITAL[0], DIGITAL[1], 1.6))
    out.append(t(X(dig["x"] + dig["w"] / 2), Y(dig["y"] + dig["h"] / 2) - 6, "DIGITAL", 12, "middle", "bold", DIGITAL[1]))
    out.append(t(X(dig["x"] + dig["w"] / 2), Y(dig["y"] + dig["h"] / 2) + 8, f"{dig['w']:.0f} x {dig['h']:.0f} um", 9,
                 "middle", fill=DIGITAL[1]))
    out.append(t(X(dig["x"] + dig["w"] / 2), Y(dig["y"] + dig["h"] / 2) + 20, f"{100 * a['digital'] / a['core']:.2f} % of core",
                 9, "middle", fill=DIGITAL[1]))
    out.append(rect(X(mac["x"]), Y(mac["y"] + mac["h"]), mac["w"] * S, mac["h"] * S, ANALOG[0], ANALOG[1], 1.6))
    for bb in fp["macro"]["boxes"]:
        if bb["kind"] == "channel":
            continue
        out.append(rect(X(mac["x"] + bb["x"]), Y(mac["y"] + bb["y"] + bb["h"]), bb["w"] * S, bb["h"] * S,
                        blk_fill(bb["kind"]), BLK[bb["kind"]][1], 0.4))
    out.append(t(X(mac["x"] + mac["w"] / 2), Y(mac["y"] + mac["h"]) - 5, "ANALOG", 11, "middle", "bold", ANALOG[1]))
    # analog <-> digital interface
    ya, yd = Y(mac["y"]), Y(dig["y"] + dig["h"])
    for k in range(9):
        xx = X(mac["x"] + 20 + k * (mac["w"] - 40) / 8)
        out.append(f'<line x1="{xx:.1f}" y1="{ya:.1f}" x2="{xx:.1f}" y2="{yd:.1f}" stroke="#1d5fae" stroke-width="0.8"/>')

    # core label in the empty core
    out.append(t(X((cx0 + cx1) / 2 + 300), Y((cy0 + cy1) / 2) - 8, f"Core {(cx1-cx0):.0f} x {(cy1-cy0):.0f} um", 16,
                 "middle", "bold", "#6b665a"))
    out.append(t(X((cx0 + cx1) / 2 + 300), Y((cy0 + cy1) / 2) + 14,
                 f"analog {100 * a['analog'] / a['core']:.2f} %  ·  digital {100 * a['digital'] / a['core']:.2f} %  ·  "
                 f"free {100 * (1 - (a['analog'] + a['digital']) / a['core']):.1f} %", 12, "middle", fill="#6b665a"))
    out.append(t(X((cx0 + cx1) / 2 + 300), Y((cy0 + cy1) / 2) + 32,
                 "free core: fill + density only (wafer.space slot is pad-limited)", 10, "middle", fill="#8a8578", italic=True))

    # zoom frame: the analog + digital corner, from the west pads' inner part
    # to the north pads' inner part, so every analog wire and both straps show
    zx0, zy0 = 200.0, dig["y"] - 30
    zx1 = max(mac["x"] + mac["w"], dig["x"] + dig["w"]) + 230
    zy1 = DH - fp["pad_cell"][1] + 70
    out.append(rect(X(zx0), Y(zy1), (zx1 - zx0) * S, (zy1 - zy0) * S, "none", "#374151", 1, dash="4 3"))
    out.append(t(X(zx1) + 4, Y(zy1) + 10, "zoom A", 10, weight="bold", fill="#374151"))

    # ---------------------------------------------------- legend
    ly = OY + die_h + 40
    lx = OX
    for key, lab in PAD_LEGEND:
        cnt = sum(1 for p in fp["pads"] if p["type"] == key or (key == "avdd" and p["type"] == "avss"))
        out.append(rect(lx, ly - 10, 12, 12, PAD_FILL[key], "#333" if key in ("bi_a", "asig_5p0", "avdd") else "none", 0.8,
                        extra=' rx="2"'))
        s = f"{lab} x{cnt}"
        out.append(t(lx + 17, ly, s, 10, fill="#333"))
        lx += 22 + 6.0 * len(s)
    ly2 = ly + 20
    lx = OX
    for col, lab in ((ANALOG, "Analog_top hard macro"), (DIGITAL, "digital region (soft cells)"),
                     (("#fde68a", "#b45309"), "CDM secondary protection (reserved)")):
        out.append(rect(lx, ly2 - 10, 12, 12, col[0], col[1], 1))
        out.append(t(lx + 17, ly2, lab, 10, fill="#333"))
        lx += 30 + 6.0 * len(lab)
    for pin, col in WIRE.items():
        out.append(f'<line x1="{lx:.1f}" y1="{ly2 - 4:.1f}" x2="{lx + 16:.1f}" y2="{ly2 - 4:.1f}" stroke="{col}" stroke-width="2"/>')
        out.append(t(lx + 20, ly2, pin, 10, fill="#333"))
        lx += 28 + 6.2 * len(pin)

    # ---------------------------------------------------- zoom A
    zs = 0.9
    ZX, ZY = OX, ly2 + 50
    zw, zh = (zx1 - zx0) * zs, (zy1 - zy0) * zs

    def ZXf(x):
        return ZX + (x - zx0) * zs

    def ZYf(y):
        return ZY + (zy1 - y) * zs

    out.append(t(ZX, ZY - 12, f"Zoom A: analog + digital corner ({zs} px/um)", 13, weight="bold"))
    out.append(f'<clipPath id="zclip"><rect x="{ZX:.1f}" y="{ZY:.1f}" width="{zw:.1f}" height="{zh:.1f}"/></clipPath>')
    out.append('<g clip-path="url(#zclip)">')
    out.append(rect(ZX, ZY, zw, zh, "#ebe7dc"))
    out.append(rect(ZXf(cx0), ZYf(cy1), (cx1 - cx0) * zs, (cy1 - cy0) * zs, "url(#free)", "#a29d90", 1, dash="6 4"))
    for p in fp["pads"]:
        if p["x"] > zx1 or p["x"] + p["w"] < zx0 or p["y"] > zy1 or p["y"] + p["h"] < zy0:
            continue
        big = p["type"] in ("bi_a", "asig_5p0", "avdd", "avss")
        out.append(rect(ZXf(p["x"]), ZYf(p["y"] + p["h"]), p["w"] * zs, p["h"] * zs, PAD_FILL[p["type"]],
                        "#1f2937" if big else "#ffffff", 1.2 if big else 0.6))
        col = "#111" if p["type"] == "asig_5p0" else "#fff"
        lab = p["label"]
        if p["side"] == "W":
            out.append(t(ZXf(min(p["x"] + p["w"], zx0 + 170) - 4), ZYf(p["c"]) + 4,
                         lab + (f" · {p['type']}" if p["type"] in ("bi_a", "asig_5p0") else ""), 10, "end",
                         "bold" if big else "normal", col))
        elif p["side"] == "N":
            out.append(t(ZXf(p["c"]) + 4, ZYf(p["y"]) - 8, lab, 10, "start", "bold" if big else "normal", col, rot=-90))
    out.append(t(ZXf(cx0) + 3, ZY + zh - 6, "core edge", 9, fill="#8a8578"))
    for lab, s in fp["straps"].items():
        col = PAD_FILL["avdd"] if lab == "AVDD" else "#7f1d1d"
        pts = " ".join(f"{ZXf(px):.1f},{ZYf(py):.1f}" for px, py in s["pts"])
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{10 * zs:.1f}" '
                   f'stroke-linejoin="miter" opacity="0.45"/>')
        (xa, ya_), (xb, yb) = s["pts"][-2], s["pts"][-1]
        out.append(t(ZXf(xa) + 9, ZYf(yb + (ya_ - yb) * (0.62 if lab == "AVDD" else 0.38)), f"{lab} strap, 10 um, {s['len_um']:.0f} um from {s['pad']}", 9,
                     weight="bold", fill=col))
    for pin, w in fp["wires"].items():
        pts = " ".join(f"{ZXf(px):.1f},{ZYf(py):.1f}" for px, py in w["pts"])
        out.append(f'<polyline points="{pts}" fill="none" stroke="{WIRE[pin]}" stroke-width="2.2" stroke-linejoin="round"/>')
        y0w = w["pts"][0][1]
        if len(w["pts"]) == 2:
            out.append(t(ZXf(w["pts"][0][0]) + 3, ZYf(y0w) - 5, f"{pin} · {w['len_um']:.0f} um", 9, weight="bold",
                         fill=WIRE[pin]))
        else:
            out.append(t(ZXf(w["pts"][1][0]) + 6, ZYf(y0w) + 3, f"{pin} · {w['len_um']:.0f} um", 9,
                         weight="bold", fill=WIRE[pin]))
    for b in fp["chip"]:
        if b["kind"] == "cdm":
            out.append(rect(ZXf(b["x"]), ZYf(b["y"] + b["h"]), b["w"] * zs, b["h"] * zs, "#fde68a", "#b45309", 0.8))
            out.append(t(ZXf(b["x"] + b["w"] / 2), ZYf(b["y"] + b["h"] / 2) + 3, "CDM", 7, "middle", fill="#92400e"))
    out.append(rect(ZXf(dig["x"]), ZYf(dig["y"] + dig["h"]), dig["w"] * zs, dig["h"] * zs, DIGITAL[0], DIGITAL[1], 1.6))
    dxc, dyc = ZXf(dig["x"] + dig["w"] / 2), ZYf(dig["y"] + dig["h"] / 2)
    out.append(t(dxc, dyc - 18, "asic_digital_top", 14, "middle", "bold", DIGITAL[1]))
    out.append(t(dxc, dyc, f"{dig['w']:.2f} x {dig['h']:.2f} um = {fmt(a['digital'])} um²", 11, "middle", fill=DIGITAL[1]))
    out.append(t(dxc, dyc + 16, "outline from its GDS; soft cells in the Chip flow", 9, "middle", fill=DIGITAL[1], italic=True))
    out.append(t(dxc, dyc + 30, "clk/rst_n (S), inputs[0-3] (W), bidir (S, E, N)", 9, "middle", fill=DIGITAL[1]))
    out.append(rect(ZXf(mac["x"]), ZYf(mac["y"] + mac["h"]), mac["w"] * zs, mac["h"] * zs, ANALOG[0], ANALOG[1], 1.6))
    for bb in fp["macro"]["boxes"]:
        out.append(rect(ZXf(mac["x"] + bb["x"]), ZYf(mac["y"] + bb["y"] + bb["h"]), bb["w"] * zs, bb["h"] * zs,
                        blk_fill(bb["kind"]), BLK[bb["kind"]][1], 0.6))
        short = {"bias_gen_s": "bias_gen", "ramp_simple_d": "ramp", "midref": "mid", "vrlo_ref": "vrlo",
                 "TEST (reserved)": "test"}.get(bb["label"])
        if short and bb["w"] * zs > 18:
            out.append(t(ZXf(mac["x"] + bb["x"] + bb["w"] / 2), ZYf(mac["y"] + bb["y"] + bb["h"] / 2) + 3, short, 8,
                         "middle", fill="#333"))
    out.append(t(ZXf(mac["x"] + mac["w"]) + 6, ZYf(mac["y"] + mac["h"] / 2) - 4, "Analog_top", 11, weight="bold",
                 fill=ANALOG[1]))
    out.append(t(ZXf(mac["x"] + mac["w"]) + 6, ZYf(mac["y"] + mac["h"] / 2) + 10,
                 f"{mac['w']:.1f} x {mac['h']:.1f} um", 10, fill=ANALOG[1]))
    out.append(t(ZXf(mac["x"] + mac["w"]) + 6, ZYf(mac["y"] + mac["h"] / 2) + 23, "detail: analog_macro_floorplan.svg",
                 9, fill=ANALOG[1], italic=True))
    ya, yd = ZYf(mac["y"]), ZYf(dig["y"] + dig["h"])
    nsig = len(fp["macro"]["pins_south"])
    for k in range(nsig):
        xx = ZXf(mac["x"] + 10 + k * (mac["w"] - 20) / (nsig - 1))
        out.append(f'<line x1="{xx:.1f}" y1="{ya:.1f}" x2="{xx:.1f}" y2="{yd:.1f}" stroke="#1d5fae" stroke-width="0.6"/>')
    gap = mac["y"] - dig["y"] - dig["h"]
    out.append(t(ZXf(dig["x"] + dig["w"]) + 6, (ya + yd) / 2 + 4, f"{nsig} signals across a {gap:.0f} um gap", 9,
                 fill="#1d5fae"))
    out.append('</g>')
    out.append(rect(ZX, ZY, zw, zh, "none", "#374151", 1))
    # ---------------------------------------------------- area table
    TX = ZX + zw + 40
    TY = ZY
    rows = [("", "W x H (um)", "Area (um²)", "% core")]
    rows.append(("Analog_top macro", f"{mac['w']:.1f} x {mac['h']:.1f}", fmt(a["macro"]), f"{100 * a['macro'] / a['core']:.2f}"))
    rows.append(("CDM cells, 4 analog pads", "4 x 24 x 30", fmt(a["cdm"]), f"{100 * a['cdm'] / a['core']:.3f}"))
    rows.append(("Analog total", "", fmt(a["analog"]), f"{100 * a['analog'] / a['core']:.2f}"))
    rows.append(("asic_digital_top (GDS bbox)", f"{dig['w']:.2f} x {dig['h']:.2f}", fmt(a["digital"]),
                 f"{100 * a['digital'] / a['core']:.2f}"))
    used = a["analog"] + a["digital"]
    rows.append(("Free core", "", fmt(a["core"] - used), f"{100 * (1 - used / a['core']):.1f}"))
    rows.append(("Core", f"{cx1 - cx0:.0f} x {cy1 - cy0:.0f}", fmt(a["core"]), "100"))
    out.append(t(TX, TY - 12, "Area", 13, weight="bold"))
    cw = [190, 110, 90, 60]
    for i, r in enumerate(rows):
        yy = TY + 16 + i * 19
        if i in (3, 4):
            out.append(rect(TX - 4, yy - 13, sum(cw), 18, ANALOG[0] if i == 3 else DIGITAL[0]))
        xx = TX
        for j, c in enumerate(r):
            out.append(t(xx + (cw[j] - 6 if j else 0), yy, c, 10, "end" if j else "start",
                         "bold" if i == 0 or i in (3, 4) else "normal", "#222"))
            xx += cw[j]
    yy = TY + 16 + len(rows) * 19 + 10
    out.append(t(TX, yy, "Analog macro contents (um²; MIM over the circuit, so area = max(devices, MIM))", 11, weight="bold"))
    blocks = fp["blocks"]
    names = [("atop_cell", "unit cell (x4 + replica)"), ("ramp_simple_d", "ramp_simple_d (4 pF)"),
             ("vrlo_ref", "vrlo_ref (3.47 + 1.02 pF)"), ("bias_gen_s", "bias_gen_s (2 x 1 pF)"),
             ("midref_buf", f"midref_buf (x{blocks['midref_buf']['instances']})"), ("midref_div", "midref_div")]
    yy += 18
    out.append(t(TX, yy, "block", 10, weight="bold"))
    out.append(t(TX + 250, yy, "devices", 10, "end", "bold"))
    out.append(t(TX + 320, yy, "MIM", 10, "end", "bold"))
    out.append(t(TX + 400, yy, "MOS/R/C", 10, "end", "bold"))
    for k, lab in names:
        b = blocks[k]
        yy += 16
        out.append(t(TX, yy, lab, 10))
        out.append(t(TX + 250, yy, fmt(b["dev_um2"]), 10, "end", "bold" if b["dev_um2"] >= b["mim_um2"] else "normal"))
        out.append(t(TX + 320, yy, fmt(b["mim_um2"]), 10, "end", "bold" if b["mim_um2"] > b["dev_um2"] else "normal"))
        out.append(t(TX + 400, yy, f"{b['n_mos']}/{b['n_res']}/{b['n_mim']}", 10, "end"))
    yy += 16
    out.append(t(TX, yy, f"test zone (reserved, not designed): {fmt(fp['test_area'])}", 10, italic=True))
    yy += 22
    notes = [
        f"devices = {fp['k_layout']:.2f} x project MOS footprint (k measured on drawn UC_MIM, DRC 0)",
        f"MIM footprint = plate + {fp['mim_keep_um']:.2f} um keep-out per side (same record)",
        "pad positions: evenly spaced between corners; confirm with the padmap (T2.2)",
        "AVDD/AVSS: dedicated straps, never through the core ring",
        "Metal4/Metal5 PDN keep-out over the macro: the MIMs use M4/M5",
    ]
    for n_ in notes:
        out.append(t(TX, yy, "· " + n_, 9, fill="#555"))
        yy += 14

    H = max(ZY + zh, yy) + 30
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" '
           f'font-family="{FONT}">' + "<title>Chip floorplan 1x0p5</title>" + defs()
           + rect(0, 0, W, H, "#ffffff") + "".join(out) + "</svg>")
    with open(path, "w") as f:
        f.write(svg)


# --------------------------------------------------------------------- macro
def macro_svg(fp, path):
    m = fp["macro"]
    S = 4.2
    OX, OY = 190, 150
    W = int(OX + m["w"] * S + 400)

    def X(x):
        return OX + x * S

    def Y(y):
        return OY + (m["h"] - y) * S

    out = []
    out.append(t(OX - 170, 34, "Analog_top as a hard macro: floorplan to scale", 18, weight="bold"))
    out.append(t(OX - 170, 56, f"{m['w']:.1f} x {m['h']:.1f} um = {fmt(m['w'] * m['h'])} um² · west edge faces the analog pads, "
                 "south edge the digital top, north edge the AVDD pair", 11, fill="#555"))
    out.append(t(OX - 170, 72, f"Block areas from the Analog_top netlist; MIMs (cap_mim_2f0_m4m5) drawn over their circuits. "
                 f"Scale {S} px/um.", 11, fill="#555", italic=True))
    # ring
    out.append(rect(X(0), Y(m["h"]), m["w"] * S, m["h"] * S, "#8b8f97", "none"))
    r = 8.0
    out.append(rect(X(r / 2), Y(m["h"] - r / 2), (m["w"] - r) * S, (m["h"] - r) * S, "#f19a9a", "none"))
    out.append(rect(X(r), Y(m["h"] - r), (m["w"] - 2 * r) * S, (m["h"] - 2 * r) * S, "#fffdf8", "none"))
    out.append(t(X(m["w"] / 2), Y(m["h"]) + 12, "AVSS (outer) / AVDD (inner) ring, 8 um", 9, "middle", fill="#fff"))
    for bb in m["boxes"]:
        k = bb["kind"]
        out.append(rect(X(bb["x"]), Y(bb["y"] + bb["h"]), bb["w"] * S, bb["h"] * S, blk_fill(k), BLK[k][1], 1.2))
        cxm, cym = X(bb["x"] + bb["w"] / 2), Y(bb["y"] + bb["h"] / 2)
        if k == "channel":
            for i, (lab, col) in enumerate((("vin", "#c2410c"), ("vramp", "#7b4fa0"), ("vref = vbl", "#2f6db5"),
                                            ("ibias[4:0]", "#4b8b2b"))):
                yy = Y(bb["y"] + bb["h"] * (0.82 - 0.21 * i))
                out.append(f'<line x1="{X(bb["x"]):.1f}" y1="{yy:.1f}" x2="{X(bb["x"] + bb["w"]):.1f}" y2="{yy:.1f}" '
                           f'stroke="{col}" stroke-width="{2.4 if i < 3 else 1.2}"/>')
                out.append(t(X(bb["x"] + bb["w"]) - 4, yy - 2, lab, 8, "end", fill=col))
            out.append(t(X(bb["x"]) + 4, Y(bb["y"]) - 3, f"bus channel {bb['h']:.1f} um", 8, fill="#8a6d0b"))
            continue
        if k == "cell" or bb["key"] == "rep":
            ha = fp["cell"]["ha"]
            lh = fp["cell"]["latch"][1]
            out.append(rect(X(bb["x"]), Y(bb["y"] + lh), bb["w"] * S, lh * S, "#cfe3f7", "#1d5fae", 0.8))
            ms = (fp["mim_keep_um"] * 2 + 5.0)
            out.append(rect(X(bb["x"] + (bb["w"] - ms) / 2), Y(bb["y"] + bb["h"] - 0.6), ms * S, ms * S, "none", "#7c2d12", 1.2,
                            dash="3 2"))
            ym = Y(bb["y"] + bb["h"] - 0.6 - ms / 2)
            out.append(t(cxm, ym - 2, bb["label"], 9, "middle", "bold"))
            out.append(t(cxm, ym + 10, "MIM", 8, "middle", fill="#7c2d12"))
            out.append(t(cxm, Y(bb["y"]) - 6, "dfxtn_2", 7, "middle", fill="#1d5fae"))
            continue
        lines = [bb["label"], f"{bb['w']:.1f} x {bb['h']:.1f} um"] + (bb["note"].split(", ") if k == "reserved" else [bb["note"]])
        for i, s in enumerate(lines):
            out.append(t(cxm, cym + 4 - 7 * (len(lines) - 1) + 14 * i, s, 11 if i == 0 else 9, "middle", "bold" if i == 0 else "normal",
                         "#222" if i == 0 else "#444"))
    # west pins (pads)
    for pin, yl in m["pins_west"].items():
        yy = Y(yl)
        col = WIRE[pin]
        dash = ' stroke-dasharray="5 3"' if m["pin_status"][pin] == "planned" else ""
        out.append(f'<line x1="{X(0) - 70:.1f}" y1="{yy:.1f}" x2="{X(0) + 8:.1f}" y2="{yy:.1f}" stroke="{col}" '
                   f'stroke-width="2.4"{dash} marker-end="url(#ah)"/>' if pin not in ("AMON", "CMP_OUT") else
                   f'<line x1="{X(0) + 8:.1f}" y1="{yy:.1f}" x2="{X(0) - 70:.1f}" y2="{yy:.1f}" stroke="{col}" '
                   f'stroke-width="2.4"{dash} marker-end="url(#ah)"/>')
        pad = next(w["pad"] for k_, w in fp["wires"].items() if k_ == pin)
        out.append(t(X(0) - 76, yy - 2, pin, 10, "end", "bold", col))
        out.append(t(X(0) - 76, yy + 10, f"pad {pad}" + (" · planned" if dash else ""), 9, "end", fill="#555"))
    # south pins (digital)
    sp = m["pins_south"]
    for i, pin in enumerate(sp):
        xx = X(14 + i * (m["w"] - 28) / (len(sp) - 1))
        out_dir = pin.startswith("Q")
        y1, y2 = Y(0) + 4, Y(0) + 26
        dash = ' stroke-dasharray="3 2"' if m["pin_status"][pin] == "planned" else ""
        out.append(f'<line x1="{xx:.1f}" y1="{(y2 if not out_dir else y1):.1f}" x2="{xx:.1f}" '
                   f'y2="{(y1 if not out_dir else y2):.1f}" stroke="#1d5fae" stroke-width="1.4"{dash} marker-end="url(#ah)"/>')
        out.append(t(xx + 3, y2 + 6, pin, 9, "end", fill="#1d5fae", rot=-60))
    out.append(t(X(m["w"]) + 10, Y(0) + 20, "to / from asic_digital_top", 10, weight="bold", fill="#1d5fae"))
    out.append(t(X(m["w"]) + 10, Y(0) + 34, "(DVDD/DVSS rails for the latch row enter here)", 9, fill="#1d5fae"))
    # north: AVDD / AVSS
    for i, lab in enumerate(("AVSS", "AVDD")):
        xx = X(fp["straps"][lab]["pts"][-1][0] - m["x"])
        out.append(f'<line x1="{xx:.1f}" y1="{Y(m["h"]) - 30:.1f}" x2="{xx:.1f}" y2="{Y(m["h"]) - 2:.1f}" '
                   f'stroke="{"#7f1d1d" if lab == "AVSS" else "#e53935"}" stroke-width="6" marker-end="url(#ah)"/>')
        out.append(t(xx, Y(m["h"]) - 34, lab, 10, "middle", "bold", "#b71c1c"))
    out.append(t(X(m["w"] * 0.02), Y(m["h"]) - 14, "10 um straps from bidir[45] / bidir[44]; Metal4/5 PDN keep-out over "
                 "the whole macro (MIMs use M4/M5)", 9, fill="#7f1d1d"))
    # dimensions
    yd = Y(0) + 92
    out.append(f'<line x1="{X(0):.1f}" y1="{yd:.1f}" x2="{X(m["w"]):.1f}" y2="{yd:.1f}" stroke="#444" '
               f'marker-start="url(#ah)" marker-end="url(#ah)"/>')
    out.append(t(X(m["w"] / 2), yd - 4, f"{m['w']:.2f} um", 11, "middle", "bold", "#333"))
    xd = X(m["w"]) + 28
    out.append(f'<line x1="{xd:.1f}" y1="{Y(0):.1f}" x2="{xd:.1f}" y2="{Y(m["h"]):.1f}" stroke="#444" '
               f'marker-start="url(#ah)" marker-end="url(#ah)"/>')
    out.append(t(xd + 6, Y(m["h"] / 2), f"{m['h']:.2f} um", 11, weight="bold", fill="#333"))
    # side notes
    nx, ny = X(m["w"]) + 100, Y(m["h"]) + 10
    notes = ["Floorplan rules followed", "· vin enters on the pad side, one short bus to 4 x S0",
             "· vramp, vref (= vbl) in the bus channel, each beside AVSS", "· bot[i] (floating plate) under its own MIM;",
             "  no digital line over it", "· latch row (DVDD) at the south edge:", "  dout -> latch is one short hop",
             "· bias lines drop from bias_gen in the", "  gap west of vrlo_ref", "· vrlo_ref beside the ramp it feeds",
             "· test zone on the pad side; replica cell", "  at the west end of the cell row",
             "", "Hatched = reserved, not designed:", "  replica cmp + latch, CMP_OUT",
             "  driver, AMON follower + 4:1 mux,", "  EXT_RAMP TG mux (areas from proxies)",
             "Dotted = AVDD decap (MOS caps) fill", "Dashed pins = planned (no circuit yet)"]
    for i, s in enumerate(notes):
        out.append(t(nx, ny + 15 * i, s, 10, weight="bold" if i in (0, 13) else "normal", fill="#333"))
    H = int(yd + 40)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="{FONT}">' + "<title>Analog macro floorplan</title>" + defs()
           + rect(0, 0, W, H, "#ffffff") + "".join(out) + "</svg>")
    with open(path, "w") as f:
        f.write(svg)
