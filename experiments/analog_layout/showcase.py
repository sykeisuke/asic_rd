"""What gdsfactory + the gf180mcu PDK plugin can do — a quick tour.

Run: experiments/analog_layout/run.sh experiments/analog_layout/showcase.py showcase
Outputs (work/): showcase.gds, showcase.png, catalog.txt
"""
import collections, gdsfactory as gf, gf180mcu
from sampling_cell import sampling_cell_tg, W_NMOS, W_PMOS, MIM_SIDE

PDK = gf180mcu.PDK; PDK.activate()

# 1) The PDK is a Python object: every primitive is a callable with parameters.
cells = sorted(PDK.cells)
groups = collections.Counter(n.split("_")[0] for n in cells)
with open("work/catalog.txt", "w") as f:
    f.write(f"{len(cells)} cells\n")
    for k, v in groups.most_common(): f.write(f"{k:12s} {v}\n")
    f.write("\n" + "\n".join(cells))
print(f"PDK cells: {len(cells)}; families: {dict(groups.most_common(8))}")

# 2) Parametric replication: a 4-cell sampling array from ONE Python function.
@gf.cell
def sampling_array(n: int = 4, pitch: float = 40.0) -> gf.Component:
    c = gf.Component()
    cell = sampling_cell_tg()
    for i in range(n):
        ref = c << cell
        ref.dmovey(i * pitch)
        # expose the cell's held-voltage node position as a named port for later routing
        c.add_port(name=f"vhold_{i}", center=(ref.dxmax, ref.dy), width=0.5, orientation=0, layer=(34, 0))
    return c

arr = sampling_array(n=4)
bb = arr.dbbox()
print(f"4-cell array: {bb.width():.1f} x {bb.height():.1f} um = {bb.width()*bb.height()/1e6:.4f} mm^2 "
      f"({len(arr.ports)} ports)")
arr.write_gds("work/showcase.gds")

# 3) Rendering straight to an image (no GUI needed): matplotlib plot of the layout.
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
arr.plot()                      # gdsfactory -> matplotlib
plt.gcf().set_size_inches(6, 10); plt.title("4 x sampling_cell_tg (nfet %.0fu / pfet %.0fu / MIM %.1fu)" % (W_NMOS, W_PMOS, MIM_SIDE), fontsize=9)
plt.savefig("work/showcase.png", dpi=130, bbox_inches="tight"); print("wrote work/showcase.png")

# 4) Sweeps are one loop: what does the cell area do vs. hold-cap size?
for side in (10.0, 15.9, 22.4):          # ~0.2, 0.5, 1.0 pF at ~2 fF/um^2
    c = sampling_cell_tg(mim_side=side)   # each argument set -> its own cached cell + unique name
    b = c.dbbox(); print(f"  MIM {side:5.1f} um -> cell {b.width():5.1f} x {b.height():5.1f} um  ({c.name})")
