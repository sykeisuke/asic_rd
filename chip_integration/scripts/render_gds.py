#!/usr/bin/env python3
"""GDS renders with real layers (KLayout), for the report.

    python3 scripts/render_gds.py inputs   # step 0: the three input GDS files
    python3 scripts/render_gds.py chip     # step 6: the signed-off chip, whole and zoomed

Run inside the container. Colours are the PDK's KLayout layer properties
(the template's gf180mcu_render.lyp, the same file LibreLane renders
with); the background is white. Every picture lands in renders/.
"""

import json
import os
import sys

import klayout.db as db
import klayout.lay as lay

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(HERE, "renders")
LYP = os.path.join(HERE, "inputs", "template", "librelane", "gf180mcu_render.lyp")
PDK_LYP = "/foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp"
CHIP = os.path.join(HERE, "librelane", "runs", "chip_top", "final", "gds", "chip_top.gds")
HIDE = {(0, 0)}         # the PR boundary would hatch a whole macro


def view(gds, lyp=LYP, texts=True):
    lv = lay.LayoutView()
    lv.load_layout(gds, True)
    if os.path.exists(lyp):
        lv.load_layer_props(lyp)
    lv.add_missing_layers()
    it = lv.begin_layers()
    while not it.at_end():
        p = it.current()
        if (p.source_layer, p.source_datatype) in HIDE:
            p.dither_pattern = 1
            p.frame_color = 0x808080
            lv.set_layer_properties(it, p)
        it.next()
    lv.set_config("background-color", "#ffffff")
    lv.set_config("grid-visible", "false")
    lv.set_config("text-visible", "true" if texts else "false")
    lv.set_config("text-color", "#000000")
    lv.set_config("text-lazy-rendering", "false")
    lv.max_hier()
    return lv


def save(lv, box, name, width):
    lv.zoom_box(box)
    h = int(width * box.height() / box.width())
    out = os.path.join(R, name)
    lv.save_image(out, width, max(h, 200))
    print(f"PNG: {out}")


def inputs():
    a = os.path.join(HERE, "inputs", "analog", "wsa_analog_top.gds")
    d = os.path.join(HERE, "inputs", "digital", "asic_digital_top.gds")
    lv = view(a, PDK_LYP)
    bb = lv.active_cellview().layout().top_cell().dbbox()
    save(lv, bb.enlarged(3, 3), "00a_input_analog_gds.png", 2000)
    lv = view(d, LYP, texts=False)
    bb = lv.active_cellview().layout().top_cell().dbbox()
    save(lv, bb.enlarged(3, 3), "00b_input_digital_gds.png", 1600)
    #- the provider ID cells the template requires, side by side
    ip = os.path.join(HERE, "inputs", "template", "ip")
    ly = db.Layout()
    top = ly.create_cell("template_ip")
    x = 0.0
    for n in ("qrcode_id", "shuttle_id", "project_id", "marker", "logo"):
        tmp = db.Layout()
        tmp.read(os.path.join(ip, f"gf180mcu_ws_ip__{n}", "gds", f"gf180mcu_ws_ip__{n}.gds"))
        c = tmp.top_cell()
        bb = c.dbbox()
        tgt = ly.create_cell(c.name)
        tgt.copy_tree(c)
        top.insert(db.DCellInstArray(tgt.cell_index(), db.DTrans(x - bb.left, -bb.bottom)))
        x += bb.width() + 20
    os.makedirs(os.path.join(HERE, "work", "render"), exist_ok=True)
    tmp = os.path.join(HERE, "work", "render", "template_ip.gds")
    ly.write(tmp)
    lv = view(tmp, LYP, texts=False)
    bb = lv.active_cellview().layout().top_cell().dbbox()
    save(lv, bb.enlarged(10, 10), "00c_input_template_ip.png", 2000)


def chip():
    lv = view(CHIP, LYP, texts=False)
    bb = lv.active_cellview().layout().top_cell().dbbox()
    save(lv, bb.enlarged(10, 10), "06a_chip_final.png", 2400)
    #- the windows render_steps.py measured on the PDN database (the drawn
    #- analog wires, the drawn supply straps); fixed fall-backs otherwise
    win = {"analog_wires": (340, 1180, 760, 1560), "supply_straps": (430, 1280, 960, 2531)}
    wj = os.path.join(HERE, "work", "render", "windows.json")
    if os.path.exists(wj):
        with open(wj) as f:
            win.update({k: tuple(v) for k, v in json.load(f).items()})
    #- the two macros and the west analog pads (macros.yaml placements)
    save(lv, db.DBox(300, 930, 840, 1480), "06b_chip_macros_zoom.png", 2000)
    #- the analog pad wires as they are in the final GDS (analog_routes.tcl)
    save(lv, db.DBox(*win["analog_wires"]), "06c_chip_analog_wires_zoom.png", 2000)
    #- the AVDD / AVSS pads and their drawn straps (power_routes.tcl)
    save(lv, db.DBox(*win["supply_straps"]), "06d_chip_supply_straps_zoom.png", 1600)


def main(argv):
    os.makedirs(R, exist_ok=True)
    for w in argv[1:] or ["inputs", "chip"]:
        {"inputs": inputs, "chip": chip}[w]()


if __name__ == "__main__":
    main(sys.argv)
