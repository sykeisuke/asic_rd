# Does the xschem netlist of a testbench drawing carry its bench?
#
#   awk -v tb=tb_drive -f check-tb.awk work/xtb_tb_drive/tb_drive.spice
#
# xschem SILENTLY drops an instance whose symbol it cannot find, so every
# instance of the bench is looked for by name, nodes and model (lower case,
# one space): the DUT line (XL ... latch), the latch's own subcircuit from
# latch.sch with the library cell inside, the sources, the load, and for
# tb_kick the comparator from comparator.sch, its bias diode and the charge
# path. One .control block and the standard-cell library include must be
# present. Prints one PASS or FAIL line per testbench.
BEGIN {
    n = 0
    if (tb == "tb_drive" || tb == "tb_aperture") {
        want[++n] = "^xl d clk q dvdd 0 latch$"; dut = n
        want[++n] = "^\\.subckt latch d clk q vdd vss$"
        want[++n] = "^xff vdd vdd vss vss clk d q gf180mcu_as_sc_mcu7t3v3__dfxtn_2$"
        want[++n] = "^vdvdd dvdd 0 "
        want[++n] = "^vclk clk 0 pulse\\("
        want[++n] = "^vd d 0 pwl\\("
        want[++n] = "^cq q 0 "
    } else if (tb == "tb_kick") {
        want[++n] = "^xl dout clk q dvdd 0 latch$"; dut = n
        want[++n] = "^\\.subckt latch d clk q vdd vss$"
        want[++n] = "^xff vdd vdd vss vss clk d q gf180mcu_as_sc_mcu7t3v3__dfxtn_2$"
        want[++n] = "^xdut vbl top dout 0 vdd 0 0 pbias comparator$"; cmpi = n
        want[++n] = "^\\.subckt comparator inp inn dout clk vdd vss nbias pbias$"
        want[++n] = "^xrefp pbias pbias vdd vdd pfet_03v3 "
        want[++n] = "^irefp pbias 0 "
        want[++n] = "^xcs (top bot|bot top) cap_mim_2f0_m4m5_noshield "
        want[++n] = "^s2 vref top s2 0 swideal"
        want[++n] = "^rlkt top 0 1e15"
        want[++n] = "^vdd_source vdd 0 "
        want[++n] = "^vdvdd dvdd 0 "
        want[++n] = "^vvbl vbl 0 "
        want[++n] = "^vvref vref 0 "
        want[++n] = "^vclk clk 0 pulse\\("
        want[++n] = "^vbot bot 0 pwl\\("
        want[++n] = "^vs2 s2 0 pwl\\("
        want[++n] = "^cq q 0 "
    } else {
        printf "FAIL: check-tb.awk: unknown testbench %s\n", tb; exit 1
    }
    ncontrol = 0; nlib = 0
}
{
    line = tolower($0)
    gsub(/[ \t]+/, " ", line)
    sub(/ $/, "", line)
    sub(/^ /, "", line)
    if (line ~ /^\.control/) ncontrol++
    if (line ~ /^\.include .*gf180mcu_as_sc_mcu7t3v3\.spice$/) nlib++
    lines[NR] = line
}
END {
    st = 0; nhit = 0
    for (i = 1; i <= n; i++) {
        hit[i] = ""
        for (k = 1; k <= NR; k++) if (lines[k] ~ want[i]) { hit[i] = lines[k]; break }
        if (hit[i] == "") { printf "FAIL: %s: no netlist line matching /%s/\n", tb, want[i]; st = 1 }
        else nhit++
    }
    if (ncontrol != 1) { printf "FAIL: %s: %d .control blocks (want 1)\n", tb, ncontrol; st = 1 }
    if (nlib != 1) { printf "FAIL: %s: %d includes of the standard-cell library (want 1)\n", tb, nlib; st = 1 }
    if (!st) {
        extra = (tb == "tb_kick") ? sprintf("; comparator [%s]", hit[cmpi]) : ""
        printf "PASS: %s netlists its bench: %d of %d lines, DUT [%s]%s\n", tb, nhit, n, hit[dut], extra
    }
    exit st
}
