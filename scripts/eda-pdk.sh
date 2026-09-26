#!/bin/sh
# Fetch the frozen GF180MCU PDK libraries that the IIC-OSIC-TOOLS image does
# not ship (notably the 3.3 V standard cells gf180mcu_as_sc_mcu7t3v3 and the
# gf180mcu_ocd_io pads) into a repository-local, git-ignored PDK root
# (.eda-tools/pdk) with ciel, at the project's frozen PDK commit.
# Run once per checkout: make pdk   (about 1 GB, under a minute)
set -eu

. "$(dirname -- "$0")/eda-common.sh"

PDK_COMMIT=f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7
mkdir -p "$EDA_TOOLS_DIR/pdk"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc "
        set -euo pipefail
        root=/foss/designs/.eda-tools/pdk
        if [ -f \"\$root/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/lib/gf180mcu_as_sc_mcu7t3v3__tt_025C_3v30.lib\" ]; then
            echo 'PDK libraries already present'
        else
            ciel enable --pdk-root \"\$root\" --pdk-family gf180mcu \
                --include-libraries gf180mcu_as_sc_mcu7t3v3 \
                --include-libraries gf180mcu_fd_pr \
                --include-libraries gf180mcu_fd_io \
                --include-libraries gf180mcu_ocd_io \
                $PDK_COMMIT
        fi
        ls \"\$root/gf180mcuD/libs.ref\"
    "

printf '%s\n' "PDK root with 3.3 V libraries: $EDA_TOOLS_DIR/pdk (commit $PDK_COMMIT)"
