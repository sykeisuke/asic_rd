"""Continuous-time comparator (NMOS-input baseline) with a generic column router.

Devices follow simulations/gf180_comparator/comparator.spice (9 transistors).
Each transistor is a routed block (fet_fix + tg_switch.route_fet): metal2 rail
'a' (even S/D columns), rail 'b' (odd columns), metal1 gate bar. Blocks are
stacked vertically; every net gets a vertical metal3 bus on the right, and each
rail / gate bar is extended in metal2 to its bus and connected with via2
(gate bars: via1 first). Body taps go to vdd / vss buses.

Pins: sample, ramp, bias, dout, vdd, vss  (internal: left, outa, outb, tail)

Run: experiments/analog_layout/run.sh experiments/analog_layout/comparator.py comparator
LVS: experiments/analog_layout/lvs.sh work/comparator.gds comparator comparator_sch.spice
"""
import gdsfactory as gf
import gf180mcu
from tg_switch import fet_geom, route_fet, _rect, _via, M1, M2, M3, V1, V2, M2_W, M1_PIN, M2_PIN
from fet_fix import nfet_fixed, pfet_fixed

PDK = gf180mcu.PDK; PDK.activate()
M3_PIN = (42, 10)
BUS_PITCH = 0.76
GAP_DEV = 2.6

# name, kind, w_finger, nf, L, source net (rail a), drain net (rail b), gate net
DEVICES = [
    ("XINP",   "nfet", 2.0, 10, 0.5,  "tail", "left", "sample"),
    ("XINN",   "nfet", 2.0, 10, 0.5,  "tail", "outa", "ramp"),
    ("XLOADD", "pfet", 4.0, 10, 0.5,  "vdd",  "left", "left"),
    ("XLOADM", "pfet", 4.0, 10, 0.5,  "vdd",  "outa", "left"),
    ("XTAIL",  "nfet", 2.0, 10, 1.0,  "vss",  "tail", "bias"),
    ("XBUF1",  "nfet", 1.0, 4,  0.28, "vss",  "outb", "outa"),
    ("XBUF2",  "pfet", 2.0, 4,  0.28, "vdd",  "outb", "outa"),
    ("XBUF3",  "nfet", 2.0, 4,  0.28, "vss",  "dout", "outb"),
    ("XBUF4",  "pfet", 4.0, 4,  0.28, "vdd",  "dout", "outb"),
]
# PMOS-input variant (comparator_offset_pmos.spice): input pair and tail in PMOS, loads in NMOS
DEVICES_P = [
    ("XINP",   "pfet", 4.0, 10, 0.5,  "tail", "left", "sample"),
    ("XINN",   "pfet", 4.0, 10, 0.5,  "tail", "outa", "ramp"),
    ("XLOADD", "nfet", 2.0, 10, 0.5,  "vss",  "left", "left"),
    ("XLOADM", "nfet", 2.0, 10, 0.5,  "vss",  "outa", "left"),
    ("XTAIL",  "pfet", 2.0, 10, 1.0,  "vdd",  "tail", "bias"),
    ("XBUF1",  "nfet", 1.0, 4,  0.28, "vss",  "outb", "outa"),
    ("XBUF2",  "pfet", 2.0, 4,  0.28, "vdd",  "outb", "outa"),
    ("XBUF3",  "nfet", 2.0, 4,  0.28, "vss",  "dout", "outb"),
    ("XBUF4",  "pfet", 4.0, 4,  0.28, "vdd",  "dout", "outb"),
]
NETS = ["vdd", "vss", "sample", "ramp", "bias", "tail", "left", "outa", "outb", "dout"]
PINS = ["sample", "ramp", "bias", "dout", "vdd", "vss"]


def _build(devices) -> gf.Component:
    c = gf.Component()
    def nolabel(name, pos, layer): pass
    # place devices top-down
    blocks = []
    y = 0.0
    xmax = 0.0
    for (name, kind, wf, nf, L, s_net, d_net, g_net) in devices:
        cell = (nfet_fixed if kind == "nfet" else pfet_fixed)(w_gate=wf, l_gate=L, nf=nf, gate_side="top")
        g = fet_geom(cell, wf)
        h = cell.dbbox().height()
        yoff = y - h / 2
        (c << cell).dmovey(yoff)
        y_a, y_b = route_fet(c, g, yoff, g_net, nolabel)
        y_gate = yoff + g["pad_y1"] - 0.12
        # tap bar for this device
        y_tap = y_a - 0.75
        for x in g["taps"]:
            _rect(c, M1, x - 0.115, y_tap - 0.19, x + 0.115, yoff - g["tap_half"] + 0.05)
            _via(c, M1, V1, M2, x, y_tap)
        _rect(c, M2, min(g["taps"]) - 0.19, y_tap - M2_W / 2, max(g["taps"]) + 0.19, y_tap + M2_W / 2)
        blocks.append(dict(g=g, yoff=yoff, y_a=y_a, y_b=y_b, y_gate=y_gate, y_tap=y_tap,
                           s_net=s_net, d_net=d_net, g_net=g_net,
                           tap_net=("vss" if kind == "nfet" else "vdd")))
        xmax = max(xmax, cell.dbbox().right)
        y = yoff - h / 2 - GAP_DEV
    y_bottom = y + GAP_DEV
    # vertical M3 buses on the right
    bus_x = {net: xmax + 1.2 + i * BUS_PITCH for i, net in enumerate(NETS)}
    def to_bus(net, y_row, x_from, layer_from):
        """Extend a horizontal connection at y_row from x_from to the net's bus and drop a via2."""
        xb = bus_x[net]
        if layer_from == M1:                       # gate bar: via1 up to M2 first
            _via(c, M1, V1, M2, x_from, y_row)
        _rect(c, M2, x_from - 0.19, y_row - M2_W / 2, xb + 0.19, y_row + M2_W / 2)
        _via(c, M2, V2, M3, xb, y_row, pad_w=0.38, pad_h=0.38)
    for b in blocks:
        g = b["g"]
        to_bus(b["d_net"], b["y_b"], max(g["straps"][1::2]), M2)       # drain rail (odd cols)
        to_bus(b["s_net"], b["y_a"], max(g["straps"][0::2]), M2)       # source rail (even cols)
        to_bus(b["g_net"], b["y_gate"], g["pad_x1"] - 0.17, M1)         # gate bar end
        to_bus(b["tap_net"], b["y_tap"], max(g["taps"]), M2)           # body tap bar
    for net in NETS:
        xb = bus_x[net]
        _rect(c, M3, xb - M2_W / 2, y_bottom - 0.4, xb + M2_W / 2, 0.6)
        if net in PINS:
            c.add_label(net, position=(xb, 0.3), layer=M3_PIN)
    return c

@gf.cell
def cmp_nmos() -> gf.Component:
    return _build(DEVICES)

@gf.cell
def cmp_pmos() -> gf.Component:
    return _build(DEVICES_P)


if __name__ == "__main__":
    import sys
    variant = sys.argv[1] if len(sys.argv) > 1 else "n"
    k = cmp_pmos() if variant == "p" else cmp_nmos()
    name = "comparator_p" if variant == "p" else "comparator"
    top = gf.Component(name=name); top << k; top.flatten(); top.write_gds(f"work/{name}.gds")
    b = k.dbbox(); print(f"wrote work/{name}.gds; {b.width():.1f} x {b.height():.1f} um = {b.width()*b.height()/1e6:.4f} mm^2")
