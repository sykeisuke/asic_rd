#!/bin/sh
# Host-side entry point of the chip flow. A make target that calls it
# lets ./scripts/sim.sh keep a metrics record of the run.
#
#   chip_integration/scripts/run.sh            # macros, chip, renders (~30 min)
#   chip_integration/scripts/run.sh macros     # step 3 only (minutes)
#   chip_integration/scripts/run.sh chip       # steps 4-6 (needs macros first)
#   chip_integration/scripts/run.sh collect    # re-read the last chip run
#   chip_integration/scripts/run.sh renders    # redraw renders/ from the last run
#
# 1. checks that inputs/ still matches inputs/MANIFEST.sha256 (the copies
#    the flow is built from; refresh them with scripts/fetch_inputs.sh);
# 2. runs scripts/build.sh <stage> in the pinned container, log to work/;
# 3. keeps the `name = value` / REPORT / artifact lines of that log and
#    judges them with scripts/check-chip.awk;
# 4. copies the run's final metrics into final/.
set -eu

FLOW=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
stage=${1:-all}
log="$FLOW/work/chip-integration-$stage.log"
results="$FLOW/work/chip-integration-$stage.txt"
mkdir -p "$FLOW/work" "$FLOW/final"
chmod 777 "$FLOW/work" "$FLOW/final"

#- 1. the inputs are what the manifest says they are
if ( cd "$FLOW/inputs" && sha256sum --quiet -c MANIFEST.sha256 ) >/dev/null 2>&1; then
    manifest_line="inputs_manifest_ok = 1"
else
    manifest_line="inputs_manifest_ok = 0
REPORT: inputs differ from inputs/MANIFEST.sha256 (re-run scripts/fetch_inputs.sh)"
fi

#- 2. the container half
status=0
"$FLOW/scripts/container.sh" "bash scripts/build.sh $stage" >"$log" 2>&1 || status=$?

#- 3. the lines the verdict is made of; the log stays unread
{
    echo "$manifest_line"
    grep -E '^REPORT: |^[A-Za-z][A-Za-z0-9_]* = |^[A-Za-z][A-Za-z0-9 /-]*: /' "$log" || :
} >"$results"
case $stage in
    chip|all)
        awk -f "$FLOW/scripts/flow-errors.awk" "$log" >>"$results"
        last=$(ls -d "$FLOW/librelane/runs/chip_top/"[0-9]*-* 2>/dev/null | sort -V | tail -n 1)
        if [ -n "$last" ] && [ ! -d "$FLOW/librelane/runs/chip_top/final/gds" ]; then
            for f in "$last"/*.log; do
                [ -f "$f" ] && awk -f "$FLOW/scripts/step-errors.awk" "$f" >>"$results"
            done
        fi
        ;;
esac
cat "$results"
awk -v stage="$stage" -f "$FLOW/scripts/check-chip.awk" "$results" || status=1

#- 4. the record that stays with the folder
run="$FLOW/librelane/runs/chip_top"
case $stage in
    chip|all|collect)
        if [ -s "$run/final/metrics.csv" ]; then
            cp "$run/final/metrics.csv" "$FLOW/final/metrics.csv"
            [ -s "$run/final/metrics.json" ] && cp "$run/final/metrics.json" "$FLOW/final/metrics.json"
        fi
        ;;
esac
cp "$results" "$FLOW/final/results-$stage.txt"

printf '%s\n' "Results: $results"
printf '%s\n' "Log: $log"
exit "$status"
