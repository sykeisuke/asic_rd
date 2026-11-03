v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 320 -560 320 -470 {}
N 320 -560 480 -560 {}
N 320 -410 320 -300 {}
N 320 -300 460 -300 {}
N 460 -300 460 -210 {}
N 460 -300 720 -300 {}
N 460 -150 460 0 {}
N 640 -180 680 -180 {}
N 720 -300 720 -210 {}
N 720 -300 900 -300 {}
N 720 -150 720 -60 {}
T {RAMP_SIMPLE  -  PMOS current source + 4.00 pF MIM + reset switch} 20 -760 0 0 0.70 0.70 {}
T {current source} 220 -640 0 0 0.45 0.45 {layer=13}
T {integrating capacitor} 380 -380 0 0 0.35 0.35 {layer=13}
T {reset to vrlo} 680 -380 0 0 0.35 0.35 {layer=13}
T {0.475 uA} 340 -545 0 0 0.35 0.35 {layer=4}
T {C = 4.00 pF} 480 -140 0 0 0.45 0.45 {layer=4}
C {devices/opin.sym} 20 -480 0 0 {name=p_vramp lab=vramp}
C {devices/ipin.sym} 20 -440 0 0 {name=p_rst lab=rst}
C {devices/ipin.sym} 20 -400 0 0 {name=p_vrlo lab=vrlo}
C {devices/ipin.sym} 20 -360 0 0 {name=p_pbias lab=pbias}
C {devices/iopin.sym} 20 -320 0 0 {name=p_vdd lab=vdd}
C {devices/iopin.sym} 20 -280 0 0 {name=p_vss lab=vss}
C {devices/lab_pin.sym} 480 -560 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 300 -440 0 0 {name=XPS
L="\{RS_LPS\}"
W="\{RS_WPS\}"
nf="\{RS_NFPS\}"
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 280 -440 0 0 {name=l2 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 320 -440 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -300 0 1 {name=l4 sig_type=std_logic lab=vramp}
C {symbols/cap_mim_2f0fF.sym} 460 -180 0 0 {name=XCR W="\{RS_CW\}" L="\{RS_CW\}" model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 460 0 0 1 {name=l5 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} 700 -180 0 0 {name=XRST
L=0.28u
W="\{RS_WRST\}"
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 720 -180 0 1 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 -60 0 1 {name=l7 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 640 -180 0 0 {name=l8 sig_type=std_logic lab=rst}
