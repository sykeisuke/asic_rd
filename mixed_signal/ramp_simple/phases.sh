#!/bin/bash
# phases.sh -- the ramp_simple flow, inside the pinned container (run.sh calls it).
#
#   PHASES   subset of: size schematic ramp pvt adc4 plot check
#   JOBS     parallel ngspice runs
#
# Every phase prints `name = value`, PASS:/FAIL: and REPORT: lines only; the
# simulator output stays in work/. Each phase's lines are also kept in
# work/ph_<phase>.txt; the check phase reads them all (work/phases_out.txt).
set -uo pipefail
cd /foss/designs/mixed_signal/ramp_simple
PHASES=${PHASES:-'size schematic ramp pvt adc4 src plot check'}
JOBS=${JOBS:-16}
export JOBS
has() { case " $PHASES " in *" $1 "*) return 0;; *) return 1;; esac; }
mkdir -p work data assets
printf 'set num_threads=1\n' > work/.spiceinit
: > work/phases_out.txt
run_phase() {
    # a phase not selected contributes its LAST lines (work/ph_<phase>.txt), so a partial
    # run re-judges the rest from cache; the check phase sees which phases ran this time
    if ! has "$1"; then
        if [ -s "work/ph_$1.txt" ]; then
            echo "REPORT: phase $1 not run this time; its lines re-used from the previous run" | tee -a work/phases_out.txt
            grep -v '^REPORT: phase .* re-used' "work/ph_$1.txt" | tee -a work/phases_out.txt
        fi
        return 0
    fi
    if declare -F "ph_$1" > /dev/null; then
        "ph_$1" > "work/ph_$1.txt" 2>&1
    else
        echo "REPORT: phase $1 is not implemented yet" > "work/ph_$1.txt"
    fi
    cat "work/ph_$1.txt" | tee -a work/phases_out.txt
}

# ------------------------------------------------------------------ size
# the sizer re-derives every size into work/size and must reproduce the
# controlled netlist and sizing record
ph_size() {
    rm -rf work/size; mkdir -p work/size; cp work/.spiceinit work/size/
    RS_OUT=work/size python3 size_simple.py > work/size/size.txt 2>&1 || echo "FAIL: size_simple.py exited with an error (work/size/size.txt)"
    grep -E "^(size_|REPORT|FAIL|PASS)" work/size/size.txt
    if [ -s work/size/ramp_simple.spice ] && diff -q <(grep -v '^\*' work/size/ramp_simple.spice) <(grep -v '^\*' ramp_simple.spice) >/dev/null; then
        echo "PASS: size_simple.py reproduces ramp_simple.spice (every device line)"
    else
        echo "FAIL: size_simple.py output differs from ramp_simple.spice (re-run the sizer and review: cp work/size/ramp_simple.spice . and data/sizing.json)"
    fi
}

# ------------------------------------------------------------- schematic
# the cell drawing netlists back to the deck; the testbench drawing holds the
# cell, the ideal ramp current and the sources of the `level` case; both rendered
ph_schematic() {
    RC=/foss/designs/mixed_signal/ramp_simple/xschemrc
    python3 ramp_simple_sch.py || { echo "FAIL: ramp_simple_sch.py"; return; }
    rm -f work/ramp_simple.spice work/ramp_simple_sch.spice work/tb_ramp.spice
    xschem --rcfile "$RC" -b -q -n -s -o work ramp_simple.sch > work/xschem_ramp_simple.txt 2>&1
    if [ -s work/ramp_simple.spice ]; then
        mv work/ramp_simple.spice work/ramp_simple_sch.spice
        awk -v sub_=ramp_simple -f check-schematic.awk ramp_simple.spice work/ramp_simple_sch.spice
    else
        echo "FAIL: xschem produced no netlist for ramp_simple.sch"
    fi
    xschem --rcfile "$RC" -b -q -n -s -o work tb_ramp.sch > work/xschem_tb.txt 2>&1
    if [ -s work/tb_ramp.spice ]; then
        n=$(grep -c -E "^XRG .* ramp_simple$" work/tb_ramp.spice); i=$(grep -c -i "^IRAMP " work/tb_ramp.spice)
        s=$(grep -c "^\.subckt ramp_simple " work/tb_ramp.spice); v=$(grep -c -i -E "^V(RST|RLO|DD_SOURCE) " work/tb_ramp.spice)
        if [ "$n" = 1 ] && [ "$i" = 1 ] && [ "$s" = 1 ] && [ "$v" = 3 ]; then
            echo "PASS: tb_ramp.sch netlists: the cell (from ramp_simple.sch), the ideal ramp current, VDD / VRLO / VRST"
        else
            echo "FAIL: tb_ramp.sch netlist: $n cell, $i IRAMP, $s subcircuit, $v sources"
        fi
    else
        echo "FAIL: xschem produced no netlist for tb_ramp.sch"
    fi
    for f in ramp_simple tb_ramp; do
        rm -f assets/${f}_xschem.png
        timeout 120 xvfb-run -a xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
            --command "xschem zoom_full; xschem print png assets/${f}_xschem.png 2400 1400; xschem exit closewindow force" \
            $f.sch > work/xschem_print_$f.txt 2>&1
        if [ -s assets/${f}_xschem.png ]; then echo "PASS: xschem render assets/${f}_xschem.png"
        else echo "REPORT: xschem render of $f.sch not produced (headless print)"; fi
    done
}

# ------------------------------------------------------------------ ramp
# the ramp alone (tb_ramp.py): one run per case line "tag KEY=VAL ..."
run_ramp() {
    tag=$1; shift
    d=work/ramp_$tag; rm -rf "$d"; mkdir -p "$d"; cp work/.spiceinit "$d/"
    python3 tb_ramp.py "$d" "$@" || { echo "FAIL: tb_ramp.py $tag"; return; }
    ( cd "$d" && ngspice -b tb.spice > out.txt 2>&1 )
    grep -E "^[a-z_0-9]+ +=" "$d/out.txt" | sed -E "s/^([a-z_0-9]+) += +([-+0-9.e]+).*/${tag}_\1 = \2/" > "$d/meas.txt"
    [ -s "$d/ramp.csv" ] || { echo "FAIL: tb_ramp case $tag wrote no ramp.csv ($(grep -m1 -i -E 'error|timestep too small' "$d/out.txt" | cut -c1-120))"; return; }
    python3 reduce_ramp.py "$d" "$tag" > "$d/red.txt" 2>&1 || echo "FAIL: reduce_ramp.py case $tag: $(tail -1 "$d/red.txt" | cut -c1-120)"
}
export -f run_ramp
ph_ramp() {
    printf '%s\n' "nom" "level VRLO=ideal" "nokick VKICK=0" "n16 NCELL=16" "n64 NCELL=64" \
        "kick KICK3=1 VRLO=ideal" "islow I=0.98 VRLO=ideal" "ifast I=1.10 VRLO=ideal" \
        "mimss MIM=ss VRLO=ideal" "mimff MIM=ff VRLO=ideal" > work/ramp_cases.txt
    xargs -P "$JOBS" -L 1 bash -c 'run_ramp "$@"' _ < work/ramp_cases.txt
    for c in $(cut -d' ' -f1 work/ramp_cases.txt); do
        [ -f "work/ramp_$c/meas.txt" ] && cat "work/ramp_$c/meas.txt"
        [ -f "work/ramp_$c/red.txt" ] && cat "work/ramp_$c/red.txt"
    done
}

# ------------------------------------------------------------------- pvt
# 45 cells x MIM typical / ss / ff, the design current from an ideal source,
# ideal VR_LO at the pre-roll level, 4 cells of load and S1 charge
ph_pvt() {
    rm -rf work/ramp_pvt_*
    python3 - > work/pvt_cases.txt <<'EOF'
import rs_common as rs
for c in rs.CORNERS:
    for t in rs.TEMPS:
        for v in rs.VDDS:
            for m in rs.MIMS:
                print("pvt_%s_%gc_%sv_%s CORNER=%s TEMP=%g VDDX=%.6f MIM=%s VRLO=ideal"
                      % (c, t, str(v).replace(".", "p"), m, c, t, v / 3.3, m))
EOF
    echo "pvt_cases_planned = $(grep -c . work/pvt_cases.txt)"
    xargs -P "$JOBS" -L 1 bash -c 'run_ramp "$@"' _ < work/pvt_cases.txt
    python3 pvt_reduce.py || echo "FAIL: pvt_reduce.py"
}

# ------------------------------------------------------------------ adc4
# four real cells on the ramp, the macro's own bench (adc4.py): the cell with an
# ideal current vs an ideal ramp, the 0.5 V level of vrlo_ref and the pre-roll
# level; case line "kind tag KEY=VAL ..."
run_adc4() {
    kind=$1; tag=$2; shift 2
    d=work/adc4/$tag; rm -rf "$d"; mkdir -p "$d"
    python3 adc4.py gen "$d" "$@" || { echo "FAIL: adc4.py gen $tag"; return; }
    ( cd "$d" && ngspice -b tb.spice > out.txt 2>&1 )
    awk '/^[a-z_][a-z_0-9]* +=/ { v = $3; sub(/^\+/, "", v); print $1 " = " v }' "$d/out.txt" > "$d/meas.txt"
    grep -q "^code3 " "$d/meas.txt" || echo "FAIL: adc4 run $tag incomplete ($(grep -c . "$d/meas.txt") measures; $(grep -m1 -i -E "^error|timestep too small|aborted" "$d/out.txt" | cut -c1-120))"
    case $tag in show*) ;; *) rm -f "$d/wave.csv";; esac
}
export -f run_adc4
adc4_cases() {
    echo "show show_r REAL=1 LEVEL=real POS0=16.5 POS1=80.5 POS2=160.5 POS3=240.5"
    echo "show show_i REAL=0 LEVEL=real POS0=16.5 POS1=80.5 POS2=160.5 POS3=240.5"
    # the pre-roll level: VIN = 0.503 / 1.0 / 1.5 / 1.995 V, the whole 0.5-2.0 V window (ADR 0025)
    p=$(python3 -c "import rs_common as rs; print(' '.join('POS%d=%.4f' % (i, (v - rs.VR_LO_TAP) / rs.LSB) for i, v in enumerate((0.5 + 0.5 * rs.LSB, 1.0, 1.5, 2.0 - 0.5 * rs.LSB))))")
    echo "showp showp_r REAL=1 LEVEL=ideal $p"
    echo "showp showp_i REAL=0 LEVEL=ideal $p"
    echo "lowp lowp_r REAL=1 LEVEL=ideal POS0=0.5 POS1=1.5 POS2=2.5 POS3=4.5"
    echo "lowp lowp_i REAL=0 LEVEL=ideal POS0=0.5 POS1=1.5 POS2=2.5 POS3=4.5"
    for r in 0 1 2 3 4 5 6 7; do
        p="POS0=$((4 + 8 * r)).5 POS1=$((68 + 8 * r)).5 POS2=$((132 + 8 * r)).5 POS3=$((196 + 8 * r)).5"
        echo "coarse c${r}_r REAL=1 LEVEL=real $p"; echo "coarse c${r}_i REAL=0 LEVEL=real $p"
    done
    echo "fine fine_r REAL=1 LEVEL=real POS0=127.125 POS1=127.375 POS2=127.625 POS3=127.875"
    echo "fine fine_i REAL=0 LEVEL=real POS0=127.125 POS1=127.375 POS2=127.625 POS3=127.875"
    echo "low low_r REAL=1 LEVEL=real POS0=1.5 POS1=2.5 POS2=3.5 POS3=5.5"
    echo "low low_i REAL=0 LEVEL=real POS0=1.5 POS1=2.5 POS2=3.5 POS3=5.5"
    for dd in 0.25 1 4 16 24 32 64; do
        dn=$(awk -v d=$dd 'BEGIN{printf "%g", 128.5 - d}'); up=$(awk -v d=$dd 'BEGIN{printf "%g", 128.5 + d}')
        t=$(echo $dd | tr . p)
        echo "xt xtm${t}_r REAL=1 LEVEL=real POS0=128.5 POS1=$dn POS2=$dn POS3=$dn"
        echo "xt xtp${t}_r REAL=1 LEVEL=real POS0=128.5 POS1=$up POS2=$up POS3=$up"
        echo "xt xtm${t}_i REAL=0 LEVEL=real POS0=128.5 POS1=$dn POS2=$dn POS3=$dn"
        echo "xt xtp${t}_i REAL=0 LEVEL=real POS0=128.5 POS1=$up POS2=$up POS3=$up"
    done
    echo "xc x0_r REAL=1 LEVEL=real POS0=5.5 POS1=20.5 POS2=0.5 POS3=0.5"
    echo "xc x1_r REAL=1 LEVEL=real POS0=5.5 POS1=20.5 POS2=254.5 POS3=254.5"
}
ph_adc4() {
    adc4_cases > data/adc4_cases.txt
    rm -rf work/adc4; mkdir -p work/adc4
    xargs -P "$JOBS" -L 1 bash -c 'run_adc4 "$@"' _ < data/adc4_cases.txt
    python3 adc4.py reduce data/adc4_cases.txt || echo "FAIL: adc4.py reduce"
}

# ------------------------------------------------------------------- src
# the ramp on the REAL I/C source (../ic_source, ADR 0025 step 3): the same macro
# bench, the pre-roll level (an ideal 7/55 AVDD source: the macro's own vrlo_ref
# is still the 0.5 V one until integration), T0 = 60 us for the source's start;
# every real-source case (_s) has an ideal-ramp twin (_pi) with the same T0
src_cases() {
    p=$(python3 -c "import rs_common as rs; print(' '.join('POS%d=%.4f' % (i, (v - rs.VR_LO_TAP) / rs.LSB) for i, v in enumerate((0.5 + 0.5 * rs.LSB, 1.0, 1.5, 2.0 - 0.5 * rs.LSB))))")
    echo "showp showp_s REAL=1 SRC=ic LEVEL=ideal $p"
    echo "lowp lowp_s REAL=1 SRC=ic LEVEL=ideal POS0=0.5 POS1=1.5 POS2=2.5 POS3=4.5"
    for r in 0 1 2 3 4 5 6 7; do
        q="POS0=$((4 + 8 * r)).5 POS1=$((68 + 8 * r)).5 POS2=$((132 + 8 * r)).5 POS3=$((196 + 8 * r)).5"
        echo "coarse c${r}_s REAL=1 SRC=ic LEVEL=ideal $q"; echo "coarse c${r}_pi REAL=0 LEVEL=ideal T0=60u $q"
    done
    echo "fine fine_s REAL=1 SRC=ic LEVEL=ideal POS0=127.125 POS1=127.375 POS2=127.625 POS3=127.875"
    for pol in m p; do
        a=$([ $pol = m ] && echo 104.5 || echo 152.5)
        echo "xt xt${pol}24_s REAL=1 SRC=ic LEVEL=ideal POS0=128.5 POS1=$a POS2=$a POS3=$a"
        echo "xt xt${pol}24_pi REAL=0 LEVEL=ideal T0=60u POS0=128.5 POS1=$a POS2=$a POS3=$a"
    done
}
ph_src() {
    src_cases > data/src_cases.txt
    mkdir -p work/adc4
    xargs -P "$JOBS" -L 1 bash -c 'run_adc4 "$@"' _ < data/src_cases.txt
    python3 adc4.py reduce data/src_cases.txt | sed 's/^adc4_cases =/src_cases =/; s/^adc4_missing =/src_missing =/' || echo "FAIL: adc4.py reduce (src)"
}

# ------------------------------------------------------------------ plot
ph_plot() { python3 plot_ramp.py || echo "FAIL: plot_ramp.py"; }

for p in size schematic ramp pvt adc4 src plot; do run_phase $p; done

# ----------------------------------------------------------------- check
if has check; then
    awk -f check-ramp.awk work/phases_out.txt
fi
exit 0
