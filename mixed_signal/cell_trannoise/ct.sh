#!/bin/bash
# ct.sh -- the cell_trannoise flow, INSIDE the container (cwd = this block;
# run.sh calls it through container.sh). Prints only `name = value`, PASS:/FAIL:
# and REPORT: lines, then check-ct.awk's verdicts.
#
#   STEPS   subset of: models align ngspice sim reduce   (default all)
#   JOBS    parallel simulator runs (12)                 FORCE=1   re-simulate cached runs
#   NSEED (12)  NREC_LO (48)  NREC_HI (16)  NSEED_G (4)  NSEED_BAND (4)  NSEED_TOL (4)
#   TWARM (150e-6)  FMAX (2e9)  RELTOL (1e-6)  NOISE_BLOCKS ('ramp cmp ff sw')
#   LOOSE_G ('ramp ff sw')  RELTOL_G (1e-5)
#   A cached re-run must leave out `models`: it rewrites work/net_*.inc, and a result
#   older than its netlist is simulated again (STEPS='align ngspice sim reduce').
#
# models   work/models.inc (ct_models.py) and the translated subcircuits:
#          net_drawn.inc (as drawn, noiseless references), net_all.inc (every group
#          noisy, NF1 finger expansion), net_only_<g>.inc (group g alone noisy)
# align    per level (nominal mid-code 16.5, 240.5): a noiseless VACASK run, then
#          ct_align.py moves POS so that the noiseless decision lands on a falling
#          clock edge (work/align.txt). Every later run uses the aligned POS.
# ngspice  ngspice runs the same bench noiseless (ct_bench.py ngspice, NREC 4): the
#          reference the VACASK translation must reproduce
# sim      VACASK per level at the aligned POS:
#            q    noiseless, drawn nf, maxstep 0.2 ns, NREC 4 (vs ngspice; numerical floor)
#            q1   noiseless, the noisy-run finger expansion (NF1)
#            n    every device noise source, noisefmax FMAX, NSEED seeds, TWARM of idle
#                 tracking first (VACASK's flicker Lorentzians start from zero; the
#                 clock starts 1 us before the first record), reltol RELTOL
#            g_<grp>  one group alone noisy, NSEED_G seeds (the per-block shares).
#                 The groups in LOOSE_G ('ramp ff sw') run at RELTOL_G (1e-5), at both
#                 levels: with only a few MOS noisy the circuit is nearly noiseless and
#                 VACASK loses the run at 1e-6 ("Timestep too small", as ../Analog_top_bkp/Analog_top_v4's
#                 noiseless bench; ramp alone always, latch alone at c16 and switches alone
#                 at c240 on both attempts of the 2026-10-14 launch). ct_reduce.py reports
#                 each group's mean decision against the noiseless one (a floating-plate
#                 leak would show there)
#          and at one level only:
#            b6   n at noisefmax 6 GHz, c16, NSEED_BAND seeds (is FMAX wide enough for kT/C?)
#            tt   n at reltol 2e-7, c240, NSEED_TOL seeds (is RELTOL tight enough?)
#          A run's result (r.csv) is kept while its regenerated tn.sim is identical.
# reduce   ct_reduce.py: metrics, data/ct_summary.json, data/ct_noise.npz,
#          assets/ct_noise.png/.svg; check-ct.awk
[ -n "${BASH_VERSION:-}" ] || exec bash "$0" "$@"
set -uo pipefail
B=/foss/designs/mixed_signal/cell_trannoise
cd "$B"
export PYTHONPATH="/foss/tools/vacask/lib/vacask/python:${PYTHONPATH:-}"
STEPS=${STEPS:-'models align ngspice sim reduce'}
JOBS=${JOBS:-12}; NSEED=${NSEED:-12}; NREC_LO=${NREC_LO:-48}; NREC_HI=${NREC_HI:-16}
NSEED_G=${NSEED_G:-4}; NSEED_BAND=${NSEED_BAND:-4}; NSEED_TOL=${NSEED_TOL:-4}
TWARM=${TWARM:-150e-6}; FMAX=${FMAX:-2e9}; RELTOL=${RELTOL:-1e-6}
NOISE_BLOCKS=${NOISE_BLOCKS:-'ramp cmp ff sw'}; LOOSE_G=${LOOSE_G:-'ramp ff sw'}; RELTOL_G=${RELTOL_G:-1e-5}
export FMAX RELTOL RELTOL_G LOOSE_G
LEVELS='c16:16.5 c240:240.5'
has() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
mkdir -p work data assets
printf 'set num_threads=1\n' > work/.spiceinit
st=0
TFIRST_N=$(awk -v w="$TWARM" 'BEGIN { printf "%.9e", w + 1e-6 }')
echo "ct_twarm_us = $(awk -v w="$TWARM" 'BEGIN { print w * 1e6 }')"
echo "ct_fmax_ghz = $(awk -v f="$FMAX" 'BEGIN { print f / 1e9 }')"
echo "ct_reltol = $RELTOL"
echo "ct_reltol_g = $RELTOL_G"
echo "REPORT: blocks alone at reltol $RELTOL_G: $LOOSE_G"

if has models; then
    python3 ct_models.py || exit 1
    CT_NF1=0 python3 ct_netlist.py > work/net_drawn.inc 2> work/net_drawn.txt || { cat work/net_drawn.txt; exit 1; }
    CT_NF1=1 python3 ct_netlist.py > work/net_all.inc 2> work/net_all.txt || { cat work/net_all.txt; exit 1; }
    for g in $NOISE_BLOCKS; do
        others=$(for x in ramp cmp ff sw; do [ "$x" = "$g" ] || printf '%s ' "$x"; done)
        CT_NF1=1 python3 ct_netlist.py $others > "work/net_only_$g.inc" 2> "work/net_only_$g.txt" \
            || { cat "work/net_only_$g.txt"; exit 1; }
    done
    sed 's/^/REPORT: /' work/net_all.txt
    echo "PASS: translated ramp_simple_d + atop_cell (sw_s0/1/2, comparator_d, latch = dfxtn_2) from ../Analog_top/analog_top.spice"
fi
for f in work/models.inc work/net_drawn.inc work/net_all.inc; do
    [ -s "$f" ] || { echo "FAIL: $f missing; run the models step"; exit 1; }
done

vrun() {   # dir: run VACASK on dir/tn.sim, extract with dir/params.txt
    d=$1
    ( cd "$d" && vacask tn.sim > vacask.txt 2>&1 )
    if [ -s "$d/tn.raw" ] && ! grep -q -i aborted "$d/vacask.txt"; then
        python3 ct_extract.py "$d/tn.raw" "$d/r.csv" $(cat "$d/params.txt") > "$d/extract.txt" 2>&1 \
            || echo "FAIL: ct_extract.py $d: $(tail -1 "$d/extract.txt" | cut -c1-160)"
        rm -f "$d/tn.raw"
        return 0
    fi
    rm -f "$d/tn.raw"
    return 1
}

if has align; then
    : > work/align.txt
    for lv in $LEVELS; do
        tag=${lv%%:*}; pos=${lv#*:}; d=work/al_$tag/s0
        mkdir -p "$d"
        echo "POS=$pos NREC=2" > "$d/params.txt"
        python3 ct_bench.py vacask "$d/tn.sim" "$B/work/net_drawn.inc" --scale 0 --maxstep 0.2e-9 POS=$pos NREC=2
        vrun "$d" || { echo "FAIL: align $tag: VACASK noiseless run lost: $(grep -m1 -i -E 'error|abort|small' "$d/vacask.txt" | cut -c1-160)"; exit 1; }
        python3 ct_align.py "$tag" "$pos" "$d/r.csv" || exit 1
    done
fi
[ -s work/align.txt ] || { echo "FAIL: no work/align.txt; run the align step"; exit 1; }
apos() { awk -v t="$1" '$1 == t { print $2 }' work/align.txt; }

if has ngspice; then
    for lv in $LEVELS; do
        tag=${lv%%:*}; pos=$(apos "$tag"); d=work/ng_$tag
        rm -rf "$d"; mkdir -p "$d"; cp work/.spiceinit "$d/"
        python3 ct_bench.py ngspice "$d/tb.spice" POS=$pos NREC=4
        t0=$(date +%s)
        ( cd "$d" && ngspice -b tb.spice > ngspice.out 2>&1 ) || { echo "FAIL: ngspice reference ($tag)"; st=1; }
        echo "ct_ngspice_${tag}_s = $(( $(date +%s) - t0 ))"
        python3 ct_extract.py "$d/tb.raw" "$d/r.csv" POS=$pos NREC=4 > /dev/null || { echo "FAIL: ct_extract ngspice $tag"; st=1; }
        rm -f "$d/tb.raw"
    done
fi

lost() {   # REPORT every run directory with a VACASK console but no result
    for d in work/*/s*; do
        [ -f "$d/vacask.txt" ] && [ ! -s "$d/r.csv" ] || continue
        echo "REPORT: $1 ${d#work/}: no result ($(grep -m1 -i -E 'small|error|abort' "$d/vacask.txt" | cut -c1-120))"
    done
}

if has sim; then
    lost "lost before this launch:"
    : > work/jobs.txt
    add() {   # dir net prio [ct_bench.py vacask arguments ...]; queues the run unless cached
        d=$1; net=$2; prio=$3; shift 3
        mkdir -p "$d"
        python3 ct_bench.py vacask "$d/tn.new" "$B/work/$net" "$@" || { echo "FAIL: ct_bench.py $d"; st=1; return; }
        printf '%s\n' "$*" | tr ' ' '\n' | grep -E '^[A-Z][A-Z_0-9]*=' | tr '\n' ' ' > "$d/params.txt"
        key=$d/tn.sim; [ -f "$d/tn.key" ] && key=$d/tn.key    # a retried run keeps its original deck as the key
        if [ "${FORCE:-0}" != 1 ] && [ -s "$d/r.csv" ] && [ -f "$key" ] && cmp -s "$d/tn.new" "$key" \
           && [ ! "work/$net" -nt "$d/r.csv" ]; then
            rm -f "$d/tn.new"; return
        fi
        mv "$d/tn.new" "$d/tn.sim"; rm -f "$d/r.csv" "$d/tn.key"
        echo "$prio $d" >> work/jobs.txt
    }
    for lv in $LEVELS; do
        tag=${lv%%:*}; pos=$(apos "$tag")
        nrec=$NREC_HI; pr=1; [ "$tag" = c16 ] && { nrec=$NREC_LO; pr=3; }
        add work/q_$tag/s0 net_drawn.inc 0 --scale 0 --maxstep 0.2e-9 POS=$pos NREC=4
        add work/q1_$tag/s0 net_all.inc 0 --scale 0 --maxstep 0.2e-9 POS=$pos NREC=4
        base=$((20261014 + 1000 * ${pos%.*}))
        for j in $(seq 0 $((NSEED - 1))); do
            add work/n_$tag/s$j net_all.inc $pr --seed $((base + j)) --fmax "$FMAX" --reltol "$RELTOL" \
                POS=$pos NREC=$nrec TFIRST=$TFIRST_N
        done
        gi=0
        for g in $NOISE_BLOCKS; do
            gi=$((gi + 1)); rt=$RELTOL; case " $LOOSE_G " in *" $g "*) rt=$RELTOL_G;; esac
            for j in $(seq 0 $((NSEED_G - 1))); do
                add work/g_${g}_$tag/s$j "net_only_$g.inc" $((pr + 1)) --seed $((base + 100 * gi + j)) --fmax "$FMAX" \
                    --reltol "$rt" POS=$pos NREC=$nrec TFIRST=$TFIRST_N
            done
        done
    done
    p16=$(apos c16); p240=$(apos c240)
    for j in $(seq 0 $((NSEED_BAND - 1))); do
        add work/b6_c16/s$j net_all.inc 3 --seed $((20262014 + j)) --fmax 6e9 --reltol "$RELTOL" \
            POS=$p16 NREC=$NREC_LO TFIRST=$TFIRST_N
    done
    for j in $(seq 0 $((NSEED_TOL - 1))); do
        add work/tt_c240/s$j net_all.inc 1 --seed $((20263014 + j)) --fmax "$FMAX" --reltol 2e-7 \
            POS=$p240 NREC=$NREC_HI TFIRST=$TFIRST_N
    done
    echo "REPORT: ct: $(wc -l < work/jobs.txt) VACASK runs to simulate (the rest cached), JOBS=$JOBS"
    run_one() {
        d=$1; s=$(date +%s)
        if ! vrun "$d"; then
            case $d in
                *tt_*) echo "REPORT: VACASK run $d lost at reltol 2e-7: $(grep -m1 -i -E 'error|abort|small' "$d/vacask.txt" | cut -c1-120)" ;;
                *) echo "REPORT: VACASK run $d aborted ($(grep -m1 -i -E 'small|error|abort' "$d/vacask.txt" | cut -c1-80)); retried once with seed + 1000000"
                   cp "$d/tn.sim" "$d/tn.key"
                   sed -i -E 's/noiseseed=([0-9]+)/noiseseed=1\1/' "$d/tn.sim"
                   vrun "$d" || echo "FAIL: VACASK run $d lost twice: $(grep -m1 -i -E 'error|abort|small' "$d/vacask.txt" | cut -c1-160)" ;;
            esac
        fi
        echo $(( $(date +%s) - s )) > "$d/wall.txt"
    }
    export -f run_one vrun
    t0=$(date +%s)
    sort -k1,1n work/jobs.txt | cut -d' ' -f2 | xargs -r -P "$JOBS" -I{} bash -c 'run_one {}'
    echo "ct_sim_wall_s = $(( $(date +%s) - t0 ))"
    lost "lost in this launch:"
    for c in work/q_* work/q1_* work/n_* work/g_* work/b6_* work/tt_*; do
        [ -d "$c" ] || continue
        cat "$c"/s*/wall.txt 2>/dev/null | awk -v c="${c#work/}" '{ s += $1; if ($1 > m) m = $1; n++ }
            END { if (n) printf "REPORT: %s: %d runs, mean %.0f s, max %.0f s of VACASK per run\n", c, n, s / n, m }'
    done
fi

if has reduce; then
    python3 ct_reduce.py > work/summary.txt || st=1
    cat work/summary.txt
    awk -f check-ct.awk work/summary.txt || st=1
fi
exit $st
