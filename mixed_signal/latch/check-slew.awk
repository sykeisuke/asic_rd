# Acceptance on data/slew.csv (bench.py slew): the drive bench at clock
# 10-90 % edges 0.2 .. 8 ns, at the drive cells (typical 27 C 3.3 V, ss 0 C
# 3.0 V, ff 85 C 3.6 V, ss 85 C 3.0 V). A row passes when q's four edges are at the right
# sampling edges and q stays within 1.0 V of its rail in every static state.
#
#   awk -v req=1.0 -f check-slew.awk data/slew.csv
#
# Gate (SPEC.md S6): every edge up to `req` ns (the clock-tree requirement
# at each latch, assumed 1.0 ns) passes at every cell.
# REPORT: the slowest edge below which everything passes, per cell.
BEGIN { FS = ","; fail = 0; if (req == "") req = 1.0 }
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
{
    cell = $c["corner"] "_" $c["temp"] "C_" $c["vdd"] "V"
    s = $c["clk_t1090_ns"] + 0; p = $c["pass"] + 0
    cells[cell] = 1
    if (s <= req + 1e-9) { nreq[cell]++; if (!p) { bad[cell] = bad[cell] " " s; fail = 1 } }
    edge[cell, ++ne[cell]] = s; ok[cell, ne[cell]] = p
}
END {
    for (cl in cells) {
        if (nreq[cl] == 0) { printf "FAIL: slew %s: no row at or below %.2f ns\n", cl, req; fail = 1; continue }
        if (bad[cl] == "") printf "PASS: slew %s: every clock edge up to %.2f ns 10-90 %% passes (%d rows)\n", cl, req, nreq[cl]
        else printf "FAIL: slew %s: fails at clock edge(s)%s ns (requirement %.2f ns)\n", cl, bad[cl], req
        # largest edge below which every row passes (rows sorted by edge)
        best = 0
        for (k = 1; k <= ne[cl]; k++) for (j = k + 1; j <= ne[cl]; j++) if (edge[cl, j] < edge[cl, k]) {
            t = edge[cl, j]; edge[cl, j] = edge[cl, k]; edge[cl, k] = t
            t = ok[cl, j]; ok[cl, j] = ok[cl, k]; ok[cl, k] = t }
        for (k = 1; k <= ne[cl]; k++) { if (!ok[cl, k]) break; best = edge[cl, k] }
        name = cl; gsub(/\./, "p", name)          # a metric name cannot carry a dot
        printf "meas_slew_limit_%s_ns = %g\n", name, best
        printf "REPORT: slew %s: passes every clock edge up to %g ns 10-90 %% (largest tested %g ns)\n", cl, best, edge[cl, ne[cl]]
    }
    exit fail
}
