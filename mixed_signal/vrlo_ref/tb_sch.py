#!/usr/bin/env python3
"""Draw the xschem testbenches of vrlo_ref's five hand-written benches.

    python3 tb_sch.py   -> tb_op.sch, tb_tran.sch, tb_loop.sch, tb_noise.sch, tb_mc.sch,
                           vrlo_ref_lb.sym, s1cell.sym, work/dut_lb.spice

Each sheet is the hand bench (tb_<name>.spice, filled by vr.fill at the
nominal case: typical, res_typical, mimcap_typical, 27 C, 3.3 V, the design
bias of data/sizing.json, the ramp diode current vr.IRAMP_DIODE) drawn AS THE
DECK IS. Every instance value, every dot card and the .control block are read
from the filled deck, so the drawing cannot drift from the bench; only the
placement and the sheet texts are authored here. The DUT is vrlo_ref.sym
(xschem descends into vrlo_ref.sch), the ramp load is the OLD PMOS-mirror
ramp_simple.sym of ../ramp_gen (the deck's load; xschem descends into
../ramp_gen/ramp_simple.sch through this folder's xschemrc, its sizes come
from the params include in the code block), the bias diode XRD is the PDK
pfet symbol with the deck's L / W / nf and no S/D geometry. Two primitive
symbols stand for subcircuits the decks carry as text: vrlo_ref_lb.sym
(tb_loop's loop-broken DUT, written by vr.loop_variant into work/dut_lb.spice
and included by the code block) and s1cell.sym (tb_tran's S1 model of one
cell, whose .subckt stays in the code block with the switch model).

| Sheet        | Bench           | Case                                                |
| tb_op.sch    | tb_op.spice     | reset state, AVDD looped 3.0 / 3.3 / 3.6 V           |
| tb_tran.sch  | tb_tran.spice   | KS = 1 (full-scale cells), forced end of ramp        |
| tb_loop.sch  | tb_loop.spice   | RST = 1 (reset state)                                |
| tb_noise.sch | tb_noise.spice  | reset state, 1 Hz - 1 GHz, AC 1 on AVDD              |
| tb_mc.sch    | tb_mc.spice     | one mismatch draw, seed SEED_BASE + 1                |

xschem drops the text after an escaped double quote with a space inside it
(measured: `echo \\"OP 3.3\\"` netlists as `echo OP` and the rest of the block
is lost), so the decks' quoted echo lines are written unquoted; ngspice's
echo does not need the quotes. xtb.py netlists each sheet, checks it carries
every instance, dot card and control line of its bench, simulates both and
compares the figures (data/xtb.csv).
"""
import json
import os
import re
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BLOCK)
import vr  # noqa: E402

CBLOCK = "/foss/designs/mixed_signal/vrlo_ref"      # this folder inside the container
IB = json.load(open(os.path.join(vr.DATA, "sizing.json")))["design"]["IB"] * 1e-6
NOM = ("typical", 27, vr.VDD)
SEED_BASE = 20261009                                 # verify_vrlo.py
TAG = "typical 27 1 1"                               # verify_vrlo.py phase_op's tag at the nominal case
FMT = 'format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"'   # vrlo_ref_sch.py: no S/D geometry

# The nominal fill of every template, shared with xtb.py (one source).
SUBS = {
    "op": dict(CORNER="typical", MIMCORNER="typical", RESCORNER="res_typical", TEMP=27, IB="%.6g" % IB,
               IRD="%.6g" % vr.IRAMP_DIODE, TAG=TAG, RATIO="%.10f" % vr.RATIO),
    "tran": vr.tran_subs(NOM, 1.0, 1.0, IB, ks=1, real_ramp=False),
    "loop": dict(CORNER="typical", MIMCORNER="typical", RESCORNER="res_typical", TEMP=27, VDD="%g" % vr.VDD,
                 IB="%.6g" % IB, IRD="%.6g" % vr.IRAMP_DIODE, RST=1, CEQ="%.4g" % vr.C_EQ),
    "noise": dict(CORNER="typical", MIMCORNER="typical", RESCORNER="res_typical", TEMP=27, VDD="%g" % vr.VDD,
                  IB="%.6g" % IB, IRD="%.6g" % vr.IRAMP_DIODE, CEQ="%.4g" % vr.C_EQ),
    "mc": dict(CORNER="typical", MIMCORNER="typical", RESCORNER="res_typical", TEMP=27, VDD="%g" % vr.VDD,
               IB="%.6g" % IB, IRD="%.6g" % vr.IRAMP_DIODE, MM=1, SEED=SEED_BASE + 1, K=1,
               RATIO="%.10f" % vr.RATIO),
}


def unquote_echo(s):
    m = re.match(r'^(\s*echo\s+)"(.*)"\s*$', s)
    return m.group(1) + m.group(2) if m else s


def parse(name):
    """The filled hand bench as (instances, code): instances = {name: tokens
    after the name}; code = the dot cards, model / subcircuit text and the
    .control block in deck order, less the includes the hierarchy replaces
    (dut.spice, ramp_simple.spice) and with dut_lb.spice by container path."""
    txt = vr.fill("tb_%s.spice" % name, SUBS[name])
    inst, code, state = {}, [], None
    for ln in txt.splitlines():
        s = ln.strip()
        if not s or s.startswith("*"):
            continue
        low = s.lower()
        if state == "ctl":
            code.append(unquote_echo(ln.rstrip()))
            if low.startswith(".endc"):
                state = None
            continue
        if state == "sub":
            code.append(s)
            if low.startswith(".ends"):
                state = None
            continue
        if low.startswith(".control"):
            state, _ = "ctl", code.append(s)
            continue
        if low.startswith(".subckt"):
            state, _ = "sub", code.append(s)
            continue
        if s.startswith("."):
            if low == ".include dut.spice" or low.endswith("/ramp_simple.spice") or low == ".end":
                continue
            if low == ".include dut_lb.spice":
                s = ".include %s/work/dut_lb.spice" % CBLOCK
            code.append(s)
            continue
        t = s.split()
        inst[t[0]] = t[1:]
    return inst, code


def esc(s):
    return s.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


class Sch:
    # pin offsets (symbol coordinates) in SPICE terminal order, with the direction the stub leaves in
    PINS = {
        "vsource": [("p", 0, -30, "U"), ("m", 0, 30, "D")],
        "isource": [("p", 0, -30, "U"), ("m", 0, 30, "D")],
        "capa": [("p", 0, -30, "U"), ("m", 0, 30, "D")],
        "res": [("P", 0, -30, "U"), ("M", 0, 30, "D")],
        "switch": [("P", 0, -30, "U"), ("M", 0, 30, "D"), ("CP", -40, 0, "L"), ("CM", -40, 20, "L")],
        "pfet": [("D", 20, 30, "D"), ("G", -20, 0, "L"), ("S", 20, -30, "U"), ("B", 20, 0, "R")],
        "vrlo_ref": [("vrlo", 80, 0, "R"), ("ib", -80, 0, "L"), ("avdd", 0, -60, "U"), ("avss", 0, 60, "D")],
        "vrlo_ref_lb": [("vrlo", 80, 0, "R"), ("fb", -80, 20, "L"), ("ib", -80, -20, "L"), ("avdd", 0, -60, "U"),
                        ("avss", 0, 60, "D")],
        "ramp_simple": [("vramp", 120, 0, "R"), ("rst", -120, 0, "L"), ("vrlo", -120, -60, "L"),
                        ("pbias", -120, 60, "L"), ("vdd", 0, -120, "U"), ("vss", 0, 120, "D")],
        "s1cell": [("vramp", 80, 0, "R"), ("vin", -80, -30, "L"), ("pre", -80, 0, "L"), ("s1", -80, 30, "L")],
    }
    SYM = {"vsource": "devices/vsource.sym", "isource": "devices/isource.sym", "capa": "devices/capa.sym",
           "res": "devices/res.sym", "switch": "devices/switch_ngspice.sym", "pfet": "symbols/pfet_03v3.sym",
           "vrlo_ref": "vrlo_ref.sym", "vrlo_ref_lb": "vrlo_ref_lb.sym", "ramp_simple": "ramp_simple.sym",
           "s1cell": "s1cell.sym"}
    STUB = 40

    def __init__(self):
        self.wires, self.inst, self.texts, self.n = [], [], [], 0

    def label(self, x, y, net, text_left):
        self.n += 1
        self.inst.append("C {devices/lab_pin.sym} %d %d 0 %d {name=l%d sig_type=std_logic lab=%s}"
                         % (x, y, 0 if text_left else 1, self.n, net))

    def part(self, kind, x, y, attrs, nets):
        self.inst.append("C {%s} %d %d 0 0 {%s}" % (self.SYM[kind], x, y, attrs))
        for pin, dx, dy, d in self.PINS[kind]:
            px, py = x + dx, y + dy
            st = 110 if (kind == "pfet" and pin == "B") else self.STUB   # the PDK symbol's size text sits there
            ex, ey = {"U": (px, py - st), "D": (px, py + st), "L": (px - st, py), "R": (px + st, py)}[d]
            self.wires.append((px, py, ex, ey))
            self.label(ex, ey, nets[pin], d != "R")

    def dev(self, kind, name, x, y, toks):
        """One deck instance `name toks...` placed at (x, y): terminals from the
        kind's pin order, the value / model / parameters from the rest."""
        pins = [p[0] for p in self.PINS[kind]]
        nodes = [t for t in toks if "=" not in t]
        params = [t for t in toks if "=" in t]
        nets = dict(zip(pins, nodes[:len(pins)]))
        rest = nodes[len(pins):]
        if kind in ("vsource", "isource", "capa", "res"):
            value = " ".join(toks[len(pins):])
            attrs = 'name=%s value="%s"' % (name, esc(value))
            attrs += " savecurrent=false" if kind == "vsource" else (" m=1" if kind in ("capa", "res") else "")
        elif kind == "switch":
            attrs = "name=%s model=%s" % (name, rest[0])
        elif kind == "pfet":
            kv = dict(p.split("=", 1) for p in params)
            attrs = ("name=%s\nL=%s\nW=%s\nnf=%s\nm=1\nmodel=%s\nspiceprefix=\"\"\n%s"
                     % (name, kv["L"], kv["W"], kv["nf"], rest[0], FMT))
        else:                                   # subcircuit symbols: the model is the symbol's own name
            assert rest == [kind], (name, rest, kind)
            attrs = "\n".join(["name=%s" % name] + params)
        self.part(kind, x, y, attrs, nets)

    def code(self, x, y, lines):
        self.inst.append('C {devices/code_shown.sym} %d %d 0 0 {name=CTL only_toplevel=false value="%s"}'
                         % (x, y, esc("\n".join(lines))))

    def T(self, s, x, y, size=0.45, layer=None):
        self.texts.append("T {%s} %d %d 0 0 %s %s {%s}" % (s, x, y, size, size, "layer=%d" % layer if layer else ""))

    def write(self, name, order=()):
        """order: the bench's instance names in deck order; the sheet's instances
        are written in that order so xschem netlists them as the deck lists
        them (ngspice's mismatch draws follow netlist order: tb_mc under one
        seed must land every draw on the same device as the hand bench)."""
        if order:
            byname = {}
            for ln in self.inst:
                m = re.match(r"C \{[^}]*\} -?\d+ -?\d+ \d \d \{name=([^\s}]+)", ln)
                if m:
                    byname.setdefault(m.group(1), ln)
            devs = [byname[n] for n in order if n in byname]
            self.inst = devs + [ln for ln in self.inst if ln not in set(devs)]
        body = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        body += ["N %d %d %d %d {}" % w for w in self.wires]
        body += self.texts + self.inst
        open(os.path.join(BLOCK, name), "w", newline="\n").write("\n".join(body) + "\n")
        print("REPORT: wrote %s: %d symbols, %d wires, %d texts" % (name, len(self.inst) - self.n,
                                                                  len(self.wires), len(self.texts)))


# ---- the sheets --------------------------------------------------------------
# y grows downwards: title on top, the source row, the device row, (tb_tran: the
# S1 models, one row per cell so the long PWL values have room), the code block
# bottom-left. Sources are spaced by the length of their value text.
Y_TITLE, Y_HEAD, Y_SRC, Y_DEV = -1240, -1120, -980, -560
Y_DEVH = Y_DEV - 200
VAL = 0.35      # bench parameter values (>= 0.28, root CLAUDE.md)
I_B = "I_B = %.2f uA" % (IB * 1e6)
I_RD = "I_RD = %.2f uA" % (vr.IRAMP_DIODE * 1e6)
RATIO = "%d/%d AVDD" % (vr.N_BOT, vr.N_DIV)
X_RD, X_REG, X_RAMP = 200, 640, 1120


def sources(s, inst, names, y=Y_SRC):
    """Sources left to right, each given room for its value text (~8 units per
    character); returns {name: x}."""
    x, pos = 120, {}
    for n in names:
        pos[n] = x
        s.dev("vsource" if n[0] == "V" else "isource", n, x, y, inst[n])
        x += max(170, 60 + 8 * len(" ".join(inst[n][2:])))
    return pos


def bias_values(s, pos):
    s.T(I_B, pos["IB"] - 30, Y_SRC + 100, VAL, 4)
    s.T(I_RD, pos["IRD"] - 30, Y_SRC + 100, VAL, 4)


def bias_dut_ramp(s, inst, dut="vrlo_ref", y=Y_DEV):
    s.dev("pfet", "XRD", X_RD, y, inst["XRD"])
    s.dev(dut, "XREG", X_REG, y, inst["XREG"])
    s.dev("ramp_simple", "XRAMP", X_RAMP, y, inst["XRAMP"])


def tb_op():
    inst, code = parse("op")
    s = Sch()
    s.T("TB_OP  -  operating point of vrlo_ref in reset, AVDD 3.0 / 3.3 / 3.6 V", 40, Y_TITLE, 0.7)
    s.T("SUPPLY + BIAS", 60, Y_HEAD)
    s.T("DUT", X_REG - 80, Y_DEVH)
    s.T("RAMP LOAD  ramp_simple (../ramp_gen), rst = avdd", X_RAMP - 220, Y_DEVH)
    bias_values(s, sources(s, inst, ["VAVDD", "VAMR", "IB", "IRD"]))
    s.T(RATIO, X_REG - 80, Y_DEV + 150, VAL, 4)
    bias_dut_ramp(s, inst)
    s.code(40, Y_DEV + 260, code)
    s.write("tb_op.sch", order=list(inst))


def tb_tran():
    inst, code = parse("tran")
    s = Sch()
    s.T("TB_TRAN  -  two records of vrlo_ref on ramp_simple, forced end of ramp, KS = 1", 40, Y_TITLE, 0.7)
    s.T("SUPPLY + BIAS + TIMELINE", 60, Y_HEAD)
    s.T("DUT + RAMP LOAD (../ramp_gen) + FORCED END OF RAMP", X_REG - 80, Y_DEVH)
    bias_values(s, sources(s, inst, ["VAVDD", "VAMR", "IB", "IRD", "VRST", "VTOPS", "VFRC"]))
    s.T(RATIO, X_REG - 80, Y_DEV + 150, VAL, 4)
    bias_dut_ramp(s, inst)
    s.dev("switch", "SFRC", X_RAMP + 420, Y_DEV, inst["SFRC"])
    y0 = Y_DEV + 380
    s.T("S1 MODELS OF THE FOUR CELLS, KS = 1", 60, y0 - 150)
    s.T("CEQ = %g fF per cell" % (vr.C_EQ * 1e15), 760, y0 - 150, VAL, 4)
    for k in range(4):
        y = y0 + 160 * k
        for n, x in (("VV%d" % k, 120), ("VP%d" % k, 400), ("VQ%d" % k, 1480)):
            s.dev("vsource", n, x, y, inst[n])
        s.dev("s1cell", "XS%d" % k, 2560, y, inst["XS%d" % k])
    s.code(40, y0 + 160 * 4 + 20, code)
    s.write("tb_tran.sch", order=list(inst))


def tb_loop():
    inst, code = parse("loop")
    s = Sch()
    s.T("TB_LOOP  -  loop gain of vrlo_ref by voltage injection at XM1's gate, RST = 1", 40, Y_TITLE, 0.7)
    s.T("SUPPLY + BIAS + INJECTION", 60, Y_HEAD)
    s.T("DUT  loop broken, fb = XM1 gate", X_REG - 160, Y_DEVH)
    s.T("RAMP LOAD (../ramp_gen) + four cells' CEQ", X_RAMP - 60, Y_DEVH)
    bias_values(s, sources(s, inst, ["VAVDD", "IB", "IRD", "VRST", "VHOLD", "VINJ"]))
    bias_dut_ramp(s, inst, dut="vrlo_ref_lb")
    s.dev("capa", "CEQ", X_RAMP + 300, Y_DEV, inst["CEQ"])
    s.dev("res", "RHOLD", X_RAMP + 460, Y_DEV, inst["RHOLD"])
    s.T("CEQ = 4 x %g fF" % (vr.C_EQ * 1e15), X_RAMP + 260, Y_DEV + 150, VAL, 4)
    s.code(40, Y_DEV + 260, code)
    s.write("tb_loop.sch", order=list(inst))


def tb_noise():
    inst, code = parse("noise")
    s = Sch()
    s.T("TB_NOISE  -  output noise of vrlo_ref in reset, 1 Hz - 1 GHz, and AVDD -> vrlo", 40, Y_TITLE, 0.7)
    s.T("SUPPLY (AC 1) + BIAS + NOISE INPUT", 60, Y_HEAD)
    s.T("DUT", X_REG - 80, Y_DEVH)
    s.T("RAMP LOAD (../ramp_gen) + four cells' CEQ", X_RAMP - 120, Y_DEVH)
    pos = sources(s, inst, ["VAVDD", "IB", "IRD", "VNIN"])
    s.dev("res", "RNIN", pos["VNIN"] + 170, Y_SRC, inst["RNIN"])
    bias_values(s, pos)
    s.T(RATIO, X_REG - 80, Y_DEV + 150, VAL, 4)
    bias_dut_ramp(s, inst)
    s.dev("capa", "CEQ", X_RAMP + 300, Y_DEV, inst["CEQ"])
    s.T("CEQ = 4 x %g fF" % (vr.C_EQ * 1e15), X_RAMP + 260, Y_DEV + 150, VAL, 4)
    s.code(40, Y_DEV + 260, code)
    s.write("tb_noise.sch", order=list(inst))


def tb_mc():
    inst, code = parse("mc")
    s = Sch()
    s.T("TB_MC  -  vrlo_ref under PDK mismatch, one draw, seed %d" % SUBS["mc"]["SEED"], 40, Y_TITLE, 0.7)
    s.T("SUPPLY + BIAS", 60, Y_HEAD)
    s.T("DUT", X_REG - 80, Y_DEVH)
    s.T("RAMP LOAD  ramp_simple (../ramp_gen), rst = avdd", X_RAMP - 220, Y_DEVH)
    bias_values(s, sources(s, inst, ["VAVDD", "IB", "IRD"]))
    s.T(RATIO, X_REG - 80, Y_DEV + 150, VAL, 4)
    bias_dut_ramp(s, inst)
    s.code(40, Y_DEV + 260, code)
    s.write("tb_mc.sch", order=list(inst))


# ---- the two primitive symbols ----------------------------------------------
def box_sym(path, cell, pins, label, size=(60, 40), extra=()):
    """A rectangular primitive symbol: pins (name, x, y, dir) on its edge,
    netlisted as `@name @pinlist <cell> ...` (no .sch: the subcircuit text
    comes from the bench's code block / include)."""
    hw, hh = size
    L = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}",
         'K {type=primitive\nformat="@name @pinlist %s%s"\ntemplate="name=X1%s"\n}'
         % (cell, "".join(" %s=@%s" % (e, e) for e, _ in extra), "".join(" %s=%s" % e for e in extra)),
         "V {}", "S {}", "E {}",
         "L 4 %d %d %d %d {}" % (-hw, -hh, hw, -hh), "L 4 %d %d %d %d {}" % (hw, -hh, hw, hh),
         "L 4 %d %d %d %d {}" % (hw, hh, -hw, hh), "L 4 %d %d %d %d {}" % (-hw, hh, -hw, -hh)]
    for p, x, y, d in pins:
        if abs(x) > hw:
            L.append("L 4 %d %d %d %d {}" % (x, y, hw if x > 0 else -hw, y))
            tx, ty = (x - 55 if x < 0 else x - 75), y - 16
        else:
            L.append("L 4 %d %d %d %d {}" % (x, y, x, hh if y > 0 else -hh))
            tx, ty = x + 4, (y + 4 if y < 0 else y - 16)
        L.append("B 5 %g %g %g %g {name=%s dir=%s}" % (x - 2.5, y - 2.5, x + 2.5, y + 2.5, p, d))
        L.append("T {%s} %d %d 0 0 0.15 0.15 {layer=7}" % (p, tx, ty))
    L.append("T {@name} %d %d 0 0 0.25 0.25 {}" % (-hw + 2, -hh - 18))
    L.append("T {%s} %d %d 0 0 0.2 0.2 {layer=13}" % (label, -hw + 2, hh - 16))
    for e, _ in extra:
        L.append("T {%s=@%s} %d %d 0 0 0.2 0.2 {layer=4}" % (e, e, -hw + 2, -hh + 4))
    open(os.path.join(BLOCK, path), "w", newline="\n").write("\n".join(L) + "\n")


def write_syms():
    box_sym("vrlo_ref_lb.sym", "vrlo_ref_lb",
            [("vrlo", 80, 0, "out"), ("fb", -80, 20, "in"), ("ib", -80, -20, "in"), ("avdd", 0, -60, "inout"),
             ("avss", 0, 60, "inout")], "vrlo_ref_lb")
    box_sym("s1cell.sym", "s1cell",
            [("vramp", 80, 0, "inout"), ("vin", -80, -30, "in"), ("pre", -80, 0, "in"), ("s1", -80, 30, "in")],
            "s1cell", extra=[("c", "40f")])


def main():
    os.makedirs(vr.WORK, exist_ok=True)
    # tb_loop's DUT: the loop-broken netlist, as verify_vrlo.py / vr.loop() write it
    open(os.path.join(vr.WORK, "dut_lb.spice"), "w").write(
        vr.loop_variant(open(os.path.join(BLOCK, "vrlo_ref.spice")).read()))
    write_syms()
    for f in (tb_op, tb_tran, tb_loop, tb_noise, tb_mc):
        f()


if __name__ == "__main__":
    main()
