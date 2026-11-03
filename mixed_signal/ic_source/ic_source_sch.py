#!/usr/bin/env python3
"""Emit the xschem drawings of the I/C current source from the controlled netlist
and the sizing record: ic_source.sch (the cell), its symbol ic_source.sym, the
two standard-cell symbols the phase generator uses, and tb_ic.sch (the cell on
its supplies, the 20 MHz clock, bias_gen's sink and the ramp node as a level).

    ./container.sh 'python3 ic_source_sch.py'

The cell drawing netlists back to ic_source.spice device for device
(check-schematic.awk); the testbench drawing is checked for the cell and its
five sources. Text per root CLAUDE.md ("Schematic drawings"): a title, one
`layout:` line, headings, values. Bias and supply nets are drawn by labels,
the signal path (pair, fold, cascodes, gate node, node a) by wires.
"""
import json
import os

from sch_lib import Sheet

BLOCK = os.path.dirname(os.path.abspath(__file__))
SZ = json.load(open(os.path.join(BLOCK, "data", "sizing.json")))
PD, PR = SZ["predicted"], SZ["params"]
PORTS = ["iout", "ibias", "clk", "avdd", "avss", "dvdd", "dvss"]
LIB = "gf180mcu_as_sc_mcu7t3v3"


def devices():
    out = {}
    for line in open(os.path.join(BLOCK, "ic_source.spice")):
        if not line.startswith("X"):
            continue
        t = line.split()
        name, rest = t[0], t[1:]
        i = next((j for j, s in enumerate(rest) if "=" in s), len(rest))
        out[name] = (rest[i - 1], rest[:i - 1], dict(s.split("=", 1) for s in rest[i:]))
    return out


D = devices()


class S(Sheet):
    def res3k(self, name, x, y, W, L, r=0):
        """ppolyf_u_3k strip; returns (M, P, B) coordinates (M first in the pin list)."""
        self.inst.append("C {symbols/ppolyf_u_3k.sym} %d %d %d 0 {name=%s\nW=%s\nL=%s\nmodel=ppolyf_u_3k\n"
                         "spiceprefix=\"\"\nm=1}" % (x, y, r, name, self.par(W), self.par(L)))
        m_ = self.rot(0, 30, r); p_ = self.rot(0, -30, r); b_ = self.rot(-20, 0, r)
        p = ((x + m_[0], y + m_[1]), (x + p_[0], y + p_[1]), (x + b_[0], y + b_[1]))
        self.pins += list(p)
        return p

    def cell(self, sym, name, x, y):
        """a standard cell drawn from its local symbol; pins: supplies VDD VNW (top) VPW VSS (bottom), A/B left, Y right"""
        self.inst.append("C {%s.sym} %d %d 0 0 {name=%s}" % (sym, x, y, name))
        t = {"VDD": (x - 20, y - 60), "VNW": (x + 20, y - 60), "VSS": (x - 20, y + 60), "VPW": (x + 20, y + 60),
             "A": (x - 80, y + 20 if sym.endswith("nor2_2") else y), "B": (x - 80, y - 20), "Y": (x + 80, y),
             "D": (x - 80, y - 20), "CLK": (x - 80, y + 20), "Q": (x + 80, y)}
        self.pins += list(t.values())
        return t

    def port(self, kind, x, y, net):
        self.inst.append("C {devices/%s.sym} %d %d 0 0 {name=p_%s lab=%s sim_pinnumber=%d}" % (kind, x, y, net, net, PORTS.index(net) + 1))

    def stub(self, p, dx, dy, net, right=True):
        """a short wire from pin p to a net label"""
        q = (p[0] + dx, p[1] + dy)
        self.W(p, q)
        self.lab(q[0], q[1], net, right)

    def mos3(self, name, x, y, g=None, s=None, d=None):
        """a MOS from the deck on the PDK's 3-terminal symbol (body as an attribute); labels on the
        named terminals; returns the terminal dict d g s"""
        m, nodes, p = D[name]
        kind = {"pfet_03v3": "pfet3_03v3", "nfet_03v3": "nfet3_03v3"}[m]
        self.inst.append("C {symbols/%s.sym} %d %d 0 0 {name=%s\nL=%s\nW=%s\nnf=%s\nm=%s\nbody=%s\nmodel=%s\n"
                         "spiceprefix=\"\"\nformat=\"@name @pinlist @body @model L=@L W=@W nf=@nf m=@m\"}"
                         % (kind, x, y, name, p["L"], p["W"], p["nf"], p.get("m", "1"), nodes[3], m))
        dy = -30 if m == "nfet_03v3" else 30
        t = {"d": (x + 20, y + dy), "g": (x - 20, y), "s": (x + 20, y - dy)}
        self.pins += list(t.values())
        if g:
            self.stub(t["g"], -40, 0, g, right=False)
        if s:
            self.stub(t["s"], 0, dy * -1, s, right=True)
        if d:
            self.stub(t["d"], 0, dy, d, right=True)
        return t

    def rail(self, p, y):
        """a vertical wire from pin p to the supply rail at y"""
        self.W(p, (p[0], y))

    def onwire(self, x, y, net):
        """a net label sitting on a wire (the wire is split there), text to the right"""
        self.lab(x, y, net, right=True)

    def pdiode(self, t):
        """gate tied to the drain below a pfet; returns the node point under the drain"""
        (xg, yg), (xd, yd) = t["g"], t["d"]
        self.W(t["g"], (xg - 20, yg), (xg - 20, yd + 20), (xd, yd + 20))
        self.W(t["d"], (xd, yd + 20))
        return (xd, yd + 20)

    def ndiode(self, t):
        """gate tied to the drain above an nfet; returns the node point over the drain"""
        (xg, yg), (xd, yd) = t["g"], t["d"]
        self.W(t["g"], (xg - 20, yg), (xg - 20, yd - 20), (xd, yd - 20))
        self.W(t["d"], (xd, yd - 20))
        return (xd, yd - 20)

    def mimm(self, name, x, y):
        """a MIM from the deck (m units); returns (first, second) = (top, bottom) pins"""
        _, _, p = D[name]
        pins = self.mim(name, x, y, p["c_width"])
        self.inst[-1] = self.inst[-1].replace("m=1}", "m=%s}" % p.get("m", "1"))
        return pins

    def vres(self, pre, x, y, top, bot):
        """a chain of identical series strips drawn as ONE arrayed instance pre[n-1:0] (vertical, P on top);
        its ends and internal nodes are bus labels: top,mid[n-2:0] on P and mid[n-2:0],bot on M"""
        bits = sorted(int(k[len(pre) + 1:-1]) for k in D if k.startswith(pre + "["))
        n = len(bits)
        _, nodes, p = D["%s[1]" % pre]
        mid = nodes[0].split("[")[0]
        m_, p_, b_ = self.res3k("%s[%d:0]" % (pre, n - 1), x, y, p["r_width"], p["r_length"], 0)
        self.stub(p_, 0, -20, "%s,%s[%d:0]" % (top, mid, n - 2), right=True)
        self.stub(m_, 0, 20, "%s[%d:0],%s" % (mid, n - 2, bot), right=True)
        self.stub(b_, -20, 0, "avss", right=False)


# ---------------------------------------------------------------- standard-cell symbols
def std_symbol(cell, pins_left, path):
    hdr = "v {xschem version=3.4.8RC file_version=1.2}\nG {}"
    pl = " ".join("@@%s" % p for p in ("VDD", "VNW", "VPW", "VSS", "Y") + tuple(pins_left))
    sym = [hdr, 'K {type=primitive\nformat="@name %s @symname"\ntemplate="name=X1"\n}' % pl, "V {}", "S {}", "E {}"]
    for x1, y1, x2, y2 in ((-60, -40, 60, -40), (60, -40, 60, 40), (60, 40, -60, 40), (-60, 40, -60, -40)):
        sym.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))
    ys = {("A",): (0,), ("B", "A"): (-20, 20)}[tuple(pins_left)]
    for pin, y in zip(pins_left, ys):
        sym.append("L 4 -80 %d -60 %d {}" % (y, y))
        sym.append("B 5 -82.5 %.1f -77.5 %.1f {name=%s dir=in}" % (y - 2.5, y + 2.5, pin))
        sym.append("T {%s} -54 %d 0 0 0.25 0.25 {}" % (pin, y - 6))
    sym.append("L 4 60 0 80 0 {}")
    sym.append("B 5 77.5 -2.5 82.5 2.5 {name=Y dir=out}")
    sym.append("T {Y} 44 -6 0 0 0.25 0.25 {}")
    for pin, x, y in (("VDD", -20, -60), ("VNW", 20, -60), ("VSS", -20, 60), ("VPW", 20, 60)):
        sym.append("L 4 %d %d %d %d {}" % (x, y, x, y + (20 if y < 0 else -20)))
        sym.append("B 5 %.1f %.1f %.1f %.1f {name=%s dir=inout}" % (x - 2.5, y - 2.5, x + 2.5, y + 2.5, pin))
    sym.append("T {@name} -60 -58 0 0 0.3 0.3 {}")
    sym.append("T {%s} -40 -8 0 0 0.3 0.3 {layer=13}" % cell.split("__")[1].upper().replace("_2", ""))
    open(path, "w").write("\n".join(sym) + "\n")


std_symbol(LIB + "__inv_2", ("A",), os.path.join(BLOCK, LIB + "__inv_2.sym"))
std_symbol(LIB + "__nor2_2", ("B", "A"), os.path.join(BLOCK, LIB + "__nor2_2.sym"))

# =========================================================== the cell
# One sheet, signal flow left to right between an avdd rail (top) and an avss rail (bottom):
# bias | folded-cascode OTA | gate node | pass mirror, with node a and the switched capacitor under
# it; below the avss rail the reference divider and the phase generator. MOS bodies are attributes
# (3-terminal PDK symbols); the bias nets (ibias, nb, vcasn, vcasp) and the loop's inputs a / vref
# are labels. Columns 280 apart leave room for the PDK symbols' parameter text.
s = S()
Y_DD, Y_SS, X_END = -1400, -460, 3420
s.T("IC_SOURCE  -  I/C current source, I = C_UNIT x V_REF x F_CLK", 60, -1600, 0.75)
s.T("layout: pair, sinks and pass mirror interdigitated with end dummies; unit MIM beside the ramp's array; "
    "divider and R_s as unit-strip rows with dummies", 60, -1540, 0.4)
s.W((100, Y_DD), (X_END, Y_DD))
s.port("iopin", 100, Y_DD, "avdd")
s.W((100, Y_SS), (X_END, Y_SS))
s.port("iopin", 100, Y_SS, "avss")

# ---------------------------------------------------------------- bias: ibias into the diode, copies by finger count
B1, B2, B3, B4 = 160, 440, 720, 1000
s.T("bias", 120, -1470, 0.45, 13)
t = s.mos3("XPB", B1, -1300); s.rail(t["s"], Y_DD)
n = s.pdiode(t)
s.W(n, (B1 + 20, -1180)); s.port("ipin", B1 + 20, -1180, "ibias")
s.T("%.3f uA per finger" % (SZ["contract"]["i_bias_ua"] / 10), 100, -1100, 0.35, 4)
t = s.mos3("XPNB", B2, -1300, g="ibias"); s.rail(t["s"], Y_DD)
tb = s.mos3("XNB", B2, -560); s.rail(tb["s"], Y_SS)
s.W(t["d"], s.ndiode(tb))
s.onwire(B2 + 20, -800, "nb")
t = s.mos3("XPNC", B3, -1300, g="ibias"); s.rail(t["s"], Y_DD)
t1 = s.mos3("XND1", B3, -700)
s.W(t["d"], s.ndiode(t1))
s.onwire(B3 + 20, -900, "vcasn")
t2 = s.mos3("XND2", B3, -560); s.rail(t2["s"], Y_SS)
s.W(t1["s"], s.ndiode(t2))
s.onwire(B3 + 20, -640, "ncm")
t1 = s.mos3("XPD1", B4, -1300); s.rail(t1["s"], Y_DD)
t2 = s.mos3("XPD2", B4, -1150)
s.W(s.pdiode(t1), t2["s"])
s.onwire(B4 + 20, -1215, "pcm")
t3 = s.mos3("XNCS", B4, -560, g="nb"); s.rail(t3["s"], Y_SS)
s.W(s.pdiode(t2), t3["d"])
s.onwire(B4 + 20, -900, "vcasp")
s.T("V_CASN %.2f V   V_CASP %.2f V" % (PD["casn_v"], PD["casp_v"]), 440, -420, 0.35, 4)

# ---------------------------------------------------------------- the OTA: the pair between two fold columns
X1, XIA_, XT, XIR_, X2 = 1330, 1500, 1640, 1780, 2060
s.T("folded-cascode OTA", X1, -1470, 0.45, 13)
for x, lname, cname, nname, sname, sl, fh in ((X1, "XPL1", "XPLC1", "XNC1", "XN1", "sl1", "fh1"),
                                             (X2, "XPL2", "XPLC2", "XNC2", "XN2", "sl2", "fh2")):
    tl = s.mos3(lname, x, -1300, g="dl"); s.rail(tl["s"], Y_DD)
    tc = s.mos3(cname, x, -1150, g="vcasp")
    s.W(tl["d"], tc["s"]); s.onwire(x + 20, -1225, sl)
    tn = s.mos3(nname, x, -700, g="vcasn")
    s.W(tc["d"], tn["d"])
    tk = s.mos3(sname, x, -560, g="nb"); s.rail(tk["s"], Y_SS)
    s.W(tn["s"], tk["d"])
    s.onwire(x + 20, -650, fh)
s.onwire(X1 + 20, -900, "dl")
t = s.mos3("XPT", XT, -1300, g="ibias"); s.rail(t["s"], Y_DD)
ta = s.mos3("XIA", XIA_, -1000, g="a")
tr = s.mos3("XIR", XIR_, -1000, g="vref")
s.W(t["d"], (XT + 20, -1080))
s.W(ta["s"], (XIA_ + 20, -1080), (XIR_ + 20, -1080), tr["s"])
s.onwire(XT + 20, -1180, "ts")
s.W(ta["d"], (XIA_ + 20, -630), (X1 + 20, -630))
s.W(tr["d"], (XIR_ + 20, -630), (X2 + 20, -630))
s.T("tail %.3f uA, sinks %.3f uA" % (SZ["contract"]["i_bias_ua"] / 10, PD["i_sink_ua"]), X1, -420, 0.35, 4)

# ---------------------------------------------------------------- the gate node vg: C_g and the start-up pre-charge
XCG_, XSU_, XV = 2200, 2340, 2520
s.T("gate node", 2160, -1470, 0.45, 13)
s.W((X2 + 20, -900), (XV, -900))
s.onwire(2120, -900, "vg")
top, bot = s.mimm("XCG", XCG_, -760)
s.W(top, (XCG_, -900))
s.rail(bot, Y_SS)
s.T("C_g = %d units = %.2f pF" % (PR["c_g_units"], PD["c_g_pf"]), XCG_ + 20, -660, 0.35, 4)
t1 = s.mos3("XSU1", XSU_, -1300); s.rail(t1["s"], Y_DD)
t2 = s.mos3("XSU2", XSU_, -1150)
s.W(s.pdiode(t1), t2["s"]); s.onwire(XSU_ + 20, -1215, "su")
s.W(s.pdiode(t2), (XSU_ + 20, -900))

# ---------------------------------------------------------------- the pass mirror: R_s, pass device, cascode
XP1, XP2 = 2600, 2880
s.T("pass mirror", XP1 - 20, -1470, 0.45, 13)
for xr, pre, xm, xc, sn, dn in ((XP1, "XRS1", "XM1", "XM1C", "s1", "d1"), (XP2, "XRS2", "XMO", "XMOC", "s2", "d2")):
    s.vres(pre, xr + 20, -1280, "avdd", sn)
    tm = s.mos3(xm, xr, -1100, g=None if xm == "XM1" else "vg")
    s.stub(tm["s"], 0, -50, sn, right=True)
    tc = s.mos3(xc, xr, -950, g="vcasp")
    s.W(tm["d"], tc["s"]); s.onwire(xr + 20, -1025, dn)
    if xm == "XM1":
        s.W((XV, -900), (XV, -1100), tm["g"])
        s.W(tc["d"], (xr + 20, -800))
    else:
        s.W(tc["d"], (xr + 20, -860), (3180, -860))
        s.port("opin", 3180, -860, "iout")
s.T("R_s = %d x %.1f kohm = %.2f V" % (PR["rs_units"], PD["r_unit_kohm"], PD["v_deg_v"]), XP2 + 160, -1290, 0.35, 4)
s.T("I = %.3f uA" % PD["i_ref_ua"], XP2 + 120, -900, 0.35, 4)

# ---------------------------------------------------------------- node a and the switched unit capacitor
XCF_, XSA_, XSG_ = 2760, 3000, 3300
s.T("switched capacitor", XSA_ + 60, -830, 0.45, 13)
s.lab(XV + 20, -800, "a", right=False)
s.W((XV + 20, -800), (XSA_ + 20, -800))
top, bot = s.mimm("XCF", XCF_, -700)
s.W(top, (XCF_, -800))
s.rail(bot, Y_SS)
s.T("C_F = %d units" % PR["c_f_units"], XCF_ - 120, -620, 0.35, 4)
t = s.mos3("XSA", XSA_, -720, g="phi1")
s.W(t["d"], (XSA_ + 20, -800))
top, bot = s.mimm("XCU", XSA_ + 20, -580)
s.W(t["s"], top)
s.rail(bot, Y_SS)
s.T("C_UNIT %.2f fF" % PD["c_unit_ff"], XSA_ + 40, -520, 0.35, 4)
t = s.mos3("XSG", XSG_, -600, g="phi2")
s.W(t["d"], (XSG_ + 20, -650), (XSA_ + 20, -650)); s.onwire(XSA_ + 140, -650, "ct")
s.rail(t["s"], Y_SS)

# ---------------------------------------------------------------- the reference divider (below the rail, left)
s.T("reference divider", 120, -340, 0.45, 13)
s.vres("XRU", 220, -230, "avdd", "vref")
s.vres("XRL", 220, -60, "vref", "avss")
top, bot = s.mimm("XCT", 600, -150)
s.stub(top, 0, -30, "vref"); s.stub(bot, 0, 30, "avss")
s.T("V_REF = %d/%d AVDD = %.3f V" % (PR["tap_ref"], PR["n_div"], PD["v_ref"]), 440, -290, 0.35, 4)
s.T("C_T = %d units" % PR["c_t_units"], 640, -50, 0.35, 4)

# ---------------------------------------------------------------- the phase generator (below the rail, right)
s.T("non-overlapping phases on dvdd", 1100, -340, 0.45, 13)
s.port("iopin", 1120, -290, "dvdd")
s.port("iopin", 1300, -290, "dvss")


def sup(t):
    """VDD + VNW joined to one dvdd label above the cell, VSS + VPW to one dvss label below"""
    for a, b, dy, net in (("VDD", "VNW", -20, "dvdd"), ("VSS", "VPW", 20, "dvss")):
        (xa, ya), (xb, _) = t[a], t[b]
        s.W(t[a], (xa, ya + dy), (xb, ya + dy), t[b])
        s.stub(((xa + xb) // 2, ya + dy), 0, dy, net)


YA, YB, XC = -170, 90, 1300
t0 = s.cell(LIB + "__inv_2", "XI0", XC, YA); sup(t0)
s.W(t0["A"], (XC - 120, YA)); s.port("ipin", XC - 120, YA, "clk")
n1 = s.cell(LIB + "__nor2_2", "XNR1", XC + 240, YA); sup(n1)
s.W(t0["Y"], (XC + 120, YA), (XC + 120, YA + 20), n1["A"]); s.onwire(XC + 120, YA + 10, "clkb")
s.stub(n1["B"], -40, 0, "phi2", right=False)
i1 = s.cell(LIB + "__inv_2", "XI1", XC + 480, YA); sup(i1)
s.W(n1["Y"], i1["A"]); s.onwire(XC + 360, YA, "p1")
i2 = s.cell(LIB + "__inv_2", "XI2", XC + 720, YA); sup(i2)
s.W(i1["Y"], i2["A"]); s.onwire(XC + 600, YA, "p1b")
s.stub(i2["Y"], 40, 0, "phi1")
n2 = s.cell(LIB + "__nor2_2", "XNR2", XC + 240, YB); sup(n2)
s.stub(n2["A"], -40, 0, "clk", right=False)
s.stub(n2["B"], -40, 0, "phi1", right=False)
i3 = s.cell(LIB + "__inv_2", "XI3", XC + 480, YB); sup(i3)
s.W(n2["Y"], i3["A"]); s.onwire(XC + 360, YB, "p2")
i4 = s.cell(LIB + "__inv_2", "XI4", XC + 720, YB); sup(i4)
s.W(i3["Y"], i4["A"]); s.onwire(XC + 600, YB, "p2b")
s.stub(i4["Y"], 40, 0, "phi2")
nseg, njun = s.write(os.path.join(BLOCK, "ic_source.sch"))


# =========================================================== the symbol
def symbol(path):
    hdr = "v {xschem version=3.4.8RC file_version=1.2}\nG {}"
    sym = [hdr, 'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=XIC"\n'
           'description="The I/C current source (ic_source.spice): I = C_UNIT x V_REF x F_CLK into iout, folded-cascode OTA loop. Pins in the subcircuit order: %s."\n}'
           % " ".join(PORTS), "V {}", "S {}", "E {}"]
    for x1, y1, x2, y2 in ((-140, -100, 140, -100), (140, -100, 140, 100), (140, 100, -140, 100), (-140, 100, -140, -100)):
        sym.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))
    # glyph: a switched capacitor and a current-source circle
    for line in ("L 7 -90 -10 -60 -10 {}", "L 7 -60 -10 -45 -25 {}", "L 7 -30 -10 -30 10 {}", "L 7 -40 10 -20 10 {}",
                 "L 7 -40 25 -20 25 {}", "L 7 -30 25 -30 45 {}", "L 7 -90 45 -30 45 {}", "L 7 -90 -10 -90 45 {}",
                 "A 7 50 0 25 0 360 {}", "L 7 50 -25 50 25 {}", "L 7 44 15 50 25 {}", "L 7 56 15 50 25 {}"):
        sym.append(line)
    sym.append("L 4 140 0 160 0 {}")
    sym.append("B 5 157.5 -2.5 162.5 2.5 {name=iout dir=out}")
    for pin, y in (("ibias", -40), ("clk", 40)):
        sym.append("L 4 -160 %d -140 %d {}" % (y, y))
        sym.append("B 5 -162.5 %.1f -157.5 %.1f {name=%s dir=in}" % (y - 2.5, y + 2.5, pin))
    for pin, x in (("avdd", -40), ("dvdd", 40)):
        sym.append("L 4 %d -120 %d -100 {}" % (x, x))
        sym.append("B 5 %.1f -122.5 %.1f -117.5 {name=%s dir=inout}" % (x - 2.5, x + 2.5, pin))
    for pin, x in (("avss", -40), ("dvss", 40)):
        sym.append("L 4 %d 100 %d 120 {}" % (x, x))
        sym.append("B 5 %.1f 117.5 %.1f 122.5 {name=%s dir=inout}" % (x - 2.5, x + 2.5, pin))
    sym.append("T {iout} 90 -6 0 0 0.25 0.25 {}")
    sym.append("T {ibias} -134 -46 0 0 0.25 0.25 {}")
    sym.append("T {clk} -134 34 0 0 0.25 0.25 {}")
    sym.append("T {avdd} -58 -96 0 0 0.2 0.2 {}")
    sym.append("T {dvdd} 22 -96 0 0 0.2 0.2 {}")
    sym.append("T {avss} -58 84 0 0 0.2 0.2 {}")
    sym.append("T {dvss} 22 84 0 0 0.2 0.2 {}")
    sym.append("T {@name} -140 -116 0 0 0.3 0.3 {}")
    sym.append("T {I/C source} 70 70 0 0 0.22 0.22 {layer=13}")
    open(path, "w").write("\n".join(sym) + "\n")


symbol(os.path.join(BLOCK, "ic_source.sym"))


# =========================================================== the testbench
import ic_common as ic  # noqa: E402


def source(b, sym, name, x, y, value, rot=0):
    b.inst.append('C {devices/%s.sym} %d %d %d 0 {name=%s value="%s" savecurrent=false}' % (sym, x, y, rot, name, value))
    a, c = Sheet.rot(0, -30, rot), Sheet.rot(0, 30, rot)
    p = ((x + a[0], y + a[1]), (x + c[0], y + c[1]))
    b.pins += list(p)
    return p


b = S()
b.T("TB_IC  -  the I/C source alone: cold AVDD / DVDD, 20 MHz clock, the bias sink, the ramp node as a level", 60, -700, 0.7)
p, mm = source(b, "vsource", "VDD_SOURCE", 200, -500, "PWL(0 0 100n %g)" % ic.VDD)
b.W(p, (200, -580)); b.lab(200, -580, "avdd")
b.W(mm, (200, -420)); b.lab(200, -420, "0")
p, mm = source(b, "vsource", "VDVDD", 360, -500, "PWL(0 0 100n %g)" % ic.VDD)
b.W(p, (360, -580)); b.lab(360, -580, "dvdd")
b.W(mm, (360, -420)); b.lab(360, -420, "0")
b.T("supplies", 200, -620, 0.45, 13)
p, mm = source(b, "vsource", "VCLK", 560, -500, "PULSE(0 %g 150n 0.5n 0.5n 24.5n 50n)" % ic.VDD)
b.W(p, (560, -580)); b.lab(560, -580, "clk")
b.W(mm, (560, -420)); b.lab(560, -420, "0")
b.T("20 MHz clock", 520, -620, 0.45, 13)
p, mm = source(b, "isource", "IB", 760, -500, "%.4gu" % (ic.I_BIAS * 1e6))
b.W(p, (760, -580)); b.lab(760, -580, "ibias")
b.W(mm, (760, -420)); b.lab(760, -420, "0")
b.T("bias sink %.2f uA" % (ic.I_BIAS * 1e6), 700, -620, 0.45, 13)
b.inst.append("C {ic_source.sym} 1200 -300 0 0 {name=XIC}")
b.pins += [(1360, -300), (1040, -340), (1040, -260), (1160, -420), (1240, -420), (1160, -180), (1240, -180)]
b.W((1040, -340), (980, -340)); b.lab(980, -340, "ibias", right=False)
b.W((1040, -260), (980, -260)); b.lab(980, -260, "clk", right=False)
b.W((1160, -420), (1160, -460)); b.lab(1160, -460, "avdd")
b.W((1240, -420), (1240, -460)); b.lab(1240, -460, "dvdd")
b.W((1160, -180), (1160, -140)); b.lab(1160, -140, "0")
b.W((1240, -180), (1240, -140)); b.lab(1240, -140, "0")
b.W((1360, -300), (1600, -300)); b.lab(1460, -300, "iout"); b.J(1460, -300)
p, mm = source(b, "vsource", "VLD", 1600, -220, "1.2")
b.W((1600, -300), p)
b.W(mm, (1600, -140)); b.lab(1600, -140, "0")
b.T("the ramp node: 0.4355 / 1.2 / 2.053 V", 1500, -360, 0.45, 13)
b.inst.append('C {devices/code_shown.sym} 1000 60 0 0 {name=MODELS only_toplevel=false value="'
              + (ic.head(std=True)).strip().replace("{", "\\{").replace("}", "\\}") + '"}')
nseg2, njun2 = b.write(os.path.join(BLOCK, "tb_ic.sch"))
print("PASS: ic_source_sch.py wrote ic_source.sch (%d devices, %d wire segments), ic_source.sym, two standard-cell symbols and tb_ic.sch (%d segments)"
      % (len(D), nseg, nseg2))
