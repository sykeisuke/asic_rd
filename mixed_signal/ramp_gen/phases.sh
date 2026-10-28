#!/bin/bash
# phases.sh -- the ramp_gen flow, inside the pinned container (run.sh calls it).
#
#   PHASES   subset of: size schematic ramp loop noise trannoise adc4 simple compare plot check
#   JOBS     parallel ngspice runs in the adc4 phase
#
# Every phase prints `name = value`, PASS:/FAIL: and REPORT: lines only; the
# simulator output stays in work/. Each phase's lines are also kept in
# work/ph_<phase>.txt; the check phase reads them (work/phases_out.txt).
set -uo pipefail
cd /foss/designs/mixed_signal/ramp_gen
PHASES=${PHASES:-'size schematic ramp loop noise trannoise adc4 simple compare plot check'}
JOBS=${JOBS:-16}
has() { case " $PHASES " in *" $1 "*) return 0;; *) return 1;; esac; }
mkdir -p work data assets
: > work/phases_out.txt
run_phase() {
    has "$1" || return 0
    "ph_$1" > "work/ph_$1.txt" 2>&1
    cat "work/ph_$1.txt" | tee -a work/phases_out.txt
}

# the loop-break copy every small-signal bench uses (vx and XM1's gate as ports)
sed -e 's/^\.subckt ramp_gen vramp rst vrlo pbias vdd vss$/.subckt ramp_gen_lb vramp rst vrlo pbias vdd vss vx vxg/' \
    -e 's/^\.ends ramp_gen$/.ends ramp_gen_lb/' \
    -e 's/^XM1 d1 vx tail /XM1 d1 vxg tail /' ramp_gen.spice > work/ramp_gen_lb.spice
grep -q "^XM1 d1 vxg tail" work/ramp_gen_lb.spice || echo "FAIL: loop-break copy of ramp_gen.spice not made"

# ------------------------------------------------------------------ size
# the sizer re-derives every size into work/size and must reproduce data/
ph_size() {
    RG_OUT=work/size python3 size_ramp.py > work/size.txt 2>&1
    grep -E "^(size_|REPORT|FAIL)" work/size.txt
    if diff -q <(grep -v '^\*' work/size/ramp_gen_params.spice) <(grep -v '^\*' data/ramp_gen_params.spice) >/dev/null; then
        echo "PASS: size_ramp.py reproduces data/ramp_gen_params.spice"
    else
        echo "FAIL: size_ramp.py output differs from data/ramp_gen_params.spice (re-run the sizer and review)"
    fi
}

# ------------------------------------------------------------- schematic
ph_schematic() {
    RC=/foss/designs/mixed_signal/ramp_gen/xschemrc
    rm -f work/ramp_gen.spice work/ramp_gen_sch.spice work/tb_ramp_adc4.spice
    xschem --rcfile "$RC" -b -q -n -s -o work ramp_gen.sch > work/xschem_ramp_gen.txt 2>&1
    if [ -s work/ramp_gen.spice ]; then
        mv work/ramp_gen.spice work/ramp_gen_sch.spice
        awk -f check-schematic.awk ramp_gen.spice work/ramp_gen_sch.spice
    else
        echo "FAIL: xschem produced no netlist for ramp_gen.sch"
    fi
    xschem --rcfile "$RC" -b -q -n -s -o work tb_ramp_adc4.sch > work/xschem_tb.txt 2>&1
    if [ -s work/tb_ramp_adc4.spice ]; then
        n=$(grep -c -E "^XC[0-3] .* cell_bps$" work/tb_ramp_adc4.spice)
        r=$(grep -c -E "^XRG vramp rst vrlo pbias_r vdd_ramp 0 ramp_gen$" work/tb_ramp_adc4.spice)
        s=$(grep -c "^\.subckt ramp_gen " work/tb_ramp_adc4.spice)
        c=$(grep -c "^XCMP " work/tb_ramp_adc4.spice); w=$(grep -c -E "^XS[012] " work/tb_ramp_adc4.spice)
        if [ "$c" = 1 ] && [ "$w" = 3 ]; then
            echo "PASS: tb_ramp_adc4.sch netlist has the cell's comparator and three switches (cell_bps symbols resolved)"
        else
            echo "FAIL: tb_ramp_adc4.sch netlist: $c XCMP and $w switch lines in cell_bps (symbols not found?)"
        fi
        if [ "$n" = 4 ] && [ "$r" = 1 ] && [ "$s" = 1 ]; then
            echo "PASS: tb_ramp_adc4.sch netlists: XRG (ramp_gen from ramp_gen.sch) and four cell_bps cells"
        else
            echo "FAIL: tb_ramp_adc4.sch netlist: $n cells, $r XRG lines, $s ramp_gen subcircuits"
        fi
    else
        echo "FAIL: xschem produced no netlist for tb_ramp_adc4.sch"
    fi
    for f in ramp_gen tb_ramp_adc4; do
        rm -f assets/${f}_xschem.png
        timeout 120 xvfb-run -a xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
            --command "xschem zoom_full; xschem print png assets/${f}_xschem.png 2400 1400; xschem exit closewindow force" \
            $f.sch > work/xschem_print_$f.txt 2>&1
        if [ -s assets/${f}_xschem.png ]; then echo "PASS: xschem render assets/${f}_xschem.png"
        else echo "REPORT: xschem render of $f.sch not produced (headless print)"; fi
    done
}

# ------------------------------------------------------------------ ramp
# the ramp alone on the real bias generator; case "tag NCELL VKICK VDDX TPRE"
run_ramp() {
    d=work/ramp_$1; rm -rf $d; mkdir -p $d
    printf ".param NCELL=%s\n.param VKICK=%s\n.param VDDX=%s\n.param TPRE=%s\n" $2 $3 $4 $5 > $d/case.spice
    ( cd $d && ngspice -b ../../${RAMP_TB:-tb_ramp.spice} > out.txt 2>&1 )
    grep -E "^[a-z_0-9]+ +=" $d/out.txt | sed -E "s/^([a-z_0-9]+) += +([-+0-9.e]+).*/$1_\1 = \2/" > $d/meas.txt
    [ -s $d/meas.txt ] || echo "FAIL: tb_ramp case $1 produced no measures"
    python3 reduce_ramp.py $d $1 > $d/red.txt 2>&1 || echo "FAIL: reduce_ramp.py case $1"
}
export -f run_ramp
ph_ramp() {
    printf '%s\n' "nom 4 2.0 1 0" "nokick 4 0.5 1 0" "vlo 4 2.0 0.98 0" "vhi 4 2.0 1.02 0" \
        "n16 16 2.0 1 0" "n64 64 2.0 1 0" "pre 4 2.0 1 300n" > work/ramp_cases.txt
    xargs -P 7 -L 1 bash -c 'run_ramp "$@"' _ < work/ramp_cases.txt
    for c in nom nokick vlo vhi n16 n64 pre; do cat work/ramp_$c/meas.txt work/ramp_$c/red.txt; done
}

# ------------------------------------------------------------------ loop
ph_loop() {
    for c in "rst 1 0.5 4" "r0p5 0 0.5 4" "r1p25 0 1.25 4" "r2p1 0 2.1 4" "n64rst 1 0.5 64"; do
        set -- $c
        d=work/loop_$1; mkdir -p $d
        printf ".param MODE=%s\n.param VOP=%s\n.param NCELL=%s\n" $2 $3 $4 > $d/case.spice
        ( cd $d && ngspice -b ../../tb_loop.spice > out.txt 2>&1 )
        python3 reduce_loop.py $d loop_$1 || echo "FAIL: loop case $1 not reduced"
    done
}

# ----------------------------------------------------------------- noise
ph_noise() {
    python3 noise_bench.py > work/noise.txt 2>&1
    grep -E "^(noise_|REPORT|FAIL)" work/noise.txt
    [ -s data/noise_breakdown.csv ] || echo "FAIL: noise_bench.py wrote no data/noise_breakdown.csv"
}

# ------------------------------------------------------------- trannoise
# VACASK transient noise, group by group, against the kernel (trannoise/, ~18 min)
ph_trannoise() {
    JOBS=12 bash trannoise/run.sh
}

# ------------------------------------------------------------------ adc4
run_adc4() {   # set tag real tpre p0 p1 p2 p3
    d=work/adc4_$2; rm -rf $d; mkdir -p $d
    printf ".param POS0=%s\n.param POS1=%s\n.param POS2=%s\n.param POS3=%s\n.param RAMP_REAL=%s\n.param TPRE=%s\n.param VRLO_TRIM=0\n" \
        $5 $6 $7 $8 $3 $4 > $d/case.spice
    ( cd $d && ngspice -b ../${ADC4_TB:-tb_ramp_adc4.spice} > out.txt 2>&1 )
    grep -E "^[a-z_0-9]+ +=" $d/out.txt > $d/measures.txt
    grep -q "^err3 " $d/measures.txt || echo "FAIL: adc4 run $2 incomplete ($(grep -c . $d/measures.txt) measures; first error: $(grep -m1 -i -E "^error|timestep too small|aborted" $d/out.txt | cut -c1-120))"
}
export -f run_adc4
adc4_cases() {   # the four-cell case list, shared by ramp_gen and the simple ramp
    {
        echo "show s_r 1 0 16.5 80.5 160.5 240.5"
        echo "show s_i 0 0 16.5 80.5 160.5 240.5"
        for r in 0 1 2 3 4 5 6 7; do
            p="$((4 + 8 * r)).5 $((68 + 8 * r)).5 $((132 + 8 * r)).5 $((196 + 8 * r)).5"
            echo "coarse c${r}_r 1 0 $p"; echo "coarse c${r}_i 0 0 $p"
            echo "pre p${r}_r 1 300e-9 $p"
        done
        echo "fine f_r 1 0 127.125 127.375 127.625 127.875"
        echo "fine f_i 0 0 127.125 127.375 127.625 127.875"
        echo "low l_r 1 0 1.5 2.5 3.5 5.5"
        echo "low l_i 0 0 1.5 2.5 3.5 5.5"
        for d in 0.25 1 4 16; do
            dn=$(awk -v d=$d 'BEGIN{printf "%g", 128.5 - d}'); up=$(awk -v d=$d 'BEGIN{printf "%g", 128.5 + d}')
            t=$(echo $d | tr . p)
            echo "xt xtm$t 1 0 128.5 $dn $dn $dn"; echo "xt xtp$t 1 0 128.5 $up $up $up"
            echo "xti xtim$t 0 0 128.5 $dn $dn $dn"; echo "xti xtip$t 0 0 128.5 $up $up $up"
        done
        echo "xc x0 1 0 5.5 20.5 0.5 0.5"
        echo "xc x1 1 0 5.5 20.5 254.5 254.5"
    }
}
ph_adc4() {
    adc4_cases > data/adc4_cases.txt
    if [ ! -s work/tb_ramp_adc4.spice ]; then
        echo "FAIL: adc4 needs the schematic phase (work/tb_ramp_adc4.spice)"; return
    fi
    xargs -P "$JOBS" -L 1 bash -c 'run_adc4 "$@"' _ < data/adc4_cases.txt
    python3 reduce_adc4.py data/adc4_cases.txt || echo "FAIL: reduce_adc4.py"
}

# ---------------------------------------------------------------- simple
# the comparison baseline ramp_simple (current source + C + switch) through the
# same benches: sizing, schematic, ramp alone, noise, the four-cell set
ph_simple() {
    RC=/foss/designs/mixed_signal/ramp_gen/xschemrc
    RS_OUT=work/size_simple python3 size_simple.py > work/size_simple.txt 2>&1
    grep -E "^(simple_size_|REPORT|FAIL)" work/size_simple.txt
    if diff -q <(grep -v '^\*' work/size_simple/ramp_simple_params.spice) <(grep -v '^\*' data/ramp_simple_params.spice) >/dev/null; then
        echo "PASS: size_simple.py reproduces data/ramp_simple_params.spice"
    else
        echo "FAIL: size_simple.py output differs from data/ramp_simple_params.spice"
    fi
    rm -f work/ramp_simple.spice work/tb_ramp_simple_adc4.spice
    xschem --rcfile "$RC" -b -q -n -s -o work ramp_simple.sch > work/xschem_ramp_simple.txt 2>&1
    if [ -s work/ramp_simple.spice ]; then
        mv work/ramp_simple.spice work/ramp_simple_sch.spice
        awk -v sub_=ramp_simple -f check-schematic.awk ramp_simple.spice work/ramp_simple_sch.spice
    else
        echo "FAIL: xschem produced no netlist for ramp_simple.sch"
    fi
    xschem --rcfile "$RC" -b -q -n -s -o work tb_ramp_simple_adc4.sch > work/xschem_tb_simple.txt 2>&1
    n=$(grep -c "^XRG vramp rst vrlo pbias_r vdd_ramp 0 ramp_simple$" work/tb_ramp_simple_adc4.spice 2>/dev/null)
    c=$(grep -c "^XCMP " work/tb_ramp_simple_adc4.spice 2>/dev/null)
    if [ "$n" = 1 ] && [ "$c" = 1 ]; then echo "PASS: tb_ramp_simple_adc4.sch netlists: XRG = ramp_simple on its own bias, four cell_bps cells"
    else echo "FAIL: tb_ramp_simple_adc4.sch netlist ($n XRG, $c XCMP)"; fi
    for f in ramp_simple tb_ramp_simple_adc4; do
        rm -f assets/${f}_xschem.png
        timeout 120 xvfb-run -a xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
            --command "xschem zoom_full; xschem print png assets/${f}_xschem.png 2400 1400; xschem exit closewindow force" \
            $f.sch > work/xschem_print_$f.txt 2>&1
        [ -s assets/${f}_xschem.png ] && echo "PASS: xschem render assets/${f}_xschem.png"
    done
    printf '%s\n' "simple_nom 4 2.0 1 0" "simple_nokick 4 0.5 1 0" "simple_vlo 4 2.0 0.98 0" "simple_vhi 4 2.0 1.02 0" \
        "simple_n16 16 2.0 1 0" "simple_n64 64 2.0 1 0" "simple_pre 4 2.0 1 300n" > work/ramp_simple_cases.txt
    RAMP_TB=tb_ramp_simple.spice xargs -P 7 -L 1 bash -c 'run_ramp "$@"' _ < work/ramp_simple_cases.txt
    for c in nom nokick vlo vhi n16 n64 pre; do cat work/ramp_simple_$c/meas.txt work/ramp_simple_$c/red.txt; done
    python3 noise_simple.py > work/noise_simple.txt 2>&1
    grep -E "^(simple_noise_|REPORT|FAIL)" work/noise_simple.txt
    adc4_cases | awk '{ $2 = "S" $2; print }' > data/adc4s_cases.txt
    if [ ! -s work/tb_ramp_simple_adc4.spice ]; then echo "FAIL: no simple four-cell netlist"; return; fi
    ADC4_TB=tb_ramp_simple_adc4.spice xargs -P "$JOBS" -L 1 bash -c 'run_adc4 "$@"' _ < data/adc4s_cases.txt
    ADC4_PREFIX=simple_ python3 reduce_adc4.py data/adc4s_cases.txt || echo "FAIL: reduce_adc4.py (simple)"
}

# --------------------------------------------------------------- compare
ph_compare() {
    python3 compare_ramps.py work/ph_*.txt || echo "FAIL: compare_ramps.py"
}

# ------------------------------------------------------------------ plot
ph_plot() {
    python3 plot_ramp.py || echo "FAIL: plot_ramp.py"
}

for p in size schematic ramp loop noise trannoise adc4 simple compare plot; do run_phase $p; done

# ----------------------------------------------------------------- check
if has check; then
    awk -f check-ramp.awk work/phases_out.txt
fi
exit 0
