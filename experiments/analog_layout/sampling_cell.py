"""Transmission-gate sampling cell for gf180mcuD, routed, with LVS pin labels.

Devices follow simulations/gf180_sampling_cell/transmission_gate.spice:
NMOS W=10u (10 x 1u fingers), PMOS W=20u (10 x 2u fingers), L=0.28u, 1 pF MIM.
Primitives: fet_fix.nfet_fixed / pfet_fixed (DRC-clean wrappers of the plugin
fets, gate contacts on top only) and mim_cap.mim_cap_b (layer-drawn MIM-B).

Routing plan (all metal2 rails run over the active region):
  - gates: metal1 bar across the top gate pads          -> sample / sample_b
  - even S/D columns: via1 at the strap's lower end, M2 rail  -> in
  - odd  S/D columns: via1 at strap centre, M2 rail            -> hold
  - in / hold rails of both devices joined by vertical M2 on the left / right
  - hold -> MIM top plate through a M2..M5 via stack; MIM bottom plate -> vss
  - body taps: nfet legs -> vss (M2 bar below the device), pfet legs -> vdd

Run: experiments/analog_layout/run.sh experiments/analog_layout/sampling_cell.py sampling_cell_tg
LVS: experiments/analog_layout/lvs.sh work/sampling_cell_tg.gds sampling_cell_tg sampling_cell_tg_sch.spice
"""
import gdsfactory as gf
import gf180mcu
from mim_cap import mim_cap_b
from fet_fix import nfet_fixed, pfet_fixed

PDK = gf180mcu.PDK; PDK.activate()

# layers
M1, M2, M3, M4, M5 = (34, 0), (36, 0), (42, 0), (46, 0), (81, 0)
V1, V2, V3, V4 = (35, 0), (38, 0), (40, 0), (41, 0)
M1_PIN, M2_PIN = (34, 10), (36, 10)
# rule-driven dimensions (um)
VIA = 0.26; ENC_SIDE = 0.01; ENC_END = 0.06
M2_W = 0.30; M1_SP = 0.23; M2_SP = 0.28
# device geometry (from fet_fix inventory): 11 S/D straps at x = -4.0 + 0.8 k, width 0.23
STRAP_X = [-4.0 + 0.8 * k for k in range(11)]
FINGER_X = [-3.6 + 0.8 * k for k in range(10)]
TAP_X = 4.69                       # tap leg centre (both sides), metal1 0.23 wide

W_NMOS_F, W_PMOS_F, NF, L_GATE = 1.0, 2.0, 10, 0.28
MIM_SIDE = 22.4


def _rect(c, layer, x0, y0, x1, y1):
    c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)

def _via(c, lower, via, upper, x, y, pad_w=0.28, pad_h=0.38):
    """Single via between two metals with rule-compliant pads on both."""
    _rect(c, lower, x - pad_w / 2, y - pad_h / 2, x + pad_w / 2, y + pad_h / 2)
    _rect(c, via, x - VIA / 2, y - VIA / 2, x + VIA / 2, y + VIA / 2)
    _rect(c, upper, x - 0.19, y - 0.19, x + 0.19, y + 0.19)

M5_W = 0.50                         # MT.1: top metal >= 0.44
def _stack_m2_m5(c, x, y):
    for lower, via, upper in ((M2, V2, M3), (M3, V3, M4), (M4, V4, M5)):
        _via(c, lower, via, upper, x, y, pad_w=0.38, pad_h=0.38)
    _rect(c, M5, x - M5_W / 2, y - M5_W / 2, x + M5_W / 2, y + M5_W / 2)


@gf.cell
def sampling_cell_tg(w_nmos_f: float = W_NMOS_F, w_pmos_f: float = W_PMOS_F, nf: int = NF,
                     mim_side: float = MIM_SIDE, l_gate: float = L_GATE) -> gf.Component:
    c = gf.Component()
    n = c << nfet_fixed(w_gate=w_nmos_f, l_gate=l_gate, nf=nf, gate_side="top")
    p = c << pfet_fixed(w_gate=w_pmos_f, l_gate=l_gate, nf=nf, gate_side="top")
    hn, hp = w_nmos_f / 2, w_pmos_f / 2           # strap half-heights (0.49 / 0.99 ~ w/2)
    # place: nfet at origin, pfet below with room for the vss bar and rails
    py = -(1.55 + 2.05 + 2.2)
    p.dmovey(py)

    def route_device(yoff, hw, gate_pad_y0, gate_pad_y1, net_gate):
        # gate bar over the top pads (pads are 0.34 wide at finger centres, y gate_pad_y0..y1)
        _rect(c, M1, FINGER_X[0] - 0.17, yoff + gate_pad_y1 - 0.25, FINGER_X[-1] + 0.17, yoff + gate_pad_y1)
        c.add_label(net_gate, position=(0, yoff + gate_pad_y1 - 0.12), layer=M1_PIN)
        # odd columns -> hold: via at strap centre, M2 rail at y=yoff
        for k, x in enumerate(STRAP_X):
            if k % 2 == 1:
                _via(c, M1, V1, M2, x, yoff)
        _rect(c, M2, STRAP_X[1] - 0.19, yoff - M2_W / 2, STRAP_X[-2] + 0.19, yoff + M2_W / 2)
        # even columns -> in: extend strap downward, via below the active, M2 rail
        y_in = yoff - hw - 0.55
        for k, x in enumerate(STRAP_X):
            if k % 2 == 0:
                _rect(c, M1, x - 0.115, y_in - 0.19, x + 0.115, yoff - hw + 0.05)
                _via(c, M1, V1, M2, x, y_in)
        _rect(c, M2, STRAP_X[0] - 0.19, y_in - M2_W / 2, STRAP_X[-1] + 0.19, y_in + M2_W / 2)
        return y_in

    y_in_n = route_device(0.0, hn, 0.705, 1.205, "sample")
    y_in_p = route_device(py, hp, 1.205, 1.705, "sample_b")

    # vertical M2 joins: 'in' on the left, 'hold' on the right (outside the tap legs)
    xl, xr = -(TAP_X + 0.65), (TAP_X + 0.65)
    _rect(c, M2, xl - M2_W / 2, y_in_p - M2_W / 2, xl + M2_W / 2, y_in_n + M2_W / 2)
    _rect(c, M2, STRAP_X[0] - 0.19, y_in_n - M2_W / 2, xl + M2_W / 2, y_in_n + M2_W / 2)      # nfet in rail -> left
    _rect(c, M2, STRAP_X[0] - 0.19, y_in_p - M2_W / 2, xl + M2_W / 2, y_in_p + M2_W / 2)      # pfet in rail -> left
    c.add_label("in", position=(xl, (y_in_n + y_in_p) / 2), layer=M2_PIN)
    _rect(c, M2, xr - M2_W / 2, py - M2_W / 2, xr + M2_W / 2, 0 + M2_W / 2)
    _rect(c, M2, STRAP_X[-2] - 0.19, -M2_W / 2, xr + M2_W / 2, M2_W / 2)                       # nfet hold rail -> right
    _rect(c, M2, STRAP_X[-2] - 0.19, py - M2_W / 2, xr + M2_W / 2, py + M2_W / 2)              # pfet hold rail -> right
    c.add_label("hold", position=(xr, py / 2), layer=M2_PIN)

    # body taps: nfet legs -> vss bar (M2 below the nfet 'in' rail), pfet legs -> vdd bar
    def tap_bar(yoff, leg_half, y_bar, net):
        for sx in (-1, 1):
            x = sx * TAP_X
            _rect(c, M1, x - 0.115, min(yoff - leg_half, y_bar) - 0.19, x + 0.115, yoff - leg_half + 0.05)
            _via(c, M1, V1, M2, x, y_bar)
        _rect(c, M2, -TAP_X - 0.19, y_bar - M2_W / 2, TAP_X + 0.19, y_bar + M2_W / 2)
        c.add_label(net, position=(0, y_bar), layer=M2_PIN)
    y_vss = y_in_n - 0.75
    y_vdd = y_in_p - 0.75
    tap_bar(0.0, 0.905, y_vss, "vss")
    tap_bar(py, 1.405, y_vdd, "vdd")

    # hold capacitor to the right: hold -> top plate (M2..M5 stack), bottom plate -> vss
    cap = c << mim_cap_b(w=mim_side, l=mim_side)
    cap.dmovex(xr + 3.0 - cap.dxmin)
    cap.dmovey(py / 2 - cap.dy)
    top = cap.ports["top"]; bot = cap.ports["bot"]
    tx, ty = top.dcenter; bx, by = bot.dcenter
    # via stacks must keep their Metal4 pads >= 1.2 um from the MIM bottom plate (MIMTM.1):
    # place them 1.5 um beyond the terminals and bridge with M5 (top-metal strips, >= 0.44 wide).
    GAP = 1.5
    # hold stack right of the cap. Its M2 feed runs at sy, deliberately ABOVE the
    # cap centre line where the vss stack's M2 pad sits (they must not share y).
    sx, sy = tx + GAP, py / 2 + 2.5
    _rect(c, M2, xr - M2_W / 2, sy - M2_W / 2, sx + 0.19, sy + M2_W / 2)      # M2 from the hold column
    _stack_m2_m5(c, sx, sy)
    _rect(c, M5, tx - 0.4, ty - M5_W / 2, sx + M5_W / 2, ty + M5_W / 2)       # M5 terminal -> stack x
    _rect(c, M5, sx - M5_W / 2, min(sy, ty) - M5_W / 2, sx + M5_W / 2, max(sy, ty) + M5_W / 2)
    # vss: cap bottom terminal (M5) -> stack down (left of the cap) -> M3 -> vss bar.
    # The link runs in M3 because it must cross the vertical M2 'hold' column at xr.
    sbx = bx - GAP
    _stack_m2_m5(c, sbx, by)
    _rect(c, M5, sbx - M5_W / 2, by - M5_W / 2, bx + 0.4, by + M5_W / 2)
    _via(c, M2, V2, M3, TAP_X, y_vss, pad_w=0.38, pad_h=0.38)                  # vss bar (M2) -> M3
    _rect(c, M3, TAP_X - 0.19, y_vss - M2_W / 2, sbx + 0.19, y_vss + M2_W / 2)  # M3 horizontal, crosses hold (M2)
    _rect(c, M3, sbx - M2_W / 2, y_vss - M2_W / 2, sbx + M2_W / 2, by + 0.19)  # M3 vertical into the stack

    c.info.update(dict(w_nmos_um=w_nmos_f * nf, w_pmos_um=w_pmos_f * nf, mim_side_um=mim_side))
    return c


if __name__ == "__main__":
    comp = sampling_cell_tg()
    # LVS/Magic want a stable top-cell name: wrap the cached (auto-named) cell.
    top = gf.Component(name="sampling_cell_tg")
    top << comp
    top.flatten()                       # bring pin labels to the top level for Magic/Netgen
    top.write_gds("work/sampling_cell_tg.gds")
    bb = comp.dbbox()
    print(f"wrote work/sampling_cell_tg.gds (top cell sampling_cell_tg); bbox {bb.width():.2f} x {bb.height():.2f} um")
