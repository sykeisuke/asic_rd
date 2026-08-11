/crossing_delay/ { delay = $3 }
/output_low/ { low = $3 }
/output_high/ { high = $3 }
/avg_power/ { power = $3 }

END {
    failed = 0
    if (delay >= 40e-9) {
        print "FAIL: crossing delay >= 40 ns"
        failed = 1
    }
    if (low >= 0.3) {
        print "FAIL: output low >= 0.3 V"
        failed = 1
    }
    if (high <= 3.0) {
        print "FAIL: output high <= 3.0 V"
        failed = 1
    }
    if (power >= 1e-3) {
        print "FAIL: average power >= 1 mW"
        failed = 1
    }
    if (!failed) print "PASS: provisional 6-bit comparator limits"
    exit failed
}
