v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1010 120 -1050 {}
N 120 -950 120 -910 {}
N 348 -1010 348 -1050 {}
N 348 -950 348 -910 {}
N 518 -1010 518 -1050 {}
N 518 -950 518 -910 {}
N 770 -1010 770 -1050 {}
N 770 -950 770 -910 {}
N 1038 -1010 1038 -1050 {}
N 1038 -950 1038 -910 {}
N 1634 -1010 1634 -1050 {}
N 1634 -950 1634 -910 {}
N 1804 -1010 1804 -1050 {}
N 1804 -950 1804 -910 {}
N 220 -530 220 -490 {}
N 180 -560 140 -560 {}
N 220 -590 220 -630 {}
N 220 -560 330 -560 {}
N 720 -560 760 -560 {}
N 560 -560 520 -560 {}
N 640 -620 640 -660 {}
N 640 -500 640 -460 {}
N 1240 -560 1280 -560 {}
N 1000 -560 960 -560 {}
N 1000 -620 960 -620 {}
N 1000 -500 960 -500 {}
N 1120 -680 1120 -720 {}
N 1120 -440 1120 -400 {}
N 1540 -590 1540 -630 {}
N 1540 -530 1540 -490 {}
N 1500 -560 1460 -560 {}
N 1500 -540 1460 -540 {}
N 120 -210 120 -250 {}
N 120 -150 120 -110 {}
N 400 -210 400 -250 {}
N 400 -150 400 -110 {}
N 1480 -210 1480 -250 {}
N 1480 -150 1480 -110 {}
N 2640 -180 2680 -180 {}
N 2480 -210 2440 -210 {}
N 2480 -180 2440 -180 {}
N 2480 -150 2440 -150 {}
N 120 -50 120 -90 {}
N 120 10 120 50 {}
N 400 -50 400 -90 {}
N 400 10 400 50 {}
N 1480 -50 1480 -90 {}
N 1480 10 1480 50 {}
N 2640 -20 2680 -20 {}
N 2480 -50 2440 -50 {}
N 2480 -20 2440 -20 {}
N 2480 10 2440 10 {}
N 120 110 120 70 {}
N 120 170 120 210 {}
N 400 110 400 70 {}
N 400 170 400 210 {}
N 1480 110 1480 70 {}
N 1480 170 1480 210 {}
N 2640 140 2680 140 {}
N 2480 110 2440 110 {}
N 2480 140 2440 140 {}
N 2480 170 2440 170 {}
N 120 270 120 230 {}
N 120 330 120 370 {}
N 400 270 400 230 {}
N 400 330 400 370 {}
N 1480 270 1480 230 {}
N 1480 330 1480 370 {}
N 2640 300 2680 300 {}
N 2480 270 2440 270 {}
N 2480 300 2440 300 {}
N 2480 330 2440 330 {}
T {TB_TRAN  -  two records of vrlo_ref on ramp_simple, forced end of ramp, KS = 1} 40 -1240 0 0 0.7 0.7 {}
T {SUPPLY + BIAS + TIMELINE} 60 -1120 0 0 0.45 0.45 {}
T {DUT + RAMP LOAD (../ramp_gen) + FORCED END OF RAMP} 560 -760 0 0 0.45 0.45 {}
T {I_B = 1.37 uA} 488 -880 0 0 0.35 0.35 {layer=4}
T {I_RD = 3.25 uA} 740 -880 0 0 0.35 0.35 {layer=4}
T {7/55 AVDD} 560 -410 0 0 0.35 0.35 {layer=4}
T {S1 MODELS OF THE FOUR CELLS, KS = 1} 60 -330 0 0 0.45 0.45 {}
T {CEQ = 40 fF per cell} 760 -330 0 0 0.35 0.35 {layer=4}
C {devices/vsource.sym} 120 -980 0 0 {name=VAVDD value="PWL(0 0 \{TPWR\} \{VDD\})" savecurrent=false}
C {devices/vsource.sym} 348 -980 0 0 {name=VAMR value="0" savecurrent=false}
C {devices/isource.sym} 518 -980 0 0 {name=IB value="PWL(0 0 \{TPWR\} 1.37e-06)"}
C {vrlo_ref.sym} 640 -560 0 0 {name=XREG}
C {devices/isource.sym} 770 -980 0 0 {name=IRD value="PWL(0 0 \{TPWR\} 3.2512e-06)"}
C {symbols/pfet_03v3.sym} 200 -560 0 0 {name=XRD
L=1u
W=20u
nf=10
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/vsource.sym} 1038 -980 0 0 {name=VRST value="PWL(0 0 \{TPWR\} \{VDD\} \{TR\} \{VDD\} \{TR+0.1n\} 0 \{TD\} 0 \{TD+0.1n\} \{VDD\})" savecurrent=false}
C {ramp_simple.sym} 1120 -560 0 0 {name=XRAMP}
C {devices/vsource.sym} 1634 -980 0 0 {name=VTOPS value="2.1557" savecurrent=false}
C {devices/vsource.sym} 1804 -980 0 0 {name=VFRC value="PWL(0 0 \{TR+20n\} 0 \{TR+20.1n\} 3.3 \{TD-1n\} 3.3 \{TD-0.9n\} 0)" savecurrent=false}
C {devices/switch_ngspice.sym} 1540 -560 0 0 {name=SFRC model=swm}
C {devices/vsource.sym} 400 -180 0 0 {name=VP0 value="PWL(0 3.3 \{TS0+5n\} 3.3 \{TS0+5.1n\} 0 \{TD+50n\} 0 \{TD+50.1n\} 3.3 \{TS0B+5n\} 3.3 \{TS0B+5.1n\} 0)" savecurrent=false}
C {devices/vsource.sym} 400 -20 0 0 {name=VP1 value="PWL(0 3.3 \{TS0+TSP+5n\} 3.3 \{TS0+TSP+5.1n\} 0 \{TD+50n\} 0 \{TD+50.1n\} 3.3 \{TS0B+TSP+5n\} 3.3 \{TS0B+TSP+5.1n\} 0)" savecurrent=false}
C {devices/vsource.sym} 400 140 0 0 {name=VP2 value="PWL(0 3.3 \{TS0+2*TSP+5n\} 3.3 \{TS0+2*TSP+5.1n\} 0 \{TD+50n\} 0 \{TD+50.1n\} 3.3 \{TS0B+2*TSP+5n\} 3.3 \{TS0B+2*TSP+5.1n\} 0)" savecurrent=false}
C {devices/vsource.sym} 400 300 0 0 {name=VP3 value="PWL(0 3.3 \{TS0+3*TSP+5n\} 3.3 \{TS0+3*TSP+5.1n\} 0 \{TD+50n\} 0 \{TD+50.1n\} 3.3 \{TS0B+3*TSP+5n\} 3.3 \{TS0B+3*TSP+5.1n\} 0)" savecurrent=false}
C {devices/vsource.sym} 1480 -180 0 0 {name=VQ0 value="PWL(0 0 \{TS0+10n\} 0 \{TS0+10.1n\} 3.3 \{TD+20n\} 3.3 \{TD+20.1n\} 0 \{TS0B+10n\} 0 \{TS0B+10.1n\} 3.3)" savecurrent=false}
C {devices/vsource.sym} 1480 -20 0 0 {name=VQ1 value="PWL(0 0 \{TS0+TSP+10n\} 0 \{TS0+TSP+10.1n\} 3.3 \{TD+20n\} 3.3 \{TD+20.1n\} 0 \{TS0B+TSP+10n\} 0 \{TS0B+TSP+10.1n\} 3.3)" savecurrent=false}
C {devices/vsource.sym} 1480 140 0 0 {name=VQ2 value="PWL(0 0 \{TS0+2*TSP+10n\} 0 \{TS0+2*TSP+10.1n\} 3.3 \{TD+20n\} 3.3 \{TD+20.1n\} 0 \{TS0B+2*TSP+10n\} 0 \{TS0B+2*TSP+10.1n\} 3.3)" savecurrent=false}
C {devices/vsource.sym} 1480 300 0 0 {name=VQ3 value="PWL(0 0 \{TS0+3*TSP+10n\} 0 \{TS0+3*TSP+10.1n\} 3.3 \{TD+20n\} 3.3 \{TD+20.1n\} 0 \{TS0B+3*TSP+10n\} 0 \{TS0B+3*TSP+10.1n\} 3.3)" savecurrent=false}
C {devices/vsource.sym} 120 -180 0 0 {name=VV0 value="\{VIN0\}" savecurrent=false}
C {devices/vsource.sym} 120 -20 0 0 {name=VV1 value="\{VIN1\}" savecurrent=false}
C {devices/vsource.sym} 120 140 0 0 {name=VV2 value="\{VIN2\}" savecurrent=false}
C {devices/vsource.sym} 120 300 0 0 {name=VV3 value="\{VIN3\}" savecurrent=false}
C {s1cell.sym} 2560 -180 0 0 {name=XS0
c=4e-14}
C {s1cell.sym} 2560 -20 0 0 {name=XS1
c=4e-14}
C {s1cell.sym} 2560 140 0 0 {name=XS2
c=4e-14}
C {s1cell.sym} 2560 300 0 0 {name=XS3
c=4e-14}
C {devices/lab_pin.sym} 120 -1050 0 0 {name=l1 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 120 -910 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 348 -1050 0 0 {name=l3 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 348 -910 0 0 {name=l4 sig_type=std_logic lab=avdd_r}
C {devices/lab_pin.sym} 518 -1050 0 0 {name=l5 sig_type=std_logic lab=avdd_r}
C {devices/lab_pin.sym} 518 -910 0 0 {name=l6 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 770 -1050 0 0 {name=l7 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 770 -910 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1038 -1050 0 0 {name=l9 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 1038 -910 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1634 -1050 0 0 {name=l11 sig_type=std_logic lab=vtop}
C {devices/lab_pin.sym} 1634 -910 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1804 -1050 0 0 {name=l13 sig_type=std_logic lab=frc}
C {devices/lab_pin.sym} 1804 -910 0 0 {name=l14 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 220 -490 0 0 {name=l15 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 140 -560 0 0 {name=l16 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 220 -630 0 0 {name=l17 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 330 -560 0 1 {name=l18 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 760 -560 0 1 {name=l19 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 520 -560 0 0 {name=l20 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 640 -660 0 0 {name=l21 sig_type=std_logic lab=avdd_r}
C {devices/lab_pin.sym} 640 -460 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1280 -560 0 1 {name=l23 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 960 -560 0 0 {name=l24 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 960 -620 0 0 {name=l25 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 960 -500 0 0 {name=l26 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 1120 -720 0 0 {name=l27 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1120 -400 0 0 {name=l28 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1540 -630 0 0 {name=l29 sig_type=std_logic lab=vtop}
C {devices/lab_pin.sym} 1540 -490 0 0 {name=l30 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1460 -560 0 0 {name=l31 sig_type=std_logic lab=frc}
C {devices/lab_pin.sym} 1460 -540 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 120 -250 0 0 {name=l33 sig_type=std_logic lab=v0}
C {devices/lab_pin.sym} 120 -110 0 0 {name=l34 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 400 -250 0 0 {name=l35 sig_type=std_logic lab=p0}
C {devices/lab_pin.sym} 400 -110 0 0 {name=l36 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1480 -250 0 0 {name=l37 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 1480 -110 0 0 {name=l38 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2680 -180 0 1 {name=l39 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2440 -210 0 0 {name=l40 sig_type=std_logic lab=v0}
C {devices/lab_pin.sym} 2440 -180 0 0 {name=l41 sig_type=std_logic lab=p0}
C {devices/lab_pin.sym} 2440 -150 0 0 {name=l42 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 120 -90 0 0 {name=l43 sig_type=std_logic lab=v1}
C {devices/lab_pin.sym} 120 50 0 0 {name=l44 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 400 -90 0 0 {name=l45 sig_type=std_logic lab=p1}
C {devices/lab_pin.sym} 400 50 0 0 {name=l46 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1480 -90 0 0 {name=l47 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 1480 50 0 0 {name=l48 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2680 -20 0 1 {name=l49 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2440 -50 0 0 {name=l50 sig_type=std_logic lab=v1}
C {devices/lab_pin.sym} 2440 -20 0 0 {name=l51 sig_type=std_logic lab=p1}
C {devices/lab_pin.sym} 2440 10 0 0 {name=l52 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 120 70 0 0 {name=l53 sig_type=std_logic lab=v2}
C {devices/lab_pin.sym} 120 210 0 0 {name=l54 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 400 70 0 0 {name=l55 sig_type=std_logic lab=p2}
C {devices/lab_pin.sym} 400 210 0 0 {name=l56 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1480 70 0 0 {name=l57 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 1480 210 0 0 {name=l58 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2680 140 0 1 {name=l59 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2440 110 0 0 {name=l60 sig_type=std_logic lab=v2}
C {devices/lab_pin.sym} 2440 140 0 0 {name=l61 sig_type=std_logic lab=p2}
C {devices/lab_pin.sym} 2440 170 0 0 {name=l62 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 120 230 0 0 {name=l63 sig_type=std_logic lab=v3}
C {devices/lab_pin.sym} 120 370 0 0 {name=l64 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 400 230 0 0 {name=l65 sig_type=std_logic lab=p3}
C {devices/lab_pin.sym} 400 370 0 0 {name=l66 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1480 230 0 0 {name=l67 sig_type=std_logic lab=q3}
C {devices/lab_pin.sym} 1480 370 0 0 {name=l68 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2680 300 0 1 {name=l69 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2440 270 0 0 {name=l70 sig_type=std_logic lab=v3}
C {devices/lab_pin.sym} 2440 300 0 0 {name=l71 sig_type=std_logic lab=p3}
C {devices/lab_pin.sym} 2440 330 0 0 {name=l72 sig_type=std_logic lab=q3}
C {devices/code_shown.sym} 40 480 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice
.temp 27
.param TGAP=300n
.param VDD=3.3 TPWR=100n T0=1e-05 TS0='T0+300n' TSP=40n TR='TS0+3*TSP+TGAP'
.param TD='TR+1.5u' TREC=1e-06 TS0B='TD+TREC' TR2='TS0B+3*TSP+TGAP' TSTOP='TR2+20n'
.param KS=1 VLO='0.1272727273*VDD' DV='1.5/256'
.param VIN0='VLO+KS*16.5*DV' VIN1='VLO+KS*80.5*DV' VIN2='VLO+KS*160.5*DV' VIN3='VLO+KS*240.5*DV'
.model swm sw vt=1.65 vh=0.1 ron=1k roff=1e14
.subckt s1cell vramp vin pre s1 c=40f
SP b vin pre 0 swm
SS b vramp s1 0 swm
CB b 0 \{c\}
.ends
.options reltol=1e-5 gmin=1e-15
.tran 0.2n \{TSTOP\} 0 2n
.measure tran vp_q FIND v(vramp) AT=\{TS0-1n\}
.measure tran vp_q2 FIND v(vramp) AT=\{TS0B-1n\}
.measure tran vp_t0 FIND v(vramp) AT=\{T0\}
.measure tran vp_t2u FIND v(vramp) AT=2u
.measure tran vp_tr FIND v(vramp) AT=\{TR-0.2n\}
.measure tran vp_tr2 FIND v(vramp) AT=\{TR2-0.2n\}
.measure tran vr_q FIND v(vrlo) AT=\{TS0-1n\}
.measure tran vtap_q FIND v(xreg.tap) AT=\{TS0-1n\}
.measure tran vg_q FIND v(xreg.g) AT=\{TS0-1n\}
.measure tran vr_frc FIND v(vrlo) AT=\{TD-1n\}
.measure tran vp_td FIND v(vramp) AT=\{TD-2n\}
.measure tran vr_pk MAX v(vrlo) FROM=\{TD\} TO=\{TS0B\}
.measure tran vp_kpk MAX v(vramp) FROM=\{TS0\} TO=\{TR\}
.measure tran ireg_q AVG i(VAMR) FROM=\{TS0-200n\} TO=\{TS0-10n\}
.measure tran ireg_r AVG i(VAMR) FROM=\{TD-500n\} TO=\{TD-10n\}
.control
set num_threads=1
run
quit
.endc"}
