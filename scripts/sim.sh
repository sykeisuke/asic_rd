#!/bin/sh
# Run one make target, capture its console output, and reduce it to a
# machine-readable metrics record.
#
#   ./scripts/sim.sh <make-target> [extra make arguments]
#
# Writes:
#   runs/<target>/<timestamp>/console.log   full tool output (never read directly)
#   runs/<target>/<timestamp>/metrics.json  scalar summary and pass/fail
#   runs/<target>/latest -> <timestamp>
#
# Exit status mirrors the make target, so this is safe in a regression chain.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

if [ "$#" -lt 1 ]; then
    printf '%s\n' 'usage: scripts/sim.sh <make-target> [make args...]' >&2
    exit 2
fi

target=$1
shift

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$PROJECT_ROOT/runs/$target/$stamp"
mkdir -p "$run_dir"

status=0
( cd "$PROJECT_ROOT" && make "$target" "$@" ) >"$run_dir/console.log" 2>&1 || status=$?

# Physical runs report their figures of merit in a CSV instead of stdout.
extra="$run_dir/extra-metrics.txt"
: >"$extra"
physical_metrics="$PROJECT_ROOT/digital/asic_digital_top/physical/runs/gf180_rtl2gds/final/metrics.csv"
if [ "$target" = digital-physical ] && [ -s "$physical_metrics" ]; then
    awk -F, 'NF == 2 && $2 ~ /^[-+0-9.]/ { print $1 " = " $2 }' \
        "$physical_metrics" >>"$extra"
fi

awk -v target="$target" -v stamp="$stamp" -v status="$status" \
    -v corner="${ASIC_RD_CORNER:-typical_27c}" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$extra" >"$run_dir/metrics.json"

ln -sfn "$stamp" "$PROJECT_ROOT/runs/$target/latest"

printf '%s\n' "Metrics: $run_dir/metrics.json"
printf '%s\n' "Console: $run_dir/console.log"
exit "$status"
