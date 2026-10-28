#!/usr/bin/env python3
"""pwr_bench.py -- write the pwr phase's bench: work/pwr/tb_pwr.spice is
tb_analog_top.spice (the same circuit, sources, rshunt aid and models, the same
timeline) with its tb_measure.inc replaced by work/pwr/tb_pwr.inc, which holds

  * the same .options and .tran as tb_measure.inc (reltol 1e-4, gmin 1e-15,
    0.1 ns / 2 ns ceiling, to TSTOP)
  * .save of the supply-side branch currents in BRANCHES, the eight block
    ammeters, the two supplies and each cell's dout
  * the timeline echoed as p_* measures (pwr_reduce.py never re-derives it)
  * in .control: wrdata work/pwr/pwr.csv, one column per vector in COLUMNS order

A "branch" is a device or resistor whose terminal sits on the block's AVDD:
every microamp a block draws from AVDD enters through one of them. The sum of
a block's branches is checked against its ammeter in pwr_reduce.py; what is
left over is displacement current (MIM / junction / gate charge to AVDD).

    python3 pwr_bench.py       (cwd = this block; pwr.sh calls it)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "work", "pwr")
BLOCK_ABS = "/foss/designs/mixed_signal/Analog_top"

# block key -> (ammeter vector, label)
BLOCKS = [
    ("bg", "i(v.xdut.vmbg)", "bias_gen_s"),
    ("ref", "i(v.xdut.vmref)", "midref_div + XVREF (vref = vbl)"),
    ("vrlo", "i(v.xdut.vmvrlo)", "vrlo_ref"),
    ("ramp", "i(v.xdut.vmramp)", "ramp_simple_d"),
    ("c0", "i(v.xdut.vmc0)", "cell 0"),
    ("c1", "i(v.xdut.vmc1)", "cell 1"),
    ("c2", "i(v.xdut.vmc2)", "cell 2"),
    ("c3", "i(v.xdut.vmc3)", "cell 3"),
]


def _m(path):
    return "@m.xdut.%s.m0[id]" % path


def _r(path):
    return "@r.xdut.%s.rt1[i]" % path


# (block, key, vector, where the current goes). Positive = drawn from AVDD
# (BSIM4 id is type-normalised: positive into a PMOS source from VDD).
BRANCHES = [
    ("bg", "xmp1", _m("xbg.xmp1"), "core PMOS mirror -> XMN1 diode (nb)"),
    ("bg", "xmp2", _m("xbg.xmp2"), "core PMOS diode pb -> XMN2 (K=8) -> 5 x ppolyf_u"),
    ("bg", "xov", _m("xbg.xov"), "ivref source -> XVREF bias diode XMBN"),
    ("bg", "xol", _m("xbg.xol"), "ivrlo source -> vrlo_ref bias diode XMBN"),
    ("bg", "xsb1", _m("xbg.xsb1"), "start-up bleeder chain -> XSU4"),
    ("ref", "div", _r("xdiv.xrt"), "VDD/2 divider 2 x 204 kohm"),
    ("ref", "vref_xmbp", _m("xvref.xmbp"), "XVREF pb diode (<- XMBN2 mirror)"),
    ("ref", "vref_xmit", _m("xvref.xmit"), "XVREF PMOS source -> a -> XM4 NMOS follower -> XM5 out diode"),
    ("ref", "vref_xm3", _m("xvref.xm3"), "XVREF FVF PMOS -> p -> XM1 follower + XM2 out diode"),
    ("vrlo", "div", _r("xvrlo.xr1"), "5/33 tap divider 33 x 63 kohm"),
    ("vrlo", "xmbp", _m("xvrlo.xmbp"), "pb diode (<- XMBN2 mirror)"),
    ("vrlo", "xmt", _m("xvrlo.xmt"), "OTA tail -> XM1/XM2 -> XM3/XM4/XM5"),
    ("vrlo", "xmk", _m("xvrlo.xmk"), "keep-alive source into vrlo -> XMS shunt"),
    ("ramp", "xrd", _m("xramp.xrd"), "iramp diode (sunk by bias_gen XOR)"),
    ("ramp", "xps", _m("xramp.xps"), "ramp current -> 4 pF MIM (reset: XRST -> vrlo)"),
]
for k in range(4):
    c = "c%d" % k
    BRANCHES += [
        (c, "xrefp", _m("x%s.xcmp.xrefp" % c), "icmp diode (sunk by bias_gen XOC%d)" % k),
        (c, "xtail", _m("x%s.xcmp.xtail" % c), "comparator tail -> XINP/XINN -> NMOS loads"),
        (c, "xbst", _m("x%s.xcmp.xbst" % c), "starved inverter source -> XBUF2 / XBUF1"),
        (c, "xbuf4", _m("x%s.xcmp.xbuf4" % c), "output inverter PMOS -> dout / XBUF3"),
        (c, "xi0p", _m("x%s.xi0p" % c), "s0 control inverter PMOS (S0 PMOS gate)"),
        (c, "xi1p", _m("x%s.xi1p" % c), "s1 control inverter PMOS (S1 PMOS gate)"),
        (c, "xi2p", _m("x%s.xi2p" % c), "s2 control inverter PMOS (s2b, unused load)"),
    ]

# not on AVDD, saved to show where a branch splits (informative only)
SPLITS = []
for k in range(4):
    c = "c%d" % k
    SPLITS += [
        (c, "xinp", _m("x%s.xcmp.xinp" % c), "tail -> inp leg (gate vbl)"),
        (c, "xinn", _m("x%s.xcmp.xinn" % c), "tail -> inn leg (gate bot)"),
        (c, "xbuf1", _m("x%s.xcmp.xbuf1" % c), "starved inverter NMOS (crowbar when it equals xbst)"),
        (c, "xbuf3", _m("x%s.xcmp.xbuf3" % c), "output inverter NMOS (crowbar when it equals xbuf4)"),
    ]

SUPPLIES = [("avdd", "i(vavdd)"), ("dvdd", "i(vdvdd)")]
DOUT = [("dout%d" % k, "v(xdut.xc%d.dout)" % k) for k in range(4)]
# wrdata column order (after the single time column)
COLUMNS = ([("sup_" + k, v) for k, v in SUPPLIES]
           + [("amm_" + k, v) for k, v, _ in BLOCKS]
           + [("br_%s_%s" % (b, k), v) for b, k, v, _ in BRANCHES]
           + [("sp_%s_%s" % (b, k), v) for b, k, v, _ in SPLITS]
           + DOUT)
TIMELINE = ["VDD", "T0", "TS0", "TS1", "TS2", "TS3", "TNOV", "TR", "TE", "TOVR",
            "TSTOP", "TCOUNT"]


def main():
    os.makedirs(W, exist_ok=True)
    deck = open(os.path.join(HERE, "tb_analog_top.spice")).read().splitlines()
    out, n = [], 0
    for ln in deck:
        if ln.strip().lower().startswith(".include") and ln.strip().endswith("tb_measure.inc"):
            out.append(".include %s/work/pwr/tb_pwr.inc" % BLOCK_ABS)
            n += 1
        else:
            out.append(ln)
    assert n == 1, "tb_analog_top.spice must include tb_measure.inc exactly once"
    out[0] = "* tb_pwr -- GENERATED by pwr_bench.py from tb_analog_top.spice (pwr phase); " + out[0].lstrip("* ")
    open(os.path.join(W, "tb_pwr.spice"), "w", newline="\n").write("\n".join(out) + "\n")

    L = ["* tb_pwr.inc -- GENERATED by pwr_bench.py. Supply-side branch currents over the record.",
         ".options reltol=1e-4 gmin=1e-15",
         ".tran 0.1n {TSTOP} 0 2n"]
    vecs = [v for _, v in COLUMNS]
    for i in range(0, len(vecs), 6):
        L.append((".save " if i == 0 else "+ ") + " ".join(vecs[i:i + 6]))
    for p in TIMELINE:
        L.append(".measure tran p_%s PARAM='%s'" % (p.lower(), p))
    L += [".control", "set num_threads=1", "set wr_singlescale", "set wr_vecnames", "run",
          "wrdata pwr.csv " + " ".join(vecs), "quit", ".endc"]
    open(os.path.join(W, "tb_pwr.inc"), "w", newline="\n").write("\n".join(L) + "\n")
    print("REPORT: pwr: wrote work/pwr/tb_pwr.spice + tb_pwr.inc: %d branches on AVDD, "
          "%d split devices, %d ammeters, %d columns" % (len(BRANCHES), len(SPLITS), len(BLOCKS), len(COLUMNS)))


if __name__ == "__main__":
    main()
