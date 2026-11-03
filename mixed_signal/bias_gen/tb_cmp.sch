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
N 970 -1210 970 -1250 {}
N 970 -1150 970 -1110 {}
N 120 -930 120 -970 {}
N 120 -870 120 -830 {}
N 340 -930 340 -970 {}
N 300 -900 260 -900 {}
N 340 -870 340 -830 {}
N 340 -900 380 -900 {}
N 480 -930 480 -970 {}
N 480 -870 480 -830 {}
N 700 -870 700 -830 {}
N 660 -900 620 -900 {}
N 700 -930 700 -970 {}
N 700 -900 740 -900 {}
N 1400 -1140 1360 -1140 {}
N 1400 -1110 1360 -1110 {}
N 1400 -1080 1360 -1080 {}
N 1400 -1050 1360 -1050 {}
N 1400 -1020 1360 -1020 {}
N 1600 -1125 1640 -1125 {}
N 1500 -1200 1500 -1240 {}
N 1500 -960 1500 -920 {}
N 1760 -1110 1760 -1150 {}
N 1760 -1050 1760 -1010 {}
N 300 -640 300 -680 {}
N 300 -400 300 -360 {}
N 400 -600 520 -600 {}
N 400 -575 460 -575 {}
N 400 -550 520 -550 {}
N 400 -525 460 -525 {}
N 400 -500 520 -500 {}
N 400 -475 460 -475 {}
N 400 -450 520 -450 {}
N 780 -530 780 -490 {}
N 740 -560 700 -560 {}
N 780 -590 780 -630 {}
N 780 -560 820 -560 {}
N 1040 -530 1040 -490 {}
N 1000 -560 960 -560 {}
N 1040 -590 1040 -630 {}
N 1040 -560 1080 -560 {}
N 1300 -530 1300 -490 {}
N 1260 -560 1220 -560 {}
N 1300 -590 1300 -630 {}
N 1300 -560 1340 -560 {}
N 1560 -530 1560 -490 {}
N 1520 -560 1480 -560 {}
N 1560 -590 1560 -630 {}
N 1560 -560 1600 -560 {}
N 1820 -590 1820 -630 {}
N 1780 -560 1740 -560 {}
N 1820 -530 1820 -490 {}
N 1820 -560 1860 -560 {}
N 2080 -590 2080 -630 {}
N 2040 -560 2000 -560 {}
N 2080 -530 2080 -490 {}
N 2080 -560 2120 -560 {}
N 120 -130 120 -170 {}
N 120 -70 120 -30 {}
N 120 110 120 70 {}
N 120 170 120 210 {}
N 760 -130 760 -170 {}
N 760 -70 760 -30 {}
N 720 -100 680 -100 {}
N 720 -80 680 -80 {}
N 920 110 920 70 {}
N 920 170 920 210 {}
N 1080 -130 1080 -170 {}
N 1080 -70 1080 -30 {}
N 1280 -160 1240 -160 {}
N 1280 -130 1240 -130 {}
N 1280 -100 1240 -100 {}
N 1280 -70 1240 -70 {}
N 1280 -40 1240 -40 {}
N 1480 -145 1520 -145 {}
N 1380 -220 1380 -260 {}
N 1380 20 1380 60 {}
N 1620 -130 1620 -170 {}
N 1620 -70 1620 -30 {}
T {TB_CMP  -  comparator on icmp0 of bias_gen: static trip, then delay on the charge path} 40 -1340 0 0 0.7 0.7 {}
T {IREF 0: pbias from the generator} 60 -1010 0 0 0.3 0.3 {layer=4}
T {STATIC TRIP} 1400 -1290 0 0 0.4 0.4 {}
T {GENERATOR, the other consumers' diodes} 60 -740 0 0 0.4 0.4 {}
T {CHARGE PATH, VIN = VR_LO + 40.5 LSB} 60 -260 0 0 0.4 0.4 {}
T {C_S 54.52 fF} 960 200 0 0 0.3 0.3 {layer=4}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -1180 0 0 {name=VDD_BIAS value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -1250 0 0 {name=l3 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 290 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 460 -1180 0 0 {name=VVBL value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -1250 0 0 {name=l5 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 460 -1110 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1180 0 0 {name=VVREF value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 630 -1250 0 0 {name=l7 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 630 -1110 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 800 -1180 0 0 {name=VCLK value="0" savecurrent=false}
C {devices/lab_pin.sym} 800 -1250 0 0 {name=l9 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 800 -1110 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/vsource.sym} 970 -1180 0 0 {name=VDC value="1.65" savecurrent=false}
C {devices/lab_pin.sym} 970 -1250 0 0 {name=l11 sig_type=std_logic lab=vdc}
C {devices/lab_pin.sym} 970 -1110 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/isource.sym} 120 -900 0 0 {name=IREFN value="\{IREF\}"}
C {devices/lab_pin.sym} 120 -970 0 0 {name=l13 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 120 -830 0 0 {name=l14 sig_type=std_logic lab=nbias}
C {symbols/nfet_03v3.sym} 320 -900 0 0 {name=XREFN
L=1u
W=20u
nf=10
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 340 -970 0 0 {name=l15 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 260 -900 0 0 {name=l16 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -830 0 0 {name=l17 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 380 -900 0 1 {name=l18 sig_type=std_logic lab=0}
C {devices/isource.sym} 480 -900 0 0 {name=IREFP value="\{IREF\}"}
C {devices/lab_pin.sym} 480 -970 0 0 {name=l19 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 480 -830 0 0 {name=l20 sig_type=std_logic lab=0}
C {symbols/pfet_03v3.sym} 680 -900 0 0 {name=XREFP
L=0.28u
W=1u
nf=1
m=1
ad=1.8e-13
pd=2.36e-06
as=1.8e-13
ps=2.36e-06
nrd=0.18
nrs=0.18
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad pd=@pd as=@as ps=@ps nrd=@nrd nrs=@nrs"}
C {devices/lab_pin.sym} 700 -830 0 0 {name=l21 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 620 -900 0 0 {name=l22 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -970 0 0 {name=l23 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 740 -900 0 1 {name=l24 sig_type=std_logic lab=vddb}
C {comparator.sym} 1500 -1080 0 0 {name=XDC}
C {devices/lab_pin.sym} 1360 -1140 0 0 {name=l25 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1360 -1110 0 0 {name=l26 sig_type=std_logic lab=vdc}
C {devices/lab_pin.sym} 1360 -1080 0 0 {name=l27 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1360 -1050 0 0 {name=l28 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1360 -1020 0 0 {name=l29 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1640 -1125 0 1 {name=l30 sig_type=std_logic lab=doutdc}
C {devices/lab_pin.sym} 1500 -1240 0 0 {name=l31 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1500 -920 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/capa.sym} 1760 -1080 0 0 {name=CLDC value=1e-14 m=1}
C {devices/lab_pin.sym} 1760 -1150 0 0 {name=l33 sig_type=std_logic lab=doutdc}
C {devices/lab_pin.sym} 1760 -1010 0 0 {name=l34 sig_type=std_logic lab=0}
C {bias_gen.sym} 300 -520 0 0 {name=XG}
C {devices/lab_pin.sym} 300 -680 0 0 {name=l35 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 300 -360 0 0 {name=l36 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 520 -600 0 1 {name=l37 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 460 -575 0 1 {name=l38 sig_type=std_logic lab=gc1}
C {devices/lab_pin.sym} 520 -550 0 1 {name=l39 sig_type=std_logic lab=gc2}
C {devices/lab_pin.sym} 460 -525 0 1 {name=l40 sig_type=std_logic lab=gc3}
C {devices/lab_pin.sym} 520 -500 0 1 {name=l41 sig_type=std_logic lab=glr}
C {devices/lab_pin.sym} 460 -475 0 1 {name=l42 sig_type=std_logic lab=glv}
C {devices/lab_pin.sym} 520 -450 0 1 {name=l43 sig_type=std_logic lab=glb}
C {symbols/pfet_03v3.sym} 760 -560 0 0 {name=XGDgc1
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
C {devices/lab_pin.sym} 780 -490 0 0 {name=l44 sig_type=std_logic lab=gc1}
C {devices/lab_pin.sym} 700 -560 0 0 {name=l45 sig_type=std_logic lab=gc1}
C {devices/lab_pin.sym} 780 -630 0 0 {name=l46 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 820 -560 0 1 {name=l47 sig_type=std_logic lab=vddb}
C {symbols/pfet_03v3.sym} 1020 -560 0 0 {name=XGDgc2
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
C {devices/lab_pin.sym} 1040 -490 0 0 {name=l48 sig_type=std_logic lab=gc2}
C {devices/lab_pin.sym} 960 -560 0 0 {name=l49 sig_type=std_logic lab=gc2}
C {devices/lab_pin.sym} 1040 -630 0 0 {name=l50 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 1080 -560 0 1 {name=l51 sig_type=std_logic lab=vddb}
C {symbols/pfet_03v3.sym} 1280 -560 0 0 {name=XGDgc3
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
C {devices/lab_pin.sym} 1300 -490 0 0 {name=l52 sig_type=std_logic lab=gc3}
C {devices/lab_pin.sym} 1220 -560 0 0 {name=l53 sig_type=std_logic lab=gc3}
C {devices/lab_pin.sym} 1300 -630 0 0 {name=l54 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 1340 -560 0 1 {name=l55 sig_type=std_logic lab=vddb}
C {symbols/pfet_03v3.sym} 1540 -560 0 0 {name=XGDR
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
C {devices/lab_pin.sym} 1560 -490 0 0 {name=l56 sig_type=std_logic lab=glr}
C {devices/lab_pin.sym} 1480 -560 0 0 {name=l57 sig_type=std_logic lab=glr}
C {devices/lab_pin.sym} 1560 -630 0 0 {name=l58 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 1600 -560 0 1 {name=l59 sig_type=std_logic lab=vddb}
C {symbols/nfet_03v3.sym} 1800 -560 0 0 {name=XGDV
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
C {devices/lab_pin.sym} 1820 -630 0 0 {name=l60 sig_type=std_logic lab=glv}
C {devices/lab_pin.sym} 1740 -560 0 0 {name=l61 sig_type=std_logic lab=glv}
C {devices/lab_pin.sym} 1820 -490 0 0 {name=l62 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1860 -560 0 1 {name=l63 sig_type=std_logic lab=0}
C {symbols/nfet_03v3.sym} 2060 -560 0 0 {name=XGDB
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
C {devices/lab_pin.sym} 2080 -630 0 0 {name=l64 sig_type=std_logic lab=glb}
C {devices/lab_pin.sym} 2000 -560 0 0 {name=l65 sig_type=std_logic lab=glb}
C {devices/lab_pin.sym} 2080 -490 0 0 {name=l66 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2120 -560 0 1 {name=l67 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -100 0 0 {name=VBOT value="PWL(0 \{VIN\} \{TCONN\} \{VIN\} \{TCONN+TEDGE\} \{VR_LO\} \{TR\} \{VR_LO\} \{TR+14u\} \{VEND\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -170 0 0 {name=l68 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 120 -30 0 0 {name=l69 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 140 0 0 {name=VS2 value="PWL(0 1 \{TS\} 1 \{TS+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 70 0 0 {name=l70 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 120 210 0 0 {name=l71 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 760 -100 0 0 {name=S2 model=swideal}
C {devices/lab_pin.sym} 760 -170 0 0 {name=l72 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 760 -30 0 0 {name=l73 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 680 -100 0 0 {name=l74 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 680 -80 0 0 {name=l75 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 920 140 0 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 920 70 0 0 {name=l76 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 920 210 0 0 {name=l77 sig_type=std_logic lab=bot}
C {devices/res.sym} 1080 -100 0 0 {name=RLKT value=1e15 m=1}
C {devices/lab_pin.sym} 1080 -170 0 0 {name=l78 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1080 -30 0 0 {name=l79 sig_type=std_logic lab=0}
C {comparator.sym} 1380 -100 0 0 {name=XDUT}
C {devices/lab_pin.sym} 1240 -160 0 0 {name=l80 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1240 -130 0 0 {name=l81 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1240 -100 0 0 {name=l82 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1240 -70 0 0 {name=l83 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1240 -40 0 0 {name=l84 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1520 -145 0 1 {name=l85 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1380 -260 0 0 {name=l86 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1380 60 0 0 {name=l87 sig_type=std_logic lab=0}
C {devices/capa.sym} 1620 -100 0 0 {name=CLOAD value=1e-14 m=1}
C {devices/lab_pin.sym} 1620 -170 0 0 {name=l88 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1620 -30 0 0 {name=l89 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 2200 -1200 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
.param VDD=3.3
.temp 27
.param IREF=0
.param VIN=0.737304688
.param VR_LO=0.5
.param LSB=0.005859375
.param TCOUNT=50n
.param SLOPE='LSB/TCOUNT'
.param TS=300n
.param TCONN=310n
.param TR=400n
.param TEDGE=100p
.param VEND='VR_LO+14u*SLOPE'
.csparam cs_vdd=\{VDD\}
.csparam cs_tr=\{TR\}
.csparam cs_tconn=\{TCONN\}
.csparam cs_tideal=\{TR+(VIN-VR_LO)/SLOPE\}
.options savecurrents reltol=1e-4 gmin=1e-15
.control
set num_threads=1
* static trip (tb_sel_dc): inn swept through inp = VBL
dc VDC 1.6 1.7 25u
meas dc vtrip when v(doutdc)=1.65 fall=1
let vtr6 = floor(vtrip * 1e6 + 0.5) / 1e6
set numdgt=10
set vtrip_s = $&vtr6
* charge path (tb_sel), plateau level: delay from the trip crossing
set wr_singlescale
tran 0.25n 2.825e-06 0 0.5n
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_cross when v(top)=1.65 rise=1 td=$&cs_tr
meas tran t_cs when v(top)=$vtrip_s rise=1 td=$&cs_tr
meas tran t_dout when v(dout)=$&half fall=1 td=$&cs_tr
meas tran t_f90 when v(dout)=$&hi90 fall=1 td=$&cs_tr
meas tran t_f10 when v(dout)=$&lo10 fall=1 td=$&cs_tr
meas tran armed find v(dout) at=$&cs_tr
let t_after = t_dout + 5e-9
meas tran t_rerise when v(dout)=$&half rise=1 td=$&t_after
meas tran i_avg avg i(vdd_source) from=$&cs_tconn to=$&t_cross
let delay_vbl = t_dout - t_cross
let delay_dyn = t_dout - t_cs
let fall = t_f10 - t_f90
let ped_counts = (t_dout - $&cs_tideal) / 50e-9
let p_avg = -$&cs_vdd * i_avg
echo RESULT_BEGIN
echo vtrip_v = $vtrip_s
print delay_vbl delay_dyn fall ped_counts armed p_avg
echo RESULT_END
quit
.endc"}
