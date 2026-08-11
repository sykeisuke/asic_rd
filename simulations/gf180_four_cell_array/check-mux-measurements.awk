/mux0_value/ { value0 = $3 }
/mux1_value/ { value1 = $3 }
/mux2_value/ { value2 = $3 }
/mux3_value/ { value3 = $3 }
/mux0_error/ { error0 = $3 }
/mux1_error/ { error1 = $3 }
/mux2_error/ { error2 = $3 }
/mux3_error/ { error3 = $3 }
/hold0_disturb/ { disturb0 = $3 }
/hold1_disturb/ { disturb1 = $3 }
/hold2_disturb/ { disturb2 = $3 }
/hold3_disturb/ { disturb3 = $3 }

END {
    failed = 0
    if (error0 >= 30e-3 || error1 >= 30e-3 ||
        error2 >= 30e-3 || error3 >= 30e-3) {
        print "FAIL: one or more mux errors >= 30 mV"
        failed = 1
    }
    if (disturb0 >= 35e-3 || disturb1 >= 35e-3 ||
        disturb2 >= 35e-3 || disturb3 >= 35e-3) {
        print "FAIL: one or more hold disturbances >= 35 mV"
        failed = 1
    }
    if (!(value0 < value1 && value1 < value2 && value2 < value3)) {
        print "FAIL: mux output order is incorrect"
        failed = 1
    }
    if (!failed) print "PASS: sequential mux readout meets provisional limits"
    exit failed
}
