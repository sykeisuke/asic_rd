# check-schematic.awk -- the xschem drawing of vrlo_ref must netlist back to its
# subcircuit in vrlo_ref.spice (copied from ../midrail_ref_bkp/midrail_ref_v2/check-schematic.awk;
# the node set is now the -v nodes="..." argument, given per subcircuit by schematic.sh)
# (a copy of misc/true_bps_adc/check-schematic.awk; the frozen node set is the subcircuit internals).
#
# Netlist mode (default):
#
#   awk -v ref=true_bps_adc.spice -f check-schematic.awk \
#       true_bps_adc.spice work/true_bps_adc_sch.spice
#
# File 1 is the controlled SPICE source, file 2 is what xschem produced from
# true_bps_adc.sch. A drawing that merely looks like the deck is not
# evidence, so every instance is compared on its name, its terminals in
# order, and its value, model and parameters:
#   * V / I sources     terminals, value (DC, PWL, PULSE)
#   * R / C             terminals, value, m
#   * S switches        both contact and both control terminals, model
#   * X subcircuits     every terminal in order, the model (subcircuit
#                       name), and the parameter set: the MIM XCS, the bias
#                       MOSFETs XREFN / XREFP, the comparator XDUT
# and every dot card (.include, .lib, .param, .tran, .measure, ...) plus
# every line of the .control block must be present on both sides, so the
# xschem netlist is the complete runnable deck and not a circuit fragment.
#
# Normalised, because xschem and a hand-written deck spell the same thing
# differently:
#   * xschem writes expressions in 'single quotes' where the deck writes
#     {braces}; quotes and braces are stripped on both sides.
#   * xschem omits m=1; a missing m reads as 1 on both sides.
#   * xschem folds long lines with a leading "+"; continuations are joined.
#   * engineering suffixes are canonicalised, so 5u == 5000n == 5e-06.
#   * expression punctuation is spaced out, so "a>b?c:d" == "a > b ? c : d".
#   * subcircuit parameters are compared as a set (key order is free), with
#     keys case-folded; whitespace inside a quoted or braced value is closed
#     up first so a value such as 'int((nf+1)/2) * W/nf' stays one token.
#   * the SPICE title line and comments are not circuit.
#
# Node names are additionally checked against the frozen set in CONTRACT.md,
# because an unlabelled wire in xschem silently becomes net1 and a netlist
# that agrees with itself on the wrong name is not evidence either.
#
# Simulation mode:
#
#   awk -v mode=sim -v level=a0 -f check-schematic.awk \
#       work/lv_a0/measures.txt work/lv_sch/measures.txt
#
# File 1 is the deck's measure echoes for one level, file 2 the measure
# echoes of the xschem netlist simulated at the same level.spice. code must
# be equal, t_dout and t_top within TOL_PS (1 ps); every measure of the deck
# must be present and numeric in the schematic's run. The echoes carry six
# significant digits (10 ps on t_dout itself), so the time bounds are taken
# through err_lsb and cmp_delay as well and always include one last-digit
# unit: a PASS never rests on a difference the echo cannot resolve.
#
# Prints one PASS:/FAIL: line per check (plus REPORT: lines), exits non-zero
# on failure.

BEGIN {
    CONTRACT_NODES = (nodes != "") ? nodes : "out vin ib vdd vss pb a b p n"
    if (ref == "") ref = "the deck"
    if (level == "") level = "a0"
    TOL_PS = 1
}

# ---------------------------------------------------------------- helpers

function isnum(s) {
    return s ~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/
}

# canonicalise one SPICE number token: 5u == 5000n == 5e-06, 0.720 == 0.72
function nval(t,    mant, suf, mul) {
    if (t !~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?[a-z]*$/)
        return t
    mant = t
    sub(/[a-z]+$/, "", mant)
    if (mant == "" || mant ~ /[eE][-+]?$/) return t
    suf = substr(t, length(mant) + 1)
    mul = 1
    if      (suf == "t")              mul = 1e12
    else if (suf == "g")              mul = 1e9
    else if (suf == "meg" || suf == "x") mul = 1e6
    else if (suf == "k")              mul = 1e3
    else if (suf == "mil")            mul = 25.4e-6
    else if (suf == "m")              mul = 1e-3
    else if (suf == "u")              mul = 1e-6
    else if (suf == "n")              mul = 1e-9
    else if (suf == "p")              mul = 1e-12
    else if (suf == "f")              mul = 1e-15
    else if (suf != "")               return t     # not a suffix we know
    return sprintf("%.12g", (mant + 0) * mul)
}

# normalise a value / model / expression string for comparison
function norm(s,    n, a, i, out) {
    gsub(/[{}'"]/, " ", s)
    s = tolower(s)
    gsub(/[()?:,]/, " & ", s)
    gsub(/[<>]/, " & ", s)
    gsub(/=/, " = ", s)
    n = split(s, a, /[ \t]+/)
    out = ""
    for (i = 1; i <= n; i++) {
        if (a[i] == "") continue
        out = out (out == "" ? "" : " ") nval(a[i])
    }
    return out
}

# close up whitespace inside '...' and {...} so a quoted value is one token
function squeeze(s,    out, i, c, q, depth) {
    out = ""; q = 0; depth = 0
    for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c == "'") q = !q
        else if (c == "{") depth++
        else if (c == "}" && depth > 0) depth--
        if ((c == " " || c == "\t") && (q || depth > 0)) continue
        out = out c
    }
    return out
}

# first "key=value" token of a joined device line, or "" when absent
function param(text, key,    n, a, i, t) {
    n = split(text, a, /[ \t]+/)
    for (i = 1; i <= n; i++) {
        t = a[i]
        if (tolower(substr(t, 1, length(key) + 1)) == tolower(key) "=")
            return norm(substr(t, length(key) + 2))
    }
    return ""
}

function defaulted(text, key, fallback,    v) {
    v = param(text, key)
    return (v == "") ? fallback : v
}

# tokens start..end of a device line, dropping instance-parameter tokens
function tail(text, start,    n, a, i, out) {
    n = split(text, a, /[ \t]+/)
    out = ""
    for (i = start; i <= n; i++) {
        if (tolower(a[i]) ~ /^(m|savecurrent|temp|dtemp|scale|tc1|tc2)=/) continue
        out = out (out == "" ? "" : " ") a[i]
    }
    return out
}

function remember(n1, n2, n3, n4) {
    if (n1 != "") node[side, tolower(n1)] = 1
    if (n2 != "") node[side, tolower(n2)] = 1
    if (n3 != "") node[side, tolower(n3)] = 1
    if (n4 != "") node[side, tolower(n4)] = 1
}

# insertion sort of k[1..n] (a handful of parameters)
function sortk(k, n,    i, j, t) {
    for (i = 2; i <= n; i++) {
        t = k[i]
        for (j = i - 1; j >= 1 && k[j] > t; j--) k[j + 1] = k[j]
        k[j + 1] = t
    }
}

# an X line: terminals in order, the model, the parameter set (m defaults 1)
function subckt_key(text,    n, a, i, first, nodes, model, np, pk, eq, key, hasm, out) {
    n = split(squeeze(text), a, /[ \t]+/)
    first = n + 1
    for (i = 2; i <= n; i++) if (index(a[i], "=") > 1) { first = i; break }
    model = a[first - 1]
    nodes = ""
    for (i = 2; i <= first - 2; i++) {
        nodes = nodes (nodes == "" ? "" : "/") tolower(a[i])
        node[side, tolower(a[i])] = 1
    }
    np = 0; hasm = 0
    for (i = first; i <= n; i++) {
        eq = index(a[i], "=")
        if (eq <= 1) { pk[++np] = "?" norm(a[i]); continue }   # stray token
        key = tolower(substr(a[i], 1, eq - 1))
        if (key == "m") hasm = 1
        pk[++np] = key "=" norm(substr(a[i], eq + 1))
    }
    if (!hasm) pk[++np] = "m=1"
    sortk(pk, np)
    out = ""
    for (i = 1; i <= np; i++) out = out (out == "" ? "" : " ") pk[i]
    return "subckt " nodes " model=[" tolower(model) "] params=[" out "]"
}

# a dot card or a .control line, compared as a multiset on both sides
function card(text,    c) {
    c = norm(squeeze(text))
    ncard[side]++
    cards[side, c]++
    if (!((c) in cardtext)) { cardtext[c] = text; cardorder[++ncardorder] = c }
}

# ------------------------------------------------------------ device line

function flush(    n, a, name, kind, key) {
    if (buf == "") return
    gsub(/^[ \t]+/, "", buf)
    if (isdot) { card(buf); buf = ""; isdot = 0; return }
    n = split(buf, a, /[ \t]+/)
    name = toupper(a[1])
    kind = substr(name, 1, 1)
    key = ""

    if ((kind == "V" || kind == "I") && n >= 4) {
        key = "source " tolower(a[2] "/" a[3]) " value=[" norm(tail(buf, 4)) "]"
        remember(a[2], a[3])
        nsrc[side]++
    } else if ((kind == "C" || kind == "R" || kind == "L") && n >= 4) {
        key = "passive " tolower(a[2] "/" a[3]) " value=[" norm(a[4]) "]" \
              " m=" defaulted(buf, "m", "1")
        remember(a[2], a[3])
        npas[side]++
    } else if ((kind == "S" || kind == "W") && n >= 6) {
        key = "switch " tolower(a[2] "/" a[3] "/" a[4] "/" a[5]) \
              " model=[" norm(a[6]) "]"
        remember(a[2], a[3], a[4], a[5])
        nsw[side]++
    } else if (kind == "X" && n >= 3) {
        key = subckt_key(buf)
        nsub[side]++
    } else if (kind == "B" && n >= 4) {
        key = "bsource " tolower(a[2] "/" a[3]) " expr=[" norm(tail(buf, 4)) "]"
        remember(a[2], a[3])
        nbsrc[side]++
    } else if (n >= 3) {
        # anything else still has to be on both sides, compared verbatim
        key = "other [" norm(tail(buf, 2)) "]"
        remember(a[2], a[3])
        noth[side]++
    } else {
        buf = ""
        return
    }

    ndev[side]++
    dev[side, name] = key
    if (side == 1) order[++nord] = name
    else seen[name] = 1
    buf = ""
}

# ----------------------------------------------------------------- parser

FNR == 1 { if (mode != "sim") flush(); side++; incontrol = 0 }

# simulation mode: "name = value" measure echoes, one file per run
mode == "sim" {
    if ($2 == "=" && $1 ~ /^[a-z_0-9]+$/) {
        mval[side, $1] = $3
        if (side == 1) morder[++nmeas] = $1
        mcount[side]++
    }
    next
}

{
    line = $0
    sub(/\r$/, "", line)
    sub(/[ \t]*;.*$/, "", line)         # ngspice inline comment
    sub(/[ \t]+$/, "", line)

    # the first line of a SPICE deck is its title, never a device
    if (FNR == 1 && line !~ /^[*.]/) next

    lower = tolower(line)
    # "\b" is not a portable awk regex operator, so the word end is spelled out
    if (lower ~ /^[ \t]*\.control([ \t]|$)/) { flush(); incontrol = 1; next }
    if (lower ~ /^[ \t]*\.endc([ \t]|$)/)    { incontrol = 0; next }
    if (incontrol) {
        if (line ~ /^[ \t]*$/ || line ~ /^[ \t]*[*#]/) next
        sub(/^[ \t]+/, "", line)
        card("control: " line)
        next
    }

    # xschem folds long device lines with a leading "+"
    if (line ~ /^\+/) { buf = buf " " substr(line, 2); next }
    flush()

    probe = line
    sub(/^\*+/, "", probe)              # xschem comments its .subckt header
    if (tolower(probe) ~ /^\.subckt[ \t]/) {
        n = split(probe, a, /[ \t]+/)
        for (i = 3; i <= n; i++) ports[side] = ports[side] " " tolower(a[i])
        next
    }

    if (line ~ /^[*]/ || line ~ /^[ \t]*$/) next
    if (line ~ /^[.]/) {
        # .end / .ends close the deck or a (commented) subckt, not circuit
        if (lower ~ /^\.(end|ends)([ \t]|$)/) next
        buf = line; isdot = 1
        next
    }
    buf = line
}

# ---------------------------------------------------------------- verdicts

# one unit in the last printed digit of a measure echo: ngspice prints
# "%e" with 5 decimals, so 6.69637e-06 is only known to 1e-11 (10 ps)
function ulp(s,    m, e, d, p) {
    m = s; e = 0
    if (match(s, /[eE][-+]?[0-9]+$/)) { e = substr(s, RSTART + 1) + 0; m = substr(s, 1, RSTART - 1) }
    p = index(m, ".")
    d = (p > 0) ? length(m) - p : 0
    return 10 ^ (e - d)
}

function absd(x, y) { return (x > y) ? x - y : y - x }

# A time difference below the echo resolution cannot be read off t_dout
# directly, so the bound is the tighter of two routes, each "printed
# difference + one last-digit unit" (both sides round to nearest):
#   t_dout directly                       resolution 10 ps near 7 us
#   TCOUNT x err_lsb, err_lsb = (t_dout - TR - t_trip_ideal)/TCOUNT, valid
#   when t_trip_ideal is identical and TR, TCOUNT are (the netlist mode
#   requires their .param cards identical)  resolution 0.5 ps, |err_lsb| < 10
#   t_top directly, or t_dout - cmp_delay resolution of the t_dout bound + 0.1 ps
function sim_verdict(    i, k, a, b, bad, missing, worst, wname, d, rel, ca, cb,
                         bt, bp, fine, ea, eb, qa, qb) {
    if (side != 2) {
        print "FAIL: schematic simulates to the deck: expects two measure files (deck, schematic)"
        exit 1
    }
    for (i = 1; i <= nmeas; i++) {
        k = morder[i]
        a = mval[1, k]; b = mval[2, k]
        if (!((2, k) in mval) || !isnum(b)) {
            if (isnum(a)) { missing = missing " " k; bad++ }
            continue
        }
        if (!isnum(a)) continue
        d = absd(a, b)
        rel = (a == 0) ? d : d / (a < 0 ? -a : a)
        if (rel > worst || wname == "") { worst = rel; wname = k }
    }
    if (worst == 0)
        printf "REPORT: schematic simulation (level %s): %d measures (deck %d), every one identical to the last printed digit\n",
               level, mcount[2] + 0, mcount[1] + 0
    else
        printf "REPORT: schematic simulation (level %s): %d measures (deck %d); largest relative difference %.3g in %s\n",
               level, mcount[2] + 0, mcount[1] + 0, worst, wname
    ca = mval[1, "code"]; cb = mval[2, "code"]
    if (!isnum(ca) || !isnum(cb) || !isnum(mval[1, "t_dout"]) || !isnum(mval[2, "t_dout"]) ||
        !isnum(mval[1, "t_top"]) || !isnum(mval[2, "t_top"])) {
        printf "FAIL: schematic simulates to the deck (level %s): code/t_dout/t_top missing (deck %s/%s/%s, schematic %s/%s/%s)\n",
               level, ca, mval[1, "t_dout"], mval[1, "t_top"], cb, mval[2, "t_dout"], mval[2, "t_top"]
        exit 1
    }
    TCOUNT = 50e-9                      # frozen in CONTRACT.md

    # t_dout
    bt = absd(mval[1, "t_dout"], mval[2, "t_dout"]) + ulp(mval[1, "t_dout"])
    ea = mval[1, "err_lsb"]; eb = mval[2, "err_lsb"]
    qa = mval[1, "t_trip_ideal"]; qb = mval[2, "t_trip_ideal"]
    if (isnum(ea) && isnum(eb) && isnum(qa) && qa == qb) {
        fine = TCOUNT * (absd(ea, eb) + ulp(ea))
        if (fine < bt) bt = fine
    }
    # t_top
    bp = absd(mval[1, "t_top"], mval[2, "t_top"]) + ulp(mval[1, "t_top"])
    ea = mval[1, "cmp_delay"]; eb = mval[2, "cmp_delay"]
    if (isnum(ea) && isnum(eb)) {
        fine = bt + absd(ea, eb) + ulp(ea)
        if (fine < bp) bp = fine
    }
    bt *= 1e12; bp *= 1e12

    if (missing != "") printf "FAIL: schematic simulation lacks deck measure(s):%s\n", missing
    if (ca + 0 == cb + 0 && bt <= TOL_PS && bp <= TOL_PS && bad == 0) {
        printf "PASS: schematic simulates to the deck (level %s): code %d = %d, |dt_dout| <= %.2f ps, |dt_top| <= %.2f ps (limit %g ps; bounds include the echo resolution)\n",
               level, cb, ca, bt, bp, TOL_PS
        exit 0
    }
    printf "FAIL: schematic simulates to the deck (level %s): code %d vs %d, |dt_dout| <= %.2f ps, |dt_top| <= %.2f ps (limit %g ps; bounds include the echo resolution)\n",
           level, cb, ca, bt, bp, TOL_PS
    exit 1
}

END {
    if (mode == "sim") sim_verdict()
    flush()
    if (side != 2) {
        print "FAIL: check-schematic.awk expects two netlists (deck, schematic)"
        exit 1
    }
    if (ndev[1] == 0 || ndev[2] == 0) {
        printf "FAIL: no devices parsed (deck %d, schematic %d)\n",
               ndev[1] + 0, ndev[2] + 0
        exit 1
    }

    for (i = 1; i <= nord; i++) {
        name = order[i]
        if (dev[2, name] == "")
            printf "FAIL: %s is in %s but not in the schematic\n", name, ref
        else if (dev[1, name] != dev[2, name])
            printf "FAIL: %s deck %s / schematic %s\n",
                   name, dev[1, name], dev[2, name]
        else
            continue
        bad++
    }
    for (name in seen)
        if (dev[1, name] == "") {
            printf "FAIL: %s is in the schematic but not in %s\n", name, ref
            bad++
        }

    if (ports[1] != ports[2]) {
        printf "FAIL: port list deck [%s] schematic [%s]\n", ports[1], ports[2]
        bad++
    } else if (ports[1] == "")
        print "PASS: both netlists are flat top-level decks, no subcircuit ports"
    else
        printf "PASS: subcircuit ports in order:%s\n", ports[1]

    # frozen node names (CONTRACT.md); an unlabelled xschem wire becomes net1
    nwant = split(CONTRACT_NODES, want, / /)
    for (i = 1; i <= nwant; i++) {
        wanted[want[i]] = 1
        if (!((2, want[i]) in node)) {
            printf "FAIL: node %s of the frozen set is absent from the schematic\n",
                   want[i]
            nodebad++
        }
    }
    for (k in node) {
        split(k, kk, SUBSEP)
        if (kk[1] != "2") continue
        if (!(kk[2] in wanted)) {
            printf "FAIL: schematic node %s is not in the frozen node set\n", kk[2]
            nodebad++
        }
    }
    if (nodebad == 0)
        printf "PASS: schematic nodes are exactly the frozen set: %s\n",
               CONTRACT_NODES
    bad += nodebad

    # the non-device text: every dot card and .control line, as a multiset
    for (i = 1; i <= ncardorder; i++) {
        c = cardorder[i]
        if (cards[1, c] + 0 == cards[2, c] + 0) continue
        t = cardtext[c]
        if (length(t) > 90) t = substr(t, 1, 87) "..."
        printf "FAIL: card deck x%d / schematic x%d: %s\n", cards[1, c], cards[2, c], t
        cardbad++
    }
    if (cardbad == 0)
        printf "PASS: schematic carries the deck's %d dot cards and .control lines (includes, params, tran, measures, control)\n",
               ncard[1]
    bad += cardbad

    printf "REPORT: deck %d devices (%d source, %d passive, %d switch, %d subckt, %d bsource, %d other), %d cards\n",
           ndev[1] + 0, nsrc[1] + 0, npas[1] + 0, nsw[1] + 0, nsub[1] + 0, nbsrc[1] + 0, noth[1] + 0, ncard[1] + 0
    printf "REPORT: schematic %d devices (%d source, %d passive, %d switch, %d subckt, %d bsource, %d other), %d cards\n",
           ndev[2] + 0, nsrc[2] + 0, npas[2] + 0, nsw[2] + 0, nsub[2] + 0, nbsrc[2] + 0, noth[2] + 0, ncard[2] + 0

    if (bad == 0)
        printf "PASS: schematic netlists to %s: %d instances match on terminals, value, model and parameters\n",
               ref, ndev[1]
    else
        printf "FAIL: schematic does not netlist to %s: %d mismatch(es)\n", ref, bad

    exit (bad == 0) ? 0 : 1
}
