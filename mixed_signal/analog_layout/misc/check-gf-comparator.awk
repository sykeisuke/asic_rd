# Acceptance for `make gf-comparator`: the gdsfactory comparator CMP_LP was
# drawn with its pins, rendered, passes the PDK's KLayout DRC and LVS, the
# LVS control with swapped inp/inn is rejected, and extraction produced a
# drop-in netlist whose every finger maps back onto a reference device.
#
# Density is reported and not judged (see ../check-drc.awk for why).
# Parasitic totals are reported, not judged: no simulation runs here.

/^[a-z_0-9]+ = / { v[$1] = substr($0, index($0, "= ") + 2) }

END {
    fail = 0
    c = "cmp_lp"

    if (v[c "_gds_bytes"] + 0 > 0)
        printf "PASS: CMP_LP drawn with gdsfactory: %s devices, %s x %s um (%s um^2)\n",
            v[c "_devices"], v[c "_width_um"], v[c "_height_um"], v[c "_area_um2"]
    else { print "FAIL: CMP_LP wrote no GDS"; fail = 1 }

    if (v[c "_devices"] + 0 != v[c "_devices_expected"] + 0 || v[c "_devices"] + 0 == 0) {
        printf "FAIL: CMP_LP has %s transistor instances, expected %s\n",
            v[c "_devices"], v[c "_devices_expected"]; fail = 1
    }
    if (v[c "_ref_devices"] + 0 != v[c "_devices_expected"] + 0) {
        printf "FAIL: LVS reference has %s transistors, cmp_lp.spice layout set is %s\n",
            v[c "_ref_devices"], v[c "_devices_expected"]; fail = 1
    }
    if ((c "_ref_dropped") in v)
        printf "REPORT: LVS reference drops %s from cmp_lp.spice (routing-load stand-in)\n",
            v[c "_ref_dropped"]

    if (v[c "_pins"] + 0 == v[c "_pins_expected"] + 0 && v[c "_pins"] + 0 > 0)
        printf "PASS: CMP_LP pins %s; internal nets labelled %s\n",
            v[c "_pin_names"], v[c "_net_labels"]
    else {
        printf "FAIL: CMP_LP has %s of %s pins (%s)\n", v[c "_pins"],
            v[c "_pins_expected"], v[c "_pin_names"]; fail = 1
    }

    if (v[c "_render_bytes"] + 0 > 0)
        print "PASS: CMP_LP rendered from its own GDS"
    else { print "FAIL: CMP_LP produced no render"; fail = 1 }

    if (!((c "_drc_violations") in v)) {
        print "FAIL: CMP_LP KLayout DRC did not run"; fail = 1
    } else if (v[c "_drc_violations"] + 0 == 0)
        print "PASS: CMP_LP KLayout DRC clean (gf180mcu.drc, density apart)"
    else {
        printf "FAIL: CMP_LP has %s KLayout DRC violations: %s\n",
            v[c "_drc_violations"], v[c "_drc_rules"]; fail = 1
    }
    if ((c "_density_violations") in v)
        printf "REPORT: CMP_LP die-density rules not met at cell level: %s (%s)\n",
            v[c "_density_violations"], v[c "_density_rules"]

    if (!((c "_lvs_match") in v)) {
        print "FAIL: CMP_LP KLayout LVS did not run"; fail = 1
    } else if (v[c "_lvs_match"] + 0 == 1)
        printf "PASS: CMP_LP LVS matches %s\n", v[c "_lvs_netlist"]
    else {
        printf "FAIL: CMP_LP LVS %s against %s\n", v[c "_lvs"], v[c "_lvs_netlist"]; fail = 1
    }

    # KLayout's compare pairs top-level nets by topology, so the pin names
    # are checked separately, device by device (extract.py --names)
    if (v[c "_names"] == "match")
        print "PASS: CMP_LP LVS extraction matches the reference net name by net name (pins on the right devices)"
    else {
        printf "FAIL: CMP_LP net names differ from the reference: %s unmatched, short W on %s\n",
            v[c "_names_unmatched_fingers"], v[c "_names_w_short"]; fail = 1
    }
    if (v[c "_ctl_swapped_labels"] + 0 != 2) {
        printf "FAIL: pin control swapped %s labels, expected 2\n",
            v[c "_ctl_swapped_labels"]; fail = 1
    } else if (v[c "_ctl_names"] == "mismatch")
        printf "PASS: name check rejects the control with inp and inn swapped (short W on %s)\n",
            v[c "_ctl_names_w_short"]
    else {
        printf "FAIL: name check passed the control with inp/inn swapped ('%s')\n",
            v[c "_ctl_names"]; fail = 1
    }
    if ((c "_ctl_lvs") in v)
        printf "REPORT: KLayout LVS on the inp/inn-swapped control: %s (topology only; names not compared)\n",
            v[c "_ctl_lvs"]

    if (v[c "_pex_netlist"] + 0 != 1) {
        print "FAIL: CMP_LP extraction wrote no netlist"; fail = 1
    } else {
        ok = 1
        if (v[c "_pex_lvs"] != "match") {
            printf "FAIL: kpex's own LVS came back '%s'\n", v[c "_pex_lvs"]; ok = 0
        }
        if (v[c "_pex_devices"] + 0 != v[c "_devices_expected"] + 0) {
            printf "FAIL: extracted netlist has %s devices after finger merge, expected %s\n",
                v[c "_pex_devices"], v[c "_devices_expected"]; ok = 0
        }
        if (v[c "_pex_w_max_rel_dev"] + 0 > 1e-9) {
            printf "FAIL: extracted total W differs from cmp_lp.spice by %s (relative)\n",
                v[c "_pex_w_max_rel_dev"]; ok = 0
        }
        if (v[c "_pex_unnamed_nets"] + 0 != 0 || v[c "_pex_stray_nets"] != "none") {
            printf "FAIL: extracted netlist has %s unnamed and stray nets '%s'\n",
                v[c "_pex_unnamed_nets"], v[c "_pex_stray_nets"]; ok = 0
        }
        if (ok)
            printf "PASS: extracted drop-in subckt %s: %s fingers -> %s devices, W exact, %s capacitances, all nets named\n",
                v[c "_pex_subckt"], v[c "_pex_fingers"], v[c "_pex_devices"], v[c "_pex_caps"]
        else
            fail = 1
        printf "REPORT: extracted C total (fF): outa %s, left %s, tail %s, outb %s, rep %s, bst %s, inp %s, inn %s, dout %s; inp-inn %s\n",
            v[c "_pex_c_outa_ff"], v[c "_pex_c_left_ff"], v[c "_pex_c_tail_ff"],
            v[c "_pex_c_outb_ff"], v[c "_pex_c_rep_ff"], v[c "_pex_c_bst_ff"],
            v[c "_pex_c_inp_ff"], v[c "_pex_c_inn_ff"], v[c "_pex_c_dout_ff"],
            v[c "_pex_c_inp_inn_ff"]
        printf "REPORT: n-well junctions, typical zero bias (fF): clamp well on outa %s, main well on vdd %s\n",
            v[c "_pex_cwell_outa_ff"], v[c "_pex_cwell_vdd_ff"]
    }

    exit fail
}
