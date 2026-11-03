# check-ic.awk -- gates of the I/C current source (SPEC.md R1-R13) on the
# `name = value` lines of every phase (work/phases_out.txt). One PASS:/FAIL:
# line per gate, REPORT: lines for what is recorded without a verdict.
# Labels: [C] contract, [P] PDK, [M] measured, [A] assumed, [D] derived.
function absv(x) { return x < 0 ? -x : x }
function have(k) { return (k in v) }
function le(k, lim, text) {
    if (!have(k)) { printf "FAIL: %s %s missing\n", text, k; return }
    printf "%s: %s %s = %.4g <= %.4g\n", (v[k] <= lim ? "PASS" : "FAIL"), text, k, v[k], lim
}
function ale(k, lim, text) {
    if (!have(k)) { printf "FAIL: %s %s missing\n", text, k; return }
    printf "%s: %s |%s| = %.4g <= %.4g\n", (absv(v[k]) <= lim ? "PASS" : "FAIL"), text, k, absv(v[k]), lim
}
function ge(k, lim, text) {
    if (!have(k)) { printf "FAIL: %s %s missing\n", text, k; return }
    printf "%s: %s %s = %.4g >= %.4g\n", (v[k] >= lim ? "PASS" : "FAIL"), text, k, v[k], lim
}
function rep(k, text) { if (have(k)) printf "REPORT: %s %s = %.4g\n", text, k, v[k] }
/^[A-Za-z_@][A-Za-z_0-9@.\[\]()]* = / { v[$1] = $3; next }
END {
    print "REPORT: gates of SPEC.md; tolerances: typical 1.5 % [A], PVT 1.0 % about the mean [A], mismatch 3 sigma 2.0 % [A]; the slow sum must stay inside the ramp's 2.0 % allocation (ramp_simple R3, ADR 0025)"
    if (have("nom_i_out_ua")) {
        ale("nom_i_err_pct", 1.5, "R1 [A] current vs C_UNIT x V_REF x F_CLK at typical (%):")
        rep("nom_i_out_ua", "R1 the current delivered (uA)")
        rep("nom_i_ideal_ua", "R1 C_UNIT x V_REF x F_CLK (uA)")
        ale("nom_va_err_mv", 2.0, "R1 [A] the regulated node vs V_REF (mV):")
        le("op_mim_track_err_pct", 1.0, "R2 [A] tracking: current error change at the MIM corners (%):")
        ge("op_rout_gohm", 2.0, "R3 [C] output resistance at the ramp node over its span (0.420..2.156 V, ADR 0025; Gohm):")
        ge("op_hr_top_min_mv", 0.0, "R8 [A] headroom of every loop and pass device with the ramp at its top, typical + ss/85/3.0, ff/85/3.0, ff/0/3.6 (mV):")
        rep("op_bow_est_lsb", "R3 ramp bow from r_out (LSB, ramp_simple R6)")
        le("op_ripple_ramp_lsb", 0.05, "R4 [C] 20 MHz ripple at the ramp node (LSB):")
        rep("nom_i_out_pp_na", "R4 output current ripple (nA p-p)")
        rep("nom_va_pp_mv", "node a ripple (mV p-p)")
        le("nom_t_start_us", 60.0, "R7 [U] settled within 1 % from a cold supply, typical (us):")
        ge("nom_hr_min_mv", 0.0, "R8 [A] headroom V_DS - Vdsat of every loop and pass device, typical (mV):")
        le("op_duty_sens_pct_per_pct", 0.2, "R9 [A] current per clock duty, 45..55 % (% per %):")
        le("op_vdd_dev_pct", 0.5, "R10 [A] ratiometric: current error change at AVDD 3.0 / 3.6 V (%):")
        le("op_p_total_uw", 80.0, "R12 [A] power AVDD + DVDD incl. the bias diode and the phase generator (uW):")
        rep("nom_p_avdd_uw", "R12 AVDD (uW)")
        rep("nom_p_dvdd_uw", "R12 DVDD, the phase generator at 20 MHz (uW)")
    }
    for (k in v) if (k ~ /^loop[a-z]*_pm_deg$/) ge(k, 60.0, "R6 [A] loop phase margin (deg):")
    for (k in v) if (k ~ /^loop[a-z]*_f_unity_khz$/) rep(k, "R6 loop unity frequency (kHz)")
    for (k in v) if (k ~ /^loop[a-z]*_loop_dc_db$/) rep(k, "R6 loop gain at DC (dB)")
    if (have("noise_noise_code255_lsb")) {
        le("noise_noise_code255_lsb", 0.11, "R5 [C] current noise through the ramp's 13.8 us kernel at code 255 (LSB):")
        rep("noise_noise_code255_below1khz_lsb", "R5 share below 1 kHz (LSB)")
        rep("noise_noise_i_1khz_pa_rthz", "R5 output current noise at 1 kHz (pA/rtHz)")
        rep("noisehi_noise_code255_lsb", "R5 the same at the ramp top (LSB)")
    }
    if (have("pvt_cells")) {
        printf "%s: R2/R7/R8 [A] PVT: %d of %d cells (5 corners x 3 T x 3 AVDD) pass current within 1.0 %% of the mean, headroom >= 0, start <= 60 us\n", (v["pvt_pass"] == v["pvt_cells"] && v["pvt_cells"] == 45 ? "PASS" : "FAIL"), v["pvt_pass"], v["pvt_cells"]
        rep("pvt_i_err_spread_pct", "R2 PVT current error spread (%)")
        rep("pvt_i_err_mean_pct", "R2 PVT current error mean (%)")
        rep("pvt_hr_min_mv", "R8 PVT headroom min (mV)")
        rep("pvt_t_start_max_us", "R7 PVT start max (us)")
    }
    if (have("mc_draws")) {
        le("mc_t_start_max_us", 60.0, "R7 [U] every mismatch draw settled within the limit, before its 65-70 us window (us):")
        le("mc_i_3sigma_pct", 2.0, "R13 [A] mismatch: 3 sigma of the current (%):")
        rep("mc_i_sigma_pct", "R13 sigma (%)")
        rep("mc_loop_err_sigma", "R13 sigma of the loop's part, the OTA offset (%)")
        rep("mc_mirror_err_sigma", "R13 sigma of the pass mirror's part (%)")
        rep("mc_sc_err_sigma", "R13 sigma of the switched capacitor's part (%)")
        if (have("pvt_i_err_mean_pct") && have("pvt_i_err_min_pct") && have("op_duty_sens_pct_per_pct")) {
            v["slow_total_pct"] = v["mc_i_3sigma_pct"] + (v["pvt_i_err_mean_pct"] - v["pvt_i_err_min_pct"]) + 2.0 * v["op_duty_sens_pct_per_pct"]
            le("slow_total_pct", 2.0, "R3 (ramp) [A] slowest current: mismatch 3 sigma + PVT below the mean + a 2 % clock duty error, inside the ramp's 2.0 % allocation (ADR 0025, %):")
        }
        rep("size_mirror_sigma_pct", "R13 the pass mirror's Pelgrom estimate (%)")
    }
}
