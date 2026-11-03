v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1210 120 -1250 {}
N 120 -1150 120 -1110 {}
N 290 -1210 290 -1250 {}
N 290 -1150 290 -1110 {}
N 460 -1210 460 -1250 {}
N 460 -1150 460 -1110 {}
N 630 -1210 630 -1250 {}
N 630 -1150 630 -1110 {}
N 800 -1210 800 -1250 {}
N 800 -1150 800 -1110 {}
N 120 -930 120 -970 {}
N 120 -870 120 -830 {}
N 300 -900 260 -900 {}
N 340 -930 340 -970 {}
N 340 -870 340 -830 {}
N 340 -900 380 -900 {}
N 480 -930 480 -970 {}
N 480 -870 480 -830 {}
N 660 -900 620 -900 {}
N 700 -870 700 -830 {}
N 700 -930 700 -970 {}
N 700 -900 740 -900 {}
N 1200 -1060 1160 -1060 {}
N 1200 -1030 1160 -1030 {}
N 1200 -1000 1160 -1000 {}
N 1200 -970 1160 -970 {}
N 1200 -940 1160 -940 {}
N 1400 -1045 1440 -1045 {}
N 1300 -1120 1300 -1160 {}
N 1300 -880 1300 -840 {}
N 1540 -1030 1540 -1070 {}
N 1540 -970 1540 -930 {}
T {TB_TRIP  -  static trip of comparator, inp = VBL = VDD/2, I_B = 1.93 uA} 60 -1330 0 0 0.7 0.7 {}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -1180 0 0 {name=VDD_BIAS value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -1250 0 0 {name=l3 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 290 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 460 -1180 0 0 {name=VVBL value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -1250 0 0 {name=l5 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 460 -1110 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1180 0 0 {name=VDC value="1.65" savecurrent=false}
C {devices/lab_pin.sym} 630 -1250 0 0 {name=l7 sig_type=std_logic lab=vdc}
C {devices/lab_pin.sym} 630 -1110 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 800 -1180 0 0 {name=VCLK value="0" savecurrent=false}
C {devices/lab_pin.sym} 800 -1250 0 0 {name=l9 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 800 -1110 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/isource.sym} 120 -900 0 0 {name=IREFN value="\{IREF\}"}
C {devices/lab_pin.sym} 120 -970 0 0 {name=l11 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 120 -830 0 0 {name=l12 sig_type=std_logic lab=nbias}
C {symbols/nfet_03v3.sym} 320 -900 0 0 {name=REFN
L=1u W=20u nf=10 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 260 -900 0 0 {name=l13 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -970 0 0 {name=l14 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -830 0 0 {name=l15 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 380 -900 0 1 {name=l16 sig_type=std_logic lab=0}
C {devices/isource.sym} 480 -900 0 0 {name=IREFP value="\{IREF\}"}
C {devices/lab_pin.sym} 480 -970 0 0 {name=l17 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 480 -830 0 0 {name=l18 sig_type=std_logic lab=0}
C {symbols/pfet_03v3.sym} 680 -900 0 0 {name=REFP
L=0.28u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 620 -900 0 0 {name=l19 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -830 0 0 {name=l20 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -970 0 0 {name=l21 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 740 -900 0 1 {name=l22 sig_type=std_logic lab=vddb}
C {comparator.sym} 1300 -1000 0 0 {name=XDC}
C {devices/lab_pin.sym} 1160 -1060 0 0 {name=l23 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1160 -1030 0 0 {name=l24 sig_type=std_logic lab=vdc}
C {devices/lab_pin.sym} 1160 -1000 0 0 {name=l25 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1160 -970 0 0 {name=l26 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1160 -940 0 0 {name=l27 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1440 -1045 0 1 {name=l28 sig_type=std_logic lab=doutdc}
C {devices/lab_pin.sym} 1300 -1160 0 0 {name=l29 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1300 -840 0 0 {name=l30 sig_type=std_logic lab=0}
C {devices/capa.sym} 1540 -1000 0 0 {name=CLDC value=10f m=1}
C {devices/lab_pin.sym} 1540 -1070 0 0 {name=l31 sig_type=std_logic lab=doutdc}
C {devices/lab_pin.sym} 1540 -930 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1000 -560 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.param VDD=3.3
.param IREF=1.93077e-06   $ data/sizing.json iref: ideal current into one tail finger
.temp 27
.control
dc VDC 1.60 1.70 25u
meas dc vtrip when v(doutdc)=1.65 fall=1
echo \"RESULT_BEGIN\"
print vtrip
echo \"RESULT_END\"
quit
.endc"}
