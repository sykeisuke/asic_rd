# Acceptance for the comparator transient-noise characterization
# (trannoise.py reduce -> work/tn/measurements.txt).
#
# Gated, in the order the argument depends on them:
#   1. the engine: at the AC-noise bias point the Welch PSD of the transient
#      record, referred through |A(f)|, integrates to the noise analysis
#      within 10 % over 100 kHz..20 MHz (thermal) and within 20 % over
#      1..300 kHz (flicker; VACASK approximates 1/f by a sum of Lorentzians)
#   2. the measurement: every conversion of every ramp record crossed, and
#      the numerical floor (same grid, noise off) is under 10 % of the
#      noisy sigma at 1.25 V
#   3. the generator bandwidth: noisefmax 1 GHz gives the 200 MHz sigma
#      within three combined standard errors of the two estimates
#   4. the design: the worst transient-noise sigma at the 8-bit slope,
#      referred to the ADC input (worst_sigma_lsb = sigma / alpha / LSB), is
#      within the comparator's allocation in ../Analog_top_bkp/unit_cell_noise/NOISE_BUDGET.md
#      (row 5, decision noise incl. transient: 0.080 LSB; -v alloc= overrides),
#      and, as before, within the contract's 1/4 LSB
# The AC predictions each sigma is compared with are REPORTed, not judged:
# they are what this characterization replaces.

BEGIN { if (alloc == "") alloc = 0.080 }

$2 == "=" { value[$1] = $3 + 0; seen[$1] = 1 }

function absval(x) { return x < 0 ? -x : x }
function need(k) {
    if (!(k in seen)) { print "FAIL: trannoise: no " k " in the measurements"; failed = 1; return 0 }
    return 1
}

END {
    failed = 0
    if (need("psd_hi_ratio") && absval(value["psd_hi_ratio"] - 1) > 0.10) {
        printf "FAIL: transient-noise PSD, 100 kHz-20 MHz, is %.3fx the noise analysis (tolerance 10%%)\n", value["psd_hi_ratio"]
        failed = 1
    }
    if (need("psd_lo_ratio") && absval(value["psd_lo_ratio"] - 1) > 0.20) {
        printf "FAIL: transient-noise PSD, 1-300 kHz, is %.3fx the noise analysis (tolerance 20%%)\n", value["psd_lo_ratio"]
        failed = 1
    }
    # -v tags= and -v levels= name the case set (one decision common
    # mode, "r_1p65 r_1p65_q r_1p65_f1g"); the defaults are the old top-plate cases.
    # -v alpha= is the top-plate attenuation the budget was referred by.
    if (tags == "") tags = "r_0p5 r_1p25 r_2p0 r_1p25_q r_1p25_s0p25 r_1p25_s4 r_1p25_f1g"
    if (levels == "") levels = "r_0p5 r_1p25 r_2p0"
    n = split(tags, tags_a, " ")
    for (i = 1; i <= n; i++) {
        t = tags_a[i]
        if (!need(t "_found")) continue
        if (value[t "_found"] != value[t "_nconv"]) {
            printf "FAIL: %s: dout crossed in %d of %d conversions\n", t, value[t "_found"], value[t "_nconv"]
            failed = 1
        }
        if (value[t "_extra_crossings"] > 0)
            printf "REPORT: %s: %d extra dout crossings (chatter)\n", t, value[t "_extra_crossings"]
    }
    if (need("floor_over_noise") && value["floor_over_noise"] >= 0.10) {
        printf "FAIL: numerical jitter floor is %.3f of the noisy sigma (limit 0.10)\n", value["floor_over_noise"]
        failed = 1
    }
    if (need("fmax_ratio") && absval(value["fmax_ratio"] - 1) > value["fmax_ratio_tol"]) {
        printf "FAIL: sigma at noisefmax 1 GHz is %.3fx the 200 MHz value (tolerance %.3f)\n", value["fmax_ratio"], value["fmax_ratio_tol"]
        failed = 1
    }
    if (need("worst_sigma_uv") && value["worst_sigma_uv"] > value["noise_budget_uv"]) {
        printf "FAIL: transient-noise sigma %.1f uV exceeds the 1/4 LSB budget %.1f uV at the pins\n", value["worst_sigma_uv"], value["noise_budget_uv"]
        failed = 1
    }
    if (need("worst_sigma_lsb")) {
        printf "meas_tn_worst_sigma_in_lsb = %.5f\n", value["worst_sigma_lsb"]
        if (value["worst_sigma_lsb"] > alloc + 0) {
            printf "FAIL: transient-noise crossing jitter %.4f LSB at the ADC input exceeds the gate %.3f LSB (-v alloc; default the 0.080 LSB allocation of NOISE_BUDGET.md row 5)\n", value["worst_sigma_lsb"], alloc + 0
            failed = 1
        } else
            printf "PASS: transient-noise crossing jitter %.4f LSB at the ADC input is within the gate %.3f LSB (-v alloc; default the 0.080 LSB allocation of NOISE_BUDGET.md row 5)\n", value["worst_sigma_lsb"], alloc + 0
    }
    bps = (alpha != "" && alpha + 0 != 1)
    m = split(levels, lv, " ")
    for (i = 1; i <= m; i++) {
        t = lv[i]
        if (t "_sigma_uv" in seen) {
            if (bps)
                printf "REPORT: %s: tran sigma %.1f uV at the pins = %.4f LSB at the ADC input (alpha %.3f), fast %.1f uV; x%.2f AC window, x%.2f AC own band, x%.2f AC noise/slew\n", \
                    t, value[t "_sigma_uv"], value[t "_sigma_in_lsb"], alpha + 0, value[t "_sigma_fast_uv"], \
                    value[t "_over_ac_win"], value[t "_over_ac_own"], value[t "_over_ac_slew"]
            else
                printf "REPORT: %s: tran sigma %.1f uV (%.4f LSB), fast %.1f uV; x%.2f AC window, x%.2f AC own band, x%.2f AC noise/slew\n", \
                    t, value[t "_sigma_uv"], value[t "_sigma_lsb"], value[t "_sigma_fast_uv"], \
                    value[t "_over_ac_win"], value[t "_over_ac_own"], value[t "_over_ac_slew"]
        }
    }
    if (!failed) {
        if (bps)
            printf "PASS: comparator transient noise: engine matches AC (x%.3f thermal, x%.3f flicker), worst sigma %.1f uV at the pins = %.4f LSB at the ADC input (alpha %.3f; budget 1/4 LSB = %.1f uV at the pins)\n", \
                value["psd_hi_ratio"], value["psd_lo_ratio"], value["worst_sigma_uv"], value["worst_sigma_lsb"], alpha + 0, value["noise_budget_uv"]
        else
            printf "PASS: comparator transient noise: engine matches AC (x%.3f thermal, x%.3f flicker), worst sigma %.1f uV = %.4f LSB (budget 1/4 LSB)\n", \
                value["psd_hi_ratio"], value["psd_lo_ratio"], value["worst_sigma_uv"], value["worst_sigma_lsb"]
    }
    exit failed
}
