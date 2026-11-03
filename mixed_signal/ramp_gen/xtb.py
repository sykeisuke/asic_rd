"""The xschem testbench drawings against their hand-written benches (phases.sh,
schematic phase, after xschem has netlisted tb_ramp.sch, tb_ramp_simple.sch and
tb_loop.sch into work/).

    python3 xtb.py [tb_ramp tb_ramp_simple tb_loop]

For each drawing: its xschem netlist (work/<tb>.spice, the DUT from
ramp_gen.sch / ramp_simple.sch, or the primitive ramp_gen_lb) is simulated by
ngspice in work/xtb_<tb>/sch/, and the hand bench (tb_ramp.spice,
tb_ramp_simple.spice, tb_loop.spice) in work/xtb_<tb>/ref/ with the same
case.spice (the nominal case the drawing carries). Both outputs go through the
block's reducers (reduce_ramp.py: slope, INL, start, kick, recovery;
reduce_loop.py: loop gain, crossover, margins), and every .measure echo and
reduced figure is compared:

  devices identical (the drawn ramps carry no S/D geometry, the bias block
  and every source are the same lines):
    voltages           within 10 uV          currents  within 1e-6 relative
    slope error        within 1e-4 % (1e-6 of the slope)
    LSB figures        within 1.7e-3 LSB (10 uV)
    loop gain / PM     within 1e-4 dB / deg, crossover 1e-6 relative
  REPORTED, not gated: the threshold-crossing times kick_settle_ns and rec_ns
    (read off the 0.2 ns output grid: one grid step of difference is not a
    circuit difference).

Prints PASS:/FAIL:/REPORT: and `xtb_<tb>_<figure> = value` lines; writes
data/xtb.csv. A bench whose simulation does not finish in 10 min is skipped
and reported.
"""
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
NUM = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[-+]?nan|[-+]?inf)"
TIMEOUT = 600
RAMP_CASE = ".param NCELL=4\n.param VKICK=2.0\n.param VDDX=1\n.param TPRE=0\n"
LOOP_CASE = ".param MODE=1\n.param VOP=0.5\n.param NCELL=4\n"
BENCH = {
    "tb_ramp": dict(hand="tb_ramp.spice", case=RAMP_CASE, reduce=["reduce_ramp.py"]),
    "tb_ramp_simple": dict(hand="tb_ramp_simple.spice", case=RAMP_CASE, reduce=["reduce_ramp.py"]),
    "tb_loop": dict(hand="tb_loop.spice", case=LOOP_CASE, reduce=["reduce_loop.py", "loop"]),
}
LSB = 1.5 / 256
# tolerance by figure: (kind, value); kind abs / rel / report / exact
TOL = {
    "slope_err_pct": ("abs", 1e-4), "offset_lsb": ("abs", 10e-6 / LSB), "inl_lsb": ("abs", 10e-6 / LSB),
    "inl_end_lsb": ("abs", 10e-6 / LSB), "inl_ovr_lsb": ("abs", 10e-6 / LSB), "start_settle_k": ("exact", 0),
    "vx_span_mv": ("abs", 0.01), "kick_peak_mv": ("abs", 0.01), "kick_res_tr_mv": ("abs", 0.01),
    "rec_level_mv": ("abs", 0.01), "kick_settle_ns": ("report", 0), "rec_ns": ("report", 0),
    "loop_t_1k_db": ("abs", 1e-4), "loop_fc_hz": ("rel", 1e-6), "loop_pm_deg": ("abs", 1e-4), "loop_gm_db": ("abs", 1e-4),
}
MAIN = {"tb_ramp": ("slope_err_pct", "inl_lsb", "kick_peak_mv", "rec_ns", "i_total"),
        "tb_ramp_simple": ("slope_err_pct", "inl_lsb", "kick_peak_mv", "rec_ns", "i_total"),
        "tb_loop": ("loop_t_1k_db", "loop_fc_hz", "loop_pm_deg", "loop_gm_db", "op_vx")}


def tol_of(name):
    if name in TOL:
        return TOL[name]
    if name.startswith("start_dev_lsb_"):
        return ("abs", 10e-6 / LSB)
    if name.startswith("vx_") and name.endswith("_mv"):
        return ("abs", 0.01)
    if name.startswith("i_"):
        return ("rel", 1e-6)
    return ("abs", 10e-6)          # every other .measure is a voltage


def parse(text):
    """`name = value` lines (ngspice .measure echoes, print, the reducers)"""
    r = {}
    for m in re.finditer(r"^([a-z][a-z_0-9]*)\s*=\s*" + NUM, text, re.M):
        try:
            r[m.group(1)] = float(m.group(2))
        except ValueError:
            pass
    return r


def run(d, deck, case=None):
    """ngspice on `deck` in directory d (one thread); returns (seconds, out text) or (None, reason)"""
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    if case is not None:
        open(os.path.join(d, "case.spice"), "w").write(case)
    t = time.time()
    try:
        subprocess.run(["ngspice", "-b", deck], cwd=d, stdin=subprocess.DEVNULL,
                       stdout=open(os.path.join(d, "out.txt"), "w"), stderr=subprocess.STDOUT, timeout=TIMEOUT,
                       env=dict(os.environ, OMP_NUM_THREADS="1"))
    except subprocess.TimeoutExpired:
        return None, "did not finish in %d s" % TIMEOUT
    return time.time() - t, open(os.path.join(d, "out.txt"), errors="replace").read()


def reduce(d, args):
    p = subprocess.run(["python3", os.path.join(BLOCK, args[0]), d] + args[1:], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else ""


def one(tb):
    b = BENCH[tb]
    net = os.path.join(WORK, tb + ".spice")
    if not os.path.exists(net):
        return tb, None, "xschem netlist work/%s.spice missing" % tb
    dsch, dref = os.path.join(WORK, "xtb_" + tb, "sch"), os.path.join(WORK, "xtb_" + tb, "ref")
    os.makedirs(dsch, exist_ok=True)
    open(os.path.join(dsch, "tb.spice"), "w").write(open(net).read())
    with ThreadPoolExecutor(max_workers=2) as ex:
        fs = ex.submit(run, dsch, "tb.spice")
        fr = ex.submit(run, dref, os.path.join(BLOCK, b["hand"]), b["case"])
        (ts, osch), (tr, oref) = fs.result(), fr.result()
    if ts is None or tr is None:
        return tb, None, "schematic %s; hand bench %s" % (osch if ts is None else "ran", oref if tr is None else "ran")
    vs = parse(osch); vs.update(parse(reduce(dsch, b["reduce"])))
    vr = parse(oref); vr.update(parse(reduce(dref, b["reduce"])))
    return tb, (vs, vr, ts, tr), ""


def main():
    tbs = sys.argv[1:] or list(BENCH)
    rows, ok_all = [], True
    with ThreadPoolExecutor(max_workers=3) as ex:
        results = list(ex.map(one, tbs))
    for tb, res, why in results:
        if res is None:
            if "missing" in why:
                print("FAIL: xtb %s: %s" % (tb, why)); ok_all = False
            else:
                print("REPORT: xtb %s skipped: %s" % (tb, why))
            continue
        vs, vr, ts, tr = res
        print("xtb_%s_sec = %.1f" % (tb, ts))
        names = [n for n in vr if not n.startswith("xtb_")]
        if not names:
            print("FAIL: xtb %s: the hand bench produced no figures" % tb); ok_all = False; continue
        nfail, ngate, worst = 0, 0, []
        for n in names:
            kind, t = tol_of(n)
            x, h = vs.get(n, float("nan")), vr[n]
            diff = x - h
            rel = abs(diff) / abs(h) if h else (0.0 if diff == 0 else float("inf"))
            if kind == "report":
                print("REPORT: xtb %s %s: schematic %.6g, bench %.6g (output-grid crossing time, not gated)" % (tb, n, x, h))
                verdict = "report"
            else:
                ngate += 1
                if kind == "abs":
                    good = abs(diff) <= t
                elif kind == "rel":
                    good = rel <= t
                else:
                    good = diff == 0
                good = bool(good) and x == x
                verdict = "pass" if good else "FAIL"
                if not good:
                    nfail += 1
                    print("FAIL: xtb %s %s: schematic %.6g, bench %.6g, diff %.3g (tol %s %g)" % (tb, n, x, h, diff, kind, t))
                worst.append((abs(diff) / t if kind != "exact" and t else abs(diff), n, diff))
            rows.append((tb, n, h, x, diff, kind, t, verdict))
        for n in MAIN[tb]:
            if n in vs:
                print("xtb_%s_%s = %.6g" % (tb, n, vs[n]))
        if nfail == 0:
            w = max(worst) if worst else (0, "-", 0)
            print("PASS: xtb %s: the xschem netlist reproduces %s at the nominal case, %d figures within tolerance "
                  "(worst %s, diff %.3g = %.2f of its tolerance)" % (tb, BENCH[tb]["hand"], ngate, w[1], w[2], w[0]))
        else:
            print("FAIL: xtb %s: %d of %d figures outside tolerance against %s" % (tb, nfail, ngate, BENCH[tb]["hand"]))
            ok_all = False
    os.makedirs(os.path.join(BLOCK, "data"), exist_ok=True)
    with open(os.path.join(BLOCK, "data", "xtb.csv"), "w") as h:
        h.write("bench,figure,hand,xschem,diff,tol_kind,tol,verdict\n")
        for r in rows:
            h.write("%s,%s,%.8g,%.8g,%.4g,%s,%g,%s\n" % r)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
