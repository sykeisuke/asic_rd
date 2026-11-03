#!/usr/bin/env python3
"""check_equiv.py -- the v7 macro netlist is the v6 one with the sampling
sequencer ../sample_seq inside, apart from nothing else.

    python3 check_equiv.py <v6 analog_top.spice> <v7 analog_top.spice>

Both netlists are flattened from subckt analog_top down to the PDK primitives,
the standard cells and the V / R elements. Every leaf device gets its
hierarchical path, model, parameters (keys case-folded, values normalised:
quotes / braces / spaces, engineering suffixes, m=1 default) and the net on
each terminal.

Declared v6 -> v7 differences (nothing else may differ; ADR 0027):
  * ports: the twelve switch controls s0_k, s1_k, s2_k leave the port list
    and become internal nets; acq (the controller's acquire level) is a new
    port after cnt_clk
  * devices: xseq.* (sample_seq: the standard-cell sequencer) is new; every v6
    device keeps its path, model and every parameter
  * xseq.* may touch only s0_k, s1_k, s2_k, acq, cnt_clk, dvdd, dvss
Connectivity is compared WITHOUT trusting names: every net is the set of
(device, terminal) pins on it. Each v6 net must have exactly one v7 net with
the same pins once the sequencer's pins (and, for the twelve former ports,
the port itself) are taken out.

One PASS:/FAIL: line per check, REPORT: lines with details; exit 1 on FAIL.
"""
import re
import sys


def nval(t):
    m = re.fullmatch(r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(meg|[tgkmunpf])?", t)
    if not m:
        return t
    mul = {"t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12,
           "f": 1e-15, None: 1}[m.group(2)]
    return "%.12g" % (float(m.group(1)) * mul)


def norm(v):
    v = re.sub(r"['\"\s]", "", v.lower()).replace("{", "").replace("}", "")
    return " ".join(nval(x) for x in re.split(r"([-+*/(),])", v) if x != "")


def squeeze(s):
    """Close up whitespace inside '...' and {...}, so a quoted expression is one token."""
    out, q, depth = [], False, 0
    for c in s:
        if c == "'":
            q = not q
        elif c == "{":
            depth += 1
        elif c == "}" and depth:
            depth -= 1
        if c in " \t" and (q or depth):
            continue
        out.append(c)
    return "".join(out)


def parse(path):
    lines = []
    for ln in open(path):
        ln = ln.rstrip("\n")
        if ln.startswith("+") and lines:
            lines[-1] += " " + ln[1:]
        else:
            lines.append(ln)
    subs, cur = {}, None
    for ln in lines:
        t = squeeze(ln).split()
        if not t or t[0].startswith("*"):
            continue
        h = t[0].lower()
        if h == ".subckt":
            cur = t[1].lower()
            subs[cur] = dict(ports=[x.lower() for x in t[2:] if "=" not in x], dev=[])
        elif h.startswith(".ends"):
            cur = None
        elif cur is not None and not h.startswith("."):
            subs[cur]["dev"].append(t)
    return subs


def flatten(subs, top="analog_top"):
    devs = {}

    def walk(name, prefix, netmap):
        for t in subs[name]["dev"]:
            inst = t[0].lower()
            kind = inst[0]
            pos = [x for x in t[1:] if "=" not in x]
            kv = {}
            for x in t[1:]:
                if "=" in x:
                    k, v = x.split("=", 1)
                    kv[k.lower()] = norm(v)
            path = prefix + inst
            if kind == "x":
                model = pos[-1].lower()
                nodes = pos[:-1]
            elif kind in "vrc":
                model = kind
                nodes = pos[:2]
                kv["value"] = norm(" ".join(pos[2:]))
            else:
                raise SystemExit("FAIL: equiv: unknown element " + t[0])
            nets = [netmap.get(n.lower(), prefix + n.lower()) if n != "0" else "0" for n in nodes]
            if kind == "x" and model in subs:
                sp = subs[model]["ports"]
                assert len(sp) == len(nets), (path, model)
                walk(model, path + ".", dict(zip(sp, nets)))
            else:
                kv.setdefault("m", "1")
                devs[path] = dict(model=model, params=kv, nets=nets)

    tp = subs[top]["ports"]
    walk(top, "", {p: "port:" + p for p in tp})
    return devs, tp


def pinsets(devs, skip):
    ps = {}
    for k, d in devs.items():
        if k in skip:
            continue
        for i, n in enumerate(d["nets"]):
            ps.setdefault(n, set()).add((k, i))
    for n in list(ps):
        if n.startswith("port:"):
            ps[n].add(("port", n[5:]))
    return ps


CTRL = ["s%d_%d" % (j, k) for j in range(3) for k in range(4)]
# the macro-level nets the sequencer may touch (v7 names)
SEQ_NETS = set(CTRL) | {"port:acq", "port:cnt_clk", "port:dvdd", "port:dvss"}


def own(path, n):
    """True if net n is internal to the instance that device path sits in."""
    return n.startswith(path.split(".")[0] + ".")


def main():
    v6p, v7p = sys.argv[1], sys.argv[2]
    d6, p6 = flatten(parse(v6p))
    d7, p7 = flatten(parse(v7p))
    st = 0
    # ---- ports
    want = [p for p in p6 if p not in CTRL]
    want.insert(want.index("cnt_clk") + 1, "acq")
    if p7 != want:
        print("FAIL: equiv: analog_top ports: v7 %s, expected %s" % (" ".join(p7), " ".join(want)))
        st = 1
    else:
        print("PASS: equiv: analog_top ports = v6's %d - the 12 switch controls + acq, v6's order (%d)"
              % (len(p6), len(p7)))
    # ---- devices
    new = {k for k in d7 if k.startswith("xseq.")}
    miss = sorted(set(d6) - set(d7))
    extra = sorted(set(d7) - new - set(d6))
    if not miss and not extra and new:
        cells = {}
        for k in new:
            cells[d7[k]["model"].split("__")[-1]] = cells.get(d7[k]["model"].split("__")[-1], 0) + 1
        print("PASS: equiv: %d leaf devices in v7 = v6's %d + sample_seq's %d standard cells (%s); every v6 "
              "device path kept" % (len(d7), len(d6), len(new),
                                     " ".join("%s x%d" % kv for kv in sorted(cells.items()))))
    else:
        print("FAIL: equiv: devices: %d v6 devices missing in v7 [%s], %d v7 devices not declared [%s], "
              "sequencer cells %d" % (len(miss), " ".join(miss[:8]), len(extra), " ".join(extra[:8]), len(new)))
        st = 1
    # ---- models and parameters of the common devices
    bad = []
    for k in sorted(set(d6) & (set(d7) - new)):
        a, b = d6[k], d7[k]
        if a["model"] != b["model"] or a["params"] != b["params"] or len(a["nets"]) != len(b["nets"]):
            bad.append(k)
            if len(bad) <= 6:
                diff = {q: (a["params"].get(q), b["params"].get(q)) for q in set(a["params"]) | set(b["params"])
                        if a["params"].get(q) != b["params"].get(q)}
                print("REPORT: equiv: %s v6 %s / v7 %s %s" % (k, a["model"], b["model"], diff))
    nmos = sum(1 for k in d7 if d7[k]["model"].startswith(("nfet", "pfet")))
    if bad:
        print("FAIL: equiv: %d devices differ in model or parameters [%s]" % (len(bad), " ".join(bad[:6])))
        st = 1
    else:
        print("PASS: equiv: every v6 device has v6's model and every parameter in v7 (%d MOS outside the "
              "standard cells: L W nf m and S/D geometry; R, C, V values)" % nmos)
    # ---- the nets the sequencer touches
    ext = sorted({n for k in new for n in d7[k]["nets"] if not own(k, n)})
    if set(ext) <= SEQ_NETS and set(CTRL) <= set(ext):
        print("PASS: equiv: sample_seq drives the 12 switch controls and touches only the declared nets: %s"
              % " ".join(ext))
    else:
        print("FAIL: equiv: sample_seq nets [%s]; undeclared [%s]; controls not driven [%s]"
              % (" ".join(ext), " ".join(sorted(set(ext) - SEQ_NETS)), " ".join(sorted(set(CTRL) - set(ext)))))
        st = 1
    # ---- connectivity by pin sets: the former control ports lose their port pin
    s6, s7 = pinsets(d6, set()), pinsets(d7, new)
    for c in CTRL:
        if "port:" + c in s6:
            s6["port:" + c].discard(("port", c))
    inv7 = {}
    for n, s in s7.items():
        inv7.setdefault(frozenset(s), []).append(n)
    unmatched, pairs = [], {}
    for n, s in s6.items():
        c = inv7.get(frozenset(s), [])
        if len(c) != 1:
            unmatched.append(n)
        else:
            pairs[n] = c[0]
    left = [n for n in s7 if n not in pairs.values() and n != "port:acq"]
    if unmatched or left:
        print("FAIL: equiv: connectivity: %d v6 nets have no v7 net with their remaining pins [%s]; %d v7 nets not "
              "in v6 [%s]" % (len(unmatched), " ".join(sorted(unmatched)[:8]), len(left), " ".join(left[:6])))
        st = 1
    else:
        print("PASS: equiv: connectivity: all %d v6 nets match v7's one-to-one by their (device, terminal) pins, "
              "the sequencer's pins taken out" % len(pairs))
    ren = {a: b for a, b in pairs.items() if a != b}
    declared = {"port:" + c: c for c in CTRL}
    if any(declared.get(a) != b for a, b in ren.items()):
        print("FAIL: equiv: net names: undeclared renames %s"
              % dict([(a, b) for a, b in ren.items() if declared.get(a) != b][:6]))
        st = 1
    else:
        print("PASS: equiv: net names equal to v6's apart from the 12 controls, now internal (%d renames, all "
              "declared)" % len(ren))
    print("equiv_n_devices = %d" % len(d7))
    print("equiv_n_sample_seq_cells = %d" % len(new))
    print("equiv_n_nets = %d" % len(pinsets(d7, set())))
    return st


if __name__ == "__main__":
    sys.exit(main())
