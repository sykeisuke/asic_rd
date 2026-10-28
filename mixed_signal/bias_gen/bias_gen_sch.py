"""Write the xschem drawing of bias_gen from bias_gen.spice (sizes are
read from the netlist, so the drawing cannot drift from it):

  bias_gen.sch / .sym   startup on the left, the beta-multiplier core in the
                           middle (PMOS mirror over the NMOS pair, the
                           degeneration resistor strips under XMN2), the
                           comparator / ramp sinks and the midref sources on
                           the right, the MIM decaps beside the core

The text (title, summary box, per-device Id and gm/Id, R and C values, the
operating-point table) is read from data/op_devices.csv / op_passives.csv
(verify_bg.py phase opdev) and changes no instance, wire or label.

schematic.sh netlists it headless and compares it with bias_gen.spice
instance by instance (check-schematic.awk, terminals and every parameter).
The Sheet helper follows ../midrail_ref_bkp/midrail_ref_v2/midref_v2_sch.py.

    ./container.sh 'python3 bias_gen_sch.py'
"""
import os
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
FMT = ('format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"')
PIN = {
    "pfet": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "nfet": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "res": {"M": (0, 30), "P": (0, -30), "B": (-20, 0)},
    "mim": {"B": (0, 30), "G": (0, -30)},
}
PORTS = ["vdd", "vss", "icmp0", "icmp1", "icmp2", "icmp3", "iramp", "ivref", "ivbl"]


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
        self.inst, self.points, self.wires, self.texts, self.nl = [], [], [], [], 0

    def pin(self, kind, x, y, rot, flip, name):
        px, py = PIN[kind][name]
        if flip:
            px = -px
        for _ in range(rot):
            px, py = -py, px
        return (x + px, y + py)

    def mos(self, d, name, x, y, flip=0):
        kind = "pfet" if d["model"].startswith("pfet") else "nfet"
        geo = "".join(f"\n{k}={d[k]}" for k in ("ad", "pd", "as", "ps", "nrd", "nrs"))
        self.inst.append(f"C {{symbols/{d['model']}.sym}} {x} {y} 0 {flip} {{name={name}\nL={d['L']}\nW={d['W']}\n"
                         f"nf={d['nf']}\nm={d['m']}{geo}\nmodel={d['model']}\nspiceprefix=\"\"\n{FMT}}}")
        p = {k: self.pin(kind, x, y, 0, flip, k) for k in "DGSB"}
        self.points += list(p.values())
        return p

    def res(self, d, name, x, y):
        self.inst.append(f"C {{symbols/{d['model']}.sym}} {x} {y} 2 0 {{name={name}\nW={d['r_width']}\n"
                         f"L={d['r_length']}\nmodel={d['model']}\nspiceprefix=\"\"\nm=1}}")
        p = {k: self.pin("res", x, y, 2, 0, k) for k in "MPB"}
        self.points += list(p.values())
        return p

    def mim(self, d, name, x, y):
        self.inst.append(f"C {{symbols/cap_mim_2f0fF.sym}} {x} {y} 0 0 {{name={name} W={d['c_width']} "
                         f"L={d['c_length']} model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1}}")
        p = {k: self.pin("mim", x, y, 0, 0, k) for k in "BG"}
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

    def stub(self, p, net, dx=40, dy=0):
        """A short wire off a pin ending in a net label (right of the pin by default)."""
        e = (p[0] + dx, p[1] + dy)
        self.wire(net, p, e)
        self.lab(*e, net, right=dx > 0)

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
        tl = ('C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/bias_gen - '
              + title + '"}')
        open(path, "w", newline="\n").write(head + "\n".join(self.texts) + "\n" + "\n".join(out) + "\n"
                                            + "\n".join(self.inst) + "\n" + tl + "\n")



# ---------------------------------------------------------------- annotation
# Every number written on the sheet comes from a record of this block:
#   data/op_devices.csv, data/op_passives.csv   verify_bg.py phase opdev (ngspice,
#       typical / 27 C / res_typical / 3.3 V, every consumer diode as load,
#       PDK-model replicas of the resistor strips and the MIM decaps)
# A missing record prints "not recorded" instead of a number. Text only: no
# instance, wire or label depends on anything below.
TXT_TITLE = 0.75          # title hsize / vsize
TXT_BODY = 0.42           # summary box
TXT_TAG = 0.36            # values next to devices and the tables
TAG = "{layer=4}"         # device values: the symbol colour, distinct from the white prose
HEAD = "{layer=8}"


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


def mos_tag(rows, dev):
    """Two lines: Id and gm/Id of one device at the bench bias."""
    i = num(rows, dev, "id", 1e6, "%.3f")
    g = num(rows, dev, "gmid", 1.0, "%.1f")
    return [f"Id {say(i, ' uA')}", f"gm/Id {say(g, ' /V')}"]


def amp(rows, dev):
    """Id with a unit that shows it: uA, nA or pA."""
    v = num(rows, dev, "id", 1.0, "%.6g")
    if v is None:
        return "not recorded"
    a = float(v)
    if a >= 1e-8:
        return "%.3f uA" % (a * 1e6)
    if a >= 1e-11:
        return "%.2f nA" % (a * 1e9)
    return "%.3f pA" % (a * 1e12)


def mim_formula(d):
    """C from the PDK model card's own constants (sm141064_mim.ngspice: c_cox 1.99e-3 F/m2,
    c_capsw 2.383e-10 F/m) at the drawn W x L, in fF: the cross-check of the ngspice value."""
    w = float(d["c_width"].rstrip("u"))
    l = float(d["c_length"].rstrip("u"))
    return w * l * 1.99 + 2 * (w + l) * 0.2383, w * l, 2 * (w + l)


def annotate(s, dv):
    D, P = records()
    rec = "verify_bg.py opdev -> data/op_devices.csv, op_passives.csv"
    # ------------------------------------------------ title + summary box
    s.text(f"T {{BIAS_GEN_V2  -  CONSTANT-GM BETA-MULTIPLIER BIAS GENERATOR, CURRENT OUTPUTS (8-bit ADC)}} "
           f"40 -1700 0 0 {TXT_TITLE} {TXT_TITLE} {{}}")
    ic = say(num(P, "i_icmp", "value", 1e6, "%.3f"), " uA")
    ir = say(num(P, "i_iramp", "value", 1e6, "%.3f"), " uA")
    iv = say(num(P, "i_ivref", "value", 1e6, "%.2f"), " uA")
    isup = say(num(P, "i_vdd", "value", 1e6, "%.1f"), " uA")
    rstr = say(num(P, "xr_string", "value", 1e-3, "%.2f"), " kOhm")
    body = [
        "WHAT  Reference current for the 8-bit bottom-plate ADC. An NMOS-defined beta multiplier sets one core current;",
        "      mirrors hand it out as CURRENTS (no shared bias voltage leaves the block).",
        f"PINS  vdd / vss: 3.3 V analog supply (AVDD); {isup} from vdd at the bench, incl. the two midref currents.",
        f"      icmp0..3: SINK {ic} each, into each comparator's own pbias diode (1.68 x its 1.931 uA bench current).",
        f"      iramp: SINK {ir} into the ramp's pbias diode (nominal 3.1314 uA).",
        f"      ivref, ivbl: SOURCE {iv} each, into midref_buf ib (0.90 x its 12.36 uA bench current).",
        f"CORE  XMN1 diode + XMN2 (K = 8 x XMN1) degenerated by R = 5 ppolyf_u strips ({rstr}), 1:1 PMOS mirror XMP1 / XMP2;",
        "      moderate / weak inversion, so the current goes as about T / R.",
        "CHOICES  every MOS L 0.9 um, finger W 4 um; one PMOS row over one NMOS row, even finger counts, common centroid;",
        "      ppolyf_u for its flat TC; untrimmed: the comparator current meets comparator's requirement x (1 + 3 sigma)",
        "      at all 135 PVT cells; startup bleeder XSB1..4 + kick XSU5, released by XSU4; 1 pF MIM decaps on pb and nb.",
        "DECISION  ADR 0017.   REPRODUCE  ./scripts/sim.sh bias-gen  (make bias-gen)",
        "NETLIST  bias_gen.spice, GENERATED by size_bg.py; this drawing by bias_gen_sch.py.",
    ]
    s.text("T {" + "\n".join(body) + f"}} 60 -1600 0 0 {TXT_BODY} {TXT_BODY} {{}}")
    note = [
        "VALUES ON THIS SHEET (layer-4 tags): ngspice at the block's OWN bench bias, typical / 27 C / res_typical / 3.3 V,",
        f"every consumer diode as load ({rec}).",
        "R and C: PDK-model replicas (R = 0.1 V / I; C from the AC current at 1 MHz).",
        "gm/Id = gm / Id of the BSIM4 instance; Id includes m. In analog_top the loads and biases differ:",
        "in-macro values are measured there, not here.",
    ]
    s.text("T {" + "\n".join(note) + f"}} 1800 -1600 0 0 0.36 0.36 {HEAD}")
    s.text("B 4 40 -1615 2790 -1250 {fill=false dash=4}")
    # ------------------------------------------------ values next to the devices
    # core: in the free band between the pb gate wire (y -780) and the NMOS drains
    tag(s, 592, -770, ["XMP1"] + mos_tag(D, "xmp1"))
    tag(s, 792, -770, ["XMP2 (diode)"] + mos_tag(D, "xmp2"))
    tag(s, 592, -680, ["XMN1 (diode)"] + mos_tag(D, "xmn1"))
    tag(s, 792, -680, ["XMN2 (K = 8)"] + mos_tag(D, "xmn2"))
    # resistor strips: value right of each, string total below
    rs = sorted([k for k in dv if k.startswith("XR")], key=lambda k: int(k[2:]))
    y = -560 + 30 + 60
    for k in rs:
        tag(s, 808, y - 22, [say(num(P, "xr1", "value", 1e-3, "%.3f"), " kOhm")])
        y += 80
    tag(s, 800, y - 50, [f"R = {len(rs)} x strip", f"  = {rstr}"])
    # MIM decaps
    for name, ycap in (("XCP", -720), ("XCN", -340)):
        c = num(P, name, "value", 1e15, "%.1f")
        f, a, per = mim_formula(dv[name])
        tag(s, 412, ycap + 34, [f"C = {say(c, ' fF')}", f"(card: {f:.1f} fF)"])
    # outputs
    x = 1000
    for name in ["XOC0", "XOC1", "XOC2", "XOC3", "XOR"]:
        tag(s, x + 28, -262, mos_tag(D, name.lower()))
        x += 160
    x = 1080
    for name in ["XOV", "XOB"]:
        tag(s, x + 28, -820, mos_tag(D, name.lower()))
        x += 240
    tag(s, 192, -400, ["bleeder " + say(num(D, "xsb1", "id", 1e9, "%.2f"), " nA"),
                       "XSU4 / XSU5", "off at the bench"])
    # ------------------------------------------------ device table (right)
    X0, Y0 = 1800, -1060
    s.text(f"T {{DEVICE OPERATING POINT AT THE BENCH BIAS}} {X0} {Y0} 0 0 0.5 0.5 {HEAD}")
    s.text(f"T {{typical / 27 C / res_typical / 3.3 V, ngspice ({rec})}} {X0} {Y0 + 34} 0 0 0.32 0.32 {{}}")
    groups = [("XMN1", "xmn1", "core diode"), ("XMN2", "xmn2", "core, K x XMN1, on R"),
              ("XMP1", "xmp1", "PMOS mirror"), ("XMP2", "xmp2", "PMOS mirror diode"),
              ("XOC0..3", "xoc0", "comparator sinks"), ("XOR", "xor", "ramp sink"),
              ("XOV, XOB", "xov", "midref sources"), ("XSB1", "xsb1", "startup bleeder (4 in series)"),
              ("XSU4", "xsu4", "startup release"), ("XSU5", "xsu5", "startup kick (off)")]
    cols = [("device", 0), ("role", 120), ("Id", 440), ("gm/Id", 560), ("|Vgs|", 660), ("|Vds|", 760), ("Vdsat", 860)]
    yt = Y0 + 80
    for (hdr, dx) in cols:
        col = [hdr]
        for name, key, role in groups:
            if hdr == "device":
                col.append(name)
            elif hdr == "role":
                col.append(role)
            elif hdr == "Id":
                col.append(amp(D, key))
            elif hdr == "gm/Id":
                col.append(say(num(D, key, "gmid", 1.0, "%.2f")))
            else:
                c = {"|Vgs|": "vgs", "|Vds|": "vds", "Vdsat": "vdsat"}[hdr]
                col.append(say(num(D, key, c, 1.0, "%.3f"), " V"))
        tag(s, X0 + dx, yt, col, prop=TAG if hdr != "device" else "{}")
    yp = yt + 22 * (len(groups) + 2)
    s.text(f"T {{PASSIVES (PDK model, ngspice replica)}} {X0} {yp} 0 0 0.5 0.5 {HEAD}")
    f, a, per = mim_formula(dv["XCP"])
    w1 = dv[rs[0]]
    lines = [
        f"XR1..XR{len(rs)}  ppolyf_u W {w1['r_width']} L {w1['r_length']}: "
        f"{say(num(P, 'xr1', 'value', 1e-3, '%.3f'), ' kOhm')} each, string {rstr}",
        f"XCP (pb-vdd), XCN (nb-vss)  cap_mim_2f0 {dv['XCP']['c_width']} x {dv['XCP']['c_length']}: "
        f"{say(num(P, 'xcp', 'value', 1e15, '%.1f'), ' fF')} each",
        f"   card check: 1.99 fF/um2 x {a:.1f} um2 + 0.2383 fF/um x {per:.1f} um = {f:.1f} fF",
        f"nodes: ns {say(num(P, 'v_ns', 'value', 1e3, '%.1f'), ' mV')}, nb {say(num(P, 'v_nb', 'value', 1.0, '%.3f'), ' V')}, "
        f"pb {say(num(P, 'v_pb', 'value', 1.0, '%.3f'), ' V')}",
    ]
    tag(s, X0, yp + 40, lines)


def sheet(dv):
    s = Sheet()
    VDD, VSS = -980, -20
    s.port("iopin", 40, VDD, "vdd", 1, 1)
    s.port("iopin", 40, VSS, "vss", 2, 1)
    # ---------------------------------------------------------------- startup (left)
    X = 160
    nbl = len([k for k in dv if k.startswith("XSB")])
    prev = (X + 20, VDD)
    y = VDD + 70
    for k in range(1, nbl + 1):
        p = s.mos(dv[f"XSB{k}"], f"XSB{k}", X, y)
        s.wire("vdd" if k == 1 else f"sb{k - 1}", prev, p["S"])
        net = "su" if k == nbl else f"sb{k}"
        s.wire(net, p["G"], (X - 20, y + 30), p["D"])
        s.stub(p["B"], "vdd")
        if k < nbl:
            s.lab(*p["D"], net, sym="lab_wire")
        prev = p["D"]
        y += 100
    su4 = s.mos(dv["XSU4"], "XSU4", X, y + 40)
    s.wire("su", prev, su4["D"])
    s.wire("vss", su4["S"], (X + 20, VSS))
    s.stub(su4["G"], "nb", dx=-40)
    s.stub(su4["B"], "vss")
    if "XSU5" in dv:
        su5 = s.mos(dv["XSU5"], "XSU5", X + 160, y + 40)
        s.wire("su", (X + 20, y - 20), (X + 120, y - 20), (X + 120, y + 40), su5["G"])
        s.wire("vss", su5["S"], (X + 180, VSS))
        s.stub(su5["D"], "pb", dy=-40, dx=0)
        s.stub(su5["B"], "vss")
    s.lab(X + 20, y - 20, "su", sym="lab_wire")
    # ---------------------------------------------------------------- core (middle)
    A, B = 560, 760
    mp1 = s.mos(dv["XMP1"], "XMP1", A, VDD + 120, flip=0)
    mp2 = s.mos(dv["XMP2"], "XMP2", B, VDD + 120)
    mn1 = s.mos(dv["XMN1"], "XMN1", A, -560)
    mn2 = s.mos(dv["XMN2"], "XMN2", B, -560)
    s.wire("vdd", mp1["S"], (A + 20, VDD))
    s.wire("vdd", mp2["S"], (B + 20, VDD))
    s.wire("nb", mp1["D"], mn1["D"])
    s.wire("pb", mp2["D"], mn2["D"])
    s.wire("pb", mp2["G"], (B - 20, VDD + 160), (B + 20, VDD + 160))
    s.wire("pb", mp1["G"], (A - 60, VDD + 120), (A - 60, VDD + 200), (B + 20, VDD + 200))
    s.wire("nb", mn1["G"], (A - 20, -620), (A + 20, -620))
    s.wire("nb", mn1["G"], (A - 60, -560), (A - 60, -500), (B - 60, -500), (B - 60, -560), mn2["G"])
    s.wire("vss", mn1["S"], (A + 20, VSS))
    s.lab(A + 20, -700, "nb", sym="lab_wire")
    s.lab(B + 20, -700, "pb", sym="lab_wire")
    for p, net in ((mp1, "vdd"), (mp2, "vdd"), (mn1, "vss"), (mn2, "vss")):
        s.stub(p["B"], net)
    rs = sorted([k for k in dv if k.startswith("XR")], key=lambda k: int(k[2:]))
    top = mn2["S"]
    y = top[1] + 60
    for k in rs:
        r = s.res(dv[k], k, B + 20, y)
        s.wire(dv[k]["nodes"][0], top, r["M"])
        s.stub(r["B"], "vss", dx=-40)
        if dv[k]["nodes"][1] != "vss":
            s.lab(*r["P"], dv[k]["nodes"][1], sym="lab_wire")
        top = r["P"]
        y += 80
    s.wire("vss", top, (B + 20, VSS))
    s.lab(B + 20, mn2["S"][1] + 10, "ns", sym="lab_wire")
    # decaps
    cp = s.mim(dv["XCP"], "XCP", A - 160, VDD + 260)
    s.stub(cp["G"], "vdd", dx=0, dy=-30)
    s.stub(cp["B"], "pb", dx=0, dy=30)
    cn = s.mim(dv["XCN"], "XCN", A - 160, -340)
    s.stub(cn["G"], "nb", dx=0, dy=-30)
    s.stub(cn["B"], "vss", dx=0, dy=30)
    # ---------------------------------------------------------------- outputs (right)
    x = 1000
    for k, name in enumerate(["XOC0", "XOC1", "XOC2", "XOC3", "XOR"]):
        o = s.mos(dv[name], name, x, -300)
        port = dv[name]["nodes"][0]
        s.wire(port, o["D"], (x + 20, -440))
        s.port("iopin", x + 20, -440, port, 3 + k)
        s.stub(o["G"], "nb", dx=-40)
        s.wire("vss", o["S"], (x + 20, VSS))
        s.stub(o["B"], "vss")
        x += 160
    x = 1080
    for k, name in enumerate(["XOV", "XOB"]):
        o = s.mos(dv[name], name, x, VDD + 120)
        port = dv[name]["nodes"][0]
        s.wire(port, o["D"], (x + 20, VDD + 260))
        s.port("iopin", x + 20, VDD + 260, port, 8 + k)
        s.stub(o["G"], "pb", dx=-40)
        s.wire("vdd", o["S"], (x + 20, VDD))
        s.stub(o["B"], "vdd")
        x += 240
    s.wire("vdd", (40, VDD), (1640, VDD))
    s.wire("vss", (40, VSS), (1680, VSS))
    annotate(s, dv)
    s.text("T {STARTUP} 100 -1080 0 0 0.4 0.4 {}")
    s.text("T {CORE} 560 -1080 0 0 0.4 0.4 {}")
    s.text("T {SINKS (nb)  /  SOURCES (pb)} 1000 -1080 0 0 0.4 0.4 {}")
    s.text("L 4 400 -1100 400 0 {dash=6}")
    s.text("L 4 940 -1100 940 0 {dash=6}")
    return s


def write_sym():
    """type=subcircuit symbol: a parent schematic netlists the X line and descends into bias_gen.sch."""
    L = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
         'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=X1"\n'
         'description="bias_gen: constant-gm bias generator, current outputs (mixed_signal/bias_gen)"\n}',
         "V {}", "S {}", "E {}",
         "L 4 -80 -100 80 -100 {}", "L 4 80 -100 80 100 {}", "L 4 80 100 -80 100 {}", "L 4 -80 100 -80 -100 {}"]
    pos = {"vdd": (0, -120, "inout"), "vss": (0, 120, "inout")}
    for k, p in enumerate(PORTS[2:]):
        pos[p] = (100, -80 + 25 * k, "inout")
    for p in PORTS:
        x, y, d = pos[p]
        if x == 100:
            L.append(f"L 4 80 {y} 100 {y} {{}}")
        else:
            L.append(f"L 4 {x} {y} {x} {100 if y > 0 else -100} {{}}")
        L.append(f"B 5 {x - 2.5} {y - 2.5} {x + 2.5} {y + 2.5} {{name={p} dir={d}}}")
        tx, ty = (x - 60, y - 8) if x == 100 else (x + 4, y + 4 if y < 0 else y - 16)
        L.append(f"T {{{p}}} {tx} {ty} 0 0 0.15 0.15 {{layer=7}}")
    L += ["T {@name} -78 -96 0 0 0.25 0.25 {}", "T {bias_gen} -78 76 0 0 0.2 0.2 {layer=13}"]
    open(os.path.join(BLOCK, "bias_gen.sym"), "w", newline="\n").write("\n".join(L) + "\n")


def main():
    net = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BLOCK, "bias_gen.spice")
    sc = subckts(net)["bias_gen"]
    assert sc["ports"] == PORTS, sc["ports"]
    sheet(sc["dev"]).write(os.path.join(BLOCK, "bias_gen.sch"), "bias_gen")
    write_sym()
    print("REPORT: wrote bias_gen.sch/.sym from " + os.path.basename(net))


if __name__ == "__main__":
    main()
