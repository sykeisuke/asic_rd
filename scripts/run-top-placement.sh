#!/bin/sh
# Digital-on-top chip on the wafer.space gf180mcu project template: pad
# ring, the digital top as soft logic, the analog cells as hard macros
# with generated pins, placed and routed by LibreLane's Chip flow.
#
#   ./scripts/run-top-placement.sh           # macros, then the chip
#   ./scripts/run-top-placement.sh macros    # wrappers + their DRC/LVS only (minutes)
#   ./scripts/run-top-placement.sh chip      # the chip only (slow: full-die DRC)
#
# The provider's ID macros and render layer properties come from the
# template at WS_TEMPLATE_COMMIT (config/wafer_space_run3.mk), cloned
# into mixed_signal/top_placement/work/template. That needs the network
# once; the commit is checked every run.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

stage=${1:-all}
block="$PROJECT_ROOT/mixed_signal/top_placement"
tpl="$block/work/template"
log="$block/work/top-placement.log"
results="$block/work/top-placement.txt"
commit=$(awk '$1 == "WS_TEMPLATE_COMMIT" { print $3 }' \
         "$PROJECT_ROOT/config/wafer_space_run3.mk")

#- the container runs as uid 1000; LibreLane writes librelane/runs/
for d in "$block/work" "$block/librelane" "$block/physical/final_views"; do
    mkdir -p "$d"
    chmod 777 "$d"
done

if [ "$stage" != macros ]; then
    if [ ! -d "$tpl/.git" ]; then
        git clone -q --no-checkout \
            https://github.com/wafer-space/gf180mcu-project-template "$tpl"
    fi
    git -C "$tpl" cat-file -e "$commit^{commit}" 2>/dev/null ||
        git -C "$tpl" fetch -q origin
    git -C "$tpl" -c advice.detachedHead=false checkout -q "$commit"
    if [ "$(git -C "$tpl" rev-parse HEAD)" != "$commit" ]; then
        printf '%s\n' "FAIL: template is not at $commit"
        exit 1
    fi
    chmod -R a+rX "$tpl"
fi

status=0
"$block/container.sh" "bash build.sh $stage" >"$log" 2>&1 || status=$?

#- the lines the metrics record is made of; the log stays unread
grep -E '^REPORT: |^[A-Za-z][A-Za-z0-9_]* = |^[A-Za-z][A-Za-z0-9 /-]*: /' "$log" \
    >"$results" || :
if [ "$stage" != macros ]; then
    awk -f "$block/flow-errors.awk" "$log" >>"$results"
    #- the tagged tool messages of the step the flow stopped in
    last=$(ls -d "$block/librelane/runs/chip_top/"[0-9]*-* 2>/dev/null | sort -V | tail -n 1)
    if [ -n "$last" ] && [ ! -d "$block/librelane/runs/chip_top/final/gds" ]; then
        for f in "$last"/*.log; do
            [ -f "$f" ] && awk -f "$block/step-errors.awk" "$f" >>"$results"
        done
    fi
fi
cat "$results"
awk -v stage="$stage" -f "$block/check-top.awk" "$results" || status=1

run="$block/librelane/runs/chip_top"
final="$block/physical/final_views"
if [ "$stage" != macros ] && [ -s "$run/final/metrics.csv" ]; then
    cp "$run/final/metrics.csv" "$final/metrics.csv"
    [ -s "$run/final/metrics.json" ] && cp "$run/final/metrics.json" "$final/metrics.json"
    png=$(find "$run" -name 'chip_top.png' 2>/dev/null | sort | tail -n 1)
    if [ -n "$png" ]; then
        mkdir -p "$final/render"
        cp "$png" "$final/render/chip_top.png"
        printf '%s\n' "Render: $final/render/chip_top.png"
    fi
fi

printf '%s\n' "Results: $results"
printf '%s\n' "Log: $log"
exit "$status"
