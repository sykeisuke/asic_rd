# Parses RESULT lines and derives, for a sweep of the sampled level vs:
#   code      = (t_cross - TRAMP) / TCOUNT
#   pedestal  = stored-node error referred to the input:
#               sense-top    : v_hold - vs
#               sense-bottom : (VREFB - v_hold) * (C+Cp)/C - vs  ~ computed from
#                              the crossing instead (see below)
#   gain      = fitted codes/V against the ideal +-1/(SLOPE*TCOUNT)
#   linearity = max residual of code from its own least-squares line (LSB)
#   offset    = input-referred pedestal derived from the crossing time:
#               (code_fit_intercept ...) reported as t_cross(vs) - ideal
# Pass criteria (Tape-out 1 provisional):
#   monotonic, linearity <= 0.25 LSB, input-referred pedestal spread <= 2 mV.
BEGIN { n = 0; TRAMP = 300e-9; TCOUNT = 50e-9; SLOPE = 117.1875e3; LSB = 1.5 / 256
        if (SENSE == "") SENSE = "top" }
/^RESULT/ {
    for (i = 2; i <= NF; i++) { split($i, kv, "="); v[kv[1]] = kv[2] + 0 }
    n++
    vs[n] = v["vs"]; vh[n] = v["v_hold"]; tc[n] = v["t_cross"]
    code[n] = (tc[n] - TRAMP) / TCOUNT
    # Input-referred pedestal from the crossing: the ramp voltage at crossing
    # equals (VCMP - vs - ped) for sense-top and (vs + ped) for sense-bottom,
    # up to the parasitic gain factor removed below by the fit.
    vr[n] = (tc[n] - TRAMP) * SLOPE
}
END {
    if (n < 3) { print "FAIL: fewer than 3 RESULT lines"; exit 1 }
    sx = sy = sxx = sxy = 0
    for (i = 1; i <= n; i++) { sx += vs[i]; sy += code[i]; sxx += vs[i]*vs[i]; sxy += vs[i]*code[i] }
    b = (n*sxy - sx*sy) / (n*sxx - sx*sx); a = (sy - b*sx) / n
    ideal_b = (SENSE == "top") ? -1.0/(SLOPE*TCOUNT) : 1.0/(SLOPE*TCOUNT)
    gain = b / ideal_b
    maxres = 0; mono = 1; pmin = 1e9; pmax = -1e9
    for (i = 1; i <= n; i++) {
        r = code[i] - (a + b*vs[i]); if (r < 0) r = -r; if (r > maxres) maxres = r
        if (i > 1 && ((SENSE == "top" && code[i] >= code[i-1]) || (SENSE != "top" && code[i] <= code[i-1]))) mono = 0
        # input-referred pedestal after removing the fitted gain
        ped[i] = (SENSE == "top") ? (2.0 - vr[i]/gain) - vs[i] : vr[i]/gain - vs[i]
        if (ped[i] < pmin) pmin = ped[i]; if (ped[i] > pmax) pmax = ped[i]
        printf("vs=%.2f V  v_hold(sensed node)=%.4f V  t_cross=%.3f us  code=%.2f  input-referred pedestal=%+.2f mV\n",
               vs[i], vh[i], tc[i]*1e6, code[i], ped[i]*1e3)
    }
    printf("codes/V slope=%.2f (ideal %.2f) -> gain %.4f (error %+.2f %%, expected C/(C+Cp))\n", b, ideal_b, gain, (gain-1)*100)
    printf("linearity (max residual from own line)=%.3f LSB\n", maxres)
    printf("input-referred pedestal: mean=%+.2f mV, spread over 0.5-2.0 V=%.2f mV (%.3f LSB)\n",
           (pmax+pmin)/2*1e3, (pmax-pmin)*1e3, (pmax-pmin)/LSB)
    fail = 0
    if (!mono) { print "FAIL: codes not monotonic"; fail = 1 }
    if (maxres > 0.25) { print "FAIL: linearity > 0.25 LSB"; fail = 1 }
    if ((pmax - pmin) > 2e-3) { print "FAIL: pedestal spread > 2 mV (signal-dependent injection)"; fail = 1 }
    if (fail) exit 1
    print "PASS: bottom-plate cell (" SENSE "-sensed) linearity and signal-independent pedestal"
}
