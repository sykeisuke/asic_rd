#!/bin/sh
# sample_seq: the on-chip sampling sequencer (SPEC.md). One 20 MHz clock and
# the controller's acquire level in; S2 / S0 / S1 of the four bottom-plate
# cells out, S2 -> S0 -> S1 at least 5 ns apart, the cells 50 ns apart.
#
#   ./run.sh                               phases size schematic typ pvt duty check
#   PHASES='typ check' ./run.sh            a subset
#
# Phases:
#   size       bench.py size: 45 PVT cells at N = 8 and 24 delay cells per stage,
#              each gap fitted to a + b N; the smallest N with every gap >= 5.25 ns
#              -> data/sizing.json, data/size_fit.csv, sample_seq.spice
#   schematic  schematic.sh: the sheets drawn from the record, sample_seq.sch netlists
#              back to the deck (check_sch.py), renders
#   typ        bench.py typ: typical, 27 C, 3.3 V          -> data/typ.csv
#   pvt        bench.py pvt: 5 corners x 0/27/85 C x 3.0/3.3/3.6 V -> data/pvt.csv
#   duty       bench.py duty: clock duty 30 / 70 % at typ, ff/0/3.6, ss/85/3.0 -> data/duty.csv
#   check      check-seq.awk on each table
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-sample-seq}
PHASES=${PHASES:-'size schematic typ pvt duty check'}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR" 2>/dev/null || true

status=0
JOBS=${JOBS:-16} sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    step() { python3 bench.py \"\$1\" || printf 'FAIL: bench.py %s aborted\n' \"\$1\"; }
    has size && step size
    if has schematic; then sh schematic.sh || printf 'FAIL: schematic.sh\n'; fi
    has typ && step typ
    has pvt && step pvt
    has duty && step duty
    if has check; then
        for t in typ pvt duty; do
            [ -s data/\$t.csv ] && { awk -v set=\$t -f check-seq.awk data/\$t.csv || true; }
        done
    fi
    true
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL' "$run_dir/console.log"; then status=1; fi

{
    printf '%s\n' "Netlist: $BLOCK_DIR/sample_seq.spice"
    printf '%s\n' "Sizing: $BLOCK_DIR/data/sizing.json"
    for t in typ pvt duty size_fit; do printf '%s\n' "Table: $BLOCK_DIR/data/$t.csv"; done
} >"$run_dir/extra-metrics.txt"

if [ "${NO_RECORD:-0}" = 1 ]; then
    cat "$run_dir/console.log" "$run_dir/extra-metrics.txt"
    rm -rf "$run_dir"
    exit "$status"
fi

awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="typical_27c" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
mkdir -p "$PROJECT_ROOT/runs/$TARGET"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
exit "$status"
