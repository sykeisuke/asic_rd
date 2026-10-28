#!/bin/sh
# cell_trannoise: one Analog_top cell (S0/S1/S2 + inverters, 54.52 fF MIM,
# comparator_d, latch = dfxtn_2) on ramp_simple_d, ideal supplies, references,
# bias currents, controls and clock; VACASK transient noise of the whole
# conversion with the input on a code transition, so the latch captures on Clk
# or Clk+1 by noise alone (README.md).
#
#   ./run.sh                                  every step
#   STEPS='reduce' ./run.sh                   re-judge the cached runs
#   NSEED=2 NREC_LO=8 NREC_HI=2 NSEED_G=1 NSEED_BAND=1 NSEED_TOL=1 TWARM=5e-6 ./run.sh   a smoke run
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk),
# unless NO_RECORD=1 (scripts/sim.sh records the run).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-cell-trannoise}
stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
# the container user (uid 1000) writes generated files next to the sources
chmod -R a+rwX "$BLOCK_DIR" 2>/dev/null || true

env_line="STEPS='${STEPS:-models align ngspice sim reduce}' NSEED=${NSEED:-12} NREC_LO=${NREC_LO:-48} NREC_HI=${NREC_HI:-16} NSEED_G=${NSEED_G:-4} NSEED_BAND=${NSEED_BAND:-4} NSEED_TOL=${NSEED_TOL:-4} TWARM=${TWARM:-150e-6} FMAX=${FMAX:-2e9} RELTOL=${RELTOL:-1e-6} LOOSE_G='${LOOSE_G:-ramp ff sw}' RELTOL_G=${RELTOL_G:-1e-5}"
status=0
sh "$BLOCK_DIR/container.sh" "$env_line bash ct.sh" 2>&1 | tee "$run_dir/console.log" || status=$?

if [ "${NO_RECORD:-0}" != 1 ]; then
    : >"$run_dir/extra-metrics.txt"
    awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
        -v corner="typical_27c" \
        -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
        "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
    ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
    printf '%s\n' "Metrics: $run_dir/metrics.json"
fi
grep -q '^FAIL' "$run_dir/console.log" && exit 1
exit "$status"
