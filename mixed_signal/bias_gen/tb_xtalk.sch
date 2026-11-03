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
N 300 -920 300 -960 {}
N 300 -680 300 -640 {}
N 400 -880 520 -880 {}
N 400 -855 460 -855 {}
N 400 -830 520 -830 {}
N 400 -805 460 -805 {}
N 400 -780 520 -780 {}
N 400 -755 460 -755 {}
N 400 -730 520 -730 {}
N 780 -810 780 -770 {}
N 740 -840 700 -840 {}
N 780 -870 780 -910 {}
N 780 -840 820 -840 {}
N 1040 -810 1040 -770 {}
N 1000 -840 960 -840 {}
N 1040 -870 1040 -910 {}
N 1040 -840 1080 -840 {}
N 1300 -810 1300 -770 {}
N 1260 -840 1220 -840 {}
N 1300 -870 1300 -910 {}
N 1300 -840 1340 -840 {}
N 1560 -810 1560 -770 {}
N 1520 -840 1480 -840 {}
N 1560 -870 1560 -910 {}
N 1560 -840 1600 -840 {}
N 1820 -810 1820 -770 {}
N 1780 -840 1740 -840 {}
N 1820 -870 1820 -910 {}
N 1820 -840 1860 -840 {}
N 2080 -870 2080 -910 {}
N 2040 -840 2000 -840 {}
N 2080 -810 2080 -770 {}
N 2080 -840 2120 -840 {}
N 2340 -870 2340 -910 {}
N 2300 -840 2260 -840 {}
N 2340 -810 2340 -770 {}
N 2340 -840 2380 -840 {}
N 120 -430 120 -470 {}
N 120 -370 120 -330 {}
N 760 -430 760 -470 {}
N 760 -370 760 -330 {}
N 720 -400 680 -400 {}
N 720 -380 680 -380 {}
N 920 -430 920 -470 {}
N 920 -370 920 -330 {}
N 1180 -430 1180 -470 {}
N 1180 -370 1180 -330 {}
N 1380 -460 1340 -460 {}
N 1380 -430 1340 -430 {}
N 1380 -400 1340 -400 {}
N 1380 -370 1340 -370 {}
N 1380 -340 1340 -340 {}
N 1580 -445 1620 -445 {}
N 1480 -520 1480 -560 {}
N 1480 -280 1480 -240 {}
N 1720 -430 1720 -470 {}
N 1720 -370 1720 -330 {}
N 120 -30 120 -70 {}
N 120 30 120 70 {}
N 760 -30 760 -70 {}
N 760 30 760 70 {}
N 720 0 680 0 {}
N 720 20 680 20 {}
N 920 -30 920 -70 {}
N 920 30 920 70 {}
N 1180 -30 1180 -70 {}
N 1180 30 1180 70 {}
N 1380 -60 1340 -60 {}
N 1380 -30 1340 -30 {}
N 1380 0 1340 0 {}
N 1380 30 1340 30 {}
N 1380 60 1340 60 {}
N 1580 -45 1620 -45 {}
N 1480 -120 1480 -160 {}
N 1480 120 1480 160 {}
N 1720 -30 1720 -70 {}
N 1720 30 1720 70 {}
N 120 370 120 330 {}
N 120 430 120 470 {}
N 760 370 760 330 {}
N 760 430 760 470 {}
N 720 400 680 400 {}
N 720 420 680 420 {}
N 920 370 920 330 {}
N 920 430 920 470 {}
N 1180 370 1180 330 {}
N 1180 430 1180 470 {}
N 1380 340 1340 340 {}
N 1380 370 1340 370 {}
N 1380 400 1340 400 {}
N 1380 430 1340 430 {}
N 1380 460 1340 460 {}
N 1580 355 1620 355 {}
N 1480 280 1480 240 {}
N 1480 520 1480 560 {}
N 1720 370 1720 330 {}
N 1720 430 1720 470 {}
N 120 770 120 730 {}
N 120 830 120 870 {}
N 760 770 760 730 {}
N 760 830 760 870 {}
N 720 800 680 800 {}
N 720 820 680 820 {}
N 920 770 920 730 {}
N 920 830 920 870 {}
N 1180 770 1180 730 {}
N 1180 830 1180 870 {}
N 1380 740 1340 740 {}
N 1380 770 1340 770 {}
N 1380 800 1340 800 {}
N 1380 830 1340 830 {}
N 1380 860 1340 860 {}
N 1580 755 1620 755 {}
N 1480 680 1480 640 {}
N 1480 920 1480 960 {}
N 1720 770 1720 730 {}
N 1720 830 1720 870 {}
T {TB_XTALK  -  four comparators on bias_gen, aggressors 1..3 decide one LSB before the victim} 40 -1340 0 0 0.7 0.7 {}
T {GENERATOR, pb0..3 = the comparators' pbias diodes} 60 -1020 0 0 0.4 0.4 {}
T {victim 40.5 LSB, aggressors 39.5 LSB (quiet: 300 LSB)} 60 -620 0 0 0.3 0.3 {layer=4}
T {CELLS 0 (VICTIM) .. 3} 60 -560 0 0 0.4 0.4 {}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -1180 0 0 {name=VVBL value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -1250 0 0 {name=l3 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 290 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 460 -1180 0 0 {name=VVREF value="\{VDD/2\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -1250 0 0 {name=l5 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 460 -1110 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1180 0 0 {name=VCLK value="0" savecurrent=false}
C {devices/lab_pin.sym} 630 -1250 0 0 {name=l7 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 630 -1110 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 800 -1180 0 0 {name=VS2 value="PWL(0 1 300n 1 300.1n 0)" savecurrent=false}
C {devices/lab_pin.sym} 800 -1250 0 0 {name=l9 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 800 -1110 0 0 {name=l10 sig_type=std_logic lab=0}
C {bias_gen.sym} 300 -800 0 0 {name=XG}
C {devices/lab_pin.sym} 300 -960 0 0 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 300 -640 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 520 -880 0 1 {name=l13 sig_type=std_logic lab=pb0}
C {devices/lab_pin.sym} 460 -855 0 1 {name=l14 sig_type=std_logic lab=pb1}
C {devices/lab_pin.sym} 520 -830 0 1 {name=l15 sig_type=std_logic lab=pb2}
C {devices/lab_pin.sym} 460 -805 0 1 {name=l16 sig_type=std_logic lab=pb3}
C {devices/lab_pin.sym} 520 -780 0 1 {name=l17 sig_type=std_logic lab=glr}
C {devices/lab_pin.sym} 460 -755 0 1 {name=l18 sig_type=std_logic lab=glv}
C {devices/lab_pin.sym} 520 -730 0 1 {name=l19 sig_type=std_logic lab=glb}
C {symbols/pfet_03v3.sym} 760 -840 0 0 {name=XRP0
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
C {devices/lab_pin.sym} 780 -770 0 0 {name=l20 sig_type=std_logic lab=pb0}
C {devices/lab_pin.sym} 700 -840 0 0 {name=l21 sig_type=std_logic lab=pb0}
C {devices/lab_pin.sym} 780 -910 0 0 {name=l22 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 820 -840 0 1 {name=l23 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 1020 -840 0 0 {name=XRP1
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
C {devices/lab_pin.sym} 1040 -770 0 0 {name=l24 sig_type=std_logic lab=pb1}
C {devices/lab_pin.sym} 960 -840 0 0 {name=l25 sig_type=std_logic lab=pb1}
C {devices/lab_pin.sym} 1040 -910 0 0 {name=l26 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1080 -840 0 1 {name=l27 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 1280 -840 0 0 {name=XRP2
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
C {devices/lab_pin.sym} 1300 -770 0 0 {name=l28 sig_type=std_logic lab=pb2}
C {devices/lab_pin.sym} 1220 -840 0 0 {name=l29 sig_type=std_logic lab=pb2}
C {devices/lab_pin.sym} 1300 -910 0 0 {name=l30 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1340 -840 0 1 {name=l31 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 1540 -840 0 0 {name=XRP3
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
C {devices/lab_pin.sym} 1560 -770 0 0 {name=l32 sig_type=std_logic lab=pb3}
C {devices/lab_pin.sym} 1480 -840 0 0 {name=l33 sig_type=std_logic lab=pb3}
C {devices/lab_pin.sym} 1560 -910 0 0 {name=l34 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1600 -840 0 1 {name=l35 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 1800 -840 0 0 {name=XGDR
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
C {devices/lab_pin.sym} 1820 -770 0 0 {name=l36 sig_type=std_logic lab=glr}
C {devices/lab_pin.sym} 1740 -840 0 0 {name=l37 sig_type=std_logic lab=glr}
C {devices/lab_pin.sym} 1820 -910 0 0 {name=l38 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1860 -840 0 1 {name=l39 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 2060 -840 0 0 {name=XGDV
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
C {devices/lab_pin.sym} 2080 -910 0 0 {name=l40 sig_type=std_logic lab=glv}
C {devices/lab_pin.sym} 2000 -840 0 0 {name=l41 sig_type=std_logic lab=glv}
C {devices/lab_pin.sym} 2080 -770 0 0 {name=l42 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2120 -840 0 1 {name=l43 sig_type=std_logic lab=0}
C {symbols/nfet_03v3.sym} 2320 -840 0 0 {name=XGDB
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
C {devices/lab_pin.sym} 2340 -910 0 0 {name=l44 sig_type=std_logic lab=glb}
C {devices/lab_pin.sym} 2260 -840 0 0 {name=l45 sig_type=std_logic lab=glb}
C {devices/lab_pin.sym} 2340 -770 0 0 {name=l46 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2380 -840 0 1 {name=l47 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -400 0 0 {name=VBOT0 value="PWL(0 \{VVIC\} 310n \{VVIC\} 310.1n 0.5 400n 0.5 14.4u \{VEND\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -470 0 0 {name=l48 sig_type=std_logic lab=bot0}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l49 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 760 -400 0 0 {name=S2_0 model=swideal}
C {devices/lab_pin.sym} 760 -470 0 0 {name=l50 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 760 -330 0 0 {name=l51 sig_type=std_logic lab=top0}
C {devices/lab_pin.sym} 680 -400 0 0 {name=l52 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 680 -380 0 0 {name=l53 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 920 -400 0 0 {name=XCS0 W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 920 -470 0 0 {name=l54 sig_type=std_logic lab=top0}
C {devices/lab_pin.sym} 920 -330 0 0 {name=l55 sig_type=std_logic lab=bot0}
C {devices/res.sym} 1180 -400 0 0 {name=RLK0 value=1e15 m=1}
C {devices/lab_pin.sym} 1180 -470 0 0 {name=l56 sig_type=std_logic lab=top0}
C {devices/lab_pin.sym} 1180 -330 0 0 {name=l57 sig_type=std_logic lab=0}
C {comparator.sym} 1480 -400 0 0 {name=XDUT0}
C {devices/lab_pin.sym} 1340 -460 0 0 {name=l58 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1340 -430 0 0 {name=l59 sig_type=std_logic lab=top0}
C {devices/lab_pin.sym} 1340 -400 0 0 {name=l60 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1340 -370 0 0 {name=l61 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1340 -340 0 0 {name=l62 sig_type=std_logic lab=pb0}
C {devices/lab_pin.sym} 1620 -445 0 1 {name=l63 sig_type=std_logic lab=dout0}
C {devices/lab_pin.sym} 1480 -560 0 0 {name=l64 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 -240 0 0 {name=l65 sig_type=std_logic lab=0}
C {devices/capa.sym} 1720 -400 0 0 {name=CL0 value=10f m=1}
C {devices/lab_pin.sym} 1720 -470 0 0 {name=l66 sig_type=std_logic lab=dout0}
C {devices/lab_pin.sym} 1720 -330 0 0 {name=l67 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 0 0 0 {name=VBOT1 value="PWL(0 \{VAGG\} 310n \{VAGG\} 310.1n 0.5 400n 0.5 14.4u \{VEND\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -70 0 0 {name=l68 sig_type=std_logic lab=bot1}
C {devices/lab_pin.sym} 120 70 0 0 {name=l69 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 760 0 0 0 {name=S2_1 model=swideal}
C {devices/lab_pin.sym} 760 -70 0 0 {name=l70 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 760 70 0 0 {name=l71 sig_type=std_logic lab=top1}
C {devices/lab_pin.sym} 680 0 0 0 {name=l72 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 680 20 0 0 {name=l73 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 920 0 0 0 {name=XCS1 W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 920 -70 0 0 {name=l74 sig_type=std_logic lab=top1}
C {devices/lab_pin.sym} 920 70 0 0 {name=l75 sig_type=std_logic lab=bot1}
C {devices/res.sym} 1180 0 0 0 {name=RLK1 value=1e15 m=1}
C {devices/lab_pin.sym} 1180 -70 0 0 {name=l76 sig_type=std_logic lab=top1}
C {devices/lab_pin.sym} 1180 70 0 0 {name=l77 sig_type=std_logic lab=0}
C {comparator.sym} 1480 0 0 0 {name=XDUT1}
C {devices/lab_pin.sym} 1340 -60 0 0 {name=l78 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1340 -30 0 0 {name=l79 sig_type=std_logic lab=top1}
C {devices/lab_pin.sym} 1340 0 0 0 {name=l80 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1340 30 0 0 {name=l81 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1340 60 0 0 {name=l82 sig_type=std_logic lab=pb1}
C {devices/lab_pin.sym} 1620 -45 0 1 {name=l83 sig_type=std_logic lab=dout1}
C {devices/lab_pin.sym} 1480 -160 0 0 {name=l84 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 160 0 0 {name=l85 sig_type=std_logic lab=0}
C {devices/capa.sym} 1720 0 0 0 {name=CL1 value=10f m=1}
C {devices/lab_pin.sym} 1720 -70 0 0 {name=l86 sig_type=std_logic lab=dout1}
C {devices/lab_pin.sym} 1720 70 0 0 {name=l87 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 400 0 0 {name=VBOT2 value="PWL(0 \{VAGG\} 310n \{VAGG\} 310.1n 0.5 400n 0.5 14.4u \{VEND\})" savecurrent=false}
C {devices/lab_pin.sym} 120 330 0 0 {name=l88 sig_type=std_logic lab=bot2}
C {devices/lab_pin.sym} 120 470 0 0 {name=l89 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 760 400 0 0 {name=S2_2 model=swideal}
C {devices/lab_pin.sym} 760 330 0 0 {name=l90 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 760 470 0 0 {name=l91 sig_type=std_logic lab=top2}
C {devices/lab_pin.sym} 680 400 0 0 {name=l92 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 680 420 0 0 {name=l93 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 920 400 0 0 {name=XCS2 W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 920 330 0 0 {name=l94 sig_type=std_logic lab=top2}
C {devices/lab_pin.sym} 920 470 0 0 {name=l95 sig_type=std_logic lab=bot2}
C {devices/res.sym} 1180 400 0 0 {name=RLK2 value=1e15 m=1}
C {devices/lab_pin.sym} 1180 330 0 0 {name=l96 sig_type=std_logic lab=top2}
C {devices/lab_pin.sym} 1180 470 0 0 {name=l97 sig_type=std_logic lab=0}
C {comparator.sym} 1480 400 0 0 {name=XDUT2}
C {devices/lab_pin.sym} 1340 340 0 0 {name=l98 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1340 370 0 0 {name=l99 sig_type=std_logic lab=top2}
C {devices/lab_pin.sym} 1340 400 0 0 {name=l100 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1340 430 0 0 {name=l101 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1340 460 0 0 {name=l102 sig_type=std_logic lab=pb2}
C {devices/lab_pin.sym} 1620 355 0 1 {name=l103 sig_type=std_logic lab=dout2}
C {devices/lab_pin.sym} 1480 240 0 0 {name=l104 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 560 0 0 {name=l105 sig_type=std_logic lab=0}
C {devices/capa.sym} 1720 400 0 0 {name=CL2 value=10f m=1}
C {devices/lab_pin.sym} 1720 330 0 0 {name=l106 sig_type=std_logic lab=dout2}
C {devices/lab_pin.sym} 1720 470 0 0 {name=l107 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 800 0 0 {name=VBOT3 value="PWL(0 \{VAGG\} 310n \{VAGG\} 310.1n 0.5 400n 0.5 14.4u \{VEND\})" savecurrent=false}
C {devices/lab_pin.sym} 120 730 0 0 {name=l108 sig_type=std_logic lab=bot3}
C {devices/lab_pin.sym} 120 870 0 0 {name=l109 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 760 800 0 0 {name=S2_3 model=swideal}
C {devices/lab_pin.sym} 760 730 0 0 {name=l110 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 760 870 0 0 {name=l111 sig_type=std_logic lab=top3}
C {devices/lab_pin.sym} 680 800 0 0 {name=l112 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 680 820 0 0 {name=l113 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 920 800 0 0 {name=XCS3 W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 920 730 0 0 {name=l114 sig_type=std_logic lab=top3}
C {devices/lab_pin.sym} 920 870 0 0 {name=l115 sig_type=std_logic lab=bot3}
C {devices/res.sym} 1180 800 0 0 {name=RLK3 value=1e15 m=1}
C {devices/lab_pin.sym} 1180 730 0 0 {name=l116 sig_type=std_logic lab=top3}
C {devices/lab_pin.sym} 1180 870 0 0 {name=l117 sig_type=std_logic lab=0}
C {comparator.sym} 1480 800 0 0 {name=XDUT3}
C {devices/lab_pin.sym} 1340 740 0 0 {name=l118 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1340 770 0 0 {name=l119 sig_type=std_logic lab=top3}
C {devices/lab_pin.sym} 1340 800 0 0 {name=l120 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1340 830 0 0 {name=l121 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1340 860 0 0 {name=l122 sig_type=std_logic lab=pb3}
C {devices/lab_pin.sym} 1620 755 0 1 {name=l123 sig_type=std_logic lab=dout3}
C {devices/lab_pin.sym} 1480 640 0 0 {name=l124 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 960 0 0 {name=l125 sig_type=std_logic lab=0}
C {devices/capa.sym} 1720 800 0 0 {name=CL3 value=10f m=1}
C {devices/lab_pin.sym} 1720 730 0 0 {name=l126 sig_type=std_logic lab=dout3}
C {devices/lab_pin.sym} 1720 870 0 0 {name=l127 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 2460 -1200 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27
.param VDD=3.3
.param LSB=0.005859375
.param SLOPE='LSB/50n'
.param VVIC=0.737305
.param VAGG=0.731445
.param VEND=2.140625
.options savecurrents reltol=1e-4 gmin=1e-15
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
.control
set num_threads=1
* case a: aggressors one LSB below the victim
tran 0.25n 2.625e-06 0 0.5n
let half = 3.3 / 2
meas tran t0 when v(dout0)=$&half fall=1 td=400n
meas tran pbx max v(pb0) from=400n to=2.625e-06
meas tran pbn min v(pb0) from=400n to=2.625e-06
echo XT $&t0 $&pbx $&pbn
* case q: aggressors quiet (input above the ramp's end)
alterparam VAGG=2.257812
reset
tran 0.25n 2.625e-06 0 0.5n
let half = 3.3 / 2
meas tran t0 when v(dout0)=$&half fall=1 td=400n
meas tran pbx max v(pb0) from=400n to=2.625e-06
meas tran pbn min v(pb0) from=400n to=2.625e-06
echo XT $&t0 $&pbx $&pbn
quit
.endc"}
