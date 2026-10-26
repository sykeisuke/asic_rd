#!/bin/sh
# VACASK benches of comparator, run INSIDE the container from this block
# (run-pvt.sh calls it through container.sh). Phases, from $PHASES:
#
#   vmodels  GF180 3.3 V models converted for VACASK (five corners), gated on
#            reproducing ngspice's drain currents (vacask_lib/devcheck.py, 2 %)
#   vmc      VACASK Monte Carlo (PDK fets_mm mismatch) at the 7 corner cells of
#            pvt_v3.py, MC_VA_SAMPLES each: sigma(Vos) / alpha against 4/3 LSB
#   tn       VACASK transient noise at typical (trannoise.py): engine gates
#            (PSD vs the noise analysis), numerical floor, generator bandwidth,
#            and the crossing jitter of the 8-bit conversion
#   tnpvt    the conversion jitter again at the PVT cell with the most ngspice
#            noise (data/pvt.csv), corner mode (TN_SUFFIX)
#
# The transient-noise gate is the user's noise limit, 1.2 mV rms at the pins
# (alloc = 1.2 mV / alpha / LSB at the ADC input); the 0.080 LSB allocation
# of ../Analog_top_bkp/unit_cell_noise/NOISE_BUDGET.md is reported against.
set -u
PHASES=${PHASES:-'vmodels vmc tn tnpvt'}
MC_VA_SAMPLES=${MC_VA_SAMPLES:-500}
MC_SEED=${MC_SEED:-20261006}
MC_CELLS=${MC_CELLS:-'typical:27:3.3 ss:85:3.0 ff:0:3.6 sf:27:3.3 fs:27:3.3 ss:0:3.0 ff:85:3.6'}
has() { case " $PHASES " in *" $1 "*) return 0;; *) return 1;; esac; }
sj() { python3 -c "import json;print(json.load(open('data/sizing.json'))['$1'])"; }
export PYTHONPATH="/foss/tools/vacask/lib/vacask/python:${PYTHONPATH:-}"
mkdir -p work data assets
st=0
iref=$(sj iref); alpha=$(sj alpha); lb=$(sj l_b); wfp=$(python3 -c "print('%g' % ($(sj w_fp) * 1e6))")
REFP="xrefp (pbias pbias vddb vddb) pfet_03v3 l=${lb}u w=${wfp}u nf=1 m=1"
alloc=$(python3 -c "print(1.2e-3 / $alpha / (1.5 / 256))")
printf "REPORT: VACASK benches: ideal %s A into %s; alpha %s; transient-noise gate 1.2 mV at the pins = %.4f LSB at the ADC input\n" "$iref" "$REFP" "$alpha" "$alloc"

run_vacask() {  # sim (in work/)
    if ! (cd work && vacask --quiet-progress "$1" > "${1%.sim}.vlog" 2>&1); then
        grep -iE "error|fatal" "work/${1%.sim}.vlog" | head -3 | sed "s|^|FAIL: vacask $1: |" || true
        printf "FAIL: vacask aborted on %s\n" "$1"; st=1
    fi
}

# ------------------------------------------------------------------ models
if has vmodels; then
    for c in typical ss ff sf fs; do
        python3 vacask_lib/gf180_vacask.py "$c" "work/gf180_03v3_$c.inc" || { printf "FAIL: model conversion for %s\n" "$c"; st=1; }
    done
    sed -e "s/@CORNER@/typical/g" vacask_lib/tb_devcheck.sim.tmpl > work/tb_devcheck_typical.sim
    printf 'set num_threads=1\n' > .spiceinit
    ngspice -b -o work/devcheck_ngspice.log tb_vacask_devcheck.spice >/dev/null 2>&1 || true
    run_vacask tb_devcheck_typical.sim
    python3 vacask_lib/devcheck.py work/devcheck_ngspice.log work/devcheck.raw 0.02 || st=1
fi
python3 vacask_lib/spice2sim.py comparator.spice work/dut.inc || { printf "FAIL: spice2sim.py\n"; st=1; }
cp comparator.spice work/dut.spice

# ------------------------------------------------------------- Monte Carlo
if has vmc; then
    printf "tag,corner,temp,vdd,level,samples,found,vos_nom_v,vos_mean_v,vos_sigma_v,vos_min_v,vos_max_v\n" > data/vmc.csv
    for cell in $MC_CELLS; do
        c=${cell%%:*}; rest=${cell#*:}; t=${rest%%:*}; v=${rest#*:}
        vcm=$(python3 -c "print('%g' % ($v / 2))")
        ftag=$(printf "%s_%s_%s" "$c" "$t" "$v" | tr . p)
        sed -e "s/@CORNER@/$c/g; s/@TEMP@/$t/g; s/@VDD@/$v/g; s/@VCM@/$vcm/g; s/@IREF@/$iref/g; s/@TAG@/$ftag/g; s/@SAMPLES@/$MC_VA_SAMPLES/g; s/@SEED@/$MC_SEED/g; s|@REFP@|$REFP|; s/@CLOAD@/10f/" \
            vacask_lib/tb_mc.sim.tmpl > "work/mc_${ftag}.sim"
        run_vacask "mc_${ftag}.sim"
        python3 vacask_lib/mc_reduce.py work "$ftag" "${c}_${t}_${v}" "$c" "$t" "$v" "$vcm" "$MC_VA_SAMPLES" >> data/vmc.csv \
            || { printf "FAIL: mc_reduce.py on %s\n" "$ftag"; st=1; }
        rm -f work/mc_${ftag}.[0-9]*.dc.raw
    done
    awk -F, -v a="$alpha" -v n="$MC_VA_SAMPLES" 'NR > 1 {
        s = $10 / a / (1.5 / 256); printf "REPORT: VACASK MC %s: %d/%d samples crossed, sigma(Vos) %.2f mV = %.3f LSB, mean %+.2f mV\n", $1, $7, $6, $10 * 1e3, s, $9 * 1e3
        if (s > mx || NR == 2) mx = s; if (s < mn || NR == 2) mn = s; if ($7 < 0.99 * n) inc = inc " " $1 }
        END { printf "vmc_sigma_max_lsb = %.6g\nvmc_sigma_min_lsb = %.6g\n", mx, mn
              if (inc != "") printf "FAIL: VACASK MC: samples without a crossing at%s\n", inc
              else printf "PASS: VACASK MC: every sample crossed at every cell\n"
              #- ADR 0015: the 4/3 LSB contract is replaced by the signal-independence gate
              printf "REPORT: VACASK MC sigma(Vos) %.2f..%.2f LSB at the ADC input (not gated, ADR 0015)\n", mn, mx }' data/vmc.csv
fi

# ------------------------------------------------------- transient noise
tn_all() {   # run every .sim in the current directory in parallel; $1 = glob
    for sim in $1; do
        [ -e "$sim" ] || continue
        ( if vacask --quiet-progress "$sim" > "${sim%.sim}.vlog" 2>&1; then :; else
              printf "FAIL: vacask aborted on %s\n" "$sim"; fi ) &
    done
    wait
}
if has tn; then
    python3 trannoise.py gen 1 || { printf "FAIL: trannoise.py gen 1\n"; st=1; }
    (cd work/tn && tn_all "*_ss.sim" && tn_all "r_*.sim")
    python3 trannoise.py gen 2 || { printf "FAIL: trannoise.py gen 2\n"; st=1; }
    (cd work/tn && for s in psd_*.sim; do case "$s" in *_ss.sim) ;; *) echo "$s";; esac; done > .psd && tn_all "$(cat .psd)")
    python3 trannoise.py reduce > work/tn/measurements.txt || { printf "FAIL: trannoise.py reduce\n"; st=1; }
    grep -E "^[a-z_0-9]+ = " work/tn/measurements.txt | sed "s/^/tn_/"
    nomtag="r_1p65"
    awk -v tags="$nomtag ${nomtag}_q ${nomtag}_f1g" -v levels="$nomtag" -v alpha="$alpha" -v alloc="$alloc" \
        -f check-trannoise.awk work/tn/measurements.txt || st=1
    python3 -c "
import re
m = dict(re.findall(r'^(\w+) = ([-+0-9.eE]+)', open('work/tn/measurements.txt').read(), re.M))
w = float(m.get('worst_sigma_lsb', 'nan'))
print('REPORT: transient decision noise %.4f LSB at the ADC input against the 0.080 LSB allocation of NOISE_BUDGET.md: %s' % (w, 'within' if w <= 0.080 else 'OVER'))"
fi
if has tnpvt && [ -s data/pvt.csv ]; then
    worst=$(awk -F, 'NR == 1 { for (i = 1; i <= NF; i++) c[$i] = i; next }
        $c["noise"] > m { m = $c["noise"]; w = $c["corner"] " " $c["temp"] " " $c["vdd"] " " $c["tag"] } END { print w }' data/pvt.csv)
    set -- $worst
    suffix=$(printf "%s" "$4" | tr . p)
    vcm=$(python3 -c "print('%g' % ($3 / 2))")
    printf "REPORT: transient noise at the worst-noise PVT cell %s (VBL %s V)\n" "$4" "$vcm"
    [ -s "work/gf180_03v3_$1.inc" ] || python3 vacask_lib/gf180_vacask.py "$1" "work/gf180_03v3_$1.inc"
    export TN_SUFFIX="$suffix" TN_CORNER="$1" TN_TEMP="$2" TN_VDD="$3" VCM_DEC="$vcm"
    python3 trannoise.py gen 1 || { printf "FAIL: trannoise.py gen 1 (pvt)\n"; st=1; }
    (cd "work/tn_$suffix" && tn_all "*.sim")
    python3 trannoise.py gen 2 || true
    python3 trannoise.py reduce > "work/tn_$suffix/measurements.txt" || { printf "FAIL: trannoise.py reduce (pvt)\n"; st=1; }
    cp "work/tn_$suffix/measurements.txt" data/pvt_trannoise.txt
    grep -E "^[a-z_0-9]+ = " "work/tn_$suffix/measurements.txt" | sed "s/^/tnpvt_/"
    python3 -c "
import re
m = dict(re.findall(r'^(\w+) = ([-+0-9.eE]+)', open('data/pvt_trannoise.txt').read(), re.M))
w = float(m.get('worst_sigma_lsb', 'nan'))
print('%s: transient-noise crossing jitter at $4: %.4f LSB at the ADC input (gate %.4f LSB = 1.2 mV at the pins; 0.080 allocation %s)'
      % ('PASS' if w <= $alloc else 'FAIL', w, $alloc, 'met' if w <= 0.08 else 'exceeded'))"
    unset TN_SUFFIX TN_CORNER TN_TEMP TN_VDD VCM_DEC
fi
exit $st
