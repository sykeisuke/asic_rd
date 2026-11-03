#!/usr/bin/env python3
"""Step 3 of the flow: turn the input GDS files into hard macros.

    python3 scripts/macros.py analog     # analog GDS -> LEF, liberty, Verilog, SPICE, pins.json
    python3 scripts/macros.py digital    # digital top: liberty timing models (OpenSTA)
    python3 scripts/macros.py svg        # LEF views of both macros as SVG (renders/)
    python3 scripts/macros.py            # all three

Run inside the container (scripts/container.sh); needs KLayout's Python
module and OpenSTA.

Analog. A GDS knows shapes and text, not ports. This script reads, from
inputs/analog/wsa_analog_top.gds:

- the outline: the PR boundary on GDS layer 0/0, which is also what
  LibreLane's Magic.StreamOut reads as the macro's fixed bbox;
- the pins: every text label on a metal pin layer (Metal1..Metal5,
  datatype 10), with the pin-layer shape under it as the pin's port;

and from inputs/analog/wsa_analog_top.pins.csv the two things a GDS does
not hold: each pin's direction / use, and the port order. Every pin in
the contract must be found in the GDS exactly once and every labelled pin
in the GDS must be in the contract; anything else stops the script.

It writes into work/macros/wsa_analog_top/:

    lef/wsa_analog_top.lef     SIZE, PINs, OBS = Metal1..Metal5 over the
                               whole outline less the pin shapes (the
                               router must not enter an analog block)
    lib/wsa_analog_top.lib     pin directions and a nominal load, no arcs
    vh/wsa_analog_top.v        black box, power pins under USE_POWER_PINS
    spice/wsa_analog_top.spice black box for chip LVS (ports only)
    pins.json                  what was found, in um, macro frame

Digital. The hardened digital top is used as it is (GDS, LEF and gate
netlist from inputs/digital). Its final views have no liberty, and
without one LibreLane black-boxes it in STA, so OpenSTA's
write_timing_model makes one per corner from its gate netlist
(scripts/digital_timing_model.tcl; cell delays only, no wires).
"""

import csv
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "wsa_analog_top"
GDS = os.path.join(HERE, "inputs", "analog", NAME + ".gds")
CONTRACT = os.path.join(HERE, "inputs", "analog", NAME + ".pins.csv")
OUT = os.path.join(HERE, "work", "macros", NAME)
DIG_LEF = os.path.join(HERE, "inputs", "digital", "asic_digital_top.lef")
RENDERS = os.path.join(HERE, "renders")

#- gf180mcuD GDS layer numbers (libs.tech/klayout/tech/gf180mcu.map):
#- drawing on datatype 0, pin on datatype 10
METALS = {"Metal1": 34, "Metal2": 36, "Metal3": 42, "Metal4": 46,
          "Metal5": 81}
BOUNDARY = (0, 0)

# --------------------------------------------------------------------- analog
def read_contract():
    rows = []
    with open(CONTRACT) as f:
        for r in csv.reader(ln for ln in f if not ln.startswith("#")):
            if r:
                rows.append({"name": r[0], "direction": r[1], "use": r[2],
                             "status": r[3] if len(r) > 3 else ""})
    return rows

def analog():
    import klayout.db as db
    ly = db.Layout()
    ly.read(GDS)
    top = ly.cell(NAME)
    if top is None:
        raise SystemExit(f"FAIL: no cell {NAME} in {GDS}")
    um = ly.dbu

    #- outline
    bl = ly.find_layer(*BOUNDARY)
    if bl is None or top.shapes(bl).is_empty():
        raise SystemExit("FAIL: no PR boundary (0/0) in the analog GDS")
    ob = top.bbox_per_layer(bl)
    if ob.left != 0 or ob.bottom != 0:
        raise SystemExit(f"FAIL: PR boundary does not start at the origin: {ob}")
    W, H = ob.width() * um, ob.height() * um

    #- pins: labels on <metal>/10 over a shape on <metal>/10
    found = {}
    for metal, num in METALS.items():
        li = ly.find_layer(num, 10)
        if li is None:
            continue
        shapes = [s for s in top.shapes(li).each() if not s.is_text()]
        for s in top.shapes(li).each():
            if not s.is_text():
                continue
            name = s.text_string
            p = s.text_pos
            hit = [sh.bbox() for sh in shapes if sh.bbox().contains(p)]
            if len(hit) != 1:
                raise SystemExit(f"FAIL: label {name} on {metal} sits on "
                                 f"{len(hit)} pin shapes")
            if name in found:
                raise SystemExit(f"FAIL: pin {name} labelled twice")
            b = hit[0]
            found[name] = {"layer": metal,
                           "rect": [round(b.left * um, 3), round(b.bottom * um, 3),
                                    round(b.right * um, 3), round(b.top * um, 3)]}

    contract = read_contract()
    names = [c["name"] for c in contract]
    missing = [n for n in names if n not in found]
    extra = [n for n in found if n not in names]
    if missing or extra:
        raise SystemExit(f"FAIL: pins missing from the GDS {missing}, "
                         f"not in the contract {extra}")
    pins = [dict(c, **found[c["name"]]) for c in contract]

    #- OBS: every metal over the outline, less the pin shapes
    full = db.Region(db.Box(0, 0, ob.right, ob.top))
    obs = []
    for metal in METALS:
        reg = full.dup()
        for p in pins:
            if p["layer"] == metal:
                reg -= db.Region(db.Box(*(round(v / um) for v in p["rect"])))
        for poly in reg.decompose_trapezoids_to_region().each():
            assert poly.is_box(), "OBS piece is not a rectangle"
            b = poly.bbox()
            obs.append((metal, (b.left * um, b.bottom * um, b.right * um, b.top * um)))

    d = {k: os.path.join(OUT, k) for k in ("gds", "lef", "lib", "vh", "spice")}
    for p in d.values():
        os.makedirs(p, exist_ok=True)
    #- the GDS LibreLane streams in is the input, unchanged
    with open(GDS, "rb") as fi, open(os.path.join(d["gds"], NAME + ".gds"), "wb") as fo:
        fo.write(fi.read())
    write_lef(os.path.join(d["lef"], NAME + ".lef"), W, H, pins, obs)
    write_lib(os.path.join(d["lib"], NAME + ".lib"), pins)
    write_vh(os.path.join(d["vh"], NAME + ".v"), pins)
    write_spice(os.path.join(d["spice"], NAME + ".spice"), pins)
    with open(os.path.join(OUT, "pins.json"), "w") as f:
        json.dump({"cell": NAME, "width_um": W, "height_um": H,
                   "source": os.path.relpath(GDS, HERE), "pins": pins}, f, indent=1)
    by_layer = {}
    for p in pins:
        by_layer[p["layer"]] = by_layer.get(p["layer"], 0) + 1
    print(f"{NAME}_width_um = {W:.3f}")
    print(f"{NAME}_height_um = {H:.3f}")
    print(f"{NAME}_pins_contract = {len(contract)}")
    print(f"{NAME}_pins_found = {len(pins)}")
    for k, v in sorted(by_layer.items()):
        print(f"{NAME}_pins_{k.lower()} = {v}")
    print(f"{NAME}_obs_rects = {len(obs)}")
    print(f"LEF: {os.path.join(d['lef'], NAME + '.lef')}")

def fmt(r):
    return f"{r[0]:.3f} {r[1]:.3f} {r[2]:.3f} {r[3]:.3f}"

def write_lef(path, W, H, pins, obs):
    o = ["VERSION 5.7 ;", "  NOWIREEXTENSIONATPIN ON ;",
         '  DIVIDERCHAR "/" ;', '  BUSBITCHARS "[]" ;',
         f"MACRO {NAME}", "  CLASS BLOCK ;", f"  FOREIGN {NAME} ;",
         "  ORIGIN 0.000 0.000 ;", f"  SIZE {W:.3f} BY {H:.3f} ;",
         "  SYMMETRY X Y ;"]
    for p in pins:
        o += [f"  PIN {p['name']}", f"    DIRECTION {p['direction']} ;",
              f"    USE {p['use']} ;", "    PORT",
              f"      LAYER {p['layer']} ;", f"        RECT {fmt(p['rect'])} ;",
              "    END", f"  END {p['name']}"]
    o.append("  OBS")
    for layer, r in obs:
        o += [f"      LAYER {layer} ;", f"        RECT {fmt(r)} ;"]
    o += ["  END", f"END {NAME}", "END LIBRARY", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))

def write_lib(path, pins):
    o = [f"library ({NAME}) {{", "  delay_model : table_lookup;",
         "  time_unit : \"1ns\";", "  voltage_unit : \"1V\";",
         "  current_unit : \"1mA\";", "  capacitive_load_unit (1, pf);",
         "  pulling_resistance_unit : \"1kohm\";",
         "  input_threshold_pct_fall : 50.0;", "  input_threshold_pct_rise : 50.0;",
         "  output_threshold_pct_fall : 50.0;", "  output_threshold_pct_rise : 50.0;",
         "  slew_lower_threshold_pct_fall : 20.0;", "  slew_lower_threshold_pct_rise : 20.0;",
         "  slew_upper_threshold_pct_fall : 80.0;", "  slew_upper_threshold_pct_rise : 80.0;",
         f"  cell ({NAME}) {{", "    dont_touch : true;", "    dont_use : true;"]
    kw = {"INOUT": "inout", "OUTPUT": "output", "INPUT": "input"}
    for p in pins:
        if p["use"] == "SIGNAL":
            o += [f"    pin ({p['name']}) {{", f"      direction : {kw[p['direction']]};",
                  "      capacitance : 0.02;", "    }"]
    o += ["  }", "}", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))

def write_vh(path, pins):
    kw = {"INOUT": "inout", "OUTPUT": "output", "INPUT": "input"}
    sig = [p for p in pins if p["use"] == "SIGNAL"]
    sup = [p for p in pins if p["use"] != "SIGNAL"]
    o = [f"// Black box of the analog hard macro {NAME}, from its GDS pins",
         "// (chip_integration/scripts/macros.py).",
         "(* blackbox *)", f"module {NAME} (", "`ifdef USE_POWER_PINS"]
    o += [f"    inout  wire {p['name']}," for p in sup]
    o.append("`endif")
    for i, p in enumerate(sig):
        o.append(f"    {kw[p['direction']]:6s} wire {p['name']}"
                 f"{',' if i < len(sig) - 1 else ''}")
    o += [");", "endmodule", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))

def write_spice(path, pins):
    """Ports only: chip LVS sees the analog macro as a black box."""
    names = [p["name"] for p in pins]
    o = [f"* {NAME}: black box of the analog hard macro, ports from its GDS",
         f".subckt {NAME} {' '.join(names[:13])}"]
    for i in range(13, len(names), 13):
        o.append("+ " + " ".join(names[i:i + 13]))
    o += [f".ends {NAME}", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))

# -------------------------------------------------------------------- digital
def digital():
    os.makedirs(os.path.join(HERE, "work", "macros", "asic_digital_top", "lib"),
                exist_ok=True)
    r = subprocess.run(["sta", "-no_init", "-exit",
                        os.path.join(HERE, "scripts", "digital_timing_model.tcl")],
                       cwd=HERE, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    n = 0
    for ln in r.stdout.splitlines():
        if ln.startswith("digital_timing_model_"):
            print(ln)
            n += 1
    print(f"digital_timing_models = {n}")

# ------------------------------------------------------------------- LEF view
def parse_lef(path):
    """SIZE, pins (layer, rects, direction, use) and OBS rects of the
    first MACRO in a LEF. Enough for a picture, not a LEF reader."""
    m = {"size": (0, 0), "pins": [], "obs": []}
    pin = None
    obs = False
    layer = None
    for raw in open(path, errors="replace"):
        t = raw.replace(";", " ").split()
        if not t:
            continue
        k = t[0]
        if k == "SIZE":
            m["size"] = (float(t[1]), float(t[3]))
        elif k == "PIN":
            pin = {"name": t[1], "rects": [], "dir": "", "use": "SIGNAL"}
            m["pins"].append(pin)
        elif k == "DIRECTION" and pin:
            pin["dir"] = t[1]
        elif k == "USE" and pin:
            pin["use"] = t[1]
        elif k == "OBS":
            obs, pin = True, None
        elif k == "LAYER":
            layer = t[1]
        elif k == "RECT":
            r = tuple(float(v) for v in t[1:5])
            if obs:
                m["obs"].append((layer, r))
            elif pin is not None:
                pin["rects"].append((layer, r))
        elif k == "END" and len(t) > 1 and pin and t[1] == pin["name"]:
            pin = None
    return m

LCOL = {"Metal1": "#4c8bf5", "Metal2": "#e8710a", "Metal3": "#1e8e3e",
        "Metal4": "#a142f4", "Metal5": "#8b5a2b"}
SUPPLY = {"POWER": "#d93025", "GROUND": "#1a73e8"}

def spread(items, lo, hi, gap):
    """Label positions along one edge: in pin order, at least `gap`
    apart, kept inside [lo, hi]. items: [(pos, name)] -> [(pos, at, name)]."""
    items = sorted(items)
    at = []
    for p, n in items:
        a = max(p, at[-1][1] + gap) if at else max(p, lo)
        at.append((p, a, n))
    over = at[-1][1] - hi if at else 0
    if over > 0:        # shift back, still keeping the gap
        at = [(p, a - over, n) for p, a, n in at]
        for i in range(len(at) - 2, -1, -1):
            if at[i][1] > at[i + 1][1] - gap:
                at[i] = (at[i][0], at[i + 1][1] - gap, at[i][2])
    return at

def lef_svg(lef, title, out):
    """The LEF as a router sees it: the outline, the OBS keep-out, every
    pin shape (signal pins by layer, supply pins by net), signal and
    edge supply pins labelled outside the edge they sit on."""
    m = parse_lef(lef)
    W, H = m["size"]
    s = 640.0 / max(W, H)
    edge_pins = {"W": [], "E": [], "S": [], "N": []}
    for p in m["pins"]:
        if not p["rects"]:
            continue
        x0 = min(r[0] for _, r in p["rects"]); x1 = max(r[2] for _, r in p["rects"])
        y0 = min(r[1] for _, r in p["rects"]); y1 = max(r[3] for _, r in p["rects"])
        tol = 0.5
        if x1 - x0 > 0.5 * W or y1 - y0 > 0.5 * H:
            continue        # a strap through the macro: legend, not a label
        if x0 <= tol:
            edge_pins["W"].append(((y0 + y1) / 2, p["name"]))
        elif x1 >= W - tol:
            edge_pins["E"].append(((y0 + y1) / 2, p["name"]))
        elif y0 <= tol:
            edge_pins["S"].append(((x0 + x1) / 2, p["name"]))
        elif y1 >= H - tol:
            edge_pins["N"].append(((x0 + x1) / 2, p["name"]))
    chw = 6.6           # px per character at font-size 11
    longest = {k: max([len(n) for _, n in v] or [0]) * chw for k, v in edge_pins.items()}
    lead = 26           # px of leader line before a label
    ml = 30 + longest["W"] + lead
    mr = 30 + longest["E"] + lead
    mt = 80 + longest["N"] + lead
    mb = 50 + longest["S"] + lead
    vw, vh = ml + W * s + mr, mt + H * s + mb

    def X(x): return ml + x * s

    def Y(y): return mt + (H - y) * s
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw:.0f}" height="{vh:.0f}" '
         f'viewBox="0 0 {vw:.0f} {vh:.0f}" font-family="Helvetica,Arial,sans-serif">',
         '<rect width="100%" height="100%" fill="white"/>',
         f'<text x="16" y="28" font-size="19" font-weight="bold">{title}</text>',
         f'<text x="16" y="50" font-size="13" fill="#555">{W:.2f} x {H:.2f} um, '
         f'{len(m["pins"])} pins; grey = OBS (router keep-out)</text>']
    if m["obs"]:
        o.append(f'<rect x="{X(0):.1f}" y="{Y(H):.1f}" width="{W * s:.1f}" '
                 f'height="{H * s:.1f}" fill="#e6e6e6"/>')
    o.append(f'<rect x="{X(0):.1f}" y="{Y(H):.1f}" width="{W * s:.1f}" height="{H * s:.1f}" '
             'fill="none" stroke="black" stroke-width="2"/>')
    legend = {}
    for p in m["pins"]:
        sup = p["use"] in SUPPLY
        for layer, (x0, y0, x1, y1) in p["rects"]:
            c = SUPPLY[p["use"]] if sup else LCOL.get(layer, "#333")
            legend[(f"{p['name']} ({p['use'].lower()})" if sup else f"{layer} pin")] = c
            w, h = (x1 - x0) * s, (y1 - y0) * s
            #- signal pins are tiny: draw them at least 5 px
            if not sup:
                cx, cy = X((x0 + x1) / 2), Y((y0 + y1) / 2)
                w, h = max(w, 5), max(h, 5)
                o.append(f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" '
                         f'height="{h:.1f}" fill="{c}"/>')
            else:
                o.append(f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{max(w, 1.5):.1f}" '
                         f'height="{max(h, 1.5):.1f}" fill="{c}" fill-opacity="0.8"/>')
    gap = 13
    lab = 'font-size="11" fill="#202124"'
    line = 'stroke="#9aa0a6" stroke-width="0.8"'
    for p, a, n in spread([(Y(v), n) for v, n in edge_pins["W"]], mt, mt + H * s, gap):
        o.append(f'<polyline points="{X(0):.1f},{p:.1f} {X(0) - 8:.1f},{p:.1f} '
                 f'{X(0) - lead + 4:.1f},{a:.1f}" fill="none" {line}/>')
        o.append(f'<text x="{X(0) - lead:.1f}" y="{a + 4:.1f}" text-anchor="end" {lab}>{n}</text>')
    for p, a, n in spread([(Y(v), n) for v, n in edge_pins["E"]], mt, mt + H * s, gap):
        o.append(f'<polyline points="{X(W):.1f},{p:.1f} {X(W) + 8:.1f},{p:.1f} '
                 f'{X(W) + lead - 4:.1f},{a:.1f}" fill="none" {line}/>')
        o.append(f'<text x="{X(W) + lead:.1f}" y="{a + 4:.1f}" {lab}>{n}</text>')
    for p, a, n in spread([(X(v), n) for v, n in edge_pins["S"]], ml, ml + W * s, gap):
        o.append(f'<polyline points="{p:.1f},{Y(0):.1f} {p:.1f},{Y(0) + 8:.1f} '
                 f'{a:.1f},{Y(0) + lead - 4:.1f}" fill="none" {line}/>')
        o.append(f'<text transform="translate({a + 4:.1f},{Y(0) + lead:.1f}) rotate(90)" {lab}>{n}</text>')
    for p, a, n in spread([(X(v), n) for v, n in edge_pins["N"]], ml, ml + W * s, gap):
        o.append(f'<polyline points="{p:.1f},{Y(H):.1f} {p:.1f},{Y(H) - 8:.1f} '
                 f'{a:.1f},{Y(H) - lead + 4:.1f}" fill="none" {line}/>')
        o.append(f'<text transform="translate({a + 4:.1f},{Y(H) - lead:.1f}) rotate(-90)" {lab}>{n}</text>')
    lx, ly = 16, vh - 18
    for name, c in legend.items():
        o.append(f'<rect x="{lx}" y="{ly - 11:.0f}" width="13" height="13" fill="{c}"/>')
        o.append(f'<text x="{lx + 18}" y="{ly:.0f}" font-size="12">{name}</text>')
        lx += 30 + 7 * len(name)
        if lx > vw - 140:
            lx, ly = 16, ly + 18
    o.append("</svg>")
    #- legend may have wrapped: grow the canvas
    if ly > vh - 18:
        nh = ly + 18
        o[0] = o[0].replace(f'height="{vh:.0f}"', f'height="{nh:.0f}"').replace(
            f'0 0 {vw:.0f} {vh:.0f}', f'0 0 {vw:.0f} {nh:.0f}')
        vh = nh
    with open(out, "w") as f:
        f.write("\n".join(o))
    png = out[:-4] + ".png"
    try:
        import cairosvg
        cairosvg.svg2png(url=out, write_to=png, output_width=int(vw * 1.6))
    except Exception as e:      # the SVG is the deliverable; the PNG a copy
        print(f"REPORT: no PNG for {out}: {e}")
    print(f"SVG: {out}")

def svg():
    os.makedirs(RENDERS, exist_ok=True)
    lef_svg(os.path.join(OUT, "lef", NAME + ".lef"),
            f"{NAME}: LEF made from the analog GDS by macros.py",
            os.path.join(RENDERS, "03a_analog_macro_lef.svg"))
    lef_svg(DIG_LEF, "asic_digital_top: LEF from the digital flow, used as is",
            os.path.join(RENDERS, "03b_digital_macro_lef.svg"))

def main(argv):
    what = argv[1:] or ["analog", "digital", "svg"]
    for w in what:
        {"analog": analog, "digital": digital, "svg": svg}[w]()

if __name__ == "__main__":
    main(sys.argv)
