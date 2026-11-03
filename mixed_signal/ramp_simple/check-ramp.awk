# check-ramp.awk -- acceptance of ramp_simple against SPEC.md (the R numbers),
# from the `name = value` lines every phase printed. The ramp current is an
# ideal source in this block; what the I/C source must deliver is reported.
#
#   awk -f check-ramp.awk work/phases_out.txt
#
# One PASS:/FAIL: line per gate, REPORT: for figures recorded without
# judgement; exit non-zero on a FAIL or on a missing figure of a phase that ran.

/^[a-z_0-9]+ = [-+0-9.eEinfa]+/ { v[$1] = $3 + 0; have[$1] = 1 }
/^size_/ { ran["size"] = 1 } /^nom_/ { ran["ramp"] = 1 } /^pvt_/ { ran["pvt"] = 1 } /^adc4_(missing|coarse)/ { ran["adc4"] = 1 }
/^src_cases/ { ran["src"] = 1 }

function need(k) { if (!(k in have)) { printf "FAIL: figure %s missing (its phase did not run or failed)\n", k; bad = 1; return 0 } return 1 }
function le(k, lim, what) { if (!need(k)) return; ok = (v[k] <= lim); printf "%s: %s %s = %.4g <= %g\n", ok ? "PASS" : "FAIL", what, k, v[k], lim; if (!ok) bad = 1 }
function ge(k, lim, what) { if (!need(k)) return; ok = (v[k] >= lim); printf "%s: %s %s = %.4g >= %g\n", ok ? "PASS" : "FAIL", what, k, v[k], lim; if (!ok) bad = 1 }
function absle(k, lim, what) { if (!need(k)) return; x = v[k] < 0 ? -v[k] : v[k]; ok = (x <= lim); printf "%s: %s |%s| = %.4g <= %g\n", ok ? "PASS" : "FAIL", what, k, x, lim; if (!ok) bad = 1 }
function rep(k, what) { if (k in have) printf "REPORT: %s %s = %.4g\n", what, k, v[k] }
function codes4(t) { return sprintf("%d %d %d %d", v["adc4_" t "_code0"], v["adc4_" t "_code1"], v["adc4_" t "_code2"], v["adc4_" t "_code3"]) }

END {
    bad = 0
    LSB = ("size_lsb_mv" in have) ? v["size_lsb_mv"] * 1e-3 : 6.7015e-3     # ADR 0025
    V_NEED = ("size_v_need_v" in have) ? v["size_v_need_v"] : 2.0999        # the window's top + the offset margin (R3/R4)
    KLO = ("size_k_lo" in have) ? v["size_k_lo"] : 11                         # the pre-roll in whole counts
    if ("size" in ran) {
        rep("size_lsb_mv", "grid (ADR 0025) LSB (mV)"); rep("size_window_codes", "codes over the 0.5-2.0 V window")
        rep("size_n_ramp_units", "R1 unit MIMs in the ramp capacitor")
        ge("size_slow_margin_cell_pct", 0, "R3 [D] the source at its slowest (2.0 % [A]) on the design slope stays at or above the grid's 0.982 (margin left for the cell, %):")
        rep("size_node_max_v", "R4 sensed-node maximum VREF + alpha (top - 0.5 V) at the end of the ramp, 3.0 V allocation, 3.3 V devices (V)")
        le("size_rst_drop_worst_lsb", 0.5, "R8a [A] I x Ron of the reset switch at 1.1x current, ss/85/3.0 (LSB):")
        le("size_rst_tau_worst_ns", 30, "R8b [D] reset time constant, ss/85/3.0 (ns):")
        rep("size_i_ramp_ua", "R1 the ramp current the I/C source must deliver (uA)")
        rep("size_src_i_at_mim_ss_ua", "... at the MIM ss corner (uA)"); rep("size_src_i_at_mim_ff_ua", "... at the MIM ff corner (uA)")
        rep("size_src_rout_for_0p05lsb_gohm", "R6 the source's output resistance for a 0.05 LSB bow (Gohm)")
        rep("size_src_rout_for_0p15lsb_gohm", "... for 0.15 LSB (Gohm)")
        rep("size_ktc_reset_lsb", "R12 reset kT/C on the ramp (LSB)"); rep("size_rst_junction_inl_est_lsb", "R6 the switch's junction C(V) (LSB)")
    }
    if ("ramp" in ran) {
        # the unit count is rounded DOWN (R3: never slow), so the design slope is size_slope_err_design_pct fast; the gate is the residual
        if (need("size_slope_err_design_pct")) {
            v["nom_slope_dev_pct"] = v["nom_slope_err_pct"] - v["size_slope_err_design_pct"]; have["nom_slope_dev_pct"] = 1
            v["level_slope_dev_pct"] = v["level_slope_err_pct"] - v["size_slope_err_design_pct"]; have["level_slope_dev_pct"] = 1
            rep("size_slope_err_design_pct", "R1 the design slope error from the unit rounding, fast (%)")
            rep("nom_slope_err_pct", "R1 slope error vs the ideal grid, real vrlo_ref (%)")
            absle("nom_slope_dev_pct", 0.5, "R1 [D] slope at the design current vs the design slope, real vrlo_ref (%):")
            absle("level_slope_dev_pct", 0.5, "R1 [D] slope at the design current vs the design slope, pre-roll level (%):")
        } else {
            absle("nom_slope_err_pct", 0.5, "R1 [D] slope at the design current, real vrlo_ref (%):")
            absle("level_slope_err_pct", 0.5, "R1 [D] slope at the design current on the pre-roll level (%):")
        }
        le("level_inl_end_lsb", 0.2, "R6 [A] ramp INL end-point over the conversion window, pre-roll level, ideal current:")
        le("nom_inl_end_lsb", 0.2, "R6 [A] ramp INL end-point, vrlo_ref level:")
        rep("level_inl_lsb", "R6 best-fit INL (LSB)"); rep("level_inl_ovr_lsb", "R6 INL over the overrun (LSB)")
        le("level_start_settle_k", KLO, "R2/R8 [D] start transient settled inside the pre-roll, ideal level (counts):")
        le("nom_start_settle_k", KLO, "R2/R8 [D] ... on the real vrlo_ref (counts):")
        absle("ifast_drop_tr_lsb", 0.5, "R8a [A] vramp - vrlo at the release at 1.1x current (LSB):")
        rep("nom_drop_tr_lsb", "R8a drop at TR with the real vrlo_ref (LSB)")
        absle("nom_kick_res_tr_mv", 0.05 * LSB * 1e3, "R8b [C] S1 charge left at TR with the real vrlo_ref (mV, 0.05 LSB):")
        rep("nom_kick_peak_mv", "S1 charge of 4 full-scale cells: peak on vramp (mV)")
        le("nom_rec_ns", 1000, "R11 [C] recovery after the end-of-ramp reset into vrlo_ref (ns):")
        rep("nom_rec_level_mv", "R11 level after recovery minus vrlo (mV)"); rep("nom_vrlo_pk_mv", "R11 vrlo peak at the dump (mV)")
        ge("level_vr_255_v", V_NEED, "R4 [D] vramp at count 255 >= the window's top + the +3 sigma offset, design current (V):")
        ge("islow_vr_255_v", V_NEED, "R3/R4 [D] ... at the source's slowest current, 0.98x (V):")
        rep("level_vr_top_v", "vramp at the end of the ramp, count 259 (V)"); rep("ifast_vr_top_v", "... at 1.1x current (V)")
        if (need("n16_slope_err_pct") && need("n64_slope_err_pct") && need("nom_slope_err_pct"))
            printf "REPORT: R7a load dependence: 16 cells %+.4f %%, 64 cells %+.4f %% against 4 (the cells add to C)\n", v["n16_slope_err_pct"] - v["nom_slope_err_pct"], v["n64_slope_err_pct"] - v["nom_slope_err_pct"]
        if (need("mimss_slope_err_pct") && need("mimff_slope_err_pct"))
            printf "REPORT: R5 slope at the MIM corners with a fixed current: ss %+.3f %%, ff %+.3f %% (what the I/C source's C_ref must track)\n", v["mimss_slope_err_pct"], v["mimff_slope_err_pct"]
        absle("kick_kick3_lsb", 0.1, "R9 [A] three injected decision kicks (0.24 fC each) leave on the ramp (LSB):")
        rep("nom_i_src_avg", "the ramp current over the ramp (A)")
    }
    if ("pvt" in ran) {
        if (need("pvt_cells") && need("pvt_pass_cells")) {
            ok = (v["pvt_pass_cells"] == v["pvt_cells"] && v["pvt_cells"] > 0)
            printf "%s: R15 [A] PVT: %d of %d cells (5 corners x 3 T x 3 AVDD, MIM typical, ideal design current) pass R1/R4/R6/R8a/start\n", ok ? "PASS" : "FAIL", v["pvt_pass_cells"], v["pvt_cells"]
            if (!ok) bad = 1
        }
        rep("pvt_worst_slope_err_pct", "PVT worst slope error (%)"); rep("pvt_worst_inl_end_lsb", "PVT worst INL end-point (LSB)")
        rep("pvt_worst_drop_tr_lsb", "PVT worst drop at TR (LSB)")
        if (need("pvt_mim_ss_slope_err_min_pct") && need("pvt_mim_ff_slope_err_max_pct"))
            printf "REPORT: R5 slope at the MIM corners over the 45 cells: ss %+.2f..%+.2f %%, ff %+.2f..%+.2f %% (the I/C source tracks C)\n", v["pvt_mim_ss_slope_err_min_pct"], v["pvt_mim_ss_slope_err_max_pct"], v["pvt_mim_ff_slope_err_min_pct"], v["pvt_mim_ff_slope_err_max_pct"]
    }
    if ("adc4" in ran) {
        if (need("adc4_missing")) { ok = (v["adc4_missing"] == 0); printf "%s: every four-cell macro run converted (%d missing of %d)\n", ok ? "PASS" : "FAIL", v["adc4_missing"], v["adc4_cases"]; if (!ok) bad = 1 }
        ge("adc4_coarse_real_monotonic", 1, "32-level transfer on the real ramp monotonic:")
        rep("adc4_coarse_real_err_spread_lsb", "err spread over the 32 coarse levels, raw (LSB; gain not removed)")
        rep("adc4_coarse_ideal_err_spread_lsb", "... on the ideal ramp (the cells' own spread, LSB)")
        absle("adc4_ramp_gain_err_pct", 1.8, "R1/R7 [D] the ramp's gain error in the conversion (real - ideal; the cells' load vs 19 fF each) inside R3's slow margin (%):")
        le("adc4_ramp_inl_lsb", 0.30, "R6 [U] the ramp's INL in the conversion incl. the comparator-ramp interaction (real - ideal ramp, after the line; ADR 0025, LSB):")
        rep("adc4_ramp_offset_lsb", "the ramp's own offset in the conversion (LSB)")
        absle("adc4_xtr_d1_lsb", 0.30, "R9 [U] the ramp's share of the trip-kick crosstalk, 3 aggressors 1 LSB away (ADR 0025, LSB):")
        absle("adc4_xtr_d4_lsb", 0.30, "R9 [U] ... 4 LSB away:"); absle("adc4_xtr_d16_lsb", 0.30, "R9 [U] ... 16 LSB away:"); absle("adc4_xtr_d24_lsb", 0.30, "R9 [U] ... 24 LSB away:"); absle("adc4_xtr_d32_lsb", 0.30, "R9 [U] ... 32 LSB away:"); absle("adc4_xtr_d64_lsb", 0.30, "R9 [U] ... 64 LSB away (beyond the ~20-count pull):"); absle("adc4_xtr_d0p25_lsb", 0.30, "R9 [U] ... 0.25 LSB away:")
        rep("adc4_xti_d1_lsb", "crosstalk without the ramp (ideal ramp: cells, references), 1 LSB (LSB)"); rep("adc4_xti_d4_lsb", "... 4 LSB (LSB)")
        absle("adc4_xc_v20_lsb", 0.1, "R8b/R9 [A] S1-connection crosstalk at code 20, 2 aggressors 0.5 -> 254.5 (LSB):")
        rep("adc4_xc_v5_lsb", "S1-connection crosstalk at code 5 (LSB)")
        if (need("adc4_show_r_codes")) printf "REPORT: codes for mid-codes 16/80/160/240 on vrlo_ref's 0.5 V level: real ramp %s\n", codes4("show_r")
        rep("adc4_show_r_err_d0_lsb", "cell 0 input-referred error (LSB)"); rep("adc4_show_r_err_d3_lsb", "cell 3 input-referred error (LSB)")
        rep("adc4_showp_r_ramp_slope_err_pct", "pre-roll level: ramp slope error in the macro (%)"); rep("adc4_showp_r_ramp_inl_ep_lsb", "pre-roll level: ramp INL end-point in the macro (LSB)")
        if (need("adc4_lowp_r_codes")) printf "REPORT: R2 pre-roll: codes for levels 0.5/1.5/2.5/4.5 LSB above the 0.42 V reset level: %s (no dead zone: every level resolved)\n", codes4("lowp_r")
        if (need("adc4_showp_r_codes")) printf "REPORT: R2/R3 pre-roll: codes for VIN = 0.503 / 1.0 / 1.5 / 1.995 V (the whole window, ADR 0025): %s\n", codes4("showp_r")
        if (need("adc4_showp_r_code3")) { ok = (v["adc4_showp_r_code3"] <= 254 && v["adc4_showp_r_code3"] + V_NEED / LSB - 2.0 / LSB <= 255); printf "%s: R3 [D] the window's top (1.995 V) converts (code %d <= 254) with room for the +3 sigma offset\n", ok ? "PASS" : "FAIL", v["adc4_showp_r_code3"]; if (!ok) bad = 1 }
    }
    if ("src" in ran) {
        # step 3 of ADR 0025: the ramp on the REAL I/C source, against the ideal ramp, pre-roll level, T0 60 us
        if (need("src_missing")) { ok = (v["src_missing"] == 0); printf "%s: every macro run on the real I/C source converted (%d missing of %d)\n", ok ? "PASS" : "FAIL", v["src_missing"], v["src_cases"]; if (!ok) bad = 1 }
        ge("adc4_src_monotonic", 1, "32-level transfer on the real I/C source monotonic:")
        le("adc4_src_gain_err_pct", 1.8, "R3 [D] the real I/C source's ramp in the conversion not slower than 1.8 % against the ideal one (real - ideal codes per volt; positive = slower, %):")
        rep("adc4_src_offset_lsb", "the real source's offset in the conversion (LSB)")
        le("adc4_src_inl_lsb", 0.30, "R6 [U] INL in the conversion on the real I/C source (incl. its 20 MHz ripple and the comparator-ramp interaction, LSB):")
        absle("adc4_xts_d24_lsb", 0.30, "R9 [U] trip-kick crosstalk on the real I/C source, 3 aggressors 24 LSB away (LSB):")
        rep("adc4_showp_s_ramp_slope_err_pct", "real source: ramp slope against the grid in the macro (%)"); rep("adc4_showp_s_ramp_inl_ep_lsb", "real source: ramp INL end-point in the macro (LSB)")
        if (need("adc4_showp_s_code3")) { ok = (v["adc4_showp_s_code3"] <= 254 && v["adc4_showp_s_code3"] + V_NEED / LSB - 2.0 / LSB <= 255); printf "%s: R3 [D] real source: VIN = 0.503 / 1.0 / 1.5 / 1.995 V read %s; the window's top converts with room for the offset margin\n", ok ? "PASS" : "FAIL", codes4("showp_s"); if (!ok) bad = 1 }
        if (need("adc4_lowp_s_code0")) printf "REPORT: R2 real source: levels 0.5/1.5/2.5/4.5 LSB above the reset read %s\n", codes4("lowp_s")
        if (need("adc4_fine_s_err_spread_lsb")) printf "REPORT: real source: quarter-LSB staircase at 127 reads %s (err spread %.4f LSB)\n", codes4("fine_s"), v["adc4_fine_s_err_spread_lsb"]
    }
    exit bad
}
