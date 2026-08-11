/acquisition_error/ { acquisition = $3 }
/conversion_time/ { conversion = $3 }
/output_code/ { code = $3 }
/code_error/ { code_error = $3 }
/avg_power/ { power = $3 }

END {
    failed = 0
    if (acquisition >= 10e-3) {
        print "FAIL: acquisition error >= 10 mV"
        failed = 1
    }
    if (conversion <= 0 || conversion >= 3e-6) {
        print "FAIL: conversion time outside 0-3 us"
        failed = 1
    }
    if (code < 0 || code > 63) {
        print "FAIL: output code outside 6-bit range"
        failed = 1
    }
    if (code_error < -1 || code_error > 1) {
        print "FAIL: code error exceeds one count"
        failed = 1
    }
    if (power >= 1e-3) {
        print "FAIL: average analog power >= 1 mW"
        failed = 1
    }
    if (!failed) print "PASS: integrated 6-bit slice baseline"
    exit failed
}
