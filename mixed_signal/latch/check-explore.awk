# Report on data/explore.csv (bench.py explore): every candidate of
# scff_variants.spice (dfxtn_2 alone, + buff_2, + buff_4) through the drive
# bench at four cells, q into 50 fF.
#
#   awk -f check-explore.awk data/explore.csv
#
# Gate (SPEC.md s.3, the buffer question): the flop ALONE meets S4's q fall
# (<= 2.15 ns into 50 fF) and S2 at every cell; if it does, no buffer is
# added. REPORT: each candidate's clock-to-q, q fall and power per cell.
BEGIN { FS = ","; fall_max = 2.15 }
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
{
    s = $c["subckt"]; cell = $c["corner"] "_" $c["temp"] "C_" $c["vdd"] "V"
    printf "REPORT: explore %s %s: edges %s, clock-to-q %.2f ns, q fall %.2f ns into 50 fF, %.2f uW clocked (d high)\n", \
        s, cell, $c["edges_ok"], $c["tcq_f1_ns"], $c["q_edge_f1_ns"], $c["p_dhigh_uw"]
    if (s == "scff_bare") {
        nb++
        if ($c["ok"] == 1 && $c["edges_ok"] == 1 && $c["q_edge_f1_ns"] + 0 <= fall_max && $c["q_edge_f0_ns"] + 0 <= fall_max) okb++
        if ($c["q_edge_f1_ns"] + 0 > worst) { worst = $c["q_edge_f1_ns"] + 0; wcell = cell }
    }
}
END {
    if (nb == 0) { print "FAIL: explore: no scff_bare rows"; exit 1 }
    printf "meas_explore_bare_qfall_worst_ns = %g\n", worst
    if (okb == nb) { printf "PASS: explore: dfxtn_2 alone drives 50 fF at all %d cells (worst q fall %.2f ns at %s <= %.2f ns): no buffer\n", nb, worst, wcell, fall_max; exit 0 }
    printf "FAIL: explore: dfxtn_2 alone misses the drive gate at %d of %d cells: a buffer is needed\n", nb - okb, nb
    exit 1
}
