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
N 340 -870 340 -830 {}
N 340 -930 340 -970 {}
N 340 -900 380 -900 {}
N 120 -630 120 -670 {}
N 120 -570 120 -530 {}
N 120 -460 120 -500 {}
N 120 -400 120 -360 {}
N 1400 -1170 1400 -1210 {}
N 1400 -1110 1400 -1070 {}
N 1360 -1140 1320 -1140 {}
N 1360 -1120 1320 -1120 {}
N 1400 -870 1400 -830 {}
N 1400 -930 1400 -970 {}
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
N 2200 -1065 2160 -1065 {}
N 2200 -1025 2160 -1025 {}
N 2400 -1065 2440 -1065 {}
N 2300 -1125 2300 -1165 {}
N 2300 -965 2300 -925 {}
N 2540 -1095 2540 -1135 {}
N 2540 -1035 2540 -995 {}
T {TB_KICK  -  comparator + latch on the cell's charge path, count clock running} 60 -1360 0 0 0.7 0.7 {}
T {SUPPLIES / BIAS / CLOCK} 40 -1292 0 0 0.45 0.45 {layer=4}
T {clk 10-90 % 0.5 ns} 760 -1010 0 0 0.3 0.3 {layer=4}
T {I_B 3.25 uA} 40 -790 0 0 0.3 0.3 {layer=4}
T {VIN = 0.875 V  (code 64)} 40 -750 0 0 0.3 0.3 {layer=4}
T {CHARGE PATH} 1240 -1292 0 0 0.45 0.45 {layer=4}
T {C_S 54.52 fF} 1440 -840 0 0 0.3 0.3 {layer=4}
T {COMPARATOR + LATCH} 1760 -1292 0 0 0.45 0.45 {layer=4}
T {CQ = 50 fF} 2580 -995 0 0 0.3 0.3 {layer=4}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -1180 0 0 {name=VDVDD value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -1250 0 0 {name=l3 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 290 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 460 -1180 0 0 {name=VVBL value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -1250 0 0 {name=l5 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 460 -1110 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1180 0 0 {name=VVREF value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 630 -1250 0 0 {name=l7 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 630 -1110 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 800 -1180 0 0 {name=VCLK value="PULSE(0 \{VDD\} \{TCOUNT-TCE/2\} \{TCE\} \{TCE\} \{TCOUNT/2-TCE\} \{TCOUNT\})" savecurrent=false}
C {devices/lab_pin.sym} 800 -1250 0 0 {name=l9 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 800 -1110 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/isource.sym} 120 -900 0 0 {name=IREFP value="\{IBIAS\}"}
C {devices/lab_pin.sym} 120 -970 0 0 {name=l11 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 120 -830 0 0 {name=l12 sig_type=std_logic lab=0}
C {symbols/pfet_03v3.sym} 320 -900 0 0 {name=REFP
L=0.28u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 260 -900 0 0 {name=l13 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 340 -830 0 0 {name=l14 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 340 -970 0 0 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 380 -900 0 1 {name=l16 sig_type=std_logic lab=vdd}
C {devices/vsource.sym} 120 -600 0 0 {name=VBOT value="PWL(0 \{VIN\} \{TCONN\} \{VIN\} \{TCONN+TEDGE\} \{VR_LO\} \{TR\} \{VR_LO\} \{TR+TRAMP\} \{VR_HI+OVR\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -670 0 0 {name=l17 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 120 -530 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -430 0 0 {name=VS2 value="PWL(0 1 \{TS\} 1 \{TS+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 -500 0 0 {name=l19 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 120 -360 0 0 {name=l20 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1400 -1140 0 0 {name=S2 model=swideal}
C {devices/lab_pin.sym} 1400 -1210 0 0 {name=l21 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1400 -1070 0 0 {name=l22 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1320 -1140 0 0 {name=l23 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1320 -1120 0 0 {name=l24 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 1400 -900 0 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 1400 -830 0 0 {name=l25 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1400 -970 0 0 {name=l26 sig_type=std_logic lab=bot}
C {devices/res.sym} 1560 -1010 0 0 {name=RLKT value=1e15 footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 1560 -1080 0 0 {name=l27 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1560 -940 0 0 {name=l28 sig_type=std_logic lab=0}
C {comparator.sym} 1900 -1000 0 0 {name=XDUT}
C {devices/lab_pin.sym} 1760 -1060 0 0 {name=l29 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1760 -1030 0 0 {name=l30 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1760 -1000 0 0 {name=l31 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1760 -970 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1760 -940 0 0 {name=l33 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 2040 -1045 0 1 {name=l34 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1900 -1160 0 0 {name=l35 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1900 -840 0 0 {name=l36 sig_type=std_logic lab=0}
C {latch.sym} 2300 -1045 0 0 {name=XL}
C {devices/lab_pin.sym} 2160 -1065 0 0 {name=l37 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 2160 -1025 0 0 {name=l38 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2440 -1065 0 1 {name=l39 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 2300 -1165 0 0 {name=l40 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 2300 -925 0 0 {name=l41 sig_type=std_logic lab=0}
C {devices/capa.sym} 2540 -1065 0 0 {name=CQ value=50f m=1}
C {devices/lab_pin.sym} 2540 -1135 0 0 {name=l42 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 2540 -995 0 0 {name=l43 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1240 -810 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
.param VDD=3.3
.param IBIAS='1.681*1.93077e-6'
.param VIN=0.875
.param VR_LO=0.5
.param VR_HI=2.0
.param LSB=0.005859375
.param TCOUNT=50n
.param SLOPE='LSB/TCOUNT'
.param OVR='20*LSB'
.param TS=300n
.param TCONN=310n
.param TR=400n
.param TEDGE=100p
.param TCE=6.250000e-10
.param TRAMP='(VR_HI+OVR-VR_LO)/SLOPE'
.param TSTOP='TR+(VIN-VR_LO)/SLOPE+300n'
.temp 27
.csparam cs_vdd=\{VDD\}
.csparam cs_tr=\{TR\}
.csparam cs_tcount=\{TCOUNT\}
.options savecurrents reltol=1e-4 gmin=1e-15
.tran 1n \{TSTOP\} 0 2n
.control
run
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_cross when v(top)=v(vbl) rise=1 td=$&cs_tr
meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr
meas tran t_f90 when v(dout)=$&hi90 fall=1 td=$&cs_tr
meas tran t_f10 when v(dout)=$&lo10 fall=1 td=$&cs_tr
meas tran t_q when v(q)=$&half fall=1 td=$&cs_tr
let delay = t_dout - t_cross
let dout_fall = t_f10 - t_f90
let t_edge = $&cs_tr + $&cs_tcount/2 + floor((t_q - $&cs_tr - $&cs_tcount/2) / $&cs_tcount) * $&cs_tcount
let tcq = t_q - t_edge
let t_k = $&cs_tr + $&cs_tcount/2 + floor((t_cross - $&cs_tr - $&cs_tcount/2) / $&cs_tcount) * $&cs_tcount
let t_kc = t_k - 6e-9
let t_ka = t_k - 2e-9
let t_kb = t_k + 2e-9
meas tran v_kc find v(top) at=$&t_kc
meas tran v_ka find v(top) at=$&t_ka
meas tran v_kb find v(top) at=$&t_kb
let plate_step = (v_kb - v_ka) - (v_ka - v_kc)
set numdgt=10
echo RESULT_BEGIN
print t_cross t_dout t_q delay dout_fall tcq plate_step
echo RESULT_END
quit
.endc"}
