#!/bin/sh
# Run a gdsfactory sandbox script inside the pinned container, then run the
# frozen PDK's KLayout DRC deck (gf180mcuD: 5LM, 11K top metal, MIM option B)
# on the GDS it writes into work/.
# Usage: experiments/analog_layout/run.sh experiments/analog_layout/<script>.py [gds basename without .gds]
set -eu
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
. "$REPO_ROOT/scripts/eda-common.sh"
# eda-common.sh derives PROJECT_ROOT (and reuses the name script_dir) from the
# caller's directory, assuming scripts/; this script lives two levels down.
PROJECT_ROOT="$REPO_ROOT"
py=${1:?python script path relative to repo root}
name=${2:-$(basename "$py" .py)}
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc "
        set -euo pipefail
        export PYTHONUSERBASE=/foss/designs/.eda-tools
        cd /foss/designs/$(dirname "$py")
        mkdir -p work
        python3 $(basename "$py")
        gds=\$(ls -t work/*.gds | head -1)
        echo \"--- KLayout DRC (frozen PDK deck, gf180mcuD) on \$gds ---\"
        klayout -b -r /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc \
            -rd input=\"\$gds\" -rd report=work/${name}.lyrdb \
            -rd variant=gf180mcuD -rd run_mode=deep -rd threads=max \
            2>&1 | grep -E 'DRC RESULT|violations\\)|Executing rule' | grep -vE 'Executing rule' || true
        python3 - <<PY
import xml.etree.ElementTree as ET, collections
t = ET.parse('work/${name}.lyrdb'); root = t.getroot()
cats = collections.Counter(i.findtext('category').strip(\"'\") for i in root.iter('item'))
print('violations by rule:', dict(cats) if cats else 'none')
PY
    "
