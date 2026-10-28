# check-schematic.awk -- an xschem netlist must equal the controlled deck
# (adapted from ../bias_gen/check-schematic.awk; one verdict per call).
#
#   awk -v label="atop_cell.sch vs analog_top.spice subckt atop_cell" \
#       -f check-schematic.awk work/ref_atop_cell.spice work/sch_atop_cell.spice
#   awk -v mode=tb -v replaced="bias_gen.spice midref.spice ..." -v label=... \
#       -f check-schematic.awk work/ref_tb.spice work/sch_tb.spice
#
# File 1 is the deck side, file 2 what xschem produced. schematic.sh cuts both
# to the piece being compared: one subcircuit (header + body), or, in tb mode,
# the top level of a deck with every subcircuit definition removed.
#
# Compared, instance by instance (matched by name):
#   * V / I sources   terminals, value (DC, PWL, PULSE; {param} expressions)
#   * R / C           terminals, value, m (absent m reads as 1)
#   * X subcircuits   every terminal in order, the model / subcircuit name,
#                     the parameter set (keys case-folded, order free, m=1 default)
# plus the port list in order and the subcircuit name (cell mode), and every
# dot card as a multiset (tb mode). In tb mode the deck includes named in
# -v replaced are the subcircuits xschem's hierarchy emits itself: they must
# be ABSENT from the schematic side (a second definition) and are not
# expected there; every other card must be on both sides.
#
# Normalised, because xschem and a hand-written deck spell the same thing
# differently: 'quotes' vs {braces}; "+" continuation lines; engineering
# suffixes (5u == 5000n == 5e-06); whitespace inside expressions; case.
# Node names are compared as they are: an unlabelled xschem wire becomes
# net<N> and fails the terminal comparison.
#
# Prints one PASS:/FAIL: line (prefixed "schematic: "), REPORT: lines with
# the first mismatches, exits non-zero on failure. -v noname=1 skips the
# subcircuit-name comparison (the drawing's subcircuit is named by its symbol,
# e.g. comparator, the deck's cmp).
#
# Geometry mode, -v geo=<file>: the drawing is made of the PDK MOS symbols,
# whose format adds the drawn S/D junction geometry ad as pd ps nrd nrs sa sb sd
# that the deck does not carry. Those nine keys are left out of the instance
# comparison (everything else, L W nf m included, must be equal) and judged
# instead: the deck side must carry none of them (they are ADDED by the
# drawing), and on the drawing side every MOS must carry all nine, each the
# expression of the PDK symbol's template. <file> holds `model key expression`
# lines read from the PDK symbols by schematic.sh. REPORT lines give the
# formula and its values per device type (model, W, nf).

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

function strip(v) { gsub(/['" \t]/, "", v); return tolower(v) }

function subckt_key(text,    n, a, i, first, nodes, model, np, pk, eq, key, hasm, out) {
    n = split(squeeze(text), a, /[ \t]+/)
    first = n + 1
    for (i = 2; i <= n; i++) if (index(a[i], "=") > 1) { first = i; break }
    model = a[first - 1]
    mdl[side, curname] = tolower(model)
    nodes = ""
    for (i = 2; i <= first - 2; i++) nodes = nodes (nodes == "" ? "" : "/") tolower(a[i])
    np = 0; hasm = 0
    for (i = first; i <= n; i++) {
        eq = index(a[i], "=")
        if (eq <= 1) { pk[++np] = "?" norm(a[i]); continue }
        key = tolower(substr(a[i], 1, eq - 1))
        if (key == "w") wv[side, curname] = norm(substr(a[i], eq + 1))
        if (key == "nf") nfv[side, curname] = norm(substr(a[i], eq + 1))
        if (geo != "" && key ~ /^(ad|as|pd|ps|nrd|nrs|sa|sb|sd)$/) {
            gx[side, curname, key] = strip(substr(a[i], eq + 1)); ngx[side, curname]++
            continue
        }
        if (key == "m") hasm = 1
        pk[++np] = key "=" norm(substr(a[i], eq + 1))
    }
    if (!hasm) pk[++np] = "m=1"
    sortk(pk, np)
    out = ""
    for (i = 1; i <= np; i++) out = out (out == "" ? "" : " ") pk[i]
    return "X " nodes " model=" tolower(model) " [" out "]"
}

function card(text,    c, f, nf, base) {
    c = norm(squeeze(text))
    if (mode == "tb" && tolower(text) ~ /^\.include/) {
        nf = split(text, f, /[ \t\/]+/)
        base = f[nf]
        if (index(" " replaced " ", " " base " ")) {
            if (side == 1) { nrepl++; return }
            rep("schematic still includes " base " (its subcircuits come from the hierarchy: defined twice)")
            bad++
            return
        }
    }
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
    else if (kind == "X" && n >= 3) {
        curname = name
        key = subckt_key(buf)
    }
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
    if (mode != "tb") {
        if (ports[1] != ports[2]) { rep("ports deck [" ports[1] " ] / schematic [" ports[2] " ]"); bad++ }
        if (!noname && sname[1] != sname[2]) { rep("subckt name deck " sname[1] " / schematic " sname[2]); bad++ }
    }
    for (i = 1; i <= ncardorder; i++) {
        c = cardorder[i]
        if (cards[1, c] + 0 == cards[2, c] + 0) continue
        rep(sprintf("card deck x%d / schematic x%d: %s", cards[1, c], cards[2, c], cardtext[c]))
        bad++
    }
    if (geo != "") geocheck()
    np = split(ports[1], pp, " ")
    if (bad == 0) {
        if (mode == "tb")
            printf "PASS: schematic: %s: %d instances equal (terminals, value, model, parameters), %d cards equal, %d deck includes replaced by the hierarchy and absent\n",
                   label, nord, ncard[1], nrepl
        else if (geo != "")
            printf "PASS: schematic: %s: subckt %s, %d ports in order, %d instances equal (terminals, model, L/W/nf/m); S/D geometry (ad as pd ps nrd nrs sa sb sd) ADDED by the drawing on %d/%d MOS, every expression the PDK symbol's\n",
                   label, sname[2], np, nord, ngeook, nmos
        else
            printf "PASS: schematic: %s: subckt %s, %d ports in order, %d instances equal (terminals, value, model, parameters)\n",
                   label, sname[2], np, nord
        exit 0
    }
    printf "FAIL: schematic: %s: %d mismatch(es) (deck %d / schematic %d instances)\n", label, bad, ndev[1], ndev[2]
    exit 1
}

# ------------------------------------------------------------ geometry mode
function fmt(v) {
    if (v == 0) return "0"
    if (v < 1e-9) return sprintf("%.4gp", v * 1e12)
    if (v < 1e-3) return sprintf("%.4gu", v * 1e6)
    return sprintf("%.4g", v)
}
function geocheck(    l, f, i, name, m, k, keys, nk, ok, w, nf, grp, ng, g, gk, gn, gm, gw, gnf, ad, as_, pd, ps, nr) {
    while ((getline l < geo) > 0) {
        split(l, f, " ")
        k = f[2]; sub(/^[^ ]+ [^ ]+ /, "", l)
        pexp[f[1], k] = strip(l)
        pform[f[1]] = pform[f[1]] (pform[f[1]] == "" ? "" : ", ") k " = " l
    }
    close(geo)
    nk = split("ad as pd ps nrd nrs sa sb sd", keys, " ")
    nmos = 0; ngeook = 0; ng = 0
    for (i = 1; i <= nord; i++) {
        name = order[i]
        if (ngx[1, name] + 0 > 0) { rep(name ": the deck already carries S/D geometry (not ADDED by the drawing)"); bad++ }
        m = mdl[2, name]
        if (m !~ /^[np]fet_/) continue
        nmos++
        if (!((m, "ad") in pexp)) { rep(name ": no PDK template expressions for model " m); bad++; continue }
        ok = 1
        for (k = 1; k <= nk; k++) {
            if (!((2, name, keys[k]) in gx)) { rep(name ": " keys[k] " missing on the drawing side"); ok = 0 }
            else if (gx[2, name, keys[k]] != pexp[m, keys[k]]) {
                rep(name ": " keys[k] "=" gx[2, name, keys[k]] " is not the PDK symbol's " pexp[m, keys[k]]); ok = 0
            }
        }
        if (!ok) { bad++; continue }
        ngeook++
        gk = m " W=" wv[2, name] " nf=" nfv[2, name]
        if (!(gk in gn)) { grp[++ng] = gk; gm[gk] = m; gw[gk] = wv[2, name] + 0; gnf[gk] = nfv[2, name] + 0 }
        gn[gk] = gn[gk] (gn[gk] == "" ? "" : " ") name
    }
    for (g = 1; g <= ng; g++) usedm[gm[grp[g]]] = 1
    for (m in usedm) print "REPORT: schematic: " label ": PDK " m ".sym template: " pform[m]
    # the template's expressions, evaluated (W in m)
    for (g = 1; g <= ng; g++) {
        gk = grp[g]; w = gw[gk]; nf = gnf[gk]
        ad = int((nf + 1) / 2) * w / nf * 0.18e-6
        as_ = int((nf + 2) / 2) * w / nf * 0.18e-6
        pd = 2 * int((nf + 1) / 2) * (w / nf + 0.18e-6)
        ps = 2 * int((nf + 2) / 2) * (w / nf + 0.18e-6)
        nr = 0.18e-6 / w
        printf "REPORT: schematic: %s: %s W=%s nf=%d (%s): ad=%s as=%s pd=%s ps=%s nrd=nrs=%s sa=sb=sd=0\n",
               label, gm[gk], fmt(w), nf, gn[gk], fmt(ad), fmt(as_), fmt(pd), fmt(ps), fmt(nr)
    }
}
