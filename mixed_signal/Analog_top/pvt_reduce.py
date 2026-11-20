#!/usr/bin/env python3
"""pvt_reduce.py -- one row per PVT cell of the `pvt` phase.

    python3 pvt_reduce.py <cell> [<cell> ...]

Reads, per cell, work/pvt/<cell>/{func_measures.txt, func_reduce.txt,
check.txt, sim.txt} (pvt_cell.sh) and the typical record's codes
(data/func_measures.txt, the `func` phase). Writes data/pvt_cells.csv, read by
check-pvt.awk and by the slides, and prints one REPORT line per cell plus
pvt_* metrics (`name = value`).

Columns (per cell):
  g_<gate>         check-func.awk's verdict at this cell (PASS / FAIL / NA)
  code<k>, dcode<k>   code and its difference from the typical record
  decided_once     every q_k fell exactly once in (TR, TE + TOVR] and never again
  codes_inc        code0 < code1 < code2 < code3
  gain_err_pct, offset_lsb, res_max_lsb   trip-count line over the four cells
                   (xfer_d_*: dout's fall, the gated transfer)
  plate_spread_lsb max - min of bps_err_k (input-referred error at the crossing)
  armed_mv         smallest vref(TR) - bot_k(TR)
  seq_gap_min_ns   smallest S2 -> S0 or S0 -> S1 gap of the four cells
  seq_gap_t4_min   the same in units of the cell's four-inverter delay (ADR 0031)
  bot_max_v        highest bottom plate from S1 closing to TSTOP
  pw_*_uw          AVDD / DVDD / total over the ramp; pw_track_uw over [T0, TS0]
"""
import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATES = ["sequencer", "bias", "references", "vrlo", "sample", "plate", "armed", "decision", "latch",
         "range", "order", "transfer", "rails"]
NAN = float("nan")


def kv(path):
    m = {}
    if not os.path.exists(path):
        return m
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) >= 3 and p[1] == "=":
                try:
                    m[p[0]] = float(p[2])
                except ValueError:
                    m[p[0]] = NAN
    return m


def fmt(v):
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "nan"
    if isinstance(v, int):
        return "%d" % v
    return "%.6g" % v


def main(cells):
    typ = kv(os.path.join(HERE, "data", "func_measures.txt"))
    rows = []
    for cell in cells:
        d = os.path.join(HERE, "work", "pvt", cell)
        c, t, v = cell.split("_")
        m = kv(os.path.join(d, "func_measures.txt"))
        r = kv(os.path.join(d, "func_reduce.txt"))
        s = kv(os.path.join(d, "sim.txt"))
        g = {}
        if os.path.exists(os.path.join(d, "check.txt")):
            for line in open(os.path.join(d, "check.txt")):
                for gate in GATES:
                    for verd in ("PASS", "FAIL"):
                        if line.startswith("%s: %s:" % (verd, gate)):
                            g[gate] = verd
        get = lambda k, src=None: (src if src is not None else {**m, **r}).get(k, NAN)
        row = dict(cell=cell, corner=c, temp=int(t), vdd=float(v),
                   sim_s=s.get("sim_seconds", NAN), sim_status=s.get("sim_status", NAN),
                   n_meas=len(m))
        for gate in GATES:
            row["g_" + gate] = g.get(gate, "NA")
        bad = [gate for gate in GATES if row["g_" + gate] != "PASS"]
        row["n_fail"] = len(bad)
        row["failed"] = ";".join(bad)
        codes = [get("code%d" % k) for k in range(4)]
        for k in range(4):
            row["code%d" % k] = codes[k]
            row["dcode%d" % k] = codes[k] - typ.get("code%d" % k, NAN)
        qf = [get("q_falls%d" % k) for k in range(4)]
        qa = [get("q_falls_all%d" % k) for k in range(4)]
        qr = [get("q_rises_all%d" % k) for k in range(4)]
        row["decided_once"] = int(all(a == 1 for a in qf) and all(a == 1 for a in qa) and all(a == 0 for a in qr))
        row["codes_inc"] = int(all(not math.isnan(x) for x in codes) and all(codes[k] > codes[k - 1] for k in range(1, 4)))
        row["gain_err_pct"] = get("xfer_d_gain_err_pct")
        row["offset_lsb"] = get("xfer_d_offset_lsb")
        row["res_max_lsb"] = get("xfer_d_res_max_lsb")
        row["code_gain_err_pct"] = get("xfer_q_gain_err_pct")
        be = [get("bps_err%d" % k) for k in range(4)]
        row["plate_mean_lsb"] = sum(be) / 4
        row["plate_spread_lsb"] = max(be) - min(be)
        vref_tr = get("vref_at_tr")
        row["armed_mv"] = min((vref_tr - get("vbot_tr%d" % k)) * 1e3 for k in range(4))
        gaps = [get("seq_g20_%d" % k) for k in range(4)] + [get("seq_g01_%d" % k) for k in range(4)]
        row["seq_gap_min_ns"] = min(gaps) * 1e9
        # ADR 0031: the gaps in units of each cell's own four-inverter delay
        row["seq_gap_t4_min"] = min(min(get("seq_g20_%d" % k), get("seq_g01_%d" % k)) / get("seq_t4_%d" % k)
                                    for k in range(4))
        row["seq_t4_max_ns"] = max(get("seq_t4_%d" % k) for k in range(4)) * 1e9
        row["seq_ap_max_ns"] = max(get("seq_ap_%d" % k) for k in range(4)) * 1e9
        tsp = get("p_tspace")
        row["seq_space_dev_ns"] = max(abs(get("seq_sp_%d" % k) - tsp) for k in range(1, 4)) * 1e9
        row["bot_max_v"] = max(get("vbot_max%d" % k) for k in range(4))
        row["bot_min_v"] = min(get("vbot_min%d" % k) for k in range(4))
        row["cmp_delay_min_ns"] = min(get("cmp_delay%d" % k) for k in range(4)) * 1e9
        row["cmp_delay_max_ns"] = max(get("cmp_delay%d" % k) for k in range(4)) * 1e9
        row["tcq_max_ns"] = max(get("latch_tcq%d_ns" % k) for k in range(4))
        row["alpha_min"] = get("alpha_min")
        row["pw_total_uw"] = get("pw_total_uw")
        row["pw_avdd_uw"] = get("pw_avdd_uw")
        row["pw_dvdd_uw"] = get("pw_dvdd_uw")
        row["pw_track_uw"] = get("pw_avdd_idle_uw") + get("pw_dvdd_idle_uw")
        row["vrlo_err_mv"] = get("vrlo_err_tr_mv")
        row["vref_err_mv"] = get("vref_err_ts0") * 1e3
        row["settle_max_ns"] = max(get("settle_%s_ns" % n) for n in ("pbias0", "pbias_r", "vref", "vrlo", "vramp"))
        row["ramp_gain_err_pct"] = get("ramp_gain_err_pct")
        row["ramp_inl_lsb"] = get("ramp_inl_bf_lsb")
        row["lsb_mv"] = get("p_lsb") * 1e3
        rows.append(row)
        print("REPORT: pvt %s: %s; codes %s / %s / %s / %s (vs typical %+g/%+g/%+g/%+g); gain %+.2f %%, residual %.3f LSB, "
              "plate spread %.3f LSB, armed %.1f mV, sequencer gap %.2f ns, bottom plate max %.3f V, comparator delay %.2f-%.2f ns, "
              "%.0f uW over the ramp, %.0f uW tracking, simulated in %.0f s"
              % (cell, "every check-func gate PASS" if not bad else "FAIL " + ",".join(bad),
                 fmt(codes[0]), fmt(codes[1]), fmt(codes[2]), fmt(codes[3]),
                 row["dcode0"], row["dcode1"], row["dcode2"], row["dcode3"], row["gain_err_pct"], row["res_max_lsb"],
                 row["plate_spread_lsb"], row["armed_mv"], row["seq_gap_min_ns"], row["bot_max_v"],
                 row["cmp_delay_min_ns"], row["cmp_delay_max_ns"], row["pw_total_uw"], row["pw_track_uw"], row["sim_s"]))
    out = os.path.join(HERE, "data", "pvt_cells.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for row in rows:
            w.writerow({k: fmt(x) for k, x in row.items()})
    ok = [x for x in rows if x["n_meas"] > 0]
    print("pvt_n_with_measures = %d" % len(ok))
    print("pvt_n_all_gates_pass = %d" % sum(1 for x in rows if x["n_fail"] == 0))
    for k, f in (("res_max_lsb", max), ("plate_spread_lsb", max), ("armed_mv", min), ("seq_gap_min_ns", min),
                 ("bot_max_v", max), ("pw_total_uw", max), ("cmp_delay_max_ns", max), ("gain_err_pct", min)):
        vals = [x[k] for x in ok if not math.isnan(x[k])]
        if vals:
            print("pvt_worst_%s = %.6g" % (k, f(vals)))
    print("Measures: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
