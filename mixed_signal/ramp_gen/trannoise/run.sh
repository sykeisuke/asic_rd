#!/bin/bash
# trannoise/run.sh -- VACASK transient-noise cross-check of the ramp_gen noise
# breakdown, inside the pinned container (from the block: ./container.sh 'bash trannoise/run.sh').
#
#   NSEED   seeds per case (default 12)        NPER  conversions per seed (default 30)
#   NDISC   first conversions dropped (6)      JOBS  parallel VACASK runs (default 12)
#   FMIN / FMAX  generated noise band (2e3 / 20e6 Hz)
#   CASES   subset of: all ramp bias cells quiet
#
# Prints only `name = value`, PASS:/FAIL: and REPORT: lines. Snapshots
# ramp_gen.spice and data/ramp_gen_params.spice into work/snap first, so the
# translation is of one consistent design.
set -uo pipefail
cd /foss/designs/mixed_signal/ramp_gen/trannoise
NSEED=${NSEED:-12}; NPER=${NPER:-30}; NDISC=${NDISC:-6}; JOBS=${JOBS:-12}
FMIN=${FMIN:-2e3}; FMAX=${FMAX:-20e6}
CASES=${CASES:-'all ramp bias cells quiet'}
mkdir -p work
rm -rf work/snap && mkdir -p work/snap
cp ../ramp_gen.spice ../data/ramp_gen_params.spice work/snap/
echo "REPORT: trannoise snapshot $(md5sum work/snap/ramp_gen_params.spice | cut -c1-12) of data/ramp_gen_params.spice; band $FMIN-$FMAX Hz; $NSEED seeds x $NPER conversions, first $NDISC dropped"

python3 tn_models.py || exit 1
( cd work && cp ../probe_models.py . && vacask ../probe_models.sim 2>&1 | grep -E "^(PASS|FAIL|tn_)" )

quiet_of() {
    case $1 in
        # bias = the ramp's own bias_gen only; cells = cells + the cells' bias_gen
        all) echo "" ;; ramp) echo "ramp_bias cell_bias cells" ;;
        bias) echo "ramp_ota ramp_chain cell_bias cells" ;;
        cells) echo "ramp_ota ramp_chain ramp_bias" ;; quiet) echo "" ;;
    esac
}
: > work/jobs.txt
for c in $CASES; do
    mkdir -p work/case_$c; ln -sfn ../models.inc work/case_$c/models.inc
    python3 tn_netlist.py work/snap $(quiet_of $c) > work/case_$c/net.inc 2> work/case_$c/net_counts.txt || { echo "FAIL: tn_netlist.py for case $c"; exit 1; }
    scale=1; [ "$c" = quiet ] && scale=0
    for s in $(seq 1 $NSEED); do
        d=work/case_$c/s$s; rm -rf $d; mkdir -p $d
        python3 tn_bench.py $d/tn.sim ../net.inc $NPER $((20261002 + s)) $scale $FMIN $FMAX
        echo "$d" >> work/jobs.txt
    done
done
run_one() {
    d=$1; nper=$2
    ( cd $d && vacask tn.sim > vacask.txt 2>&1 )
    if [ ! -s $d/tn.raw ] || grep -q -i aborted $d/vacask.txt; then
        # a noise realisation can still collapse the step: one retry, new seed, counted
        echo "REPORT: VACASK run $d aborted (timestep too small); retried once with seed 3026xxxx"
        sed -i 's/noiseseed=2026/noiseseed=3026/' $d/tn.sim
        rm -f $d/tn.raw
        ( cd $d && vacask tn.sim > vacask.txt 2>&1 )
    fi
    if [ -s $d/tn.raw ] && ! grep -q -i aborted $d/vacask.txt; then
        python3 tn_extract.py $d $nper > $d/extract.txt 2>&1 || echo "FAIL: tn_extract.py $d"
        rm -f $d/tn.raw
    else
        echo "REPORT: VACASK run $d lost: aborted again after the retry (the case gate needs >= 6 seeds)"
    fi
}
export -f run_one
t0=$(date +%s)
xargs -P "$JOBS" -I{} bash -c "run_one {} $NPER" < work/jobs.txt
echo "tn_wall_s = $(( $(date +%s) - t0 ))"

python3 tn_predict.py work/snap $FMIN $FMAX | grep -E "^(tn_pred|tn_flicker|FAIL|REPORT)" | grep -v -E "_lo |_hi "
python3 tn_reduce.py $NDISC
