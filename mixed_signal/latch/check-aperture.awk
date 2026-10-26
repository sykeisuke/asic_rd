# Acceptance on data/aperture.csv (tb_aperture.spice, bench.py aperture):
# dout's falling edge swept across the sampling edge (-4 .. +4 ns in 0.25 ns),
# bisected onto the decision boundary to 1 fs, then placed 1e-10 .. 1e-15 s
# either side of it. Slow d (comparator's slowest dout fall, 10.4 ns) at
# typical, ss 0 C 3.0 V and ff 85 C 3.6 V; fast d (1 ns) at typical. Clock edge
# 0.5 ns.
#
#   awk -f check-aperture.awk data/aperture.csv
#
# Gates (SPEC.md S7), on every row -- the property the TSPC needed its keeper
# for (../latch_bkp/cmp_tspc/SPEC.md s.3.3: without it q fell twice when dout arrived at
# the sampling edge, a lost conversion):
#   one edge   q falls exactly once and never rises
#   no runt    before its fall, q stays above VDD/2 + 0.3 V
#   stays low  after its fall q stays below VDD/2 - 0.3 V to the end of the run
#   in time    q crosses VDD/2 less than 75 ns after the edge that decided
# REPORT: slowest clock-to-q, slowest fall, deepest pre-fall dip.
BEGIN { FS = ","; fail = 0; late = 75 }
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
{
    n++
    tag = $c["tag"]; vdd = $c["vdd"] + 0; runt = vdd / 2 + 0.3; low = vdd / 2 - 0.3
    if ($c["ok"] != 1) { printf "FAIL: aperture %s: ngspice did not complete\n", tag; fail = 1; next }
    if (!($c["n_fall"] == 1 && $c["n_rise"] == 0)) { bad1++; printf "FAIL: aperture %s: q falls %s times and rises %s times\n", tag, $c["n_fall"], $c["n_rise"] }
    m = $c["q_min_pre"] + 0
    if (m < runt) { bad2++; printf "FAIL: aperture %s: q dips to %.2f V before its fall (limit %.2f V)\n", tag, m, runt }
    if (minpre == "" || m - vdd < minpre) { minpre = m - vdd; mintag = tag }
    p = $c["q_max_post"] + 0
    if (p > low) { bad4++; printf "FAIL: aperture %s: q comes back to %.2f V after its fall\n", tag, p }
    if (p > pmax) pmax = p
    t = $c["tcq_ns"] + 0
    if (!(t > 0 && t < late)) { bad3++; printf "FAIL: aperture %s: clock-to-q %.2f ns\n", tag, t }
    if (t > tmax) { tmax = t; ttag = tag }
    if ($c["q_fall_ns"] + 0 > fmax) fmax = $c["q_fall_ns"] + 0
}
END {
    if (n == 0) { print "FAIL: aperture table is empty"; exit 1 }
    if (bad1 == 0) printf "PASS: aperture: q makes exactly one fall and no rise in all %d runs (down to 1 fs from the boundary, 3 cells)\n", n
    if (bad2 == 0) printf "PASS: aperture: q never dips towards VDD/2 + 0.3 V before its fall (deepest %.0f mV below VDD, %s)\n", -minpre * 1e3, mintag
    if (bad4 == 0) printf "PASS: aperture: q stays low after its fall in every run (highest %.0f mV)\n", pmax * 1e3
    if (bad3 == 0) printf "PASS: aperture: q crosses VDD/2 within %.2f ns of its deciding edge in every run (< %d ns)\n", tmax, late
    fail = (fail || bad1 || bad2 || bad3 || bad4)
    printf "meas_aperture_tcq_max_ns = %g\n", tmax
    printf "meas_aperture_qfall_max_ns = %g\n", fmax
    printf "meas_aperture_qdip_pre_mv = %g\n", -minpre * 1e3
    printf "REPORT: aperture: slowest clock-to-q %.2f ns (%s, at the boundary), slowest q fall %.2f ns\n", tmax, ttag, fmax
    exit fail
}
