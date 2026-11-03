#!/usr/bin/env python3
"""Emit the xschem testbench drawings of bias_gen's benches, and check their
netlists.

    python3 tb_sch.py            -> tb_op.sch tb_startup.sch tb_mc.sch tb_noise.sch tb_cmp.sch tb_xtalk.sch
                                    + work/tb_manifest.json (what each sheet places)
    python3 tb_sch.py check      -> PASS/FAIL per sheet: every placed instance is in
                                    work/xtb_<tb>/tb_<tb>.spice with its nodes in order,
                                    and the descended subcircuits are there

Each sheet draws one bench that verify_bg.py builds, at its nominal case
(typical, 27 C, 3.3 V, res_typical): the sources with their expressions, the
generator as bias_gen.sym (xschem netlists bias_gen.sch into it, so the
testbench exercises the drawing, not the deck), every load device the deck
gives it (the consumers' own bias diodes behind 0 V ammeters, bg.consumer_loads),
and a code block carrying the deck's own cards: the PDK model lines, .param,
.temp, .options and the .control with its measures. xtb.py netlists every
sheet, simulates it and compares its figures with the hand deck's (data/xtb.csv).

| Sheet          | Bench it draws (verify_bg.py)                  | Nominal case drawn                              |
| tb_op.sch      | bg.op_deck (phase op)                          | VDD 3.0 / 3.3 / 3.6 V in one .control           |
| tb_startup.sch | startup_deck ramp100n and dead                 | both cases from one sheet (alter in .control)   |
| tb_mc.sch      | mc_deck (phase mc)                             | draw k = 1, .options seed = SEED_BASE + 1       |
| tb_noise.sch   | phase_noise "new" deck                         | noise v(lr), 1 Hz - 100 MHz                     |
| tb_cmp.sch     | phase_cmp (tb_sel_dc + tb_sel on icmp0)        | static trip, then the plateau level 40.5 LSB    |
| tb_xtalk.sch   | XT_DECK (phase xtalk)                          | case a, then case q by alterparam               |

The midref bench (phase midref) places the frozen ref/midrail_ref_v2 cells,
which have no drawings here: it stays deck-only (README).

Sheet text: one title, short headings, the bench's parameter values
(CLAUDE.md, "Schematic drawings"). The deck's model and control cards are
taken from verify_bg.py / bg.py at import time, so the code block cannot
drift from the deck.
"""
import json
import os
import re
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BLOCK)
import bg  # noqa: E402
import verify_bg as V  # noqa: E402  the deck builders (no phase runs at import)

GEN = os.path.join(BLOCK, "bias_gen.spice")
WORK = os.path.join(BLOCK, "work")
MANIFEST = os.path.join(WORK, "tb_manifest.json")
SHEETS = ("op", "startup", "mc", "noise", "cmp", "xtalk")
HEAD = bg.NGSPICE_HEAD.format(corner="typical", rcorner="res_typical", mim="typical").rstrip("\n")
MIM_ATTR = 'W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1'


def esc(s):
    return s.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


def cards(deck, skip_includes):
    """The non-element lines of a hand deck: every dot card (the model lines,
    .param, .temp, .options, .save, .model) and the .control block, in order;
    the title line, element lines and the .include of a generated subcircuit
    file are left out (the drawing places those)."""
    out, ctl = [], False
    for ln in deck.splitlines()[1:]:
        s = ln.strip()
        if not s:
            continue
        if s.lower().startswith(".control"):
            ctl = True
        if ctl:
            out.append(s)
            if s.lower().startswith(".endc"):
                ctl = False
            continue
        if s.startswith("*"):
            continue
        if s.startswith("."):
            if s.lower() == ".end":
                continue
            if s.lower().startswith(".include") and any(k in s for k in skip_includes):
                continue
            out.append(s)
    return "\n".join(out)


def mos_attrs(line):
    """xschem attributes of a PDK MOS symbol from one hand-deck device line
    (bg.mos / size_v3.dev): the name, every parameter as written, the deck's
    model and a format that writes the parameters back in the deck's order
    (no sa/sb/sd, spiceprefix empty: the X comes from the name)."""
    t = line.split()
    name, model = t[0], [x for x in t[1:] if "=" not in x][-1]
    kv = [x.split("=", 1) for x in t if "=" in x]
    fmt = " ".join(f"{k}=@{k}" for k, _ in kv)
    attrs = f"name={name}\n" + "\n".join(f"{k}={v}" for k, v in kv) + f"\nmodel={model}\nspiceprefix=\"\"\n"
    attrs += f'format="@name @pinlist @model {fmt}"'
    kind = "pfet" if model.startswith("pfet") else "nfet"
    return kind, name, attrs, t[1:5]


class Sch:
    # pin offsets (symbol coordinates) and the direction each stub leaves in
    PINS = {
        "vsource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "isource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "capa": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "res": {"p": (0, -30, "U"), "m": (0, 30, "D")},
        "switch": {"P": (0, -30, "U"), "M": (0, 30, "D"), "CP": (-40, 0, "L"), "CM": (-40, 20, "L")},
        "mim": {"G": (0, -30, "U"), "B": (0, 30, "D")},
        "pfet": {"D": (20, 30, "D"), "G": (-20, 0, "L"), "S": (20, -30, "U"), "B": (20, 0, "R")},
        "nfet": {"D": (20, -30, "U"), "G": (-20, 0, "L"), "S": (20, 30, "D"), "B": (20, 0, "R")},
        "bg": {"vdd": (0, -120, "U"), "vss": (0, 120, "D"), "icmp0": (100, -80, "R"), "icmp1": (100, -55, "R"),
               "icmp2": (100, -30, "R"), "icmp3": (100, -5, "R"), "iramp": (100, 20, "R"), "ivref": (100, 45, "R"),
               "ivbl": (100, 70, "R")},
        "cmp": {"inp": (-100, -60, "L"), "inn": (-100, -30, "L"), "clk": (-100, 0, "L"), "nbias": (-100, 30, "L"),
                "pbias": (-100, 60, "L"), "dout": (100, -45, "R"), "vdd": (0, -120, "U"), "vss": (0, 120, "D")},
    }
    # @pinlist order of each symbol (the order of its pin boxes)
    ORDER = {"vsource": ("p", "m"), "isource": ("p", "m"), "capa": ("p", "m"), "res": ("p", "m"),
             "switch": ("P", "M", "CP", "CM"), "mim": ("G", "B"), "pfet": ("D", "G", "S", "B"),
             "nfet": ("D", "G", "S", "B"), "bg": tuple(bg.PORTS.split()),
             "cmp": ("inp", "inn", "dout", "clk", "vdd", "vss", "nbias", "pbias")}
    SYM = {"vsource": "devices/vsource.sym", "isource": "devices/isource.sym", "capa": "devices/capa.sym",
           "res": "devices/res.sym", "switch": "devices/switch_ngspice.sym", "mim": "symbols/cap_mim_2f0fF.sym",
           "pfet": "symbols/pfet_03v3.sym", "nfet": "symbols/nfet_03v3.sym", "bg": "bias_gen.sym",
           "cmp": "comparator.sym"}
    SUBCKT = {"bg": "bias_gen", "cmp": "comparator"}
    STUB = 40

    def __init__(self, name):
        self.name = name
        self.wires, self.inst, self.texts, self.n = [], [], [], 0
        self.devices = []          # (name, [nets in pinlist order], subckt or "")

    def label(self, x, y, net, text_left):
        self.n += 1
        self.inst.append("C {devices/lab_pin.sym} %d %d 0 %d {name=l%d sig_type=std_logic lab=%s}"
                         % (x, y, 0 if text_left else 1, self.n, net))

    def part(self, kind, x, y, attrs, nets, stubs=None):
        """One symbol with a stub and a net label on every pin."""
        self.inst.append("C {%s} %d %d 0 0 {%s}" % (self.SYM[kind], x, y, attrs))
        for pin, net in nets.items():
            dx, dy, d = self.PINS[kind][pin]
            px, py = x + dx, y + dy
            ln = (stubs or {}).get(pin, self.STUB)
            ex, ey = {"U": (px, py - ln), "D": (px, py + ln), "L": (px - ln, py), "R": (px + ln, py)}[d]
            self.wires.append((px, py, ex, ey))
            self.label(ex, ey, net, d != "R")
        name = re.match(r"name=(\S+)", attrs).group(1)
        self.devices.append((name, [nets[p] for p in self.ORDER[kind]], self.SUBCKT.get(kind, "")))

    def mos(self, line, x, y):
        """A MOS from a hand-deck line, its nodes on the pins D G S B."""
        kind, name, attrs, nodes = mos_attrs(line)
        self.part(kind, x, y, attrs, dict(zip(("D", "G", "S", "B"), nodes)))

    def vsrc(self, name, x, y, value, p, m="0"):
        self.part("vsource", x, y, 'name=%s value="%s" savecurrent=false' % (name, esc(value)), {"p": p, "m": m})

    def isrc(self, name, x, y, value, p, m="0"):
        self.part("isource", x, y, 'name=%s value="%s"' % (name, esc(value)), {"p": p, "m": m})

    def code(self, x, y, text):
        """The deck's cards as a code_shown block. xschem drops a double quote
        inside the value and ends the token at the next space (an echo "a b"
        came out as echo a), so echo lines lose their quotes here (ngspice's
        echo prints its arguments the same way) and any other quote is an error."""
        lines = []
        for ln in text.splitlines():
            if ln.startswith("echo "):
                ln = ln.replace('"', "")
            if '"' in ln:
                raise SystemExit(f"tb_{self.name}: a double quote in the code block is dropped by xschem: {ln}")
            lines.append(ln)
        self.inst.append('C {devices/code_shown.sym} %d %d 0 0 {name=CTL only_toplevel=false value="%s"}'
                         % (x, y, esc("\n".join(lines))))

    def T(self, s, x, y, size=0.4, layer=None):
        self.texts.append("T {%s} %d %d 0 0 %s %s {%s}" % (s, x, y, size, size, "layer=%d" % layer if layer else ""))

    def title(self, s):
        self.T(s, 40, -1340, 0.7)

    def write(self):
        body = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        body += ["N %d %d %d %d {}" % w for w in self.wires]
        body += self.texts + self.inst
        path = os.path.join(BLOCK, f"tb_{self.name}.sch")
        open(path, "w", newline="\n").write("\n".join(body) + "\n")
        print("REPORT: wrote tb_%s.sch: %d symbols, %d wires, %d texts" % (
            self.name, len(self.inst) - self.n, len(self.wires), len(self.texts)))
        return {"devices": self.devices, "texts": len(self.texts)}


# ------------------------------------------------------------------ shared pieces
def generator(s, x, y, outs=None, vdd="vdd", vss="0"):
    """bias_gen.sym with its seven outputs labelled (default: the port names)."""
    outs = outs or bg.PORTS.split()[2:]
    nets = {"vdd": vdd, "vss": vss}
    nets.update(dict(zip(bg.PORTS.split()[2:], outs)))
    stubs = {p: (60 if k % 2 else 120) for k, p in enumerate(bg.PORTS.split()[2:])}
    s.part("bg", x, y, "name=XG", nets, stubs)


def consumer_loads(s, x0, y):
    """bg.consumer_loads() as drawn: the comparator diodes XLC0..3 and the ramp
    diode XLR (PMOS, on vdd) each behind its 0 V ammeter, the midref diodes
    XLV / XLB (NMOS, to 0) behind theirs."""
    lines = {ln.split()[0]: ln for ln in bg.consumer_loads().splitlines() if ln.strip()}
    pairs = [(f"XLC{k}", f"VMC{k}") for k in range(bg.N_CMP)] + [("XLR", "VMR"), ("XLV", "VMV"), ("XLB", "VMB")]
    for k, (dev, amm) in enumerate(pairs):
        x = x0 + 260 * k
        s.mos(lines[dev], x, y)
        t = lines[amm].split()                    # VMC<k> lc<k> icmp<k> 0 ; VMV ivref lv 0
        s.vsrc(t[0], x + 100, y + 200, t[3], t[1], t[2])


# ------------------------------------------------------------------ sheets
def tb_op():
    s = Sch("op")
    s.title("TB_OP  -  operating point of bias_gen, every output into its consumer diode")
    s.vsrc("VDD", 120, -1180, "3.3", "vdd")
    s.T("VDD 3.0 / 3.3 / 3.6 V", 60, -1040, 0.3, 4)
    generator(s, 600, -1100)
    s.T("CONSUMER DIODES, 0 V AMMETERS", 60, -800, 0.4)
    consumer_loads(s, 160, -680)
    deck = bg.op_deck(V.SIZ, ("typical", 27.0), "res_typical", GEN)
    s.code(60, -300, cards(deck, ["bias_gen.spice"]))
    return s.write()


def tb_startup():
    s = Sch("startup")
    s.title("TB_STARTUP  -  start-up of bias_gen: supply ramp, and the forced dead state released")
    s.vsrc("VDD", 120, -1180, "PWL(0 0 {TRAMP} 3.3)", "vdd")
    s.T("TRAMP 100 ns", 60, -1040, 0.3, 4)
    s.T("DEAD-STATE HOLD, released at TREL = 10 us", 300, -1290, 0.4)
    s.vsrc("VHC", 360, -1180, "PWL(0 1 {TREL} 1 {TREL+10n} 0)", "hc")
    s.part("switch", 800, -1180, "name=SHP model=swh", {"P": "vdd", "M": "xg.pb", "CP": "hc", "CM": "0"})
    s.part("switch", 1020, -1180, "name=SHN model=swh", {"P": "xg.nb", "M": "0", "CP": "hc", "CM": "0"})
    generator(s, 600, -840)
    s.T("CONSUMER DIODES, 0 V AMMETERS", 60, -560, 0.4)
    consumer_loads(s, 160, -440)
    # the deck's two nominal cases, from startup_deck's own numbers
    tr = 100e-9
    t_ramp = tr + max(20e-6, 0.2 * tr)
    step_r = t_ramp / 4000
    t_dead, t0_dead = 60e-6, 10e-6
    step_d = t_dead / 4000
    code = (HEAD + "\n.temp 27\n.param TRAMP=100n\n.param TREL=10u\n"
            ".model swh sw vt=0.5 vh=0.1 ron=10 roff=1e15\n"
            ".save all @m.xg.xmn1.m0[id]\n.control\nset num_threads=1\n"
            "* case ramp100n: the supply ramps in TRAMP, the hold stays off\n"
            "alter @vhc[pwl] = [ 0 0 1 0 ]\n"
            f"tran {step_r:g} {t_ramp:g} 0 {step_r:g} uic\n"
            f"meas tran icf find @m.xg.xmn1.m0[id] at={t_ramp:g}\n"
            f"meas tran icmpf find i(vmc0) at={t_ramp:g}\n"
            f"meas tran suf find v(xg.su) at={t_ramp:g}\n"
            "echo \"START $&icf $&icmpf $&suf\"\n"
            "let i90 = 0.9 * icf\n"
            "meas tran t90 when @m.xg.xmn1.m0[id]=$&i90 rise=1\n"
            f"let tup = t90 - {tr:g}\n"
            "echo \"T90 $&tup\"\n"
            "* case dead: settled supply, pb held at vdd and nb at 0 until TREL\n"
            "alter @vdd[pwl] = [ 0 3.3 1 3.3 ]\n"
            f"alter @vhc[pwl] = [ 0 1 {t0_dead:g} 1 {t0_dead + 10e-9:g} 0 ]\n"
            f"tran {step_d:g} {t_dead:g} 0 {step_d:g} uic\n"
            f"meas tran icf find @m.xg.xmn1.m0[id] at={t_dead:g}\n"
            f"meas tran icmpf find i(vmc0) at={t_dead:g}\n"
            f"meas tran suf find v(xg.su) at={t_dead:g}\n"
            "echo \"START $&icf $&icmpf $&suf\"\n"
            "let i90 = 0.9 * icf\n"
            "meas tran t90 when @m.xg.xmn1.m0[id]=$&i90 rise=1\n"
            f"let tup = t90 - {t0_dead:g}\n"
            "echo \"T90 $&tup\"\nquit\n.endc")
    s.code(60, -80, code)
    return s.write()


def tb_mc():
    s = Sch("mc")
    s.title("TB_MC  -  outputs of bias_gen, one local-mismatch draw")
    s.vsrc("VDD", 120, -1180, "3.3", "vdd")
    s.T("seed %d" % (V.SEED_BASE + 1), 60, -1040, 0.3, 4)
    generator(s, 600, -1100)
    s.T("CONSUMER DIODES, 0 V AMMETERS", 60, -800, 0.4)
    consumer_loads(s, 160, -680)
    s.code(60, -300, cards(V.mc_deck(1, 1), ["bias_gen.spice"]))
    return s.write()


def tb_noise():
    s = Sch("noise")
    s.title("TB_NOISE  -  noise on the ramp's mirror line lr, bias_gen iramp into the ramp diode")
    s.vsrc("VDD", 120, -1180, "3.3 ac 1", "vdd")
    generator(s, 600, -1100)
    s.T("CONSUMER DIODES, 0 V AMMETERS", 60, -800, 0.4)
    consumer_loads(s, 160, -680)
    code = (HEAD + "\n.temp 27\n.control\nset num_threads=1\nnoise v(lr) VDD dec 20 1 100meg\nsetplot noise1\n"
            "wrdata nz_new.txt onoise_spectrum\nquit\n.endc")
    s.code(60, -300, code)
    return s.write()


def cmp_design():
    S3 = V.cmp_module()
    sel = json.load(open(os.path.join(V.CMP_BLOCK, "data", "sizing.json")))
    s = {k: sel[k] for k in S3.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    return S3, s


def gen_diodes(s, x0, y, outs, vdd):
    """verify_bg.gen_lines' diodes on the generator outputs a foreign bench does
    not use: XGDgc1..3 (comparator diodes, on vdd), XGDR (ramp), XGDV / XGDB
    (midref, to 0)."""
    lines = [ln for ln in V.gen_lines("res_typical", vdd, outs[0], outs).splitlines() if ln.startswith("XGD")]
    for k, ln in enumerate(lines):
        s.mos(ln, x0 + 260 * k, y)


def tb_cmp():
    S3, sz = cmp_design()
    s = Sch("cmp")
    lvl = 40.5
    s.title("TB_CMP  -  comparator on icmp0 of bias_gen: static trip, then delay on the charge path")
    # row 1: supplies, levels, the zero ideal currents and their diodes (the bench's bias parts)
    for i, (name, val, net) in enumerate([("VDD_SOURCE", "{VDD}", "vdd"), ("VDD_BIAS", "{VDD}", "vddb"),
                                          ("VVBL", "{VDD/2}", "vbl"), ("VVREF", "{VDD/2}", "vref"),
                                          ("VCLK", "0", "clk"), ("VDC", "1.65", "vdc")]):
        s.vsrc(name, 120 + 170 * i, -1180, val, net)
    s.isrc("IREFN", 120, -900, "{IREF}", "vddb", "nbias")
    s.mos("XREFN nbias nbias 0 0 nfet_03v3 L=1u W=20u nf=10 m=1", 320, -900)
    s.isrc("IREFP", 480, -900, "{IREF}", "pbias", "0")
    s.mos(S3.ref_line(sz, 0.0)[0], 680, -900)
    s.T("IREF 0: pbias from the generator", 60, -1010, 0.3, 4)
    s.T("STATIC TRIP", 1400, -1290, 0.4)
    s.part("cmp", 1500, -1080, "name=XDC", {"inp": "vbl", "inn": "vdc", "clk": "clk", "nbias": "nbias",
                                            "pbias": "pbias", "dout": "doutdc", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1760, -1080, "name=CLDC value=1e-14 m=1", {"p": "doutdc", "m": "0"})
    # row 3: the generator, icmp0 = pbias, the other consumers on diodes
    s.T("GENERATOR, the other consumers' diodes", 60, -740, 0.4)
    generator(s, 300, -520, ["pbias", "gc1", "gc2", "gc3", "glr", "glv", "glb"], vdd="vddb")
    gen_diodes(s, 760, -560, ["pbias", "gc1", "gc2", "gc3"], "vddb")
    # row 4: the cell's charge path at the plateau level
    s.T("CHARGE PATH, VIN = VR_LO + 40.5 LSB", 60, -260, 0.4)
    s.vsrc("VBOT", 120, -100, "PWL(0 {VIN} {TCONN} {VIN} {TCONN+TEDGE} {VR_LO} {TR} {VR_LO} {TR+14u} {VEND})", "bot")
    s.vsrc("VS2", 120, 140, "PWL(0 1 {TS} 1 {TS+TEDGE} 0)", "s2")
    s.part("switch", 760, -100, "name=S2 model=swideal", {"P": "vref", "M": "top", "CP": "s2", "CM": "0"})
    s.part("mim", 920, 140, "name=XCS " + MIM_ATTR, {"G": "top", "B": "bot"})
    s.T("C_S 54.52 fF", 960, 200, 0.3, 4)
    s.part("res", 1080, -100, "name=RLKT value=1e15 m=1", {"p": "top", "m": "0"})
    s.part("cmp", 1380, -100, "name=XDUT", {"inp": "vbl", "inn": "top", "clk": "clk", "nbias": "nbias",
                                            "pbias": "pbias", "dout": "dout", "vdd": "vdd", "vss": "0"})
    s.part("capa", 1620, -100, "name=CLOAD value=1e-14 m=1", {"p": "dout", "m": "0"})
    vin = S3.VR_LO + lvl * S3.LSB
    tstop = 400e-9 + lvl * S3.TCOUNT + 400e-9
    code = (HEAD + "\n.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16\n"
            ".param VDD=3.3\n.temp 27\n.param IREF=0\n"
            f".param VIN={vin:.9g}\n.param VR_LO=0.5\n.param LSB=0.005859375\n.param TCOUNT=50n\n"
            ".param SLOPE='LSB/TCOUNT'\n.param TS=300n\n.param TCONN=310n\n.param TR=400n\n.param TEDGE=100p\n"
            ".param VEND='VR_LO+14u*SLOPE'\n"
            ".csparam cs_vdd={VDD}\n.csparam cs_tr={TR}\n.csparam cs_tconn={TCONN}\n"
            ".csparam cs_tideal={TR+(VIN-VR_LO)/SLOPE}\n"
            ".options savecurrents reltol=1e-4 gmin=1e-15\n"
            ".control\nset num_threads=1\n"
            "* static trip (tb_sel_dc): inn swept through inp = VBL\n"
            "dc VDC 1.6 1.7 25u\n"
            "meas dc vtrip when v(doutdc)=1.65 fall=1\n"
            "let vtr6 = floor(vtrip * 1e6 + 0.5) / 1e6\n"
            "set numdgt=10\n"
            "set vtrip_s = $&vtr6\n"
            "* charge path (tb_sel), plateau level: delay from the trip crossing\n"
            "set wr_singlescale\n"
            f"tran 0.25n {tstop:.6g} 0 0.5n\n"
            "let half = $&cs_vdd / 2\n"
            "let hi90 = 0.9 * $&cs_vdd\n"
            "let lo10 = 0.1 * $&cs_vdd\n"
            "meas tran t_cross when v(top)=1.65 rise=1 td=$&cs_tr\n"
            "meas tran t_cs when v(top)=$vtrip_s rise=1 td=$&cs_tr\n"
            "meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr\n"
            "meas tran t_f90 when v(dout)=$&hi90 fall=1 td=$&cs_tr\n"
            "meas tran t_f10 when v(dout)=$&lo10 fall=1 td=$&cs_tr\n"
            "meas tran armed find v(dout) at=$&cs_tr\n"
            "let t_after = t_dout + 5e-9\n"
            "meas tran t_rerise when v(dout)=$&half rise=1 td=$&t_after\n"
            "meas tran i_avg avg i(vdd_source) from=$&cs_tconn to=$&t_cross\n"
            "let delay_vbl = t_dout - t_cross\n"
            "let delay_dyn = t_dout - t_cs\n"
            "let fall = t_f10 - t_f90\n"
            "let ped_counts = (t_dout - $&cs_tideal) / 50e-9\n"
            "let p_avg = -$&cs_vdd * i_avg\n"
            "echo \"RESULT_BEGIN\"\n"
            "echo \"vtrip_v = $vtrip_s\"\n"
            "print delay_vbl delay_dyn fall ped_counts armed p_avg\n"
            "echo \"RESULT_END\"\nquit\n.endc")
    s.code(2200, -1200, code)
    return s.write()


XT_LVL = 40.5


def xt_levels():
    """The deck's %.6f input levels: victim at XT_LVL, aggressors one LSB lower (case a) or quiet (case q)."""
    f = lambda k: "%.6f" % (0.5 + k * 1.5 / 256)
    return f(XT_LVL), f(XT_LVL - 1), f(300), "%.6f" % (0.5 + 14e-6 * 1.5 / 256 / 50e-9)


def tb_xtalk():
    S3, sz = cmp_design()
    s = Sch("xtalk")
    vvic, vagg, vq, vend = xt_levels()
    s.title("TB_XTALK  -  four comparators on bias_gen, aggressors 1..3 decide one LSB before the victim")
    for i, (name, val, net) in enumerate([("VDD_SOURCE", "{VDD}", "vdd"), ("VVBL", "{VDD/2}", "vbl"),
                                          ("VVREF", "{VDD/2}", "vref"), ("VCLK", "0", "clk")]):
        s.vsrc(name, 120 + 170 * i, -1180, val, net)
    s.vsrc("VS2", 800, -1180, "PWL(0 1 300n 1 300.1n 0)", "s2")
    s.T("GENERATOR, pb0..3 = the comparators' pbias diodes", 60, -1020, 0.4)
    generator(s, 300, -800, ["pb0", "pb1", "pb2", "pb3", "glr", "glv", "glb"])
    kind, L, wf, nf = bg.CMP_DIODE
    k2, L2, w2, n2 = bg.RAMP_DIODE
    k3, L3, w3, n3 = bg.MR_DIODE
    diodes = [bg.mos(f"XRP{i}", f"pb{i}", f"pb{i}", "vdd", "vdd", kind, L, wf, nf) for i in range(4)]
    diodes += [bg.mos("XGDR", "glr", "glr", "vdd", "vdd", k2, L2, w2, n2),
               bg.mos("XGDV", "glv", "glv", "0", "0", k3, L3, w3, n3),
               bg.mos("XGDB", "glb", "glb", "0", "0", k3, L3, w3, n3)]
    for k, ln in enumerate(diodes):
        s.mos(ln, 760 + 260 * k, -840)
    s.T("victim 40.5 LSB, aggressors 39.5 LSB (quiet: 300 LSB)", 60, -620, 0.3, 4)
    s.T("CELLS 0 (VICTIM) .. 3", 60, -560, 0.4)
    for i in range(4):
        y0 = -400 + 400 * i
        vin = "{VVIC}" if i == 0 else "{VAGG}"
        s.vsrc(f"VBOT{i}", 120, y0, f"PWL(0 {vin} 310n {vin} 310.1n 0.5 400n 0.5 14.4u {{VEND}})", f"bot{i}")
        s.part("switch", 760, y0, f"name=S2_{i} model=swideal", {"P": "vref", "M": f"top{i}", "CP": "s2", "CM": "0"})
        s.part("mim", 920, y0, f"name=XCS{i} " + MIM_ATTR, {"G": f"top{i}", "B": f"bot{i}"})
        s.part("res", 1180, y0, f"name=RLK{i} value=1e15 m=1", {"p": f"top{i}", "m": "0"})
        s.part("cmp", 1480, y0, f"name=XDUT{i}", {"inp": "vbl", "inn": f"top{i}", "clk": "clk", "nbias": "0",
                                                  "pbias": f"pb{i}", "dout": f"dout{i}", "vdd": "vdd", "vss": "0"})
        s.part("capa", 1720, y0, f"name=CL{i} value=10f m=1", {"p": f"dout{i}", "m": "0"})
    tstop = 400e-9 + (XT_LVL + 4) * 50e-9
    code = (HEAD + "\n.temp 27\n.param VDD=3.3\n.param LSB=0.005859375\n.param SLOPE='LSB/50n'\n"
            f".param VVIC={vvic}\n.param VAGG={vagg}\n.param VEND={vend}\n"
            ".options savecurrents reltol=1e-4 gmin=1e-15\n"
            ".model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16\n"
            ".control\nset num_threads=1\n"
            "* case a: aggressors one LSB below the victim\n"
            f"tran 0.25n {tstop:g} 0 0.5n\n"
            "let half = 3.3 / 2\n"
            "meas tran t0 when v(dout0)=$&half fall=1 td=400n\n"
            f"meas tran pbx max v(pb0) from=400n to={tstop:g}\n"
            f"meas tran pbn min v(pb0) from=400n to={tstop:g}\n"
            "echo \"XT $&t0 $&pbx $&pbn\"\n"
            "* case q: aggressors quiet (input above the ramp's end)\n"
            f"alterparam VAGG={vq}\nreset\n"
            f"tran 0.25n {tstop:g} 0 0.5n\n"
            "let half = 3.3 / 2\n"
            "meas tran t0 when v(dout0)=$&half fall=1 td=400n\n"
            f"meas tran pbx max v(pb0) from=400n to={tstop:g}\n"
            f"meas tran pbn min v(pb0) from=400n to={tstop:g}\n"
            "echo \"XT $&t0 $&pbx $&pbn\"\nquit\n.endc")
    s.code(2460, -1200, code)
    return s.write()


# ------------------------------------------------------------------ check
def check():
    man = json.load(open(MANIFEST))
    bad = 0
    for tb in SHEETS:
        path = os.path.join(WORK, f"xtb_{tb}", f"tb_{tb}.spice")
        if not os.path.exists(path):
            print(f"FAIL: tb_{tb}.sch: xschem produced no netlist ({path})")
            bad += 1
            continue
        inst = {}
        for ln in open(path):
            t = ln.split()
            if t and ln[0] not in "*.+ \t":
                inst.setdefault(t[0].lower(), t)
        subs = {ln.split()[1] for ln in open(path) if ln.lower().startswith(".subckt")}
        missing, wrong = [], []
        for name, nets, sub in man[tb]["devices"]:
            t = inst.get(name.lower())
            if t is None:
                missing.append(name)
                continue
            if [x.lower() for x in t[1:1 + len(nets)]] != [n.lower() for n in nets]:
                wrong.append(f"{name} {' '.join(t[1:1 + len(nets)])} (drawn {' '.join(nets)})")
            if sub and (t[1 + len(nets)].lower() != sub or sub not in subs):
                wrong.append(f"{name}: subcircuit {t[1 + len(nets)]} ({'defined' if sub in subs else 'NOT descended'})")
        n = len(man[tb]["devices"])
        subl = sorted({sub for _, _, sub in man[tb]["devices"] if sub})
        if missing or wrong:
            bad += 1
            print(f"FAIL: tb_{tb}.sch netlists {n - len(missing)} of {n} drawn instances; missing: "
                  f"{' '.join(missing) or 'none'}; wrong nodes: {'; '.join(wrong) or 'none'}")
        else:
            print(f"PASS: tb_{tb}.sch netlists every drawn instance on its nodes ({n}: sources, loads, "
                  f"{' + '.join(subl)} from {' / '.join(s + '.sch' for s in subl)})")
    return 1 if bad else 0


def main(argv):
    if argv[1:] == ["check"]:
        return check()
    os.makedirs(WORK, exist_ok=True)
    man = {}
    for tb, fn in (("op", tb_op), ("startup", tb_startup), ("mc", tb_mc), ("noise", tb_noise),
                   ("cmp", tb_cmp), ("xtalk", tb_xtalk)):
        man[tb] = fn()
    json.dump(man, open(MANIFEST, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
