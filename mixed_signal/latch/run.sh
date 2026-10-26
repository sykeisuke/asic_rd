#!/bin/sh
# Characterize latch, the standard-cell clocked latch after comparator (SPEC.md).
#
#   ./run.sh                              every phase (~15 min)
#   PHASES='drive aperture check' ./run.sh
#
# Writes runs/cmp-scff/<stamp>/metrics.json and links `latest`
# (scripts/summarize-metrics.awk by path). `make latch` calls this through
# scripts/run-latch.sh. Needs the full library install (make pdk-libs).
#
# Phases:
#   explore    the candidates (dfxtn_2 alone, + buff_2, + buff_4) through the
#              drive bench at four cells                      -> data/explore.csv
#   drive      the latch alone, four cells, q into 50 fF; tspc_dff on the same
#              bench for reference                            -> data/drive.csv, drive_tspc.csv
#   slew       the drive bench at clock edges 0.2-8 ns        -> data/slew.csv
#   aperture   dout's edge across the sampling edge, bisected to 1 fs, three cells
#                                                             -> data/aperture.csv
#   kick       comparator + latch on the cell's charge path, clock on/off;
#              tspc_dff and 10 fF as references               -> data/kick.csv
#   schematic  schematic.sh: latch.sch netlists back to latch.spice; render
#   check      check-*.awk on the tables
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-latch}
PHASES=${PHASES:-'explore drive slew aperture kick schematic check'}
SLEW_REQ=${SLEW_REQ:-1.0}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"

status=0
JOBS=${JOBS:-20} sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    step() { python3 bench.py \"\$1\" || printf 'FAIL: bench.py %s aborted\n' \"\$1\"; }
    has explore && step explore
    has drive && step drive
    has slew && step slew
    has aperture && step aperture
    has kick && step kick
    if has schematic; then sh schematic.sh || printf 'FAIL: schematic.sh\n'; fi
    if has check; then
        has explore && awk -f check-explore.awk data/explore.csv
        has drive && awk -v ref=data/drive_tspc.csv -f check-drive.awk data/drive.csv
        has slew && awk -v req=$SLEW_REQ -f check-slew.awk data/slew.csv
        has aperture && awk -f check-aperture.awk data/aperture.csv
        has kick && awk -f check-kick.awk data/kick.csv
        true
    fi
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL' "$run_dir/console.log"; then status=1; fi

{
    printf '%s\n' "Explore: $BLOCK_DIR/data/explore.csv"
    printf '%s\n' "Drive: $BLOCK_DIR/data/drive.csv"
    printf '%s\n' "Drive (tspc_dff reference): $BLOCK_DIR/data/drive_tspc.csv"
    printf '%s\n' "Slew: $BLOCK_DIR/data/slew.csv"
    printf '%s\n' "Aperture: $BLOCK_DIR/data/aperture.csv"
    printf '%s\n' "Kick: $BLOCK_DIR/data/kick.csv"
    printf '%s\n' "Figure: $BLOCK_DIR/assets/latch_xschem.png"
} >"$run_dir/extra-metrics.txt"

if [ "${NO_RECORD:-0}" = 1 ]; then
    cat "$run_dir/console.log"
    rm -rf "$run_dir"
    exit "$status"
fi
awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="${ASIC_RD_CORNER:-typical_27c}" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
printf '%s\n' "Console: $run_dir/console.log"
exit "$status"
