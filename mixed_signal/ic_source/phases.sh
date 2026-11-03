#!/bin/bash
# phases.sh -- the ic_source flow, inside the pinned container (run.sh calls it).
#
#   PHASES   subset of: lut size schematic op loop noise pvt mc plot check
#   JOBS     parallel ngspice runs
#
# Every phase prints `name = value`, PASS:/FAIL: and REPORT: lines only; the
# simulator output stays in work/. Each phase's lines are also kept in
# work/ph_<phase>.txt; the check phase reads them all (work/phases_out.txt).
set -uo pipefail
cd /foss/designs/mixed_signal/ic_source
PHASES=${PHASES:-'size schematic op loop noise pvt mc plot check'}
JOBS=${JOBS:-16}
NMC=${NMC:-100}
export JOBS
has() { case " $PHASES " in *" $1 "*) return 0;; *) return 1;; esac; }
mkdir -p work data assets
printf 'set num_threads=1\n' > work/.spiceinit
: > work/phases_out.txt
run_phase() {
    # a phase not selected contributes its LAST lines (work/ph_<phase>.txt), so a partial
    # run re-judges the rest (as ../ramp_simple); the check phase itself is never re-used
    if ! has "$1"; then
        if [ "$1" != check ] && [ -s "work/ph_$1.txt" ]; then
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

# ------------------------------------------------------------------- lut
ph_lut() { sh lut/build.sh || echo "FAIL: lut/build.sh"; }

# ------------------------------------------------------------------ size
ph_size() {
    [ -s work/lut/pfet_03v3.npz ] || sh lut/build.sh > work/lut_build.txt 2>&1 || { echo "FAIL: lut/build.sh"; return; }
    rm -rf work/size; mkdir -p work/size; cp work/.spiceinit work/size/
    IC_OUT=work/size python3 size_ic.py > work/size/size.txt 2>&1 || echo "FAIL: size_ic.py exited with an error (work/size/size.txt)"
    grep -E "^(size_|REPORT|FAIL|PASS)" work/size/size.txt
    if [ -s work/size/ic_source.spice ] && diff -q <(grep -v '^\*' work/size/ic_source.spice) <(grep -v '^\*' ic_source.spice) >/dev/null; then
        echo "PASS: size_ic.py reproduces ic_source.spice (every device line)"
    else
        echo "FAIL: size_ic.py output differs from ic_source.spice (review and cp work/size/ic_source.spice . ; cp work/size/data/sizing.json data/)"
    fi
}

# ------------------------------------------------------------- schematic
ph_schematic() {
    RC=/foss/designs/mixed_signal/ic_source/xschemrc
    python3 ic_source_sch.py || { echo "FAIL: ic_source_sch.py"; return; }
    rm -f work/ic_source.spice work/ic_source_sch.spice work/tb_ic.spice
    xschem --rcfile "$RC" -b -q -n -s -o work ic_source.sch > work/xschem_ic_source.txt 2>&1
    if [ -s work/ic_source.spice ]; then
        mv work/ic_source.spice work/ic_source_sch.spice
        awk -v sub_=ic_source -f check-schematic.awk ic_source.spice work/ic_source_sch.spice
    else
        echo "FAIL: xschem produced no netlist for ic_source.sch"
    fi
    xschem --rcfile "$RC" -b -q -n -s -o work tb_ic.sch > work/xschem_tb.txt 2>&1
    if [ -s work/tb_ic.spice ]; then
        n=$(grep -c -E "^XIC .* ic_source$" work/tb_ic.spice); s=$(grep -c "^\.subckt ic_source " work/tb_ic.spice)
        v=$(grep -c -i -E "^(VDD_SOURCE|VDVDD|VCLK|VLD|IB) " work/tb_ic.spice)
        if [ "$n" = 1 ] && [ "$s" = 1 ] && [ "$v" = 5 ]; then
            echo "PASS: tb_ic.sch netlists: the cell (from ic_source.sch), AVDD / DVDD / the clock / the bias sink / the load"
        else
            echo "FAIL: tb_ic.sch netlist: $n cell, $s subcircuit, $v sources"
        fi
    else
        echo "FAIL: xschem produced no netlist for tb_ic.sch"
    fi
    for f in ic_source tb_ic; do
        rm -f assets/${f}_xschem.png
        timeout 120 xvfb-run -a xschem --rcfile "$RC" --tcl "set dark_colorscheme 0" \
            --command "xschem zoom_full; xschem print png assets/${f}_xschem.png 2400 1400; xschem exit closewindow force" \
            $f.sch > work/xschem_print_$f.txt 2>&1
        if [ -s assets/${f}_xschem.png ]; then echo "PASS: xschem render assets/${f}_xschem.png"
        else echo "REPORT: xschem render of $f.sch not produced (headless print)"; fi
    done
}

# ---------------------------------------------------------------- cases
# one run per case line "tag KEY=VAL ..." (tb_ic.py); the reduced lines go to <dir>/red.txt
run_case() {
    tag=$1; shift
    d=work/cases/$tag
    rm -rf "$d"; python3 tb_ic.py gen "$d" "$tag" "$@" || { echo "FAIL: tb_ic.py gen $tag"; return; }
    ( cd "$d" && ngspice -b -o tb.out tb.spice > /dev/null 2>&1 )
    python3 tb_ic.py reduce "$d" "$tag" > "$d/red.txt" 2>&1 || echo "FAIL: tb_ic.py reduce $tag: $(grep -m1 -i -E 'error|timestep too small' "$d/tb.out" | cut -c1-100) $(tail -1 "$d/red.txt" | cut -c1-100)"
}
export -f run_case
run_list() {   # $1 = file of case lines
    xargs -P "$JOBS" -L 1 bash -c 'run_case "$@"' _ < "$1"
    for c in $(cut -d' ' -f1 "$1"); do [ -s "work/cases/$c/red.txt" ] && cat "work/cases/$c/red.txt"; done
}

# -------------------------------------------------------------------- op
# the typical cell: the current, headroom, start-up; the ramp node at its three
# levels (output resistance), the clock duty at 45 / 55 %, AVDD at 3.0 / 3.6 V,
# the MIM corners, one slow and one fast cell
ph_op() {
    mkdir -p work/cases
    # the ramp's span from ../ramp_simple's sizing record (ADR 0025); its top scales with AVDD
    # (slope and reset level are both AVDD taps), so the corner cells see VHI x VDDX / 3.3
    vlo=$(python3 -c "import ic_common as ic; print('%.4f' % ic.V_RAMP_LO)")
    vhi() { python3 -c "import ic_common as ic; print('%.4f' % (ic.V_RAMP_HI * $1 / ic.VDD))"; }
    printf '%s\n' "nom" "rlo VLOAD=$vlo" "rhi VLOAD=$(vhi 3.3)" "d45 DUTY=0.45" "d55 DUTY=0.55" \
        "v30 VDDX=3.0" "v36 VDDX=3.6" "mss MIM=ss" "mff MIM=ff" \
        "slow CORNER=ss TEMP=85 VDDX=3.0" "fast CORNER=ff TEMP=0 VDDX=3.6" \
        "rhis CORNER=ss TEMP=85 VDDX=3.0 VLOAD=$(vhi 3.0)" "rhiw CORNER=ff TEMP=85 VDDX=3.0 VLOAD=$(vhi 3.0)" \
        "rhif CORNER=ff TEMP=0 VDDX=3.6 VLOAD=$(vhi 3.6)" > work/op_cases.txt
    run_list work/op_cases.txt
    python3 summarize.py op
}

# ------------------------------------------------------------------ loop
ph_loop() {
    mkdir -p work/cases
    printf '%s\n' "loop KIND=loop" "loophi KIND=loop VLOAD=$(python3 -c 'import ic_common as ic; print(ic.V_RAMP_HI)')" "loopss KIND=loop CORNER=ss TEMP=0 VDDX=3.0" \
        "loopff KIND=loop CORNER=ff TEMP=85 VDDX=3.6" > work/loop_cases.txt
    run_list work/loop_cases.txt
}

# ----------------------------------------------------------------- noise
ph_noise() {
    mkdir -p work/cases
    printf '%s\n' "noise KIND=noise" "noisehi KIND=noise VLOAD=$(python3 -c 'import ic_common as ic; print(ic.V_RAMP_HI)')" > work/noise_cases.txt
    run_list work/noise_cases.txt
}

# ------------------------------------------------------------------- pvt
ph_pvt() {
    mkdir -p work/cases
    python3 - > work/pvt_cases.txt <<'EOF'
import ic_common as ic
for c in ic.CORNERS:
    for t in ic.TEMPS:
        for v in ic.VDDS:
            print("pvt_%s_%gc_%sv CORNER=%s TEMP=%g VDDX=%g" % (c, t, str(v).replace(".", "p"), c, t, v))
EOF
    echo "pvt_cases_planned = $(grep -c . work/pvt_cases.txt)"
    run_list work/pvt_cases.txt > /dev/null
    python3 summarize.py pvt
}

# -------------------------------------------------------------------- mc
ph_mc() {
    mkdir -p work/cases
    : > work/mc_cases.txt
    for k in $(seq 1 "$NMC"); do echo "mc_$k MC=1 SEED=$((20261028 + k))" >> work/mc_cases.txt; done
    run_list work/mc_cases.txt > /dev/null
    python3 summarize.py mc
}

# ------------------------------------------------------------------ plot
ph_plot() { python3 plot_ic.py || echo "REPORT: plot_ic.py failed"; }

# ----------------------------------------------------------------- check
ph_check() { awk -f check-ic.awk work/phases_out.txt; }

for ph in lut size schematic op loop noise pvt mc plot check; do run_phase $ph; done
