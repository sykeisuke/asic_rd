# Acceptance for `make gf-inverter`: the gdsfactory inverter was drawn,
# rendered, and passes the PDK's KLayout DRC and LVS.
#
# Density is reported and not judged (see ../check-drc.awk for why).

/^[a-z_0-9]+ = / { v[$1] = substr($0, index($0, "= ") + 2) }

END {
    fail = 0
    c = "inv_gf"

    if (v[c "_gds_bytes"] + 0 > 0)
        printf "PASS: INV_GF drawn with gdsfactory: %s devices, %s pins, %s x %s um (%s um^2)\n",
            v[c "_devices"], v[c "_pins"], v[c "_width_um"], v[c "_height_um"],
            v[c "_area_um2"]
    else { print "FAIL: INV_GF wrote no GDS"; fail = 1 }

    if (v[c "_devices"] + 0 != 2) {
        printf "FAIL: INV_GF has %s transistor instances, expected 2\n",
            v[c "_devices"]; fail = 1
    }

    if (v[c "_render_bytes"] + 0 > 0)
        print "PASS: INV_GF rendered from its own GDS"
    else { print "FAIL: INV_GF produced no render"; fail = 1 }

    if (!((c "_drc_violations") in v)) {
        print "FAIL: INV_GF KLayout DRC did not run"; fail = 1
    } else if (v[c "_drc_violations"] + 0 == 0)
        print "PASS: INV_GF KLayout DRC clean (gf180mcu.drc, density apart)"
    else {
        printf "FAIL: INV_GF has %s KLayout DRC violations: %s\n",
            v[c "_drc_violations"], v[c "_drc_rules"]; fail = 1
    }
    if ((c "_density_violations") in v)
        printf "REPORT: INV_GF die-density rules not met at cell level: %s (%s)\n",
            v[c "_density_violations"], v[c "_density_rules"]

    if (!((c "_lvs_match") in v)) {
        print "FAIL: INV_GF KLayout LVS did not run"; fail = 1
    } else if (v[c "_lvs_match"] + 0 == 1)
        printf "PASS: INV_GF LVS matches %s\n", v[c "_lvs_netlist"]
    else {
        printf "FAIL: INV_GF LVS %s against %s\n", v[c "_lvs"],
            v[c "_lvs_netlist"]; fail = 1
    }

    exit fail
}
