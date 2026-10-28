#!/bin/sh
# midref: the VDD/2 reference of the 8-bit bottom-plate cell with ONE
# output -- midref_v2's divider and one midref_buf (device for device), its
# output both VREF and VBL (README.md). The second buffer of midref_v2 is gone.
# Ideal bias current.
#
#   ./run.sh                              phases verify schematic (~10 min)
#   PHASES='verify' VPHASES='op cmp' ./run.sh
#
# Phases:
#   verify     verify_v3.py: PVT operating point and S2 kick (45 cells + bias
#              span), noise on the one node, decision with comparator on the
#              shared node (incl. a neighbour's kick during the hold), Monte
#              Carlo of the output (VDD/2 offset)
#   schematic  the xschem drawings netlist back to midref.spice
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-midrail-ref}
PHASES=${PHASES:-'verify schematic'}
VPHASES=${VPHASES:-'op opdev kick noise cmp mc mchr'}
JOBS=${JOBS:-12}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)        # scripts/sim.sh records the run
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"
# the schematic phase (re)writes midref_buf/midref_div .sch/.sym here as the container user
chmod a+rwX "$BLOCK_DIR"; chmod a+rw "$BLOCK_DIR"/*.sch "$BLOCK_DIR"/*.sym 2>/dev/null || true

status=0
sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has verify; then JOBS=$JOBS PHASES='$VPHASES' python3 -u verify_v3.py || true; fi
    if has schematic; then sh schematic.sh || echo 'FAIL: schematic.sh'; fi
" >"$run_dir/console.log" 2>&1 || status=$?

if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "Netlist: $BLOCK_DIR/midref.spice"
    printf '%s\n' "Sizing: $BLOCK_DIR/data/sizing_v2.json"
    printf '%s\n' "Kick: $BLOCK_DIR/data/verify_kick.json"
    printf '%s\n' "Report: $BLOCK_DIR/README.md"
} >"$run_dir/extra-metrics.txt"

if [ "${NO_RECORD:-0}" = 1 ]; then
    cat "$run_dir/console.log" "$run_dir/extra-metrics.txt"
    rm -rf "$run_dir"
    exit "$status"
fi
awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="${ASIC_RD_CORNER:-typical_27c}" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
exit "$status"
