# PASS/FAIL over floorplan.py's `name = value` lines.
#
#   awk -f check-floorplan.awk work/floorplan.txt
#
# Asserted: all four cells built, all DRC clean on the PDK deck, the MIM over
# the transistors (inside the PMOS block, no silicon), the MOM beside them,
# the switch following the capacitor, and the two area ratios reported.
BEGIN { fails = 0 }
/^[a-z_0-9]+ = / { v[$1] = $3 }
function chk(ok, msg) {
    if (ok) printf "PASS: %s\n", msg; else { printf "FAIL: %s\n", msg; fails++ }
}
END {
    chk(v["cells_built"] == 4, "four unit cells built (cells_built = " v["cells_built"] ")")
    n = split("uc_mim uc_mom uc_mim_125 uc_mom_125", cells, " ")
    for (i = 1; i <= n; i++) {
        c = cells[i]
        chk(v[c "_drc_violations"] == 0, c " DRC clean on gf180mcu.drc (" v[c "_drc_violations"] " violations)")
    }
    chk(v["uc_mim_cap_over_devices"] == 1 && v["uc_mim_125_cap_over_devices"] == 1, "MIM cells: capacitor over the transistors, M4/FuseTop/M5 only")
    chk(v["uc_mom_cap_over_devices"] == 0 && v["uc_mom_125_cap_over_devices"] == 0, "MOM cells: capacitor beside the transistors, M1-M4")
    chk(v["uc_mim_cap_area_um2"] >= 25.0 && v["uc_mim_cap_area_um2"] < 25.01, "UC_MIM at the MIMTM.8a floor: " v["uc_mim_cap_area_um2"] " um2 FuseTop, " v["uc_mim_cap_value_ff"] " fF")
    chk(v["uc_mim_125_cap_value_ff"] >= 125 && v["uc_mom_125_cap_value_ff"] >= 124.5, "125 fF cells at value: MIM " v["uc_mim_125_cap_value_ff"] " fF, 8 x MOM " v["uc_mom_125_cap_value_ff"] " fF")
    chk(v["uc_mim_mim_inside_pmos_block"] == 1 && v["uc_mim_125_mim_inside_pmos_block"] == 1, "both MIMs lie inside the PMOS block's outline: no silicon of their own")
    chk(v["uc_mim_comparator"] == "mim55" && v["uc_mom_comparator"] == "mom16" && v["uc_mim_125_comparator"] == "mim125", "each cell carries the comparator sized into its own capacitor (" v["uc_mim_comparator"] ", " v["uc_mom_comparator"] ", " v["uc_mim_125_comparator"] ")")
    chk(v["uc_mim_sw_wn_um"] >= v["uc_mom_sw_wn_um"], "switch follows the capacitor: WN " v["uc_mom_sw_wn_um"] " um (MOM) vs " v["uc_mim_sw_wn_um"] " um (MIM) at " v["fs_mhz"] " MHz")
    chk(v["area_ratio_mom_over_mim_min"] != "" && v["area_ratio_mom_over_mim_125"] != "", "area ratios MOM/MIM: " v["area_ratio_mom_over_mim_min"] " at the minimum capacitor, " v["area_ratio_mom_over_mim_125"] " at 125 fF")
    if (fails) { printf "FAIL: unit cell floorplan (%d)\n", fails; exit 1 }
    print "PASS: unit cell floorplan, MIM over vs MOM beside, minimum and 125 fF"
}
