"""Write the transistor-level xschem views of the three unit-cell switches
from ref/switches.spice (sizes and S/D geometry are read from
the deck, so the drawing cannot drift from it):

  sw_s0.sch / .sym   S0 vfe -> top     transmission gate (NMOS + PMOS)
  sw_s1.sch / .sym   S1 vramp -> top   transmission gate (same devices)
  sw_s2.sch / .sym   S2 vref -> bot    single NMOS, ctlb in the port list, unused

v3 (Analog_top): plate names swapped against Analog_top (top = S0/S1 side,
bot = S2 / comparator side), text larger and with each switch's function;
the devices and the netlist are unchanged.

Ports in the deck's order: a b ctl ctlb vdd vss (a = driving side, b = plate
side, ctl HIGH = closed, ctlb its complement).

The PDK MOS symbols' own format adds nrd/nrs/sa/sb/sd, which the deck does not
carry; every instance therefore overrides format= with exactly the deck's
parameter set (L W nf m ad as pd ps), so the netlisted line equals the deck
line. sw_schematic.sh netlists the three drawings headless and compares each
with its deck subcircuit (check-sw.awk). The Sheet helper follows
analog_top_sch.py / ../bias_gen/bias_gen_sch.py.

    ./container.sh 'python3 sw_sch.py'
"""
import os

import symbols
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(BLOCK, "ref", "switches.spice")
PORTS = ["a", "b", "ctl", "ctlb", "vdd", "vss"]
GEO = ("L", "W", "nf", "m", "ad", "as", "pd", "ps")
FMT = 'format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad as=@as pd=@pd ps=@ps"'
PIN = {
    "pfet": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "nfet": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
}
ROLE = {
    "sw_s0": "S0  vfe -> top (top plate), transmission gate",
    "sw_s1": "S1  vramp -> top (top plate), transmission gate",
    "sw_s2": "S2  vref -> bot (bottom plate), single NMOS; ctlb unused",
}
# what each switch does in the conversion (written on its sheet)
FUNC = {
    "sw_s0": "Closed while the cell tracks: the top plate follows the input vfe = vin. Opens TNOV = 5 ns\n"
             "after S2 (the sample is already frozen by S2), isolating the top plate before S1 closes.",
    "sw_s1": "Closes TNOV = 5 ns after S0 opened and stays closed through the conversion: the shared ramp\n"
             "vramp drives the top plate from vrlo = 0.5 V to 2.0 V, lifting the floating bottom plate.",
    "sw_s2": "Closed while the cell tracks: the bottom plate sits at vref = VDD/2. Its falling ctl edge IS the\n"
             "sampling instant (bottom-plate sampling). It always opens at vref, so the charge it injects does not\n"
             "depend on the signal; one NMOS gives one aperture edge.",
}


def subckts(path):
    out, cur = {}, None
    for ln in open(path):
        t = ln.split()
        if not t or t[0].startswith("*"):
            continue
        if t[0].lower() == ".subckt":
            cur = t[1]
            out[cur] = dict(ports=t[2:], dev={}, order=[])
        elif t[0].lower().startswith(".ends"):
            cur = None
        elif cur:
            kv = dict(x.split("=", 1) for x in t if "=" in x)
            nodes = [x for x in t[1:] if "=" not in x]
            out[cur]["dev"][t[0]] = dict(nodes=nodes[:-1], model=nodes[-1], **kv)
            out[cur]["order"].append(t[0])
    return out


def xf(px, py, rot, flip):
    """xschem's ROTATION about the origin: flip first, then rot x 90 deg."""
    if flip:
        px = -px
    for _ in range(rot):
        px, py = -py, px
    return px, py


class Sheet:
    def __init__(self):
        self.inst, self.points, self.wires, self.texts, self.nl = [], [], [], [], 0

    def mos(self, name, d, x, y, rot, flip):
        kind = "pfet" if d["model"].startswith("pfet") else "nfet"
        extra = set(d) - set(GEO) - {"nodes", "model"}
        assert not extra, f"{name}: deck parameters not drawn: {extra}"
        par = "\n".join(f"{k}={d[k]}" for k in GEO)
        self.inst.append(f"C {{symbols/{d['model']}.sym}} {x} {y} {rot} {flip} {{name={name}\n{par}\n"
                         f"model={d['model']}\nspiceprefix=\"\"\nhide_texts=true\n{FMT}}}")
        p = {}
        for k, (px, py) in PIN[kind].items():
            qx, qy = xf(px, py, rot, flip)
            p[k] = (x + qx, y + qy)
        self.points += list(p.values())
        # the symbol's pin order is D G S B; the deck's terminals are d g s b
        return dict(zip("DGSB", d["nodes"])), p

    def lab(self, x, y, net, flip=0, rot=0):
        self.nl += 1
        self.inst.append(f"C {{devices/lab_pin.sym}} {x} {y} {rot} {flip} "
                         f"{{name=l{self.nl} sig_type=std_logic lab={net}}}")
        self.points.append((x, y))

    def port(self, sym, x, y, net, flip=0):
        num = PORTS.index(net) + 1
        self.inst.append(f"C {{devices/{sym}.sym}} {x} {y} 0 {flip} "
                         f"{{name=p{net} lab={net} sim_pinnumber={num}}}")
        self.points.append((x, y))

    def wire(self, net, *pts):
        self.wires.append((list(pts), net))
        self.points += [pts[0], pts[-1]]

    def text(self, t):
        self.texts.append(t)

    def write(self, path, title):
        segs = [(a, b, n) for pts, n in self.wires for a, b in zip(pts, pts[1:])]
        pset = set(self.points) | {p for a, b, _ in segs for p in (a, b)}
        out = []
        for (x1, y1), (x2, y2), net in segs:
            assert x1 == x2 or y1 == y2
            if x1 == x2:
                cut = sorted({y1, y2} | {py for px, py in pset if px == x1 and min(y1, y2) < py < max(y1, y2)})
                pts = [(x1, y) for y in cut]
            else:
                cut = sorted({x1, x2} | {px for px, py in pset if py == y1 and min(x1, x2) < px < max(x1, x2)})
                pts = [(x, y1) for x in cut]
            out += [f"N {p[0]} {p[1]} {q[0]} {q[1]} {{lab={net}}}" for p, q in zip(pts, pts[1:])]
        head = "v {xschem version=3.4.8RC file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n"
        tl = ('C {devices/title.sym} 0 460 0 0 {name=l99 author="ASIC R&D - mixed_signal/Analog_top - '
              + title + '"}')
        open(path, "w", newline="\n").write(head + "\n".join(self.texts) + "\n" + "\n".join(out) + "\n"
                                            + "\n".join(self.inst) + "\n" + tl + "\n")


def size(d):
    return f"{d['W'].rstrip('u')}/{d['L'].rstrip('u')}"


def sheet(name, sc):
    """S/D line of the PMOS at y=-H (gate up, ctlb), of the NMOS at y=+H
    (gate down, ctl); a joins the two left terminals, b the two right ones;
    the body ties run into the gap between them. The symbols' own texts are
    hidden (hide_texts): each device is annotated beside its gate instead."""
    s = Sheet()
    dv = sc["dev"]
    XA, XB, XC, H = 280, 520, 400, 120     # a rail, b rail, device centre, half gap
    nm = [k for k in sc["order"] if dv[k]["model"].startswith("nfet")]
    pm = [k for k in sc["order"] if dv[k]["model"].startswith("pfet")]
    assert len(nm) == 1 and len(pm) <= 1, sc["order"]
    ys = [0]
    # NMOS: flip 1, rot 1 -> gate below, S left, D right, bulk on the S/D line
    nets, p = s.mos(nm[0], dv[nm[0]], XC, H + 20, 1, 1)
    assert p["S"][1] == p["D"][1] == p["B"][1] == H and p["S"][0] < p["D"][0]
    left, right = nets["S"], nets["D"]
    s.wire(left, p["S"], (XA, H))
    s.wire(right, p["D"], (XB, H))
    s.wire(nets["B"], p["B"], (XC, H - 60))
    s.lab(XC, H - 60, nets["B"], flip=1)
    s.wire(nets["G"], p["G"], (XC, H + 100), (XC - 80, H + 100))
    s.port("ipin", XC - 80, H + 100, nets["G"])
    ys.append(H)
    if pm:
        # PMOS: flip 1, rot 3 -> gate above, S left, D right
        pn, q = s.mos(pm[0], dv[pm[0]], XC, -H - 20, 3, 1)
        assert q["S"][1] == q["D"][1] == q["B"][1] == -H and q["S"][0] < q["D"][0]
        assert (pn["S"], pn["D"]) == (left, right), "PMOS and NMOS not drawn in parallel"
        s.wire(left, q["S"], (XA, -H))
        s.wire(right, q["D"], (XB, -H))
        s.wire(pn["B"], q["B"], (XC, -H + 60))
        s.lab(XC, -H + 60, pn["B"], flip=1)
        s.wire(pn["G"], q["G"], (XC, -H - 100), (XC - 80, -H - 100))
        s.port("ipin", XC - 80, -H - 100, pn["G"])
        ys.append(-H)
    else:
        # ctlb is a port of the subcircuit with nothing on it
        s.port("ipin", XC - 80, -H - 100, "ctlb")
        s.text(f"T {{ctlb: in the port list for uniformity, not connected\n(one device, one aperture edge)}} "
               f"{XC - 60} {-H - 135} 0 0 0.32 0.32 {{layer=4}}")
    # rails: a on the left, b on the right, ports level with the middle (TG)
    # or with the single device's S/D line
    YP = 0 if pm else H
    if pm:
        s.wire(left, (XA, min(ys)), (XA, max(ys)))
        s.wire(right, (XB, min(ys)), (XB, max(ys)))
    s.wire(left, (XA - 120, YP), (XA, YP))
    s.wire(right, (XB, YP), (XB + 120, YP))
    s.port("iopin", XA - 120, YP, left)
    s.port("iopin", XB + 120, YP, right, flip=1)
    # supplies: ports carrying the body-tie nets by name
    s.port("iopin", 80, H + 180, "vdd")
    s.port("iopin", 80, H + 220, "vss")
    note = "supplies: body ties only" if pm else "vss: body tie only; vdd: in the port list, not connected"
    s.text(f"T {{{note}}} 120 {H + 145} 0 0 0.32 0.32 {{layer=4}}")
    for k in ([nm[0]] + pm):
        d = dv[k]
        y = H + 40 if k in nm else -H - 95
        s.text(f"T {{{k}  {d['model']}  W/L = {size(d)}  nf={d['nf']} m={d['m']}\n"
               f"ad=as={d['ad']}  pd=ps={d['pd']}}} {XC + 20} {y} 0 0 0.35 0.35 {{layer=13}}")
    s.text(f"T {{{name.upper()}  -  {ROLE[name]}}} 80 -640 0 0 0.75 0.75 {{}}")
    s.text(f"T {{{FUNC[name]}}} 80 -560 0 0 0.42 0.42 {{}}")
    s.text("T {a = driving side, b = plate side; ctl HIGH = closed, ctlb its complement (made in atop_cell).\n"
           "S/D at the DRC-minimum contacted geometry (ad = W x 0.44 um, pd = 2 (W + 0.44 um)).\n"
           "Netlist: ref/switches.spice (GENERATED by switches/size_switches.py);\n"
           "this drawing by sw_sch.py, checked by sw_schematic.sh. Ron while closed: analog_top sheet (op table).} "
           "80 -470 0 0 0.36 0.36 {}")
    return s


def write_sym(name, sc):
    """type=subcircuit: a parent netlists 'X.. a b ctl ctlb vdd vss sw_sN' and descends into sw_sN.sch."""
    dv = sc["dev"]
    nm = [k for k in sc["order"] if dv[k]["model"].startswith("nfet")][0]
    pm = [k for k in sc["order"] if dv[k]["model"].startswith("pfet")]
    sizes = f"N {size(dv[nm])}" + (f"  P {size(dv[pm[0]])}" if pm else "")
    # the drawing: symbols.py (TG bow-tie or NMOS switch blade), pins as before
    symbols.switch(name, f"{ROLE[name]}; {sizes} (um); transistor level in {name}.sch, "
                   "from ref/switches.spice", f"X{name[3:].upper()}", bool(pm), sizes)


def main():
    deck = sys.argv[1] if len(sys.argv) > 1 else DECK
    sc = subckts(deck)
    for name in ("sw_s0", "sw_s1", "sw_s2"):
        assert sc[name]["ports"] == PORTS, (name, sc[name]["ports"])
        sheet(name, sc[name]).write(os.path.join(BLOCK, f"{name}.sch"), name)
        write_sym(name, sc[name])
    print("REPORT: wrote sw_s0/1/2.sch/.sym from " + os.path.relpath(deck, BLOCK))


if __name__ == "__main__":
    main()
