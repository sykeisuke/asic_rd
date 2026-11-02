#!/bin/sh
# Refresh chip_integration/inputs/ from where each input is made.
# The flow itself only ever reads inputs/; this script is the one place
# that knows where the copies come from. Run it on the host from the
# repository (it calls the container only to regenerate the analog GDS).
#
#   chip_integration/scripts/fetch_inputs.sh            # all three inputs
#   ANALOG_GDS=/path/x.gds ANALOG_PINS=/path/x.csv \
#       chip_integration/scripts/fetch_inputs.sh         # a different analog GDS
#   REGEN=0 chip_integration/scripts/fetch_inputs.sh     # copy, do not regenerate
#
# inputs/digital   the hardened digital top, as the digital flow left it
#                  (digital/asic_digital_top/physical/final_views)
# inputs/analog    the analog top GDS + its pin contract (name, direction,
#                  use: a GDS carries pin shapes and names, not directions)
# inputs/template  the wafer.space gf180mcu-project-template files this
#                  chip uses, at WS_TEMPLATE_COMMIT (config/wafer_space_run3.mk)
#
# Ends with inputs/MANIFEST.sha256, one line per copied file.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ROOT=$(CDPATH= cd -- "$HERE/.." && pwd)
IN="$HERE/inputs"
REGEN=${REGEN:-1}
commit=$(awk '$1 == "WS_TEMPLATE_COMMIT" { print $3 }' "$ROOT/config/wafer_space_run3.mk")
TEMPLATE_URL=${TEMPLATE_URL:-https://github.com/wafer-space/gf180mcu-project-template}

mkdir -p "$IN/digital" "$IN/analog" "$IN/template" "$HERE/work"
chmod 777 "$HERE/work"

# --- digital: the hardened top, used as is --------------------------------
fv="$ROOT/digital/asic_digital_top/physical/final_views"
for f in gds/asic_digital_top.gds lef/asic_digital_top.lef \
         nl/asic_digital_top.nl.v metrics.json render/asic_digital_top.png; do
    [ -s "$fv/$f" ] || { echo "FAIL: missing $fv/$f (make digital-physical)"; exit 1; }
    cp "$fv/$f" "$IN/digital/"
done
cp "$ROOT/digital/asic_digital_top/physical/physical.sdc" "$IN/digital/asic_digital_top.sdc"

# --- analog: the GDS and its pin contract ---------------------------------
if [ -n "${ANALOG_GDS:-}" ]; then
    [ -n "${ANALOG_PINS:-}" ] || { echo "FAIL: ANALOG_GDS needs ANALOG_PINS (csv)"; exit 1; }
    cp "$ANALOG_GDS" "$IN/analog/wsa_analog_top.gds"
    cp "$ANALOG_PINS" "$IN/analog/wsa_analog_top.pins.csv"
elif [ ! -f "$ROOT/mixed_signal/top_placement/analog_macro.py" ]; then
    #- the placeholder generator is not in this checkout: keep the copy
    echo "REPORT: no mixed_signal/top_placement/analog_macro.py; inputs/analog kept as is"
else
    tp="$ROOT/mixed_signal/top_placement"
    if [ "$REGEN" = 1 ]; then
        #- the placeholder macro generator (outline, pins, rings, MIMs; no
        #- transistors), in the pinned container
        "$tp/container.sh" 'python3 analog_macro.py' | grep -E '^wsa_analog_top_' || :
    fi
    src="$tp/work/macros/wsa_analog_top"
    [ -s "$src/gds/wsa_analog_top.gds" ] || { echo "FAIL: no $src/gds/wsa_analog_top.gds"; exit 1; }
    cp "$src/gds/wsa_analog_top.gds" "$IN/analog/"
    #- the contract: the generator's pins.json, reduced to what a GDS
    #- cannot say (direction, use) plus the port order
    python3 - "$src/pins.json" "$IN/analog/wsa_analog_top.pins.csv" <<'EOF'
import json, sys
pins = json.load(open(sys.argv[1]))["pins"]
with open(sys.argv[2], "w") as f:
    f.write("# name,direction,use,status  (port order = row order)\n")
    for p in pins:
        f.write(f"{p['name']},{p['direction']},{p['use']},{p['status']}\n")
EOF
fi

# --- template: the provider's files at the pinned commit -------------------
tpl="$HERE/work/template_clone"
if [ ! -d "$tpl/.git" ]; then
    git clone -q --no-checkout "$TEMPLATE_URL" "$tpl"
fi
git -C "$tpl" cat-file -e "$commit^{commit}" 2>/dev/null || git -C "$tpl" fetch -q origin
git -C "$tpl" -c advice.detachedHead=false checkout -q "$commit"
[ "$(git -C "$tpl" rev-parse HEAD)" = "$commit" ] || { echo "FAIL: template not at $commit"; exit 1; }
rm -rf "$IN/template"
mkdir -p "$IN/template"
( cd "$tpl" && cp --parents LICENSE README.md \
    librelane/config.yaml librelane/chip_top.sdc librelane/gf180mcu_render.lyp \
    librelane/slots/slot_1x0p5.yaml librelane/pdn/pdn_cfg.tcl \
    librelane/macros/macros_3v3.yaml \
    src/chip_top.sv src/chip_core.sv src/slot_defines.svh \
    "$IN/template/" )
for ip in qrcode_id shuttle_id project_id marker logo; do
    d=ip/gf180mcu_ws_ip__$ip
    for v in gds lef lib vh; do
        mkdir -p "$IN/template/$d/$v"
        cp "$tpl/$d/$v/"* "$IN/template/$d/$v/"
    done
done
#- the canonical repository, whatever TEMPLATE_URL mirror was cloned:
#- the commit hash is what identifies the files
printf '%s\n' https://github.com/wafer-space/gf180mcu-project-template "$commit" \
    >"$IN/template/COMMIT"

# --- manifest ---------------------------------------------------------------
( cd "$IN" && find digital analog template -type f ! -name MANIFEST.sha256 | sort |
      xargs sha256sum ) >"$IN/MANIFEST.sha256"
chmod -R a+rwX "$IN"
echo "inputs_files = $(wc -l <"$IN/MANIFEST.sha256")"
echo "template_commit = $commit"
echo "Manifest: $IN/MANIFEST.sha256"
