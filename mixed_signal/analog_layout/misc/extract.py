#!/usr/bin/env python3
"""Extract CMP_LP and write it as a drop-in replacement for cmp_lp.spice.

    make gf-comparator      # scripts/run-gf-comparator.sh runs this after DRC/LVS
    python3 misc/extract.py --names work/CMP_LP-lvs/CMP_LP.cir [TAG]
                            # pin/net-name check of an LVS extraction only

Runs kpex (2.5D engine, gf180mcuD) on build/gds/CMP_LP.gds against the
generated LVS reference build/CMP_LP.spice, then rewrites kpex's netlist
into build/CMP_LP_pex.spice so that the comparator_lp benches take it
unchanged in place of cmp_lp.spice:

- the same subcircuit name (`cmp`) and port order, read from cmp_lp.spice;
  clk and nbias stay unconnected ports, as they are there;
- the same instance names (XINP ... XBUF4) as PDK-subcircuit calls, so
  @m.xdut.xinp.m0[...] still resolves. kpex writes one M device per
  finger; the fingers of each transistor are merged back into one call
  with the summed W and junction geometry and nf = finger count, which
  keeps ngspice's bin choice the same as the pre-layout netlist's (it
  bins on total W);
- the same internal node names (left, tail, outa, outb, rep, bst), which
  the layout carries as labels;
- every coupling and ground capacitance kpex extracted, the substrate
  (kpex's VSUBS / gf180mcu_gnd) mapped to vss, which the layout taps it to;
- the two n-well junctions, which extraction does not produce, as linear
  capacitors from the drawn well and diode_nw2ps_03v3's typical zero-bias
  cjo and cjp: the clamp well on outa, the main well on vdd. Zero bias
  overstates a reverse-biased junction, i.e. errs slow.

COUTA is not carried over: it was the recipe's stand-in for exactly the
parasitics this file now lists.

Every figure of merit is one `name = value` line on stdout.
"""

import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
CELL = "CMP_LP"
GDS = os.path.join(OUT, "gds", CELL + ".gds")
REF = os.path.join(OUT, CELL + ".spice")
#- kpex turns every label into a top-level pin, so its own LVS gets the
#- reference with the labelled internal nets as ports as well
KPEX_REF = os.path.join(OUT, CELL + "_kpex.spice")
#- kpex keeps the substrate as its own net under this name rather than
#- merging it into vss through the taps, as ../signoff.py's LVS does
KPEX_SUB = "gf180mcu_gnd"
PEX_DIR = os.path.join(OUT, "pex")
DROPIN = os.path.join(OUT, CELL + "_pex.spice")
CMP_SOURCE = os.path.normpath(os.path.join(HERE, "..", "..", "comparator_lp", "cmp_lp.spice"))
MODELS = "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice"

SUBSTRATE = {"vsubs", "gf180mcu_gnd"}

sys.path.insert(0, HERE)
SI = {"a": 1e-18, "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3,
      "meg": 1e6, "g": 1e9}


def si(tok):
    m = re.fullmatch(r"([-+0-9.e]+)(meg|[afpnumkg])?", tok.strip().lower())
    if not m:
        raise ValueError(f"not a number: {tok}")
    return float(m.group(1)) * SI.get(m.group(2) or "", 1.0)


def logical_lines(path):
    """SPICE lines with '+' continuations joined, comments dropped."""
    out = []
    for raw in open(path):
        s = raw.rstrip("\n")
        if s.startswith("+") and out:
            out[-1] += " " + s[1:].strip()
        elif s.strip() and not s.lstrip().startswith("*"):
            out.append(s.strip())
    return out


def params(tokens):
    return {k.lower(): v for k, v in (t.split("=", 1) for t in tokens if "=" in t)}


def kpex_reference():
    """The reference as kpex's LVS needs it: the labelled internal nets as
    ports, and every transistor as its drawn fingers (kpex runs the PDK
    deck without device combination, so one nf=12 device would not match
    twelve extracted ones), written as M devices -- kpex reads the
    schematic without the PDK's X-to-M conversion that ../signoff.py
    applies, and an X line would be a call to an undefined subcircuit."""
    from gfp_misc.cells.comparator import DEVICES, INTERNAL_NETS
    with open(KPEX_REF, "w") as fo:
        for s in logical_lines(REF):
            t = s.split()
            if t[0].lower() == ".subckt":
                s += " " + " ".join(INTERNAL_NETS) + " " + KPEX_SUB
            elif t[0][0] in "Xx":
                p = params(t[6:])
                nf = DEVICES[t[0].upper()][3]
                wf = si(p["w"]) / nf
                if t[5].lower().startswith("nfet") and t[4] == "vss":
                    t[4] = KPEX_SUB
                s = "\n".join(f"M{t[0][1:]}_{i} {' '.join(t[1:6])} L={p['l']} W={wf * 1e6:.6g}u"
                              for i in range(nf))
            fo.write(s + "\n")


def run_kpex():
    kpex_reference()
    #- kpex caches its LVS database keyed on the GDS path, not on the
    #- schematic, and will reuse one from an earlier reference (measured:
    #- "Cache hit: Reusing cached LVSDB" after the reference changed). The
    #- whole directory, cache included, goes every run.
    for root, dirs, files in os.walk(PEX_DIR, topdown=False):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            os.rmdir(os.path.join(root, d))
    os.makedirs(os.path.join(PEX_DIR, "run"), exist_ok=True)
    #- kpex's LVS writes into the parent of its cwd (see ../pex.py, point 2)
    r = subprocess.run(["kpex", "--pdk", "gf180mcuD", "--gds", GDS, "--cell", CELL,
                        "--schematic", KPEX_REF, "--out_dir", PEX_DIR, "--2.5D"],
                       cwd=os.path.join(PEX_DIR, "run"), text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with open(os.path.join(PEX_DIR, "kpex-console.txt"), "w") as fo:
        fo.write(r.stdout)
    net = os.path.join(PEX_DIR, f"{CELL}__{CELL}", f"{CELL}_k25d_pex_netlist.spice")
    if r.returncode != 0 or not os.path.exists(net):
        errs = [ln.strip() for ln in r.stdout.splitlines()
                if re.search(r"error|exception|traceback", ln, re.I)]
        raise SystemExit(f"kpex failed on {CELL} (rc {r.returncode}): "
                         f"{errs[-1][:300] if errs else 'no error line'}; "
                         f"see {os.path.relpath(PEX_DIR, HERE)}/kpex-console.txt")
    #- kpex's console wraps lines, so "Congratulations!" and the verdict
    #- need not share one
    lvs = ("mismatch" if "don't match" in r.stdout
           else "match" if "Netlists match" in r.stdout else "unknown")
    return net, lvs


def net_name(n):
    n = n.replace("\\", "")
    if n.lower() in SUBSTRATE:
        return "vss"
    return ("n" + n[1:]) if n.startswith("$") else n


def read_reference():
    devs = {}
    for s in logical_lines(REF):
        if s[0] in "Xx":
            t = s.split()
            p = params(t[6:])
            devs[t[0].upper()] = {"d": t[1], "g": t[2], "s": t[3], "b": t[4], "model": t[5],
                                  "l": si(p["l"]), "w": si(p["w"]), "nf": int(p.get("nf", 1))}
    return devs


def read_kpex(path):
    ports, fingers, caps = [], [], defaultdict(float)
    for s in logical_lines(path):
        t = s.split()
        head = t[0].upper()
        if head == ".SUBCKT":
            ports = [net_name(x) for x in t[2:]]
        elif head.startswith("M"):
            p = params(t[6:])
            fingers.append({"d": net_name(t[1]), "g": net_name(t[2]), "s": net_name(t[3]),
                            "b": net_name(t[4]), "model": t[5],
                            **{k: si(p.get(k, "0")) for k in ("l", "w", "as", "ad", "ps", "pd")}})
        elif head.startswith("C"):
            a, b = sorted((net_name(t[1]), net_name(t[2])))
            if a != b:
                caps[(a, b)] += si(t[3])
        elif head.startswith((".ENDS", ".END")):
            continue
        else:
            raise SystemExit(f"unexpected element in kpex netlist: {s[:60]}")
    return ports, fingers, caps


def merge(fingers, ref, strict=True):
    """Group fingers onto reference devices by (model, L, gate, bulk, {S, D}).

    The signature is built from net NAMES, so this is also the pin check
    KLayout's LVS does not make: its compare pairs the top-level nets by
    topology and passes a layout whose inp and inn labels are exchanged
    (measured, the control in scripts/run-gf-comparator.sh). Returns the
    merged devices and the fingers that matched nothing; strict raises on
    the first of those instead."""
    key = lambda d: (d["model"].lower(), round(d["l"] * 1e9), d["g"], d["b"],  # noqa: E731
                     frozenset((d["d"], d["s"])))
    by_key = {key(r): name for name, r in ref.items()}
    if len(by_key) != len(ref):
        raise SystemExit("two reference devices share a signature; cannot merge fingers")
    out = {name: {"w": 0.0, "nf": 0, "as": 0.0, "ad": 0.0, "ps": 0.0, "pd": 0.0}
           for name in ref}
    unmatched = []
    for f in fingers:
        name = by_key.get(key(f))
        if name is None:
            if strict:
                raise SystemExit(f"extracted finger matches no reference device: {f}")
            unmatched.append(f)
            continue
        r, o = ref[name], out[name]
        o["w"] += f["w"]
        o["nf"] += 1
        flip = f["d"] != r["d"]
        o["ad"] += f["as"] if flip else f["ad"]
        o["as"] += f["ad"] if flip else f["as"]
        o["pd"] += f["ps"] if flip else f["pd"]
        o["ps"] += f["pd"] if flip else f["ps"]
    return (out, unmatched) if not strict else out


def names(netlist, tag):
    """Device-by-device, net-name-by-net-name comparison of an extracted
    layout netlist (KLayout LVS's <cell>.cir) with the LVS reference."""
    ref = read_reference()
    _, fingers, _ = read_kpex(netlist)
    merged, unmatched = merge(fingers, ref, strict=False)
    short = [d for d in ref if abs(merged[d]["w"] - ref[d]["w"]) > 1e-12]
    ok = not unmatched and not short
    low = CELL.lower()
    print(f"{low}_{tag}names = {'match' if ok else 'mismatch'}")
    print(f"{low}_{tag}names_unmatched_fingers = {len(unmatched)}")
    print(f"{low}_{tag}names_w_short = {','.join(short) or 'none'}")


def well_caps():
    """Typical zero-bias junction capacitance of each drawn n-well."""
    text = open(MODELS).read()
    m = re.search(r"\.model\s+diode_nw2ps_03v3\s+d\b(.*?)(?=\n\.)", text, re.S | re.I)
    if not m:
        raise SystemExit("diode_nw2ps_03v3 not found in the PDK models")
    card = m.group(1)
    cjo = float(re.search(r"cjo\s*=\s*'?([0-9.eE+-]+)", card, re.I).group(1))
    cjp = float(re.search(r"cjp\s*=\s*'?([0-9.eE+-]+)", card, re.I).group(1))
    import gf180mcu
    from gfp_misc.cells.comparator import CMP_LP
    gf180mcu.PDK.activate()
    info = CMP_LP().info
    out = {}
    for net in ("outa", "vdd"):
        area = info[f"nwell_{net}_area_um2"] * 1e-12
        perim = info[f"nwell_{net}_perim_um"] * 1e-6
        out[net] = cjo * area + cjp * perim
    return out, cjo, cjp


def source_subckt():
    for s in logical_lines(CMP_SOURCE):
        t = s.split()
        if t[0].lower() == ".subckt":
            return t[1], t[2:]
    raise SystemExit("no .subckt in cmp_lp.spice")


def main():
    if sys.argv[1:2] == ["--names"]:
        names(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
        return
    net, kpex_lvs = run_kpex()
    ref = read_reference()
    ports, fingers, caps = read_kpex(net)
    merged = merge(fingers, ref)
    wells, cjo, cjp = well_caps()
    name, src_ports = source_subckt()

    nets = {n for pair in caps for n in pair}
    for f in fingers:
        nets.update((f["d"], f["g"], f["s"], f["b"]))
    unnamed = sorted(n for n in nets if re.fullmatch(r"n\d+", n))
    from gfp_misc.cells.comparator import INTERNAL_NETS
    stray = sorted(n for n in nets if n not in set(src_ports) | set(INTERNAL_NETS))

    fmt = lambda v, u, s: f"{v / s:.6g}{u}"  # noqa: E731
    with open(DROPIN, "w") as fo:
        fo.write(
            "* CMP_LP extracted -- drop-in for comparator_lp/cmp_lp.spice.\n"
            "* GENERATED by mixed_signal/analog_layout/misc/extract.py from\n"
            "* misc/build/gds/CMP_LP.gds (kpex 2.5D, gf180mcuD) -- do not edit.\n"
            "* Same subcircuit name, port order, instance names and internal nodes\n"
            "* as cmp_lp.spice. Differences:\n"
            "*   COUTA removed: the extracted capacitances below replace it.\n"
            "*   nf is the drawn finger count (XLOADD/XLOADM 10, XTAIL 10, XBST 8);\n"
            "*   total W and L are cmp_lp.spice's. AS/AD/PS/PD are the drawn diffusions.\n"
            "*   CWELL_*: n-well junctions (not extracted by kpex), typical zero-bias\n"
            f"*   cjo {cjo:.5g} F/m2, cjp {cjp:.5g} F/m of diode_nw2ps_03v3.\n"
            "*   Substrate is vss (the layout taps it there).\n"
            f".subckt {name} {' '.join(src_ports)}\n")
        for dev in ref:
            r, m = ref[dev], merged[dev]
            fo.write(f"{dev} {r['d']} {r['g']} {r['s']} {r['b']} {r['model']} "
                     f"L={fmt(r['l'], 'u', 1e-6)} W={fmt(m['w'], 'u', 1e-6)} nf={m['nf']} "
                     f"AS={fmt(m['as'], 'p', 1e-12)} AD={fmt(m['ad'], 'p', 1e-12)} "
                     f"PS={fmt(m['ps'], 'u', 1e-6)} PD={fmt(m['pd'], 'u', 1e-6)} m=1\n")
        for i, ((a, b), v) in enumerate(sorted(caps.items()), 1):
            fo.write(f"C{i} {a} {b} {fmt(v, 'f', 1e-15)}\n")
        for n, v in wells.items():
            fo.write(f"CWELL_{n.upper()} {n} vss {fmt(v, 'f', 1e-15)}\n")
        fo.write(f".ends {name}\n")

    low = CELL.lower()
    wdev = max(abs(merged[d]["w"] - ref[d]["w"]) / ref[d]["w"] for d in ref)
    tot = lambda n: sum(v for pair, v in caps.items() if n in pair)  # noqa: E731
    print(f"{low}_pex_lvs = {kpex_lvs}")
    print(f"{low}_pex_fingers = {len(fingers)}")
    print(f"{low}_pex_devices = {len(merged)}")
    print(f"{low}_pex_w_max_rel_dev = {wdev:.3e}")
    print(f"{low}_pex_caps = {len(caps)}")
    print(f"{low}_pex_ports = {','.join(ports)}")
    print(f"{low}_pex_unnamed_nets = {len(unnamed)}")
    print(f"{low}_pex_stray_nets = {','.join(stray) or 'none'}")
    for n in ("outa", "left", "tail", "outb", "rep", "bst", "inp", "inn", "dout"):
        print(f"{low}_pex_c_{n}_ff = {tot(n) * 1e15:.3f}")
    print(f"{low}_pex_c_inp_inn_ff = {caps.get(('inn', 'inp'), 0.0) * 1e15:.3f}")
    for n, v in wells.items():
        print(f"{low}_pex_cwell_{n}_ff = {v * 1e15:.3f}")
    print(f"{low}_pex_subckt = {name}")
    print(f"{low}_pex_netlist = 1")


if __name__ == "__main__":
    main()
