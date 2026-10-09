# Acceptance for `make lvs`: KLayout's LVS against a named netlist.
#
# The netlist is echoed with the verdict on purpose. "LVS clean" means
# nothing without saying what the layout was compared against.

/^[a-z_0-9]+ = / { v[$1] = substr($0, index($0, "= ") + 2) }

END {
    fail = 0
    n = 0
    for (k in v) {
        if (k !~ /_lvs_match$/) continue
        n++
        c = substr(k, 1, length(k) - length("_lvs_match"))
        if (v[k] + 0 == 1)
            printf "PASS: %s LVS matches %s\n", toupper(c),
                v[c "_lvs_netlist"]
        else {
            printf "FAIL: %s LVS %s against %s\n", toupper(c), v[c "_lvs"],
                v[c "_lvs_netlist"]; fail = 1
        }
    }
    if (n == 0) { print "FAIL: no cell was compared"; fail = 1 }
    exit fail
}
