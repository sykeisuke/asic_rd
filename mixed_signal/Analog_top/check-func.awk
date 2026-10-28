# check-func.awk -- acceptance of the analog_top functional record.
#
#   awk -f check-func.awk data/func_measures.txt data/func_reduce.txt
#
# Both files are `name = value` (ngspice measures; func_reduce.py). A missing
# or non-numeric value fails the gate that needs it. One PASS:/FAIL: line per
# gate, then REPORT: lines (recorded, not judged). Exit 1 on any FAIL.
#
# Gates and where each threshold comes from:
#   bias        pbias0..3 (each comparator's own diode) within TOL_BIAS = 5 mV
#               of its final value over [T0, TS0] and between TS0 and TE: the
#               generator is at its operating point before the first sample
#               and stays there (../Analog_top_bkp/unit_cell_bps/check-cell.awk TOL_BIAS)
#   references  VREF, VBL and the shared tap within TOL_REF of their final
#               value over [T0, TS0], TOL_REF = 0.25 LSB x alpha_min: a
#               reference still moving by TOL_REF moves one cell's code
#               against another's by at most 0.25 LSB, the spread allowed by
#               check-cell.awk's linearity gate (alpha_min is the smallest
#               bot/top transfer of the four cells, so the bound is the
#               conservative one); and the VDD/2 error <= 50 mV
#               (../midrail_ref/README.md s.1, common to VREF and VBL)
#   vrlo        (v4: vrlo is made on chip by vrlo_ref, ADR 0018) settled within
#               1 mV of its TS0 value before T0 (as the bias / references), and
#               |vrlo - 5/33 AVDD| at TR <= 2 LSB (vrlo_ref README R9: half the
#               overrun counts left after the in-cell offset)
#   sample      top = vin and bot = vref at TS_k within 0.1 LSB through the
#               real switches (check-cell.awk TOL_SAMPLE)
#   plate       the input-referred error at the crossing, bps_err_k =
#               (vramp at bot = vbl) - vin_k, is ramp-independent and holds
#               everything between the sample and the comparator threshold
#               (pedestal, plate charge, VREF at TS_k vs VBL at the decision);
#               its spread over the four cells <= 0.25 LSB (check-cell.awk
#               linearity, bps_err_lsb spread). Its mean is a pedestal the
#               calibration removes (reported)
#   armed       at TR, before the ramp moves: bot_k < vbl, dout_k and q_k
#               high; between S1_k closing (+ one count for q) and TR, dout_k
#               never below VDD/2 and q_k never falls: no cell decides early
#   decision    q_k falls exactly once in (TR, TE + TOVR], never again and
#               never rises up to TSTOP, and stays below VDD/2 afterwards
#   latch       q_k falls at the first cnt_clk falling edge after dout_k's
#               fall, clock-to-q <= 20 ns (../latch_bkp/cmp_tspc SPEC S4, kept for latch); a dout
#               within 2 ns of an edge may be caught one edge later
#   range       0 <= code_k <= 255 + 20 (the overrun), and the ramp reaches
#               VR_HI before TE + TOVR (the whole input range converts)
#   order       code0 < code1 < code2 < code3 (inputs 16.5/80.5/160.5/240.5
#               LSB in cell order)
#   transfer    least-squares line of the continuous trip count
#               (t_dout - TR)/TCOUNT against POS_k over the four cells:
#               every residual <= 0.5 LSB (half a code: past it a code
#               boundary moves by a code, i.e. a missing or doubled code)
#   rails       0 <= bot_k <= VDD from the S1 connection to TSTOP
# Reported, not judged: offset and gain error (the calibration removes
# both), comparator delay, dout fall, pedestals, alpha, ramp slope / INL /
# start / kicks, bias currents, settling times, VREF/VBL in the sampling
# window, power per block.

function isnum(s) { return s ~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/ }
function has(k) { return (k in val) && isnum(val[k]) }
function v(k) { return val[k] + 0 }
function aabs(x) { return x < 0 ? -x : x }
function need(g, k) { if (!has(k)) { note(g, k " missing"); return 0 } return 1 }
function note(g, s) { nbad[g]++; if (nbad[g] <= 4) bad[g] = bad[g] ((bad[g] == "") ? "" : "; ") s }
function verdict(g) { if (nbad[g]) fail = 1; return nbad[g] ? "FAIL" : "PASS" }
function tail(g) { return nbad[g] ? ": " bad[g] : "" }

$2 == "=" { val[$1] = $3 }

END {
    split("p_vdd p_lsb p_tcount p_tr p_te p_tovr p_tstop p_vr_hi p_tpwr alpha_min", base, " ")
    for (i in base) if (!has(base[i])) { printf "FAIL: input: %s missing from the measures\n", base[i]; exit 1 }
    VDD = v("p_vdd"); VMID = VDD / 2; LSB = v("p_lsb"); T = v("p_tcount")
    TR = v("p_tr"); TE = v("p_te"); TOVR = v("p_tovr"); NOVR = int(TOVR / T + 0.5)
    TOL_BIAS = 5e-3
    TOL_REF = 0.25 * LSB * v("alpha_min")
    TOL_SAMPLE = 0.1 * LSB
    VMID_ERR = 50e-3
    SPREAD_MAX = 0.25
    RES_MAX = 0.5
    TCQ_MAX = 20

    # ------------------------------------------------------------ bias
    w = 0
    for (k = 0; k < 4; k++) {
        n = "pbias" k
        if (!need("bias", n "_at_ts0") || !need("bias", n "_at_te") || !need("bias", "dev_" n "_mv")) continue
        d = aabs(v(n "_at_te") - v(n "_at_ts0")); if (d > w) w = d
        dd = v("dev_" n "_mv") * 1e-3; if (dd > w) w = dd
        if (d > TOL_BIAS || dd > TOL_BIAS) note("bias", sprintf("%s moves %.2f mV (TS0..TE), %.2f mV from final over [T0, TS0]", n, d * 1e3, dd * 1e3))
    }
    printf "%s: bias: pbias0..3 at their final value over [T0, TS0] and steady to TE, worst %.3f mV <= %.0f mV (pbias0 %.4f V)%s\n", \
        verdict("bias"), w * 1e3, TOL_BIAS * 1e3, v("pbias0_at_ts0"), tail("bias")

    # ------------------------------------------------------ references
    w = 0
    split("vref vbl vmid", rn, " ")
    for (i = 1; i <= 3; i++) {
        if (!need("references", "dev_" rn[i] "_mv")) continue
        d = v("dev_" rn[i] "_mv") * 1e-3; if (d > w) { w = d; wn = rn[i] }
        if (d > TOL_REF) note("references", sprintf("%s %.3f mV from its final value in [T0, TS0]", rn[i], d * 1e3))
    }
    for (i = 1; i <= 2; i++) {
        k = rn[i] "_err_ts0"
        if (need("references", k) && aabs(v(k)) > VMID_ERR) note("references", sprintf("%s %.1f mV from VDD/2", rn[i], v(k) * 1e3))
    }
    printf "%s: references: VREF, VBL and the tap at their final value over [T0, TS0] within %.3f mV (0.25 LSB x alpha_min %.3f), worst %.4f mV (%s); VDD/2 error %.2f / %.2f mV <= %.0f mV%s\n", \
        verdict("references"), TOL_REF * 1e3, v("alpha_min"), w * 1e3, wn, v("vref_err_ts0") * 1e3, v("vbl_err_ts0") * 1e3, VMID_ERR * 1e3, tail("references")

    # ------------------------------------------------------------ vrlo
    VRLO_ERR = 2 * LSB
    if (need("vrlo", "settle_vrlo_ns") && v("settle_vrlo_ns") * 1e-9 > v("p_t0"))
        note("vrlo", sprintf("vrlo settles to 1 mV at %.0f ns, after T0", v("settle_vrlo_ns")))
    if (need("vrlo", "vrlo_err_tr") && aabs(v("vrlo_err_tr")) > VRLO_ERR)
        note("vrlo", sprintf("vrlo %.3f mV from 5/33 AVDD at TR", v("vrlo_err_tr") * 1e3))
    printf "%s: vrlo: vrlo_ref settled to 1 mV at %.0f ns <= T0 %.0f ns; at TR %.5f V, %+.3f mV (%+.3f LSB) from 5/33 AVDD, |err| <= %.2f mV (2 LSB)%s\n", \
        verdict("vrlo"), v("settle_vrlo_ns"), v("p_t0") * 1e9, v("vrlo_at_tr"), v("vrlo_err_tr") * 1e3, v("vrlo_err_tr") / LSB, VRLO_ERR * 1e3, tail("vrlo")

    # ---------------------------------------------------------- sample
    wb = 0; wt = 0
    for (k = 0; k < 4; k++) {
        if (!need("sample", "vtop_ts" k) || !need("sample", "vin_ts" k) || !need("sample", "vbot_ts" k) || !need("sample", "vref_ts_" k)) continue
        db = aabs(v("vtop_ts" k) - v("vin_ts" k)); dt = aabs(v("vbot_ts" k) - v("vref_ts_" k))
        if (db > wb) wb = db; if (dt > wt) wt = dt
        if (db > TOL_SAMPLE || dt > TOL_SAMPLE) note("sample", sprintf("cell %d: top %+.3f mV from vin, bot %+.3f mV from vref", k, (v("vtop_ts" k) - v("vin_ts" k)) * 1e3, (v("vbot_ts" k) - v("vref_ts_" k)) * 1e3))
    }
    printf "%s: sample: at TS_k top = vin and bot = vref within %.3f mV (0.1 LSB) in every cell, worst %.4f / %.4f mV%s\n", \
        verdict("sample"), TOL_SAMPLE * 1e3, wb * 1e3, wt * 1e3, tail("sample")

    # ----------------------------------------------------------- plate
    bmin = 1e9; bmax = -1e9
    for (k = 0; k < 4; k++) {
        if (!need("plate", "bps_err" k)) continue
        b = v("bps_err" k); if (b < bmin) bmin = b; if (b > bmax) bmax = b
    }
    if (!nbad["plate"] && bmax - bmin > SPREAD_MAX) note("plate", sprintf("bps_err spread %.4f LSB", bmax - bmin))
    printf "%s: plate: input-referred error at the crossing (vramp - vin) %.4f .. %.4f LSB over the four cells, spread %.4f <= %.2f LSB%s\n", \
        verdict("plate"), bmin, bmax, bmax - bmin, SPREAD_MAX, tail("plate")

    # ----------------------------------------------------------- armed
    for (k = 0; k < 4; k++) {
        if (!need("armed", "vbot_tr" k) || !need("armed", "vbl_at_tr") || !need("armed", "dout_tr" k) || !need("armed", "q_tr" k) \
            || !need("armed", "q_falls_pre" k) || !need("armed", "dout_min_pre" k)) continue
        if (v("vbot_tr" k) >= v("vbl_at_tr")) note("armed", sprintf("cell %d: bot %.4f V >= vbl %.4f V at TR", k, v("vbot_tr" k), v("vbl_at_tr")))
        if (v("dout_tr" k) <= VMID) note("armed", sprintf("cell %d: dout %.3f V at TR", k, v("dout_tr" k)))
        if (v("q_tr" k) <= VMID) note("armed", sprintf("cell %d: q %.3f V at TR", k, v("q_tr" k)))
        if (v("q_falls_pre" k) != 0) note("armed", sprintf("cell %d: q fell %d times before TR", k, v("q_falls_pre" k)))
        if (v("dout_min_pre" k) <= VMID) note("armed", sprintf("cell %d: dout down to %.3f V before TR", k, v("dout_min_pre" k)))
        mg = v("vbl_at_tr") - v("vbot_tr" k); if (k == 0 || mg < mgmin) mgmin = mg
    }
    printf "%s: armed: at TR every bot below vbl (smallest margin %.2f mV), dout and q high; no dout below VDD/2 and no q fall between S1 closing and TR%s\n", \
        verdict("armed"), mgmin * 1e3, tail("armed")

    # -------------------------------------------------------- decision
    for (k = 0; k < 4; k++) {
        if (!need("decision", "q_falls" k) || !need("decision", "q_falls_all" k) || !need("decision", "q_rises_all" k) || !need("decision", "q_max_after" k)) continue
        if (v("q_falls" k) != 1) note("decision", sprintf("cell %d: %d q falls in (TR, TE+TOVR]", k, v("q_falls" k)))
        if (v("q_falls_all" k) != 1 || v("q_rises_all" k) != 0) note("decision", sprintf("cell %d: %d falls / %d rises up to TSTOP", k, v("q_falls_all" k), v("q_rises_all" k)))
        if (v("q_max_after" k) >= VMID) note("decision", sprintf("cell %d: q back up to %.3f V after its fall", k, v("q_max_after" k)))
    }
    printf "%s: decision: each q falls exactly once in (TR, TE+TOVR] and stays low to TSTOP (t_q %.4f / %.4f / %.4f / %.4f us)%s\n", \
        verdict("decision"), v("t_q0") * 1e6, v("t_q1") * 1e6, v("t_q2") * 1e6, v("t_q3") * 1e6, tail("decision")

    # ----------------------------------------------------------- latch
    s = ""
    for (k = 0; k < 4; k++) {
        if (!need("latch", "latch_ok" k)) continue
        if (v("latch_ok" k) != 1) note("latch", sprintf("cell %d: q %.2f ns after the edge %d, dout %.2f ns before it", k, v("latch_tcq" k "_ns"), v("latch_edge" k), v("latch_margin" k "_ns")))
        s = s sprintf("%s%.2f/%.2f", (k ? ", " : ""), v("latch_margin" k "_ns"), v("latch_tcq" k "_ns"))
    }
    printf "%s: latch: q falls at the first cnt_clk falling edge after dout, clock-to-q <= %d ns (dout margin before the edge / clock-to-q, ns: %s)%s\n", \
        verdict("latch"), TCQ_MAX, s, tail("latch")

    # ----------------------------------------------------------- range
    for (k = 0; k < 4; k++) {
        if (!need("range", "code" k)) continue
        if (v("code" k) < 0 || v("code" k) > 255 + NOVR) note("range", sprintf("cell %d: code %d", k, v("code" k)))
    }
    if (need("range", "vramp_at_tovr") && v("vramp_at_tovr") < v("p_vr_hi")) note("range", sprintf("vramp %.4f V at TE+TOVR < VR_HI", v("vramp_at_tovr")))
    printf "%s: range: codes %d / %d / %d / %d inside 0..%d; vramp %.4f V at TE+TOVR >= VR_HI %.1f V (reached after %.2f counts)%s\n", \
        verdict("range"), v("code0"), v("code1"), v("code2"), v("code3"), 255 + NOVR, v("vramp_at_tovr"), v("p_vr_hi"), v("n_ramp_hi"), tail("range")

    # ----------------------------------------------------------- order
    for (k = 1; k < 4; k++) if (has("code" k) && has("code" (k - 1)) && v("code" k) <= v("code" (k - 1))) note("order", sprintf("code%d %d <= code%d %d", k, v("code" k), k - 1, v("code" (k - 1))))
    printf "%s: order: codes strictly increasing in cell order (inputs 16.5 / 80.5 / 160.5 / 240.5 LSB)%s\n", verdict("order"), tail("order")

    # -------------------------------------------------------- transfer
    if (need("transfer", "xfer_d_res_max_lsb") && v("xfer_d_res_max_lsb") > RES_MAX) note("transfer", sprintf("residual %.4f LSB", v("xfer_d_res_max_lsb")))
    printf "%s: transfer: gain + offset fit of the trip count over the four cells, max residual %.4f <= %.1f LSB (residuals %+.3f / %+.3f / %+.3f / %+.3f)%s\n", \
        verdict("transfer"), v("xfer_d_res_max_lsb"), RES_MAX, v("xfer_d_res0_lsb"), v("xfer_d_res1_lsb"), v("xfer_d_res2_lsb"), v("xfer_d_res3_lsb"), tail("transfer")

    # ----------------------------------------------------------- rails
    tmin = 1e9; tmax = -1e9
    for (k = 0; k < 4; k++) {
        if (!need("rails", "vbot_min" k) || !need("rails", "vbot_max" k)) continue
        if (v("vbot_min" k) < tmin) tmin = v("vbot_min" k); if (v("vbot_max" k) > tmax) tmax = v("vbot_max" k)
        if (v("vbot_min" k) < 0 || v("vbot_max" k) > VDD) note("rails", sprintf("cell %d: bot %.3f .. %.3f V", k, v("vbot_min" k), v("vbot_max" k)))
    }
    printf "%s: rails: every bottom plate inside 0..%.1f V from S1 closing to TSTOP (%.3f .. %.3f V)%s\n", verdict("rails"), VDD, tmin, tmax, tail("rails")

    # --------------------------------------------------------- reports
    printf "REPORT: power-up: avdd 90 %% at %.1f ns; settled to 1 mV (vs TS0) at pbias0..3 %.0f/%.0f/%.0f/%.0f ns, pbias_r %.0f, vmid %.0f, vref %.0f, vbl %.0f, vrlo %.0f, vramp %.0f ns; T0 = %.2f us\n", \
        v("t_avdd90") * 1e9, v("settle_pbias0_ns"), v("settle_pbias1_ns"), v("settle_pbias2_ns"), v("settle_pbias3_ns"), v("settle_pbias_r_ns"), \
        v("settle_vmid_ns"), v("settle_vref_ns"), v("settle_vbl_ns"), v("settle_vrlo_ns"), v("settle_vramp_ns"), v("p_t0") * 1e6
    printf "REPORT: bias currents at TS0 (device drain currents): icmp0..3 %.3f/%.3f/%.3f/%.3f uA, iramp %.3f uA (%+.2f %% of 3.1314), ivref %.3f uA, ivrlo %.3f uA (%.3f x 1.37), core %.3f uA\n", \
        v("icmp0_ts0_ua"), v("icmp1_ts0_ua"), v("icmp2_ts0_ua"), v("icmp3_ts0_ua"), v("iramp_ts0_ua"), (v("iramp_ts0_ua") / 3.1314 - 1) * 100, \
        v("ivref_ts0_ua"), v("ivrlo_ts0_ua"), v("ivrlo_ts0_ua") / 1.37, v("icore_ts0_ua")
    printf "REPORT: vrlo: %.5f V at T0, %.5f at TS0, %.5f at TR, %.5f at TE (peak-to-peak %.3f mV over [TS0, TSTOP]); vramp - vrlo at TR %+.2f uV (%+.4f LSB: XRST drop from the ramp current + the S1 charge left after the 300 ns gap)\n", \
        v("vrlo_at_t0"), v("vrlo_at_ts0"), v("vrlo_at_tr"), v("vrlo_at_te"), v("vrlo_pp_conv_mv"), v("vramp_vrlo_tr_uv"), v("vramp_vrlo_tr_lsb")
    printf "REPORT: references at TS0: vref %.5f V, vbl %.5f V (VDD/2 error %.2f / %.2f mV), vbl - vref %+.4f mV; at the samples TS0..3 vref is %+.3f/%+.3f/%+.3f/%+.3f mV from final; peaks in [TS0, TR] (vin steps, S2 kicks) vref %.1f, vbl %.1f, tap %.1f mV; back within 0.1 LSB %.0f / %.0f / %.0f ns after the last vin step (vref / vbl / tap)\n", \
        v("vref_at_ts0"), v("vbl_at_ts0"), v("vref_err_ts0") * 1e3, v("vbl_err_ts0") * 1e3, v("vbl_vref_ts0") * 1e3, \
        v("vref_dev_ts0_mv"), v("vref_dev_ts1_mv"), v("vref_dev_ts2_mv"), v("vref_dev_ts3_mv"), v("vref_kick_pk_mv"), v("vbl_kick_pk_mv"), v("vmid_kick_pk_mv"), \
        v("vref_recover_ns"), v("vbl_recover_ns"), v("vmid_recover_ns")
    printf "REPORT: sample: S2 pedestal on bot %.3f/%.3f/%.3f/%.3f mV; vbl - vref(TS_k) at the crossing %.3f/%.3f/%.3f/%.3f mV; alpha (large signal, TR to crossing) %.3f/%.3f/%.3f/%.3f\n", \
        v("ped_bot0") * 1e3, v("ped_bot1") * 1e3, v("ped_bot2") * 1e3, v("ped_bot3") * 1e3, v("refd0") * 1e3, v("refd1") * 1e3, v("refd2") * 1e3, v("refd3") * 1e3, \
        v("alpha0"), v("alpha1"), v("alpha2"), v("alpha3")
    printf "REPORT: ramp: reset level %.5f V (%+.2f LSB from VR_LO), release step %+.3f mV, fitted start %+.3f LSB, slope %.5f V/us (gain error %+.3f %%; first/last 1.2 us %.5f/%.5f, bow %+.3f %%), INL %.3f LSB best-fit / %.3f end-point, VR_HI after %.2f counts; vramp %.4f V at TE, %.4f at TE+TOVR\n", \
        v("vramp_at_tr"), (v("vramp_at_tr") - v("p_vr_lo")) / LSB, v("ramp_release_step_mv"), v("ramp_start_lsb"), v("ramp_slope_vpus"), v("ramp_gain_err_pct"), \
        v("ramp_slope_start_vpus"), v("ramp_slope_end_vpus"), v("ramp_bow_pct"), v("ramp_inl_bf_lsb"), v("ramp_inl_ep_lsb"), v("n_ramp_hi"), v("vramp_at_te"), v("vramp_at_tovr")
    printf "REPORT: ramp kick left by each decision %+.3f/%+.3f/%+.3f/%+.3f mV; pbias_r peak-to-peak over the ramp %.2f uV\n", \
        v("ramp_kick0_mv"), v("ramp_kick1_mv"), v("ramp_kick2_mv"), v("ramp_kick3_mv"), v("pbias_r_ramp_pp_uv")
    for (k = 0; k < 4; k++)
        printf "REPORT: cell %d: vin %.5f V (%.1f LSB); crossing %.2f ns after TR, dout %.2f ns (delay %.3f ns, fall 90-10 %.3f ns), q %.2f ns -> code %d, ideal %d (%+d); err %+.3f LSB analog, %+.3f at dout; plate %+.3f LSB\n", \
            k, v("p_vin" k), v("p_pos" k), (v("t_bot" k) - TR) * 1e9, (v("t_dout" k) - TR) * 1e9, v("cmp_delay" k) * 1e9, v("dout_tf" k) * 1e9, \
            (v("t_q" k) - TR) * 1e9, v("code" k), v("code_ideal" k), v("code_err" k), v("err_x" k), v("err_d" k), v("bps_err" k)
    printf "REPORT: transfer over four cells: trip count gain error %+.3f %%, offset %+.3f LSB at VR_LO; analog crossing %+.3f %% / %+.3f LSB (res %.3f); codes %+.3f %% / %+.3f LSB (res %.3f); the ramp alone predicts %+.3f %%\n", \
        v("xfer_d_gain_err_pct"), v("xfer_d_offset_lsb"), v("xfer_x_gain_err_pct"), v("xfer_x_offset_lsb"), v("xfer_x_res_max_lsb"), \
        v("xfer_q_gain_err_pct"), v("xfer_q_offset_lsb"), v("xfer_q_res_max_lsb"), v("ramp_gain_xfer_pct")
    printf "REPORT: power over the ramp: total %.1f uW = AVDD %.1f (bias_gen %.1f, refs %.1f, vrlo %.1f, ramp %.1f, cells %.1f = %.1f/%.1f/%.1f/%.1f) + DVDD %.2f uW; tracking [T0, TS0]: AVDD %.1f (bias_gen %.1f, refs %.1f, vrlo %.1f, ramp %.1f, cells %.1f), DVDD %.2f uW; cell 0 after its decision %.1f uW\n", \
        v("pw_total_uw"), v("pw_avdd_uw"), v("pw_bg_uw"), v("pw_ref_uw"), v("pw_vrlo_uw"), v("pw_ramp_uw"), v("pw_cells_uw"), v("pw_c0_uw"), v("pw_c1_uw"), v("pw_c2_uw"), v("pw_c3_uw"), v("pw_dvdd_uw"), \
        v("pw_avdd_idle_uw"), v("pw_bg_idle_uw"), v("pw_ref_idle_uw"), v("pw_vrlo_idle_uw"), v("pw_ramp_idle_uw"), v("pw_cells_idle_uw"), v("pw_dvdd_idle_uw"), v("pw_c0_post_uw")
    exit fail ? 1 : 0
}
