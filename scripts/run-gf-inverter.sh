#!/bin/sh
# gdsfactory inverter on the gf180mcu PDK plugin: draw INV_GF, render it,
# then KLayout DRC and LVS against mixed_signal/analog_layout/misc/INV_GF.spice.
#
#   ./scripts/run-gf-inverter.sh
#
# The cell is mixed_signal/analog_layout/misc/gfp_misc/cells/inverter.py,
# a GDSFactory+ project folder. When the GDSFactory+ VS Code extension is
# installed on this host its indexer is run on the folder as well, to show
# the extension sees the same factory; that step is skipped, not failed,
# without the extension.
#
# Needs the gf180mcu plugin: run `make tools` once per checkout.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

block="$PROJECT_ROOT/mixed_signal/analog_layout"
misc="$block/misc"
#- the container runs as uid 1000 and these are created on the host as
#- root; the build writes into all of them
for d in "$block/work" "$misc/build" "$misc/build/gds" "$misc/build/render"; do
    mkdir -p "$d"
    chmod 777 "$d"
done

if [ ! -d "$EDA_TOOLS_DIR/lib/python3.12/site-packages/gf180mcu" ]; then
    printf '%s\n' 'gf180mcu gdsfactory plugin is not installed. Run: make tools' >&2
    exit 1
fi

results="$block/work/gf-inverter.txt"
status=0
"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    -e PYTHONUSERBASE=/foss/designs/.eda-tools \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        cd /foss/designs/mixed_signal/analog_layout
        gds=misc/build/gds/INV_GF.gds
        #- a failed build must not leave the previous run''s verdicts behind
        rm -f "$gds" work/INV_GF-drc.lyrdb work/INV_GF-density.lyrdb
        rm -rf work/INV_GF-lvs
        python3 misc/build.py | tee work/gf-inverter.txt
        python3 signoff.py drc INV_GF --gds "$gds" | tee -a work/gf-inverter.txt
        python3 signoff.py lvs INV_GF misc/INV_GF.spice --gds "$gds" \
            | tee -a work/gf-inverter.txt
        awk -f misc/check-gf-inverter.awk work/gf-inverter.txt
    ' || status=$?

# GDSFactory+ extension indexer (host side, WSL/VS Code server install)
gfp=$(ls -d "$HOME"/.vscode-server/extensions/gdsfactory.gdsfactoryplus-*/bin/gfp \
      2>/dev/null | tail -n 1 || true)
if [ -n "$gfp" ] && [ -x "$gfp" ]; then
    idx="$block/work/gf-inverter-index.json"
    "$gfp" --cwd "$misc" index --factories >"$idx" 2>/dev/null || :
    names=$(python3 - "$idx" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
except Exception:
    data = []
# one record per indexed file, each with its list of factories
names = []
for rec in data if isinstance(data, list) else []:
    for fac in rec.get("factories", []) if isinstance(rec, dict) else []:
        if isinstance(fac, dict) and fac.get("name"):
            names.append(str(fac["name"]))
print(",".join(names))
PY
)
    n=$(printf '%s\n' "$names" | awk -F, '{ print ($0 == "" ? 0 : NF) }')
    printf '%s\n' "gfp_factories = $n"
    case ",$names," in
        *,INV_GF,*|*.INV_GF,*)
            printf '%s\n' "PASS: GDSFactory+ indexer ($(basename "$(dirname "$(dirname "$gfp")")")) lists INV_GF" ;;
        *)
            printf '%s\n' "FAIL: GDSFactory+ indexer did not list INV_GF (found: ${names:-none})"
            status=1 ;;
    esac
else
    printf '%s\n' "REPORT: GDSFactory+ extension not found on this host; indexer step skipped"
fi

printf '%s\n' "Results: $results"
[ -f "$misc/build/gds/INV_GF.gds" ] && printf '%s\n' "Layout: $misc/build/gds/INV_GF.gds"
[ -f "$misc/build/render/INV_GF.png" ] && printf '%s\n' "Render: $misc/build/render/INV_GF.png"
[ -f "$block/work/INV_GF-drc.lyrdb" ] && printf '%s\n' "Report: $block/work/INV_GF-drc.lyrdb"
[ -d "$block/work/INV_GF-lvs" ] && printf '%s\n' "Report: $block/work/INV_GF-lvs/"

exit "$status"
