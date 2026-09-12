"""Four-cell sampling array: 4 x sampling_cell_tg with a shared input bus.

Array-level routing (cells stacked vertically at PITCH):
  - in:      each cell's vertical M2 'in' column (x = xl) joined by one M2 bus
  - vss/vdd: via2 from each cell's M2 tap bar onto vertical M3 buses (x = 0 / x = 1.2)
  - hold_i, sample_i, sample_b_i: per-cell pins (labels at array level)

Run: experiments/analog_layout/run.sh experiments/analog_layout/sampling_array.py sampling_array4
LVS: experiments/analog_layout/lvs.sh work/sampling_array4.gds sampling_array4 sampling_array4_sch.spice
"""
import gdsfactory as gf
import gf180mcu
from sampling_cell import sampling_cell_tg, M1_PIN, M2_PIN, M2, M3, V2, M2_W, _rect, _via

PDK = gf180mcu.PDK; PDK.activate()
M3_PIN = (42, 10)
N_CELLS, PITCH = 4, 26.0
X_VSS_BUS, X_VDD_BUS = 0.0, 1.2


@gf.cell
def sampling_array4(n: int = N_CELLS, pitch: float = PITCH) -> gf.Component:
    c = gf.Component()
    cell = sampling_cell_tg(labels=False)
    g = cell.info
    xl, xr = g["xl"], g["xr"]
    for i in range(n):
        ref = c << cell
        ref.dmovey(-i * pitch)
        yo = -i * pitch
        # per-cell pins
        c.add_label(f"hold{i}", position=(xr, yo + g["py"] / 2), layer=M2_PIN)
        c.add_label(f"sample{i}", position=(0, yo + g["y_gate_n"]), layer=M1_PIN)
        c.add_label(f"sample_b{i}", position=(0, yo + g["y_gate_p"]), layer=M1_PIN)
        # power: lift each cell's vss / vdd M2 bar onto the M3 buses
        _via(c, M2, V2, M3, X_VSS_BUS, yo + g["y_vss"], pad_w=0.38, pad_h=0.38)
        _via(c, M2, V2, M3, X_VDD_BUS, yo + g["y_vdd"], pad_w=0.38, pad_h=0.38)
    # shared input: one M2 strip along the cells' 'in' columns
    y_top = g["y_in_n"] + M2_W / 2
    y_bot = -(n - 1) * pitch + g["y_in_p"] - M2_W / 2
    _rect(c, M2, xl - M2_W / 2, y_bot, xl + M2_W / 2, y_top)
    c.add_label("in", position=(xl, (y_top + y_bot) / 2), layer=M2_PIN)
    # M3 power buses
    for x, net in ((X_VSS_BUS, "vss"), (X_VDD_BUS, "vdd")):
        ys = [(-i * pitch + (g["y_vss"] if net == "vss" else g["y_vdd"])) for i in range(n)]
        _rect(c, M3, x - M2_W / 2, min(ys) - 0.19, x + M2_W / 2, max(ys) + 0.19)
        c.add_label(net, position=(x, (min(ys) + max(ys)) / 2), layer=M3_PIN)
    return c


if __name__ == "__main__":
    arr = sampling_array4()
    top = gf.Component(name="sampling_array4"); top << arr; top.flatten()
    top.write_gds("work/sampling_array4.gds")
    bb = arr.dbbox()
    print(f"wrote work/sampling_array4.gds; bbox {bb.width():.1f} x {bb.height():.1f} um = {bb.width()*bb.height()/1e6:.4f} mm^2")
