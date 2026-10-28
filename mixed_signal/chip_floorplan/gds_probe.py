"""Measure the outlines the floorplan is drawn from, from GDS, not from notes.

    ./container.sh 'python3 gds_probe.py'      (run.sh phase `probe`)

- the digital top: the bounding box of the top cell of
  digital/asic_digital_top/physical/final_views/gds/asic_digital_top.gds;
- the frozen pad library gf180mcu_ocd_io (mounted at /foss/pdk_libs by
  `make pdk-libs`): the size of every pad cell the 1x0p5 ring uses;
- the frozen standard-cell library: the size of dfxtn_2, the latch in every
  unit cell, and so the library's row height.

Writes data/gds_probe.json and prints one `name = value` line per figure.
"""
import json
import os

import klayout.db as db

ROOT = "/foss/designs"
DIG = f"{ROOT}/digital/asic_digital_top/physical/final_views/gds/asic_digital_top.gds"
LIBS = "/foss/pdk_libs/gf180mcuD/libs.ref"
PAD_GDS = f"{LIBS}/gf180mcu_ocd_io/gds/gf180mcu_ocd_io.gds"
SC_GDS = f"{LIBS}/gf180mcu_as_sc_mcu7t3v3/gds/gf180mcu_as_sc_mcu7t3v3.gds"
PADS = ["asig_5p0", "bi_24t", "bi_a", "in_c", "in_s", "vdd", "vss", "dvdd", "dvss", "cor"]
SC = ["dfxtn_2"]


def size(cell):
    b = cell.dbbox()
    return round(b.width(), 4), round(b.height(), 4), [round(v, 4) for v in (b.left, b.bottom, b.right, b.top)]


def main():
    out = {"digital": {}, "pads": {}, "stdcell": {}}

    ly = db.Layout()
    ly.read(DIG)
    top = ly.top_cell()
    w, h, bb = size(top)
    out["digital"] = {"gds": DIG.replace(ROOT + "/", ""), "top": top.name, "w_um": w, "h_um": h, "bbox": bb}
    print(f"digital_w_um = {w}")
    print(f"digital_h_um = {h}")
    print(f"digital_area_um2 = {w * h:.1f}")

    ly = db.Layout()
    ly.read(PAD_GDS)
    names = {c.name for c in ly.each_cell()}
    for p in PADS:
        n = f"gf180mcu_ocd_io__{p}"
        if n not in names:
            out["pads"][p] = None
            print(f"REPORT: pad cell {n} not in gf180mcu_ocd_io")
            continue
        w, h, bb = size(ly.cell(n))
        out["pads"][p] = {"w_um": w, "h_um": h}
        print(f"pad_{p}_w_um = {w}")
        print(f"pad_{p}_h_um = {h}")
    out["pad_cells_in_library"] = sorted(n for n in names if n.startswith("gf180mcu_ocd_io__"))

    ly = db.Layout()
    ly.read(SC_GDS)
    for s in SC:
        n = f"gf180mcu_as_sc_mcu7t3v3__{s}"
        w, h, bb = size(ly.cell(n))
        out["stdcell"][s] = {"w_um": w, "h_um": h}
        print(f"sc_{s}_w_um = {w}")
        print(f"sc_{s}_h_um = {h}")

    os.makedirs("data", exist_ok=True)
    with open("data/gds_probe.json", "w") as f:
        json.dump(out, f, indent=1)
    print("REPORT: ocd_io pad cells: " + " ".join(c.replace("gf180mcu_ocd_io__", "") for c in out["pad_cells_in_library"]))


if __name__ == "__main__":
    main()
