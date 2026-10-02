#!/usr/bin/env python3
"""Hard-macro views of the analog cells, for the digital-on-top chip.

    python3 macros.py            # every macro in MACROS
    python3 macros.py wsa_cmp

The analog layouts in `../analog_layout/physical/final_views/gds/` are
drawn cells with their ports as Metal2 labels deep inside dense Metal2.
A digital router cannot use them as they are: nothing says where a pin
is, the pins have no free metal above them to land on, and a 6 um tall
cell will usually fall between two top-level Metal5 power straps.

Each macro here is the cell, unchanged, inside a wrapper that adds:

- a Via2 onto every signal pin's own Metal2 (or the cell's own Metal3,
  where the cell already routes that net there), and a Metal3 stub from
  it to the north or south edge of the macro -- that stub is the LEF
  pin, so the router only ever connects at the boundary;
- for VDD and VSS, a Via2 array onto the cell's supply Metal2, a Metal3
  pad, a Via3 array, and a Metal4 strap running the full macro height.
  The macro is 90 um tall because the chip's Metal5 straps are 75 um
  apart (`PDN_HPITCH`): any 85 um window holds one VDD and one VSS
  strap wherever the macro is placed, and PDN connects the two at the
  crossing (`add_pdn_connect Metal4 Metal5`).

Every coordinate in the tables is in the cell's own frame and was read
off the GDS with `probe_pins.py`; the cell is not modified.  All cell
names inside a macro are prefixed with the macro name, so two cicpy
cells that both contain an `NFET03V3_W2_L0p28_NF2` cannot collide when
the chip merges their GDS.

Writes `work/macros/<macro>/{gds,lef,lib,vh,spice}/<macro>.*`.
"""

import os
import sys

import klayout.db as db

HERE = os.path.dirname(os.path.abspath(__file__))
ANALOG = os.path.join(HERE, "..", "analog_layout")
OUT = os.path.join(HERE, "work", "macros")

#- gf180mcuD GDS numbers (libs.tech/klayout/tech/gf180mcu.map)
LAYER = {"Metal1": (34, 0), "Via1": (35, 0), "Metal2": (36, 0),
         "Via2": (38, 0), "Metal3": (42, 0), "Via3": (40, 0),
         "Metal4": (46, 0)}
PIN = {"Metal3": (42, 10), "Metal4": (46, 10)}
#- 0/0 is the PR boundary (Magic's PRBNDRY, `calma 0 0`). LibreLane's
#- Magic.StreamOut reads each macro's FIXED_BBOX from it and stops
#- ("Failed to extract PR boundary") without one, so the macro draws its
#- own outline there. The cell's cicpy outline on 0/0 is dropped: one
#- boundary per macro, the macro's.
BOUNDARY = (0, 0)
DROP = [BOUNDARY]

#- Via2/Via3: 0.26 square, 0.26 space, metal enclosure 0.01 everywhere
#- and 0.06 on two opposite sides (tech LEF ENCLOSURE BELOW/ABOVE)
VIA, VSPACE, ENC_MIN, ENC_OPP = 0.26, 0.26, 0.01, 0.06
STUB_W = 0.50            # Metal3 signal stub, 0.28 minimum
PAD_ENC = 0.12           # Metal3 around a signal pin's Via2
STRAP_W = 4.00           # Metal4 supply strap
KEEPOUT = 1.00           # OBS margin around the analog cell

MACROS = {
    #- the comparator of simulations/gf180_comparator, as cicpy placed it.
    #- Its signal nets are NOT routed inside the cell (make lvs CELL=CMP
    #- fails, ADR 0006); the macro gives it a place and pins on the chip,
    #- not a working comparator.
    "wsa_cmp": {
        "cell": "CMP",
        "size": (109.2, 90.0),
        "origin": (6.0, 42.0),
        "signals": [
            # name, LEF direction, landing layer, landing rect, edge
            ("vin",   "INOUT",  "Metal2", (19.63, 3.255, 19.97, 4.100), "N"),
            ("vramp", "INOUT",  "Metal2", (5.930, 3.255, 6.270, 4.100), "N"),
            ("vbias", "INOUT",  "Metal2", (88.43, 3.255, 88.77, 4.100), "N"),
            ("dout",  "OUTPUT", "Metal2", (61.24, 1.210, 65.10, 1.550), "S"),
        ],
        "supplies": [
            # name, USE, Via2 rect on the cell's Metal2, Metal3 pad,
            # Via3 rect, Metal4 strap centre x
            ("VDD", "POWER", (28.20, 4.450, 38.90, 4.790),
             (28.00, 4.330, 39.00, 5.900), (28.00, 5.200, 39.00, 5.900), 33.50),
            ("VSS", "GROUND", (0.000, 3.255, 0.655, 4.100),
             (0.000, 3.200, 0.655, 5.500), (0.000, 4.500, 0.655, 5.500), 0.33),
        ],
    },
    #- the LVS-clean inverter (make lvs CELL=INV). A and Y already reach
    #- Metal3 inside the cell, so their stubs join that Metal3 directly.
    "wsa_inv": {
        "cell": "INV",
        "size": (14.0, 90.0),
        "origin": (3.0, 42.0),
        "signals": [
            ("A", "INOUT", "Metal3", (3.500, 5.380, 4.000, 5.660), "N"),
            #- Y leaves by the north edge too, so every analog pin faces
            #- the pad row: down off the Y bar, west under the cell's
            #- keep-out, then up a column outside it. Waypoints are in the
            #- cell frame; the last one runs to the edge named.
            ("Y", "INOUT", "Metal3", (3.750, 1.200, 4.250, 1.525),
             [(4.0, -2.5), (-2.0, -2.5), (-2.0, "N")]),
        ],
        "supplies": [
            ("VDD", "POWER", (7.550, 3.500, 8.160, 3.840),
             (7.600, 2.600, 8.600, 3.960), (7.600, 2.600, 8.600, 3.300), 7.85),
            ("VSS", "GROUND", (0.000, 2.900, 0.655, 3.600),
             (0.000, 1.900, 0.655, 3.500), (0.000, 1.900, 0.655, 2.700), 0.33),
        ],
    },
    #- the gdsfactory inverter (make gf-inverter, ADR 0008): same circuit
    #- as INV, drawn by hand on the gf180mcu plugin. Everything it draws
    #- is Metal1, so each port lands on Metal1: Via1 -> a Metal2 pad ->
    #- Via2 beside (not on) the Via1 -> Metal3. Y is a 0.23 um strip,
    #- narrower than a Via1, so it gets a Metal1 patch where the via
    #- lands. The cell's origin is its centre. Unlike the analog pads'
    #- nets, A and Y connect to ordinary core nets, so LibreLane's router
    #- wires them the way the template's SRAM pins are wired.
    "wsa_inv_gf": {
        "cell": "INV_GF",
        "gds": os.path.join("misc", "build", "gds", "INV_GF.gds"),
        "spice": os.path.join("misc", "INV_GF.spice"),
        "size": (16.0, 90.0),
        "origin": (8.0, 42.0),
        "signals": [
            # name, direction, "Metal1", Via1 rect, edge, {m1 patch,
            # Metal2 pad, Via2 rect}
            ("A", "INPUT", "Metal1", (-1.555, 0.860, -1.215, 2.560), "N",
             {"m2": (-1.635, 0.800, -1.135, 3.300),
              "v2": (-1.635, 2.720, -1.135, 3.300)}),
            ("Y", "OUTPUT", "Metal1", (-0.190, 1.400, 0.190, 2.020), "N",
             {"m1": (-0.190, 1.400, 0.190, 2.020),
              "m2": (-0.250, 1.400, 0.250, 3.300),
              "v2": (-0.250, 2.720, 0.250, 3.300)}),
        ],
        "supplies": [
            # name, USE, Via2 rect, Metal3 pad, Via3 rect, strap x,
            # {Via1 rect on the cell's Metal1, Metal2 pad}
            ("VDD", "POWER", (2.000, 6.350, 2.800, 7.110),
             (1.900, 6.350, 6.200, 7.110), (3.200, 6.350, 6.200, 7.110), 5.0,
             {"v1": (0.950, 6.400, 1.550, 7.060),
              "m2": (0.900, 6.350, 2.800, 7.110)}),
            ("VSS", "GROUND", (-2.800, -2.160, -2.000, -1.460),
             (-6.200, -2.160, -1.900, -1.460), (-6.200, -2.160, -3.200, -1.460), -5.0,
             {"v1": (-1.550, -2.160, -0.950, -1.460),
              "m2": (-2.800, -2.160, -0.900, -1.460)}),
        ],
    },
}


def box(r):
    return db.DBox(r[0], r[1], r[2], r[3])


def moved(r, o):
    return (r[0] + o[0], r[1] + o[1], r[2] + o[0], r[3] + o[1])


def via_array(r):
    """Largest via array inside rect `r` meeting the enclosure rule.
    Tries both orientations of the 0.06 opposite-side enclosure."""
    best = []
    for ex, ey in ((ENC_OPP, ENC_MIN), (ENC_MIN, ENC_OPP)):
        w, h = r[2] - r[0] - 2 * ex, r[3] - r[1] - 2 * ey
        nx = int((w + VSPACE) // (VIA + VSPACE) + 1e-9)
        ny = int((h + VSPACE) // (VIA + VSPACE) + 1e-9)
        if nx < 1 or ny < 1:
            continue
        #- centre the array so the spare enclosure is shared
        x0 = r[0] + (r[2] - r[0] - (nx * VIA + (nx - 1) * VSPACE)) / 2
        y0 = r[1] + (r[3] - r[1] - (ny * VIA + (ny - 1) * VSPACE)) / 2
        cuts = [(x0 + i * (VIA + VSPACE), y0 + j * (VIA + VSPACE))
                for i in range(nx) for j in range(ny)]
        if len(cuts) > len(best):
            best = cuts
    if not best:
        raise SystemExit(f"no via fits in {r}")
    return [(snap(x), snap(y)) for x, y in best]


def snap(v):
    """The 5 nm manufacturing grid."""
    return round(v / 0.005) * 0.005


def cut_boxes(cuts):
    return [db.DBox(x, y, x + VIA, y + VIA) for x, y in cuts]


def bbox_of(boxes):
    b = db.DBox()
    for x in boxes:
        b += x
    return b


def build(name, spec):
    src = os.path.join(ANALOG, spec.get("gds", os.path.join(
        "physical", "final_views", "gds", spec["cell"] + ".gds")))
    cell_ly = db.Layout()
    cell_ly.read(src)
    for li in cell_ly.layer_indexes():
        info = cell_ly.get_info(li)
        if (info.layer, info.datatype) in DROP:
            cell_ly.clear_layer(li)

    ly = db.Layout()
    ly.dbu = 0.001
    top = ly.create_cell(name)
    inner = ly.create_cell(spec["cell"])
    #- copy_tree rescales if the cell's database unit differs
    inner.copy_tree(cell_ly.cell(spec["cell"]))
    for c in list(ly.each_cell()):
        if c.cell_index() != top.cell_index():
            c.name = f"{name}__{c.name}"
    ox, oy = spec["origin"]
    top.insert(db.DCellInstArray(inner.cell_index(), db.DTrans(ox, oy)))

    lay = {k: ly.layer(*v) for k, v in LAYER.items()}
    pin = {k: ly.layer(*v) for k, v in PIN.items()}
    W, H = spec["size"]
    top.shapes(ly.layer(*BOUNDARY)).insert(db.DBox(0, 0, W, H))
    cell_bb = inner.dbbox().moved(ox, oy)
    if not db.DBox(0, 0, W, H).contains(cell_bb.p1) or \
            not db.DBox(0, 0, W, H).contains(cell_bb.p2):
        raise SystemExit(f"{name}: cell does not fit the macro")

    lef_pins = []   # (name, direction, use, [(layer, DBox)])
    obs_m3 = []

    for sig, direction, landing, rect, edge, *more in spec["signals"]:
        opt = more[0] if more else {}
        r = moved(rect, (ox, oy))
        shapes = []
        if landing == "Metal1":
            #- Via1 on the cell's Metal1 (patched where too narrow), a
            #- Metal2 pad, and the Via2 at the far end of that pad
            if "m1" in opt:
                top.shapes(lay["Metal1"]).insert(box(moved(opt["m1"], (ox, oy))))
            for c in cut_boxes(via_array(r)):
                top.shapes(lay["Via1"]).insert(c)
            top.shapes(lay["Metal2"]).insert(box(moved(opt["m2"], (ox, oy))))
            cuts = cut_boxes(via_array(moved(opt["v2"], (ox, oy))))
            for c in cuts:
                top.shapes(lay["Via2"]).insert(c)
            pad = bbox_of(cuts).enlarged(PAD_ENC, PAD_ENC)
            xc, yc = pad.center().x, pad.center().y
            shapes.append(pad)
        elif landing == "Metal2":
            cuts = cut_boxes(via_array(r))
            for c in cuts:
                top.shapes(lay["Via2"]).insert(c)
            pad = bbox_of(cuts).enlarged(PAD_ENC, PAD_ENC)
            xc, yc = pad.center().x, pad.center().y
            shapes.append(pad)
        else:
            #- the cell's own Metal3: the stub overlaps it, no via
            pad = box(r)
            xc, yc = pad.center().x, pad.center().y
        #- the stub ends where the pad's centre is; keep that on the
        #- 5 nm grid (a 1.3625 um centre made metal3_label_OFFGRID)
        xc, yc = snap(xc), snap(yc)
        #- a plain edge name is a straight stub; a waypoint list is a
        #- Manhattan path, the last point's y an edge name
        if isinstance(edge, str):
            edge = [(xc - ox, edge)]
        pts = [(xc, yc)]
        for wx, wy in edge:
            if isinstance(wy, str):
                wy = H if wy == "N" else 0.0
            else:
                wy += oy
            pts.append((snap(wx + ox), snap(wy)))
        stubs = []
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            h = STUB_W / 2
            stubs.append(db.DBox(min(xa, xb) - h, min(ya, yb) - h,
                                 max(xa, xb) + h, max(ya, yb) + h)
                         & db.DBox(0, 0, W, H))
        shapes += stubs
        for s in shapes:
            top.shapes(lay["Metal3"]).insert(s)
        for s in stubs:
            top.shapes(pin["Metal3"]).insert(s)
        #- label at the macro edge, where the pin is reached
        xe, ye = pts[-1]
        ly_y = H - 0.5 if ye >= H else 0.5
        top.shapes(pin["Metal3"]).insert(db.DText(sig, db.DTrans(xe, ly_y)))
        lef_pins.append((sig, direction, "SIGNAL",
                         [("Metal3", s) for s in shapes]))

    for sup, use, v2, m3, v3, strap_x, *more in spec["supplies"]:
        opt = more[0] if more else {}
        xs = strap_x + ox
        strap = db.DBox(xs - STRAP_W / 2, 0.0, xs + STRAP_W / 2, H)
        if "v1" in opt:
            #- a Metal1-only cell: Via1 up to a Metal2 pad first
            for c in cut_boxes(via_array(moved(opt["v1"], (ox, oy)))):
                top.shapes(lay["Via1"]).insert(c)
            top.shapes(lay["Metal2"]).insert(box(moved(opt["m2"], (ox, oy))))
        for c in cut_boxes(via_array(moved(v2, (ox, oy)))):
            top.shapes(lay["Via2"]).insert(c)
        pad = box(moved(m3, (ox, oy)))
        top.shapes(lay["Metal3"]).insert(pad)
        obs_m3.append(pad)
        #- Via3 only where the pad lies under the strap
        v3r = box(moved(v3, (ox, oy))) & strap
        for c in cut_boxes(via_array((v3r.left, v3r.bottom,
                                      v3r.right, v3r.top))):
            top.shapes(lay["Via3"]).insert(c)
        top.shapes(lay["Metal4"]).insert(strap)
        top.shapes(pin["Metal4"]).insert(strap)
        top.shapes(pin["Metal4"]).insert(
            db.DText(sup, db.DTrans(xs, H / 2)))
        lef_pins.append((sup, "INOUT", use, [("Metal4", strap)]))

    #- nothing of the chip is routed over the analog cell: Metal1..4 are
    #- obstructed over it (Metal5 stays open for the PDN straps)
    keep = cell_bb.enlarged(KEEPOUT, KEEPOUT) & db.DBox(0, 0, W, H)
    obs = [(m, keep) for m in ("Metal1", "Metal2", "Metal3", "Metal4")]
    obs += [("Metal3", p) for p in obs_m3]

    d = {k: os.path.join(OUT, name, k) for k in
         ("gds", "lef", "lib", "vh", "spice")}
    for p in d.values():
        os.makedirs(p, exist_ok=True)
    ly.write(os.path.join(d["gds"], name + ".gds"))
    write_lef(os.path.join(d["lef"], name + ".lef"), name, W, H,
              lef_pins, obs)
    write_lib(os.path.join(d["lib"], name + ".lib"), name, lef_pins)
    write_vh(os.path.join(d["vh"], name + ".v"), name, lef_pins)
    write_spice(os.path.join(d["spice"], name + ".spice"), name, spec,
                lef_pins)

    n_v1 = sum(1 for _ in top.shapes(lay["Via1"]).each())
    n_v2 = sum(1 for _ in top.shapes(lay["Via2"]).each())
    n_v3 = sum(1 for _ in top.shapes(lay["Via3"]).each())
    print(f"{name}_width_um = {W:.2f}")
    print(f"{name}_height_um = {H:.2f}")
    print(f"{name}_pins = {len(lef_pins)}")
    print(f"{name}_via1 = {n_v1}")
    print(f"{name}_via2 = {n_v2}")
    print(f"{name}_via3 = {n_v3}")
    print(f"Macro: {os.path.join(d['gds'], name + '.gds')}")


def fmt(b):
    return f"{b.left:.3f} {b.bottom:.3f} {b.right:.3f} {b.top:.3f}"


def write_lef(path, name, W, H, pins, obs):
    o = ["VERSION 5.7 ;", "  NOWIREEXTENSIONATPIN ON ;",
         '  DIVIDERCHAR "/" ;', '  BUSBITCHARS "[]" ;',
         f"MACRO {name}", "  CLASS BLOCK ;", f"  FOREIGN {name} ;",
         "  ORIGIN 0.000 0.000 ;", f"  SIZE {W:.3f} BY {H:.3f} ;",
         "  SYMMETRY X Y ;"]
    for pname, direction, use, shapes in pins:
        o += [f"  PIN {pname}", f"    DIRECTION {direction} ;",
              f"    USE {use} ;", "    PORT"]
        for layer, b in shapes:
            o += [f"      LAYER {layer} ;", f"        RECT {fmt(b)} ;"]
        o += ["    END", f"  END {pname}"]
    o.append("  OBS")
    for layer, b in obs:
        o += [f"      LAYER {layer} ;", f"        RECT {fmt(b)} ;"]
    o += ["  END", f"END {name}", "END LIBRARY", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))


def write_lib(path, name, pins):
    """Pin directions and a nominal load, no arcs: STA sees the macro's
    output as a start point and its inputs as end points of nothing."""
    o = [f"library ({name}) {{",
         "  delay_model : table_lookup;",
         "  time_unit : \"1ns\";", "  voltage_unit : \"1V\";",
         "  current_unit : \"1mA\";", "  capacitive_load_unit (1, pf);",
         "  pulling_resistance_unit : \"1kohm\";",
         "  input_threshold_pct_fall : 50.0;",
         "  input_threshold_pct_rise : 50.0;",
         "  output_threshold_pct_fall : 50.0;",
         "  output_threshold_pct_rise : 50.0;",
         "  slew_lower_threshold_pct_fall : 20.0;",
         "  slew_lower_threshold_pct_rise : 20.0;",
         "  slew_upper_threshold_pct_fall : 80.0;",
         "  slew_upper_threshold_pct_rise : 80.0;",
         f"  cell ({name}) {{", "    dont_touch : true;",
         "    dont_use : true;"]
    for pname, direction, use, _ in pins:
        if use != "SIGNAL":
            continue
        d = {"INOUT": "inout", "OUTPUT": "output", "INPUT": "input"}[direction]
        o += [f"    pin ({pname}) {{", f"      direction : {d};",
              "      capacitance : 0.02;", "    }"]
    o += ["  }", "}", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))


def write_vh(path, name, pins):
    sig = [p for p in pins if p[2] == "SIGNAL"]
    kw = {"INOUT": "inout", "OUTPUT": "output", "INPUT": "input"}
    o = ["// Black box of an analog hard macro. Generated by macros.py.",
         "(* blackbox *)", f"module {name} ("]
    o += ["`ifdef USE_POWER_PINS", "    inout  wire VDD,",
          "    inout  wire VSS,", "`endif"]
    for i, (pname, direction, _, _) in enumerate(sig):
        comma = "," if i < len(sig) - 1 else ""
        o.append(f"    {kw[direction]:6s} wire {pname}{comma}")
    o += [");", "endmodule", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))


def write_spice(path, name, spec, pins):
    """The macro as a subcircuit of the cell's own netlist, so the
    wrapper can be LVS-checked against what the cell was generated from:
    a stub that shorts two pins, or misses one, shows up there."""
    src = os.path.join(ANALOG, spec.get("spice", os.path.join("spice", spec["cell"] + ".spice")))
    body, ports = [], None
    with open(src) as f:
        for line in f:
            t = line.split()
            if t and t[0].lower() == ".subckt":
                ports = t[2:]
            elif t and t[0].lower() == ".ends":
                break
            elif ports is not None and t and not line.startswith("*"):
                body.append(line.rstrip())
    #- the macro's port names, in the cell's port order, matched without
    #- regard to case (the cell says vdd, the macro says VDD)
    names = {p[0].lower(): p[0] for p in pins}
    mports = [names[p.lower()] for p in ports]
    ren = dict(zip(ports, mports))
    o = [f"* {name}: {spec['cell']} inside its hard-macro wrapper",
         f".subckt {name} {' '.join(mports)}"]
    for line in body:
        t = line.split()
        o.append(" ".join(ren.get(x, x) for x in t))
    o += [f".ends {name}", ""]
    with open(path, "w") as f:
        f.write("\n".join(o))


def main(argv):
    names = argv or list(MACROS)
    for n in names:
        build(n, MACROS[n])


if __name__ == "__main__":
    main(sys.argv[1:])
