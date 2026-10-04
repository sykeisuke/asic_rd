"""Ramp generator: PMOS current source + 1 pF MIM-B ramp capacitor + NMOS reset.

Mirrors simulations/gf180_ramp_generator/ramp_generator.spice:
  XSOURCE ramp biasp vdd vdd  pfet_03v3 L=2u   W=1u  nf=1
  XRESET  ramp reset vss vss  nfet_03v3 L=0.5u W=10u nf=5
  CRAMP   ramp vss 1p  (MIM-B 22.4 x 22.4 um)
Pins: ramp, biasp, reset, vdd, vss.

Run: experiments/analog_layout/run.sh experiments/analog_layout/ramp_gen.py ramp_gen
LVS: experiments/analog_layout/lvs.sh work/ramp_gen.gds ramp_gen ramp_gen_sch.spice
"""
import gdsfactory as gf
import gf180mcu
from tg_switch import fet_geom, route_fet, _rect, _via, M1, M2, M3, V1, V2, M2_W, M1_PIN, M2_PIN
from fet_fix import nfet_fixed, pfet_fixed
from mim_cap import mim_cap_b
from sampling_cell import _stack_m2_m5, M5, M5_W

PDK = gf180mcu.PDK; PDK.activate()
M3_PIN = (42, 10)


@gf.cell
def ramp_gen(mim_side: float = 22.4) -> gf.Component:
    c = gf.Component()
    def label(name, pos, layer): c.add_label(name, position=pos, layer=layer)
    src = pfet_fixed(w_gate=1.0, l_gate=2.0, nf=1, gate_side="top")     # W=1u L=2u current source
    rst = nfet_fixed(w_gate=2.0, l_gate=0.5, nf=5, gate_side="top")     # W=10u L=0.5u reset
    gs, gr = fet_geom(src, 1.0), fet_geom(rst, 2.0)
    p = c << src
    n = c << rst
    ny = -(src.dbbox().height() / 2 + rst.dbbox().height() / 2 + 2.6)
    n.dmovey(ny)
    # pfet: a (even col 0) = source -> vdd ; b (odd col 1) = drain -> ramp ; gate -> biasp
    y_a_p, y_b_p = route_fet(c, gs, 0.0, "biasp", label)
    # nfet: a (even) = source -> vss ; b (odd) = drain -> ramp ; gate -> reset
    y_a_n, y_b_n = route_fet(c, gr, ny, "reset", label)
    tap_x = max(gs["taps"] + gr["taps"])
    xl, xr = -(tap_x + 0.80), (tap_x + 0.80)
    # ramp: join the two b rails on the right
    _rect(c, M2, xr - M2_W / 2, y_b_n - M2_W / 2, xr + M2_W / 2, y_b_p + M2_W / 2)
    _rect(c, M2, max(gs["straps"][1::2]) - 0.19, y_b_p - M2_W / 2, xr + M2_W / 2, y_b_p + M2_W / 2)
    _rect(c, M2, max(gr["straps"][1::2]) - 0.19, y_b_n - M2_W / 2, xr + M2_W / 2, y_b_n + M2_W / 2)
    label("ramp", (xr, (y_b_n + y_b_p) / 2), M2_PIN)
    # vdd: pfet a rail + pfet taps (bar) joined on the left
    def tap_bar(yoff, g, y_bar):
        for x in g["taps"]:
            _rect(c, M1, x - 0.115, y_bar - 0.19, x + 0.115, yoff - g["tap_half"] + 0.05)
            _via(c, M1, V1, M2, x, y_bar)
        _rect(c, M2, min(g["taps"]) - 0.19, y_bar - M2_W / 2, max(g["taps"]) + 0.19, y_bar + M2_W / 2)
        return y_bar
    y_vdd = tap_bar(0.0, gs, y_a_p - 0.75)
    _rect(c, M2, xl - M2_W / 2, y_vdd - M2_W / 2, xl + M2_W / 2, y_a_p + M2_W / 2)
    _rect(c, M2, xl - M2_W / 2, y_a_p - M2_W / 2, min(gs["straps"]) + 0.19, y_a_p + M2_W / 2)
    _rect(c, M2, xl - M2_W / 2, y_vdd - M2_W / 2, min(gs["taps"]) + 0.19, y_vdd + M2_W / 2)
    label("vdd", (xl, (y_vdd + y_a_p) / 2), M2_PIN)
    # vss: nfet a rail + nfet taps joined on the left
    y_vss = tap_bar(ny, gr, y_a_n - 0.75)
    _rect(c, M2, xl - M2_W / 2, y_vss - M2_W / 2, xl + M2_W / 2, y_a_n + M2_W / 2)
    _rect(c, M2, xl - M2_W / 2, y_a_n - M2_W / 2, min(gr["straps"]) + 0.19, y_a_n + M2_W / 2)
    _rect(c, M2, xl - M2_W / 2, y_vss - M2_W / 2, min(gr["taps"]) + 0.19, y_vss + M2_W / 2)
    label("vss", (xl, (y_vss + y_a_n) / 2), M2_PIN)
    # ramp capacitor to the right: ramp -> top plate (stack), bottom plate -> vss (M3 link)
    cap = c << mim_cap_b(w=mim_side, l=mim_side)
    cap.dmovex(xr + 3.0 - cap.dxmin); cap.dmovey(ny / 2 - cap.dy)
    tx, ty = cap.ports["top"].dcenter; bx, by = cap.ports["bot"].dcenter
    GAP = 1.5
    sx, sy = tx + GAP, ny / 2 + 2.5
    _rect(c, M2, xr - M2_W / 2, sy - M2_W / 2, sx + 0.19, sy + M2_W / 2)
    _rect(c, M2, xr - M2_W / 2, min(sy, y_b_n) - M2_W / 2, xr + M2_W / 2, max(sy, y_b_p) + M2_W / 2)
    _stack_m2_m5(c, sx, sy)
    _rect(c, M5, tx - 0.4, ty - M5_W / 2, sx + M5_W / 2, ty + M5_W / 2)
    _rect(c, M5, sx - M5_W / 2, min(sy, ty) - M5_W / 2, sx + M5_W / 2, max(sy, ty) + M5_W / 2)
    sbx = bx - GAP
    _stack_m2_m5(c, sbx, by)
    _rect(c, M5, sbx - M5_W / 2, by - M5_W / 2, bx + 0.4, by + M5_W / 2)
    _via(c, M2, V2, M3, max(gr["taps"]), y_vss, pad_w=0.38, pad_h=0.38)          # vss bar -> M3
    _rect(c, M3, max(gr["taps"]) - 0.19, y_vss - M2_W / 2, sbx + 0.19, y_vss + M2_W / 2)
    _rect(c, M3, sbx - M2_W / 2, min(y_vss, by) - M2_W / 2, sbx + M2_W / 2, max(y_vss, by) + 0.19)
    return c


if __name__ == "__main__":
    r = ramp_gen()
    top = gf.Component(name="ramp_gen"); top << r; top.flatten(); top.write_gds("work/ramp_gen.gds")
    b = r.dbbox(); print(f"wrote work/ramp_gen.gds; {b.width():.1f} x {b.height():.1f} um")
