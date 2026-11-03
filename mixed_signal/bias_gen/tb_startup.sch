v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1210 120 -1250 {}
N 120 -1150 120 -1110 {}
N 360 -1210 360 -1250 {}
N 360 -1150 360 -1110 {}
N 800 -1210 800 -1250 {}
N 800 -1150 800 -1110 {}
N 760 -1180 720 -1180 {}
N 760 -1160 720 -1160 {}
N 1020 -1210 1020 -1250 {}
N 1020 -1150 1020 -1110 {}
N 980 -1180 940 -1180 {}
N 980 -1160 940 -1160 {}
N 600 -960 600 -1000 {}
N 600 -720 600 -680 {}
N 700 -920 820 -920 {}
N 700 -895 760 -895 {}
N 700 -870 820 -870 {}
N 700 -845 760 -845 {}
N 700 -820 820 -820 {}
N 700 -795 760 -795 {}
N 700 -770 820 -770 {}
N 180 -410 180 -370 {}
N 140 -440 100 -440 {}
N 180 -470 180 -510 {}
N 180 -440 220 -440 {}
N 260 -270 260 -310 {}
N 260 -210 260 -170 {}
N 440 -410 440 -370 {}
N 400 -440 360 -440 {}
N 440 -470 440 -510 {}
N 440 -440 480 -440 {}
N 520 -270 520 -310 {}
N 520 -210 520 -170 {}
N 700 -410 700 -370 {}
N 660 -440 620 -440 {}
N 700 -470 700 -510 {}
N 700 -440 740 -440 {}
N 780 -270 780 -310 {}
N 780 -210 780 -170 {}
N 960 -410 960 -370 {}
N 920 -440 880 -440 {}
N 960 -470 960 -510 {}
N 960 -440 1000 -440 {}
N 1040 -270 1040 -310 {}
N 1040 -210 1040 -170 {}
N 1220 -410 1220 -370 {}
N 1180 -440 1140 -440 {}
N 1220 -470 1220 -510 {}
N 1220 -440 1260 -440 {}
N 1300 -270 1300 -310 {}
N 1300 -210 1300 -170 {}
N 1480 -470 1480 -510 {}
N 1440 -440 1400 -440 {}
N 1480 -410 1480 -370 {}
N 1480 -440 1520 -440 {}
N 1560 -270 1560 -310 {}
N 1560 -210 1560 -170 {}
N 1740 -470 1740 -510 {}
N 1700 -440 1660 -440 {}
N 1740 -410 1740 -370 {}
N 1740 -440 1780 -440 {}
N 1820 -270 1820 -310 {}
N 1820 -210 1820 -170 {}
T {TB_STARTUP  -  start-up of bias_gen: supply ramp, and the forced dead state released} 40 -1340 0 0 0.7 0.7 {}
T {TRAMP 100 ns} 60 -1040 0 0 0.3 0.3 {layer=4}
T {DEAD-STATE HOLD, released at TREL = 10 us} 300 -1290 0 0 0.4 0.4 {}
T {CONSUMER DIODES, 0 V AMMETERS} 60 -560 0 0 0.4 0.4 {}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD value="PWL(0 0 \{TRAMP\} 3.3)" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 360 -1180 0 0 {name=VHC value="PWL(0 1 \{TREL\} 1 \{TREL+10n\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 360 -1250 0 0 {name=l3 sig_type=std_logic lab=hc}
C {devices/lab_pin.sym} 360 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 800 -1180 0 0 {name=SHP model=swh}
C {devices/lab_pin.sym} 800 -1250 0 0 {name=l5 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 800 -1110 0 0 {name=l6 sig_type=std_logic lab=xg.pb}
C {devices/lab_pin.sym} 720 -1180 0 0 {name=l7 sig_type=std_logic lab=hc}
C {devices/lab_pin.sym} 720 -1160 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1020 -1180 0 0 {name=SHN model=swh}
C {devices/lab_pin.sym} 1020 -1250 0 0 {name=l9 sig_type=std_logic lab=xg.nb}
C {devices/lab_pin.sym} 1020 -1110 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 940 -1180 0 0 {name=l11 sig_type=std_logic lab=hc}
C {devices/lab_pin.sym} 940 -1160 0 0 {name=l12 sig_type=std_logic lab=0}
C {bias_gen.sym} 600 -840 0 0 {name=XG}
C {devices/lab_pin.sym} 600 -1000 0 0 {name=l13 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 600 -680 0 0 {name=l14 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 820 -920 0 1 {name=l15 sig_type=std_logic lab=icmp0}
C {devices/lab_pin.sym} 760 -895 0 1 {name=l16 sig_type=std_logic lab=icmp1}
C {devices/lab_pin.sym} 820 -870 0 1 {name=l17 sig_type=std_logic lab=icmp2}
C {devices/lab_pin.sym} 760 -845 0 1 {name=l18 sig_type=std_logic lab=icmp3}
C {devices/lab_pin.sym} 820 -820 0 1 {name=l19 sig_type=std_logic lab=iramp}
C {devices/lab_pin.sym} 760 -795 0 1 {name=l20 sig_type=std_logic lab=ivref}
C {devices/lab_pin.sym} 820 -770 0 1 {name=l21 sig_type=std_logic lab=ivbl}
C {symbols/pfet_03v3.sym} 160 -440 0 0 {name=XLC0
L=0.28u
W=1u
nf=1
m=1
ad=0.18p
pd=2.36u
as=0.18p
ps=2.36u
nrd=0.18
nrs=0.18
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 180 -370 0 0 {name=l22 sig_type=std_logic lab=lc0}
C {devices/lab_pin.sym} 100 -440 0 0 {name=l23 sig_type=std_logic lab=lc0}
C {devices/lab_pin.sym} 180 -510 0 0 {name=l24 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 220 -440 0 1 {name=l25 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 260 -240 0 0 {name=VMC0 value="0" savecurrent=false}
C {devices/lab_pin.sym} 260 -310 0 0 {name=l26 sig_type=std_logic lab=lc0}
C {devices/lab_pin.sym} 260 -170 0 0 {name=l27 sig_type=std_logic lab=icmp0}
C {symbols/pfet_03v3.sym} 420 -440 0 0 {name=XLC1
L=0.28u
W=1u
nf=1
m=1
ad=0.18p
pd=2.36u
as=0.18p
ps=2.36u
nrd=0.18
nrs=0.18
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 440 -370 0 0 {name=l28 sig_type=std_logic lab=lc1}
C {devices/lab_pin.sym} 360 -440 0 0 {name=l29 sig_type=std_logic lab=lc1}
C {devices/lab_pin.sym} 440 -510 0 0 {name=l30 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 480 -440 0 1 {name=l31 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 520 -240 0 0 {name=VMC1 value="0" savecurrent=false}
C {devices/lab_pin.sym} 520 -310 0 0 {name=l32 sig_type=std_logic lab=lc1}
C {devices/lab_pin.sym} 520 -170 0 0 {name=l33 sig_type=std_logic lab=icmp1}
C {symbols/pfet_03v3.sym} 680 -440 0 0 {name=XLC2
L=0.28u
W=1u
nf=1
m=1
ad=0.18p
pd=2.36u
as=0.18p
ps=2.36u
nrd=0.18
nrs=0.18
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 700 -370 0 0 {name=l34 sig_type=std_logic lab=lc2}
C {devices/lab_pin.sym} 620 -440 0 0 {name=l35 sig_type=std_logic lab=lc2}
C {devices/lab_pin.sym} 700 -510 0 0 {name=l36 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 740 -440 0 1 {name=l37 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 780 -240 0 0 {name=VMC2 value="0" savecurrent=false}
C {devices/lab_pin.sym} 780 -310 0 0 {name=l38 sig_type=std_logic lab=lc2}
C {devices/lab_pin.sym} 780 -170 0 0 {name=l39 sig_type=std_logic lab=icmp2}
C {symbols/pfet_03v3.sym} 940 -440 0 0 {name=XLC3
L=0.28u
W=1u
nf=1
m=1
ad=0.18p
pd=2.36u
as=0.18p
ps=2.36u
nrd=0.18
nrs=0.18
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 960 -370 0 0 {name=l40 sig_type=std_logic lab=lc3}
C {devices/lab_pin.sym} 880 -440 0 0 {name=l41 sig_type=std_logic lab=lc3}
C {devices/lab_pin.sym} 960 -510 0 0 {name=l42 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1000 -440 0 1 {name=l43 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 1040 -240 0 0 {name=VMC3 value="0" savecurrent=false}
C {devices/lab_pin.sym} 1040 -310 0 0 {name=l44 sig_type=std_logic lab=lc3}
C {devices/lab_pin.sym} 1040 -170 0 0 {name=l45 sig_type=std_logic lab=icmp3}
C {symbols/pfet_03v3.sym} 1200 -440 0 0 {name=XLR
L=1u
W=20u
nf=10
m=1
ad=1.8p
pd=21.8u
as=2.16p
ps=26.16u
nrd=0.009
nrs=0.009
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 1220 -370 0 0 {name=l46 sig_type=std_logic lab=lr}
C {devices/lab_pin.sym} 1140 -440 0 0 {name=l47 sig_type=std_logic lab=lr}
C {devices/lab_pin.sym} 1220 -510 0 0 {name=l48 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1260 -440 0 1 {name=l49 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 1300 -240 0 0 {name=VMR value="0" savecurrent=false}
C {devices/lab_pin.sym} 1300 -310 0 0 {name=l50 sig_type=std_logic lab=lr}
C {devices/lab_pin.sym} 1300 -170 0 0 {name=l51 sig_type=std_logic lab=iramp}
C {symbols/nfet_03v3.sym} 1460 -440 0 0 {name=XLV
L=0.34u
W=0.5u
nf=1
m=1
ad=0.09p
pd=1.36u
as=0.09p
ps=1.36u
nrd=0.36
nrs=0.36
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 1480 -510 0 0 {name=l52 sig_type=std_logic lab=lv}
C {devices/lab_pin.sym} 1400 -440 0 0 {name=l53 sig_type=std_logic lab=lv}
C {devices/lab_pin.sym} 1480 -370 0 0 {name=l54 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1520 -440 0 1 {name=l55 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1560 -240 0 0 {name=VMV value="0" savecurrent=false}
C {devices/lab_pin.sym} 1560 -310 0 0 {name=l56 sig_type=std_logic lab=ivref}
C {devices/lab_pin.sym} 1560 -170 0 0 {name=l57 sig_type=std_logic lab=lv}
C {symbols/nfet_03v3.sym} 1720 -440 0 0 {name=XLB
L=0.34u
W=0.5u
nf=1
m=1
ad=0.09p
pd=1.36u
as=0.09p
ps=1.36u
nrd=0.36
nrs=0.36
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 1740 -510 0 0 {name=l58 sig_type=std_logic lab=lb}
C {devices/lab_pin.sym} 1660 -440 0 0 {name=l59 sig_type=std_logic lab=lb}
C {devices/lab_pin.sym} 1740 -370 0 0 {name=l60 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1780 -440 0 1 {name=l61 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1820 -240 0 0 {name=VMB value="0" savecurrent=false}
C {devices/lab_pin.sym} 1820 -310 0 0 {name=l62 sig_type=std_logic lab=ivbl}
C {devices/lab_pin.sym} 1820 -170 0 0 {name=l63 sig_type=std_logic lab=lb}
C {devices/code_shown.sym} 60 -80 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27
.param TRAMP=100n
.param TREL=10u
.model swh sw vt=0.5 vh=0.1 ron=10 roff=1e15
.save all @m.xg.xmn1.m0[id]
.control
set num_threads=1
* case ramp100n: the supply ramps in TRAMP, the hold stays off
alter @vhc[pwl] = [ 0 0 1 0 ]
tran 5.025e-09 2.01e-05 0 5.025e-09 uic
meas tran icf find @m.xg.xmn1.m0[id] at=2.01e-05
meas tran icmpf find i(vmc0) at=2.01e-05
meas tran suf find v(xg.su) at=2.01e-05
echo START $&icf $&icmpf $&suf
let i90 = 0.9 * icf
meas tran t90 when @m.xg.xmn1.m0[id]=$&i90 rise=1
let tup = t90 - 1e-07
echo T90 $&tup
* case dead: settled supply, pb held at vdd and nb at 0 until TREL
alter @vdd[pwl] = [ 0 3.3 1 3.3 ]
alter @vhc[pwl] = [ 0 1 1e-05 1 1.001e-05 0 ]
tran 1.5e-08 6e-05 0 1.5e-08 uic
meas tran icf find @m.xg.xmn1.m0[id] at=6e-05
meas tran icmpf find i(vmc0) at=6e-05
meas tran suf find v(xg.su) at=6e-05
echo START $&icf $&icmpf $&suf
let i90 = 0.9 * icf
meas tran t90 when @m.xg.xmn1.m0[id]=$&i90 rise=1
let tup = t90 - 1e-05
echo T90 $&tup
quit
.endc"}
