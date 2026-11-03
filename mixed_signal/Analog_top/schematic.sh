#!/bin/sh
# The `schematic` phase of run.sh (v7): xschem is the SOURCE of the macro netlist.
# Run inside the container, cwd = this block.
#
#   REGEN=1 sh schematic.sh   (re)write analog_top.spice from the drawings
#   sh schematic.sh           regenerate into work/sch/ and FAIL if the checked-in
#                             analog_top.spice differs (it is then stale)
#   (from the host: ./scripts/sim.sh analog-top PHASES=schematic [REGEN=1])
#
#   1. sw_schematic.sh: the transistor-level switch views sw_s0/1/2.sch against
#      ref/switches.spice (its own PASS/FAIL lines)
#   2. analog_top_sch.py draws comparator_d, bias_gen_s (each derived from its
#      block's own drawing), atop_cell, analog_top (.sch/.sym);
#      tb_sch.py draws tb_analog_top.sch from tb_analog_top.spice
#   3. xschem netlists analog_top.sch hierarchically (top as a .subckt) into
#      work/sch/gen/; with a GENERATED header that is analog_top.spice: every
#      subcircuit down to transistors, no model or parameter card
#   4. checks on that netlist (one PASS:/FAIL: line each):
#      - midref_div, midref_buf, vrlo_ref, ramp_simple, sw_s0/1/2: equal to
#        their own decks (ports, devices, terminals, models, every parameter)
#      - ic_source: equal to ../ic_source/ic_source.spice by that block's own
#        checker (it knows the standard-cell phase generator)
#      - sample_seq, seq_dly, seq_cell: equal to ../sample_seq/sample_seq.spice
#        by that block's own checker (check_sch.py: ports as a set, every
#        instance's cell and the net on every named pin)
#      - bias_gen_s: equal to the expected subcircuit make_refs.py builds from
#        the block's DECK (bias_gen + XOL / ivrlo)
#      - comparator_d: equal to make_refs.py's (comparator.spice subckt cmp,
#        ports inp inn ibias dout vdd vss, + XREFP) in L/W/nf/m; the S/D
#        geometry the PDK MOS symbols add must be the PDK template expressions
#        on every MOS, XREFP included
#      - latch vs ../latch/latch.spice: ports in order and its one
#        standard-cell instance (nodes, cell name)
#      - no plate leak resistor (no 1e15, no RLK) and no parameter reference
#        ({...}) in analog_top.spice: every size is a number
#      - check_equiv.py: flattened to devices, the macro is v6's
#        (data/v6_ref/analog_top.spice) with the sequencer inside (xseq.*),
#        the 12 switch controls internal and acq a port, nothing else
#      - each subcircuit defined once, none referenced undefined, exactly the
#        expected set, no .include / .lib / .param card
#   5. xschem netlists tb_analog_top.sch (hierarchically): its top level equals
#      tb_analog_top.spice's (sources, values, XDUT, CQ loads, cards incl.
#      .options rshunt); every subcircuit it emits equals analog_top.spice's
#   6. render.sh: every v4 sheet to assets/<sheet>.png and <sheet>.svg
set -u
cd "$(dirname -- "$0")"
mkdir -p work/sch/gen assets
RC=xschemrc
GEN=work/sch/analog_top.gen.spice
V6REF=data/v6_ref/analog_top.spice
EXPECT="analog_top atop_cell comparator_d ramp_simple ic_source sample_seq seq_dly seq_cell bias_gen_s midref_div midref_buf vrlo_ref latch sw_s0 sw_s1 sw_s2"
PDKSYM=/foss/pdks/gf180mcuD/libs.tech/xschem/symbols

# --------------------------------------------------------------- 1. switches
sh sw_schematic.sh || echo "FAIL: schematic: sw_schematic.sh"
[ -f data/sw_schematic.done ] || echo "FAIL: schematic: data/sw_schematic.done absent: sw_s0/1/2.sch not verified"

# ---------------------------------------------------------------- 2. drawings
python3 analog_top_sch.py || { echo "FAIL: schematic: analog_top_sch.py"; exit 1; }
python3 tb_sch.py || { echo "FAIL: schematic: tb_sch.py"; exit 1; }
python3 make_refs.py || { echo "FAIL: schematic: make_refs.py"; exit 1; }

# one subcircuit (header through .ends, commented xschem header accepted)
getsub() {
    awk -v n="$1" '{ l = $0; sub(/^\*+/, "", l); split(tolower(l), t, /[ \t]+/) }
        !on && t[1] == ".subckt" && t[2] == tolower(n) { on = 1 }
        on { print }
        on && t[1] ~ /^\.ends/ { exit }' "$2"
}
# a deck without its (uncommented) subcircuit definitions
toplevel() {
    awk '{ split(tolower($0), t, /[ \t]+/) }
        t[1] == ".subckt" { skip = 1 }
        !skip { print }
        skip && t[1] ~ /^\.ends/ { skip = 0 }' "$1"
}
subnames() { awk 'tolower($1) == ".subckt" { print tolower($2) }' "$1"; }
# subcircuit / model names an X line references (first token before the parameters)
xrefs() {
    awk '/^\+/ { l = l " " substr($0, 2); next } { if (l != "") print l; l = $0 } END { print l }' "$1" |
        awk 'toupper(substr($1, 1, 1)) == "X" { m = ""; for (i = 2; i <= NF; i++) { if (index($i, "=")) break; m = $i }
             print tolower(m) }' | sort -u
}

# ------------------------------------------------- 3. the generated netlist
rm -f work/sch/gen/analog_top.spice
xschem --rcfile "$RC" -b -q -n -s --tcl "set top_is_subckt 1" -o work/sch/gen analog_top.sch \
    > work/sch/gen/xschem.txt 2>&1
if [ ! -s work/sch/gen/analog_top.spice ]; then
    echo "FAIL: schematic: xschem produced no netlist for analog_top.sch"; exit 1
fi
{
    cat <<'EOF'
* analog_top (v7, mixed_signal/Analog_top) -- the analog macro of the 8-bit
* true bottom-plate single-slope ADC: four sampling/conversion cells on one
* shared ramp (ramp_simple: 73 unit MIMs + reset, fed by the I/C current
* source ic_source; ADR 0025 / 0026), bias_gen_s, vrlo_ref (7/55 AVDD), one
* midref_div and ONE midref_buf whose output vref is both the S2 level and
* every comparator's inp (midrail_ref, ADR 0021). Every analog block is inside,
* and the sampling sequencer sample_seq (v7, ADR 0027): the twelve switch
* controls are made inside from the count clock and acq.
*
* GENERATED from analog_top.sch by schematic.sh (xschem, hierarchical: every
* block down to transistors, as drawn). DO NOT HAND-EDIT. Change the drawings
* (analog_top_sch.py, the blocks' own .sch) and rewrite this file with
*   ./scripts/sim.sh analog-top PHASES=schematic REGEN=1
* Without REGEN the schematic phase FAILs while this file differs from what
* the drawings netlist to.
*
* Subcircuits: analog_top, atop_cell, comparator_d (comparator + its pbias
* diode, flat), ramp_simple, ic_source, sample_seq, seq_dly, seq_cell,
* bias_gen_s (bias_gen - XOB/ivbl + XOL -> ivrlo), vrlo_ref, midref_div,
* midref_buf, latch, sw_s0, sw_s1, sw_s2. ic_source's phase generator and
* sample_seq are standard cells (not defined here).
* comparator_d and sw_s0/1/2 carry
* drawn S/D junction geometry (the PDK MOS symbols' ad/as/pd/ps/nrd/nrs; the
* switches' from their deck), bias_gen_s its deck's. latch is one
* standard cell, gf180mcu_as_sc_mcu7t3v3__dfxtn_2 (not defined here).
* Plates: bot = MIM terminal 1, S2 to vref, comparator inn (floats during the
* conversion); top = MIM terminal 2, S0 from vfe, S1 from vramp.
* No plate leak resistor: a bench that needs a DC path on the floating plate
* adds it itself (tb_analog_top.spice: .options rshunt=1e15).
* No model or parameter card and no parameter reference: the including deck
* carries the PDK models (typical / res_typical / mimcap_typical) and the
* standard-cell library gf180mcu_as_sc_mcu7t3v3.spice (make pdk-libs;
* /foss/pdk_libs). Against v6 (data/v6_ref/analog_top.spice): check_equiv.py.
*
EOF
    awk 'tolower($0) !~ /^\.end[ \t]*$/' work/sch/gen/analog_top.spice
} > "$GEN"
if [ "${REGEN:-0}" = 1 ]; then
    if cmp -s "$GEN" analog_top.spice; then
        echo "REPORT: schematic: REGEN=1: analog_top.spice already equals the drawings' netlist (not rewritten)"
    else
        cp "$GEN" analog_top.spice
        echo "REPORT: schematic: REGEN=1: wrote analog_top.spice from analog_top.sch ($(wc -l < "$GEN") lines)"
    fi
fi
if cmp -s "$GEN" analog_top.spice; then
    echo "PASS: schematic: analog_top.spice is what analog_top.sch netlists to ($(wc -l < "$GEN") lines, $(subnames "$GEN" | wc -l) subcircuits)"
else
    echo "FAIL: schematic: analog_top.spice differs from work/sch/analog_top.gen.spice (re-run with REGEN=1)"
fi

# ------------------------------------------------------------ 4. its checks
# 4a. blocks equal to their own decks
for pair in midref_div:../midrail_ref/midref.spice midref_buf:../midrail_ref/midref.spice \
            vrlo_ref:../vrlo_ref/vrlo_ref.spice ramp_simple:../ramp_simple/ramp_simple.spice \
            sw_s0:ref/switches.spice sw_s1:ref/switches.spice \
            sw_s2:ref/switches.spice; do
    s=${pair%%:*}; deck=${pair#*:}
    getsub "$s" "$deck" > "work/sch/ref_$s.spice"
    getsub "$s" "$GEN" > "work/sch/cut_$s.spice"
    [ -s "work/sch/ref_$s.spice" ] || echo "FAIL: schematic: no subckt $s in $deck"
    awk -v label="analog_top.spice subckt $s vs $(basename "$deck")" -f check-schematic.awk \
        "work/sch/ref_$s.spice" "work/sch/cut_$s.spice"
done
# 4a''. the I/C source against its own deck, by its own checker (file 2 as xschem
# writes a top-level drawing: the ports on a commented **.subckt line, no .ends)
getsub ic_source "$GEN" | awk 'NR == 1 { sub(/^\*+/, ""); print "**" $0; next } tolower($1) !~ /^\.ends/' \
    > work/sch/cut_ic_source.spice
awk -v sub_=ic_source -f ../ic_source/check-schematic.awk ../ic_source/ic_source.spice work/sch/cut_ic_source.spice \
    | sed 's/^\(PASS\|FAIL\): /\1: schematic: analog_top.spice subckt ic_source vs ic_source.spice: /'
# 4a'. the derived bias generator against make_refs.py's expectation
for s in bias_gen_s; do
    getsub "$s" "$GEN" > "work/sch/cut_$s.spice"
    [ -s "work/sch/ref_$s.spice" ] || echo "FAIL: schematic: make_refs.py wrote no work/sch/ref_$s.spice"
    awk -v label="analog_top.spice subckt $s vs make_refs.py (its block deck + the declared addition)" \
        -f check-schematic.awk "work/sch/ref_$s.spice" "work/sch/cut_$s.spice"
done

# 4b. comparator: the deck's devices + XREFP, the PDK symbols' S/D geometry added.
# The template expressions are read from the PDK symbols (not restated here).
q=$(printf '\047')
for m in nfet_03v3 pfet_03v3; do
    awk -v m="$m" -v q="$q" '
        /^template="/ { on = 1 }
        on && /^"[ \t]*$/ { exit }
        on { l = $0; gsub(/[\\"]/, "", l)
             re = "(^|[ \t])(ad|as|pd|ps|nrd|nrs|sa|sb|sd)=(" q "[^" q "]*" q "|[^ \t]+)"
             while (match(l, re)) {
                 kv = substr(l, RSTART, RLENGTH); sub(/^[ \t]+/, "", kv)
                 e = index(kv, "=")
                 print m, substr(kv, 1, e - 1), substr(kv, e + 1)
                 l = substr(l, RSTART + RLENGTH)
             } }' "$PDKSYM/$m.sym"
done > work/sch/pdk_geo.txt
if [ "$(wc -l < work/sch/pdk_geo.txt)" -ne 18 ]; then
    echo "FAIL: schematic: read $(wc -l < work/sch/pdk_geo.txt) of 18 S/D geometry expressions from the PDK MOS symbols"
fi
getsub comparator_d "$GEN" > work/sch/cut_comparator_d.spice
[ -s work/sch/ref_comparator_d.spice ] || echo "FAIL: schematic: make_refs.py wrote no work/sch/ref_comparator_d.spice"
awk -v geo=work/sch/pdk_geo.txt \
    -v label="analog_top.spice subckt comparator_d vs make_refs.py (comparator.spice subckt cmp + XREFP)" \
    -f check-schematic.awk work/sch/ref_comparator_d.spice work/sch/cut_comparator_d.spice

# 4a''. the sampling sequencer against its own deck, by that block's checker
python3 ../sample_seq/check_sch.py ../sample_seq/sample_seq.spice "$GEN" \
    | sed 's/^\(PASS\|FAIL\): schematic: /\1: schematic: analog_top.spice vs ..\/sample_seq\/sample_seq.spice: /'
# 4b'. the latch: one standard-cell instance, equal to ../latch/latch.spice
red_scff() {
    awk '{ l = $0; sub(/^\*+/, "", l); nt = split(tolower(l), t, /[ \t]+/) }
         t[1] == ".subckt" { s = "ports:"; for (i = 3; i <= nt; i++) if (t[i] != "") s = s " " t[i]; print s }
         t[1] ~ /^x/ { s = "inst:"; for (i = 2; i <= nt; i++) if (t[i] != "") s = s " " t[i]; print s }' "$1"
}
getsub latch ../latch/latch.spice > work/sch/ref_latch.spice
getsub latch "$GEN" > work/sch/cut_latch.spice
red_scff work/sch/ref_latch.spice > work/sch/ref_latch.red
red_scff work/sch/cut_latch.spice > work/sch/cut_latch.red
if [ -s work/sch/cut_latch.red ] && cmp -s work/sch/ref_latch.red work/sch/cut_latch.red; then
    echo "PASS: schematic: analog_top.spice subckt latch (latch.sch) equals ../latch/latch.spice: $(tr '\n' ';' < work/sch/cut_latch.red)"
else
    echo "FAIL: schematic: analog_top.spice subckt latch differs from ../latch/latch.spice: deck [$(tr '\n' ';' < work/sch/ref_latch.red)] generated [$(tr '\n' ';' < work/sch/cut_latch.red)]"
fi

# 4c. no plate leak resistor and no parameter reference in the real macro
nleak=$(grep -v '^\*' analog_top.spice | grep -c -i -E '1e15|1e\+15|^[ \t]*RLK')
ncmt=$(grep -c -i '1e15' analog_top.spice)
if [ "$nleak" = 0 ]; then
    echo "PASS: schematic: analog_top.spice has no plate leak resistor (no RLK instance, no 1e15 value; $ncmt comment line(s) name the testbench's rshunt)"
else
    echo "FAIL: schematic: analog_top.spice carries $nleak line(s) with RLK / 1e15"
fi
grep -q -i '^\.options rshunt=1e15' tb_analog_top.spice \
    && echo "PASS: schematic: tb_analog_top.spice carries the simulation aid .options rshunt=1e15" \
    || echo "FAIL: schematic: tb_analog_top.spice has no .options rshunt=1e15 (the floating plates need a DC path)"
nbrace=$(grep -v '^\*' analog_top.spice | grep -c '[{}]')
if [ "$nbrace" = 0 ]; then
    echo "PASS: schematic: analog_top.spice has no parameter reference ({...}): every W / L / nf / C size is a number (the S/D geometry expressions are the PDK templates)"
else
    echo "FAIL: schematic: analog_top.spice has $nbrace device line(s) with a {parameter} reference: $(grep -v '^\*' analog_top.spice | grep '[{}]' | head -2 | tr '\n' ' ')"
fi

# 4d. the macro is v6's with the sequencer inside, nothing else
if [ -s "$V6REF" ]; then
    python3 check_equiv.py "$V6REF" "$GEN"
    echo "REPORT: schematic: equiv: compared against the frozen v6 netlist $V6REF (the v6 folder is archived in ../Analog_top_bkp/Analog_top_v6)"
else
    echo "FAIL: schematic: $V6REF absent: no v6 netlist to compare with"
fi

# 4e. definitions
subnames "$GEN" | sort > work/sch/gen_defs.txt
xrefs "$GEN" > work/sch/gen_refs.txt
ncards=$(grep -c -i -E '^[ \t]*\.(include|lib|param|model|option)' "$GEN")
awk -v defs=work/sch/gen_defs.txt -v expect="$EXPECT" -v ncards="$ncards" '
    BEGIN { while ((getline n < defs) > 0) { cnt[n]++; nd++ }
            ne = split(expect, e, " "); for (i = 1; i <= ne; i++) want[e[i]] = 1 }
    $1 ~ /^(nfet_|pfet_|cap_mim|ppolyf_|npolyf_|gf180mcu_as_sc_mcu7t3v3__)/ { next }
    { nr++; if (!($1 in cnt)) miss = miss " " $1 }
    END { for (n in cnt) { if (cnt[n] > 1) dup = dup " " n; if (!(n in want)) extra = extra " " n }
          for (n in want) if (!(n in cnt)) absent = absent " " n
          if (dup == "" && miss == "" && extra == "" && absent == "" && ncards == 0)
              printf "PASS: schematic: analog_top.spice defines %d subcircuits (%s), each once; all %d referenced are defined; no model / parameter card\n", nd, expect, nr
          else
              printf "FAIL: schematic: analog_top.spice subcircuits twice [%s ] / undefined [%s ] / unexpected [%s ] / absent [%s ], %d model or parameter cards\n", dup, miss, extra, absent, ncards }' \
    work/sch/gen_refs.txt

# --------------------------------------------------------------- 5. testbench
rm -f work/sch/tb_analog_top.spice
xschem --rcfile "$RC" -b -q -n -s -o work/sch tb_analog_top.sch > work/sch/tb_analog_top_xschem.txt 2>&1
if [ -s work/sch/tb_analog_top.spice ]; then
    tb=work/sch/tb_analog_top.spice
    toplevel tb_analog_top.spice > work/sch/ref_tb_top.spice
    toplevel "$tb" > work/sch/cut_tb_top.spice
    awk -v mode=tb -v replaced="analog_top.spice" \
        -v label="tb_analog_top.sch vs tb_analog_top.spice (top level)" \
        -f check-schematic.awk work/sch/ref_tb_top.spice work/sch/cut_tb_top.spice
    # every subcircuit the tb hierarchy emits = analog_top.spice's
    nok=0; nbad=0; bads=""
    for s in $(subnames "$tb"); do
        getsub "$s" "$GEN" > "work/sch/ref_tbh_$s.spice"
        getsub "$s" "$tb" > "work/sch/cut_tbh_$s.spice"
        if [ ! -s "work/sch/ref_tbh_$s.spice" ]; then
            nbad=$((nbad + 1)); bads="$bads $s(not in analog_top.spice)"; continue
        fi
        if awk -v label="tb hierarchy subckt $s vs analog_top.spice" -f check-schematic.awk \
               "work/sch/ref_tbh_$s.spice" "work/sch/cut_tbh_$s.spice" > "work/sch/tbh_$s.txt"; then
            nok=$((nok + 1))
        else
            nbad=$((nbad + 1)); bads="$bads $s"; grep '^REPORT' "work/sch/tbh_$s.txt"
        fi
    done
    if [ "$nbad" = 0 ] && [ "$nok" -gt 0 ]; then
        echo "PASS: schematic: tb_analog_top.sch hierarchy: $nok subcircuits, each equal to analog_top.spice's (ports, instances, parameters)"
    else
        echo "FAIL: schematic: tb_analog_top.sch hierarchy: $nbad subcircuit(s) differ from analog_top.spice:$bads"
    fi
    { subnames "$tb"
      for f in $(awk 'tolower($1) == ".include" && $2 !~ /^\/foss\/pdks/ { print $2 }' "$tb"); do
          [ -f "$f" ] && subnames "$f"
      done; } | sort > work/sch/tb_defs.txt
    xrefs "$tb" > work/sch/tb_refs.txt
    awk -v defs=work/sch/tb_defs.txt '
        BEGIN { while ((getline n < defs) > 0) { cnt[n]++; nd++ } }
        $1 ~ /^(nfet_|pfet_|cap_mim|ppolyf_|npolyf_)/ { next }
        { nr++; if (!($1 in cnt)) miss = miss " " $1 }
        END { for (n in cnt) if (cnt[n] > 1) dup = dup " " n
              if (dup == "" && miss == "")
                  printf "PASS: schematic: tb netlist defines %d subcircuits (hierarchy + included decks), each once; all %d referenced are defined\n", nd, nr
              else
                  printf "FAIL: schematic: tb netlist subcircuits defined twice [%s ] / missing [%s ]\n", dup, miss }' \
        work/sch/tb_refs.txt
else
    echo "FAIL: schematic: xschem produced no netlist for tb_analog_top.sch"
fi

# ------------------------------------------------------------------ 6. render
sh render.sh
exit 0
