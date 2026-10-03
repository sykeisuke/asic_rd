"""4-to-1 analog MUX: four TG switches onto a shared bus, plus the bus-reset NMOS.

Mirrors simulations/gf180_four_cell_array/four_cell_mux.spice:
  XMiN/XMiP: hold_i -> mux_bus, NMOS W=5u nf=5, PMOS W=10u nf=5 (sel_i / sel_bi)
  XBUS_RESET: mux_bus -> vss, NMOS L=0.5u W=5u nf=5 (bus_reset)

Run: experiments/analog_layout/run.sh experiments/analog_layout/mux4.py mux4
LVS: experiments/analog_layout/lvs.sh work/mux4.gds mux4 mux4_sch.spice
"""
import gdsfactory as gf
import gf180mcu
from tg_switch import tg_switch, fet_geom, route_fet, _rect, _via, M1, M2, M3, V1, V2, M2_W, M1_PIN, M2_PIN
from fet_fix import nfet_fixed

PDK = gf180mcu.PDK; PDK.activate()
M3_PIN = (42, 10)
PITCH = 14.0
X_VSS_BUS, X_VDD_BUS = 0.0, 1.2


@gf.cell
def mux4(pitch: float = PITCH) -> gf.Component:
    c = gf.Component()
    sw = tg_switch(w_n=1.0, w_p=2.0, nf=5, labels=False)
    g = sw.info
    xl, xr = g["xl"], g["xr"]
    for i in range(4):
        yo = -i * pitch
        (c << sw).dmovey(yo)
        c.add_label(f"hold{i}", position=(xl, yo + (g["y_a_n"] + g["y_a_p"]) / 2), layer=M2_PIN)
        c.add_label(f"sel{i}", position=(0, yo + g["y_gn"]), layer=M1_PIN)
        c.add_label(f"sel_b{i}", position=(0, yo + g["y_gp"]), layer=M1_PIN)
        _via(c, M2, V2, M3, X_VSS_BUS, yo + g["y_vss"], pad_w=0.38, pad_h=0.38)
        _via(c, M2, V2, M3, X_VDD_BUS, yo + g["y_vdd"], pad_w=0.38, pad_h=0.38)
    # shared bus: one M2 strip along the switches' 'b' columns (x = xr)
    y_top = g["y_b_n"] + M2_W / 2
    # bus-reset NMOS below the last switch: odd straps -> mux_bus, even -> vss, gate -> bus_reset
    rst = nfet_fixed(w_gate=1.0, l_gate=0.5, nf=5, gate_side="top")
    gr = fet_geom(rst, 1.0)
    y_rst = -(4 - 1) * pitch + g["py"] - 5.5
    (c << rst).dmovey(y_rst)
    def label(name, pos, layer): c.add_label(name, position=pos, layer=layer)
    y_a, y_b = route_fet(c, gr, y_rst, "bus_reset", label)          # a=even (-> vss), b=odd (-> bus)
    _rect(c, M2, max(gr["straps"][1::2]) - 0.19, y_b - M2_W / 2, xr + M2_W / 2, y_b + M2_W / 2)
    _rect(c, M2, xr - M2_W / 2, y_b - M2_W / 2, xr + M2_W / 2, y_top)
    c.add_label("mux_bus", position=(xr, (y_top + y_b) / 2), layer=M2_PIN)
    # reset source (even straps rail) -> vss bus via M3
    _via(c, M2, V2, M3, X_VSS_BUS, y_a, pad_w=0.38, pad_h=0.38)
    # reset transistor body taps -> vss (its tap legs), through the same rail
    for x in gr["taps"]:
        _rect(c, M1, x - 0.115, y_a - 0.19, x + 0.115, y_rst - gr["tap_half"] + 0.05)
        _via(c, M1, V1, M2, x, y_a)
    _rect(c, M2, min(gr["taps"]) - 0.19, y_a - M2_W / 2, max(gr["taps"]) + 0.19, y_a + M2_W / 2)
    # M3 power buses
    ys_vss = [-i * pitch + g["y_vss"] for i in range(4)] + [y_a]
    ys_vdd = [-i * pitch + g["y_vdd"] for i in range(4)]
    for x, ys, net in ((X_VSS_BUS, ys_vss, "vss"), (X_VDD_BUS, ys_vdd, "vdd")):
        _rect(c, M3, x - M2_W / 2, min(ys) - 0.19, x + M2_W / 2, max(ys) + 0.19)
        c.add_label(net, position=(x, (min(ys) + max(ys)) / 2), layer=M3_PIN)
    return c


if __name__ == "__main__":
    m = mux4()
    top = gf.Component(name="mux4"); top << m; top.flatten(); top.write_gds("work/mux4.gds")
    b = m.dbbox(); print(f"wrote work/mux4.gds; {b.width():.1f} x {b.height():.1f} um")
