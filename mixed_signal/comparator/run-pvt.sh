#!/bin/sh
# comparator over PVT and Monte Carlo (ngspice) plus the 10-device comparator's VACASK
# benches with the swapped hookup: the replica of comparator_bkp/comparator_10dev/run-pvt.sh.
#
#   ./run-pvt.sh                               every phase (about 1-2 h at JOBS=6)
#   PHASES='bench mc plot' ./run-pvt.sh        ngspice PVT grid and MC only
#
# Phases (pvt.py: bench mc lin plot; work/va/vacask.sh: vmodels vmc tn tnpvt):
#   bench   45 cells, sw (4 levels over the whole conversion) and base (2 levels):
#           delay, fall, arming, polarity, noise, power, delay at 3.25 uA
#   mc      ngspice Monte Carlo at 7 corner cells, sw and base
#   lin     offset signal-independence at the 7 MC cells, sw
#   plot    assets/pvt_summary.png
#   vmodels GF180 models converted for VACASK, gated on ngspice drain currents
#   vmc     VACASK Monte Carlo at the same 7 cells (comparator, swapped hookup)
#   tn      VACASK transient noise at typical (engine gates + conversion jitter)
#   tnpvt   the conversion jitter again at sw's worst-noise PVT cell
# The VACASK benches are the 10-device comparator's, staged in work/va by stage_vacask.py
# with the DUT and the hookup replaced (the folder's own files are not changed).
#
# Writes runs/$TARGET/<stamp>/metrics.json.
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-comparator-pvt}
PHASES=${PHASES:-'bench mc lin plot vmodels vmc tn tnpvt'}
JOBS=${JOBS:-6}
MC_SAMPLES=${MC_SAMPLES:-100}
MC_VA_SAMPLES=${MC_VA_SAMPLES:-500}
LIN_SAMPLES=${LIN_SAMPLES:-30}

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then run_dir=$(mktemp -d); else run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"; mkdir -p "$run_dir"; fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
chmod -R a+rwX "$BLOCK_DIR/work" "$BLOCK_DIR/data" "$BLOCK_DIR/assets"

pvt_phases=""
for p in bench mc lin plot; do case " $PHASES " in *" $p "*) pvt_phases="$pvt_phases $p";; esac; done
va_phases=""
for p in vmodels vmc tn tnpvt; do case " $PHASES " in *" $p "*) va_phases="$va_phases $p";; esac; done
case " $PHASES " in *" vmc "*|*" tn "*|*" tnpvt "*) case " $va_phases " in *" vmodels "*) ;; *)
    printf '%s\n' "run-pvt.sh: the VACASK phases need vmodels (the stage is rebuilt each run)" >&2; exit 2;; esac;; esac

status=0
"$BLOCK_DIR/container.sh" "
    st=0
    if [ -n '$pvt_phases' ]; then PHASES='$pvt_phases' JOBS=$JOBS MC_SAMPLES=$MC_SAMPLES LIN_SAMPLES=$LIN_SAMPLES python3 -u pvt.py || st=1; fi
    if [ -n '$va_phases' ]; then
        python3 -u stage_vacask.py || st=1
        (cd work/va && PHASES='$va_phases' JOBS=$JOBS MC_VA_SAMPLES=$MC_VA_SAMPLES sh vacask.sh) || st=1
        python3 -u stage_vacask.py collect || st=1
    fi
    exit \$st
" >"$run_dir/console.log" 2>&1 || status=$?
if grep -q '^FAIL:' "$run_dir/console.log"; then status=1; fi
{
    printf '%s\n' "PVT table (sw): $BLOCK_DIR/data/pvt.csv"
    printf '%s\n' "PVT table (base): $BLOCK_DIR/data/pvt_base.csv"
    printf '%s\n' "MC table: $BLOCK_DIR/data/pvt_mc.csv"
    printf '%s\n' "Offset lin: $BLOCK_DIR/data/pvt_offset_lin.csv"
    printf '%s\n' "VACASK MC: $BLOCK_DIR/data/pvt_vmc.csv"
    printf '%s\n' "Transient noise: $BLOCK_DIR/data/pvt_trannoise_summary.json"
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
