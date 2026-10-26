# check-ct.awk -- acceptance of the cell_trannoise bench (ct_reduce.py output).
# One PASS:/FAIL: line per criterion, a final verdict, non-zero exit on any FAIL.
#
#   translation  noiseless VACASK vs ngspice on the same bench: codes identical except
#                where a clock edge lies between the two decisions; mean decision within
#                0.1 LSB; frozen sample within 0.3 mV
#   nf1          the finger expansion moves the noiseless decision by <= 0.02 LSB
#   aligned      the noiseless decision lies within 1 ns of the Clk edge (the setup the
#                figure needs: noise alone picks Clk or Clk+1)
#   complete     every noisy conversion: armed at TR, one q fall, a dout fall
#   capture      every q fell on Clk or Clk+1, no other edge
#   match        dout before Clk <=> q on Clk, for every conversion more than 1 ns from Clk
#   share        the share on Clk+1 agrees with dout's share after Clk within 3 standard errors
#   floor        noiseless spread <= 0.1 x the noisy sigma
#   total        sigma <= 0.25 LSB: the noise share of the ENOB-7 budget (ADR 0013)
#   groups       the four blocks alone, added in power, agree with all-on within 3 standard errors
#   band         noisefmax 6 GHz vs 2 GHz: sigma and the frozen-sample spread agree within 3 se
#   reltol       reltol 2e-7 vs 1e-6 at c240: mean decision and sigma agree within 3 se
function abs(x) { return x < 0 ? -x : x }
function ok(cond, msg) { if (cond) print "PASS: " msg; else { print "FAIL: " msg; bad++ } ; n++ }
/^[a-z_0-9]+ = / { v[$1] = $3 + 0; has[$1] = 1 }
END {
    split("c16 c240", L, " ")
    for (i = 1; i <= 2; i++) {
        t = "ct_" L[i] "_"
        if (!has[t "sigma_lsb"]) { print "FAIL: " L[i] ": no noisy result"; bad++; continue }
        ok(v[t "xchk_codes_unexplained"] == 0, sprintf("%s translation: VACASK noiseless codes equal ngspice's (%d records; %d differ, each with a clock edge between the two decisions)", L[i], v[t "xchk_records"], v[t "xchk_codes_differ"]))
        ok(abs(v[t "xchk_dtd_lsb"]) <= 0.1, sprintf("%s translation: decision VACASK - ngspice %+.4f LSB (<= 0.1)", L[i], v[t "xchk_dtd_lsb"]))
        ok(abs(v[t "xchk_dtm_mv"]) <= 0.3, sprintf("%s translation: frozen sample VACASK - ngspice %+.3f mV (<= 0.3)", L[i], v[t "xchk_dtm_mv"]))
        ok(abs(v[t "nf1_dtd_lsb"]) <= 0.02, sprintf("%s finger expansion moves the noiseless decision %+.4f LSB (<= 0.02)", L[i], v[t "nf1_dtd_lsb"]))
        ok(abs(v[t "quiet_td_minus_clk_ns"]) <= 1, sprintf("%s aligned: noiseless decision %+.3f ns from Clk (edge %d, POS %.4f; <= 1 ns)", L[i], v[t "quiet_td_minus_clk_ns"], v[t "clk_edge"], v[t "pos"]))
        ok(v[t "bad_conversions"] == 0, sprintf("%s complete: %d of %d conversions not armed at TR or without exactly one q fall", L[i], v[t "bad_conversions"], v[t "conversions"]))
        printf "REPORT: %s: dout crossed VDD/2 more than once in %d of %d conversions (the latch took the first)\n", L[i], v[t "dout_chatter"], v[t "conversions"]
        ok(v[t "q_other_edge"] == 0, sprintf("%s capture: q on Clk %d, on Clk+1 %d, on another edge %d", L[i], v[t "q_on_clk"], v[t "q_on_clk1"], v[t "q_other_edge"]))
        ok(v[t "match_mismatch_outside"] == 0, sprintf("%s match: dout before Clk <=> q on Clk in every conversion more than 1 ns from Clk (%d mismatches outside, %d in all, %d conversions within 1 ns; best boundary %+.3f ns with %d)", L[i], v[t "match_mismatch_outside"], v[t "match_mismatch"], v[t "match_near_edge"], v[t "match_boundary_ns"], v[t "match_boundary_mismatch"]))
        ok(abs(v[t "frac_clk1"] - v[t "frac_clk1_dout"]) <= 3 * v[t "frac_clk1_se"], sprintf("%s share on Clk+1 %.3f vs dout after Clk %.3f (3 se %.3f); Gaussian %.3f", L[i], v[t "frac_clk1"], v[t "frac_clk1_dout"], 3 * v[t "frac_clk1_se"], v[t "frac_clk1_gauss"]))
        ok(v[t "floor_over_sigma"] <= 0.1, sprintf("%s numerical floor %.4f LSB = %.3f x sigma (<= 0.1)", L[i], v[t "floor_lsb"], v[t "floor_over_sigma"]))
        ok(v[t "sigma_lsb"] <= 0.25, sprintf("%s total transient noise %.4f +- %.4f LSB (<= 0.25)", L[i], v[t "sigma_lsb"], v[t "sigma_ci95_lsb"]))
        if (has[t "groups_rss_over_total"])
            ok(abs(v[t "groups_rss_over_total"] - 1) <= v[t "groups_rss_over_total_tol"], sprintf("%s groups: ramp %.4f, cmp %.4f, ff %.4f, sw %.4f LSB; RSS %.4f / total = x%.3f (tol %.3f)", L[i], v[t "g_ramp_sigma_lsb"], v[t "g_cmp_sigma_lsb"], v[t "g_ff_sigma_lsb"], v[t "g_sw_sigma_lsb"], v[t "groups_rss_lsb"], v[t "groups_rss_over_total"], v[t "groups_rss_over_total_tol"]))
        else { print "FAIL: " L[i] ": no group breakdown"; bad++ }
    }
    if (has["ct_band_sigma_ratio"]) {
        ok(abs(v["ct_band_sigma_ratio"] - 1) <= v["ct_band_ratio_tol"], sprintf("band: sigma at 6 GHz / 2 GHz x%.3f (tol %.3f)", v["ct_band_sigma_ratio"], v["ct_band_ratio_tol"]))
        ok(abs(v["ct_band_tm_ratio"] - 1) <= v["ct_band_ratio_tol"], sprintf("band: frozen-sample spread at 6 GHz / 2 GHz x%.3f (tol %.3f)", v["ct_band_tm_ratio"], v["ct_band_ratio_tol"]))
    } else { print "FAIL: band: no 6 GHz result"; bad++ }
    if (has["ct_tol_dmean_lsb"]) {
        ok(abs(v["ct_tol_dmean_lsb"]) <= v["ct_tol_dmean_tol_lsb"], sprintf("reltol: c240 mean decision at 2e-7 - 1e-6 %+.4f LSB (tol %.4f; %d conversions)", v["ct_tol_dmean_lsb"], v["ct_tol_dmean_tol_lsb"], v["ct_tol_conversions"]))
        ok(abs(v["ct_tol_sigma_ratio"] - 1) <= v["ct_tol_ratio_tol"], sprintf("reltol: c240 sigma at 2e-7 / 1e-6 x%.3f (tol %.3f)", v["ct_tol_sigma_ratio"], v["ct_tol_ratio_tol"]))
    } else { print "FAIL: reltol: no 2e-7 result"; bad++ }
    if (bad) { printf "FAIL: cell_trannoise: %d of %d checks failed\n", bad, n; exit 1 }
    printf "PASS: cell_trannoise: %d checks\n", n
}
