#!/bin/sh
# comparator over PVT and Monte Carlo (ngspice) plus the VACASK benches:
#
#   ./run-pvt.sh                              every phase
#   PHASES='bench mc' ./run-pvt.sh            ngspice PVT grid and MC only
#
# Phases (pvt_v3.py: bench mc plot; vacask.sh: vmodels vmc tn tnpvt):
#   bench   45 cells: delay, fall, arming, noise, power      (pvt_v3.py)
#   mc      ngspice Monte Carlo at 7 corner cells             (pvt_v3.py)
#   plot    assets/pvt_summary.png                            (pvt_v3.py)
#   vmodels GF180 models converted for VACASK, gated on ngspice drain currents
#   vmc     VACASK Monte Carlo at the same 7 cells
#   tn      VACASK transient noise at typical (engine gates + conversion jitter)
#   tnpvt   VACASK transient noise at the PVT cell with the most ngspice noise
#   lin     offset signal-independence: MC samples x 4 levels in the charge path   (offset_lin.py)
#   bias    bias-generator requirement: smallest current for 12.5 ns per cell      (bias_req.py)
#   gain    inn -> dout gain at bias_gen's 135 PVT cells, its own current each  (gain_pvt.py)
#
# Writes runs/$TARGET/<stamp>/metrics.json.
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-comparator-pvt}
PHASES=${PHASES:-'bench mc plot vmodels vmc tn tnpvt'}
JOBS=${JOBS:-14}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then run_dir=$(mktemp -d); else run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"; mkdir -p "$run_dir"; fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chown -R 1000:1000 "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets" 2>/dev/null || true
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"

pvt_phases=""
for p in bench mc plot; do case " $PHASES " in *" $p "*) pvt_phases="$pvt_phases $p";; esac; done
va_phases=""
for p in vmodels vmc tn tnpvt; do case " $PHASES " in *" $p "*) va_phases="$va_phases $p";; esac; done

status=0
"$BLOCK_DIR/container.sh" "
    st=0
    if [ -n '$pvt_phases' ]; then DUT_GEOM='${DUT_GEOM:-}' PHASES='$pvt_phases' JOBS=$JOBS python3 -u pvt_v3.py || st=1; fi
    case ' $PHASES ' in *' lin '*) JOBS=$JOBS python3 -u offset_lin.py || st=1;; esac
    case ' $PHASES ' in *' bias '*) JOBS=$JOBS python3 -u bias_req.py || st=1;; esac
    case ' $PHASES ' in *' gain '*) JOBS=$JOBS python3 -u gain_pvt.py || st=1;; esac
    if [ -n '$va_phases' ]; then PHASES='$va_phases' JOBS=$JOBS sh vacask.sh || st=1; fi
    exit \$st
" >"$run_dir/console.log" 2>&1 || status=$?
if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "PVT table: $BLOCK_DIR/data/pvt.csv"
    printf '%s\n' "MC table: $BLOCK_DIR/data/mc_pvt.csv"
    printf '%s\n' "VACASK MC: $BLOCK_DIR/data/vmc.csv"
    printf '%s\n' "Transient noise: $BLOCK_DIR/data/trannoise_summary.json"
    printf '%s\n' "Figure: $BLOCK_DIR/assets/pvt_summary.png"
} >"$run_dir/extra-metrics.txt"
if [ "${NO_RECORD:-0}" = 1 ]; then cat "$run_dir/console.log"; rm -rf "$run_dir"; exit "$status"; fi
awk -v target="$TARGET" -v stamp="$stamp" -v status="$status" \
    -v corner="${ASIC_RD_CORNER:-pvt}" \
    -f "$PROJECT_ROOT/scripts/summarize-metrics.awk" \
    "$run_dir/console.log" "$run_dir/extra-metrics.txt" >"$run_dir/metrics.json"
ln -sfn "$stamp" "$PROJECT_ROOT/runs/$TARGET/latest"
printf '%s\n' "Metrics: $run_dir/metrics.json"
exit "$status"
