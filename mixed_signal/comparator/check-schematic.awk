# check-schematic.awk -- the xschem schematic must netlist back to its deck.
#
#   awk -v ref=cmp_ts.spice -f check-schematic.awk cmp_ts.spice work/cmp_ts_sch.spice
#
# File 1 is the controlled SPICE source, file 2 is what xschem produced from
# cmp_ts.sch. A drawing that merely looks like the deck is not evidence, so
# every device is compared on its four terminals, its model and L/W/nf/m, and
# the subcircuit port list is compared in order. xschem omits m=1 and writes
# expressions in 'quotes' where the deck writes {braces}; both are normalised.
#
# Prints one PASS:/FAIL: line per check, exits non-zero on any failure.

function norm(v) {
    gsub(/[{}'"]/, "", v)
    return tolower(v)
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

function flush(    n, a, name, key) {
    if (buf == "") return
    n = split(buf, a, /[ \t]+/)
    name = toupper(a[1])
    if (substr(name, 1, 1) == "X" && n >= 6) {
        key = tolower(a[2] "/" a[3] "/" a[4] "/" a[5] "/" a[6]) \
              " L=" param(buf, "L") " W=" param(buf, "W") \
              " nf=" defaulted(buf, "nf", "1") " m=" defaulted(buf, "m", "1")
        ndev[side]++
    } else if (substr(name, 1, 1) == "C" && n >= 4) {
        key = tolower(a[2] "/" a[3]) " value=" norm(a[4]) \
              " m=" defaulted(buf, "m", "1")
        ncap[side]++
    } else {
        buf = ""
        return
    }
    dev[side, name] = key
    if (side == 1) order[++nord] = name
    else seen[name] = 1
    buf = ""
}

FNR == 1 { flush(); side++ }

{
    line = $0
    sub(/\r$/, "", line)

    # xschem wraps long device lines with a leading "+"
    if (line ~ /^\+/) { buf = buf " " substr(line, 2); next }
    flush()

    probe = line
    sub(/^\*+/, "", probe)              # xschem comments its .subckt header
    if (tolower(probe) ~ /^\.subckt[ \t]/) {
        n = split(probe, a, /[ \t]+/)
        for (i = 3; i <= n; i++) ports[side] = ports[side] " " tolower(a[i])
        next
    }

    if (line ~ /^[*]/ || line ~ /^[.]/ || line ~ /^[ \t]*$/) next
    buf = line
}

END {
    flush()
    if (side != 2) {
        print "FAIL: check-schematic.awk expects two netlists (deck, schematic)"
        exit 1
    }
    if (ndev[1] == 0 || ndev[2] == 0) {
        printf "FAIL: no devices parsed (deck %d, schematic %d)\n", ndev[1], ndev[2]
        exit 1
    }

    for (i = 1; i <= nord; i++) {
        name = order[i]
        if (dev[2, name] == "")
            printf "FAIL: %s is in %s but not in the schematic\n", name, ref
        else if (dev[1, name] != dev[2, name])
            printf "FAIL: %s deck [%s] schematic [%s]\n", name, dev[1, name], dev[2, name]
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
    } else
        printf "PASS: subcircuit ports in order:%s\n", ports[1]

    if (bad == 0)
        printf "PASS: schematic netlists to %s: %d transistors, %d capacitors\n",
               ref, ndev[1], ncap[1]
    exit (bad == 0) ? 0 : 1
}
