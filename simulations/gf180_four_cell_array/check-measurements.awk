/hold0_value/ { value0 = $3 }
/hold1_value/ { value1 = $3 }
/hold2_value/ { value2 = $3 }
/hold3_value/ { value3 = $3 }
/hold0_error/ { error0 = $3 }
/hold1_error/ { error1 = $3 }
/hold2_error/ { error2 = $3 }
/hold3_error/ { error3 = $3 }

END {
    failed = 0
    if (error0 >= 10e-3 || error1 >= 10e-3 ||
        error2 >= 10e-3 || error3 >= 10e-3) {
        print "FAIL: one or more acquisition errors >= 10 mV"
        failed = 1
    }
    if (!(value0 < value1 && value1 < value2 && value2 < value3)) {
        print "FAIL: stored cell order is incorrect"
        failed = 1
    }
    if (!failed) print "PASS: four cells captured distinct ordered samples"
    exit failed
}
