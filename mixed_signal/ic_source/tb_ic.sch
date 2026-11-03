v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 200 -580 200 -530 {}
N 200 -470 200 -420 {}
N 360 -580 360 -530 {}
N 360 -470 360 -420 {}
N 560 -580 560 -530 {}
N 560 -470 560 -420 {}
N 760 -580 760 -530 {}
N 760 -470 760 -420 {}
N 980 -340 1040 -340 {}
N 980 -260 1040 -260 {}
N 1160 -460 1160 -420 {}
N 1160 -180 1160 -140 {}
N 1240 -460 1240 -420 {}
N 1240 -180 1240 -140 {}
N 1360 -300 1460 -300 {}
N 1460 -300 1600 -300 {}
N 1600 -300 1600 -250 {}
N 1600 -190 1600 -140 {}
T {TB_IC  -  the I/C source alone: cold AVDD / DVDD, 20 MHz clock, the bias sink, the ramp node as a level} 60 -700 0 0 0.70 0.70 {}
T {supplies} 200 -620 0 0 0.45 0.45 {layer=13}
T {20 MHz clock} 520 -620 0 0 0.45 0.45 {layer=13}
T {bias sink 3.25 uA} 700 -620 0 0 0.45 0.45 {layer=13}
T {the ramp node: 0.4355 / 1.2 / 2.053 V} 1500 -360 0 0 0.45 0.45 {layer=13}
C {devices/vsource.sym} 200 -500 0 0 {name=VDD_SOURCE value="PWL(0 0 100n 3.3)" savecurrent=false}
C {devices/lab_pin.sym} 200 -580 0 1 {name=l1 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 200 -420 0 1 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 360 -500 0 0 {name=VDVDD value="PWL(0 0 100n 3.3)" savecurrent=false}
C {devices/lab_pin.sym} 360 -580 0 1 {name=l3 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 360 -420 0 1 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 560 -500 0 0 {name=VCLK value="PULSE(0 3.3 150n 0.5n 0.5n 24.5n 50n)" savecurrent=false}
C {devices/lab_pin.sym} 560 -580 0 1 {name=l5 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 560 -420 0 1 {name=l6 sig_type=std_logic lab=0}
C {devices/isource.sym} 760 -500 0 0 {name=IB value="3.25u" savecurrent=false}
C {devices/lab_pin.sym} 760 -580 0 1 {name=l7 sig_type=std_logic lab=ibias}
C {devices/lab_pin.sym} 760 -420 0 1 {name=l8 sig_type=std_logic lab=0}
C {ic_source.sym} 1200 -300 0 0 {name=XIC}
C {devices/lab_pin.sym} 980 -340 0 0 {name=l9 sig_type=std_logic lab=ibias}
C {devices/lab_pin.sym} 980 -260 0 0 {name=l10 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1160 -460 0 1 {name=l11 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1240 -460 0 1 {name=l12 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 1160 -140 0 1 {name=l13 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1240 -140 0 1 {name=l14 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1460 -300 0 1 {name=l15 sig_type=std_logic lab=iout}
C {devices/vsource.sym} 1600 -220 0 0 {name=VLD value="1.2" savecurrent=false}
C {devices/lab_pin.sym} 1600 -140 0 1 {name=l16 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1000 60 0 0 {name=MODELS only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27
.include /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice"}
