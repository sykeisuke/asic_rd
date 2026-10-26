"""The xschem testbenches against the hand-written benches (run by schematic.sh).

    ./container.sh 'python3 xtb.py'

Each tb_<name>.sch is netlisted by xschem (the comparator from
comparator.sch through comparator.sym), simulated in ngspice in
work/xtb/<name>/, and its figures are compared with the bench record of the
same design (results/verify.json, the verification run of the hand-written
decks). The PDK's xschem MOS symbols write drain/source geometry (ad as pd ps
nrd nrs) that the hand-written decks leave to BSIM4's defaults, so every
testbench also runs with those six parameters stripped (_nogeom):

  nogeom  must reproduce the bench: trip within 50 uV (2 sweep steps), delays
          within 0.1 ns, fall within 2 %, gain and noise within 1 %, the MC
          nominal trip within 0.1 mV and its spread within 20 % (200 samples
          each, drawn in a different device order: +-7 % per estimate)
  geom    the drawing as drawn: REPORTED against the bench (the junction
          capacitance the decks leave out)
Writes data/xtb.csv; prints PASS/FAIL/REPORT lines.
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import size_v3 as S  # noqa: E402

RC = "/foss/pdks/gf180mcuD/libs.tech/xschem/xschemrc"
XTB = os.path.join(S.BLOCK, "work", "xtb")
NUM = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"


def netlist(name):
    d = os.path.join(XTB, name)
    os.makedirs(d, exist_ok=True)
    net = os.path.join(d, f"tb_{name}.spice")
    if os.path.exists(net):
        os.remove(net)
    subprocess.run(["xschem", "--rcfile", RC, "-b", "-q", "-n", "-s", "-o", d, f"tb_{name}.sch"], cwd=S.BLOCK,
                   stdout=open(os.path.join(d, "xschem.out"), "w"), stderr=subprocess.STDOUT, timeout=300)
    if not os.path.exists(net):
        return None
    return open(net).read()


def variant(name, text, geom, subs=None):
    d = os.path.join(XTB, name + ("" if geom else "_nogeom"))
    os.makedirs(d, exist_ok=True)
    if not geom:
        text = re.sub(r"\s(?:ad|as|pd|ps|nrd|nrs)=('[^']*'|\S+)", "", text)
    for k, v in (subs or {}).items():
        text = re.sub(k, v, text, flags=re.M)
    open(os.path.join(d, "tb.spice"), "w").write(text)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    subprocess.run(["ngspice", "-b", "-o", "tb.out", "tb.spice"], cwd=d, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200,
                   env=dict(os.environ, OMP_NUM_THREADS="1"))
    p = os.path.join(d, "tb.out")
    return open(p, errors="replace").read() if os.path.exists(p) else ""


def block(out):
    return out.split("RESULT_BEGIN")[-1].split("RESULT_END")[0] if "RESULT_BEGIN" in out else ""


def main():
    ver = json.load(open(os.path.join(S.BLOCK, "results", "verify.json")))
    bench = dict(vtrip=ver["plat_vtrip_v"], delay_dyn=ver["plat_delay_dyn"], delay_vbl=ver["plat_delay_vbl"],
                 fall=ver["plat_fall"], ota_gain_vv=ver["ota_gain_vv"], nz_own_vin=ver["nz_own_vin"],
                 vos_nom=ver["mc_vos_nominal_v"], sigma_vos=ver["mc_sigma_vos_v"])
    nets = {n: netlist(n) for n in ("trip", "delay", "noise", "mc")}
    ok_all = True
    for n, t in nets.items():
        if t is None:
            print(f"FAIL: xtb: xschem did not netlist tb_{n}.sch")
            ok_all = False
        else:
            print(f"PASS: xtb: xschem netlisted tb_{n}.sch (comparator from its schematic: "
                  f"{'yes' if '.subckt comparator' in t else 'NO'})")
            ok_all &= ".subckt comparator" in t
    if not ok_all:
        return 1

    res = {}

    def run_geom(geom):
        r = {}
        r["vtrip"] = S.grab(block(variant("trip", nets["trip"], geom)), "vtrip")
        dl = block(variant("delay", nets["delay"], geom, {r"^\.param VTRIP=\S+": ".param VTRIP=%.6f" % r["vtrip"]}))
        for k in ("delay_vbl", "delay_dyn", "fall"):
            r[k] = S.grab(dl, k)
        nz = block(variant("noise", nets["noise"], geom))
        for k in ("ota_gain_vv", "nz_own_vin"):
            r[k] = S.grab(nz, k)
        mc = variant("mc", nets["mc"], geom)
        nom = re.findall(r"^vos_nom\s*=\s*" + NUM, mc, re.M)
        ks = np.array([float(x) for x in re.findall(r"^vos_k\s*=\s*" + NUM, mc, re.M)])
        r["vos_nom"] = float(nom[0]) if nom else float("nan")
        r["sigma_vos"] = float(np.std(ks, ddof=1)) if ks.size > 2 else float("nan")
        r["mc_n"] = ks.size
        return geom, r

    with ThreadPoolExecutor(max_workers=2) as ex:
        for geom, r in ex.map(run_geom, (False, True)):
            res[geom] = r

    tol = dict(vtrip=("abs", 50e-6), delay_dyn=("abs", 0.1e-9), delay_vbl=("abs", 0.1e-9), fall=("rel", 0.02),
               ota_gain_vv=("rel", 0.01), nz_own_vin=("rel", 0.01), vos_nom=("abs", 0.1e-3), sigma_vos=("rel", 0.20))
    rows = []
    for k, (kind, t) in tol.items():
        b = bench[k]
        for geom in (False, True):
            x = res[geom][k]
            diff = x - b
            rel = abs(diff) / abs(b) if b else float("nan")
            rows.append((k, "geom" if geom else "nogeom", b, x, diff, rel))
            if not geom:
                good = np.isfinite(x) and (abs(diff) <= t if kind == "abs" else rel <= t)
                ok_all &= bool(good)
                print(f"{'PASS' if good else 'FAIL'}: xtb nogeom {k}: schematic {x:.6g}, bench {b:.6g} "
                      f"({'diff %.3g' % diff if kind == 'abs' else 'rel %.2e' % rel}; tol {t:g} {kind})")
            else:
                print(f"REPORT: xtb as drawn (S/D geometry) {k}: schematic {x:.6g}, bench {b:.6g}, {100*diff/b:+.2f} %")
                print(f"xtb_geom_{k} = {x:.6g}")
    print(f"xtb_mc_samples = {res[False]['mc_n']}")
    with open(os.path.join(S.BLOCK, "data", "xtb.csv"), "w") as h:
        h.write("metric,variant,bench,xschem,diff,rel\n")
        for r in rows:
            h.write("%s,%s,%.6g,%.6g,%.6g,%.6g\n" % r)
    print("PASS: xtb: every testbench schematic reproduces its bench" if ok_all else "FAIL: xtb")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
