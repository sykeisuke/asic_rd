# Acceptance for the chip flow (chip_integration/scripts/run.sh).
# Reads build.sh's `name = value` lines; prints one PASS/FAIL line per
# criterion (REPORT for what is recorded, not judged) and exits non-zero
# on any FAIL.
#
#   awk -v stage=all -f scripts/check-chip.awk work/chip-integration-all.txt
#
# Every stage: inputs/ matches inputs/MANIFEST.sha256.
#
# Macro stage (step 3, scripts/macros.py + macro_check.py): every pin of
# the analog pin contract was found in the analog GDS, the analog GDS is
# clean under the PDK's gf180mcu.drc (density apart), its PR boundary is
# readable by LibreLane's Magic.StreamOut, and the three liberty timing
# models of the digital macro were written.
#
# Chip stage: LibreLane's final metrics say the routed chip has no
# routing DRC, no disconnected critical pin, zero KLayout DRC and XOR
# differences, no antenna or density error after fill, and the drawn
# analog pad wires and supply straps all went in. LVS and setup/hold are
# REPORTed with their counts (goals today, not gates: the analog macro
# is a placeholder black box and the sampling sequencer does not exist).
# A gated figure that is missing is a FAIL: an absent number is not a
# clean one.

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

function need_like(re, label,    k, found) {
    for (k in v) if (k ~ re) { found = k; break }
    if (found == "") {
        printf "FAIL: %s: no metric matching %s\n", label, re
        bad = 1
    } else need(found, 0, label)
}

function report(name, label) {
    printf "REPORT: %s: %s = %s\n", label, name, (name in v) ? v[name] : "not reported"
}

END {
    if (stage == "") stage = "all"
    need("inputs_manifest_ok", 1, "inputs/ equal to inputs/MANIFEST.sha256")
    if (stage == "macros" || stage == "all") {
        if (!("wsa_analog_top_pins_found" in v) ||
            v["wsa_analog_top_pins_found"] + 0 != v["wsa_analog_top_pins_contract"] + 0 ||
            v["wsa_analog_top_pins_found"] + 0 == 0) {
            printf "FAIL: analog GDS -> LEF: pins found %s of contract %s\n",
                v["wsa_analog_top_pins_found"], v["wsa_analog_top_pins_contract"]; bad = 1
        } else printf "PASS: analog GDS -> LEF: %s of %s contract pins found in the GDS\n",
                v["wsa_analog_top_pins_found"], v["wsa_analog_top_pins_contract"]
        need("digital_timing_models", 3, "digital macro liberty models (tt/ff/ss)")
        need("wsa_analog_top_drc_violations", 0, "wsa_analog_top macro KLayout DRC")
        need("wsa_analog_top_magic_bbox_fields", 4, "wsa_analog_top PR boundary readable by Magic.StreamOut")
        report("wsa_analog_top_density_violations", "macro density rules (die-level, fill resolves)")
    }
    if (stage == "chip" || stage == "all" || stage == "collect") {
        if (stage != "collect") need("librelane_exit", 0, "LibreLane Chip flow")
        if ("flow_error_lines" in v)
            need("flow_error_lines", 0, "LibreLane deferred errors")
        if (!("chip_gds_bytes" in v) || v["chip_gds_bytes"] + 0 <= 0) {
            print "FAIL: chip GDS not written"; bad = 1
        } else print "PASS: chip GDS written (" v["chip_gds_bytes"] " bytes)"
        need("ws_analog_routes", 4, "drawn analog pad wires (VIN, EXT_RAMP, AMON, CMP_OUT)")
        need("ws_supply_straps", 4, "drawn analog macro straps (AVDD, AVSS, DVDD, DVSS)")
        need("route__drc_errors", 0, "detailed routing")
        need("design__critical_disconnected_pin__count", 0, "connectivity")
        need("klayout__drc_error__count", 0, "KLayout gf180mcu.drc, full chip")
        need("design__xor_difference__count", 0, "Magic/KLayout stream-out XOR")
        need_like("^klayout__antenna.*count$", "KLayout antenna")
        need_like("^klayout__density.*count$", "KLayout density after fill")
        report("design__lvs_error__count", "Netgen LVS, full chip (goal)")
        report("design__lvs_unmatched_net__count", "Netgen LVS unmatched nets")
        report("design__lvs_unmatched_device__count", "Netgen LVS unmatched devices")
        report("timing__setup_vio__count", "setup violations, all corners")
        report("timing__hold_vio__count", "hold violations, all corners")
        report("timing__setup__ws", "worst setup slack (ns)")
        report("timing__hold__ws", "worst hold slack (ns)")
        report("ws_avdd_rail_breaks", "AVDD pad-ring rail break cells")
    }
    if (stage == "renders" || stage == "all") {
        need("render_steps_missing", 0, "every flow step has its picture")
        if (!("renders_files" in v) || v["renders_files"] + 0 <= 0) {
            print "FAIL: no renders written"; bad = 1
        } else print "PASS: renders written (" v["renders_files"] " files in renders/)"
    }
    exit bad
}
