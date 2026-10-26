# Acceptance on data/drive.csv (tb_drive.spice, bench.py drive): one row per
# cell (typical 27 C 3.3 V, ss 0 C 3.0 V, ff 85 C 3.6 V, ss 85 C 3.0 V), clock
# edge 0.5 ns 10-90 %, d with comparator's slowest dout fall (10.4 ns), q
# into 50 fF. The same table for ../latch_bkp/cmp_tspc/tspc_dff on the same bench is
# data/drive_tspc.csv (REPORT only, -v ref=data/drive_tspc.csv).
#
#   awk -v ref=data/drive_tspc.csv -f check-drive.awk data/drive.csv
#
# Gates (SPEC.md):
#   S2  q moves at the sampling edge that sees d's move, for d falling and
#       rising in both clock phases, and nowhere else (4 q edges)
#   S3  input load on dout <= 10 fF (NOISE_BUDGET.md L5)
#   S4  clock-to-q <= 20 ns; q 90-10 % fall into 50 fF <= 2.15 ns
#   S5  in every static state q stays within 1.0 V of its rail
# REPORT: clock-to-q, edge times, clock power in both d states against the TSPC.
BEGIN {
    FS = ","; fail = 0; cin_max = 10; tcq_max = 20; fall_max = 2.15; glitch = 1.0
    if (ref != "") {
        getline hdr < ref; nh = split(hdr, h, ",")
        for (i = 1; i <= nh; i++) rc[h[i]] = i
        while ((getline line < ref) > 0) {
            split(line, f, ","); cell = f[rc["corner"]] "_" f[rc["temp"]] "_" f[rc["vdd"]]
            tp_hi[cell] = f[rc["p_dhigh_uw"]]; tp_lo[cell] = f[rc["p_dlow_uw"]]; tf[cell] = f[rc["q_edge_f1_ns"]]
        }
    }
}
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
function v(k) { return (k in c) ? $c[k] : "nan" }
{
    n++
    tag = v("tag"); vdd = v("vdd") + 0
    if (v("ok") != 1) { printf "FAIL: drive %s: ngspice did not complete\n", tag; fail = 1; next }
    if (v("edges_ok") == 1)
        printf "PASS: drive %s: q moves once at each of the 4 sampling edges (d falls/rises with clk high and low)\n", tag
    else { printf "FAIL: drive %s: q edges wrong (n %s; tcq f1 %s r0 %s f0 %s r1 %s ns)\n", tag, v("n_qedges"), v("tcq_f1_ns"), v("tcq_r0_ns"), v("tcq_f0_ns"), v("tcq_r1_ns"); fail = 1 }
    if (v("cin_max_ff") + 0 <= cin_max) printf "PASS: drive %s: load on dout %.2f fF <= %d fF\n", tag, v("cin_max_ff"), cin_max
    else { printf "FAIL: drive %s: load on dout %.2f fF > %d fF\n", tag, v("cin_max_ff"), cin_max; fail = 1 }
    t1 = v("tcq_f1_ns") + 0; t0 = v("tcq_f0_ns") + 0
    if (t1 > 0 && t0 > 0 && t1 <= tcq_max && t0 <= tcq_max) printf "PASS: drive %s: clock-to-q (fall) %.2f / %.2f ns <= %d ns\n", tag, t1, t0, tcq_max
    else { printf "FAIL: drive %s: clock-to-q (fall) %s / %s ns\n", tag, v("tcq_f1_ns"), v("tcq_f0_ns"); fail = 1 }
    f1 = v("q_edge_f1_ns") + 0; f0 = v("q_edge_f0_ns") + 0
    if (f1 <= fall_max && f0 <= fall_max) printf "PASS: drive %s: q 90-10 %% fall into 50 fF %.2f ns <= %.2f ns, no buffer\n", tag, (f1 > f0 ? f1 : f0), fall_max
    else { printf "FAIL: drive %s: q fall %.2f / %.2f ns > %.2f ns\n", tag, f1, f0, fall_max; fail = 1 }
    hi = v("q_min_high") + 0; lo = v("q_max_low") + 0
    if (hi >= vdd - glitch && lo <= glitch) printf "PASS: drive %s: q static states within %.1f mV / %.1f mV of the rails (limit 1.0 V)\n", tag, (vdd - hi) * 1e3, lo * 1e3
    else { printf "FAIL: drive %s: q glitch %.3f V below VDD / %.3f V above 0 (limit 1.0 V)\n", tag, vdd - hi, lo; fail = 1 }
    name = tag; sub(/^drive_/, "", name)
    printf "meas_drive_%s_tcq_fall_ns = %s\n", name, v("tcq_f1_ns")
    printf "meas_drive_%s_q_fall_ns = %s\n", name, v("q_edge_f1_ns")
    printf "meas_drive_%s_cin_ff = %s\n", name, v("cin_max_ff")
    printf "meas_drive_%s_p_dhigh_uw = %s\n", name, v("p_dhigh_uw")
    printf "meas_drive_%s_p_dlow_uw = %s\n", name, v("p_dlow_uw")
    printf "meas_drive_%s_i_leak_na = %s\n", name, v("i_leak_na")
    cell = v("corner") "_" v("temp") "_" v("vdd")
    printf "REPORT: drive %s: clk-to-q fall %.2f ns rise %.2f ns; q fall %.2f ns rise %.2f ns; clock power %.2f uW with d high, %.2f uW with d low (tspc_dff on this bench: %s / %s uW, q fall %s ns); leakage %.2f nA\n", \
        tag, v("tcq_f1_ns"), v("tcq_r1_ns"), v("q_edge_f1_ns"), v("q_edge_r1_ns"), v("p_dhigh_uw"), v("p_dlow_uw"), \
        (cell in tp_hi) ? tp_hi[cell] : "n/a", (cell in tp_lo) ? tp_lo[cell] : "n/a", (cell in tf) ? tf[cell] : "n/a", v("i_leak_na")
    if (cell in tp_hi) { printf "meas_drive_%s_tspc_p_dhigh_uw = %s\n", name, tp_hi[cell]; printf "meas_drive_%s_tspc_p_dlow_uw = %s\n", name, tp_lo[cell] }
}
END {
    if (n == 0) { print "FAIL: drive table is empty"; exit 1 }
    exit fail
}
