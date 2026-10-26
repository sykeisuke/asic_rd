#!/bin/sh
# gm/Id tables (L 0.4..0.9 um, finger W 1/2/4 um, VSB 0/0.2 V) and the
# resistor characterisation for size_bg.py. Run through the block's wrapper:
#
#   ./container.sh 'sh lut/build.sh'
#
# Writes work/lut/{nfet,pfet}_03v3.npz and data/res_char.csv.
set -eu
cd "$(dirname -- "$0")"
W=../work/lut
mkdir -p "$W" ../data
printf 'set num_threads=1\n' > "$W/.spiceinit"
for dev in nfet_03v3 pfet_03v3; do
    case $dev in
        nfet_03v3) vgn='g 0'; vdn='d 0'; vbn='b 0' ;;
        pfet_03v3) vgn='0 g'; vdn='0 d'; vbn='0 b' ;;
    esac
    rm -f "$W/ts_$dev.txt" "$W/ts_$dev.idx"
    sed -e "s#@DEV@#$dev#" -e "s#@CORNER@#typical#" -e "s#@TEMP@#27#" \
        -e "s#@OUT@#ts_$dev#g" -e "s#@VGN@#$vgn#" -e "s#@VDN@#$vdn#" -e "s#@VBN@#$vbn#" \
        -e "s#@VSB2@#-0.2#g" techsweep.spice > "$W/ts_$dev.spice"
    (cd "$W" && ngspice -b -o "ts_$dev.log" "ts_$dev.spice" >/dev/null 2>&1) || true
    [ -s "$W/ts_$dev.txt" ] || { echo "FAIL: $dev techsweep produced no data"; exit 1; }
    python3 build_tables.py "$W/ts_$dev.txt" "$W/ts_$dev.idx" "$W/$dev.npz" || { echo "FAIL: build_tables $dev"; exit 1; }
    rm -f "$W/ts_$dev.txt"
done
echo "corner,temp,ppolyf_u,ppolyf_u_1k,ppolyf_u_2k,ppolyf_u_3k,npolyf_u,nplus_u,pplus_u" > ../data/res_char.csv
for rc in res_typical res_ss res_ff; do
    sed "s#@RCORNER@#$rc#g" res_char.spice > "$W/res_$rc.spice"
    (cd "$W" && ngspice -b -o "res_$rc.log" "res_$rc.spice" >/dev/null 2>&1) || true
    grep '^RES ' "$W/res_$rc.log" | awk '{printf "%s,%s", $2, $3; for (i = 4; i <= NF; i++) printf ",%s", $i; printf "\n"}' >> ../data/res_char.csv
done
n=$(($(wc -l < ../data/res_char.csv) - 1))
[ "$n" -eq 9 ] || { echo "FAIL: resistor characterisation has $n of 9 rows"; exit 1; }
echo "PASS: gm/Id tables and resistor characterisation built"
