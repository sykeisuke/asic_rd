/conversion_time/ {
    conversion_ps = int($3 * 1e12 + 0.5)
}
/output_code/ {
    expected_code = int($3 + 0.5)
}

END {
    if (conversion_ps <= 0 || expected_code < 0 || expected_code > 63)
        exit 1

    print "localparam integer ANALOG_CONVERSION_PS = " conversion_ps ";"
    print "localparam [5:0] ANALOG_EXPECTED_CODE = 6'd" expected_code ";"
}
