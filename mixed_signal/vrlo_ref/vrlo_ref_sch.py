"""Write the xschem drawing of vrlo_ref from vrlo_ref.spice (sizes are read from
the netlist, so the drawing cannot drift from it):

  vrlo_ref.sch / .sym   the 5/33 AVDD divider (28 + 5 ppolyf_u_3k units, drawn
                        as a snake of columns) and its tap capacitor on the
                        left; the bias mirror; the PMOS-input OTA with its
                        g-node diode XM5; the shunt XMS, the keep-alive XMK and
                        the decap XCD on the right at the vrlo output

schematic.sh netlists it headless and compares it with vrlo_ref.spice instance
by instance (check-schematic.awk). The Sheet class is midrail_ref_v2's
(midref_v2_sch.py), with a rotation argument on res().

    ./container.sh 'python3 vrlo_ref_sch.py'
"""
import os
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
FMT = 'format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"'
PIN = {
    "pfet": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "nfet": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "res": {"M": (0, 30), "P": (0, -30), "B": (-20, 0)},
    "mim": {"B": (0, 30), "G": (0, -30)},
}
PORTS = ["vrlo", "ib", "avdd", "avss"]


def subckts(path):
    out, cur = {}, None
    for ln in open(path):
        t = ln.split()
        if not t or t[0].startswith("*"):
            continue
        if t[0].lower() == ".subckt":
            cur = t[1]
            out[cur] = dict(ports=t[2:], dev={})
        elif t[0].lower().startswith(".ends"):
            cur = None
        elif cur:
            kv = dict(x.split("=", 1) for x in t if "=" in x)
            nodes = [x for x in t[1:] if "=" not in x]
            out[cur]["dev"][t[0]] = dict(nodes=nodes[:-1], model=nodes[-1], **kv)
    return out


class Sheet:
    def __init__(self):
        self.inst, self.points, self.wires, self.nl = [], [], [], 0

    def pin(self, kind, x, y, rot, flip, name):
        px, py = PIN[kind][name]
        if flip:
            px = -px
        for _ in range(rot):
            px, py = -py, px
        return (x + px, y + py)

    def mos(self, d, name, x, y, flip=0):
        kind = "pfet" if d["model"].startswith("pfet") else "nfet"
        self.inst.append(f"C {{symbols/{d['model']}.sym}} {x} {y} 0 {flip} {{name={name}\nL={d['L']}\nW={d['W']}\n"
                         f"nf={d['nf']}\nm={d['m']}\nmodel={d['model']}\nspiceprefix=\"\"\n{FMT}}}")
        p = {k: self.pin(kind, x, y, 0, flip, k) for k in "DGSB"}
        self.points += list(p.values())
        return p

    def res(self, d, name, x, y, rot=2):
        """rot 2: first terminal (M) on top; rot 0: first terminal at the bottom."""
        self.inst.append(f"C {{symbols/ppolyf_u_3k.sym}} {x} {y} {rot} 0 {{name={name}\nW={d['r_width']}\n"
                         f"L={d['r_length']}\nmodel=ppolyf_u_3k\nspiceprefix=\"\"\nm=1}}")
        p = {k: self.pin("res", x, y, rot, 0, k) for k in "MPB"}
        self.points += list(p.values())
        return p

    def mim(self, d, name, x, y, rot=0):
        self.inst.append(f"C {{symbols/cap_mim_2f0fF.sym}} {x} {y} {rot} 0 {{name={name} W={d['c_width']} "
                         f"L={d['c_length']} model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1}}")
        p = {k: self.pin("mim", x, y, rot, 0, k) for k in "BG"}
        self.points += list(p.values())
        return p

    def lab(self, x, y, net, right=False, sym="lab_pin"):
        self.nl += 1
        self.inst.append(f"C {{devices/{sym}.sym}} {x} {y} 0 {1 if right else 0} "
                         f"{{name=l{self.nl} sig_type=std_logic lab={net}}}")
        self.points.append((x, y))

    def port(self, sym, x, y, net, num, flip=0):
        self.inst.append(f"C {{devices/{sym}.sym}} {x} {y} 0 {flip} {{name=p{net} lab={net} sim_pinnumber={num}}}")
        self.points.append((x, y))

    def wire(self, net, *pts):
        self.wires.append((list(pts), net))
        self.points += [pts[0], pts[-1]]

    def body(self, p, net, left=False):
        x, y = p
        e = (x - 40, y) if left else (x + 40, y)
        self.wire(net, p, e)
        self.lab(*e, net, right=not left)

    def stub(self, p, net, dx=-40):
        """a short wire from a pin to a lab_pin (connection by name)."""
        x, y = p
        self.wire(net, p, (x + dx, y))
        self.lab(x + dx, y, net, right=dx > 0)

    def text(self, t):
        self.inst_text = getattr(self, "inst_text", []) + [t]

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
        tl = ('C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/vrlo_ref - '
              + title + '"}')
        open(path, "w", newline="\n").write(head + "\n".join(getattr(self, "inst_text", [])) + "\n"
                                            + "\n".join(out) + "\n" + "\n".join(self.inst) + "\n" + tl + "\n")


def divider(s, dv):
    """28 top units in four columns of seven (down, up, down, up), the tap at the
    top of column 3, the five bottom units down column 4 to avss."""
    VDD, VSS = -900, -40
    X0, DXC, YT = 100, 120, -840          # column pitch; first resistor centre
    chain = [f"XR{k}" for k in range(1, 34)]
    cols = [chain[0:7], chain[7:14], chain[14:21], chain[21:28], chain[28:33]]
    ends = {}
    for c, units in enumerate(cols):
        x = X0 + c * DXC
        down = c % 2 == 0 or c == 4
        for j, name in enumerate(units):
            y = YT + 60 * j if down else YT + 60 * (6 - j)
            p = s.res(dv[name], name, x, y, rot=2 if down else 0)
            s.body(p["B"], "avss", left=not down)
            # every node between units carries its own label (frozen node set)
            node = dv[name]["nodes"][1]
            if node not in ("tap", "avss"):
                s.lab(*p["P"], node, sym="lab_wire")
            if j == 0:
                ends[(c, "first")] = p["M"]
            ends[(c, "last")] = p["P"]
    x = [X0 + c * DXC for c in range(5)]
    s.wire("avdd", ends[(0, "first")], (x[0], VDD))
    s.wire(dv["XR7"]["nodes"][1], ends[(0, "last")], ends[(1, "first")])        # bottom jog 0 -> 1
    s.wire(dv["XR14"]["nodes"][1], ends[(1, "last")], ends[(2, "first")])       # top jog 1 -> 2
    s.wire(dv["XR21"]["nodes"][1], ends[(2, "last")], ends[(3, "first")])       # bottom jog 2 -> 3
    s.wire("tap", ends[(3, "last")], ends[(4, "first")])                        # top jog 3 -> 4: the tap
    s.wire("avss", ends[(4, "last")], (x[4], VSS))
    # tap capacitor right of column 4, the tap carried on by label
    ct = s.mim(dv["XCT"], "XCT", x[4] + 120, -700)
    s.wire("tap", (x[4], ends[(4, "first")][1]), (x[4] + 120, ends[(4, "first")][1]), ct["G"])
    s.wire("avss", ct["B"], (x[4] + 120, VSS))
    s.lab(x[4] + 120, ends[(4, "first")][1], "tap", sym="lab_wire")
    s.text("T {DIVIDER 28 : 5 units (tap = 5/33 AVDD)} 80 -1000 0 0 0.4 0.4 {}")
    return x[4] + 120


def regulator(s, dv):
    VDD, VSS = -900, -40
    # bias: ideal current into the NMOS diode XMBN -> XMBN2 -> PMOS diode XMBP
    BX = 880
    s.port("ipin", BX - 140, -450, "ib", 2)
    mbn = s.mos(dv["XMBN"], "XMBN", BX, -140, flip=1)
    mbn2 = s.mos(dv["XMBN2"], "XMBN2", BX + 180, -140)
    mbp = s.mos(dv["XMBP"], "XMBP", BX + 180, -760)
    s.wire("ib", (BX - 140, -450), (BX - 20, -450))
    s.wire("ib", (BX - 20, -450), mbn["D"])
    s.wire("ib", (BX - 20, -220), (BX + 60, -220), (BX + 60, -140))
    s.wire("ib", mbn["G"], mbn2["G"])
    s.wire("avss", mbn["S"], (BX - 20, VSS))
    s.wire("avss", mbn2["S"], (BX + 200, VSS))
    s.wire("pb", mbp["D"], mbn2["D"])
    s.wire("pb", mbp["G"], (BX + 120, -760), (BX + 120, -700), (BX + 200, -700))
    s.wire("avdd", mbp["S"], (BX + 200, VDD))
    s.body(mbn["B"], "avss", left=True)
    s.body(mbn2["B"], "avss")
    s.body(mbp["B"], "avdd")
    s.lab(BX + 200, -450, "pb", sym="lab_wire")
    # OTA: XM2 (gate tap) left, XM1 (gate vrlo) right; tail XMT above
    A, B = 1360, 1560
    mt = s.mos(dv["XMT"], "XMT", (A + B) // 2 - 20 + 20 - 20, -760)
    m2 = s.mos(dv["XM2"], "XM2", A - 20, -600)
    m1 = s.mos(dv["XM1"], "XM1", B + 20, -600, flip=1)
    m4 = s.mos(dv["XM4"], "XM4", A - 20, -300)
    m3 = s.mos(dv["XM3"], "XM3", B + 20, -300, flip=1)
    m5 = s.mos(dv["XM5"], "XM5", A - 200, -300)
    xt = mt["D"][0]
    s.wire("ts", mt["D"], (xt, -680))
    s.wire("ts", (A, -680), (B, -680))
    s.wire("ts", (A, -680), m2["S"])
    s.wire("ts", (B, -680), m1["S"])
    s.wire("avdd", mt["S"], (xt, VDD))
    s.stub(mt["G"], "pb")
    s.stub(m2["G"], "tap")
    s.stub(m1["G"], "vrlo", dx=40)
    s.wire("g", m2["D"], m4["D"])
    s.wire("d1", m1["D"], m3["D"])
    # XM3 diode, the mirror gate line under the sources
    s.wire("d1", m3["G"], (B + 40, -380), (B, -380))
    s.wire("d1", m4["G"], (A - 40, -230), (B + 80, -230), (B + 80, -300), m3["G"])
    # XM5: diode at g
    x5 = m5["D"][0]
    s.wire("g", (A, -450), (x5, -450), m5["D"])
    s.wire("g", m5["G"], (x5 - 40, -380), (x5, -380))
    for d in (m4, m3, m5):
        s.wire("avss", d["S"], (d["S"][0], VSS))
    s.body(m2["B"], "avdd")
    s.body(m1["B"], "avdd", left=True)
    s.body(mt["B"], "avdd")
    s.body(m4["B"], "avss")
    s.body(m3["B"], "avss", left=True)
    s.body(m5["B"], "avss")
    for x, y, net in ((A, -450, "g"), (B, -450, "d1"), (xt, -700, "ts")):
        s.lab(x, y, net, sym="lab_wire")
    # shunt, keep-alive, decap, output
    C = 1840
    ms = s.mos(dv["XMS"], "XMS", C - 20, -300)
    mk = s.mos(dv["XMK"], "XMK", C - 20, -760)
    s.wire("vrlo", mk["D"], ms["D"])
    s.wire("avdd", mk["S"], (C, VDD))
    s.wire("avss", ms["S"], (C, VSS))
    s.stub(mk["G"], "pb")
    s.stub(ms["G"], "g")
    s.body(ms["B"], "avss")
    s.body(mk["B"], "avdd")
    cd = s.mim(dv["XCD"], "XCD", C + 160, -300)
    s.wire("vrlo", (C, -500), (C + 260, -500))
    s.wire("vrlo", (C + 160, -500), cd["G"])
    s.wire("avss", cd["B"], (C + 160, VSS))
    s.port("opin", C + 260, -500, "vrlo", 1)
    s.lab(C, -500, "vrlo", sym="lab_wire")
    s.text("T {BIAS} 760 -1000 0 0 0.4 0.4 {}")
    s.text("T {ib -> XMBN -> XMBN2 -> XMBP (pb)} 760 -970 0 0 0.25 0.25 {}")
    s.text("T {OTA (PMOS input, g-node diode XM5)} 1120 -1000 0 0 0.4 0.4 {}")
    s.text("T {SHUNT + KEEP-ALIVE + DECAP} 1760 -1000 0 0 0.4 0.4 {}")
    return C + 260


def sheet(dv):
    s = Sheet()
    VDD, VSS = -900, -40
    s.port("iopin", 40, VDD, "avdd", 3, 1)
    s.port("iopin", 40, VSS, "avss", 4, 1)
    xd = divider(s, dv)
    xr = regulator(s, dv)
    s.wire("avdd", (40, VDD), (xr - 260 + 0, VDD))
    s.wire("avss", (40, VSS), (xr - 100, VSS))
    s.text("T {VRLO_REF  -  0.5 V SHUNT REGULATOR FOR THE RAMP RESET (vrlo_ref)} 40 -1200 0 0 0.6 0.6 {}")
    s.text("T {tap = 5/33 AVDD (28 : 5 identical ppolyf_u_3k units). The OTA compares vrlo (XM1) with the tap (XM2); "
           "its output g (resistance ~1/gm of the diode XM5)\ndrives the shunt XMS, which mirrors XM5. vrlo up -> "
           "XM1 off -> g up -> XMS sinks more. XMK (keep-alive) sources a fixed current from avdd, the decap XCD\n"
           "is the loop's dominant pole. Bias: an ideal current into ib. Netlist: vrlo_ref.spice (GENERATED by "
           "size_vrlo.py; this drawing by vrlo_ref_sch.py).} 40 -1140 0 0 0.3 0.3 {}")
    return s


def write_sym():
    desc = "0.5 V shunt regulator for ramp_simple's reset (subckt vrlo_ref of vrlo_ref.spice)"
    pos = {"vrlo": (80, 0, "out"), "ib": (-80, 0, "in"), "avdd": (0, -60, "inout"), "avss": (0, 60, "inout")}
    L = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
         f'K {{type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=X1"\ndescription="{desc}"\n}}',
         "V {}", "S {}", "E {}",
         "L 4 -60 -40 60 -40 {}", "L 4 60 -40 60 40 {}", "L 4 60 40 -60 40 {}", "L 4 -60 40 -60 -40 {}"]
    for p in PORTS:
        x, y, d = pos[p]
        if abs(x) == 80:
            L.append(f"L 4 {x} {y} {60 if x > 0 else -60} {y} {{}}")
        else:
            L.append(f"L 4 {x} {y} {x} {40 if y > 0 else -40} {{}}")
        L.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={p} dir={d}}}")
        tx = x - 55 if x < 0 else (x - 75 if x > 0 else x + 4)
        ty = y - 16 if abs(x) == 80 else (y + 4 if y < 0 else y - 16)
        L.append(f"T {{{p}}} {tx} {ty} 0 0 0.15 0.15 {{layer=7}}")
    L += ["T {@name} -58 -58 0 0 0.25 0.25 {}", "T {vrlo_ref} -58 24 0 0 0.2 0.2 {layer=13}"]
    open(os.path.join(BLOCK, "vrlo_ref.sym"), "w", newline="\n").write("\n".join(L) + "\n")


def main():
    net = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BLOCK, "vrlo_ref.spice")
    sc = subckts(net)["vrlo_ref"]
    assert sc["ports"] == PORTS, sc["ports"]
    sheet(sc["dev"]).write(os.path.join(BLOCK, "vrlo_ref.sch"), "vrlo_ref")
    write_sym()
    print("REPORT: wrote vrlo_ref.sch/.sym from " + os.path.basename(net))


if __name__ == "__main__":
    main()
