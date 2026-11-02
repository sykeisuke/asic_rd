#!/bin/sh
# Fetch the frozen GF180MCU PDK libraries that the IIC-OSIC-TOOLS image does
# not ship (notably the 3.3 V standard cells gf180mcu_as_sc_mcu7t3v3 and the
# gf180mcu_ocd_io pads) into a repository-local, git-ignored PDK root
# (.eda-tools/pdk) with ciel, at the project's frozen PDK commit.
# Run once per checkout: make pdk   (about 2.5 GB, a few minutes). The commit
# is PDK_COMMIT from eda-common.sh (the project's frozen baseline); re-run
# after a baseline change and the root switches to the new version.
set -eu

. "$(dirname -- "$0")/eda-common.sh"

mkdir -p "$EDA_TOOLS_DIR/pdk"

"$DOCKER_CLI" run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" \
    "$EDA_IMAGE" -lc "
        set -euo pipefail
        root=/foss/designs/.eda-tools/pdk
        enabled=\$(readlink \"\$root/gf180mcuD\" 2>/dev/null || true)
        if [ -f \"\$root/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/lib/gf180mcu_as_sc_mcu7t3v3__tt_025C_3v30.lib\" ] \
           && [ -d \"\$root/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu7t5v0\" ] \
           && case \"\$enabled\" in *$PDK_COMMIT*) true;; *) false;; esac; then
            echo \"PDK libraries already present at $PDK_COMMIT\"
        else
            ciel enable --pdk-root \"\$root\" --pdk-family gf180mcu \
                --include-libraries gf180mcu_as_sc_mcu7t3v3 \
                --include-libraries gf180mcu_fd_sc_mcu7t5v0 \
                --include-libraries gf180mcu_fd_pr \
                --include-libraries gf180mcu_fd_io \
                --include-libraries gf180mcu_ocd_io \
                $PDK_COMMIT
        fi
        readlink \"\$root/gf180mcuD\" || true
        ls \"\$root/gf180mcuD/libs.ref\"
    "

printf '%s\n' "PDK root with 3.3 V libraries: $EDA_TOOLS_DIR/pdk (commit $PDK_COMMIT)"
