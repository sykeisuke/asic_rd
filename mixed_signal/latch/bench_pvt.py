"""45-cell PVT of latch (opt-in phase `pvt` of run.sh; SPEC.md S2-S5, S7).

    python3 bench_pvt.py pvt     data/pvt.csv (one row per PVT cell),
                                 data/pvt_aperture.csv (every aperture run)

The record of bench.py covers three or four corner cells (typ, ss 0 C 3.0 V,
ff 85 C 3.6 V, ss 85 C 3.0 V). This phase puts the SAME two benches through
every cell of 5 corners x 0/27/85 C x 3.0/3.3/3.6 V, with bench.py's own
functions (imported, not changed):

  drive     bench.drive_case: clock-to-q (fall / rise), q 90-10 % fall into
            50 fF, static levels, dout load, clocked power (d high / d low),
            leakage
  aperture  bench.boundary_scan with the slow d (10.4 ns 10-90 %, the
            comparator's slowest dout fall): coarse grid, bisection onto the
            decision boundary to 1 fs, then 1e-10 .. 1e-15 s either side;
            per cell: the boundary, the resolution time constant tau, the
            slowest clock-to-q, and the count of runs that break S7 (q not
            exactly one fall / a rise / a dip towards VDD/2 + 0.3 V before
            its fall / back above VDD/2 - 0.3 V after it / later than 75 ns)

Also keeps, at typical only, the waveforms of six aperture runs 1e-11, 1e-13
and 1e-15 s either side of the boundary (work/pvt_apwave_*/out.csv) for the
slide figures; nothing is judged on them.

At most JOBS ngspice processes run at a time across all cells (one semaphore
around bench.ngspice); check-pvt.awk judges data/pvt.csv.
"""
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import bench

CORNERS = ["typical", "ff", "ss", "fs", "sf"]
TEMPS = [0, 27, 85]
VDDS = [3.0, 3.3, 3.6]
PVT = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]
if os.environ.get("PVT_SMOKE") == "1":      # flow test only: typical alone (check-pvt then FAILs on the count)
    PVT = [("typical", 27, 3.3)]
LATE = 75e-9                   # S7: q crosses VDD/2 < 75 ns after its deciding edge
WAVE_OFFS = [s * 10.0 ** -e for e in (11, 13, 15) for s in (-1, 1)]

_sem = threading.BoundedSemaphore(bench.JOBS)
_ngspice = bench.ngspice


def _limited(d, timeout=3600, expect="out.csv"):
    with _sem:
        return _ngspice(d, timeout=timeout, expect=expect)


bench.ngspice = _limited


def vtag(v):
    return ("%g" % v).replace(".", "p")


def one_cell(cell):
    c, t, v = cell
    lab = "%s_%d_%s" % (c, t, vtag(v))
    row = {"cell": lab, "corner": c, "temp": t, "vdd": v}
    dr = bench.drive_case("pvt_drive_" + lab, corner=c, temp=t, vdd=v)
    row["drive_ok"] = dr.get("ok", 0)
    row["drive_pass"] = dr.get("pass", 0)
    for k in ("edges_ok", "n_qedges", "tcq_f1_ns", "tcq_f0_ns", "tcq_r0_ns", "tcq_r1_ns", "q_edge_f1_ns",
              "q_edge_f0_ns", "q_edge_r0_ns", "q_edge_r1_ns", "q_min_high", "q_max_low", "cin_max_ff",
              "p_dhigh_uw", "p_dlow_uw", "i_leak_na", "e_qfall_fj"):
        row[k] = dr.get(k, float("nan"))
    s = bench.boundary_scan(bench.TDF_SLOW, "pvt_ap_" + lab, corner=c, temp=t, vdd=v)
    rows = s.pop("rows")
    for r in rows:
        r["cell"] = lab
    ok = [r for r in rows if r.get("ok")]
    row["ap_n_runs"] = len(rows)
    row["ap_n_failed_sim"] = len(rows) - len(ok)
    row["ap_boundary"] = s["boundary"]
    row["ap_dt0_ps"] = s["dt0_ps"]
    row["ap_tau_ps"] = s["tau_ps"]
    row["ap_tcq_max_ns"] = s.get("tcq_max_ns", float("nan"))
    row["ap_fall_max_ns"] = s.get("fall_max_ns", float("nan"))
    runt, low = v / 2 + 0.3, v / 2 - 0.3
    row["ap_n_not_one_fall"] = sum(1 for r in ok if not (r["n_fall"] == 1 and r["n_rise"] == 0))
    row["ap_n_runt"] = sum(1 for r in ok if not (r["q_min_pre"] >= runt))
    row["ap_n_back_high"] = sum(1 for r in ok if r["q_max_post"] > low)
    row["ap_n_late"] = sum(1 for r in ok if not (0 < r["tcq_ns"] * 1e-9 < LATE))
    row["ap_q_min_pre_v"] = min(r["q_min_pre"] for r in ok) if ok else float("nan")
    row["ap_q_max_post_v"] = max(r["q_max_post"] for r in ok) if ok else float("nan")
    if c == "typical" and t == 27 and v == 3.3 and s["boundary"]:
        dt0 = s["dt0_ps"] * 1e-12
        for o in WAVE_OFFS:
            d = bench.render("tb_aperture.spice", "pvt_apwave_%+.0e" % o,
                             {"DT": "%.15e" % (dt0 + o), "TCE": "%.6e" % (bench.T1090_CLK_NOM / 0.8),
                              "TDF": "%.6e" % bench.TDF_SLOW, "CQ": "%.6e" % bench.CQ, "VDD": "%g" % v,
                              "TEMP": "%g" % t, "NETLIST": bench.NETLIST, "SUBCKT": bench.SUBCKT}, c)
            bench.ngspice(d)
    print("pvt %s: drive pass %s, tcq %.3f ns, q fall %.3f ns, %.2f / %.2f uW; aperture %d runs, boundary %s, "
          "tau %.1f ps, tcq max %.3f ns, bad %d/%d/%d/%d" % (
              lab, row["drive_pass"], row["tcq_f1_ns"], row["q_edge_f1_ns"], row["p_dhigh_uw"], row["p_dlow_uw"],
              row["ap_n_runs"], row["ap_boundary"], row["ap_tau_ps"], row["ap_tcq_max_ns"], row["ap_n_not_one_fall"],
              row["ap_n_runt"], row["ap_n_back_high"], row["ap_n_late"]), flush=True)
    return row, rows


def cmd_pvt():
    with ThreadPoolExecutor(max_workers=len(PVT)) as ex:
        res = list(ex.map(one_cell, PVT))
    bench.write_csv(os.path.join(bench.DATA, "pvt.csv"), [r for r, _ in res])
    bench.write_csv(os.path.join(bench.DATA, "pvt_aperture.csv"), [x for _, rows in res for x in rows])


if __name__ == "__main__":
    os.makedirs(bench.WORK, exist_ok=True)
    os.makedirs(bench.DATA, exist_ok=True)
    for a in sys.argv[1:]:
        if a != "pvt":
            raise SystemExit("unknown command %s" % a)
        cmd_pvt()
