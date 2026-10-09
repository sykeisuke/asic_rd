# Acceptance for `make drc`: the KLayout signoff deck, density apart.
#
# Density is reported and not judged. M1.4 through MT.3 and PL.8 read
# "coverage over the entire die shall be >30%": a few-micron cell cannot
# satisfy them and fill satisfies them at chip level.

/^[a-z_0-9]+ = / { v[$1] = substr($0, index($0, "= ") + 2) }

END {
    fail = 0
    n = 0
    for (k in v) {
        if (k !~ /_drc_violations$/) continue
        n++
        c = substr(k, 1, length(k) - length("_drc_violations"))
        if (v[k] + 0 == 0)
            printf "PASS: %s KLayout DRC clean (gf180mcu.drc, density apart)\n",
                toupper(c)
        else {
            printf "FAIL: %s has %s KLayout DRC violations: %s\n", toupper(c),
                v[k], v[c "_drc_rules"]; fail = 1
        }
        printf "INFO: %s die-density rules not met at cell level: %s (%s)\n",
            toupper(c), v[c "_density_violations"], v[c "_density_rules"]
    }
    if (n == 0) { print "FAIL: no cell was checked"; fail = 1 }
    exit fail
}
