"""The xschem testbench tb_cell_tn.sch against the hand bench (ct.sh step
`schematic`). Three comparisons, one PASS:/FAIL: line each, exit 1 on a FAIL:

    python3 ct_xtb.py instances <deck.spice> <xschem.spice>
        the netlist xschem wrote carries exactly the deck's top-level
        instances: the same names, the same terminals in order, the same
        subcircuit on every X line (case-insensitive). Values are not compared
        here (the deck has numbers, the drawing {expressions}); the simulation
        below is their proof.
    python3 ct_xtb.py subckts <analog_top.spice> <xschem.spice>
        every subcircuit xschem emitted from the hierarchy (ramp_simple,
        atop_cell, sw_s0/1/2, comparator_d, latch) equals the same subcircuit
        of the macro netlist: ports in order and the multiset of device lines
        (instance order and case ignored); and the set emitted is exactly the
        expected one.
    python3 ct_xtb.py compare <ref r.csv> <sch r.csv>
        ct_extract.py rows of the hand deck and of the xschem netlist, one
        record at the same POS: the decision time td (first fall of xc.dout
        through VDD/2 after TR) and the q fall time tq within 1 ns.
"""
import sys

EXPECT = {"ramp_simple", "atop_cell", "sw_s0", "sw_s1", "sw_s2", "comparator_d", "latch"}


def lines(path):
    """Logical lines: '+' continuations joined, comments and blanks dropped."""
    out = []
    for ln in open(path):
        ln = ln.rstrip("\n").rstrip("\r")
        if ln.startswith("+") and out:
            out[-1] += " " + ln[1:].strip()
        elif ln.strip() and not ln.lstrip().startswith("*"):
            out.append(ln.strip())
    return out


def split_netlist(path):
    """(top-level device lines, {subckt: (ports, [device lines])})."""
    top, subs, cur, ctl = [], {}, None, False
    for ln in lines(path):
        t = ln.split()
        h = t[0].lower()
        if h == ".control":
            ctl = True
            continue
        if h == ".endc":
            ctl = False
            continue
        if ctl:
            continue
        if h == ".subckt":
            cur = t[1].lower()
            subs[cur] = (tuple(x.lower() for x in t[2:]), [])
            continue
        if h.startswith(".ends"):
            cur = None
            continue
        if h.startswith("."):
            continue
        if cur:
            subs[cur][1].append(ln)
        else:
            top.append(ln)
    return top, subs


def norm(ln):
    return " ".join(ln.lower().split())


def devices(top):
    d = {}
    for ln in top:
        t = ln.split()
        name = t[0].upper()
        if name[0] == "X":
            d[name] = ("X", tuple(x.lower() for x in t[1:-1]), t[-1].lower())
        elif name[0] in "VIRC":
            d[name] = (name[0], tuple(x.lower() for x in t[1:3]), None)
    return d


def cmd_instances(ref, sch):
    a, b = devices(split_netlist(ref)[0]), devices(split_netlist(sch)[0])
    bad = []
    for n in sorted(set(a) | set(b)):
        if n not in b:
            bad.append("%s only in the deck" % n)
        elif n not in a:
            bad.append("%s only in the xschem netlist (symbol not found, or an extra part)" % n)
        elif a[n] != b[n]:
            bad.append("%s deck %s / xschem %s" % (n, a[n], b[n]))
    print("sch_instances = %d" % len(b))
    if bad:
        for s in bad[:8]:
            print("REPORT: schematic: instances: " + s)
        print("FAIL: schematic: tb_cell_tn.sch top level: %d mismatch(es) against the ct_bench.py deck (%d / %d instances)"
              % (len(bad), len(a), len(b)))
        return 1
    xs = sorted("%s %s" % (n, a[n][2]) for n in a if a[n][0] == "X")
    print("PASS: schematic: tb_cell_tn.sch top level carries exactly the ct_bench.py deck's %d instances "
          "(names, terminals in order, subcircuits: %s; %d V/I sources, %d capacitor)"
          % (len(a), ", ".join(xs), sum(1 for n in a if a[n][0] in "VI"), sum(1 for n in a if a[n][0] == "C")))
    return 0


def cmd_subckts(macro, sch):
    ref, got = split_netlist(macro)[1], split_netlist(sch)[1]
    bad = []
    if set(got) != EXPECT:
        bad.append("subcircuits emitted %s, expected %s" % (sorted(got), sorted(EXPECT)))
    for s in sorted(set(got) & set(ref)):
        pa, da = ref[s]
        pb, db = got[s]
        if pa != pb:
            bad.append("%s ports macro %s / xschem %s" % (s, pa, pb))
        sa, sb = sorted(norm(x) for x in da), sorted(norm(x) for x in db)
        if sa != sb:
            only_a = sorted(set(sa) - set(sb))[:2]
            only_b = sorted(set(sb) - set(sa))[:2]
            bad.append("%s devices differ: macro-only %s, xschem-only %s" % (s, only_a, only_b))
    for s in sorted(set(got) - set(ref)):
        bad.append("%s is not a subcircuit of the macro netlist" % s)
    ndev = sum(len(d) for _, d in got.values())
    print("sch_subckt_devices = %d" % ndev)
    if bad:
        for s in bad[:8]:
            print("REPORT: schematic: subckts: " + s)
        print("FAIL: schematic: tb_cell_tn.sch hierarchy: %d difference(s) from ../Analog_top/analog_top.spice" % len(bad))
        return 1
    print("PASS: schematic: tb_cell_tn.sch hierarchy: %d subcircuits (%s), %d device lines, each equal to "
          "../Analog_top/analog_top.spice's (ports in order, devices as a set)" % (len(got), ", ".join(sorted(got)), ndev))
    return 0


def row0(path):
    hdr, vals = None, None
    for ln in open(path):
        t = ln.strip().split(",")
        if hdr is None:
            hdr = t
        elif t and t[0]:
            vals = [float(x) for x in t]
            break
    if hdr is None or vals is None:
        raise SystemExit("FAIL: schematic: no record in %s" % path)
    return dict(zip(hdr, vals))


def cmd_compare(ref, sch):
    a, b = row0(ref), row0(sch)
    st = 0
    for col, what in (("td", "decision (xc.dout falls through VDD/2 after TR)"), ("tq", "q fall")):
        dt = (b[col] - a[col]) * 1e9
        print("xtb_dt_%s_ns = %.6g" % ("decision" if col == "td" else "q", dt))
        print("xtb_%s_ref_ns = %.6g" % (col, a[col] * 1e9))
        ok = abs(dt) <= 1.0 and dt == dt
        print("%s: schematic: xschem netlist vs hand deck, %s: %.4f ns vs %.4f ns after TR, d = %+.4f ns (|d| <= 1 ns)"
              % ("PASS" if ok else "FAIL", what, b[col] * 1e9, a[col] * 1e9, dt))
        st |= not ok
    for col in ("nd", "nq"):
        if a[col] != b[col]:
            print("FAIL: schematic: %s count differs: deck %g, xschem %g" % (col, a[col], b[col]))
            st = 1
    return int(st)


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("instances", "subckts", "compare"):
        raise SystemExit(__doc__)
    return {"instances": cmd_instances, "subckts": cmd_subckts, "compare": cmd_compare}[sys.argv[1]](sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    sys.exit(main())
