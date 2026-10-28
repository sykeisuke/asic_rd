v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {MIDREF_B  -  VDD/2 BUFFER (VREF / VBL OF THE UNIT CELL)} 40 -1130 0 0 0.6 0.6 {}
T {Two flipped voltage followers set p = vin + VSG(M1) and n = vin - VGS(M4); the 4x diodes M2 / M5 between p and n
make out = vin, class AB. The two crossings are the FVF shunt loops (b -> M3 gate, a -> M6 gate); they do not connect.
Netlist: ref_fvf_biased.spice (run-biased.sh compares this drawing to it instance by instance).} 40 -1070 0 0 0.3 0.3 {}
T {BIAS  (1 uA)} 60 -980 0 0 0.4 0.4 {}
T {pbias slave XSLF -> diode XMBN
-> mirror XMBN2 -> diode XMBP} 60 -950 0 0 0.25 0.25 {}
T {DIVIDER} 500 -980 0 0 0.4 0.4 {}
T {vin = VDD/2, 2 x 1.65 Mohm} 500 -950 0 0 0.25 0.25 {}
T {INPUT FOLLOWERS + IB} 760 -980 0 0 0.4 0.4 {}
T {M1 / M4 follow vin; XMIB / XMIT = IB} 760 -950 0 0 0.25 0.25 {}
T {SHUNTS + OUTPUT} 1080 -980 0 0 0.4 0.4 {}
T {M3 / M6 shunt; M2 / M5 = 4 x M1 / M4} 1080 -950 0 0 0.25 0.25 {}
T {IB} 790 -605 0 0 0.35 0.35 {layer=8}
T {IB} 790 -365 0 0 0.35 0.35 {layer=8}
T {p = vin + VSG1} 1190 -735 0 0 0.25 0.25 {layer=8}
T {n = vin - VGS4} 1190 -195 0 0 0.25 0.25 {layer=8}
T {out = vin} 1200 -480 0 0 0.25 0.25 {layer=8}
L 4 475 -1000 475 20 {dash=6}
L 4 715 -1000 715 20 {dash=6}
N 40 -760 120 -760 {lab=pbias}
N 160 -860 160 -790 {lab=vdd}
N 380 -860 380 -790 {lab=vdd}
N 160 -110 160 -40 {lab=vss}
N 380 -110 380 -40 {lab=vss}
N 160 -730 160 -450 {lab=nb}
N 160 -450 160 -220 {lab=nb}
N 160 -220 160 -170 {lab=nb}
N 160 -220 240 -220 {lab=nb}
N 240 -220 240 -140 {lab=nb}
N 200 -140 240 -140 {lab=nb}
N 240 -140 340 -140 {lab=nb}
N 380 -730 380 -700 {lab=pb}
N 380 -700 380 -450 {lab=pb}
N 380 -450 380 -170 {lab=pb}
N 300 -760 340 -760 {lab=pb}
N 300 -760 300 -700 {lab=pb}
N 300 -700 380 -700 {lab=pb}
N 160 -760 200 -760 {lab=vdd}
N 380 -760 420 -760 {lab=vdd}
N 120 -140 160 -140 {lab=vss}
N 380 -140 420 -140 {lab=vss}
N 560 -860 560 -630 {lab=vdd}
N 560 -570 560 -450 {lab=vin}
N 560 -450 560 -330 {lab=vin}
N 560 -270 560 -40 {lab=vss}
N 660 -350 660 -40 {lab=vss}
N 560 -450 660 -450 {lab=vin}
N 660 -450 740 -450 {lab=vin}
N 660 -450 660 -410 {lab=vin}
N 580 -600 620 -600 {lab=vss}
N 580 -300 620 -300 {lab=vss}
N 740 -670 740 -450 {lab=vin}
N 740 -450 740 -230 {lab=vin}
N 740 -670 860 -670 {lab=vin}
N 740 -230 860 -230 {lab=vin}
N 900 -640 900 -620 {lab=b}
N 900 -620 900 -600 {lab=b}
N 900 -540 900 -520 {lab=vss}
N 900 -300 900 -280 {lab=a}
N 900 -280 900 -260 {lab=a}
N 900 -380 900 -360 {lab=vdd}
N 820 -570 860 -570 {lab=nb}
N 820 -330 860 -330 {lab=pb}
N 900 -620 1040 -620 {lab=b}
N 1040 -760 1040 -620 {lab=b}
N 1040 -760 1120 -760 {lab=b}
N 900 -280 1040 -280 {lab=a}
N 1040 -280 1040 -140 {lab=a}
N 1040 -140 1120 -140 {lab=a}
N 900 -700 1160 -700 {lab=p}
N 1160 -730 1160 -700 {lab=p}
N 900 -200 1160 -200 {lab=n}
N 1160 -200 1160 -170 {lab=n}
N 1160 -860 1160 -790 {lab=vdd}
N 1160 -110 1160 -40 {lab=vss}
N 1160 -640 1160 -610 {lab=out}
N 1160 -610 1160 -450 {lab=out}
N 1160 -450 1160 -290 {lab=out}
N 1160 -290 1160 -260 {lab=out}
N 1090 -610 1160 -610 {lab=out}
N 1090 -670 1090 -610 {lab=out}
N 1090 -670 1120 -670 {lab=out}
N 1090 -290 1160 -290 {lab=out}
N 1090 -290 1090 -230 {lab=out}
N 1090 -230 1120 -230 {lab=out}
N 1160 -450 1320 -450 {lab=out}
N 900 -670 940 -670 {lab=vdd}
N 900 -570 940 -570 {lab=vss}
N 900 -330 940 -330 {lab=vdd}
N 900 -230 940 -230 {lab=vss}
N 1160 -760 1200 -760 {lab=vdd}
N 1160 -670 1200 -670 {lab=vdd}
N 1160 -230 1200 -230 {lab=vss}
N 1160 -140 1200 -140 {lab=vss}
N 60 -860 160 -860 {lab=vdd}
N 160 -860 380 -860 {lab=vdd}
N 380 -860 560 -860 {lab=vdd}
N 560 -860 1160 -860 {lab=vdd}
N 60 -40 160 -40 {lab=vss}
N 160 -40 380 -40 {lab=vss}
N 380 -40 560 -40 {lab=vss}
N 560 -40 660 -40 {lab=vss}
N 660 -40 1160 -40 {lab=vss}
C {devices/iopin.sym} 60 -860 0 1 {name=pvdd lab=vdd sim_pinnumber=3}
C {devices/iopin.sym} 60 -40 0 1 {name=pvss lab=vss sim_pinnumber=4}
C {devices/ipin.sym} 40 -760 0 0 {name=ppbias lab=pbias sim_pinnumber=2}
C {devices/opin.sym} 1320 -450 0 0 {name=pout lab=out sim_pinnumber=1}
C {symbols/pfet_03v3.sym} 140 -760 0 0 {name=XSLF
L=1.0u
W=6.07u
nf=3
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 360 -760 0 0 {name=XMBP
L=4u
W=16u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 180 -140 0 1 {name=XMBN
L=4u
W=2u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 360 -140 0 0 {name=XMBN2
L=4u
W=2u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 200 -760 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 420 -760 0 1 {name=l2 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -140 0 0 {name=l3 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 420 -140 0 1 {name=l4 sig_type=std_logic lab=vss}
C {devices/lab_wire.sym} 160 -450 0 0 {name=l5 sig_type=std_logic lab=nb}
C {devices/lab_wire.sym} 380 -450 0 0 {name=l6 sig_type=std_logic lab=pb}
C {symbols/ppolyf_u_3k.sym} 560 -600 2 0 {name=XRT
W=1u
L=550u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 560 -300 2 0 {name=XRB
W=1u
L=550u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {devices/capa.sym} 660 -380 0 0 {name=CFLT m=1 value=1p footprint=1206 device="ideal capacitor"}
C {devices/lab_pin.sym} 620 -600 0 1 {name=l7 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 620 -300 0 1 {name=l8 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 880 -670 0 0 {name=XM1
L=2u
W=8u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 880 -570 0 0 {name=XMIB
L=4u
W=2u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 880 -330 0 0 {name=XMIT
L=4u
W=16u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 880 -230 0 0 {name=XM4
L=2u
W=8u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1140 -760 0 0 {name=XM3
L=2u
W=2u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1140 -670 0 0 {name=XM2
L=2u
W=32u
nf=4
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1140 -230 0 0 {name=XM5
L=2u
W=32u
nf=4
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1140 -140 0 0 {name=XM6
L=8u
W=1u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 900 -520 0 0 {name=l9 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 900 -380 0 1 {name=l10 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 820 -570 0 0 {name=l11 sig_type=std_logic lab=nb}
C {devices/lab_pin.sym} 820 -330 0 0 {name=l12 sig_type=std_logic lab=pb}
C {devices/lab_pin.sym} 940 -670 0 1 {name=l13 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 940 -570 0 1 {name=l14 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 940 -330 0 1 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 940 -230 0 1 {name=l16 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 -760 0 1 {name=l17 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 -670 0 1 {name=l18 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 -230 0 1 {name=l19 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 -140 0 1 {name=l20 sig_type=std_logic lab=vss}
C {devices/lab_wire.sym} 900 -620 0 0 {name=l21 sig_type=std_logic lab=b}
C {devices/lab_wire.sym} 900 -280 0 0 {name=l22 sig_type=std_logic lab=a}
C {devices/lab_wire.sym} 1160 -700 0 0 {name=l23 sig_type=std_logic lab=p}
C {devices/lab_wire.sym} 1160 -200 0 0 {name=l24 sig_type=std_logic lab=n}
C {devices/lab_wire.sym} 740 -450 0 0 {name=l25 sig_type=std_logic lab=vin}
C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/midrail_ref_bkp/midrail_ref - midref_b"}
