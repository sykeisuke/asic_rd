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

from analog_top_sch import BLOCK, PIN, Sheet, sym_pins, T_TITLE, T_SUB, T_BODY, T_NOTE

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


ROLE = {
    "VAVDD": "avdd 0 -> 3.3 V in TPWR = 100 ns (cold start)",
    "VDVDD": "dvdd, same ramp (latches only)",
    "VRST": "ramp_rst HIGH until TR = 3.72 us (TS3 + 300 ns)",
    "VCLK": "cnt_clk 20 MHz, rising edge at TR",
}


def main():
    src, dut, caps, cards = parse(DECK)
    assert dut and dut[2] == "analog_top", dut
    s = Sheet("tb_analog_top")
    # sources: supplies / references / clocks | S2 | S0 | S1 ; vin last (long PWL)
    groups = [[n for n in ("VAVDD", "VDVDD", "VRST", "VCLK")],
              [f"VS2_{k}" for k in range(4)], [f"VS0_{k}" for k in range(4)], [f"VS1_{k}" for k in range(4)]]
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
    s.text("SIMULATION AID (testbench only, not in the macro):\n"
           "rshunt = 1e15 ohm from EVERY node to ground. Each bottom plate floats\n"
           "from S2 opening to the end of the record, and at t = 0 every switch is\n"
           "open, so the MIM plates have no DC path at the initial operating point.\n"
           "The macro carries no leak resistor (since v3). 1e-15 S x 3.3 V = 3.3 fA.",
           4300, -760, T_NOTE, layer=4)
    s.text("CQ0..CQ3 = CQ = 40 fF: the capture load on each q\n(digital capture pins + wire, tb_params.inc)",
           3480, -560, T_NOTE, layer=13)
    s.text("TB_ANALOG_TOP  -  one four-cell record of the analog macro (v5: every analog block inside, one VDD/2 buffer) from a cold supply", 120, -2160, T_TITLE)
    s.text("The circuit of tb_analog_top.spice, drawn by tb_sch.py from that deck: power-up, four samples 50 ns apart "
           "(TS0..TS3 = 3.30 .. 3.42 us),\n"
           "the shared ramp from TR = 3.72 us = TS3 + 300 ns (256 counts of 50 ns + 20 overrun) and the four trips. "
           "Levels: vin = 0.5 V + (16.5 / 80.5 / 160.5 / 240.5) LSB, LSB = 1.5 V / 256.\n"
           "Per cell k: S2_k falls at TS_k (THE SAMPLE), S0_k 5 ns later (isolate the top plate), S1_k rises 5 ns "
           "after that (top plate onto vramp); vin steps 20 ns after TS_k.\n"
           "Timeline and levels: tb_params.inc. Measures, analysis, output: tb_measure.inc. XDUT = analog_top.sym; "
           "xschem descends into analog_top.sch and every block below it.\n"
           "xtb.sh simulates this netlist and compares every measure with the hand bench (func phase): "
           "the drawing reproduces the deck.\n"
           "Since v4: no vrlo source. vrlo is made inside the macro by vrlo_ref (5/33 AVDD, ADR 0018), biased by "
           "bias_gen_s; the only ideal sources are the supplies, vin, the switch controls, ramp_rst and cnt_clk.",
           120, -2070, T_BODY)
    s.text("SUPPLIES / RAMP_RST / CNT_CLK", 40, -1680, T_SUB, layer=4)
    s.text("S2_k (opens first: sample)", 760, -1680, T_SUB, layer=4)
    s.text("S0_k (isolate)", 1480, -1680, T_SUB, layer=4)
    s.text("S1_k (top -> vramp)", 2200, -1680, T_SUB, layer=4)
    s.text("VIN: one level per cell", 40, -540, T_SUB, layer=4)
    for row, nm in enumerate(groups[0]):
        s.text(ROLE[nm], 200, -1520 + 200 * row, T_NOTE, layer=13)
    s.write(os.path.join(BLOCK, "tb_analog_top.sch"), "tb_analog_top", 120, 100)
    print(f"REPORT: wrote tb_analog_top.sch from tb_analog_top.spice: {len(src)} sources, {len(caps)} loads, "
          f"{len(keep)} cards ({len(cards) - len(keep)} deck includes replaced by the hierarchy)")


if __name__ == "__main__":
    main()
