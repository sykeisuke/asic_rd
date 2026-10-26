# check-sw.awk -- an xschem netlist of one switch drawing (sw_s0/1/2.sch)
# must equal its subcircuit in ref/switches.spice. Adapted from
# check-schematic.awk (cell mode only; kept separate so the two evolve apart).
#
#   awk -v label="sw_s0.sch vs switches.spice" -f check-sw.awk #       work/sw/ref_sw_s0.spice work/sw/cut_sw_s0.spice
#
# File 1 is the deck subcircuit, file 2 the one xschem produced (a commented
# "**.subckt" header is accepted). Compared: the subcircuit name, the port
# list in order, and every instance matched by name: terminals in order,
# model, and the full parameter set (keys case-folded, order free, absent m
# reads as 1, engineering suffixes normalised: 0.22p == 2.2e-13). A parameter
# present on one side only (e.g. nrd/nrs/sa/sb/sd from the PDK symbol's own
# format) is a mismatch. One PASS:/FAIL: line ("schematic: "), REPORT: lines
# with the first mismatches, non-zero exit on failure.

BEGIN { if (label == "") label = "netlist"; MAXREP = 12 }

function nval(t,    mant, suf, mul) {
    if (t !~ /^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?[a-z]*$/)
        return t
    mant = t
    sub(/[a-z]+$/, "", mant)
    if (mant == "" || mant ~ /[eE][-+]?$/) return t
    suf = substr(t, length(mant) + 1)
    mul = 1
    if      (suf == "t")                  mul = 1e12
    else if (suf == "g")                  mul = 1e9
    else if (suf == "meg" || suf == "x")  mul = 1e6
    else if (suf == "k")                  mul = 1e3
    else if (suf == "m")                  mul = 1e-3
    else if (suf == "u")                  mul = 1e-6
    else if (suf == "n")                  mul = 1e-9
    else if (suf == "p")                  mul = 1e-12
    else if (suf == "f")                  mul = 1e-15
    else if (suf != "")                   return t
    return sprintf("%.12g", (mant + 0) * mul)
}

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

function param(text, key,    n, a, i) {
    n = split(squeeze(text), a, /[ \t]+/)
    for (i = 1; i <= n; i++)
        if (tolower(substr(a[i], 1, length(key) + 1)) == tolower(key) "=")
            return norm(substr(a[i], length(key) + 2))
    return ""
}

# tokens start..end of a device line, dropping instance-parameter tokens
function tail(text, start,    n, a, i, out) {
    n = split(text, a, /[ \t]+/)
    out = ""
    for (i = start; i <= n; i++) {
        if (tolower(a[i]) ~ /^(m|savecurrent)=/) continue
        out = out (out == "" ? "" : " ") a[i]
    }
    return out
}

function sortk(k, n,    i, j, t) {
    for (i = 2; i <= n; i++) {
        t = k[i]
        for (j = i - 1; j >= 1 && k[j] > t; j--) k[j + 1] = k[j]
        k[j + 1] = t
    }
}

function subckt_key(text,    n, a, i, first, nodes, model, np, pk, eq, key, hasm, out) {
    n = split(squeeze(text), a, /[ \t]+/)
    first = n + 1
    for (i = 2; i <= n; i++) if (index(a[i], "=") > 1) { first = i; break }
    model = a[first - 1]
    nodes = ""
    for (i = 2; i <= first - 2; i++) nodes = nodes (nodes == "" ? "" : "/") tolower(a[i])
    np = 0; hasm = 0
    for (i = first; i <= n; i++) {
        eq = index(a[i], "=")
        if (eq <= 1) { pk[++np] = "?" norm(a[i]); continue }
        key = tolower(substr(a[i], 1, eq - 1))
        if (key == "m") hasm = 1
        pk[++np] = key "=" norm(substr(a[i], eq + 1))
    }
    if (!hasm) pk[++np] = "m=1"
    sortk(pk, np)
    out = ""
    for (i = 1; i <= np; i++) out = out (out == "" ? "" : " ") pk[i]
    return "X " nodes " model=" tolower(model) " [" out "]"
}

function card(text,    c) {
    c = norm(squeeze(text))
    ncard[side]++
    cards[side, c]++
    if (!(c in cardtext)) { cardtext[c] = text; cardorder[++ncardorder] = c }
}

function rep(s) { if (++nrep <= MAXREP) print "REPORT: schematic: " label ": " s }

function flush(    n, a, name, kind, key) {
    if (buf == "") return
    gsub(/^[ \t]+/, "", buf)
    if (isdot) { card(buf); buf = ""; isdot = 0; return }
    n = split(buf, a, /[ \t]+/)
    name = toupper(a[1])
    kind = substr(name, 1, 1)
    if ((kind == "V" || kind == "I") && n >= 4)
        key = "source " tolower(a[2] "/" a[3]) " value=[" norm(tail(buf, 4)) "]"
    else if ((kind == "C" || kind == "R") && n >= 4)
        key = "passive " tolower(a[2] "/" a[3]) " value=[" norm(a[4]) "] m=" ((param(buf, "m") == "") ? "1" : param(buf, "m"))
    else if (kind == "X" && n >= 3)
        key = subckt_key(buf)
    else
        key = "other [" norm(buf) "]"
    ndev[side]++
    if ((side, name) in dev) { rep(name " defined twice"); bad++ }
    dev[side, name] = key
    if (side == 1) order[++nord] = name
    else seen[name] = 1
    buf = ""
}

FNR == 1 { flush(); side++; inhdr = 0; incontrol = 0 }

{
    line = $0
    sub(/\r$/, "", line)
    sub(/[ \t]*;.*$/, "", line)
    sub(/[ \t]+$/, "", line)
    lower = tolower(line)
    if (lower ~ /^[ \t]*\.control([ \t]|$)/) { flush(); incontrol = 1; next }
    if (lower ~ /^[ \t]*\.endc([ \t]|$)/)    { incontrol = 0; next }
    if (incontrol) { if (line !~ /^[ \t]*([*#].*)?$/) { sub(/^[ \t]+/, "", line); card("control: " line) }; next }
    # a folded .subckt header continues with "+" (xschem: "*+" when commented)
    if (inhdr && line ~ /^\**\+/) {
        sub(/^\**\+/, "", line)
        n = split(line, a, /[ \t]+/)
        for (i = 1; i <= n; i++) if (a[i] != "") ports[side] = ports[side] " " tolower(a[i])
        next
    }
    inhdr = 0
    if (line ~ /^\+/) { buf = buf " " substr(line, 2); next }
    flush()
    probe = line
    sub(/^\*+/, "", probe)
    if (tolower(probe) ~ /^\.subckt[ \t]/) {
        n = split(probe, a, /[ \t]+/)
        sname[side] = tolower(a[2])
        for (i = 3; i <= n; i++) ports[side] = ports[side] " " tolower(a[i])
        inhdr = 1
        next
    }
    if (line ~ /^[*]/ || line ~ /^[ \t]*$/) next
    if (line ~ /^[.]/) {
        if (lower ~ /^\.(end|ends)([ \t]|$)/) next
        buf = line; isdot = 1
        next
    }
    buf = line
}

END {
    flush()
    if (side != 2 || ndev[1] == 0 || ndev[2] == 0) {
        printf "FAIL: schematic: %s: nothing to compare (deck %d, schematic %d devices)\n", label, ndev[1], ndev[2]
        exit 1
    }
    for (i = 1; i <= nord; i++) {
        name = order[i]
        if (!((2, name) in dev)) { rep(name " is in the deck, not in the schematic"); bad++ }
        else if (dev[1, name] != dev[2, name]) {
            rep(name " deck " dev[1, name] " / schematic " dev[2, name]); bad++
        }
    }
    for (name in seen)
        if (!((1, name) in dev)) { rep(name " is in the schematic, not in the deck"); bad++ }
    if (ports[1] != ports[2]) { rep("ports deck [" ports[1] " ] / schematic [" ports[2] " ]"); bad++ }
    if (sname[1] != sname[2]) { rep("subckt name deck " sname[1] " / schematic " sname[2]); bad++ }
    for (i = 1; i <= ncardorder; i++) {
        c = cardorder[i]
        if (cards[1, c] + 0 == cards[2, c] + 0) continue
        rep(sprintf("card deck x%d / schematic x%d: %s", cards[1, c], cards[2, c], cardtext[c]))
        bad++
    }
    np = split(ports[1], pp, " ")
    if (bad == 0) {
        printf "PASS: schematic: %s: subckt %s, %d ports in order, %d instances equal (terminals, model, every parameter)\n",
               label, sname[2], np, nord
        exit 0
    }
    printf "FAIL: schematic: %s: %d mismatch(es) (deck %d / schematic %d instances)\n", label, bad, ndev[1], ndev[2]
    exit 1
}
