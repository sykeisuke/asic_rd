"""Write tb_analog_top.sch, the xschem testbench that draws the circuit of the
hand-written bench tb_analog_top.spice (sources, values and the DUT
connections are read from that deck, so the drawing cannot drift from it):

  * every source with its exact value / PWL / PULSE expression ({param} kept)
  * the macro XDUT through analog_top.sym; xschem descends into analog_top.sch,
    atop_cell.sch, comparator_d.sch, ramp_simple_d.sch, bias_gen_s.sch and
    every block's own drawing (midref_div, midref_buf, vrlo_ref, latch,
    sw_s0/1/2): the same hierarchy schematic.sh writes into analog_top.spice
  * CQ0..3 = {CQ} on q0..q3
  * code blocks: the deck's PDK model lines and the standard-cell library;
    the simulation aid .options rshunt=1e15 on its own, with
    why it is there; tb_params.inc / tb_measure.inc by absolute path

The deck's .include of analog_top.spice (REPLACED below) is left out on
purpose: the hierarchy emits those subcircuits itself, keeping it would
define them twice.

    ./container.sh 'python3 tb_sch.py'
"""
import os

from analog_top_sch import BLOCK, PIN, Sheet, sym_pins, T_TITLE, T_SUB, T_NOTE

DECK = os.path.join(BLOCK, "tb_analog_top.spice")
# deck includes whose subcircuits xschem's hierarchical netlist emits itself
REPLACED = ("analog_top.spice",)


def esc(v):
    return v.replace("{", "\\{").replace("}", "\\}")


def parse(path):
    lines = []
    for ln in open(path):
        ln = ln.rstrip("\n")
        if ln.startswith("+") and lines:
            lines[-1] += " " + ln[1:].strip()
        else:
            lines.append(ln)
    src, dut, caps, cards = [], None, [], []
    for i, ln in enumerate(lines):
        t = ln.split()
        if i == 0 or not t or t[0].startswith("*"):
            continue
        h = t[0].upper()
        if h.startswith("."):
            if h != ".END":
                cards.append(ln.strip())
        elif h.startswith("V"):
            src.append((t[0], t[1], t[2], " ".join(t[3:])))
        elif h.startswith("C"):
            caps.append((t[0], t[1], t[2], " ".join(t[3:])))
        elif h.startswith("X"):
            dut = (t[0], t[1:-1], t[-1])
    return src, dut, caps, cards


def main():
    src, dut, caps, cards = parse(DECK)
    assert dut and dut[2] == "analog_top", dut
    s = Sheet("tb_analog_top")
    # sources: supplies / clocks | ramp reset, acq ; vin last (long PWL)
    groups = [["VAVDD", "VDVDD", "VCLK"], ["VRST", "VACQ"]]
    byname = {v[0]: v for v in src}
    placed = set()
    for col, names in enumerate(groups):
        x = 120 + 720 * col
        for row, name in enumerate(names):
            nm, pos, neg, val = byname[name]
            y = -1500 + 200 * row
            p = s.vsrc(nm, x, y, esc(val))
            s.stub(p["p"], pos, dx=0, dy=-30)
            s.stub(p["m"], neg, dx=0, dy=30)
            placed.add(nm)
    rest = [v for v in src if v[0] not in placed]
    for row, (nm, pos, neg, val) in enumerate(rest):
        y = -380 + 200 * row
        p = s.vsrc(nm, 120, y, esc(val))
        s.stub(p["p"], pos, dx=0, dy=-30)
        s.stub(p["m"], neg, dx=0, dy=30)
    # the macro
    name, nodes, sym = dut
    dx, dy = 3200, -1000
    pins = sym_pins("analog_top.sym")
    pd = s.add("analog_top.sym", dx, dy, f"name={name}", pins)
    for (pin, (px, py)), net in zip(pins.items(), nodes):
        if px < 0:
            s.stub(pd[pin], net, dx=-60)
        elif px > 0:
            s.stub(pd[pin], net, dx=60)
        elif py < 0:
            s.stub(pd[pin], net, dx=0, dy=-40)
        else:
            s.stub(pd[pin], net, dx=0, dy=40)
    for k, (nm, pos, neg, val) in enumerate(caps):
        c = s.add("devices/capa.sym", 3560 + 140 * k, -700, f"name={nm} value={esc(val)} m=1", PIN["vsrc"])
        s.stub(c["p"], pos, dx=0, dy=-30)
        s.stub(c["m"], neg, dx=0, dy=30)
    # code blocks: models + the standard-cell library | the simulation aid | params + measures
    keep = [c for c in cards if not (c.lower().startswith(".include") and os.path.basename(c.split()[-1]) in REPLACED)]
    tail = [c for c in keep if c.split()[-1].endswith((".inc",))]
    aids = [c for c in keep if c.lower().startswith(".option")]
    head = [c for c in keep if c not in tail and c not in aids]
    s.inst.append('C {devices/code_shown.sym} 4300 -1500 0 0 {name=MODELS only_toplevel=false value="'
                  + esc("\n".join(head)) + '"}')
    s.inst.append('C {devices/code_shown.sym} 4300 -1150 0 0 {name=BENCH only_toplevel=false value="'
                  + esc("\n".join(tail)) + '"}')
    s.inst.append('C {devices/code_shown.sym} 4300 -850 0 0 {name=SIM_AIDS only_toplevel=false value="'
                  + esc("\n".join(aids)) + '"}')
    # text: title, column headings, the q load (CLAUDE.md, "Schematic drawings")
    s.text("CQ = 40 fF", 3480, -560, T_NOTE, layer=4)
    s.text("TB_ANALOG_TOP  -  one four-cell record of the analog macro from a cold supply", 120, -1900, T_TITLE)
    s.text("SUPPLIES / RAMP_RST / CNT_CLK", 40, -1680, T_SUB, layer=4)
    s.text("S2_k", 760, -1680, T_SUB, layer=4)
    s.text("S0_k", 1480, -1680, T_SUB, layer=4)
    s.text("S1_k", 2200, -1680, T_SUB, layer=4)
    s.text("VIN", 40, -540, T_SUB, layer=4)
    s.write(os.path.join(BLOCK, "tb_analog_top.sch"), "tb_analog_top", 120, 100)
    print(f"REPORT: wrote tb_analog_top.sch from tb_analog_top.spice: {len(src)} sources, {len(caps)} loads, "
          f"{len(keep)} cards ({len(cards) - len(keep)} deck includes replaced by the hierarchy)")


if __name__ == "__main__":
    main()
