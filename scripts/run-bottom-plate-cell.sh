#!/bin/sh
set -eu

. "$(dirname -- "$0")/eda-common.sh"

result_dir="$PROJECT_ROOT/simulations/gf180_bottom_plate_cell/work"
mkdir -p "$result_dir"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/simulations/gf180_bottom_plate_cell

        run_variant() {
            # $1 tag, $2 deck, $3 sensed node, $4 TBOT, $5 TTOP
            printf ".param TBOT=%s\n.param TTOP=%s\n" "$4" "$5" > work/switch_order.spice
            ngspice -b -o "work/$1.log" "$2"
            grep "^RESULT" "work/$1.log" > "work/$1_results.txt"
            echo "== $1 ($2, sensed=$3, TBOT=$4, TTOP=$5)" | tee "work/$1_summary.txt"
            awk -v SENSE="$3" -f check-results.awk "work/$1_results.txt" | tee -a "work/$1_summary.txt" || true
        }

        # A. Ramp on the bottom plate, comparator on the top node; bottom switch first.
        run_variant sense_top_bottom_first bottom_plate_cell.spice top 100n 102n
        # B. Same, conventional order (top switch first) for reference.
        run_variant sense_top_top_first    bottom_plate_cell.spice top 102n 100n
        # C. Ramp on the top node, comparator on the frozen bottom plate; bottom first.
        run_variant sense_bottom_bottom_first bottom_plate_cell_sense_bottom.spice bottom 100n 102n

        # Acceptance applies to the recommended variant (C).
        grep -q "^PASS" work/sense_bottom_bottom_first_summary.txt
        test -s work/bottom_plate_cell.csv
        test -s work/bottom_plate_cell_sense_bottom.csv
    '

printf '%s\n' "Summaries: $result_dir/*_summary.txt"
