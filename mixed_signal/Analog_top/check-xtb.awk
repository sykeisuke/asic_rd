# check-xtb.awk -- the xschem testbench, simulated, must reproduce the hand
# bench: every measure of data/func_measures.txt (func phase, tb_analog_top.spice)
# against the same measure of data/xtb_measures.txt (xtb phase, the netlist
# xschem writes from tb_analog_top.sch).
#
#   awk -f check-xtb.awk data/func_measures.txt data/xtb_measures.txt
#
# The two netlists are the same circuit (schematic.sh proves it instance by
# instance), so any difference is numerical (device order in the matrix,
# time-step history). The limits are what would matter for the ADC, at
# TCOUNT = 50 ns and LSB = 1.5 V / 256 = 5.86 mV:
#   codes        code*, code_ideal*, code_err*           identical
#   parameters   p_*                                     identical (rel 1e-9)
#   times        t_*, *delay*, dout_tf*  [s]             |d| <= 1 ns  (0.02 LSB of a count)
#   LSB values   err_x*, err_d*, bps_err*, n_ramp_hi     |d| <= 0.02 LSB
#   voltages     every other v-like measure  [V]         |d| <= 0.5 mV (0.085 LSB)
#   ratios       alpha*                                  |d| <= 1e-3
#   currents     i_*  [A]                                |d| <= max(1 %, 10 nA)
#   power        pw_* [W]                                |d| <= max(1 %, 0.1 uW)
# One PASS:/FAIL: line per class plus completeness; the worst difference of
# each class as `xtb_worst_<class> = value` (times in ns, voltages in mV).

function isnum(s) { return s ~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/ }
function absd(x)  { return x < 0 ? -x : x }

function cls(n) {
    if (n ~ /^code/)                                  return "code"
    if (n ~ /^p_/)                                    return "param"
    if (n ~ /^(err_x|err_d|bps_err)[0-9]/ || n == "n_ramp_hi") return "lsb"
    if (n ~ /^t_/ || n ~ /delay/ || n ~ /^dout_tf/)   return "time"
    if (n ~ /^alpha/)                                 return "ratio"
    if (n ~ /^i_/)                                    return "current"
    if (n ~ /^pw_/)                                   return "power"
    return "volt"
}

BEGIN {
    NCLS = split("code param time lsb volt ratio current power", CL, " ")
    unit["time"] = 1e9;  uname["time"] = "ns"
    unit["volt"] = 1e3;  uname["volt"] = "mV"
    unit["lsb"] = 1;     uname["lsb"] = "LSB"
    unit["code"] = 1;    uname["code"] = "codes"
    unit["param"] = 1;   uname["param"] = "(rel)"
    unit["ratio"] = 1;   uname["ratio"] = ""
    unit["current"] = 1e9; uname["current"] = "nA"
    unit["power"] = 1e6; uname["power"] = "uW"
}

FNR == 1 { side++ }
$2 == "=" && isnum($3) {
    v[side, $1] = $3 + 0
    if (side == 1) order[++n] = $1
}

END {
    if (n == 0) { print "FAIL: xtb: no hand-bench measures to compare against"; exit 1 }
    for (i = 1; i <= n; i++) {
        k = order[i]; c = cls(k)
        cnt[c]++
        if (!((2, k) in v)) { miss = miss " " k; nmiss++; continue }
        a = v[1, k]; b = v[2, k]; d = absd(a - b)
        if      (c == "code")    { ok = (a == b); m = d }
        else if (c == "param")   { ok = (d <= 1e-9 * absd(a)); m = (a == 0) ? d : d / absd(a) }
        else if (c == "time")    { ok = (d <= 1e-9); m = d }
        else if (c == "lsb")     { ok = (d <= 0.02); m = d }
        else if (c == "volt")    { ok = (d <= 0.5e-3); m = d }
        else if (c == "ratio")   { ok = (d <= 1e-3); m = d }
        else if (c == "current") { tol = 0.01 * absd(a); if (tol < 10e-9) tol = 10e-9; ok = (d <= tol); m = d }
        else                     { tol = 0.01 * absd(a); if (tol < 0.1e-6) tol = 0.1e-6; ok = (d <= tol); m = d }
        if (!ok) { bad[c]++; badn[c] = badn[c] " " k "(" a "/" b ")" }
        if (!(c in worst) || m > worst[c]) { worst[c] = m; wname[c] = k }
    }
    st = 0
    if (nmiss) { printf "FAIL: xtb: %d hand-bench measure(s) missing from the xschem run:%s\n", nmiss, substr(miss, 1, 300); st = 1 }
    else printf "PASS: xtb: all %d hand-bench measures present in the xschem testbench run\n", n
    lim["code"] = "identical"; lim["param"] = "identical"; lim["time"] = "<= 1 ns"
    lim["lsb"] = "<= 0.02 LSB"; lim["volt"] = "<= 0.5 mV"; lim["ratio"] = "<= 1e-3"
    lim["current"] = "<= max(1 %, 10 nA)"; lim["power"] = "<= max(1 %, 0.1 uW)"
    for (j = 1; j <= NCLS; j++) {
        c = CL[j]
        if (!cnt[c]) continue
        if (bad[c]) {
            printf "FAIL: xtb: %s: %d of %d differ beyond %s:%s\n", c, bad[c], cnt[c], lim[c], substr(badn[c], 1, 300)
            st = 1
        } else
            printf "PASS: xtb: %s: %d measures within %s of the hand bench (worst %s, %.4g %s)\n",
                   c, cnt[c], lim[c], wname[c], worst[c] * unit[c], uname[c]
        printf "xtb_worst_%s = %.6g\n", c, worst[c] * unit[c]
    }
    exit st
}
