# Acceptance on data/floorplan.txt (floorplan.py's `name = value` lines).
#
#   awk -f check-floorplan.awk data/floorplan.txt
#
# Gates:
#   - the ring is the user's 1x0p5 drawing: 72 pads, 44 bidir, 6 inputs,
#     3 bi_a + 1 asig_5p0 analog, 14 I/O power, 2 core power, the AVDD pair;
#   - floorplan.py found the macro, the digital region and the CDM cells
#     inside the core with no overlap (its PASS line);
#   - the four analog pad wires and the two supply straps: no crossing;
#   - the macro is not padded out: active blocks fill >= 45 % of it
#     (assumed bound; ring, bus channel and AVDD decap are the rest).
BEGIN { fail = 0; minfill = 45 }
$2 == "=" { v[$1] = $3 + 0; next }
/^PASS: macro, digital region/ { inside = 1 }
END {
    want["pads_total"] = 72; want["pads_bidir"] = 44; want["pads_input"] = 6; want["pads_bi_a"] = 3
    want["pads_asig_5p0"] = 1; want["pads_iopwr"] = 14; want["pads_corepwr"] = 2
    want["pads_avdd"] = 1; want["pads_avss"] = 1
    msg = ""
    for (k in want) if (v[k] != want[k]) { msg = msg sprintf(" %s=%s (want %d)", k, v[k], want[k]); fail = 1 }
    if (!inside) { msg = msg " blocks outside the core or overlapping"; fail = 1 }
    if (!("route_crossings" in v) || v["route_crossings"] != 0) { msg = msg " analog/supply routes cross"; fail = 1 }
    for (w in v) if (w ~ /^wire_/) nw++
    if (nw != 4) { msg = msg sprintf(" %d analog pad wires (want 4)", nw); fail = 1 }
    if (v["digital_region_w_um"] <= 0) { msg = msg " no digital outline"; fail = 1 }
    if (v["macro_block_fill_pct"] < minfill) {
        msg = msg sprintf(" macro fill %.1f %% < %d %%", v["macro_block_fill_pct"], minfill); fail = 1 }
    if (fail) printf "FAIL: chip floorplan:%s\n", msg
    else printf "PASS: chip floorplan: 72-pad 1x0p5 ring as drawn, AVDD pair + 4 analog pads assigned, macro %.1f x %.1f um (fill %.1f %%) and digital %.2f x %.2f um inside the core, 0 route crossings\n", \
        v["macro_w_um"], v["macro_h_um"], v["macro_block_fill_pct"], v["digital_region_w_um"], v["digital_region_h_um"]
    exit fail
}
