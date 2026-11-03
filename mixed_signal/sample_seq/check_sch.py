"""The drawing netlists back to the deck: sample_seq.sch (xschem, hierarchical)
against sample_seq.spice, subcircuit by subcircuit.

    python3 check_sch.py sample_seq.spice work/sample_seq_sch.spice

For every subcircuit of the deck (seq_dly, seq_cell, sample_seq) the xschem
netlist must hold the same port SET (xschem orders ports by its own rule; the
order is reported) and the same instances: name, cell, and the net on every
named pin. A subcircuit instance's pins are named through that file's own
port order, so a port reordering cannot hide a wrong connection. The top
sheet is written by xschem as the top level with its ports on the commented
`**.subckt` line. Prints PASS:/FAIL: lines; exits non-zero on failure.
"""
import re
import sys

LIBPINS = {
    "gf180mcu_as_sc_mcu7t3v3__dlybuff_2": ["VDD", "VNW", "VPW", "VSS", "Y", "A"],
    "gf180mcu_as_sc_mcu7t3v3__clkbuff_4": ["VDD", "VNW", "VPW", "VSS", "A", "Y"],
    "gf180mcu_as_sc_mcu7t3v3__dfxtp_2": ["VDD", "VNW", "VPW", "VSS", "CLK", "D", "Q"],
    "gf180mcu_as_sc_mcu7t3v3__nor2_2": ["VDD", "VNW", "VPW", "VSS", "Y", "B", "A"],
    "gf180mcu_as_sc_mcu7t3v3__xor2_2": ["VDD", "VNW", "VPW", "VSS", "B", "A", "Y"],
    "gf180mcu_as_sc_mcu7t3v3__nor3_2": ["VDD", "VNW", "VPW", "VSS", "A", "B", "C", "Y"],
    "gf180mcu_as_sc_mcu7t3v3__nand4_2": ["VDD", "VNW", "VPW", "VSS", "A", "B", "C", "D", "Y"],
    "gf180mcu_as_sc_mcu7t3v3__and2_2": ["VDD", "VNW", "VPW", "VSS", "B", "A", "Y"],
    "gf180mcu_as_sc_mcu7t3v3__dlxtn_2": ["VDD", "VNW", "VPW", "VSS", "ENA", "D", "Q"],
}


def parse(path, top=None):
    subs, cur = {}, None
    lines = []
    for raw in open(path):
        raw = raw.rstrip("\n")
        if raw.startswith("+") and lines:
            lines[-1] += " " + raw[1:]
        else:
            lines.append(raw)
    for l in lines:
        t = l.split()
        if not t:
            continue
        low = t[0].lower()
        if low == ".subckt" or (top and low == "**.subckt" and len(t) > 1 and t[1] == top):
            cur = t[1]
            subs[cur] = {"ports": [p.lower() for p in t[2:]], "inst": {}}
        elif low.startswith(".ends"):
            cur = None
        elif cur and low.startswith("x"):
            subs[cur]["inst"][t[0].lower()] = (t[-1], [n.lower() for n in t[1:-1]])
    if top and top in subs:
        pass
    return subs


def pinmap(cell, nodes, subs):
    names = LIBPINS.get(cell) or (subs[cell]["ports"] if cell in subs else None)
    if names is None or len(names) != len(nodes):
        return None
    return {n.lower(): v for n, v in zip(names, nodes)}


def main():
    deck = parse(sys.argv[1])
    sch = parse(sys.argv[2], top="sample_seq")
    bad = 0
    for name, d in deck.items():
        x = sch.get(name)
        if x is None:
            print("FAIL: schematic: subcircuit %s missing from the xschem netlist" % name)
            bad = 1
            continue
        if set(d["ports"]) != set(x["ports"]):
            print("FAIL: schematic: %s ports %s vs drawn %s" % (name, d["ports"], x["ports"]))
            bad = 1
            continue
        order = "same order" if d["ports"] == x["ports"] else "drawn order %s" % " ".join(x["ports"])
        diffs = []
        for iname, (cell, nodes) in d["inst"].items():
            if iname not in x["inst"]:
                diffs.append("%s missing" % iname)
                continue
            xc, xn = x["inst"][iname]
            if xc.lower() != cell.lower():
                diffs.append("%s cell %s vs %s" % (iname, cell, xc))
                continue
            a, b = pinmap(cell, nodes, deck), pinmap(xc, xn, sch)
            if a is None or b is None or a != b:
                diffs.append("%s pins %s vs %s" % (iname, a, b))
        extra = sorted(set(x["inst"]) - set(d["inst"]))
        if extra:
            diffs.append("extra instances %s" % extra)
        if diffs:
            print("FAIL: schematic: %s differs: %s" % (name, "; ".join(diffs[:6])))
            bad = 1
        else:
            print("PASS: schematic: %s netlists back to the deck, %d instances, ports equal as a set (%s)"
                  % (name, len(d["inst"]), order))
    sys.exit(bad)


if __name__ == "__main__":
    main()
