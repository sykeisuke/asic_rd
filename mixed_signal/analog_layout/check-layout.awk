# Acceptance for `make layout`: did cicpy build a cell at all, and is
# its netlist intact?
#
# DRC and LVS are NOT checked here. They are KLayout's and they have
# their own targets: `make drc`, `make lvs`.

/^[a-z_0-9]+ = / { v[$1] = substr($0, index($0, "= ") + 2) }

END {
    fail = 0
    if (v["cells_built"] + 0 < 1) {
        print "FAIL: no cell was built"; exit 1
    }

    for (k in v) {
        if (k !~ /_gds_bytes$/) continue
        c = substr(k, 1, length(k) - length("_gds_bytes"))

        # A route short is a wrong netlist. cicpy reports it before
        # anything is written, so it is the one verdict this step owns.
        if (v[c "_route_shorts"] + 0 == 0)
            printf "PASS: %s routed with no shorts, %s devices\n",
                toupper(c), v[c "_devices"]
        else {
            printf "FAIL: %s has %s route shorts\n", toupper(c),
                v[c "_route_shorts"]; fail = 1
        }

        if (v[k] + 0 > 0)
            printf "PASS: %s GDS written, %s x %s um (%s um^2)\n",
                toupper(c), v[c "_width_um"], v[c "_height_um"],
                v[c "_area_um2"]
        else {
            printf "FAIL: %s wrote no GDS\n", toupper(c); fail = 1
        }

        if (v[c "_render_bytes"] + 0 > 0)
            printf "PASS: %s rendered from its own GDS\n", toupper(c)
        else {
            printf "FAIL: %s produced no render\n", toupper(c); fail = 1
        }
    }
    exit fail
}
