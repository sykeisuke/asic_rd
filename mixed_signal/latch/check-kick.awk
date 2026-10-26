# Acceptance on data/kick.csv (tb_kick.spice, bench.py kick): comparator +
# latch on the unit cell's charge path at codes 4, 64, 128, 250, each at 8
# crossing phases within the count, clock running against clock stopped.
#
#   awk -f check-kick.awk data/kick.csv
#
# Only the kick AT the sampling edge moves a code, and only its code-to-code
# variation is an error; its common value is a pedestal term.
# Gates (SPEC.md S10, S12):
#   S10  max |kick at the edge - its mean over codes| <= 0.01 LSB (L6)
#   S12  every run completed; in every clock-running run q fell at the first
#        sampling edge after dout's crossing (runs within 1 ns of an edge are
#        not judged)
# REPORT: the common kick, its peak-to-peak over the count, comparator's
# delay and dout fall with this latch, with tspc_dff and into 10 fF.
BEGIN { FS = ","; fail = 0; tcount_ps = 50000; lim = 0.01 }
NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
{
    n++
    k[n] = $c["kick_at_edge_ps"] + 0; sum += k[n]
    if ($c["n_ok"] + 0 != 2 * $c["n_phases"] + 2) { printf "FAIL: kick code %s: %s of %d runs completed\n", $c["code"], $c["n_ok"], 2 * $c["n_phases"] + 2; fail = 1 }
    if ($c["n_latch_ok"] + 0 != $c["n_phases"] + 0) { printf "FAIL: kick code %s: q fell at the wrong edge in %d of %s phases\n", $c["code"], $c["n_phases"] - $c["n_latch_ok"], $c["n_phases"]; fail = 1 }
    else printf "PASS: kick code %s: q fell at the first sampling edge after dout in all %s phases\n", $c["code"], $c["n_phases"]
    printf "REPORT: kick code %s: %.1f ps at the sampling edge, %.1f ps peak-to-peak over the count; comparator delay in this bench %.2f ns with latch (%.2f ns with tspc_dff, %.2f ns into 10 fF), dout fall %.2f ns (%.2f, %.2f ns)\n", \
        $c["code"], k[n], $c["kick_pp_ps"], $c["delay_scff_ns"], $c["delay_tspc_ns"], $c["delay_cap10_ns"], $c["dout_fall_scff_ns"], $c["dout_fall_tspc_ns"], $c["dout_fall_cap10_ns"]
    d_s = $c["delay_scff_ns"]; d_t = $c["delay_tspc_ns"]; f_s = $c["dout_fall_scff_ns"]
}
END {
    if (n == 0) { print "FAIL: kick table is empty"; exit 1 }
    mean = sum / n; sp = 0
    for (i = 1; i <= n; i++) { d = k[i] - mean; if (d < 0) d = -d; if (d > sp) sp = d }
    printf "meas_kick_mean_lsb = %.6e\n", mean / tcount_ps
    printf "meas_kick_spread_lsb = %.6e\n", sp / tcount_ps
    printf "meas_cmp_delay_with_scff_ns = %s\n", d_s
    printf "meas_cmp_delay_with_tspc_ns = %s\n", d_t
    printf "meas_cmp_dout_fall_with_scff_ns = %s\n", f_s
    if (sp / tcount_ps <= lim) printf "PASS: kick: code-dependent part %.2e LSB <= %.2f LSB (common part %.2e LSB, a pedestal term)\n", sp / tcount_ps, lim, mean / tcount_ps
    else { printf "FAIL: kick: code-dependent part %.2e LSB > %.2f LSB\n", sp / tcount_ps, lim; fail = 1 }
    exit fail
}
