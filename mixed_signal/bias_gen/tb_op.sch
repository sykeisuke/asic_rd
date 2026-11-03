v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1210 120 -1250 {}
N 120 -1150 120 -1110 {}
N 600 -1220 600 -1260 {}
N 600 -980 600 -940 {}
N 700 -1180 820 -1180 {}
N 700 -1155 760 -1155 {}
N 700 -1130 820 -1130 {}
N 700 -1105 760 -1105 {}
N 700 -1080 820 -1080 {}
N 700 -1055 760 -1055 {}
N 700 -1030 820 -1030 {}
N 180 -650 180 -610 {}
N 140 -680 100 -680 {}
N 180 -710 180 -750 {}
N 180 -680 220 -680 {}
N 260 -510 260 -550 {}
N 260 -450 260 -410 {}
N 440 -650 440 -610 {}
N 400 -680 360 -680 {}
N 440 -710 440 -750 {}
N 440 -680 480 -680 {}
N 520 -510 520 -550 {}
N 520 -450 520 -410 {}
N 700 -650 700 -610 {}
N 660 -680 620 -680 {}
N 700 -710 700 -750 {}
N 700 -680 740 -680 {}
N 780 -510 780 -550 {}
N 780 -450 780 -410 {}
N 960 -650 960 -610 {}
N 920 -680 880 -680 {}
N 960 -710 960 -750 {}
N 960 -680 1000 -680 {}
N 1040 -510 1040 -550 {}
N 1040 -450 1040 -410 {}
N 1220 -650 1220 -610 {}
N 1180 -680 1140 -680 {}
N 1220 -710 1220 -750 {}
N 1220 -680 1260 -680 {}
N 1300 -510 1300 -550 {}
N 1300 -450 1300 -410 {}
N 1480 -710 1480 -750 {}
N 1440 -680 1400 -680 {}
N 1480 -650 1480 -610 {}
N 1480 -680 1520 -680 {}
N 1560 -510 1560 -550 {}
N 1560 -450 1560 -410 {}
N 1740 -710 1740 -750 {}
N 1700 -680 1660 -680 {}
N 1740 -650 1740 -610 {}
N 1740 -680 1780 -680 {}
N 1820 -510 1820 -550 {}
N 1820 -450 1820 -410 {}
T {TB_OP  -  operating point of bias_gen, every output into its consumer diode} 40 -1340 0 0 0.7 0.7 {}
T {VDD 3.0 / 3.3 / 3.6 V} 60 -1040 0 0 0.3 0.3 {layer=4}
T {CONSUMER DIODES, 0 V AMMETERS} 60 -800 0 0 0.4 0.4 {}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD value="3.3" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {bias_gen.sym} 600 -1100 0 0 {name=XG}
C {devices/lab_pin.sym} 600 -1260 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 600 -940 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 820 -1180 0 1 {name=l5 sig_type=std_logic lab=icmp0}
C {devices/lab_pin.sym} 760 -1155 0 1 {name=l6 sig_type=std_logic lab=icmp1}
C {devices/lab_pin.sym} 820 -1130 0 1 {name=l7 sig_type=std_logic lab=icmp2}
C {devices/lab_pin.sym} 760 -1105 0 1 {name=l8 sig_type=std_logic lab=icmp3}
C {devices/lab_pin.sym} 820 -1080 0 1 {name=l9 sig_type=std_logic lab=iramp}
C {devices/lab_pin.sym} 760 -1055 0 1 {name=l10 sig_type=std_logic lab=ivref}
C {devices/lab_pin.sym} 820 -1030 0 1 {name=l11 sig_type=std_logic lab=ivbl}
C {symbols/pfet_03v3.sym} 160 -680 0 0 {name=XLC0
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
C {devices/lab_pin.sym} 180 -610 0 0 {name=l12 sig_type=std_logic lab=lc0}
C {devices/lab_pin.sym} 100 -680 0 0 {name=l13 sig_type=std_logic lab=lc0}
C {devices/lab_pin.sym} 180 -750 0 0 {name=l14 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 220 -680 0 1 {name=l15 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 260 -480 0 0 {name=VMC0 value="0" savecurrent=false}
C {devices/lab_pin.sym} 260 -550 0 0 {name=l16 sig_type=std_logic lab=lc0}
C {devices/lab_pin.sym} 260 -410 0 0 {name=l17 sig_type=std_logic lab=icmp0}
C {symbols/pfet_03v3.sym} 420 -680 0 0 {name=XLC1
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
C {devices/lab_pin.sym} 440 -610 0 0 {name=l18 sig_type=std_logic lab=lc1}
C {devices/lab_pin.sym} 360 -680 0 0 {name=l19 sig_type=std_logic lab=lc1}
C {devices/lab_pin.sym} 440 -750 0 0 {name=l20 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 480 -680 0 1 {name=l21 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 520 -480 0 0 {name=VMC1 value="0" savecurrent=false}
C {devices/lab_pin.sym} 520 -550 0 0 {name=l22 sig_type=std_logic lab=lc1}
C {devices/lab_pin.sym} 520 -410 0 0 {name=l23 sig_type=std_logic lab=icmp1}
C {symbols/pfet_03v3.sym} 680 -680 0 0 {name=XLC2
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
C {devices/lab_pin.sym} 700 -610 0 0 {name=l24 sig_type=std_logic lab=lc2}
C {devices/lab_pin.sym} 620 -680 0 0 {name=l25 sig_type=std_logic lab=lc2}
C {devices/lab_pin.sym} 700 -750 0 0 {name=l26 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 740 -680 0 1 {name=l27 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 780 -480 0 0 {name=VMC2 value="0" savecurrent=false}
C {devices/lab_pin.sym} 780 -550 0 0 {name=l28 sig_type=std_logic lab=lc2}
C {devices/lab_pin.sym} 780 -410 0 0 {name=l29 sig_type=std_logic lab=icmp2}
C {symbols/pfet_03v3.sym} 940 -680 0 0 {name=XLC3
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
C {devices/lab_pin.sym} 960 -610 0 0 {name=l30 sig_type=std_logic lab=lc3}
C {devices/lab_pin.sym} 880 -680 0 0 {name=l31 sig_type=std_logic lab=lc3}
C {devices/lab_pin.sym} 960 -750 0 0 {name=l32 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1000 -680 0 1 {name=l33 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 1040 -480 0 0 {name=VMC3 value="0" savecurrent=false}
C {devices/lab_pin.sym} 1040 -550 0 0 {name=l34 sig_type=std_logic lab=lc3}
C {devices/lab_pin.sym} 1040 -410 0 0 {name=l35 sig_type=std_logic lab=icmp3}
C {symbols/pfet_03v3.sym} 1200 -680 0 0 {name=XLR
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
C {devices/lab_pin.sym} 1220 -610 0 0 {name=l36 sig_type=std_logic lab=lr}
C {devices/lab_pin.sym} 1140 -680 0 0 {name=l37 sig_type=std_logic lab=lr}
C {devices/lab_pin.sym} 1220 -750 0 0 {name=l38 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1260 -680 0 1 {name=l39 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 1300 -480 0 0 {name=VMR value="0" savecurrent=false}
C {devices/lab_pin.sym} 1300 -550 0 0 {name=l40 sig_type=std_logic lab=lr}
C {devices/lab_pin.sym} 1300 -410 0 0 {name=l41 sig_type=std_logic lab=iramp}
C {symbols/nfet_03v3.sym} 1460 -680 0 0 {name=XLV
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
C {devices/lab_pin.sym} 1480 -750 0 0 {name=l42 sig_type=std_logic lab=lv}
C {devices/lab_pin.sym} 1400 -680 0 0 {name=l43 sig_type=std_logic lab=lv}
C {devices/lab_pin.sym} 1480 -610 0 0 {name=l44 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1520 -680 0 1 {name=l45 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1560 -480 0 0 {name=VMV value="0" savecurrent=false}
C {devices/lab_pin.sym} 1560 -550 0 0 {name=l46 sig_type=std_logic lab=ivref}
C {devices/lab_pin.sym} 1560 -410 0 0 {name=l47 sig_type=std_logic lab=lv}
C {symbols/nfet_03v3.sym} 1720 -680 0 0 {name=XLB
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
C {devices/lab_pin.sym} 1740 -750 0 0 {name=l48 sig_type=std_logic lab=lb}
C {devices/lab_pin.sym} 1660 -680 0 0 {name=l49 sig_type=std_logic lab=lb}
C {devices/lab_pin.sym} 1740 -610 0 0 {name=l50 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1780 -680 0 1 {name=l51 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1820 -480 0 0 {name=VMB value="0" savecurrent=false}
C {devices/lab_pin.sym} 1820 -550 0 0 {name=l52 sig_type=std_logic lab=ivbl}
C {devices/lab_pin.sym} 1820 -410 0 0 {name=l53 sig_type=std_logic lab=lb}
C {devices/code_shown.sym} 60 -300 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27
.control
set num_threads=1
foreach v 3 3.3 3.6
alter VDD dc = $v
op
let ic = abs(i(vmc0))
let ic1 = abs(i(vmc1))
let ir = abs(i(vmr))
let iv = abs(i(vmv))
let icore = abs(@m.xg.xmn1.m0[id])
let ibl = abs(@m.xg.xsu4.m0[id])
let isup = -i(vdd)
let vsu = v(xg.su)
let vnb = v(xg.nb)
let vpb = v(xg.pb)
let vlc = v(lc0)
let vlr = v(lr)
let vlv = v(lv)
let hr_xmn1 = abs(@m.xg.xmn1.m0[vds]) - abs(@m.xg.xmn1.m0[vdsat])
let hr_xmn2 = abs(@m.xg.xmn2.m0[vds]) - abs(@m.xg.xmn2.m0[vdsat])
let hr_xmp1 = abs(@m.xg.xmp1.m0[vds]) - abs(@m.xg.xmp1.m0[vdsat])
let hr_xmp2 = abs(@m.xg.xmp2.m0[vds]) - abs(@m.xg.xmp2.m0[vdsat])
let hr_xoc0 = abs(@m.xg.xoc0.m0[vds]) - abs(@m.xg.xoc0.m0[vdsat])
let hr_xoc1 = abs(@m.xg.xoc1.m0[vds]) - abs(@m.xg.xoc1.m0[vdsat])
let hr_xoc2 = abs(@m.xg.xoc2.m0[vds]) - abs(@m.xg.xoc2.m0[vdsat])
let hr_xoc3 = abs(@m.xg.xoc3.m0[vds]) - abs(@m.xg.xoc3.m0[vdsat])
let hr_xor = abs(@m.xg.xor.m0[vds]) - abs(@m.xg.xor.m0[vdsat])
let hr_xov = abs(@m.xg.xov.m0[vds]) - abs(@m.xg.xov.m0[vdsat])
let hr_xob = abs(@m.xg.xob.m0[vds]) - abs(@m.xg.xob.m0[vdsat])
echo OP typical 27 res_typical $v $&ic $&ic1 $&ir $&iv $&icore $&ibl $&isup $&vsu $&vnb $&vpb $&vlc $&vlr $&vlv $&hr_xmn1 $&hr_xmn2 $&hr_xmp1 $&hr_xmp2 $&hr_xoc0 $&hr_xoc1 $&hr_xoc2 $&hr_xoc3 $&hr_xor $&hr_xov $&hr_xob
end
quit
.endc"}
