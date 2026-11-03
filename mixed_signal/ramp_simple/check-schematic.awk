# check-schematic.awk -- ramp_gen.sch must netlist back to ramp_gen.spice,
# device for device.
#
#   awk -f check-schematic.awk ramp_gen.spice work/ramp_gen_sch.spice
#   awk -v sub_=ramp_simple -f check-schematic.awk ramp_simple.spice work/ramp_simple_sch.spice
#
# File 1 is the controlled netlist (`.subckt ramp_gen`), file 2 what xschem
# wrote from ramp_gen.sch (the subcircuit as the top level, its ports on the
# commented `**.subckt ramp_gen ...` line). Every X device is compared on its
# name, its terminals in order, its model and its parameter set (keys
# case-folded, order free, m defaulting to 1, engineering numbers
# canonicalised, braces / quotes / xschem's backslashes dropped). The port
# order must match the deck's, and every net the drawing uses must be one the
# deck uses (an unlabelled wire becomes net1, which is not evidence).
#
# One PASS:/FAIL: line per check, exit non-zero on failure.

function nval(t,    mant, suf, mul) {
    if (t !~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?[a-z]*$/) return t
    mant = t; sub(/[a-z]+$/, "", mant)
    if (mant == "" || mant ~ /[eE][-+]?$/) return t
    suf = substr(t, length(mant) + 1); mul = 1
    if (suf == "meg") mul = 1e6; else if (suf == "k") mul = 1e3; else if (suf == "m") mul = 1e-3
    else if (suf == "u") mul = 1e-6; else if (suf == "n") mul = 1e-9; else if (suf == "p") mul = 1e-12
    else if (suf == "f") mul = 1e-15; else if (suf != "") return t
    return sprintf("%.12g", (mant + 0) * mul)
}
function sortk(k, n,    i, j, t) {
    for (i = 2; i <= n; i++) { t = k[i]; for (j = i - 1; j >= 1 && k[j] > t; j--) k[j + 1] = k[j]; k[j + 1] = t }
}
function devkey(line, side,    s, n, a, i, first, nodes, model, np, pk, eq, out, hasm) {
    s = tolower(line); gsub(/[{}'"\\]/, "", s)
    n = split(s, a, /[ \t]+/)
    first = n + 1
    for (i = 2; i <= n; i++) if (index(a[i], "=") > 1) { first = i; break }
    model = a[first - 1]
    nodes = ""
    for (i = 2; i <= first - 2; i++) { nodes = nodes (nodes == "" ? "" : "/") a[i]; seen[side, a[i]] = 1 }
    np = 0; hasm = 0
    for (i = first; i <= n; i++) {
        eq = index(a[i], "=")
        if (eq <= 1) { pk[++np] = "?" a[i]; continue }
        if (substr(a[i], 1, eq - 1) == "m") hasm = 1
        pk[++np] = substr(a[i], 1, eq - 1) "=" nval(substr(a[i], eq + 1))
    }
    if (!hasm) pk[++np] = "m=1"
    sortk(pk, np)
    out = ""
    for (i = 1; i <= np; i++) out = out (out == "" ? "" : " ") pk[i]
    return nodes " | " model " | " out
}
function flush(side,    name, t) {
    if (buf == "") return
    if (buf ~ /^[Xx]/ && inside) {
        split(buf, t, /[ \t]+/); name = toupper(t[1])
        key[side, name] = devkey(buf, side); names[name] = 1; count[side]++
    } else if (buf ~ /^[RrCcVvIiMm]/ && inside) {
        split(buf, t, /[ \t]+/); stray = stray " " t[1] "(" side ")"
    }
    buf = ""
}
BEGIN { bad = 0; stray = ""; if (sub_ == "") sub_ = "ramp_gen" }
FNR == 1 { flush(side); side = (FILENAME == ARGV[1]) ? "ref" : "sch"; inside = (side == "sch") }
{
    sub(/\r$/, "")
    line = $0
    if (side == "ref") {
        if (line ~ /^\.subckt[ \t]/) { n = split(line, a, /[ \t]+/); if (a[2] == sub_) { flush(side); inside = 1; for (i = 3; i <= n; i++) ports["ref"] = ports["ref"] " " a[i]; next } }
        if (line ~ /^\.ends/) { flush(side); inside = 0; next }
    } else {
        if (line ~ /^\*\*\.subckt[ \t]/) { n = split(line, a, /[ \t]+/); for (i = 3; i <= n; i++) ports["sch"] = ports["sch"] " " a[i]; next }
        if (line ~ /^\*\*\.ends/) next
    }
    if (line ~ /^\+/) { buf = buf " " substr(line, 2); next }
    flush(side)
    if (line ~ /^[ \t]*$/ || line ~ /^\*/ || line ~ /^\./) next
    buf = line
}
END {
    flush(side)
    ok = (count["ref"] > 0 && count["sch"] > 0)
    printf "%s: netlists read -- deck: %d devices in %s, drawing: %d\n", ok ? "PASS" : "FAIL", count["ref"] + 0, sub_, count["sch"] + 0
    if (!ok) exit 1
    miss = 0; extra = 0; diff = 0; matched = 0
    for (nm in names) {
        if (!(("ref", nm) in key)) { extra++; printf "FAIL: %s is drawn but not in %s.spice\n", nm, sub_; continue }
        if (!(("sch", nm) in key)) { miss++; printf "FAIL: %s is in %s.spice but not drawn\n", nm, sub_; continue }
        if (key["ref", nm] != key["sch", nm]) {
            diff++; printf "FAIL: %s differs\n  deck: %s\n  sch:  %s\n", nm, key["ref", nm], key["sch", nm]
        } else matched++
    }
    ok = (miss + extra + diff == 0)
    printf "%s: %s.sch netlists to .subckt %s -- %d devices match on terminals, model and parameters (%d missing, %d extra, %d different)\n", \
        ok ? "PASS" : "FAIL", sub_, sub_, matched, miss, extra, diff
    if (!ok) bad = 1
    if (stray != "") { printf "FAIL: non-subcircuit devices in the subcircuit:%s\n", stray; bad = 1 }
    pr = ports["ref"]; ps = ports["sch"]; gsub(/^ +/, "", pr); gsub(/^ +/, "", ps)
    ok = (pr == ps)
    printf "%s: %s ports in the deck's order: %s%s\n", ok ? "PASS" : "FAIL", sub_, pr, ok ? "" : " (drawing: " ps ")"
    if (!ok) bad = 1
    nb = 0; wn = ""
    for (k in seen) { split(k, kk, SUBSEP); if (kk[1] != "sch") continue; if (!(("ref", kk[2]) in seen)) { nb++; wn = wn " " kk[2] } }
    ok = (nb == 0)
    printf "%s: every net drawn is a net of the deck's subcircuit%s\n", ok ? "PASS" : "FAIL", nb ? " -- stray:" wn : ""
    if (!ok) bad = 1
    exit bad
}
