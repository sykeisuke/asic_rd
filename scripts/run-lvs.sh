#!/bin/sh
# KLayout LVS: a generated cell's GDS against a netlist you name.
#
#   ./scripts/run-lvs.sh CELL [NETLIST]
#   ./scripts/run-lvs.sh                 # every cell, against spice/<CELL>.spice
#
# NETLIST defaults to mixed_signal/analog_layout/spice/<CELL>.spice --
# the netlist the layout was generated from. Point it somewhere else to
# compare the layout against a netlist it was NOT built from, which is
# the comparison that actually proves something. The path may be
# absolute or relative to the repository root.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

block="$PROJECT_ROOT/mixed_signal/analog_layout"
mkdir -p "$block/work"
chmod 777 "$block/work"

gdsdir="$block/physical/final_views/gds"

# The container script reads CELL NETLIST pairs, "-" meaning the default.
# Pairs, not a cell list plus an optional netlist: with two cells and no
# netlist the second cell reads as a netlist path and LVS runs against a
# file that is not one.
if [ "$#" -ge 2 ]; then
    net=$2
    case "$net" in
        /*) : ;;
        *) net="$PROJECT_ROOT/$net" ;;
    esac
    if [ ! -f "$net" ]; then
        printf '%s\n' "No such netlist: $net" >&2
        exit 1
    fi
    # the container sees the repository at /foss/designs
    net="/foss/designs/$(printf '%s' "$net" | sed "s#^$PROJECT_ROOT/##")"
    set -- "$1" "$net"
elif [ "$#" -eq 1 ]; then
    set -- "$1" -
else
    args=""
    for f in "$gdsdir"/*.gds; do
        [ -f "$f" ] || continue
        args="$args $(basename "$f" .gds) -"
    done
    if [ -z "$args" ]; then
        printf '%s\n' 'No GDS to compare. Run: make layout' >&2
        exit 1
    fi
    # shellcheck disable=SC2086
    set -- $args
fi

cells=""
status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -e PYTHONUSERBASE=/foss/designs/.eda-tools \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/mixed_signal/analog_layout
        : > work/lvs.txt
        while [ "$#" -ge 2 ]; do
            if [ "$2" = "-" ]; then
                python3 signoff.py lvs "$1" | tee -a work/lvs.txt
            else
                python3 signoff.py lvs "$1" "$2" | tee -a work/lvs.txt
            fi
            shift 2
        done
        awk -f check-lvs.awk work/lvs.txt
    ' -- "$@" || status=$?

while [ "$#" -ge 2 ]; do
    cells="$cells $1"
    shift 2
done

printf '%s\n' "Results: $block/work/lvs.txt"
for cell in $cells; do
    [ -d "$block/work/$cell-lvs" ] &&
        printf '%s\n' "Report: $block/work/$cell-lvs/"
done

exit "$status"
