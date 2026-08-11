/held_voltage/ { held = $3 }
/acquisition_error/ { acquisition = $3 }
/conversion_time/ { conversion = $3 }
/output_code/ { code = int($3 + 0.5) }
/expected_code/ { expected = int($3 + 0.5) }
/code_error/ { error = int($3) }

END {
    if (conversion <= 0 || code < 0 || code > 63)
        exit 1
    printf "%.3f,%.9g,%.9g,%.9g,%d,%d,%d\n", input, held,
           acquisition, conversion, code, expected, error
}
