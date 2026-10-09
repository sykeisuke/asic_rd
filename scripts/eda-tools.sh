#!/bin/sh
# Install the version-pinned Python EDA add-ons that are not part of the
# IIC-OSIC-TOOLS image into a repository-local, git-ignored user site
# (.eda-tools/). Run once per checkout: make tools
set -eu

. "$(dirname -- "$0")/eda-common.sh"

mkdir -p "$EDA_TOOLS_DIR"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc '
        set -euo pipefail
        export PYTHONUSERBASE=/foss/designs/.eda-tools
        pip install --quiet --user --no-warn-script-location \
            gf180mcu==1.0.0 cicpy==0.3.1
        python3 - <<PY
import gdsfactory, kfactory, gf180mcu, cicpy
print("gdsfactory", gdsfactory.__version__, "(image)")
print("kfactory  ", kfactory.__version__, "(image)")
print("gf180mcu  ", gf180mcu.__version__, "(.eda-tools, pinned)")
pdk = gf180mcu.PDK
pdk.activate()
c = pdk.get_component("nfet", w_gate=1.0, l_gate=0.28)
assert c is not None
print("gf180mcu PDK activated; sample nfet cell built OK")
print("cicpy    ", cicpy.__version__ if hasattr(cicpy, "__version__")
      else "0.3.1", "(.eda-tools, pinned)")
PY
    '

printf '%s\n' "Installed pinned EDA add-ons into $EDA_TOOLS_DIR"
