# Acceptance on data/pvt.csv (bench_pvt.py pvt, run.sh phase `pvt`, opt-in):
# the drive and aperture benches of bench.py at 45 PVT cells (5 corners x
# 0/27/85 C x 3.0/3.3/3.6 V), slow d (10.4 ns), clock edge 0.5 ns, q into 50 fF.
#
#   awk -f check-pvt.awk data/pvt.csv
#
# Gates (SPEC.md), every cell:
#   S2/S5  drive: q moves once at each of the 4 sampling edges, static levels
#          within 1.0 V of the rails
#   S3     load on dout <= 10 fF
#   S4     clock-to-q (fall) <= 20 ns; q 90-10 % fall into 50 fF <= 2.15 ns
#   S7     aperture: a clean boundary between the two edges; in every run
#          (bisected to 1 fs, then 1e-10 .. 1e-15 s either side) q falls exactly
#          once and never rises, no dip towards VDD/2 + 0.3 V before the fall,
#          stays below VDD/2 - 0.3 V after it, crosses VDD/2 < 75 ns after the
#          deciding edge
# REPORT (not judged): power with d high / low, leakage, tau, slowest
# clock-to-q at the boundary, each with the cell that sets it.
BEGIN { FS = ","; fail = 0 }
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
function upd(name, val, cell, hi) {
    if (!(name in best) || (hi && val > best[name]) || (!hi && val < best[name])) { best[name] = val; who[name] = cell }
}
{
    n++
    cell = $c["cell"]
    if ($c["drive_ok"] != 1) { printf "FAIL: pvt %s: drive bench did not complete\n", cell; bad_sim++ }
    if ($c["drive_pass"] != 1) { printf "FAIL: pvt %s: drive: q edges %s / static levels high %.2f low %.2f V\n", cell, $c["n_qedges"], $c["q_min_high"], $c["q_max_low"]; bad_drive++ }
    cin = $c["cin_max_ff"] + 0; if (cin > 10) { printf "FAIL: pvt %s: dout load %.2f fF\n", cell, cin; bad_cin++ }
    t = $c["tcq_f1_ns"] + 0; if ($c["tcq_f0_ns"] + 0 > t) t = $c["tcq_f0_ns"] + 0
    if (!(t > 0 && t <= 20)) { printf "FAIL: pvt %s: clock-to-q %.3f ns\n", cell, t; bad_tcq++ }
    f = $c["q_edge_f1_ns"] + 0; if ($c["q_edge_f0_ns"] + 0 > f) f = $c["q_edge_f0_ns"] + 0
    if (!(f > 0 && f <= 2.15)) { printf "FAIL: pvt %s: q fall %.3f ns\n", cell, f; bad_fall++ }
    if ($c["ap_boundary"] != 1) { printf "FAIL: pvt %s: aperture: no clean boundary on the coarse grid\n", cell; bad_bnd++ }
    if ($c["ap_n_failed_sim"] + 0 > 0) { printf "FAIL: pvt %s: aperture: %d runs did not complete\n", cell, $c["ap_n_failed_sim"]; bad_sim++ }
    a1 = $c["ap_n_not_one_fall"] + 0; a2 = $c["ap_n_runt"] + 0; a3 = $c["ap_n_back_high"] + 0; a4 = $c["ap_n_late"] + 0
    if (a1) { printf "FAIL: pvt %s: aperture: %d runs where q does not fall exactly once\n", cell, a1; bad_ap1++ }
    if (a2) { printf "FAIL: pvt %s: aperture: %d runs dip towards VDD/2 + 0.3 V before the fall\n", cell, a2; bad_ap2++ }
    if (a3) { printf "FAIL: pvt %s: aperture: %d runs where q comes back above VDD/2 - 0.3 V\n", cell, a3; bad_ap3++ }
    if (a4) { printf "FAIL: pvt %s: aperture: %d runs later than 75 ns\n", cell, a4; bad_ap4++ }
    nap += $c["ap_n_runs"]
    upd("tcq", t, cell, 1); upd("tcqmin", t, cell, 0); upd("fall", f, cell, 1); upd("cin", cin, cell, 1)
    upd("aptcq", $c["ap_tcq_max_ns"] + 0, cell, 1); upd("tau", $c["ap_tau_ps"] + 0, cell, 1); upd("taumin", $c["ap_tau_ps"] + 0, cell, 0)
    p = $c["p_dhigh_uw"] + 0; if ($c["p_dlow_uw"] + 0 > p) p = $c["p_dlow_uw"] + 0
    upd("pmax", p, cell, 1); upd("pmin", p, cell, 0); upd("leak", $c["i_leak_na"] + 0, cell, 1)
    upd("apfall", $c["ap_fall_max_ns"] + 0, cell, 1)
}
END {
    if (n != 45) { printf "FAIL: pvt table has %d cells, expected 45\n", n; fail = 1 }
    if (n == 0) exit 1
    if (!bad_sim) printf "PASS: pvt (%d cells): every drive and aperture run completed (%d aperture runs)\n", n, nap
    if (!bad_drive) printf "PASS: pvt (%d cells): drive: q moves once at each of the 4 sampling edges, static levels within 1.0 V of the rails\n", n
    if (!bad_cin) printf "PASS: pvt (%d cells): load on dout <= 10 fF: max %.2f fF (%s)\n", n, best["cin"], who["cin"]
    if (!bad_tcq) printf "PASS: pvt (%d cells): clock-to-q (fall) <= 20 ns: %.3f (%s) .. %.3f ns (%s)\n", n, best["tcqmin"], who["tcqmin"], best["tcq"], who["tcq"]
    if (!bad_fall) printf "PASS: pvt (%d cells): q 90-10 %% fall into 50 fF <= 2.15 ns: max %.3f ns (%s), no buffer\n", n, best["fall"], who["fall"]
    if (!bad_bnd) printf "PASS: pvt (%d cells): aperture: a clean boundary between the two sampling edges at every cell\n", n
    if (!bad_ap1) printf "PASS: pvt (%d cells): aperture: q falls exactly once and never rises in all %d runs (to 1 fs from the boundary)\n", n, nap
    if (!bad_ap2) printf "PASS: pvt (%d cells): aperture: no dip towards VDD/2 + 0.3 V before the fall\n", n
    if (!bad_ap3) printf "PASS: pvt (%d cells): aperture: q stays below VDD/2 - 0.3 V after its fall\n", n
    if (!bad_ap4) printf "PASS: pvt (%d cells): aperture: q crosses VDD/2 < 75 ns after the deciding edge: slowest %.3f ns (%s)\n", n, best["aptcq"], who["aptcq"]
    fail = (fail || bad_sim || bad_drive || bad_cin || bad_tcq || bad_fall || bad_bnd || bad_ap1 || bad_ap2 || bad_ap3 || bad_ap4)
    printf "meas_pvt_tcq_max_ns = %g\n", best["tcq"]
    printf "meas_pvt_tcq_min_ns = %g\n", best["tcqmin"]
    printf "meas_pvt_qfall_max_ns = %g\n", best["fall"]
    printf "meas_pvt_ap_tcq_max_ns = %g\n", best["aptcq"]
    printf "meas_pvt_ap_qfall_max_ns = %g\n", best["apfall"]
    printf "meas_pvt_tau_max_ps = %g\n", best["tau"]
    printf "meas_pvt_tau_min_ps = %g\n", best["taumin"]
    printf "meas_pvt_power_max_uw = %g\n", best["pmax"]
    printf "meas_pvt_power_min_uw = %g\n", best["pmin"]
    printf "meas_pvt_leak_max_na = %g\n", best["leak"]
    printf "REPORT: pvt: clocked power %.2f (%s) .. %.2f uW (%s), the larger of d high / d low; leakage max %.2f nA (%s)\n", best["pmin"], who["pmin"], best["pmax"], who["pmax"], best["leak"], who["leak"]
    printf "REPORT: pvt: resolution time constant tau %.1f (%s) .. %.1f ps (%s); slowest clock-to-q at the boundary %.3f ns (%s)\n", best["taumin"], who["taumin"], best["tau"], who["tau"], best["aptcq"], who["aptcq"]
    exit fail
}
