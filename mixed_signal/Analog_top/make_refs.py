#!/usr/bin/env python3
"""make_refs.py -- the expected subcircuits of the three cells v5 derives from
block drawings, built from the blocks' own DECKS (not from their drawings), so
that schematic.sh can check what xschem netlists from the v5 drawings:

  work/sch/ref_comparator_d.spice   ../comparator/comparator.spice
                                    subckt cmp with the ports inp inn ibias dout
                                    vdd vss (pbias -> ibias; the no-connects clk,
                                    nbias dropped) + XREFP (the diode of every
                                    comparator bench: pfet 1 / 0.28 um)
  work/sch/ref_ramp_simple_d.spice  ../ramp_gen/ramp_simple.spice subckt
                                    ramp_simple with every {RS_*} replaced by its
                                    value (../ramp_gen/data/ramp_simple_params.spice),
                                    pbias -> ibias + XRD (pfet 20 / 1 um nf 10)
  work/sch/ref_bias_gen_s.spice   ../bias_gen/bias_gen.spice subckt
                                    bias_gen - port ivbl - XOB (v5: one
                                    VDD/2 buffer) + port ivrlo + XOL (the
                                    parameters analog_top_sch.py draws)

    python3 make_refs.py
"""
import os
import re

from analog_top_sch import XOL

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.dirname(HERE)
OUT = os.path.join(HERE, "work", "sch")


def getsub(path, name):
    lines, on = [], False
    for ln in open(path):
        t = ln.split()
        if t and t[0].lower() == ".subckt" and t[1].lower() == name:
            on = True
        if on:
            lines.append(ln.rstrip("\n"))
            if t and t[0].lower().startswith(".ends"):
                break
    assert lines, (path, name)
    return lines


def rename_net(line, a, b):
    return " ".join(b if tok == a else tok for tok in line.split())


def main():
    os.makedirs(OUT, exist_ok=True)
    # comparator
    src = getsub(os.path.join(MS, "comparator", "comparator.spice"), "cmp")
    assert src[0].split() == [".subckt", "cmp", "inp", "inn", "dout", "clk", "vdd", "vss", "nbias", "pbias"], src[0]
    body = [rename_net(ln, "pbias", "ibias") for ln in src[1:-1]]
    assert not any(t in ("clk", "nbias") for ln in body for t in ln.split()), "clk / nbias used in cmp"
    with open(os.path.join(OUT, "ref_comparator_d.spice"), "w") as f:
        f.write("\n".join([".subckt comparator_d inp inn ibias dout vdd vss"] + body
                          + ["XREFP ibias ibias vdd vdd pfet_03v3 L=0.28u W=1u nf=1 m=1", ".ends comparator_d"]) + "\n")
    # ramp
    rs = {}
    for ln in open(os.path.join(MS, "ramp_gen", "data", "ramp_simple_params.spice")):
        mm = re.match(r"\s*\.param\s+(RS_\w+)\s*=\s*(\S+)", ln)
        if mm:
            rs[mm.group(1)] = mm.group(2)
    src = getsub(os.path.join(MS, "ramp_gen", "ramp_simple.spice"), "ramp_simple")
    assert src[0].split() == [".subckt", "ramp_simple", "vramp", "rst", "vrlo", "pbias", "vdd", "vss"], src[0]
    body = []
    for ln in src[1:-1]:
        ln = re.sub(r"\{(RS_\w+)\}", lambda mm: rs[mm.group(1)], ln)
        body.append(rename_net(ln, "pbias", "ibias"))
    assert not any("{" in ln for ln in body)
    with open(os.path.join(OUT, "ref_ramp_simple_d.spice"), "w") as f:
        f.write("\n".join([".subckt ramp_simple_d vramp rst vrlo ibias vdd vss",
                           "XRD ibias ibias vdd vdd pfet_03v3 L=1u W=20u nf=10 m=1"] + body
                          + [".ends ramp_simple_d"]) + "\n")
    # bias generator
    src = getsub(os.path.join(MS, "bias_gen", "bias_gen.spice"), "bias_gen")
    hdr = src[0].split()
    assert hdr[2:] == ["vdd", "vss", "icmp0", "icmp1", "icmp2", "icmp3", "iramp", "ivref", "ivbl"], hdr
    body = [ln for ln in src[1:-1] if not ln.split() or ln.split()[0] != "XOB"]
    assert len(body) == len(src) - 3, "XOB not found exactly once"
    assert not any("ivbl" in ln.split() for ln in body), "ivbl used by another device"
    p = XOL
    xol = ("XOL ivrlo pb vdd vdd pfet_03v3 L=%s W=%s nf=%s m=%s ad=%s pd=%s as=%s ps=%s nrd=%s nrs=%s"
           % (p["L"], p["W"], p["nf"], p["m"], p["ad"], p["pd"], p["as"], p["ps"], p["nrd"], p["nrs"]))
    with open(os.path.join(OUT, "ref_bias_gen_s.spice"), "w") as f:
        f.write("\n".join([" ".join([".subckt", "bias_gen_s"] + hdr[2:-1] + ["ivrlo"])] + body
                          + [xol, ".ends bias_gen_s"]) + "\n")
    print("REPORT: make_refs: wrote work/sch/ref_comparator_d.spice, ref_ramp_simple_d.spice, ref_bias_gen_s.spice "
          "from the block decks (XOL: %s)" % xol)


if __name__ == "__main__":
    main()
