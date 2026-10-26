#!/bin/sh
# analog_top v5: the analog macro of the 8-bit true bottom-plate ADC, v4 with
# ONE VDD/2 buffer (../midrail_ref, ADR 0021): the output of XVREF is the
# net vref, every cell's S2 level AND every comparator's inp; the second
# buffer XVBL and its bias output XBG.XOB (bias_gen_s = bias_gen - XOB +
# XOL) are gone. Everything else is v4's: four cells (switches S0/S1/S2,
# 54.52 fF MIM, comparator_d, the standard-cell latch latch) on one
# ramp_simple_d, vrlo_ref making vrlo, TR = TS3 + 300 ns (README.md).
#
#   ./run.sh                               phases schematic func op xtb pwr
#   PHASES='func' ./run.sh                 the functional record alone (~1 min)
#
# Phases (each owned by one script):
#   schematic  schematic.sh: analog_top.sch netlists (xschem, hierarchical) to
#              the GENERATED analog_top.spice (REGEN=1 rewrites it, otherwise a
#              difference FAILs); every block against its deck (make_refs.py for
#              the three derived cells); no RLK / 1e15 / {param} in the macro;
#              check_equiv.py: the macro is v4's minus XVBL and XBG.XOB with vbl
#              = vref, nothing else; tb_analog_top.sch netlists to the hand
#              bench; renders (render.sh: assets/*.png, *.svg)
#   func       func.sh: tb_analog_top.spice, one record from a cold supply:
#              power-up, four samples, ramp, four trips; check-func.awk;
#              compare_v4.py: the record against v4's (reported)
#   op         op.sh: the in-macro operating point (Id, gm, gm/Id, gds,
#              Vds - Vdsat, region; switch Ron; R = V / I; MIM C) at two instants
#              -> data/op_point.csv, data/op_rc.csv, the table on analog_top.sch
#   xtb        xtb.sh: the xschem testbench netlist, simulated, reproduces func
#   pwr        pwr.sh (~1 min): the func record again, every AVDD branch
#              current saved; averages per phase (track, sample, hold, ramp,
#              before/after each decision) per branch -> data/pwr_branches.csv,
#              data/pwr_windows.csv, assets/pwr_profile.png
# v4's trannoise phase is NOT ported (it has no v4 record either).
#
# Writes runs/$TARGET/<stamp>/metrics.json (scripts/summarize-metrics.awk).
set -eu

BLOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$BLOCK_DIR/../../scripts/eda-common.sh"
PROJECT_ROOT=$(CDPATH= cd -- "$BLOCK_DIR/../.." && pwd)

TARGET=${TARGET:-analog-top}
PHASES=${PHASES:-'schematic func op xtb pwr'}
JOBS=${JOBS:-12}
export JOBS

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [ "${NO_RECORD:-0}" = 1 ]; then
    run_dir=$(mktemp -d)        # scripts/sim.sh records the run
else
    run_dir="$PROJECT_ROOT/runs/$TARGET/$stamp"
    mkdir -p "$run_dir"
fi
for d in work data assets; do mkdir -p "$BLOCK_DIR/$d"; done
# the container user (uid 1000) writes generated files next to the sources
chmod -R a+rwX "$BLOCK_DIR" 2>/dev/null || true

status=0
sh "$BLOCK_DIR/container.sh" "
    has() { case ' $PHASES ' in *\" \$1 \"*) return 0;; *) return 1;; esac; }
    if has schematic; then REGEN=${REGEN:-0} sh schematic.sh || echo 'FAIL: schematic.sh'; fi
    if has func; then sh func.sh || echo 'FAIL: func.sh'; fi
    if has op; then sh op.sh || echo 'FAIL: op.sh'; fi
    if has xtb; then sh xtb.sh || echo 'FAIL: xtb.sh'; fi
    if has pwr; then sh pwr.sh || echo 'FAIL: pwr.sh'; fi
" 2>&1 | tee "$run_dir/console.log" || status=$?

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
