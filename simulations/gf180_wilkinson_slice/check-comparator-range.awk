BEGIN { FS = "," }
NR == 1 { next }

{
    rows++
    if (rows > 1 && $5 <= previous)
        failed = 1
    previous = $5
}

END {
    if (rows != 3 || failed)
        exit 1
    print "PASS: PMOS comparator range is measurable and monotonic"
}
