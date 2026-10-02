# LibreLane's own error lines, as REPORT lines for the metrics record,
# so a failed step says why without anyone opening the log.
#
#   awk -f flow-errors.awk work/top-placement.log
#
# Keeps lines LibreLane tags [ERROR] / "ERROR" / "Error:" and the step
# that was running when the flow stopped; at most 25 lines.

# LibreLane's "[E]" message and a failed step's reason run over the
# next lines; keep those too
tail > 0 && n < 25 {
    line = $0
    gsub(/\033\[[0-9;]*m/, "", line)
    gsub(/^[ \t]+|[ \t]+$/, "", line)
    if (line != "" && !(line in seen)) {
        seen[line] = 1; print "REPORT: librelane:   " substr(line, 1, 300); n++
    }
    tail--
    next
}

/\[E\] / { tail = 8 }

/Running '[^']+'/ {
    match($0, /'[^']+'/)
    step = substr($0, RSTART + 1, RLENGTH - 2)
}

/\[ERROR|\[E\] |Error:|\[Errno|Traceback|non-zero exit|Killed|Segmentation|Aborted/ && n < 25 {
    line = $0
    gsub(/\033\[[0-9;]*m/, "", line)      # colour codes
    gsub(/^[ \t]+|[ \t]+$/, "", line)
    if (length(line) > 300) line = substr(line, 1, 300) "..."
    if (!(line in seen)) { seen[line] = 1; print "REPORT: librelane: " line; n++ }
}

END { if (step != "") print "REPORT: librelane last step started: " step }
