"""check_intent.py -- the op phase's check that the currents written on the
drawings (intent.py) match the in-macro operating point (data/op_point.csv,
state trk: every cell tracking, each comparator at its trip point).

Each bias_gen_s output against its design value (PASS within intent.TOL), and
each comparator device against the comparator's design allocation: the
deviation is printed, FAIL only beyond the sanity bound intent.CMP_TOL (a
marker no longer describing the circuit). Prints XTAIL / XREFP (REPORT).

    python3 check_intent.py      (cwd = this block; op.sh calls it)
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import intent as I  # noqa: E402


def main():
    rows = {}
    with open(os.path.join(HERE, "data", "op_point.csv")) as f:
        for r in csv.DictReader(ln for ln in f if not ln.startswith("#")):
            if r["state"] == "trk":
                rows[r["key"]] = abs(float(r["id"])) * 1e6
    st = 0

    def gate(name, sim, want, tol=I.TOL):
        nonlocal st
        err = sim / want - 1
        ok = abs(err) <= tol
        st |= not ok
        print("%s: intent: %s %.2f uA in the op record vs %g uA design (%+.1f %%, %s %d %%)"
              % ("PASS" if ok else "FAIL", name, sim, want, 100 * err,
                 "gate" if tol == I.TOL else "sanity", round(100 * tol)))

    for out, keys in I.BIAS_DEV.items():
        for k in keys:
            if k not in rows:
                print("FAIL: intent: %s missing from data/op_point.csv" % k)
                st = 1
                continue
            gate("%s (%s)" % (out, k), rows[k], I.BIAS_UA[out])
    # op_devices.py records every comparator device of cell 0 and only XTAIL /
    # XREFP of cells 1..3 (identical cells): cell 0 must be complete
    unrec = []
    for c in range(4):
        for dev, want in I.CMP_UA.items():
            k = "c%d_%s" % (c, dev)
            if k not in rows:
                if c == 0:
                    print("FAIL: intent: %s missing from data/op_point.csv" % k)
                    st = 1
                else:
                    unrec.append(k)
                continue
            gate("cell %d %s" % (c, dev.upper()), rows[k], want, I.CMP_TOL)
        if "c%d_xrefp" % c in rows:
            gate("cell %d XREFP (icmp%d)" % (c, c), rows["c%d_xrefp" % c], I.BIAS_UA["icmp"])
    if unrec:
        print("REPORT: intent: not in the op record (cells 1..3 equal cell 0): %d devices" % len(unrec))
    if "c0_xtail" in rows and "c0_xrefp" in rows:
        print("REPORT: intent: in-macro XTAIL / XREFP = %.2f (11 fingers; design %.1f: %g uA at %.2f uA)"
              % (rows["c0_xtail"] / rows["c0_xrefp"], I.CMP.INTENT_UA["xtail"] / I.CMP.I_B_UA,
                 I.CMP.INTENT_UA["xtail"], I.CMP.I_B_UA))
    return st


if __name__ == "__main__":
    sys.exit(main())
