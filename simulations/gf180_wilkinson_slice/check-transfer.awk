BEGIN {
    FS = ","
}

NR == 1 { next }

{
    rows++
    input = $1 + 0
    acquisition = $3 + 0
    code = $5 + 0
    error = $7 + 0

    if (rows > 1 && code <= previous_code) {
        printf "FAIL: non-increasing code at input %.3f V\n", input
        failed = 1
    }
    if (acquisition >= 10e-3) {
        printf "FAIL: acquisition error >= 10 mV at input %.3f V\n", input
        failed = 1
    }
    if (error < -8 || error > 8) {
        printf "FAIL: code error exceeds eight counts at input %.3f V\n", input
        failed = 1
    }
    previous_code = code
}

END {
    if (rows != 8) {
        printf "FAIL: expected 8 transfer points, got %d\n", rows
        failed = 1
    }
    if (!failed)
        print "PASS: 8-point coarse transfer is monotonic and measurable"
    exit failed
}
