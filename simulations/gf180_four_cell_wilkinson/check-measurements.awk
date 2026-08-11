/time0/ { time0 = $3 }
/time1/ { time1 = $3 }
/time2/ { time2 = $3 }
/time3/ { time3 = $3 }
/code0/ { code0 = int($3) }
/code1/ { code1 = int($3) }
/code2/ { code2 = int($3) }
/code3/ { code3 = int($3) }
/avg_power/ { power = $3 }

function abs(value) { return value < 0 ? -value : value }

END {
    failed = 0
    if (!(time0 > 0 && time1 > 0 && time2 > 0 && time3 > 0)) {
        print "FAIL: one or more comparator crossings are missing"
        failed = 1
    }
    if (!(code0 < code1 && code1 < code2 && code2 < code3)) {
        print "FAIL: four-cell output codes are not monotonic"
        failed = 1
    }
    if (abs(code0 - 13) > 3 || abs(code1 - 20) > 3 ||
        abs(code2 - 28) > 3 || abs(code3 - 36) > 3) {
        print "FAIL: one or more code errors exceed three counts"
        failed = 1
    }
    if (power >= 200e-6) {
        print "FAIL: average analog-core power >= 200 uW"
        failed = 1
    }
    if (!failed)
        print "PASS: four cells complete sequential Wilkinson conversion"
    exit failed
}
