/time0/ { time0 = int($3 * 1e12 + 0.5) }
/time1/ { time1 = int($3 * 1e12 + 0.5) }
/time2/ { time2 = int($3 * 1e12 + 0.5) }
/time3/ { time3 = int($3 * 1e12 + 0.5) }
/code0/ { code0 = int($3 + 0.5) }
/code1/ { code1 = int($3 + 0.5) }
/code2/ { code2 = int($3 + 0.5) }
/code3/ { code3 = int($3 + 0.5) }

END {
    if (time0 <= 0 || time1 <= 0 || time2 <= 0 || time3 <= 0 ||
        code0 < 0 || code0 > 63 || code1 < 0 || code1 > 63 ||
        code2 < 0 || code2 > 63 || code3 < 0 || code3 > 63)
        exit 1

    print "localparam integer ANALOG_TIME0_PS = " time0 ";"
    print "localparam integer ANALOG_TIME1_PS = " time1 ";"
    print "localparam integer ANALOG_TIME2_PS = " time2 ";"
    print "localparam integer ANALOG_TIME3_PS = " time3 ";"
    print "localparam [5:0] ANALOG_CODE0 = 6'd" code0 ";"
    print "localparam [5:0] ANALOG_CODE1 = 6'd" code1 ";"
    print "localparam [5:0] ANALOG_CODE2 = 6'd" code2 ";"
    print "localparam [5:0] ANALOG_CODE3 = 6'd" code3 ";"
}
