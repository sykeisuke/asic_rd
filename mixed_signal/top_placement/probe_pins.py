#!/usr/bin/env python3
"""Report where an analog cell's ports are, from its GDS text labels.

    python3 probe_pins.py ../analog_layout/physical/final_views/gds/CMP.gds

Prints one line per label (layer/datatype, text, position in um, the
shape on the same layer under it) and the cell bbox.  This is how the
wrapper generator's pin table is checked against the drawn layout: a
GDS is binary, the label list is not.
"""

import sys

import klayout.db as db


def main(path):
    ly = db.Layout()
    ly.read(path)
    top = ly.top_cell()
    dbu = ly.dbu
    bb = top.dbbox()
    print(f"cell {top.name} bbox = {bb.left:.3f},{bb.bottom:.3f} "
          f"{bb.right:.3f},{bb.top:.3f}  ({bb.width():.3f} x {bb.height():.3f} um)")
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        r = db.Region(top.begin_shapes_rec(li))
        if not r.is_empty():
            b = r.bbox().to_dtype(dbu)
            print(f"layer {info.layer}/{info.datatype} shapes={r.count()} "
                  f"bbox={b.left:.3f},{b.bottom:.3f} {b.right:.3f},{b.top:.3f}")
        it = top.begin_shapes_rec(li)
        while not it.at_end():
            s = it.shape()
            if s.is_text():
                t = s.text.transformed(it.trans())
                x, y = t.x * dbu, t.y * dbu
                #- the drawn shapes on the label's own layer number that
                #- contain the label point
                under = []
                for lj in ly.layer_indexes():
                    if ly.get_info(lj).layer != info.layer:
                        continue
                    rr = db.Region(top.begin_shapes_rec(lj))
                    pt = db.Box(t.x - 1, t.y - 1, t.x + 1, t.y + 1)
                    for p in rr.merged().interacting(db.Region(pt)).each():
                        pb = p.bbox().to_dtype(dbu)
                        under.append(f"{ly.get_info(lj).datatype}:"
                                     f"{pb.left:.3f},{pb.bottom:.3f},"
                                     f"{pb.right:.3f},{pb.top:.3f}")
                print(f"label {info.layer}/{info.datatype} {t.string!r} "
                      f"at {x:.3f},{y:.3f} under={under}")
            it.next()


def shapes(path, layers):
    """Merged polygons on the given `layer/datatype` pairs, and the cell
    names -- enough to see whether a pin's metal is free above it."""
    ly = db.Layout()
    ly.read(path)
    top = ly.top_cell()
    want = [tuple(int(v) for v in s.split("/")) for s in layers]
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        if (info.layer, info.datatype) not in want:
            continue
        for p in db.Region(top.begin_shapes_rec(li)).merged().each():
            b = p.bbox().to_dtype(ly.dbu)
            print(f"shape {info.layer}/{info.datatype} pts={p.num_points()} "
                  f"{b.left:.3f},{b.bottom:.3f} {b.right:.3f},{b.top:.3f}")
            if p.num_points() > 4:
                pts = " ".join(f"({q.x * ly.dbu:.3f},{q.y * ly.dbu:.3f})"
                               for q in p.each_point_hull())
                print(f"  hull {pts}")
    print("cells", sorted(c.name for c in ly.each_cell()))


if __name__ == "__main__":
    #- probe_pins.py GDS...              labels and layer extents
    #- probe_pins.py --shapes GDS L/D... merged polygons on those layers
    if sys.argv[1] == "--shapes":
        shapes(sys.argv[2], sys.argv[3:])
    else:
        for p in sys.argv[1:]:
            main(p)
