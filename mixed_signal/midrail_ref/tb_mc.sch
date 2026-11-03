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
N 980 -1100 1020 -1100 {}
N 900 -1160 900 -1200 {}
N 900 -1040 900 -1000 {}
N 1460 -1100 1500 -1100 {}
N 1300 -1100 1170 -1100 {}
N 1300 -1080 1260 -1080 {}
N 1380 -1160 1380 -1200 {}
N 1380 -1040 1380 -1000 {}
T {TB_MC  -  VDD/2 offset and follower headroom of midref under PDK mismatch, one draw} 60 -1330 0 0 0.7 0.7 {}
T {SUPPLY + BIAS} 60 -1260 0 0 0.4 0.4 {}
T {I_B = 12.36 uA} 250 -1010 0 0 0.3 0.3 {layer=4}
T {DUT} 800 -1260 0 0 0.4 0.4 {}
C {devices/vsource.sym} 120 -1130 0 0 {name=VDD_SOURCE value="3.3" savecurrent=false}
C {devices/lab_pin.sym} 120 -1200 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1060 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/isource.sym} 290 -1130 0 0 {name=IREF value="\{IF\}"}
C {devices/lab_pin.sym} 290 -1200 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 290 -1060 0 0 {name=l4 sig_type=std_logic lab=ib}
C {midref_div.sym} 900 -1100 0 0 {name=XD}
C {devices/lab_pin.sym} 1020 -1100 0 1 {name=l5 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 900 -1200 0 0 {name=l6 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -1000 0 0 {name=l7 sig_type=std_logic lab=0}
C {midref_buf.sym} 1380 -1100 0 0 {name=XB}
C {devices/lab_pin.sym} 1500 -1100 0 1 {name=l8 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1170 -1100 0 0 {name=l9 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1260 -1080 0 0 {name=l10 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 1380 -1200 0 0 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1380 -1000 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 800 -900 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.param sw_stat_mismatch=1
.temp 27
.param IF=1.23557e-05
.options seed=20261008
.control
set num_threads=1
op
let er = v(vref) - 3.3 / 2
echo MC 1 $&er
let hr1 = abs(@m.xb.xm1.m0[vds]) - abs(@m.xb.xm1.m0[vdsat])
let hr4 = abs(@m.xb.xm4.m0[vds]) - abs(@m.xb.xm4.m0[vdsat])
echo HR 1 $&hr1 $&hr4 $&er
quit
.endc"}
