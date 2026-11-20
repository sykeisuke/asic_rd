#!/usr/bin/env python3
"""check_equiv.py -- the current macro netlist is the previous one with the swapped
comparator (../comparator) in every cell, apart from nothing else.

    python3 check_equiv.py <previous analog_top.spice> <current analog_top.spice>

Both netlists are flattened from subckt analog_top down to the PDK primitives,
the standard cells and the V / R elements. Every leaf device gets its
hierarchical path, model, parameters (keys case-folded, values normalised:
quotes / braces / spaces, engineering suffixes, m=1 default) and the net on
each terminal.

Declared previous -> current differences (nothing else may differ):
  * ports: none (analog_top's port list is the previous record's, in its order)
  * devices: per cell k, xc<k>.xcmp.xbuf5 / xbuf6 are new (the comparator's
    added output inverter); each has the model and every parameter of
    xbuf3 / xbuf4 (they are copies); every previous device keeps its path, model and
    every parameter
  * comparator inputs: per cell, XCMP's inp / inn are swapped at the instance:
    the gate of xc<k>.xcmp.xinp is on the previous record's xinn gate net (the plate xc<k>.bot)
    and xinn's on the previous record's xinp gate net (vref)
  * new internal node xc<k>.xcmp.outc: the drains of xbuf3 / xbuf4 (on
    xc<k>.dout in the previous record) and the gates of xbuf5 / xbuf6, nothing else; the
    drains of xbuf5 / xbuf6 are on xc<k>.dout, their source / bulk on
    xbuf3's / xbuf4's
Connectivity is compared WITHOUT trusting names: every net is the set of
(device, terminal) pins on it. With the new devices' pins taken out, the
xinp / xinn gate pins exchanged and outc folded into dout, each previous net must
have exactly one current net with the same pins, and the same name.

One PASS:/FAIL: line per check, REPORT: lines with details; exit 1 on FAIL.
(the earlier version of this script, the sequencer change, is in
../Analog_top_bkp/Analog_top_v7_adr0031/check_equiv.py.)
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
                # par: the PDK MOS symbols (792ef670) write par=@m, the model's
                # mismatch-area multiplier; it is a difference only when it is not m
                if "par" in kv and norm(kv["par"]) == norm(kv["m"]):
                    del kv["par"]
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


CELLS = ["xc%d" % k for k in range(4)]
# MOS terminal order of the PDK subcircuits: d g s b
D, G, S, B = 0, 1, 2, 3


def main():
    v7p, v8p = sys.argv[1], sys.argv[2]
    d7, p7 = flatten(parse(v7p))
    d8, p8 = flatten(parse(v8p))
    st = 0

    def fail(msg):
        nonlocal st
        st = 1
        print("FAIL: equiv: " + msg)

    # ---- ports
    if p8 != p7:
        fail("analog_top ports: current %s, previous %s" % (" ".join(p8), " ".join(p7)))
    else:
        print("PASS: equiv: analog_top ports = the previous record's (%d, same order)" % len(p8))
    # ---- devices
    new = {"%s.xcmp.%s" % (c, x) for c in CELLS for x in ("xbuf5", "xbuf6")}
    miss = sorted(set(d7) - set(d8))
    extra = sorted(set(d8) - set(d7))
    if not miss and extra == sorted(new):
        print("PASS: equiv: %d leaf devices in the current netlist = the previous record's %d + 8 declared (xbuf5 / xbuf6 in each of the four "
              "comparators); every previous device path kept" % (len(d8), len(d7)))
    else:
        fail("devices: %d previous devices missing in current [%s]; current devices not in previous [%s], declared [%s]"
             % (len(miss), " ".join(miss[:8]), " ".join(extra[:10]), " ".join(sorted(new))))
    # ---- models and parameters of the common devices
    bad = []
    for k in sorted(set(d7) & set(d8)):
        a, b = d7[k], d8[k]
        if a["model"] != b["model"] or a["params"] != b["params"] or len(a["nets"]) != len(b["nets"]):
            bad.append(k)
            if len(bad) <= 6:
                diff = {q: (a["params"].get(q), b["params"].get(q)) for q in set(a["params"]) | set(b["params"])
                        if a["params"].get(q) != b["params"].get(q)}
                print("REPORT: equiv: %s previous %s / current %s %s" % (k, a["model"], b["model"], diff))
    nmos = sum(1 for k in d8 if d8[k]["model"].startswith(("nfet", "pfet")))
    if bad:
        fail("%d devices differ in model or parameters [%s]" % (len(bad), " ".join(bad[:6])))
    else:
        print("PASS: equiv: every previous device has its model and every parameter in the current netlist (%d MOS outside the "
              "standard cells: L W nf m and S/D geometry; R, C, V values)" % nmos)
    # ---- the added inverter: copies of xbuf3 / xbuf4, wired outc -> dout
    nb = []
    for c in CELLS:
        x = "%s.xcmp." % c
        dout, outc = "%s.dout" % c, "%s.xcmp.outc" % c
        for newd, old in (("xbuf5", "xbuf3"), ("xbuf6", "xbuf4")):
            n, o = d8.get(x + newd), d8.get(x + old)
            o7 = d7.get(x + old)
            if not (n and o and o7):
                nb.append("%s%s missing" % (x, newd))
                continue
            if n["model"] != o["model"] or n["params"] != o["params"]:
                nb.append("%s%s is not a copy of %s (%s / %s)" % (x, newd, old, n["model"], o["model"]))
            want = [dout, outc, o["nets"][S], o["nets"][B]]
            if n["nets"] != want:
                nb.append("%s%s nets %s, expected %s" % (x, newd, n["nets"], want))
            if o7["nets"][D] != dout or o["nets"][D] != outc or o["nets"][1:] != o7["nets"][1:]:
                nb.append("%s%s drain previous %s -> current %s (expected %s -> %s), other terminals %s -> %s"
                          % (x, old, o7["nets"][D], o["nets"][D], dout, outc, o7["nets"][1:], o["nets"][1:]))
        on = sorted((k, i) for k, dd in d8.items() for i, nn in enumerate(dd["nets"]) if nn == outc)
        won = sorted([(x + "xbuf3", D), (x + "xbuf4", D), (x + "xbuf5", G), (x + "xbuf6", G)])
        if on != won:
            nb.append("%s pins %s, expected %s" % (outc, on, won))
    if nb:
        fail("added inverter: " + "; ".join(nb[:6]))
    else:
        print("PASS: equiv: in each cell xbuf5 / xbuf6 have xbuf3's / xbuf4's model and every parameter, drains on "
              "dout, gates on the new node xcmp.outc (= the drains of xbuf3 / xbuf4, nothing else), source / bulk "
              "on xbuf3's / xbuf4's")
    # ---- the input swap at the instance
    sw = []
    for c in CELLS:
        x = "%s.xcmp." % c
        g7p, g7n = d7[x + "xinp"]["nets"][G], d7[x + "xinn"]["nets"][G]
        g8p, g8n = d8[x + "xinp"]["nets"][G], d8[x + "xinn"]["nets"][G]
        if not (g8p == g7n == "%s.bot" % c and g8n == g7p):
            sw.append("%s: xinp gate previous %s -> current %s, xinn gate previous %s -> current %s" % (c, g7p, g8p, g7n, g8n))
        else:
            ref = g8n
    if sw:
        fail("input swap: " + "; ".join(sw))
    else:
        print("PASS: equiv: in each cell the comparator's inputs are swapped at the instance: xinp's gate on the "
              "plate xc<k>.bot (previous: xinn's), xinn's gate on %s (previous: xinp's)" % ref)
    # ---- connectivity by pin sets, declared changes undone on the current side
    s7, s8 = pinsets(d7, set()), pinsets(d8, new)
    swap = {}
    for c in CELLS:
        swap[("%s.xcmp.xinp" % c, G)] = ("%s.xcmp.xinn" % c, G)
        swap[("%s.xcmp.xinn" % c, G)] = ("%s.xcmp.xinp" % c, G)
    s8 = {n: {swap.get(p, p) for p in s} for n, s in s8.items()}
    for c in CELLS:
        outc = "%s.xcmp.outc" % c
        s8.setdefault("%s.dout" % c, set()).update(s8.pop(outc, set()))
    inv8 = {}
    for n, s in s8.items():
        inv8.setdefault(frozenset(s), []).append(n)
    unmatched, pairs = [], {}
    for n, s in s7.items():
        cnd = inv8.get(frozenset(s), [])
        if len(cnd) != 1:
            unmatched.append(n)
        else:
            pairs[n] = cnd[0]
    left = [n for n in s8 if n not in pairs.values()]
    if unmatched or left:
        fail("connectivity: %d previous nets have no current net with their pins [%s]; %d current nets not in previous [%s]"
             % (len(unmatched), " ".join(sorted(unmatched)[:8]), len(left), " ".join(left[:6])))
    else:
        print("PASS: equiv: connectivity: all %d previous nets match the current netlist's one-to-one by their (device, terminal) pins, "
              "with the declared changes undone (new devices out, xinp / xinn gates exchanged, outc folded "
              "into dout)" % len(pairs))
    ren = {a: b for a, b in pairs.items() if a != b}
    if ren:
        fail("net names: undeclared renames %s" % dict(list(ren.items())[:6]))
    else:
        print("PASS: equiv: net names equal to the previous record's (0 renames); one new net per cell, xc<k>.xcmp.outc")
    print("equiv_n_devices = %d" % len(d8))
    print("equiv_n_new_devices = %d" % len(set(d8) - set(d7)))
    print("equiv_n_nets = %d" % len(pinsets(d8, set())))
    return st


if __name__ == "__main__":
    sys.exit(main())
