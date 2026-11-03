v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 160 -880 480 -880 {}
N 160 -360 360 -360 {}
N 240 -800 440 -800 {}
N 240 -680 320 -680 {}
N 300 -740 360 -740 {}
N 300 -560 360 -560 {}
N 320 -480 360 -480 {}
N 360 -740 360 -710 {}
N 360 -740 480 -740 {}
N 360 -680 400 -680 {}
N 360 -650 360 -560 {}
N 360 -560 360 -510 {}
N 360 -560 480 -560 {}
N 360 -450 360 -360 {}
N 360 -360 580 -360 {}
N 400 -480 480 -480 {}
N 480 -880 480 -830 {}
N 480 -880 860 -880 {}
N 480 -800 520 -800 {}
N 480 -770 480 -740 {}
N 480 -740 580 -740 {}
N 480 -560 480 -480 {}
N 480 -480 540 -480 {}
N 540 -680 580 -680 {}
N 580 -740 580 -710 {}
N 580 -650 580 -600 {}
N 580 -600 580 -510 {}
N 580 -600 680 -600 {}
N 580 -480 620 -480 {}
N 580 -450 580 -360 {}
N 580 -360 860 -360 {}
N 620 -680 700 -680 {}
N 680 -640 680 -600 {}
N 680 -600 800 -600 {}
N 780 -800 820 -800 {}
N 800 -680 800 -600 {}
N 800 -680 820 -680 {}
N 800 -600 800 -520 {}
N 800 -520 820 -520 {}
N 860 -880 860 -830 {}
N 860 -880 1080 -880 {}
N 860 -800 900 -800 {}
N 860 -770 860 -740 {}
N 860 -740 860 -710 {}
N 860 -740 920 -740 {}
N 860 -680 900 -680 {}
N 860 -650 860 -600 {}
N 860 -600 860 -550 {}
N 860 -600 960 -600 {}
N 860 -520 900 -520 {}
N 860 -490 860 -360 {}
N 860 -360 1080 -360 {}
N 960 -640 960 -600 {}
N 960 -600 1020 -600 {}
N 1020 -680 1020 -600 {}
N 1020 -680 1040 -680 {}
N 1020 -600 1020 -520 {}
N 1020 -520 1040 -520 {}
N 1080 -880 1080 -710 {}
N 1080 -880 1240 -880 {}
N 1080 -680 1120 -680 {}
N 1080 -650 1080 -600 {}
N 1080 -600 1080 -550 {}
N 1080 -600 1200 -600 {}
N 1080 -520 1120 -520 {}
N 1080 -490 1080 -360 {}
N 1080 -360 1240 -360 {}
T {COMPARATOR  -  continuous-time comparator, currents at I_B = 3.25 uA} 160 -1000 0 0 0.7 0.7 {}
T {33 uA} 235 -850 0 0 0.28 0.28 {layer=4}
T {16 uA*} 615 -850 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 130 -630 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 625 -722 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 150 -452 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 600 -452 0 0 0.28 0.28 {layer=4}
T {37 uA*} 1100 -760 0 0 0.28 0.28 {layer=4}
T {(VBL, VDD/2)} 150 -660 0 0 0.3 0.3 {}
T {(MIM top plate)} 705 -662 0 0 0.3 0.3 {}
T {PMOS 5T OTA} 320 -412 0 0 0.4 0.4 {}
T {starved inverter} 760 -412 0 0 0.4 0.4 {}
T {output inverter} 1000 -412 0 0 0.4 0.4 {}
T {clk, nbias: not connected} 290 -296 0 0 0.35 0.35 {}
C {devices/iopin.sym} 160 -880 0 0 {name=pvdd lab=vdd}
C {devices/iopin.sym} 160 -360 0 0 {name=pvss lab=vss}
C {symbols/pfet_03v3.sym} 460 -800 0 0 {name=TAIL
L=0.28u W=11u nf=11 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 520 -800 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/ipin.sym} 240 -800 0 0 {name=ppbias lab=pbias}
C {devices/lab_pin.sym} 300 -740 0 0 {name=l2 sig_type=std_logic lab=tail}
C {symbols/pfet_03v3.sym} 340 -680 0 0 {name=INP
L=0.32u W=12u nf=12 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/pfet_03v3.sym} 600 -680 0 1 {name=INN
L=0.32u W=12u nf=12 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/ipin.sym} 240 -680 0 0 {name=pinp lab=inp}
C {devices/ipin.sym} 700 -680 0 1 {name=pinn lab=inn}
C {devices/lab_pin.sym} 400 -680 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 540 -680 0 0 {name=l4 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 380 -480 0 1 {name=LOADD
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {symbols/nfet_03v3.sym} 560 -480 0 0 {name=LOADM
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 300 -560 0 0 {name=l5 sig_type=std_logic lab=left}
C {devices/lab_pin.sym} 320 -480 0 0 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 620 -480 0 1 {name=l7 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 680 -640 0 0 {name=l8 sig_type=std_logic lab=outa}
C {symbols/pfet_03v3.sym} 840 -800 0 0 {name=BST
L=0.28u W=5u nf=5 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/pfet_03v3.sym} 840 -680 0 0 {name=BUF2
L=0.36u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/nfet_03v3.sym} 840 -520 0 0 {name=BUF1
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 920 -740 0 1 {name=l9 sig_type=std_logic lab=bst}
C {devices/lab_pin.sym} 780 -800 0 0 {name=l10 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 900 -800 0 1 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -680 0 1 {name=l12 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -520 0 1 {name=l13 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 1060 -680 0 0 {name=BUF4
L=0.36u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/nfet_03v3.sym} 1060 -520 0 0 {name=BUF3
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 960 -640 0 0 {name=l14 sig_type=std_logic lab=outb}
C {devices/lab_pin.sym} 1120 -680 0 1 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1120 -520 0 1 {name=l16 sig_type=std_logic lab=vss}
C {devices/opin.sym} 1200 -600 0 0 {name=pdout lab=dout}
C {devices/ipin.sym} 240 -280 0 0 {name=pclk lab=clk}
C {devices/ipin.sym} 240 -240 0 0 {name=pnbias lab=nbias}
