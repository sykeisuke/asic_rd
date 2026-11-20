"""The xschem testbenches of comparator against their decks (run by schematic.sh).

    ./container.sh 'python3 xtb.py'

For each tb_<name>.sch (tran, dc, nz, mc):

  1. xschem netlists it (the comparator from comparator.sch through
     comparator.sym) into work/xtb/<name>/;
  2. structure: every top-level element of that netlist equals the element of
     the same name in bench.py's template tb_<name>.spice filled for the `sw`
     variant at the nominal point (bench.py's own cell_subs / hook / grid):
     nodes, value or model, and the MOS L / W / nf / m; no element missing
     or extra. The DUT subcircuit itself is check-schematic.awk's;
  3. simulation: ngspice on the netlist with the PDK symbols' S/D geometry
     (ad as pd ps nrd nrs) stripped -- the benches leave it to BSIM4's
     defaults -- must reproduce the bench record data/values_verify.txt
     (`sw` at 40.5 LSB, noise, Monte Carlo) within: trip 50 uV, delays
     0.1 ns, pedestal 0.002 count, dout high 10 mV at TR, plate at TR 1 mV,
     edge / power 2 %, gain / pole / noise 1 %, MC nominal 0.1 mV and
     spread 20 % (the same tolerances as comparator_bkp/comparator_10dev/xtb.py; the MC draws
     are expected to match exactly when the device order matches);
  4. as drawn (with the S/D geometry): REPORTED against the bench.

Writes data/xtb.csv; prints PASS / FAIL / REPORT and name = value lines.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BLOCK)
import bench as B  # noqa: E402  the templates' substitutions (never run here)
import tb_sch as TB  # noqa: E402  the drawn nominal point

RC = "/foss/pdks/gf180mcuD/libs.tech/xschem/xschemrc"
XTB = os.path.join(BLOCK, "work", "xtb")
NUM = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
GEOM = ("ad", "as", "pd", "ps", "nrd", "nrs")
IGNORE_PARAMS = set(GEOM) | {"sa", "sb", "sd", "par"}
JOBS = int(os.environ.get("XTB_JOBS", "4"))


# ------------------------------------------------------------ the filled templates
def filled(name):
    """bench.py's template for `name`, filled for `sw` at the nominal point."""
    c = B.cell_subs(B.NOMINAL)
    c.update(DUT="dut.spice", IREF="%.6g" % B.I_F, EDGE="fall")
    if name == "tran":
        lsb, vrlo = B.grid(B.NOMINAL, "new")
        c.update(VIN="%.9g" % (vrlo + TB.LEVEL * lsb), VRLO="%.9g" % vrlo, LSB="%.9g" % lsb,
                 TSTOP="%.6g" % (400e-9 + 260 * B.TCOUNT), VTRIP="%.6f" % TB.VTRIP0, LVLA="hi90", LVLB="lo10",
                 XDUT=B.hook("sw", "plate", "vref", "dout", "XDUT"), MISMATCH="", WRDATA="")
    elif name == "dc":
        c.update(XDC=B.hook("sw", "vdc", "vref", "doutdc", "XDC"))
    elif name == "nz":                       # bench.noise(), the sw branch
        c.update(NZNET=(f"VSIG inn 0 DC {c['VCM']} AC 1\nCFB inp 0 1\nLFB dout inp 1T\n"
                        f"XDUT inp inn dout clk vdd 0 nbias pbias comparator"))
    elif name == "mc":
        c.update(NMC=str(TB.N_MC), SEED=str(TB.SEED), XMC=B.hook("sw", "vsw", "vrefx", "dout", "XDUT"))
    text = open(os.path.join(BLOCK, f"tb_{name}.spice")).read()
    for k, v in c.items():
        text = text.replace(f"@{k}@", v)
    left = re.findall(r"@[A-Z0-9_]+@", text)
    if left:
        raise RuntimeError(f"tb_{name}.spice: unreplaced {sorted(set(left))}")
    return text


def norm(v):
    return re.sub(r"[{}'\"]", "", v).lower()


def elements(text):
    """Top-level element cards {NAME: normalised key}; .subckt bodies and the
    .control block are skipped, '+' continuations joined."""
    lines, cur = [], None
    for raw in text.splitlines():
        if raw.startswith("+") and cur is not None:
            cur += " " + raw[1:]
            continue
        if cur is not None:
            lines.append(cur)
        cur = raw.strip()
    if cur is not None:
        lines.append(cur)
    out, depth, ctl = {}, 0, False
    for ln in lines:
        lo = ln.lower()
        if lo.startswith(".subckt"):
            depth += 1
        elif lo.startswith(".ends"):
            depth -= 1
        elif lo.startswith(".control"):
            ctl = True
        elif lo.startswith(".endc"):
            ctl = False
        if depth or ctl or not ln or ln[0] in "*.":
            continue
        tok = ln.split()
        name, head = tok[0].upper(), tok[0][0].upper()
        if head in "VI":
            key = " ".join(norm(t) for t in tok[1:3]) + " | " + " ".join(norm(t) for t in tok[3:]
                                                                    if not norm(t).startswith("savecurrent"))
        elif head in "CRL":
            key = " ".join(norm(t) for t in tok[1:4])
        elif head == "S":
            key = " ".join(norm(t) for t in tok[1:6])
        elif head == "X":
            rest = " ".join(tok[1:])
            pat = r"(\w+)\s*=\s*('[^']*'|\{[^}]*\}|\S+)"
            pos = [norm(t) for t in re.sub(pat, " ", rest).split()]
            par = {}
            for k, v in re.findall(pat, rest):
                if k.lower() not in IGNORE_PARAMS:
                    par[k.lower()] = norm(v)
            par.setdefault("m", "1")
            key = " ".join(pos) + " | " + " ".join("%s=%s" % kv for kv in sorted(par.items()))
        else:
            key = " ".join(norm(t) for t in tok[1:])
        out[name] = key
    return out


def structure(name, net):
    want, got = elements(filled(name)), elements(net)
    bad = []
    for n, k in want.items():
        if n not in got:
            bad.append(f"{n} missing")
        elif got[n] != k:
            bad.append(f"{n} deck [{k}] drawing [{got[n]}]")
    bad += [f"{n} not in the deck" for n in got if n not in want]
    if bad:
        print(f"FAIL: xtb structure tb_{name}.sch vs tb_{name}.spice (sw, nominal): " + "; ".join(bad)[:600])
        return False
    print(f"PASS: xtb structure tb_{name}.sch = tb_{name}.spice filled for sw at the nominal point: "
          f"{len(want)} elements, nodes / values / sizes equal")
    return True


# ------------------------------------------------------------ simulation
def netlist(name):
    d = os.path.join(XTB, name)
    os.makedirs(d, exist_ok=True)
    net = os.path.join(d, f"tb_{name}.spice")
    if os.path.exists(net):
        os.remove(net)
    with open(os.path.join(d, "xschem.out"), "w") as h:
        subprocess.run(["xschem", "--rcfile", RC, "-b", "-q", "-n", "-s", "-o", d, f"tb_{name}.sch"], cwd=BLOCK,
                       stdout=h, stderr=subprocess.STDOUT, timeout=300)
    return open(net).read() if os.path.exists(net) else None


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


def grab(blk, key):
    m = re.search(r"^\s*%s\s*=\s*%s" % (key, NUM), blk, re.M)
    return float(m.group(1)) if m else float("nan")


def bench_record():
    v = {}
    for ln in open(os.path.join(BLOCK, "data", "values_verify.txt")):
        m = re.match(r"^(\w+) = (\S+)", ln)
        if m:
            v[m.group(1)] = float(m.group(2))
    return v


TRAN_KEYS = ("delay_vref", "delay_dyn", "edge", "ped_counts", "armed", "p_avg", "vplate_tr")
NZ_KEYS = ("ota_gain_vv", "ota_pole_hz", "nz_own_vin", "nz_lo_vin", "nz_ugb_vin", "op_i_vdd")


def run_tran(nets, geom):
    r = {"vtrip_v": grab(block(variant("dc", nets["dc"], geom)), "vtrip")}
    vt = r["vtrip_v"] if np.isfinite(r["vtrip_v"]) else TB.VTRIP0
    blk = block(variant("tran", nets["tran"], geom, {r'^set vtrip_s = .*$': 'set vtrip_s = "%.6f"' % vt}))
    r.update({k: grab(blk, k) for k in TRAN_KEYS})
    return r


def run_nz(nets, geom):
    blk = block(variant("nz", nets["nz"], geom))
    return {k: grab(blk, k) for k in NZ_KEYS}


def run_mc(nets, geom):
    out = variant("mc", nets["mc"], geom)
    nom = re.findall(r"^vos_nom\s*=\s*" + NUM, out, re.M)
    ks = np.array([float(x) for x in re.findall(r"^vos_k\s*=\s*" + NUM, out, re.M)])
    return {"mc_vos_nominal_v": float(nom[0]) if nom else float("nan"),
            "mc_sigma_vos_v": float(np.std(ks, ddof=1)) if ks.size > 2 else float("nan"),
            "mc_vos_mean_v": float(np.mean(ks)) if ks.size else float("nan"),
            "mc_samples": float(ks.size)}


def main():
    names = ("tran", "dc", "nz", "mc")
    nets = {n: netlist(n) for n in names}
    ok_all = True
    for n, t in nets.items():
        if t is None:
            print(f"FAIL: xtb: xschem did not netlist tb_{n}.sch")
            ok_all = False
            continue
        sub = ".subckt comparator " in t
        print(f"{'PASS' if sub else 'FAIL'}: xtb: xschem netlisted tb_{n}.sch "
              f"(comparator from its schematic: {'yes' if sub else 'NO'})")
        ok_all &= sub
        ok_all &= structure(n, t)
    if any(t is None for t in nets.values()):
        return 1

    rec = bench_record()
    bench = {k: rec.get("sw_plat_" + k, float("nan")) for k in ("vtrip_v",) + TRAN_KEYS}
    bench.update({k: rec.get("sw_" + k, float("nan")) for k in NZ_KEYS + ("mc_vos_nominal_v", "mc_sigma_vos_v")})
    tol = dict(vtrip_v=("abs", 50e-6), delay_vref=("abs", 0.1e-9), delay_dyn=("abs", 0.1e-9), edge=("rel", 0.02),
               ped_counts=("abs", 0.002), armed=("abs", 0.01), p_avg=("rel", 0.02), vplate_tr=("abs", 1e-3),
               ota_gain_vv=("rel", 0.01), ota_pole_hz=("rel", 0.01), nz_own_vin=("rel", 0.01),
               nz_lo_vin=("rel", 0.01), nz_ugb_vin=("rel", 0.01), op_i_vdd=("rel", 0.01),
               mc_vos_nominal_v=("abs", 0.1e-3), mc_sigma_vos_v=("rel", 0.20))

    jobs = [(f, g) for g in (False, True) for f in (run_tran, run_nz, run_mc)]
    res = {False: {}, True: {}}
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        futs = [(g, ex.submit(f, nets, g)) for f, g in jobs]
        for g, fu in futs:
            res[g].update(fu.result())

    rows = []
    for k, (kind, t) in tol.items():
        b = bench[k]
        for geom in (False, True):
            x = res[geom].get(k, float("nan"))
            diff = x - b
            rel = abs(diff) / abs(b) if b else float("nan")
            rows.append((k, "geom" if geom else "nogeom", b, x, diff, rel))
            if not geom:
                good = bool(np.isfinite(x) and np.isfinite(b) and (abs(diff) <= t if kind == "abs" else rel <= t))
                ok_all &= good
                print(f"{'PASS' if good else 'FAIL'}: xtb nogeom {k}: schematic {x:.6g}, bench {b:.6g} "
                      f"({'diff %.3g' % diff if kind == 'abs' else 'rel %.2e' % rel}; tol {t:g} {kind})")
            else:
                print(f"REPORT: xtb as drawn (S/D geometry) {k}: schematic {x:.6g}, bench {b:.6g}, "
                      f"{100 * diff / b if b else float('nan'):+.2f} %")
                print(f"xtb_geom_{k} = {x:.6g}")
    print(f"xtb_mc_samples = {res[False].get('mc_samples', 0):g}")
    print(f"xtb_nogeom_delay_dyn = {res[False].get('delay_dyn', float('nan')):.6g}")
    with open(os.path.join(BLOCK, "data", "xtb.csv"), "w") as h:
        h.write("metric,variant,bench,xschem,diff,rel\n")
        for r in rows:
            h.write("%s,%s,%.6g,%.6g,%.6g,%.6g\n" % r)
    print("PASS: xtb: every testbench schematic equals its deck and reproduces the bench record"
          if ok_all else "FAIL: xtb")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
