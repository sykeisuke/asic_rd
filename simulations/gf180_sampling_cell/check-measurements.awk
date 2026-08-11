/acquisition_error/ { acquisition = $3 }
/clock_feedthrough/ { feedthrough = $3 }
/hold_droop/ { droop = $3 }

END {
    failed = 0
    if (acquisition >= 20e-3) {
        print "FAIL: acquisition error >= 20 mV"
        failed = 1
    }
    if (feedthrough >= 30e-3) {
        print "FAIL: clock feedthrough >= 30 mV"
        failed = 1
    }
    if (droop >= 1e-3) {
        print "FAIL: hold droop >= 1 mV"
        failed = 1
    }
    if (!failed) print "PASS: provisional baseline limits"
    exit failed
}
