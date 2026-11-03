# check-seq.awk -- judge sample_seq's rows (SPEC.md Q1-Q8).
#
#   awk -v set=pvt -f check-seq.awk data/pvt.csv      (set = typ | pvt | duty)
#
# One PASS:/FAIL: line per requirement over every row of the file; REPORT:
# lines carry the extremes. Exits non-zero on any FAIL.
BEGIN { FS = ","; gap = 5.0; s0max = 15.0; s21max = 25.0; sptol = 0.05; apmax = 2.0; bad = 0 }
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
function v(k) { return (k in c) ? $(c[k]) : "nan" }
function lo(name, x) { if (!(name in mn) || x + 0 < mn[name] + 0) { mn[name] = x; mt[name] = v("tag") } }
function hi(name, x) { if (!(name in mx) || x + 0 > mx[name] + 0) { mx[name] = x; xt[name] = v("tag") } }
{
    n++
    if (v("sim_ok") != 1) { simfail++; ft = ft " " v("tag"); next }
    if (v("order_ok") != 1) { ordfail++; ot = ot " " v("tag") }
    if (v("static_ok") != 1) { stfail++; stt = stt " " v("tag") }
    if (v("n_glitch") != 0) { glfail++; gt = gt " " v("tag") }
    lo("g20", v("g20_min_ns")); lo("g01", v("g01_min_ns")); lo("gre", v("gre_min_ns"))
    hi("g20", v("g20_max_ns")); hi("g01", v("g01_max_ns"))
    hi("s0open", v("s0open_max_ns")); hi("s2s1", v("s2s1_max_ns"))
    hi("ap", v("aperture_max_ns")); lo("ap", v("aperture_min_ns"))
    hi("sp", v("spacing_err_max_ns"))
    hi("ptrack", v("p_track_uw")); hi("phold", v("p_hold_uw"))
    hi("eent", v("e_entry_pj")); hi("eree", v("e_reentry_pj"))
    if (v("c0_edges_track") != 0 || v("c0_edges_hold") != 0) { gatefail++; gtt = gtt " " v("tag") }
    hi("ce", v("c0_edges_entry")); lo("ce", v("c0_edges_entry"))
}
function verdict(ok, msg) { if (ok) print "PASS: " msg; else { print "FAIL: " msg; bad = 1 } }
END {
    p = "sample_seq " set " (" n " runs): "
    verdict(simfail == 0, p "every run finished" (simfail ? ", not:" ft : ""))
    if (simfail == n) exit 1
    verdict(ordfail == 0, p "Q1 order S2 open < S0 open < S1 closed, re-entry S1 open before S0 closes, every cell" (ordfail ? ", not:" ot : ""))
    verdict(stfail == 0, p "Q6 tracking state before the record (s2 = s0 = 1, s1 = 0)" (stfail ? ", not:" stt : ""))
    verdict(glfail == 0, p "Q6 one edge per control per direction in the record" (glfail ? ", not:" gt : ""))
    verdict(mn["g20"] >= gap, sprintf("%sQ2 S2 -> S0 >= %.1f ns: min %.3f ns (%s), max %.3f ns (%s)", p, gap, mn["g20"], mt["g20"], mx["g20"], xt["g20"]))
    verdict(mn["g01"] >= gap, sprintf("%sQ2 S0 -> S1 >= %.1f ns: min %.3f ns (%s), max %.3f ns (%s)", p, gap, mn["g01"], mt["g01"], mx["g01"], xt["g01"]))
    verdict(mn["gre"] >= gap, sprintf("%sQ2 re-entry S1 open -> S0 closed >= %.1f ns: min %.3f ns (%s)", p, gap, mn["gre"], mt["gre"]))
    verdict(mx["s0open"] <= s0max, sprintf("%sQ3 S0 open <= %.1f ns after the clock edge: max %.3f ns (%s)", p, s0max, mx["s0open"], xt["s0open"]))
    verdict(mx["s2s1"] <= s21max, sprintf("%sQ3 S2 open -> S1 closed <= %.1f ns: max %.3f ns (%s)", p, s21max, mx["s2s1"], xt["s2s1"]))
    verdict(mx["sp"] <= sptol, sprintf("%sQ4 cells %.0f ns apart within %.2f ns: max error %.4f ns (%s)", p, 50, sptol, mx["sp"], xt["sp"]))
    verdict(mx["ap"] <= apmax, sprintf("%sQ5 S2 opens <= %.1f ns after the clock edge: %.3f-%.3f ns (%s)", p, apmax, mn["ap"], mx["ap"], xt["ap"]))
    verdict(gatefail == 0, p "Q7 delay line gated: no clock edge in it while tracking or holding" (gatefail ? ", not:" gtt : ""))
    printf "REPORT: %sQ7 gated clock edges per entry %d-%d\n", p, mn["ce"], mx["ce"]
    printf "REPORT: %sQ8 DVDD power tracking max %.2f uW (%s), holding max %.2f uW (%s); energy per entry max %.1f pJ (%s), per re-entry %.1f pJ (%s)\n", p, mx["ptrack"], xt["ptrack"], mx["phold"], xt["phold"], mx["eent"], xt["eent"], mx["eree"], xt["eree"]
    exit bad
}
