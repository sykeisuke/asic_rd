# OpenROAD's tagged messages from the log of the step a flow stopped
# in, as REPORT lines: every [ERROR XXX-nnnn], [WARNING XXX-nnnn] once
# per code (with its count), and a crash signal if there is one. This is
# what a failed step's log is read for; the log itself stays unread.
#
#   awk -f step-errors.awk <step-dir>/<tool>.log

{ gsub(/\033\[[0-9;]*m/, ""); last3 = last2; last2 = last1; last1 = substr($0, 1, 200) }

#- the last progress message a tool printed: where it was when it died
/\[INFO [A-Z]+-[0-9]+\]|^\[INFO\]/ { lastinfo = substr($0, 1, 200) }

match($0, /\[(ERROR|WARNING) [A-Z]+-[0-9]+\]/) {
    code = substr($0, RSTART + 1, RLENGTH - 2)
    count[code]++
    if (!(code in first)) { first[code] = substr($0, 1, 300); order[++n] = code }
    next
}

#- a failing Tcl script: untagged "Error: <file>, <line> <message>"
/^Error: |invalid command name|while executing|can't read|expected (integer|boolean|floating)|wrong # args|Invalid method/ && !tclerr {
    tclerr = substr($0, 1, 300)
}

#- an assertion names its reason on the line before the signal
/[Aa]ssert|what\(\):/ && !why { why = substr($0, 1, 300) }

/Signal [0-9]+ received|Segmentation fault|Aborted|std::bad_alloc|terminate called/ && !crash {
    crash = substr($0, 1, 300)
}

END {
    #- errors first; warnings after, at most 15 codes
    for (i = 1; i <= n; i++)
        if (order[i] ~ /^ERROR/) print "REPORT: step: " first[order[i]] " (x" count[order[i]] ")"
    shown = 0
    for (i = 1; i <= n && shown < 15; i++)
        if (order[i] ~ /^WARNING/) { print "REPORT: step: " first[order[i]] " (x" count[order[i]] ")"; shown++ }
    if (tclerr != "") print "REPORT: step script error: " tclerr
    if (why != "") print "REPORT: step assertion: " why
    if (crash != "") {
        print "REPORT: step crash: " crash
        print "REPORT: step last progress before crash: " lastinfo
    }
    #- when nothing above names the failure, where the step stopped
    if (tclerr == "" && why == "" && crash == "")
        print "REPORT: step ended: " last3 " | " last2 " | " last1
}
