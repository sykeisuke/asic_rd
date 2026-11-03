v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 200 -600 200 -550 {}
N 200 -490 200 -440 {}
N 400 -380 400 -330 {}
N 400 -270 400 -220 {}
N 400 -140 400 -90 {}
N 400 -30 400 20 {}
N 760 -600 760 -550 {}
N 760 -490 760 -400 {}
N 860 -340 920 -340 {}
N 860 -260 920 -260 {}
N 1060 -180 1060 -120 {}
N 1200 -340 1260 -340 {}
N 1260 -340 1480 -340 {}
N 1480 -340 1480 -250 {}
N 1480 -340 1900 -340 {}
N 1480 -190 1480 -120 {}
N 1900 -340 1900 -250 {}
N 1900 -250 1900 -190 {}
N 1900 -190 1900 -120 {}
T {TB_RAMP  -  the ramp alone: ideal 0.545 uA into the cell, 4 cells of load, S1 charge at TCONN, VR_LO 0.4200 V} 60 -760 0 0 0.70 0.70 {}
T {supply} 140 -640 0 0 0.45 0.45 {layer=13}
T {ramp current (the I/C source's place)} 640 -640 0 0 0.45 0.45 {layer=13}
T {0.545 uA} 800 -470 0 0 0.35 0.35 {layer=4}
T {reset} 360 -420 0 0 0.45 0.45 {layer=13}
T {VR_LO (pre-roll level)} 320 -180 0 0 0.45 0.45 {layer=13}
T {C_L = 4 x 19 fF} 1320 -200 0 0 0.35 0.35 {layer=4}
T {S1 charge} 1860 -100 0 0 0.35 0.35 {layer=4}
T {cells: load and S1 charge} 1460 -420 0 0 0.45 0.45 {layer=13}
C {devices/vsource.sym} 200 -520 0 0 {name=VDD_SOURCE value="PWL(0 0 1e-07 3.3 1.81e-05 3.3)" savecurrent=false}
C {devices/lab_pin.sym} 200 -600 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 200 -440 0 1 {name=l2 sig_type=std_logic lab=0}
C {devices/isource.sym} 760 -520 0 0 {name=IRAMP value="PWL(0 0 1e-07 5.45176e-07)" savecurrent=false}
C {devices/lab_pin.sym} 760 -600 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 760 -400 0 1 {name=l4 sig_type=std_logic lab=vramp}
C {devices/vsource.sym} 400 -300 0 0 {name=VRST value="PWL(0 0 1e-07 3.3 3.6e-06 3.3 3.6001e-06 0 1.66e-05 0 1.66001e-05 3.3)" savecurrent=false}
C {devices/lab_pin.sym} 400 -380 0 1 {name=l5 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 400 -220 0 1 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 400 -60 0 0 {name=VRLO value="0.420000" savecurrent=false}
C {devices/lab_pin.sym} 400 -140 0 1 {name=l7 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 400 20 0 1 {name=l8 sig_type=std_logic lab=0}
C {ramp_simple.sym} 1060 -300 0 0 {name=XRG}
C {devices/lab_pin.sym} 860 -340 0 0 {name=l9 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 860 -260 0 0 {name=l10 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 1060 -120 0 1 {name=l11 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1260 -340 0 1 {name=l12 sig_type=std_logic lab=vramp}
C {devices/capa.sym} 1480 -220 0 0 {name=CL value="7.7e-14" savecurrent=false}
C {devices/lab_pin.sym} 1480 -120 0 1 {name=l13 sig_type=std_logic lab=0}
C {devices/isource.sym} 1900 -220 2 0 {name=IKICK value="PULSE(0 0.0001264 3.3e-06 100p 100p 0.9n 1)" savecurrent=false}
C {devices/lab_pin.sym} 1900 -120 0 1 {name=l14 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1000 60 0 0 {name=MODELS only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27"}
