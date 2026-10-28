# check-ramp.awk -- acceptance of the ramp generator (DESIGN_RECIPE.md s.1 has
# the derivation of every limit; [D] derived, [A] assumed allocation).
#
#   awk -f check-ramp.awk work/phases_out.txt
#
# Reads the `name = value` lines every phase printed; one PASS:/FAIL: line per
# gate, REPORT: for figures recorded without judgement; exit non-zero on a
# FAIL or on a missing figure.

/^[a-z_0-9]+ = [-+0-9.eEinfa]+/ { v[$1] = $3 + 0; have[$1] = 1 }

function need(k) { if (!(k in have)) { printf "FAIL: figure %s missing (its phase did not run or failed)\n", k; bad = 1; return 0 } return 1 }
function le(k, lim, what) { if (!need(k)) return; ok = (v[k] <= lim); printf "%s: %s %s = %.4g <= %g\n", ok ? "PASS" : "FAIL", what, k, v[k], lim; if (!ok) bad = 1 }
function ge(k, lim, what) { if (!need(k)) return; ok = (v[k] >= lim); printf "%s: %s %s = %.4g >= %g\n", ok ? "PASS" : "FAIL", what, k, v[k], lim; if (!ok) bad = 1 }
function absle(k, lim, what) { if (!need(k)) return; x = v[k] < 0 ? -v[k] : v[k]; ok = (x <= lim); printf "%s: %s |%s| = %.4g <= %g\n", ok ? "PASS" : "FAIL", what, k, x, lim; if (!ok) bad = 1 }
function rep(k, what) { if (k in have) printf "REPORT: %s %s = %.4g\n", what, k, v[k] }

END {
    bad = 0
    # ---- the ramp alone (tb_ramp, 4 full-scale cells of load and kick)
    absle("nom_slope_err_pct", 0.5, "[A] slope at typical within the trim step,")
    le("nom_inl_lsb", 0.05, "[A] ramp INL (best fit, codes 8-256), a fifth of the 0.25 LSB linearity budget:")
    le("nom_inl_ovr_lsb", 0.05, "[A] ramp INL over the 20-count overrun:")
    le("nom_start_settle_k", 4, "[D] start transient inside the dead-zone codes (SPEC_BPS item 13):")
    ge("nom_ns_margin", 0.1, "[A] sink XNS saturation margin VDS - Vdsat (V):")
    ge("nom_m5_margin", 0.1, "[A] XM5 saturation margin at vramp = VR_LO (V):")
    le("nom_vx_span_mv", 0.1, "[D] virtual ground excursion over the ramp (mV):")
    le("nom_rec_ns", 1000, "[A] recovery after the end-of-ramp reset (1 us of dead time per conversion), ns:")
    le("nom_kick_peak_mv", 35, "[D] S1-connection kick of 4 full-scale cells on C_OUT (5 LSB + margin), mV:")
    # load independence: 16 and 64 cells of load and kick against 4
    if (need("n16_slope_err_pct") && need("n64_slope_err_pct") && need("nom_slope_err_pct")) {
        d16 = v["n16_slope_err_pct"] - v["nom_slope_err_pct"]; d64 = v["n64_slope_err_pct"] - v["nom_slope_err_pct"]
        ok = (d64 < 0.05 && d64 > -0.05)
        printf "%s: [D] slope independent of the load: 16 cells %+.4f %%, 64 cells %+.4f %% against 4 (<= 0.05 %%)\n", ok ? "PASS" : "FAIL", d16, d64
        if (!ok) bad = 1
    }
    le("n64_inl_lsb", 0.05, "[A] ramp INL with 64 cells of load:")
    rep("n64_kick_peak_mv", "S1 kick of 64 full-scale cells (C_OUT sized for 4)")
    rep("n64_start_settle_k", "start settling with 64 cells of kick (codes)")
    # supply: slope change per supply change
    if (need("vhi_slope_err_pct") && need("vlo_slope_err_pct")) {
        psr = (v["vhi_slope_err_pct"] - v["vlo_slope_err_pct"]) / 4.0
        x = psr < 0 ? -psr : psr; ok = (x <= 0.2)
        printf "%s: [A] slope supply sensitivity %.4f %%/%% (VDD +-2 %%) <= 0.2\n", ok ? "PASS" : "FAIL", psr
        if (!ok) bad = 1
    }
    rep("pre_start_dev_lsb_0", "with a 300 ns pre-roll: start deviation at code 0 (LSB)")
    rep("nom_offset_lsb", "ramp offset at code 0 against VR_LO (pedestal, LSB)")
    rep("nom_p_total", "")
    # ---- loop
    split("rst r0p5 r1p25 r2p1", cs, " ")
    for (i = 1; i <= 4; i++) {
        ge("loop_" cs[i] "_pm_deg", 55, "[A] phase margin")
        ge("loop_" cs[i] "_gm_db", 10, "[A] gain margin")
        rep("loop_" cs[i] "_fc_hz", "loop crossover")
    }
    ge("loop_rst_t_1k_db", 60, "[D] loop gain at 1 kHz (virtual ground error <= 1.6 V / 1000):")
    rep("loop_n64rst_pm_deg", "phase margin with 64 cells of load (C_OUT unchanged)")
    # ---- noise (frequency domain, exact kernel; F_LO = 1 Hz)
    le("noise_ramp_own_c255_lsb", 0.10, "[A] the ramp generator's own noise at code 255 (LSB rms):")
    le("noise_ramp_total_c255_lsb", 0.15, "[A] ramp noise incl. the shared bias at code 255 (LSB rms):")
    if (need("noise_ramp_total_c255_lsb")) {
        # with the cell's own terms: kT/C 0.051 LSB (SPEC_BPS item 6), comparator 0.024 LSB (VACASK, RESULTS s.11)
        s = sqrt(v["noise_ramp_total_c255_lsb"] ^ 2 + 0.051 ^ 2 + 0.024 ^ 2)
        ok = (s <= 0.25)
        printf "%s: [D] channel noise at code 255 with the ramp: sqrt(ramp^2 + kTC 0.051^2 + cmp 0.024^2) = %.4f <= 0.25 LSB (contract)\n", ok ? "PASS" : "FAIL", s
        if (!ok) bad = 1
    }
    # ---- four cells converting on the real ramp
    if (need("adc4_missing")) { ok = (v["adc4_missing"] == 0); printf "%s: every cell of every four-cell run converted (%d missing of %d)\n", ok ? "PASS" : "FAIL", v["adc4_missing"], v["adc4_conversions"]; if (!ok) bad = 1 }
    ge("coarse_real_monotonic", 1, "32-level coarse transfer on the real ramp monotonic:")
    le("coarse_real_err_spread_lsb", 0.25, "[D] err spread over the coarse levels on the real ramp (contract):")
    le("ramp_inl_lsb", 0.1, "[A] the ramp's own INL in the conversion (real - ideal, after the line):")
    absle("ramp_gain_err_pct", 0.5, "[A] the ramp's own gain error in the conversion (%):")
    absle("ramp_offset_lsb", 2, "[A] the ramp's own offset (calibratable pedestal, LSB):")
    absle("xtr_d1_lsb", 0.1, "[A] the ramp's share of the trip-kick crosstalk, 3 aggressors 1 LSB below the victim (LSB):")
    absle("xtr_d4_lsb", 0.1, "[A] the ramp's share, 4 LSB:")
    absle("xtr_d16_lsb", 0.1, "[A] the ramp's share, 16 LSB:")
    absle("xtr_d0p25_lsb", 0.1, "[A] the ramp's share, 0.25 LSB:")
    split("0p25 1 4 16", xd, " ")
    for (i = 1; i <= 4; i++) { rep("xt_d" xd[i] "_lsb", "trip-kick crosstalk, total (real ramp)"); rep("xti_d" xd[i] "_lsb", "trip-kick crosstalk without the ramp (ideal ramp: VBL, pbias, cells)") }
    absle("xc_v20_lsb", 0.1, "[A] S1-connection crosstalk at code 20, 2 aggressors 0.5 -> 254.5 (LSB):")
    rep("xc_v5_lsb", "S1-connection crosstalk at code 5 (dead-zone region)")
    rep("pre_ramp_inl_lsb", "the ramp's INL with a 300 ns pre-roll")
    rep("adc4_p_ramp_uw", "ramp generator power during the ramp (uW)")
    exit bad
}
