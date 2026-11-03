#!/usr/bin/env python3
"""Emit tb_cell_tn.sch, the xschem drawing of the cell_trannoise bench.

    python3 tb_sch.py     -> tb_cell_tn.sch

The sheet draws the ngspice deck ct_bench.py writes at the nominal level
(POS 16.5): every ideal source with its tb_params.inc expression, XR through
../ramp_simple/ramp_simple.sym and XC through ../Analog_top/atop_cell.sym
(xschem descends into the blocks' own drawings: ramp_simple.sch; atop_cell.sch
-> sw_s0/1/2.sch, comparator_d.sch, latch.sym -> ../latch/latch.sch), CQ, and a
code block with the deck's cards (PDK models, standard-cell library,
tb_params.inc by absolute path, .temp, .options, the same `write` vectors).

Nothing is re-typed from memory: the terminals of every instance, the
subcircuit names, the cards and the `write` line are parsed from the deck
ct_bench.ngspice() returns; the symbol pins are read from the .sym files and
checked against the subcircuit port order of ../Analog_top/analog_top.spice;
each source's {expression} is evaluated against tb_params.inc and must equal
the number the deck carries. ct.sh (step `schematic`) netlists the drawing,
compares its instances and subcircuits with the deck and the macro, and
simulates both (ct_xtb.py).

Placement is hand-authored. Text on the sheet: the title, three headings and
the q load (root CLAUDE.md, "Schematic drawings").
"""
import os
import re
import sys
from pathlib import Path

BLOCK = Path(__file__).resolve().parent
MS = BLOCK.parent
sys.path.insert(0, str(BLOCK))
import ct_bench  # noqa: E402
from ct_common import evaluate, load_params  # noqa: E402

D = "/foss/designs/mixed_signal"
SYMS = {"ramp_simple": MS / "ramp_simple" / "ramp_simple.sym", "atop_cell": MS / "Analog_top" / "atop_cell.sym"}
MACRO = MS / "Analog_top" / "analog_top.spice"
RAW = "tb_cell_tn.raw"
T_TITLE, T_SUB, T_NOTE = 0.7, 0.5, 0.36

# each source's value as the tb_params.inc expression ngspice evaluates; checked
# below against the numbers ct_bench.sources() puts in the deck
EXPR = {
    "VAVDD": "{VDD}", "VDVDD": "{VDD}", "VVREF": "{VMID}", "VVRLO": "{VR_LO}", "VVIN": "{VIN}",
    "IRAMP": "{IRAMP}", "ICMP": "{IREF_CMP}",
    "VS2": "PULSE({VDD} 0 {TFIRST} {TEDGE} {TEDGE} {TRREL+NCNT*TCOUNT+10n-TEDGE} {PCONV})",
    "VS0": "PULSE({VDD} 0 {TFIRST+TNOV} {TEDGE} {TEDGE} {TRREL+NCNT*TCOUNT+10n-TEDGE-TNOV} {PCONV})",
    "VS1": "PULSE(0 {VDD} {TFIRST+2*TNOV} {TEDGE} {TEDGE} {TRREL+NCNT*TCOUNT-2*TNOV-TEDGE} {PCONV})",
    "VRST": "PULSE({VDD} 0 {TFIRST+TRREL} {TEDGE} {TEDGE} {NCNT*TCOUNT+5n-TEDGE} {PCONV})",
    "VCLK": "PULSE(0 {VDD} {TCLK0} {TEDGE} {TEDGE} {TCOUNT/2-TEDGE} {TCOUNT})",
}


def esc(s):
    return s.replace("{", "\\{").replace("}", "\\}").replace('"', '\\"')


def sym_pins(path):
    """[(pin, x, y)] in file order from a symbol's B 5 pin boxes."""
    pins = []
    for ln in open(path):
        m = re.match(r"B 5 (\S+) (\S+) (\S+) (\S+) \{name=(\w+)", ln)
        if m:
            x1, y1, x2, y2 = (float(v) for v in m.groups()[:4])
            pins.append((m.group(5), int(round((x1 + x2) / 2)), int(round((y1 + y2) / 2))))
    return pins


def subckt_ports(name):
    for ln in open(MACRO):
        t = ln.split()
        if len(t) > 2 and t[0].lower() == ".subckt" and t[1] == name:
            return t[2:]
    raise SystemExit("FAIL: tb_sch.py: no .subckt %s in %s" % (name, MACRO))


def parse_deck(text):
    """Instances (name -> nodes, kind, model) and cards of the deck."""
    inst, cards, write = {}, [], None
    for ln in text.splitlines():
        t = ln.split()
        if not t or t[0].startswith("*"):
            continue
        h = t[0]
        if h.startswith(".") or h in ("set", "tran", "quit"):
            if h.startswith(".") and h not in (".control", ".endc", ".end"):
                cards.append(ln.strip())
            continue
        if h == "write":
            write = t[2:]
            continue
        if h[0] in "VI":
            inst[h] = dict(kind=h[0], nodes=t[1:3])
        elif h[0] == "C":
            inst[h] = dict(kind="C", nodes=t[1:3])
        elif h[0] == "X":
            inst[h] = dict(kind="X", nodes=t[1:-1], model=t[-1])
    return inst, cards, write


class Sch:
    PINS = {"vsource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
            "isource": {"p": (0, -30, "U"), "m": (0, 30, "D")},
            "capa": {"p": (0, -30, "U"), "m": (0, 30, "D")}}
    SYM = {"vsource": "devices/vsource.sym", "isource": "devices/isource.sym", "capa": "devices/capa.sym"}
    STUB = 40

    def __init__(self):
        self.wires, self.inst, self.texts, self.n = [], [], [], 0
        self.at = {}          # label end point -> net: two nets on one point would be a silent short

    def label(self, x, y, net, text_left):
        if self.at.setdefault((x, y), net) != net:
            raise SystemExit("FAIL: tb_sch.py: labels %s and %s meet at (%d, %d)" % (self.at[(x, y)], net, x, y))
        self.n += 1
        self.inst.append("C {devices/lab_pin.sym} %d %d 0 %d {name=l%d sig_type=std_logic lab=%s}"
                         % (x, y, 0 if text_left else 1, self.n, net))

    def stub(self, px, py, d, net, length):
        ex, ey = {"U": (px, py - length), "D": (px, py + length), "L": (px - length, py), "R": (px + length, py)}[d]
        self.wires.append((px, py, ex, ey))
        self.label(ex, ey, net, d != "R")

    def part(self, kind, x, y, attrs, nets):
        self.inst.append("C {%s} %d %d 0 0 {%s}" % (self.SYM[kind], x, y, attrs))
        for pin, net in nets.items():
            dx, dy, d = self.PINS[kind][pin]
            self.stub(x + dx, y + dy, d, net, self.STUB)

    def block(self, sym, name, x, y, pins, nets, stub=60):
        """A block symbol by bare file name (found through xschemrc); every pin
        stubbed outward from the body to a net label."""
        self.inst.append("C {%s} %d %d 0 0 {name=%s}" % (sym, x, y, name))
        for (pin, px, py), net in zip(pins, nets):
            if px < 0:
                d = "L"
            elif px > 0:
                d = "R"
            else:
                d = "U" if py < 0 else "D"
            self.stub(x + px, y + py, d, net, stub if d in "LR" else self.STUB)

    def code(self, x, y, name, text):
        self.inst.append('C {devices/code_shown.sym} %d %d 0 0 {name=%s only_toplevel=false value="%s"}'
                         % (x, y, name, esc(text)))

    def T(self, s, x, y, size, layer=None):
        self.texts.append("T {%s} %d %d 0 0 %s %s {%s}" % (esc(s), x, y, size, size, "layer=%d" % layer if layer else ""))

    def write(self, path):
        body = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        body += ["N %d %d %d %d {}" % w for w in self.wires]
        body += self.texts + self.inst
        with open(path, "w", newline="\n") as h:
            h.write("\n".join(body) + "\n")
        print("REPORT: wrote %s: %d symbols, %d wires, %d texts" % (path.name, len(self.inst) - self.n,
                                                                    len(self.wires), len(self.texts)))


def check_values(P, inst):
    """Every drawn {expression} equals the number the deck carries."""
    bad = 0
    for name, a, b, kind, v in ct_bench.sources(P):
        name = name.upper()
        ex = EXPR[name]
        if kind == "pulse":
            args = re.match(r"PULSE\((.*)\)$", ex).group(1).split()
            got = [evaluate(x, P) for x in args]
            want = list(v)
        else:
            got, want = [evaluate(ex, P)], [v]
        for g, w in zip(got, want):
            if abs(g - w) > 1e-9 * max(abs(w), 1e-12):
                print("FAIL: tb_sch.py: %s: drawn %s evaluates to %s, the deck has %s" % (name, ex, got, want))
                bad += 1
                break
        if inst[name]["nodes"] != [a, b]:
            print("FAIL: tb_sch.py: %s terminals %s in the deck, sources() says %s" % (name, inst[name]["nodes"], [a, b]))
            bad += 1
    return bad


def main():
    P = load_params({"POS": 16.5, "NREC": 1})
    inst, cards, write = parse_deck(ct_bench.ngspice(P))
    if set(inst) - {"XR", "XC", "CQ"} != set(EXPR):
        raise SystemExit("FAIL: tb_sch.py: the deck's sources %s are not the drawn ones %s"
                         % (sorted(set(inst) - {"XR", "XC", "CQ"}), sorted(EXPR)))
    if check_values(P, inst):
        raise SystemExit(1)
    pins = {k: sym_pins(p) for k, p in SYMS.items()}
    for k, pl in pins.items():
        ports = subckt_ports(k)
        if [p[0] for p in pl] != ports:
            raise SystemExit("FAIL: tb_sch.py: %s.sym pins %s are not the macro's ports %s" % (k, [p[0] for p in pl], ports))
    assert inst["XR"]["model"] == "ramp_simple" and inst["XC"]["model"] == "atop_cell", (inst["XR"], inst["XC"])

    s = Sch()
    s.T("TB_CELL_TN  -  one bottom-plate cell on ramp_simple, transient noise of a conversion", 40, -1200, T_TITLE)
    s.T("SUPPLIES / REFS", 40, -1060, T_SUB, layer=4)
    s.T("CONTROLS", 40, -780, T_SUB, layer=4)
    s.T("CELL", 1500, -1060, T_SUB, layer=4)
    s.T("CQ = 40 fF", 3080, -650, T_NOTE, layer=4)

    # supplies, references, the level, the two bias currents
    row = ["VAVDD", "VDVDD", "VVREF", "VVRLO", "VVIN", "IRAMP", "ICMP"]
    for i, name in enumerate(row):
        kind = "isource" if name[0] == "I" else "vsource"
        x = 120 + 170 * i + (30 if name[0] == "I" else 0)
        a, b = inst[name]["nodes"]
        s.part(kind, x, -920, 'name=%s value="%s"%s' % (name, esc(EXPR[name]), "" if kind == "isource" else " savecurrent=false"),
               {"p": a, "m": b})
    # the switch controls, the ramp reset and the count clock, one per row
    for i, name in enumerate(["VS2", "VS0", "VS1", "VRST", "VCLK"]):
        a, b = inst[name]["nodes"]
        s.part("vsource", 120, -660 + 200 * i, 'name=%s value="%s" savecurrent=false' % (name, esc(EXPR[name])), {"p": a, "m": b})

    # the ramp, the cell, the q load
    s.block("ramp_simple.sym", "XR", 1740, -860, pins["ramp_simple"], inst["XR"]["nodes"])
    s.block("atop_cell.sym", "XC", 2600, -560, pins["atop_cell"], inst["XC"]["nodes"])
    a, b = inst["CQ"]["nodes"]
    s.part("capa", 3000, -640, 'name=CQ value="%s" m=1' % esc("{CQ}"), {"p": a, "m": b})

    # the deck's cards, its .include of the macro replaced by the hierarchy
    # xschem emits; tb_params.inc by absolute container path
    keep = [c for c in cards if not c.lower().startswith(".include") or "/foss/pdks" in c or "pdk_libs" in c]
    assert len(cards) - len(keep) == 1, cards
    code = "\n".join(keep[:-2] + [".include %s/cell_trannoise/tb_params.inc" % D] + keep[-2:]) + """
.csparam cs_tstop={TSTOP}
.control
set filetype=binary
tran 0.1n $&cs_tstop
write %s %s
quit
.endc""" % (RAW, " ".join(write))
    s.code(1000, -150, "CTL", code)
    s.write(BLOCK / "tb_cell_tn.sch")


if __name__ == "__main__":
    main()
