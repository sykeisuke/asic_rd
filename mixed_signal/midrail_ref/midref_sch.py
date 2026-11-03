"""Write the xschem drawings of midref from midref.spice (sizes are read
from the netlist, so the drawing cannot drift from it):

  midref_buf.sch / .sym   the FVF class-AB buffer, drawn as the textbook
                          figure: vdd on top, vss below, vin in on the left,
                          out on the right, the IB sources on the follower
                          drains, the two FVF shunt loops as the only crossings
  midref_div.sch / .sym   the VDD/2 divider and its tap capacitor

The text (title, section headings, per-device Id, R and C values) is read
from data/op_devices.csv / op_passives.csv (verify_v3.py phase opdev) and
changes no instance, wire or label.

schematic.sh netlists both headless and compares them with the subcircuits of
midref.spice instance by instance (check-schematic.awk).

    ./container.sh 'python3 midref_sch.py'
"""
import os
import re
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
FMT = 'format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"'
PIN = {
    "pfet": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "nfet": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "res": {"M": (0, 30), "P": (0, -30), "B": (-20, 0)},
    "mim": {"B": (0, 30), "G": (0, -30)},
}


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

    def res(self, d, name, x, y):
        self.inst.append(f"C {{symbols/ppolyf_u_3k.sym}} {x} {y} 2 0 {{name={name}\nW={d['r_width']}\n"
                         f"L={d['r_length']}\nmodel=ppolyf_u_3k\nspiceprefix=\"\"\nm=1}}")
        p = {k: self.pin("res", x, y, 2, 0, k) for k in "MPB"}
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

    def text(self, t):
        self.inst_text = getattr(self, "inst_text", []) + [t]

    def write(self, path, title, order=None):
        if order:
            # device instances in the deck's order: the hierarchical netlist of a testbench
            # drawing then expands the PDK's mismatch draws (.options seed) device for device
            # as the deck does, so one draw is the same sample in both (xtb.py, tb_mc)
            dev = {re.search(r"name=(\S+)", t).group(1): t for t in self.inst if t.startswith("C {symbols/")}
            rest = [t for t in self.inst if not t.startswith("C {symbols/")]
            self.inst = rest + [dev[n] for n in order if n in dev] + [t for n, t in dev.items() if n not in order]
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
        tl = ('C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/midrail_ref - '
              + title + '"}')
        open(path, "w", newline="\n").write(head + "\n".join(getattr(self, "inst_text", [])) + "\n"
                                            + "\n".join(out) + "\n" + "\n".join(self.inst) + "\n" + tl + "\n")



# ---------------------------------------------------------------- annotation
# The sheets carry a title, section headings, labels, the device currents and the
# R / C values only (CLAUDE.md, "Schematic drawings"); descriptions and the
# operating-point table live in README.md and data/op_devices.csv. The numbers come from
#   data/op_devices.csv, data/op_passives.csv   verify_v3.py phase opdev (ngspice,
#       one midref2 at typical / 27 C / 3.3 V, the ideal i_f into ib, PDK-model
#       replicas of the divider resistors and the MIM capacitors)
# A missing record prints "not recorded" instead of a number. Text only: no
# instance, wire or label depends on anything below.
TXT_TITLE = 0.6           # title hsize / vsize
TXT_TAG = 0.36            # values next to devices
TAG = "{layer=4}"         # device values: the symbol colour, distinct from the white prose


def records():
    """{dev: row} from data/op_devices.csv and {name: row} from data/op_passives.csv, or {} when absent."""
    out = []
    for f in ("op_devices.csv", "op_passives.csv"):
        path = os.path.join(BLOCK, "data", f)
        rows = {}
        if os.path.exists(path):
            lines = [ln.strip().split(",") for ln in open(path) if ln.strip()]
            keys = lines[0]
            for v in lines[1:]:
                rows[v[0].lower()] = dict(zip(keys, v))
        out.append(rows)
    return out


def num(rows, key, col, scale=1.0, fmt="%.3g"):
    r = rows.get(key.lower())
    if not r or col not in r or r[col] == "":
        return None
    return fmt % (float(r[col]) * scale)


def say(x, unit=""):
    return "not recorded" if x is None else f"{x}{unit}"


def tag(s, x, y, lines, size=TXT_TAG, prop=TAG):
    s.text("T {" + "\n".join(lines) + f"}} {x} {y} 0 0 {size} {size} {prop}")


def annotate_buf(s, dv):
    D, P = records()
    s.text(f"T {{MIDREF_BUF  -  FVF class-AB VDD/2 buffer (out = vref = vbl)}} 40 -1100 0 0 "
           f"{TXT_TITLE} {TXT_TITLE} {{}}")
    for dev, x, y in (("xmbn", 172, -400), ("xmbn2", 392, -112), ("xmbp", 392, -722), ("xm1", 752, -800),
                      ("xmib", 752, -532), ("xmit", 752, -312), ("xm4", 752, -205), ("xm3", 1300, -805),
                      ("xm2", 1300, -705), ("xm5", 1300, -240), ("xm6", 1300, -150)):
        tag(s, x, y, [say(num(D, dev, "id", 1e6, "%.2f"), " uA")])
    tag(s, 1275, -298, [f"C = {say(num(P, 'xcd', 'value', 1e15, '%.1f'), ' fF')}"])


def annotate_div(s, dv):
    D, P = records()
    s.text(f"T {{MIDREF_DIV  -  VDD/2 divider}} 40 -900 0 0 {TXT_TITLE} {TXT_TITLE} {{}}")
    s.text(f"T {{layout: XRT / XRB identical, ratio set by matching}} 40 -840 0 0 {TXT_TAG} {TXT_TAG} {{}}")
    for name, x, y in (("XRT", 215, -598), ("XRB", 60, -205)):
        tag(s, x, y, [f"{say(num(P, name, 'value', 1e-3, '%.1f'), ' kOhm')}"])
    if "XCT" in dv:
        tag(s, 335, -282, [f"C = {say(num(P, 'xct', 'value', 1e15, '%.1f'), ' fF')}"])


def buf_sheet(dv):
    s = Sheet()
    VDD, VSS = -860, -40
    s.port("iopin", 60, VDD, "vdd", 4, 1)
    s.port("iopin", 60, VSS, "vss", 5, 1)
    s.port("ipin", 40, -450, "ib", 3)
    s.port("ipin", 40, -560, "vin", 2)
    s.port("opin", 1320, -450, "out", 1)
    # bias: ideal current into the NMOS diode XMBN -> XMBN2 -> PMOS diode XMBP
    mbn = s.mos(dv["XMBN"], "XMBN", 180, -140, flip=1)
    mbn2 = s.mos(dv["XMBN2"], "XMBN2", 360, -140)
    mbp = s.mos(dv["XMBP"], "XMBP", 360, -760)
    s.wire("ib", (40, -450), (160, -450))
    s.wire("ib", (160, -450), mbn["D"])
    s.wire("ib", (160, -220), (240, -220), (240, -140))
    s.wire("ib", mbn["G"], mbn2["G"])
    s.wire("vss", mbn["S"], (160, VSS))
    s.wire("vss", mbn2["S"], (380, VSS))
    s.wire("pb", mbp["D"], mbn2["D"])
    s.wire("pb", mbp["G"], (300, -760), (300, -700), (380, -700))
    s.wire("vdd", mbp["S"], (380, VDD))
    s.body(mbn["B"], "vss", left=True)
    s.body(mbn2["B"], "vss")
    s.body(mbp["B"], "vdd")
    s.lab(380, -450, "pb", sym="lab_wire")
    # vin enters from the left to the two follower gates
    XI, XM, XR = 900, 1040, 1160
    m1 = s.mos(dv["XM1"], "XM1", XI - 20, -670)
    mib = s.mos(dv["XMIB"], "XMIB", XI - 20, -570)
    mit = s.mos(dv["XMIT"], "XMIT", XI - 20, -330)
    m4 = s.mos(dv["XM4"], "XM4", XI - 20, -230)
    m3 = s.mos(dv["XM3"], "XM3", XR - 20, -760)
    m2 = s.mos(dv["XM2"], "XM2", XR - 20, -670)
    m5 = s.mos(dv["XM5"], "XM5", XR - 20, -230)
    m6 = s.mos(dv["XM6"], "XM6", XR - 20, -140)
    s.wire("vin", (40, -560), (740, -560))
    s.wire("vin", (740, -670), (740, -230))
    s.wire("vin", (740, -670), m1["G"])
    s.wire("vin", (740, -230), m4["G"])
    s.wire("b", m1["D"], mib["D"])
    s.wire("vss", mib["S"], (XI, -520))
    s.lab(XI, -520, "vss")
    s.wire("a", mit["D"], m4["D"])
    s.wire("vdd", mit["S"], (XI, -380))
    s.lab(XI, -380, "vdd", right=True)
    s.wire("ib", mib["G"], (820, -570))
    s.lab(820, -570, "ib")
    s.wire("pb", mit["G"], (820, -330))
    s.lab(820, -330, "pb")
    s.wire("b", (XI, -620), (XM, -620), (XM, -760), m3["G"])
    s.wire("a", (XI, -280), (XM, -280), (XM, -140), m6["G"])
    s.wire("p", m1["S"], (XR, -700))
    s.wire("p", m3["D"], m2["S"])
    s.wire("n", m4["S"], (XR, -200))
    s.wire("n", m5["S"], m6["D"])
    s.wire("vdd", m3["S"], (XR, VDD))
    s.wire("vss", m6["S"], (XR, VSS))
    s.wire("out", m2["D"], m5["D"])
    s.wire("out", (XR, -610), (1090, -610), (1090, -670), m2["G"])
    s.wire("out", (XR, -290), (1090, -290), (1090, -230), m5["G"])
    s.wire("out", (XR, -450), (1320, -450))
    # output capacitor to vss, beside the output
    cd = s.mim(dv["XCD"], "XCD", 1260, -330)             # xschem lists G (top) first: out on G
    s.wire("out", (1260, -450), cd["G"])
    s.wire("vss", cd["B"], (1260, VSS))
    for d, net in ((m1, "vdd"), (mib, "vss"), (mit, "vdd"), (m4, "vss"),
                   (m3, "vdd"), (m2, "vdd"), (m5, "vss"), (m6, "vss")):
        s.body(d["B"], net)
    for x, y, net in ((XI, -620, "b"), (XI, -280, "a"), (XR, -700, "p"), (XR, -200, "n")):
        s.lab(x, y, net, sym="lab_wire")
    s.wire("vdd", (60, VDD), (XR, VDD))
    s.wire("vss", (60, VSS), (1260, VSS))
    annotate_buf(s, dv)
    s.text("T {BIAS} 60 -980 0 0 0.4 0.4 {}")
    s.text("T {INPUT FOLLOWERS + IB} 760 -980 0 0 0.4 0.4 {}")
    s.text("T {SHUNTS + OUTPUT} 1080 -980 0 0 0.4 0.4 {}")
    s.text("T {IB} 790 -605 0 0 0.35 0.35 {layer=8}")
    s.text("T {IB} 790 -365 0 0 0.35 0.35 {layer=8}")
    s.text("L 4 715 -1000 715 20 {dash=6}")
    return s


def div_sheet(dv):
    s = Sheet()
    VDD, VSS = -700, -100
    s.port("iopin", 60, VDD, "vdd", 2, 1)
    s.port("iopin", 60, VSS, "vss", 3, 1)
    s.port("opin", 420, -400, "vin", 1)
    rt = s.res(dv["XRT"], "XRT", 200, -550)
    rb = s.res(dv["XRB"], "XRB", 200, -250)
    s.wire("vdd", rt["M"], (200, VDD))
    s.wire("vin", rt["P"], rb["M"])
    s.wire("vss", rb["P"], (200, VSS))
    s.wire("vin", (200, -400), (420, -400))
    s.body(rt["B"], "vss")
    s.body(rb["B"], "vss")
    xr = 200
    if "XCT" in dv:
        ct = s.mim(dv["XCT"], "XCT", 320, -310)
        s.wire("vin", (320, -400), ct["G"])
        s.wire("vss", ct["B"], (320, VSS))
        xr = 320
    s.wire("vdd", (60, VDD), (200, VDD))
    s.wire("vss", (60, VSS), (xr, VSS))
    annotate_div(s, dv)
    return s


SYM = {
    "midref_buf": ("out vin ib vdd vss", ["out", "vin", "ib", "vdd", "vss"],
                   "FVF class-AB VDD/2 buffer of midrail_ref (subckt midref_buf of midref.spice)"),
    "midref_div": ("vin vdd vss", ["vin", "vdd", "vss"],
                   "VDD/2 divider of midrail_ref (subckt midref_div of midref.spice)"),
}


def write_sym(name):
    """type=subcircuit symbol: a parent schematic netlists the X line and
    descends into <name>.sch."""
    ports, _, desc = SYM[name]
    pins = ports.split()
    pos = {"out": (80, 0, "out"), "vin": (-80, 0, "in") if name == "midref_buf" else (80, 0, "out"),
           "ib": (-80, 20, "in"), "vdd": (0, -60, "inout"), "vss": (0, 60, "inout")}
    L = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
         f'K {{type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=X1"\ndescription="{desc}"\n}}',
         "V {}", "S {}", "E {}",
         "L 4 -60 -40 60 -40 {}", "L 4 60 -40 60 40 {}", "L 4 60 40 -60 40 {}", "L 4 -60 40 -60 -40 {}"]
    for p in pins:
        x, y, d = pos[p]
        if abs(x) == 80:
            L.append(f"L 4 {x} {y} {60 if x > 0 else -60} {y} {{}}")
        else:
            L.append(f"L 4 {x} {y} {x} {40 if y > 0 else -40} {{}}")
        L.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={p} dir={d}}}")
        tx = x - 55 if x < 0 else (x - 75 if x > 0 else x + 4)
        ty = y - 16 if abs(x) == 80 else (y + 4 if y < 0 else y - 16)
        L.append(f"T {{{p}}} {tx} {ty} 0 0 0.15 0.15 {{layer=7}}")
    L += ["T {@name} -58 -58 0 0 0.25 0.25 {}", f"T {{{name}}} -58 24 0 0 0.2 0.2 {{layer=13}}"]
    open(os.path.join(BLOCK, name + ".sym"), "w", newline="\n").write("\n".join(L) + "\n")


def main():
    net = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BLOCK, "midref.spice")
    sc = subckts(net)
    for name, (ports, order, _) in SYM.items():
        assert sc[name]["ports"] == order, (name, sc[name]["ports"])
    buf_sheet(sc["midref_buf"]["dev"]).write(os.path.join(BLOCK, "midref_buf.sch"), "midref_buf",
                                             order=list(sc["midref_buf"]["dev"]))
    div_sheet(sc["midref_div"]["dev"]).write(os.path.join(BLOCK, "midref_div.sch"), "midref_div",
                                             order=list(sc["midref_div"]["dev"]))
    for name in SYM:
        write_sym(name)
    print("REPORT: wrote midref_buf.sch/.sym and midref_div.sch/.sym from " + os.path.basename(net))


if __name__ == "__main__":
    main()
