"""The xschem testbenches against the hand-written benches (run by schematic.sh).

    ./container.sh 'python3 xtb.py'

Each tb_<name>.sch (tb_sch.py) is netlisted by xschem with the block's
xschemrc (the latch from latch.sch through latch.sym; in tb_kick the
comparator from ../comparator/comparator.sch through comparator.sym),
simulated by ngspice in work/xtb_<name>/, and its figures are compared with
the hand-written bench template rendered by bench.py at the same nominal
case (typical, 27 C, 3.3 V; work/xtb_ref_<name>/):

  drive     clock-to-q of the first q fall and its 90-10 % fall     within 10 ps
  aperture  q falls once and never rises; clock-to-q and fall       within 10 ps
  kick      t_cross, t_dout, t_q (absolute) and the dout fall        within 50 ps,
            with the PDK symbols' S/D junction geometry (ad as pd ps nrd nrs,
            which the hand deck lacks) stripped from the xschem netlist
            (_nogeom); the drawing as drawn is REPORTED, as is the plate
            step at the sampling edge before the crossing

Uses the netlist schematic.sh left in work/xtb_<name>/ when present (it has
already been checked by check-tb.awk), else netlists the drawing itself.
Writes data/xtb.csv; prints PASS/FAIL/REPORT lines and `xtb_* = value` lines.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B  # noqa: E402
import tb_sch as T  # noqa: E402  the nominal case the drawings are fixed at

RC = os.path.join(B.BLOCK, "xschemrc")
NUM = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
MEAS = re.compile(r"^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=\s*" + NUM)
TOL_LATCH = 10e-12
TOL_KICK = 50e-12


def netlist(name):
    d = os.path.join(B.WORK, "xtb_tb_" + name)
    os.makedirs(d, exist_ok=True)
    net = os.path.join(d, "tb_%s.spice" % name)
    if not os.path.exists(net):
        with open(os.path.join(d, "xschem.out"), "w") as h:
            subprocess.run(["xschem", "--rcfile", RC, "-b", "-q", "-n", "-s", "-o", d, "tb_%s.sch" % name],
                           cwd=B.BLOCK, stdout=h, stderr=subprocess.STDOUT, timeout=300)
    if not os.path.exists(net):
        return None
    with open(net) as h:
        return h.read()


def run_xschem(name, text, geom=True):
    d = os.path.join(B.WORK, "xtb_tb_" + name + ("" if geom else "_nogeom"))
    os.makedirs(d, exist_ok=True)
    if not geom:
        text = re.sub(r"\s(?:ad|as|pd|ps|nrd|nrs)=('[^']*'|\S+)", "", text)
    with open(os.path.join(d, "tb.spice"), "w") as h:
        h.write(text)
    with open(os.path.join(d, ".spiceinit"), "w") as h:
        h.write(B.SPICEINIT)
    subprocess.run(["ngspice", "-b", "-o", "tb.out", "tb.spice"], cwd=d, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200,
                   env=dict(os.environ, OMP_NUM_THREADS="1"))
    p = os.path.join(d, "tb.out")
    if not os.path.exists(p):
        return {}
    with open(p, errors="replace") as h:
        out = h.read()
    m = {}
    for line in out.splitlines():
        mm = MEAS.match(line)
        if mm:
            m[mm.group(1).lower()] = float(mm.group(2))
    return m


def ref_kick():
    """tb_kick.spice at the drawn case, as bench.kick_case renders it (not
    called: its tag would overwrite the kick phase's own run)."""
    vin, tce = T.KICK_VIN, B.T1090_CLK_NOM / 0.8
    clk = "PULSE(0 %g %.6e %.6e %.6e %.6e %.6e)" % (B.VDD, B.TCOUNT - tce / 2, tce, tce, B.TCOUNT / 2 - tce, B.TCOUNT)
    load = "XL dout clk q dvdd 0 %s\nCQ q 0 %.6e" % (B.SUBCKT, B.CQ)
    d = B.render("tb_kick.spice", "xtb_ref_kick", {"VIN": "%.12g" % vin, "CLK": clk, "LOAD": load,
                                                   "TCE": "%.6e" % tce, "NETLIST": B.NETLIST})
    B.ngspice(d, expect=None)
    m = {}
    try:
        with open(os.path.join(d, "run.log"), errors="replace") as h:
            for line in h:
                mm = MEAS.match(line)
                if mm:
                    m[mm.group(1).lower()] = float(mm.group(2))
    except OSError:
        pass
    tideal = B.TR + (vin - B.VR_LO) / (B.LSB / B.TCOUNT)
    r = {}
    for k in ("cross", "dout", "q"):
        r["t_" + k] = tideal + m["rel_" + k] if "rel_" + k in m else m.get("t_" + k, float("nan"))
    r["dout_fall"] = m.get("t_f10", float("nan")) - m.get("t_f90", float("nan"))
    r["delay"] = r["t_dout"] - r["t_cross"]
    return r


def main():
    nets = {n: netlist(n) for n in ("drive", "aperture", "kick")}
    ok_all = True
    for n, t in nets.items():
        if t is None:
            print("FAIL: xtb: xschem did not netlist tb_%s.sch" % n)
            ok_all = False
        else:
            has_latch = ".subckt latch" in t
            has_cmp = ".subckt comparator" in t if n == "kick" else True
            print("PASS: xtb: xschem netlisted tb_%s.sch (latch from latch.sch: %s%s)"
                  % (n, "yes" if has_latch else "NO",
                     "; comparator from comparator.sch: %s" % ("yes" if has_cmp else "NO") if n == "kick" else ""))
            ok_all &= has_latch and has_cmp
    if not ok_all:
        return 1

    jobs = {
        "x_drive": lambda: run_xschem("drive", nets["drive"]),
        "x_aperture": lambda: run_xschem("aperture", nets["aperture"]),
        "x_kick": lambda: run_xschem("kick", nets["kick"], geom=True),
        "x_kick_nogeom": lambda: run_xschem("kick", nets["kick"], geom=False),
        "r_drive": lambda: B.drive_case("xtb_ref_drive"),
        "r_aperture": lambda: B.aperture_case(T.AP_DT, "xtb_ref_aperture"),
        "r_kick": ref_kick,
    }
    with ThreadPoolExecutor(max_workers=min(B.JOBS, len(jobs))) as ex:
        futs = {k: ex.submit(f) for k, f in jobs.items()}
        res = {k: f.result() for k, f in futs.items()}

    rows = []

    def gate(bench_name, metric, x, b, tol, unit="ps", scale=1e12):
        nonlocal ok_all
        diff = x - b
        good = x == x and b == b and abs(diff) <= tol
        ok_all &= bool(good)
        rows.append((bench_name, metric, "nogeom" if bench_name == "kick" else "as drawn", b, x, diff))
        print("%s: xtb %s %s: schematic %.6g ns, bench %.6g ns (diff %.3g %s; tol %g %s)"
              % ("PASS" if good else "FAIL", bench_name, metric, x * 1e9, b * 1e9, diff * scale, unit, tol * scale, unit))
        print("xtb_%s_%s_ns = %.6g" % (bench_name, metric, x * 1e9))

    # drive: the first q fall after d falls at 412.5 ns (sampling edge 425 ns)
    xd, rd = res["x_drive"], res["r_drive"]
    gate("drive", "tcq", xd.get("tcq", float("nan")), rd.get("tcq_f1_ns", float("nan")) * 1e-9, TOL_LATCH)
    gate("drive", "q_fall", xd.get("q_fall", float("nan")), rd.get("q_edge_f1_ns", float("nan")) * 1e-9, TOL_LATCH)

    # aperture: one fall, no rise, on the same edge, same clock-to-q and fall
    xa, ra = res["x_aperture"], res["r_aperture"]
    n_fall = (1 if "t_q" in xa else 0) + (1 if "t_q2" in xa else 0)
    n_rise = 1 if "t_qr" in xa else 0
    edge = int(round(xa.get("edge_k", -1)))
    counts_ok = n_fall == ra.get("n_fall") == 1 and n_rise == ra.get("n_rise") == 0 and edge == ra.get("edge")
    ok_all &= counts_ok
    print("%s: xtb aperture DT = %g ns: q falls %d time(s) (bench %s), rises %d (bench %s), on sampling edge %d (bench %s)"
          % ("PASS" if counts_ok else "FAIL", T.AP_DT * 1e9, n_fall, ra.get("n_fall"), n_rise, ra.get("n_rise"),
             edge, ra.get("edge")))
    rows.append(("aperture", "n_fall", "as drawn", ra.get("n_fall", float("nan")), n_fall, n_fall - ra.get("n_fall", 0)))
    gate("aperture", "tcq", xa.get("tcq", float("nan")), ra.get("tcq_ns", float("nan")) * 1e-9, TOL_LATCH)
    gate("aperture", "q_fall", xa.get("q_fall", float("nan")), ra.get("q_fall_ns", float("nan")) * 1e-9, TOL_LATCH)

    # kick: the comparator drawing carries S/D geometry the deck lacks; gate without it, report as drawn
    xk, xkn, rk = res["x_kick"], res["x_kick_nogeom"], res["r_kick"]
    for k in ("t_cross", "t_dout", "t_q", "dout_fall"):
        gate("kick", k, xkn.get(k, float("nan")), rk.get(k, float("nan")), TOL_KICK)
    for k in ("t_cross", "t_dout", "t_q", "delay", "dout_fall"):
        x, b = xk.get(k, float("nan")), rk.get(k, float("nan"))
        rows.append(("kick", k, "geom", b, x, x - b))
        print("REPORT: xtb kick as drawn (S/D geometry) %s: schematic %.6g ns, bench %.6g ns, %+.3g ps"
              % (k, x * 1e9, b * 1e9, (x - b) * 1e12))
        print("xtb_kick_geom_%s_ns = %.6g" % (k, x * 1e9))
    for lab, m in (("as drawn", xk), ("nogeom", xkn)):
        print("REPORT: xtb kick plate step across the sampling edge before the crossing, the plate's own slope removed (%s): %.3g uV "
              "= %.2g LSB; clock-to-q %.4g ns" % (lab, m.get("plate_step", float("nan")) * 1e6,
                                                 m.get("plate_step", float("nan")) / B.LSB, m.get("tcq", float("nan")) * 1e9))
    print("xtb_kick_plate_step_uv = %.6g" % (xk.get("plate_step", float("nan")) * 1e6))
    print("xtb_kick_tcq_ns = %.6g" % (xk.get("tcq", float("nan")) * 1e9))

    with open(os.path.join(B.DATA, "xtb.csv"), "w") as h:
        h.write("bench,metric,variant,bench_value,xschem_value,diff\n")
        for r in rows:
            h.write("%s,%s,%s,%.10g,%.10g,%.6g\n" % r)
    print("PASS: xtb: every testbench drawing reproduces its bench" if ok_all else "FAIL: xtb")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
