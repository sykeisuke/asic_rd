"""Generic routed transmission-gate switch on the DRC-clean fets (any nf).

Nets/ports: a, b (the two switch terminals), gn (NMOS gate), gp (PMOS gate),
vdd (PMOS body taps), vss (NMOS body taps). Geometry is read back from the
fet cells so the routing follows the device (finger count, pitch, width).
Routing pattern is the one proven on sampling_cell_tg: metal1 gate bar over the
top gate pads; odd S/D columns -> via1 at strap centre -> M2 rail (b); even
columns -> strap extension below the active -> via1 -> M2 rail (a); vertical
M2 joins between NMOS and PMOS on the left (a) and right (b); tap bars in M2.
"""
import gdsfactory as gf
import gf180mcu
from fet_fix import nfet_fixed, pfet_fixed

PDK = gf180mcu.PDK; PDK.activate()
M1, M2, M3 = (34, 0), (36, 0), (42, 0)
V1, V2 = (35, 0), (38, 0)
M1_PIN, M2_PIN = (34, 10), (36, 10)
VIA = 0.26; M2_W = 0.30

def _rect(c, layer, x0, y0, x1, y1):
    c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)

def _via(c, lower, via, upper, x, y, pad_w=0.28, pad_h=0.38):
    _rect(c, lower, x - pad_w / 2, y - pad_h / 2, x + pad_w / 2, y + pad_h / 2)
    _rect(c, via, x - VIA / 2, y - VIA / 2, x + VIA / 2, y + VIA / 2)
    _rect(c, upper, x - 0.19, y - 0.19, x + 0.19, y + 0.19)

def fet_geom(cell: gf.Component, w_finger: float) -> dict:
    """Read strap / gate-pad / tap positions from a fixed fet cell's metal1."""
    ly = cell.kcl.layout; kc = ly.cell(cell.name); dbu = ly.dbu
    straps, pads, taps = [], [], []
    for sh in kc.shapes(ly.layer(34, 0)).each():
        b = sh.bbox(); x0, y0, x1, y1 = b.left * dbu, b.bottom * dbu, b.right * dbu, b.top * dbu
        W, H = x1 - x0, y1 - y0; cx = (x0 + x1) / 2
        if abs(W - 0.34) < 1e-3 and abs(H - 0.5) < 1e-3:
            pads.append((cx, y0, y1))
        elif W < 0.5 and abs(H - 2 * (w_finger / 2 - 0.01)) < 0.03:
            straps.append(cx)
        elif W < 0.5 and H > w_finger:
            taps.append(cx)
    straps.sort(); taps.sort()
    top_pads = [p for p in pads if p[1] > 0]
    return dict(straps=straps, taps=taps, hw=w_finger / 2,
                pad_y0=min(p[1] for p in top_pads), pad_y1=max(p[2] for p in top_pads),
                pad_x=[p[0] for p in top_pads],
                tap_half=max(abs(y) for y in [w_finger / 2 + 0.415]))

def route_fet(c, g, yoff, net_gate, label):
    """Route one fet placed with its centre at y=yoff. Returns (y_a, y_b)."""
    xs = g["straps"]; hw = g["hw"]
    _rect(c, M1, min(g["pad_x"]) - 0.17, yoff + g["pad_y1"] - 0.25, max(g["pad_x"]) + 0.17, yoff + g["pad_y1"])
    label(net_gate, (0, yoff + g["pad_y1"] - 0.12), M1_PIN)
    odd = xs[1::2]; even = xs[0::2]
    for x in odd:
        _via(c, M1, V1, M2, x, yoff)
    _rect(c, M2, min(odd) - 0.19, yoff - M2_W / 2, max(odd) + 0.19, yoff + M2_W / 2)
    y_a = yoff - hw - 0.55
    for x in even:
        _rect(c, M1, x - 0.115, y_a - 0.19, x + 0.115, yoff - hw + 0.05)
        _via(c, M1, V1, M2, x, y_a)
    _rect(c, M2, min(even) - 0.19, y_a - M2_W / 2, max(even) + 0.19, y_a + M2_W / 2)
    return y_a, yoff

@gf.cell
def tg_switch(w_n: float = 1.0, w_p: float = 2.0, nf: int = 5, l_gate: float = 0.28,
              labels: bool = True, names=("a", "b", "gn", "gp", "vdd", "vss")) -> gf.Component:
    c = gf.Component()
    na, nb, ngn, ngp, nvdd, nvss = names
    def label(name, pos, layer):
        if labels: c.add_label(name, position=pos, layer=layer)
    ncell = nfet_fixed(w_gate=w_n, l_gate=l_gate, nf=nf, gate_side="top")
    pcell = pfet_fixed(w_gate=w_p, l_gate=l_gate, nf=nf, gate_side="top")
    gn_, gp_ = fet_geom(ncell, w_n), fet_geom(pcell, w_p)
    n = c << ncell; p = c << pcell
    py = -(ncell.dbbox().height() / 2 + pcell.dbbox().height() / 2 + 2.2)
    p.dmovey(py)
    y_a_n, y_b_n = route_fet(c, gn_, 0.0, ngn, label)
    y_a_p, y_b_p = route_fet(c, gp_, py, ngp, label)
    tap_x = max(gn_["taps"] + gp_["taps"])
    xl, xr = -(tap_x + 0.65), (tap_x + 0.65)
    # a: left vertical join; b: right vertical join
    _rect(c, M2, xl - M2_W / 2, y_a_p - M2_W / 2, xl + M2_W / 2, y_a_n + M2_W / 2)
    for y, g in ((y_a_n, gn_), (y_a_p, gp_)):
        _rect(c, M2, xl - M2_W / 2, y - M2_W / 2, min(g["straps"]) + 0.19, y + M2_W / 2)
    label(na, (xl, (y_a_n + y_a_p) / 2), M2_PIN)
    _rect(c, M2, xr - M2_W / 2, y_b_p - M2_W / 2, xr + M2_W / 2, y_b_n + M2_W / 2)
    for y, g in ((y_b_n, gn_), (y_b_p, gp_)):
        _rect(c, M2, max(g["straps"][1::2]) - 0.19, y - M2_W / 2, xr + M2_W / 2, y + M2_W / 2)
    label(nb, (xr, (y_b_n + y_b_p) / 2), M2_PIN)
    # tap bars
    def tap_bar(yoff, g, y_bar, net):
        for x in g["taps"]:
            _rect(c, M1, x - 0.115, y_bar - 0.19, x + 0.115, yoff - g["tap_half"] + 0.05)
            _via(c, M1, V1, M2, x, y_bar)
        _rect(c, M2, min(g["taps"]) - 0.19, y_bar - M2_W / 2, max(g["taps"]) + 0.19, y_bar + M2_W / 2)
        label(net, (0, y_bar), M2_PIN)
        return y_bar
    y_vss = tap_bar(0.0, gn_, y_a_n - 0.75, nvss)
    y_vdd = tap_bar(py, gp_, y_a_p - 0.75, nvdd)
    c.info.update(dict(xl=xl, xr=xr, py=py, y_a_n=y_a_n, y_a_p=y_a_p, y_b_n=y_b_n, y_b_p=y_b_p,
                       y_vss=y_vss, y_vdd=y_vdd, y_gn=gn_["pad_y1"] - 0.12, y_gp=py + gp_["pad_y1"] - 0.12,
                       w_n_total=w_n * nf, w_p_total=w_p * nf, nf=nf))
    return c

if __name__ == "__main__":
    t = tg_switch()
    top = gf.Component(name="tg_switch"); top << t; top.flatten(); top.write_gds("work/tg_switch.gds")
    b = t.dbbox(); print(f"wrote work/tg_switch.gds; {b.width():.1f} x {b.height():.1f} um; info {dict(t.info)}")
