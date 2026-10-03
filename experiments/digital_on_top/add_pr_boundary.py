"""Keep only the macro cell and add a PR boundary (KLayout PR_bndry 0/0 and Magic PRBOUND 63/0) equal to
the layout's bounding box to the top cell of macro/comparator_min.gds."""
import pya
ly = pya.Layout(); ly.read("macro/comparator_min.gds")
# gdsfactory also writes a $$$CONTEXT_INFO$$$ top cell; LibreLane's KLayout
# steps require exactly one top cell.
for c in list(ly.top_cells()):
    if c.name != "comparator_min":
        ly.prune_cell(c.cell_index(), -1)
top = ly.top_cell()
# Normalise the origin: LEF ORIGIN must be (0,0) or the GDS geometry is
# streamed out displaced from the LEF abstract the router used.
bb = top.bbox()
if bb.p1 != pya.Point(0, 0):
    top.transform(pya.Trans(-bb.p1.x, -bb.p1.y))
    bb = top.bbox()
for ln, dt in ((0, 0), (63, 0)):
    top.shapes(ly.layer(ln, dt)).insert(bb)
ly.write("macro/comparator_min.gds")
print(f"PR boundary {bb.width()*ly.dbu:.3f} x {bb.height()*ly.dbu:.3f} um added on 0/0 and 63/0")
