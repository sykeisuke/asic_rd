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
N 460 -1210 460 -1250 {}
N 460 -1150 460 -1110 {}
N 630 -1210 630 -1250 {}
N 630 -1150 630 -1110 {}
N 120 -650 120 -690 {}
N 120 -590 120 -550 {}
N 120 -480 120 -520 {}
N 120 -420 120 -380 {}
N 1400 -1170 1400 -1210 {}
N 1400 -1110 1400 -1070 {}
N 1360 -1140 1320 -1140 {}
N 1360 -1120 1320 -1120 {}
N 1400 -930 1400 -970 {}
N 1400 -870 1400 -830 {}
N 1560 -1040 1560 -1080 {}
N 1560 -980 1560 -940 {}
N 1800 -1060 1760 -1060 {}
N 1800 -1030 1760 -1030 {}
N 1800 -1000 1760 -1000 {}
N 1800 -970 1760 -970 {}
N 1800 -940 1760 -940 {}
N 2000 -1045 2040 -1045 {}
N 1900 -1120 1900 -1160 {}
N 1900 -880 1900 -840 {}
N 2140 -1030 2140 -1070 {}
N 2140 -970 2140 -930 {}
T {TB_TRAN  -  delay and polarity of comparator on the cell's charge path, I_B = 1.93 uA} 60 -1330 0 0 0.7 0.7 {}
T {C_S 54.52 fF} 1440 -840 0 0 0.3 0.3 {layer=4}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -1180 0 0 {name=VDD_BIAS value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -1250 0 0 {name=l3 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 290 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/isource.sym} 120 -900 0 0 {name=IREFN value="\{IREF\}"}
C {devices/lab_pin.sym} 120 -970 0 0 {name=l5 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 120 -830 0 0 {name=l6 sig_type=std_logic lab=nbias}
C {symbols/nfet_03v3.sym} 320 -900 0 0 {name=REFN
L=1u W=20u nf=10 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 260 -900 0 0 {name=l7 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -970 0 0 {name=l8 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -830 0 0 {name=l9 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 380 -900 0 1 {name=l10 sig_type=std_logic lab=0}
C {devices/isource.sym} 480 -900 0 0 {name=IREFP value="\{IREF\}"}
C {devices/lab_pin.sym} 480 -970 0 0 {name=l11 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 480 -830 0 0 {name=l12 sig_type=std_logic lab=0}
C {symbols/pfet_03v3.sym} 680 -900 0 0 {name=REFP
L=0.28u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 620 -900 0 0 {name=l13 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -830 0 0 {name=l14 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -970 0 0 {name=l15 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 740 -900 0 1 {name=l16 sig_type=std_logic lab=vddb}
C {devices/vsource.sym} 460 -1180 0 0 {name=VCLK value="0" savecurrent=false}
C {devices/lab_pin.sym} 460 -1250 0 0 {name=l17 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 460 -1110 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1180 0 0 {name=VVREF value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 630 -1250 0 0 {name=l19 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 630 -1110 0 0 {name=l20 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -620 0 0 {name=VDRV value="PWL(0 \{VIN\} \{TCONN\} \{VIN\} \{TCONN+TEDGE\} \{VR_LO\} \{TR\} \{VR_LO\} \{TR+20u\} \{VR_LO+20u*SLOPE\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -690 0 0 {name=l21 sig_type=std_logic lab=drv}
C {devices/lab_pin.sym} 120 -550 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -450 0 0 {name=VS2 value="PWL(0 1 \{TS\} 1 \{TS+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 -520 0 0 {name=l23 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 120 -380 0 0 {name=l24 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1400 -1140 0 0 {name=S2 model=swideal}
C {devices/lab_pin.sym} 1400 -1210 0 0 {name=l25 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1400 -1070 0 0 {name=l26 sig_type=std_logic lab=plate}
C {devices/lab_pin.sym} 1320 -1140 0 0 {name=l27 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1320 -1120 0 0 {name=l28 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 1400 -900 0 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 1400 -970 0 0 {name=l29 sig_type=std_logic lab=plate}
C {devices/lab_pin.sym} 1400 -830 0 0 {name=l30 sig_type=std_logic lab=drv}
C {devices/res.sym} 1560 -1010 0 0 {name=RLKT value=1e15 footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 1560 -1080 0 0 {name=l31 sig_type=std_logic lab=plate}
C {devices/lab_pin.sym} 1560 -940 0 0 {name=l32 sig_type=std_logic lab=0}
C {comparator.sym} 1900 -1000 0 0 {name=XDUT}
C {devices/lab_pin.sym} 1760 -1060 0 0 {name=l33 sig_type=std_logic lab=plate}
C {devices/lab_pin.sym} 1760 -1030 0 0 {name=l34 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1760 -1000 0 0 {name=l35 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1760 -970 0 0 {name=l36 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1760 -940 0 0 {name=l37 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 2040 -1045 0 1 {name=l38 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1900 -1160 0 0 {name=l39 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1900 -840 0 0 {name=l40 sig_type=std_logic lab=0}
C {devices/capa.sym} 2140 -1000 0 0 {name=CLOAD value=1e-14 m=1}
C {devices/lab_pin.sym} 2140 -1070 0 0 {name=l41 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 2140 -930 0 0 {name=l42 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1300 -700 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
.param VDD=3.3
.temp 27
.param IREF=1.93077e-06
.param VIN=0.691415326
.param VR_LO=0.42
.param LSB=0.006701613
.param TCOUNT=50n
.param SLOPE='LSB/TCOUNT'
.param TS=300n
.param TCONN=310n
.param TR=400n
.param TEDGE=100p
.csparam cs_vdd=\{VDD\}
.csparam cs_tr=\{TR\}
.csparam cs_tconn=\{TCONN\}
.csparam cs_tideal=\{TR+(VIN-VR_LO)/SLOPE\}
.options savecurrents reltol=1e-4 gmin=1e-15
.control
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
let lvla = hi90
let lvlb = lo10
set vtrip_s = \"1.650390\"
tran 0.25n 1.34e-05 0 0.5n
meas tran t_cross when v(plate)=1.65 rise=1 td=$&cs_tr
meas tran t_cs when v(plate)=$vtrip_s rise=1 td=$&cs_tr
meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr
meas tran t_ea when v(dout)=$&lvla fall=1 td=$&cs_tr
meas tran t_eb when v(dout)=$&lvlb fall=1 td=$&cs_tr
meas tran armed find v(dout) at=$&cs_tr
meas tran vplate_tr find v(plate) at=$&cs_tr
meas tran i_avg avg i(vdd_source) from=$&cs_tconn to=$&t_cross
let delay_vref = t_dout - t_cross
let delay_dyn = t_dout - t_cs
let edge = t_eb - t_ea
let ped_counts = (t_dout - $&cs_tideal) / 50e-9
let p_avg = -$&cs_vdd * i_avg
echo \"RESULT_BEGIN\"
print delay_vref
print delay_dyn
print edge
print ped_counts
print armed
print p_avg
print vplate_tr
print t_dout
echo \"RESULT_END\"
quit
.endc"}
