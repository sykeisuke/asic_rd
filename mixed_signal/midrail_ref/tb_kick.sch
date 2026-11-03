v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1160 120 -1200 {}
N 120 -1100 120 -1060 {}
N 290 -1160 290 -1200 {}
N 290 -1100 290 -1060 {}
N 460 -1160 460 -1200 {}
N 460 -1100 460 -1060 {}
N 630 -1160 630 -1200 {}
N 630 -1100 630 -1060 {}
N 120 -890 120 -930 {}
N 120 -830 120 -790 {}
N 120 -720 120 -760 {}
N 120 -660 120 -620 {}
N 120 -550 120 -590 {}
N 120 -490 120 -450 {}
N 1080 -1100 1120 -1100 {}
N 1000 -1160 1000 -1200 {}
N 1000 -1040 1000 -1000 {}
N 1560 -1100 1600 -1100 {}
N 1400 -1100 1270 -1100 {}
N 1400 -1080 1360 -1080 {}
N 1480 -1160 1480 -1200 {}
N 1480 -1040 1480 -1000 {}
N 1900 -1130 1900 -1170 {}
N 1900 -1070 1900 -1030 {}
N 1860 -1100 1820 -1100 {}
N 1860 -1080 1820 -1080 {}
N 1900 -880 1900 -920 {}
N 1900 -820 1900 -780 {}
N 1860 -850 1820 -850 {}
N 1860 -830 1820 -830 {}
N 2150 -1030 2150 -1070 {}
N 2150 -970 2150 -930 {}
N 2450 -1030 2450 -1070 {}
N 2450 -970 2450 -930 {}
N 2700 -1030 2700 -1070 {}
N 2700 -970 2700 -930 {}
N 2150 -790 2150 -830 {}
N 2150 -730 2150 -690 {}
T {TB_KICK  -  S2 event of one cell on the one output (vref = vbl), both charge directions} 60 -1330 0 0 0.7 0.7 {}
T {SUPPLY + BIAS} 60 -1260 0 0 0.4 0.4 {}
T {I_B = 12.36 uA} 250 -1010 0 0 0.3 0.3 {layer=4}
T {SWITCH CONTROLS} 60 -990 0 0 0.4 0.4 {}
T {DUT} 900 -1260 0 0 0.4 0.4 {}
T {CELL: S2 + S0 + C_S} 1820 -1260 0 0 0.4 0.4 {}
T {C_S 54.52 fF} 2190 -900 0 0 0.3 0.3 {layer=4}
C {devices/vsource.sym} 120 -1130 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1200 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1060 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/isource.sym} 290 -1130 0 0 {name=IREF value="\{IF\}"}
C {devices/lab_pin.sym} 290 -1200 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 290 -1060 0 0 {name=l4 sig_type=std_logic lab=ib}
C {devices/vsource.sym} 460 -1130 0 0 {name=VTOP0 value="\{TOP0\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -1200 0 0 {name=l5 sig_type=std_logic lab=vtop0}
C {devices/lab_pin.sym} 460 -1060 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1130 0 0 {name=VSNS value="0" savecurrent=false}
C {devices/lab_pin.sym} 630 -1200 0 0 {name=l7 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 630 -1060 0 0 {name=l8 sig_type=std_logic lab=vrefs}
C {devices/vsource.sym} 120 -860 0 0 {name=VSPRE value="PWL(0 2 \{TK-5n\} 2 \{TK-4n\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 -930 0 0 {name=l9 sig_type=std_logic lab=spre}
C {devices/lab_pin.sym} 120 -790 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -690 0 0 {name=VS2 value="PWL(0 0 \{TK\} 0 \{TK+0.1n\} 2)" savecurrent=false}
C {devices/lab_pin.sym} 120 -760 0 0 {name=l11 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 120 -620 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -520 0 0 {name=VBOT value="PWL(0 \{VBOT0\} \{TK\} \{VBOT0\} \{TK+0.1n\} \{VFE1\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -590 0 0 {name=l13 sig_type=std_logic lab=bots}
C {devices/lab_pin.sym} 120 -450 0 0 {name=l14 sig_type=std_logic lab=0}
C {midref_div.sym} 1000 -1100 0 0 {name=XD}
C {devices/lab_pin.sym} 1120 -1100 0 1 {name=l15 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1000 -1200 0 0 {name=l16 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1000 -1000 0 0 {name=l17 sig_type=std_logic lab=0}
C {midref_buf.sym} 1480 -1100 0 0 {name=XB}
C {devices/lab_pin.sym} 1600 -1100 0 1 {name=l18 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1270 -1100 0 0 {name=l19 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1360 -1080 0 0 {name=l20 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 1480 -1200 0 0 {name=l21 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 -1000 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1900 -1100 0 0 {name=S2 model=sws2}
C {devices/lab_pin.sym} 1900 -1170 0 0 {name=l23 sig_type=std_logic lab=vrefs}
C {devices/lab_pin.sym} 1900 -1030 0 0 {name=l24 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1820 -1100 0 0 {name=l25 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1820 -1080 0 0 {name=l26 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1900 -850 0 0 {name=SPRE model=swpre}
C {devices/lab_pin.sym} 1900 -920 0 0 {name=l27 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1900 -780 0 0 {name=l28 sig_type=std_logic lab=vtop0}
C {devices/lab_pin.sym} 1820 -850 0 0 {name=l29 sig_type=std_logic lab=spre}
C {devices/lab_pin.sym} 1820 -830 0 0 {name=l30 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 2150 -1000 0 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 2150 -1070 0 0 {name=l31 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 2150 -930 0 0 {name=l32 sig_type=std_logic lab=bot}
C {devices/capa.sym} 2450 -1000 0 0 {name=CTOPP value="\{CTOP\}" m=1}
C {devices/lab_pin.sym} 2450 -1070 0 0 {name=l33 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 2450 -930 0 0 {name=l34 sig_type=std_logic lab=0}
C {devices/res.sym} 2700 -1000 0 0 {name=RLKT value="1e15" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 2700 -1070 0 0 {name=l35 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 2700 -930 0 0 {name=l36 sig_type=std_logic lab=0}
C {devices/res.sym} 2150 -760 0 0 {name=RS0 value="\{RS0\}" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 2150 -830 0 0 {name=l37 sig_type=std_logic lab=bots}
C {devices/lab_pin.sym} 2150 -690 0 0 {name=l38 sig_type=std_logic lab=bot}
C {devices/code_shown.sym} 2950 -1330 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27
.param IF=1.23557e-05
.param VDD=3.3
.param CS_W=5u
.param CS_L=5u
.param CTOP=17.12f
.param RS2=1k
.param RS0=100
.param EPS=2.9297m
.param TK=1u
.param VBOT0=2.117
.param TOP0=2.9900
.param VFE1=2.0
.csparam cs_eps=\{EPS\}
.model swpre sw vt=1 vh=0.1 ron=100 roff=1e14
.model sws2 sw vt=1 vh=0.1 ron=\{RS2\} roff=1e14
.control
set num_threads=1
tran 0.1n 2.0u 0 1n
meas tran v0r avg v(vref) from=0.8u to=0.99u
let devr = abs(v(vref) - v0r)
meas tran pkr max devr from=1u to=2u
meas tran rr250 find devr at=1.25u
meas tran rr300 find devr at=1.3u
meas tran qk integ i(vsns) from=0.99u to=1.3u
let k_c1_pkr_mv = pkr * 1e3
let k_c1_rr250_mv = rr250 * 1e3
let k_c1_rr300_mv = rr300 * 1e3
let k_c1_qk_fc = qk * 1e15
let k_c1_v0r_v = v0r
print k_c1_pkr_mv
print k_c1_rr250_mv
print k_c1_rr300_mv
print k_c1_qk_fc
print k_c1_v0r_v
meas tran tsra when devr=$&cs_eps cross=last from=1u to=1.999u
let k_c1_tsr_ns = (tsra - 1u) * 1e9
print k_c1_tsr_ns
alterparam TOP0=1.7500
alterparam VFE1=0.5
reset
tran 0.1n 2.0u 0 1n
meas tran v0r avg v(vref) from=0.8u to=0.99u
let devr = abs(v(vref) - v0r)
meas tran pkr max devr from=1u to=2u
meas tran rr250 find devr at=1.25u
meas tran rr300 find devr at=1.3u
meas tran qk integ i(vsns) from=0.99u to=1.3u
let k_c2_pkr_mv = pkr * 1e3
let k_c2_rr250_mv = rr250 * 1e3
let k_c2_rr300_mv = rr300 * 1e3
let k_c2_qk_fc = qk * 1e15
let k_c2_v0r_v = v0r
print k_c2_pkr_mv
print k_c2_rr250_mv
print k_c2_rr300_mv
print k_c2_qk_fc
print k_c2_v0r_v
meas tran tsra when devr=$&cs_eps cross=last from=1u to=1.999u
let k_c2_tsr_ns = (tsra - 1u) * 1e9
print k_c2_tsr_ns
quit
.endc"}
