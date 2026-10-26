#!/bin/sh
# Short-L gm/Id tables and device noise for size_v3.py. Run through the
# block's container wrapper:
#
#   ./container.sh 'sh lut/build.sh'
#
# Writes work/lut/{nfet,pfet}_03v3.pkl (L = 0.28, 0.30, 0.32, 0.34, 0.36 um,
# W = 2 um nf = 1; build_lut.py of ../../simulations/gf180_gmid_lut with
# only the L grid and paths changed) and data/device_noise.csv.
set -eu
cd "$(dirname -- "$0")"
mkdir -p ../work/lut ../data
printf 'set num_threads=1\n' > .spiceinit
for dev in nfet_03v3 pfet_03v3; do
    rm -f "../work/lut/techsweep_${dev}.txt"
    ngspice -b -o "../work/lut/techsweep_${dev}.log" "techsweep_${dev}.spice" >/dev/null 2>&1 || true
    [ -s "../work/lut/techsweep_${dev}.txt" ] || { echo "FAIL: ${dev} techsweep produced no data"; exit 1; }
    python3 build_lut.py "$dev" 2.0 1
    rm -f "../work/lut/techsweep_${dev}.txt"
done
ngspice -b -o ../work/lut/noise_char.log noise_char.spice >/dev/null 2>&1 || true
{
    echo "dev,l_um,vgs,id,gm,s1k,s10k,s100k,s1m,s10m,s100m,s1g"
    grep '^NZ ' ../work/lut/noise_char.log | awk '{l=$3; sub(/u$/,"",l); printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",$2,l,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13}'
} > ../data/device_noise.csv
n=$(($(wc -l < ../data/device_noise.csv) - 1))
echo "device_noise_points = $n"
[ "$n" -eq 280 ] || { echo "FAIL: expected 280 noise points"; exit 1; }
echo "PASS: short-L tables and device noise built"
