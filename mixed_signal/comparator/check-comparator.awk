# Acceptance of comparator from bench.py's data/values_<phase>.txt
# (name = value lines). One PASS:/FAIL: line per gate; exit 1 on any FAIL.
#
#   awk -v phases='verify lin bias' -f check-comparator.awk data/values_*.txt
#
# Gates (ADR 0015, on the sw variant; base and sw_noinv are reported):
#   delay     delay from the static trip <= 12.5 ns at 4.5 / 40.5 / 128.5 / 250.5 LSB, ideal bias
#   spread    level spread of that delay <= 5 ns (0.1 count)
#   armed     dout high at TR at every level
#   polarity  over the whole conversion (TR .. count 260): dout crosses VDD/2 exactly
#             once, falling, after the plate crossed the static trip; the plate rises
#   noise     input-referred at the pins, 1 kHz .. own band, < 1.2 mV
#   mc        >= 90 % of the Monte Carlo samples cross
#   lin       offset signal-independence: per mismatch sample, code offset moves
#             <= 0.1 LSB across the four levels, every sample decided, at every cell
#   harness   the base comparator on its record's grid reproduces
#             runs/comparator/20261106T033213Z: c4 delay 10.5894 ns, within 0.02 ns
# Reported only: fall (waived, ADR 0015), sigma(Vos), power, bias requirement.
function has(p) { return index(" " phases " ", " " p " ") > 0 }
function num(k) { return (k in v) ? v[k] + 0 : "nan" }
function ok(k) { return (k in v) && v[k] != "nan" && v[k] != "-nan" }
function verdict(name, good, msg) {
    printf "%s: %s: %s\n", (good ? "PASS" : "FAIL"), name, msg
    if (!good) bad = 1
}
$2 == "=" { v[$1] = $3 }
END {
    lv[1] = "c4"; lv[2] = "plat"; lv[3] = "mid"; lv[4] = "top"
    if (has("verify")) {
        dmax = -1; dmin = 1; good = 1
        for (i = 1; i <= 4; i++) {
            k = "sw_" lv[i] "_delay_dyn"
            if (!ok(k)) { good = 0; continue }
            d = num(k); if (d > dmax) dmax = d; if (d < dmin) dmin = d
        }
        verdict("delay", good && dmax <= 12.5e-9,
            sprintf("sw delay from the static trip %.2f..%.2f ns over 4.5-250.5 LSB at the ideal bias (<= 12.5 ns)", dmin * 1e9, dmax * 1e9))
        verdict("spread", good && dmax - dmin <= 5e-9, sprintf("sw level spread %.3f ns (<= 5 ns)", (dmax - dmin) * 1e9))
        good = 1
        for (i = 1; i <= 4; i++) if (!ok("sw_" lv[i] "_armed") || num("sw_" lv[i] "_armed") < 0.9 * 3.3) good = 0
        verdict("armed", good, "sw dout high at TR at every level")
        good = 1; msg = ""
        for (i = 1; i <= 4; i++) {
            p = "sw_" lv[i]
            n = num(p "_ncross"); dr = num(p "_dir"); dd = num(p "_delay_dyn"); pr = num(p "_plate_rise")
            g = ok(p "_ncross") && n == 1 && dr == -1 && ok(p "_delay_dyn") && dd > 0 && pr > 0
            if (!g) good = 0
            msg = msg sprintf("%s%s %d crossing(s) dir %d, plate +%.2f V", (i > 1 ? "; " : ""), lv[i], n, dr, pr)
        }
        verdict("polarity", good, "sw dout falls exactly once, after the plate crosses the trip, over TR..count 260: " msg)
        verdict("noise", ok("sw_nz_own_vin") && num("sw_nz_own_vin") < 1.2e-3,
            sprintf("sw %.3f mV rms at the pins, 1 kHz .. own band (< 1.2 mV); base %.3f mV", num("sw_nz_own_vin") * 1e3, num("base_nz_own_vin") * 1e3))
        verdict("mc", ok("sw_mc_samples") && num("sw_mc_samples") >= 0.9 * num("sw_mc_n"),
            sprintf("sw %d of %d Monte Carlo samples crossed", num("sw_mc_samples"), num("sw_mc_n")))
        verdict("harness", ok("base_oldc4_delay_dyn") && (num("base_oldc4_delay_dyn") - 10.5894e-9) ^ 2 <= (0.02e-9) ^ 2,
            sprintf("base on its record's grid: c4 delay %.4f ns vs 10.5894 ns (runs/comparator/20261106T033213Z)", num("base_oldc4_delay_dyn") * 1e9))
        printf "REPORT: side by side at typical, ideal bias (sw / base / sw_noinv): delay from the static trip %.2f / %.2f / %.2f ns; latency from the ideal ramp crossing %.2f / %.2f / %.2f ns; dout edge 10-90 %% %.2f / %.2f / %.2f ns (fall waived, ADR 0015); power %.1f / %.1f / %.1f uW; alpha at the trip %.3f / %.3f / %.3f; at the macro bias 3.25 uA %.2f / %.2f / %.2f ns\n", \
            num("sw_delay_max") * 1e9, num("base_delay_max") * 1e9, num("sw_noinv_delay_max") * 1e9, \
            num("sw_latency_ns_mean"), num("base_latency_ns_mean"), num("sw_noinv_latency_ns_mean"), \
            num("sw_edge_max") * 1e9, num("base_edge_max") * 1e9, num("sw_noinv_edge_max") * 1e9, \
            num("sw_p_avg_max") * 1e6, num("base_p_avg_max") * 1e6, num("sw_noinv_p_avg_max") * 1e6, \
            num("sw_alpha_trip_mean"), num("base_alpha_trip_mean"), num("sw_noinv_alpha_trip_mean"), \
            num("sw_mac_delay_dyn") * 1e9, num("base_mac_delay_dyn") * 1e9, num("sw_noinv_mac_delay_dyn") * 1e9
        printf "REPORT: sigma(Vos) at the pins sw %.2f mV (%.2f LSB at the ADC input) / base %.2f mV (%.2f LSB); not gated (ADR 0015)\n", \
            num("sw_mc_sigma_vos_v") * 1e3, num("sw_mc_sigma_in_lsb"), num("base_mc_sigma_vos_v") * 1e3, num("base_mc_sigma_in_lsb")
    }
    if (has("lin")) {
        nc = 0
        for (k in v) if (k ~ /^lin_sw_.*_worst_level_spread_lsb$/) {
            t = k; sub(/_worst_level_spread_lsb$/, "", t)
            nc++
            g = ok(k) && num(k) <= 0.1 && num(t "_unmeasured") == 0 && num(t "_samples") > 0
            verdict("offset_lin " substr(t, 8), g,
                sprintf("sw code offset moves at most %.4f LSB across 4.5..250.5 LSB over %d samples (<= 0.1 LSB), %d undecided; nominal %.4f LSB; offset mean %+.2f sigma %.2f LSB",
                    num(k), num(t "_samples"), num(t "_unmeasured"), num(t "_nominal_level_spread_lsb"), num(t "_code_offset_mean_lsb"), num(t "_code_offset_sigma_lsb")))
            b = "lin_base_" substr(t, 8)
            if ((b "_worst_level_spread_lsb") in v)
                printf "REPORT: offset_lin base %s: worst %.4f LSB, offset mean %+.2f sigma %.2f LSB, %d undecided\n", substr(t, 8), \
                    num(b "_worst_level_spread_lsb"), num(b "_code_offset_mean_lsb"), num(b "_code_offset_sigma_lsb"), num(b "_unmeasured")
        }
        if (nc == 0) verdict("offset_lin", 0, "no lin values for sw")
    }
    if (has("bias")) {
        nb = 0
        for (k in v) if (k ~ /^bias_.*_req_scale$/) nb++
        verdict("bias", nb > 0, sprintf("bias requirement derived for %d variant x cell x geometry rows (values reported, not gated)", nb))
        # the table ../bias_gen checks: sw, every one of the 45 PVT cells, both geometries, each resolved
        verdict("bias_table", num("bias_sw_deck_cells") == 45 && num("bias_sw_geom_cells") == 45 && \
                num("bias_sw_deck_unresolved") == 0 && num("bias_sw_geom_unresolved") == 0,
                sprintf("data/bias_req.csv: sw requirement at %d / %d of 45 PVT cells (deck / drawn geometry), unresolved %d / %d; " \
                        "worst %.4g x / %.4g x the ideal finger current, cells above the macro's 1.683x %d / %d", \
                        num("bias_sw_deck_cells"), num("bias_sw_geom_cells"), num("bias_sw_deck_unresolved"), \
                        num("bias_sw_geom_unresolved"), num("bias_sw_deck_req_max"), num("bias_sw_geom_req_max"), \
                        num("bias_sw_deck_over_macro"), num("bias_sw_geom_over_macro")))
    }
    exit bad
}
