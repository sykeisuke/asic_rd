# Convert run-script console output into a compact metrics record.
#
# Inputs: one or more text files containing ngspice ".measure" echoes
# ("name = value"), checker verdict lines ("PASS: ..." / "FAIL: ..."),
# checker findings that are reported but not judged ("REPORT: ..."), and
# run-script artifact lines ("Measurements: /path/to/file").
#
# REPORT lines exist because some findings must be seen and must not
# decide a verdict -- a density rule that no single cell can satisfy, or
# a measurement that says an extraction engine is untrustworthy in one
# corner of a sweep. They are kept out of "checks" so that nothing reads
# them as a verdict, and out of the log so that nothing has to read the
# log to find them.
#
# Output: metrics.json on stdout. Nothing else in the repository should
# need to read the raw logs.

function jstr(s) {
    gsub(/\\/, "\\\\", s)
    gsub(/"/, "\\\"", s)
    gsub(/\t/, " ", s)
    return "\"" s "\""
}

function isnum(s) {
    return s ~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/
}

BEGIN { nm = 0; nc = 0; nr = 0; na = 0; failed = 0 }

# ngspice .measure echo and librelane name/value pairs.
$2 == "=" && $1 ~ /^[A-Za-z][A-Za-z0-9_]*$/ && isnum($3) {
    if (!($1 in seen)) { order[++nm] = $1; seen[$1] = 1 }
    v = $3
    # JSON forbids a leading "+", which isnum() accepts; strip it so the
    # emitted record stays parseable.
    sub(/^\+/, "", v)
    value[$1] = v
    next
}

# Checker verdicts printed by the awk acceptance scripts and testbenches.
/^(PASS|FAIL)[:]/ {
    checks[++nc] = $0
    if ($1 == "FAIL:") failed = 1
    next
}

# Findings a checker records without judging.
/^REPORT[:]/ {
    reports[++nr] = $0
    next
}

# Artifact paths printed by scripts/run-*.sh on completion.
/^[A-Za-z][A-Za-z0-9 \/-]*: \// {
    idx = index($0, ": ")
    path = substr($0, idx + 2)
    if (!(path in seenart)) { seenart[path] = 1; artifacts[++na] = path }
    next
}

END {
    ok = (status == 0 && failed == 0) ? "true" : "false"
    printf "{\n"
    printf "  \"target\": %s,\n", jstr(target)
    printf "  \"timestamp\": %s,\n", jstr(stamp)
    printf "  \"corner\": %s,\n", jstr(corner)
    printf "  \"exit_status\": %d,\n", status
    printf "  \"pass\": %s,\n", ok
    printf "  \"metrics\": {"
    for (i = 1; i <= nm; i++)
        printf "%s\n    %s: %s", (i > 1 ? "," : ""), jstr(order[i]), value[order[i]]
    printf "%s},\n", (nm ? "\n  " : "")
    printf "  \"checks\": ["
    for (i = 1; i <= nc; i++)
        printf "%s\n    %s", (i > 1 ? "," : ""), jstr(checks[i])
    printf "%s],\n", (nc ? "\n  " : "")
    printf "  \"reports\": ["
    for (i = 1; i <= nr; i++)
        printf "%s\n    %s", (i > 1 ? "," : ""), jstr(reports[i])
    printf "%s],\n", (nr ? "\n  " : "")
    printf "  \"artifacts\": ["
    for (i = 1; i <= na; i++)
        printf "%s\n    %s", (i > 1 ? "," : ""), jstr(artifacts[i])
    printf "%s]\n", (na ? "\n  " : "")
    printf "}\n"
}
