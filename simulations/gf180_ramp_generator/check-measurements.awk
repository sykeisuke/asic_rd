/reset_level/ { reset = $3 }
/slope_average/ { slope = $3 }
/slope_mismatch/ { mismatch = $3 }
/avg_power/ { power = $3 }

END {
    failed = 0
    if (reset >= 10e-3) {
        print "FAIL: reset level >= 10 mV"
        failed = 1
    }
    if (slope <= 0.5e6 || slope >= 2.0e6) {
        print "FAIL: ramp slope outside 0.5-2.0 V/us"
        failed = 1
    }
    if (mismatch >= 0.02) {
        print "FAIL: half-range slope mismatch >= 2%"
        failed = 1
    }
    if (power >= 0.1e-3) {
        print "FAIL: average power >= 0.1 mW"
        failed = 1
    }
    if (!failed) print "PASS: provisional ramp-generator limits"
    exit failed
}
