"""Translate the ngspice subcircuits of the four-cell system into VACASK.

    from tn_netlist import Translator
    tr = Translator(snapshot_dir)      # reads the snapshot of ramp_gen + params
    text = tr.emit(quiet={"cells", "bias"})

Deliberately narrow. It reads exactly these subcircuits, by path:

  ramp_gen      snapshot/ramp_gen.spice + snapshot/ramp_gen_params.spice
  bias_gen      ../ref/bias_gen/bias_gen.spice + data/bias_gen_params.spice
  midref_b      ../ref/midrail_ref/ref_fvf_biased.spice + data/midrail_params.spice
  sw_s0/1/2     ../ref/unit_cell_bps/switches.spice
  unit_cell_bps ../ref/unit_cell_bps/unit_cell_bps.spice (unit_cell_top is not used)
  cmp           ../ref/comparator_updt/cmp_updt.spice

and accepts only: X instances of nfet_03v3 / pfet_03v3 (L W nf m ad as pd
ps), cap_mim_2f0_m4m5_noshield (c_width c_length), ppolyf_u / ppolyf_u_3k
(r_width r_length; the substrate pin is dropped), X instances of the
subcircuits above, and plain R / C lines. Anything else is a FAIL.

  MIM -> ideal capacitor, C = 1.99e-3 W L + 2.383e-10 x 2 (W + L)
         (the form the unit-cell testbench uses for CS_C)
  poly R -> ideal resistor with the value ngspice gives for that geometry
         (measured once by an ngspice op at 27 C, cached in work/res_values.json)

Noise groups (a run can make any set quiet):
  ramp_ota    ramp_gen XM1..XM7, XRST, XRZ
  ramp_chain  ramp_gen XPS, XND, XNS
  ramp_bias   the ramp's own bias_gen (bias_gen_r: pbias_r on the ramp's supply)
  cell_bias   the cells' bias_gen (pbias for the comparators and the FVF buffers)
  cells       cmp, the switches, the cell inverters, midref_b (incl. its resistors)
A quiet MOS uses nfet_03v3_q / pfet_03v3_q (tn_models.py); a quiet resistor
has noisy=0. Capacitors are noiseless anyway.
"""
import json
import os
import re
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.normpath(os.path.join(HERE, "..", ".."))
WORK = os.path.join(HERE, "work")
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9, "t": 1e12}
MOS = {"nfet_03v3", "pfet_03v3"}
RES = {"ppolyf_u", "ppolyf_u_3k"}
MIM = "cap_mim_2f0_m4m5_noshield"


def num(tok):
    m = re.match(r"^([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(meg|[fpnumkgt])?$", tok, re.I)
    if not m:
        return None
    return float(m.group(1)) * SI.get((m.group(2) or "").lower(), 1.0)


class Translator:
    def __init__(self, snap):
        self.snap = snap
        self.params = {}
        for f in (os.path.join(MS, "ramp_gen", "ref", "bias_gen", "data", "bias_gen_params.spice"),
                  os.path.join(MS, "ramp_gen", "ref", "midrail_ref", "data", "midrail_params.spice"),
                  os.path.join(snap, "ramp_gen_params.spice")):
            for line in open(f):
                m = re.match(r"^\.param\s+(\w+)\s*=\s*(\S+)", line.strip(), re.I)
                if m:
                    self.params[m.group(1).lower()] = self.ev(m.group(2))
        self.subckts = {}
        self.order = []
        for f, names in ((os.path.join(snap, "ramp_gen.spice"), {"ramp_gen"}),
                         (os.path.join(MS, "ramp_gen", "ref", "bias_gen", "bias_gen.spice"), {"bias_gen"}),
                         (os.path.join(MS, "ramp_gen", "ref", "midrail_ref", "ref_fvf_biased.spice"), {"midref_b"}),
                         (os.path.join(MS, "ramp_gen", "ref", "unit_cell_bps", "switches.spice"), {"sw_s0", "sw_s1", "sw_s2"}),
                         (os.path.join(MS, "ramp_gen", "ref", "comparator_updt", "cmp_updt.spice"), {"cmp"}),
                         (os.path.join(MS, "ramp_gen", "ref", "unit_cell_bps", "unit_cell_bps.spice"), {"unit_cell_bps"})):
            self.read(f, names)
        self.resvals = self.measure_resistors()

    # ---------------------------------------------------------------- parsing
    def ev(self, s):
        s = s.strip().strip("{}'\"")
        v = num(s)
        if v is not None:
            return v
        expr = re.sub(r"(?<![\w.])((?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(meg|[fpnumkgt])(?![\w])",
                      lambda m: repr(float(m.group(1)) * SI[m.group(2).lower()]), s, flags=re.I)

        def name(m):
            k = m.group(0).lower()
            if k not in self.params:
                raise SystemExit("FAIL: tn_netlist: unknown parameter %r in %r" % (m.group(0), s))
            return repr(self.params[k])
        expr = re.sub(r"\b[A-Za-z_]\w*\b", name, expr)
        return float(eval(expr, {"__builtins__": {}}))

    def read(self, path, names):
        cur = None
        lines = []
        for raw in open(path):
            line = raw.rstrip("\n")
            if line.startswith("+") and lines:
                lines[-1] += " " + line[1:]
            else:
                lines.append(line)
        for line in lines:
            s = line.strip()
            if not s or s.startswith("*"):
                continue
            low = s.lower()
            if low.startswith(".subckt"):
                p = s.split()
                cur = p[1].lower() if p[1].lower() in names else None
                if cur:
                    self.subckts[cur] = {"ports": [x.lower() for x in p[2:]], "dev": []}
                    self.order.append(cur)
                continue
            if low.startswith(".ends"):
                cur = None
                continue
            if cur is None:
                continue
            if s.startswith("."):
                raise SystemExit("FAIL: tn_netlist: dot card inside .subckt %s: %r" % (cur, s))
            self.subckts[cur]["dev"].append(s)
        miss = names - set(self.subckts)
        if miss:
            raise SystemExit("FAIL: tn_netlist: %s not found in %s" % (sorted(miss), path))

    def kv(self, toks):
        out = {}
        for t in toks:
            if "=" not in t:
                raise SystemExit("FAIL: tn_netlist: positional parameter %r" % t)
            k, v = t.split("=", 1)
            out[k.lower()] = self.ev(v)
        return out

    def parse_dev(self, s):
        t = s.split()
        name = t[0].lower()
        if name[0] == "x":
            first = next((i for i, x in enumerate(t) if "=" in x), len(t))
            master = t[first - 1].lower()
            nodes = [x.lower() for x in t[1:first - 1]]
            return name, master, nodes, self.kv(t[first:])
        if name[0] in "rc":
            return name, name[0], [t[1].lower(), t[2].lower()], {"v": self.ev(t[3])}
        raise SystemExit("FAIL: tn_netlist: unsupported device line %r" % s)

    # ------------------------------------------------------------ resistors
    def measure_resistors(self):
        geos = set()
        for sc in self.subckts.values():
            for s in sc["dev"]:
                name, master, nodes, p = self.parse_dev(s)
                if master in RES:
                    geos.add((master, p["r_width"], p["r_length"]))
        cache = os.path.join(WORK, "res_values.json")
        vals = json.load(open(cache)) if os.path.exists(cache) else {}
        todo = [g for g in sorted(geos) if "%s|%.6g|%.6g" % g not in vals]
        if todo:
            deck = ["* ppolyf resistance probe",
                    ".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
                    ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical",
                    ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical"]
            for i, (m, w, l) in enumerate(todo):
                deck += ["V%d a%d 0 1" % (i, i), "X%d a%d 0 0 %s r_width=%.6g r_length=%.6g" % (i, i, m, w, l)]
            deck += [".control", "op"] + ['echo "res%d = $&i(v%d)"' % (i, i) for i in range(len(todo))] + \
                    ["quit", ".endc", ".end"]
            with tempfile.TemporaryDirectory() as td:
                p = os.path.join(td, "r.spice")
                open(p, "w").write("\n".join(deck) + "\n")
                r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True)
            got = {}
            for line in r.stdout.splitlines():
                m = re.match(r"^res(\d+) = (\S+)", line)
                if m:
                    got[int(m.group(1))] = abs(float(m.group(2)))
            for i, g in enumerate(todo):
                if i not in got or got[i] <= 0:
                    raise SystemExit("FAIL: tn_netlist: ngspice gave no current for resistor %s" % (g,))
                vals["%s|%.6g|%.6g" % g] = 1.0 / got[i]
            os.makedirs(WORK, exist_ok=True)
            json.dump(vals, open(cache, "w"), indent=1)
        return vals

    # --------------------------------------------------------------- groups
    @staticmethod
    def group(sc, inst):
        if sc == "ramp_gen":
            return "ramp_chain" if inst in ("xps", "xnd", "xns") else "ramp_ota"
        if sc == "bias_gen_r":
            return "ramp_bias"
        if sc == "bias_gen":
            return "cell_bias"
        return "cells"

    # ----------------------------------------------------------------- emit
    def emit(self, quiet=()):
        quiet = set(quiet)
        out = ["// GENERATED by trannoise/tn_netlist.py; quiet groups: %s" % (",".join(sorted(quiet)) or "none")]
        counts = {}
        for sc in ("cmp", "sw_s0", "sw_s1", "sw_s2", "unit_cell_bps", "bias_gen", "bias_gen_r", "midref_b", "ramp_gen"):
            # bias_gen_r: the same bias_gen, the ramp's own instance (its own noise group)
            d = self.subckts["bias_gen" if sc == "bias_gen_r" else sc]
            out.append("subckt %s (%s)" % (sc, " ".join(d["ports"])))
            for s in d["dev"]:
                name, master, nodes, p = self.parse_dev(s)
                g = self.group(sc, name)
                q = g in quiet
                counts[g] = counts.get(g, 0) + 1
                if master in MOS:
                    if len(nodes) != 4:
                        raise SystemExit("FAIL: tn_netlist: %s.%s has %d terminals" % (sc, name, len(nodes)))
                    extra = " ".join("%s=%.6g" % (k, p[k]) for k in ("ad", "as", "pd", "ps") if k in p)
                    unknown = set(p) - {"l", "w", "nf", "m", "ad", "as", "pd", "ps"}
                    if unknown:
                        raise SystemExit("FAIL: tn_netlist: %s.%s unknown MOS parameters %s" % (sc, name, unknown))
                    if p["w"] * p.get("m", 1) > 100.001e-6 and p.get("m", 1) == 1:
                        raise SystemExit("FAIL: tn_netlist: %s.%s W=%.4g above the 100 um bin ceiling" % (sc, name, p["w"]))
                    out.append("  %s (%s) %s%s w=%.6g l=%.6g nf=%d m=%d %s" % (
                        name, " ".join(nodes), master, "_q" if q else "", p["w"], p["l"],
                        int(round(p.get("nf", 1))), int(round(p.get("m", 1))), extra))
                elif master == MIM:
                    w, l = p["c_width"], p["c_length"]
                    c = 1.99e-3 * w * l + 2.383e-10 * 2 * (w + l)
                    out.append("  %s (%s %s) capacitor c=%.6g" % (name, nodes[0], nodes[1], c))
                elif master in RES:
                    r = self.resvals["%s|%.6g|%.6g" % (master, p["r_width"], p["r_length"])]
                    out.append("  %s (%s %s) resistor r=%.6g noisy=%d" % (name, nodes[0], nodes[1], r, 0 if q else 1))
                elif master == "r":
                    out.append("  %s (%s %s) resistor r=%.6g noisy=%d" % (name, nodes[0], nodes[1], p["v"], 0 if q else 1))
                elif master == "c":
                    out.append("  %s (%s %s) capacitor c=%.6g" % (name, nodes[0], nodes[1], p["v"]))
                elif master in self.subckts:
                    if p:
                        raise SystemExit("FAIL: tn_netlist: parameters on subcircuit instance %s.%s" % (sc, name))
                    out.append("  %s (%s) %s" % (name, " ".join(nodes), master))
                else:
                    raise SystemExit("FAIL: tn_netlist: %s.%s: unknown master %r" % (sc, name, master))
            out.append("ends\n")
        self.counts = counts
        return "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys
    tr = Translator(sys.argv[1])
    sys.stdout.write(tr.emit(set(sys.argv[2:])))
    for g, n in sorted(tr.counts.items()):
        sys.stderr.write("tn_netlist_devices_%s = %d\n" % (g, n))
