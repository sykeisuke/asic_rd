# Acceptance for `make top-placement`. Reads build.sh's `name = value`
# lines; prints one PASS/FAIL line per criterion and exits non-zero on
# any FAIL.
#
#   awk -v stage=all -f check-top.awk work/top-placement.txt
#
# Macro stage: each wrapper is clean under the PDK's gf180mcu.drc
# (density apart), and wsa_inv still matches INV's netlist through its
# stubs. wsa_cmp's LVS is REPORTed, not judged: the cell inside it does
# not match its own netlist yet (ADR 0006), so no wrapper can.
#
# Chip stage: LibreLane's final metrics say the routed chip has no
# routing DRC, no disconnected critical pin, no setup or hold violation
# in any corner, zero KLayout DRC, LVS and XOR differences, and no
# antenna or density error after fill. A figure that is missing is a
# FAIL: an absent number is not a clean one.

$2 == "=" { v[$1] = $3 }

function need(name, want, label) {
    if (!(name in v)) {
        printf "FAIL: %s: %s not reported\n", label, name
        bad = 1
    } else if (v[name] + 0 != want) {
        printf "FAIL: %s: %s = %s (want %s)\n", label, name, v[name], want
        bad = 1
    } else {
        printf "PASS: %s: %s = %s\n", label, name, v[name]
    }
}

# the first metric whose name matches `re`, judged zero
function need_like(re, label,    k, found) {
    for (k in v) if (k ~ re) { found = k; break }
    if (found == "") {
        printf "FAIL: %s: no metric matching %s\n", label, re
        bad = 1
    } else need(found, 0, label)
}

END {
    if (stage == "") stage = "all"
    if (stage == "macros" || stage == "all") {
        need("wsa_cmp_drc_violations", 0, "wsa_cmp macro KLayout DRC")
        need("wsa_inv_drc_violations", 0, "wsa_inv macro KLayout DRC")
        need("wsa_inv_lvs_match", 1, "wsa_inv macro KLayout LVS vs INV.spice")
        need("wsa_inv_gf_drc_violations", 0, "wsa_inv_gf macro KLayout DRC")
        need("wsa_inv_gf_lvs_match", 1, "wsa_inv_gf macro KLayout LVS vs INV_GF.spice")
        need("wsa_cmp_magic_bbox_fields", 4, "wsa_cmp PR boundary readable by Magic.StreamOut")
        need("wsa_inv_magic_bbox_fields", 4, "wsa_inv PR boundary readable by Magic.StreamOut")
        need("wsa_inv_gf_magic_bbox_fields", 4, "wsa_inv_gf PR boundary readable by Magic.StreamOut")
        printf "REPORT: macro DRC rules: wsa_cmp %s, wsa_inv %s, wsa_inv_gf %s\n", \
            v["wsa_cmp_drc_rules"], v["wsa_inv_drc_rules"], v["wsa_inv_gf_drc_rules"]
        printf "REPORT: wsa_cmp macro LVS match = %s (the CMP cell itself is LVS-open, ADR 0006)\n", \
            ("wsa_cmp_lvs_match" in v) ? v["wsa_cmp_lvs_match"] : "not run"
        printf "REPORT: macro density rules (die-level, fill resolves): wsa_cmp %s, wsa_inv %s, wsa_inv_gf %s\n", \
            v["wsa_cmp_density_violations"], v["wsa_inv_density_violations"], v["wsa_inv_gf_density_violations"]
    }
    if (stage == "chip" || stage == "all" || stage == "collect") {
        #- collect summarises a run it did not start: no exit status
        if (stage != "collect") need("librelane_exit", 0, "LibreLane Chip flow")
        if ("flow_error_lines" in v)
            need("flow_error_lines", 0, "LibreLane deferred errors")
        if (!("chip_gds_bytes" in v) || v["chip_gds_bytes"] + 0 <= 0) {
            print "FAIL: chip GDS not written"; bad = 1
        } else print "PASS: chip GDS written (" v["chip_gds_bytes"] " bytes)"
        need("route__drc_errors", 0, "detailed routing")
        need("design__critical_disconnected_pin__count", 0, "connectivity")
        need("timing__setup_vio__count", 0, "setup, all corners")
        need("timing__hold_vio__count", 0, "hold, all corners")
        need("klayout__drc_error__count", 0, "KLayout gf180mcu.drc, full chip")
        need("design__lvs_error__count", 0, "Netgen LVS, full chip")
        need("design__xor_difference__count", 0, "Magic/KLayout stream-out XOR")
        need_like("^klayout__antenna.*count$", "KLayout antenna")
        need_like("^klayout__density.*count$", "KLayout density after fill")
    }
    exit bad
}
