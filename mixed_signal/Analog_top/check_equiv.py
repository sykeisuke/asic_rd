#!/usr/bin/env python3
"""check_equiv.py -- the v5 macro netlist is the v4 one minus the second VDD/2
buffer, apart from nothing else.

    python3 check_equiv.py <v4 analog_top.spice> <v5 analog_top.spice>

Both netlists are flattened from subckt analog_top down to the PDK primitives
(nfet_03v3, pfet_03v3, cap_mim_2f0_m4m5_noshield, ppolyf_u, ppolyf_u_3k), the
standard cell and the V / R elements. Every leaf device gets its hierarchical
path, model, parameters (keys case-folded, values normalised: quotes / braces /
spaces, engineering suffixes, m=1 default) and the net on each terminal.

Declared v4 -> v5 differences (nothing else may differ; ADR 0021):
  * xvbl.* (the second midref_buf, 12 devices) is gone
  * xbg.xob (the bias_gen output that sourced ivbl into it) is gone, and with
    it the net ivbl
  * the nets vbl and vref are one net, named vref: every cell's vbl pin
    (comparator inp) is on the output of xvref
Connectivity is compared WITHOUT trusting names: every net is the set of
(device, terminal) pins on it. Each v4 net minus the removed devices' pins
(vbl and vref united) must have exactly one v5 net with that pin set; a v4
net left with no pins must be one of the removed devices' own nets.

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


def pinsets(devs):
    ps = {}
    for k, d in devs.items():
        for i, n in enumerate(d["nets"]):
            ps.setdefault(n, set()).add((k, i))
    for n in list(ps):
        if n.startswith("port:"):
            ps[n].add(("port", n[5:]))
    return ps


def main():
    v4p, v5p = sys.argv[1], sys.argv[2]
    d4, p4 = flatten(parse(v4p))
    d5, p5 = flatten(parse(v5p))
    st = 0
    # ---- ports
    if p5 != p4:
        print("FAIL: equiv: analog_top ports: v5 %s, v4 %s" % (" ".join(p5), " ".join(p4)))
        st = 1
    else:
        print("PASS: equiv: analog_top ports = v4's %d, in v4's order" % len(p4))
    # ---- devices
    removed = {k for k in d4 if k.startswith("xvbl.")} | {"xbg.xob"}
    n_xvbl = len([k for k in d4 if k.startswith("xvbl.")])
    miss = sorted(set(d4) - removed - set(d5))
    extra = sorted(set(d5) - set(d4))
    still = sorted(removed & set(d5))
    if miss or extra or still or n_xvbl != 12 or "xbg.xob" not in d4:
        print("FAIL: equiv: devices: %d v4 devices missing in v5 [%s], %d v5 devices not in v4 [%s], %d removed devices "
              "still present [%s]; v4 xvbl %d devices (12 expected), xbg.xob in v4 %s"
              % (len(miss), " ".join(miss[:8]), len(extra), " ".join(extra[:8]), len(still), " ".join(still[:4]),
                 n_xvbl, "xbg.xob" in d4))
        st = 1
    else:
        print("PASS: equiv: %d leaf devices in v5 = v4's %d - the 12 of xvbl (midref_buf) - xbg.xob; every other "
              "device path equal" % (len(d5), len(d4)))
    # ---- models and parameters of the common devices
    bad = []
    for k in sorted(set(d4) & set(d5)):
        a, b = d4[k], d5[k]
        if a["model"] != b["model"] or a["params"] != b["params"] or len(a["nets"]) != len(b["nets"]):
            bad.append(k)
            if len(bad) <= 6:
                diff = {q: (a["params"].get(q), b["params"].get(q)) for q in set(a["params"]) | set(b["params"])
                        if a["params"].get(q) != b["params"].get(q)}
                print("REPORT: equiv: %s v4 %s / v5 %s %s" % (k, a["model"], b["model"], diff))
    nmos = sum(1 for k in d5 if d5[k]["model"].startswith(("nfet", "pfet")))
    if bad:
        print("FAIL: equiv: %d devices differ in model or parameters [%s]" % (len(bad), " ".join(bad[:6])))
        st = 1
    else:
        print("PASS: equiv: every common device has v4's model and every parameter in v5 (%d MOS: L W nf m and S/D "
              "geometry; R, C, V values)" % nmos)
    # ---- connectivity by pin sets
    s4, s5 = pinsets(d4), pinsets(d5)
    exp = {}
    for n, s in s4.items():
        rest = {p for p in s if p[0] not in removed}
        key = "vref" if n in ("vbl", "vref") else n
        exp.setdefault(key, set()).update(rest)
    gone = sorted(n for n, s in exp.items() if not s)
    gone_bad = [n for n in gone if not all(p[0] in removed for p in s4[n])]
    inv5 = {}
    for n, s in s5.items():
        inv5.setdefault(frozenset(s), []).append(n)
    unmatched, pairs = [], {}
    for n, s in exp.items():
        if not s:
            continue
        c = inv5.get(frozenset(s), [])
        if len(c) != 1:
            unmatched.append(n)
        else:
            pairs[n] = c[0]
    new = [n for n in s5 if n not in pairs.values()]
    if unmatched or new or gone_bad:
        print("FAIL: equiv: connectivity: %d v4 nets have no v5 net with their remaining pins [%s]; %d v5 nets not in "
              "v4 [%s]; %d emptied nets touched kept devices [%s]"
              % (len(unmatched), " ".join(sorted(unmatched)[:8]), len(new), " ".join(new[:6]), len(gone_bad),
                 " ".join(gone_bad[:4])))
        st = 1
    else:
        print("PASS: equiv: connectivity: all %d v5 nets match v4's one-to-one by their (device, terminal) pins, with "
              "the removed devices' pins taken out and v4's vbl + vref united (%d pins: every cell's S2 and comparator "
              "inp, xvref's output); %d v4 nets vanish with the removed devices (%s)"
              % (len(pairs), len(exp["vref"]), len(gone), " ".join(gone[:6]) + (" ..." if len(gone) > 6 else "")))
    ren = {a: b for a, b in pairs.items() if a != b}
    if ren:
        print("FAIL: equiv: net names: undeclared renames %s" % dict(list(ren.items())[:6]))
        st = 1
    else:
        print("PASS: equiv: net names equal to v4's (vbl and vref are the one net vref)")
    vb = sorted(p for p in s4.get("vbl", ()) if p[0] not in removed)
    print("REPORT: equiv: v4's vbl pins now on vref: %s" % ", ".join("%s.%d" % p for p in vb))
    print("equiv_n_devices = %d" % len(d5))
    print("equiv_n_nets = %d" % len(s5))
    return st


if __name__ == "__main__":
    sys.exit(main())
