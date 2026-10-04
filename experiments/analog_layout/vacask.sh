#!/bin/sh
# VACASK transient-noise experiment on GF180 (Murmann's suggestion).
# The pinned container ships vacask 764f693 (aarch64) but an older ngspice->VACASK
# converter without MOSFET/GF180 support; upstream's *python* (gf180tovc.py) works
# with the container binary after two small patches. Everything lands in the
# git-ignored .eda-tools/.
# Usage: experiments/analog_layout/vacask.sh [N_SEEDS]
set -eu
REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
. "$REPO_ROOT/scripts/eda-common.sh"
PROJECT_ROOT="$REPO_ROOT"
N=${1:-40}
if [ ! -d "$REPO_ROOT/.eda-tools/vacask-src/vacask/python" ]; then
    mkdir -p "$REPO_ROOT/.eda-tools/vacask-src"
    curl -sL "https://codeberg.org/arpadbuermen/VACASK/archive/main.tar.gz" -o "$REPO_ROOT/.eda-tools/vacask-src/main.tar.gz"
    tar -xzf "$REPO_ROOT/.eda-tools/vacask-src/main.tar.gz" -C "$REPO_ROOT/.eda-tools/vacask-src"
fi
"$DOCKER_CLI" run --rm --entrypoint /bin/bash \
    -v "$PROJECT_ROOT:/foss/designs:rw" "$EDA_IMAGE" -lc "
        set -euo pipefail
        R=/foss/designs/.eda-tools/pdk-vacask; M=\$R/gf180mcuD/libs.tech/vacask/models
        if [ ! -f \$M/mos_tt.lib ]; then
            mkdir -p \$R/gf180mcuD/libs.tech \$R/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu9t5v0 \$R/gf180mcuD/libs.ref/gf180mcu_fd_io
            cp -r /foss/pdks/gf180mcuD/libs.tech/ngspice \$R/gf180mcuD/libs.tech/
            cp -r /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu9t5v0/spice \$R/gf180mcuD/libs.ref/gf180mcu_fd_sc_mcu9t5v0/
            cp -r /foss/pdks/gf180mcuD/libs.ref/gf180mcu_fd_io/spice \$R/gf180mcuD/libs.ref/gf180mcu_fd_io/
            ( cd \$R/gf180mcuD/libs.tech/ngspice && PDK_ROOT=\$R PDK=gf180mcuD PYTHONPATH=/foss/designs/.eda-tools/vacask-src/vacask/python python3 -m gf180tovc > \$R/gf180tovc.log 2>&1 )
            # container binary lacks inline behavioural instances: linearise the SAB resistors
            python3 - <<PY
import re, glob
pat = re.compile(r'^(\s*)rb \(1 2\) \(\s*\n\s*\n?\s*i=v\(1,2\)/\(r_temp\*r_n\*\(r_rsh0[^\n]*\n\s*\)\n', re.M)
for f in glob.glob('\$M/*.lib'):
    s = open(f).read(); s2, n = pat.subn(r'\1rb (1 2) gf180_default_mod_r r=r_temp*r_n*r_rsh0\n', s)
    if n: open(f,'w').write(s2)
PY
            sed -i 's|/opt/vacask/lib/vacask/mod|/foss/tools/vacask/lib/vacask/mod|' \$R/gf180mcuD/libs.tech/vacask/.vacaskrc.toml
        fi
        W=/foss/designs/experiments/analog_layout/work/vacask; mkdir -p \$W; cd \$W
        cp \$R/gf180mcuD/libs.tech/vacask/.vacaskrc.toml .
        export PDK_ROOT=\$R PDK=gf180mcuD PYTHONPATH=/foss/tools/vacask/lib/vacask/python
        python3 ../../vacask_tg_noise.py write tg_noise_seeds.sim $N
        vacask -qp tg_noise_seeds.sim > vacask.log 2>&1
        python3 ../../vacask_tg_noise.py eval . $N
    "
