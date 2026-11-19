# check-pvt.awk -- acceptance of the analog_top functional record over PVT.
#
#   awk -F, -f check-pvt.awk data/pvt_cells.csv
#
# data/pvt_cells.csv (pvt_reduce.py): one row per cell, check-func.awk's
# verdict per gate (g_*) and the scalars below. One PASS:/FAIL: line per gate
# over every cell, the worst cell named; REPORT: lines are recorded, not
# judged. Exit 1 on any FAIL.
#
# Gates and where each threshold comes from:
#   complete     every listed cell simulated and measured (ngspice status 0)
#   functional   every check-func.awk gate (sequencer, bias, references, vrlo,
#                sample, plate, armed, decision, latch, range, order,
#                transfer, rails) PASSes at every cell: the typical gates,
#                thresholds unchanged, at each corner
#   decision     every cell's four q fall exactly once and the codes rise in
#                cell order (inputs 16.5 / 80.5 / 160.5 / 240.5 LSB)
#   transfer     gain + offset line of the trip count, max residual <= 0.5 LSB
#                (check-func.awk RES_MAX)
#   plate        input-referred error spread over the four cells <= 0.25 LSB
#                (check-func.awk SPREAD_MAX)
#   armed        at TR every bottom plate below V_REF: margin > 0
#   sequencer    S2 -> S0 and S0 -> S1 >= 5 ns [U] (sample_seq Q2)
#   overvoltage  every bottom plate <= 3.3 V from S1 closing to TSTOP: the
#                3.3 V devices (spec 5.3 over-voltage constraint); check-func's
#                rails gate holds it to the cell's own VDD
# Reported: the codes against the typical record (the calibration removes a
# common offset and gain), gain error, comparator delay, power.

function isnum(s) { return s ~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/ }
function v(k) { return $(col[k]) + 0 }
function s(k) { return $(col[k]) }
function lim(g, txt) { nbad[g]++; if (nbad[g] <= 6) bad[g] = bad[g] ((bad[g] == "") ? "" : "; ") txt }
function verdict(g) { if (nbad[g]) fail = 1; return nbad[g] ? "FAIL" : "PASS" }
function tail(g) { return nbad[g] ? ": " bad[g] (nbad[g] > 6 ? sprintf(" (+%d more)", nbad[g] - 6) : "") : "" }
function worst(g, x, cell, hi) {
    if (!(g in wv) || (hi && x > wv[g]) || (!hi && x < wv[g])) { wv[g] = x; wc[g] = cell }
}

NR == 1 { for (i = 1; i <= NF; i++) col[$i] = i; next }
{
    n++
    c = s("cell")
    if (!isnum(s("n_meas")) || v("n_meas") == 0 || s("sim_status") != "0") { lim("complete", c " not simulated (status " s("sim_status") ")"); next }
    ok++
    if (v("n_fail") > 0) lim("functional", c ": " s("failed"))
    if (v("decided_once") != 1 || v("codes_inc") != 1)
        lim("decision", sprintf("%s: once %d, increasing %d (codes %s/%s/%s/%s)", c, v("decided_once"), v("codes_inc"), s("code0"), s("code1"), s("code2"), s("code3")))
    x = s("res_max_lsb"); if (!isnum(x) || x + 0 > 0.5) lim("transfer", c " residual " x " LSB"); else worst("res", x + 0, c, 1)
    x = s("plate_spread_lsb"); if (!isnum(x) || x + 0 > 0.25) lim("plate", c " spread " x " LSB"); else worst("plate", x + 0, c, 1)
    x = s("armed_mv"); if (!isnum(x) || x + 0 <= 0) lim("armed", c " margin " x " mV"); else worst("armed", x + 0, c, 0)
    x = s("seq_gap_t4_min"); if (!isnum(x) || x + 0 < 1) lim("sequencer", c " gap " x " x four-inverter delay"); else { worst("gap", x + 0, c, 0); worst("gapns", s("seq_gap_min_ns") + 0, c, 0) }
    x = s("bot_max_v"); if (!isnum(x) || x + 0 > 3.3) lim("overvoltage", c " bottom plate " x " V"); else worst("bot", x + 0, c, 1)
    if (isnum(s("bot_max_v"))) worst("botall", v("bot_max_v"), c, 1)
    for (k = 0; k < 4; k++) if (isnum(s("dcode" k))) { worst("dlo", v("dcode" k), c " cell " k, 0); worst("dhi", v("dcode" k), c " cell " k, 1) }
    if (isnum(s("gain_err_pct"))) { worst("glo", v("gain_err_pct"), c, 0); worst("ghi", v("gain_err_pct"), c, 1) }
    if (isnum(s("cmp_delay_max_ns"))) { worst("dly", v("cmp_delay_max_ns"), c, 1); worst("dlymin", v("cmp_delay_min_ns"), c, 0) }
    if (isnum(s("pw_total_uw"))) { worst("pw", v("pw_total_uw"), c, 1); worst("pwlo", v("pw_total_uw"), c, 0) }
    if (isnum(s("pw_track_uw"))) worst("pwt", v("pw_track_uw"), c, 1)
    if (isnum(s("plate_mean_lsb"))) { worst("pmlo", v("plate_mean_lsb"), c, 0); worst("pmhi", v("plate_mean_lsb"), c, 1) }
}
END {
    if (n == 0) { print "FAIL: pvt: no cell in data/pvt_cells.csv"; exit 1 }
    printf "%s: pvt complete: %d of %d cells simulated and measured%s\n", verdict("complete"), ok, n, tail("complete")
    printf "%s: pvt functional: every check-func gate passes at every cell (%d cells)%s\n", verdict("functional"), ok, tail("functional")
    printf "%s: pvt decision: four q falls exactly once and codes rising in cell order at every cell%s\n", verdict("decision"), tail("decision")
    printf "%s: pvt transfer: max residual of the trip-count line %.4f LSB <= 0.5 (worst %s)%s\n", verdict("transfer"), wv["res"], wc["res"], tail("transfer")
    printf "%s: pvt plate: spread of the input-referred error over the four cells %.4f LSB <= 0.25 (worst %s)%s\n", verdict("plate"), wv["plate"], wc["plate"], tail("plate")
    printf "%s: pvt armed: smallest margin of a bottom plate below V_REF at TR %.2f mV > 0 (worst %s)%s\n", verdict("armed"), wv["armed"], wc["armed"], tail("armed")
    printf "%s: pvt sequencer: smallest S2 -> S0 / S0 -> S1 gap %.2f x the cell's four-inverter delay >= 1 (worst %s); smallest gap %.3f ns (%s); 10/90 clearance in the functional gate (ADR 0031)%s\n", verdict("sequencer"), wv["gap"], wc["gap"], wv["gapns"], wc["gapns"], tail("sequencer")
    printf "%s: pvt overvoltage: highest bottom plate %.3f V <= 3.3 V (at %s)%s\n", verdict("overvoltage"), wv["botall"], wc["botall"], tail("overvoltage")
    printf "REPORT: pvt codes vs the typical record: %+d (%s) .. %+d (%s)\n", wv["dlo"], wc["dlo"], wv["dhi"], wc["dhi"]
    printf "REPORT: pvt trip-count gain error %+.3f %% (%s) .. %+.3f %% (%s); plate mean %+.3f (%s) .. %+.3f LSB (%s)\n", wv["glo"], wc["glo"], wv["ghi"], wc["ghi"], wv["pmlo"], wc["pmlo"], wv["pmhi"], wc["pmhi"]
    printf "REPORT: pvt comparator delay from the plate crossing %.2f (%s) .. %.2f ns (%s)\n", wv["dlymin"], wc["dlymin"], wv["dly"], wc["dly"]
    printf "REPORT: pvt power over the ramp %.1f (%s) .. %.1f uW (%s); tracking up to %.1f uW (%s)\n", wv["pwlo"], wc["pwlo"], wv["pw"], wc["pw"], wv["pwt"], wc["pwt"]
    exit fail ? 1 : 0
}
