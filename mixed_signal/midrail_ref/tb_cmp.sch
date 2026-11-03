v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1160 120 -1200 {}
N 120 -1100 120 -1060 {}
N 290 -1160 290 -1200 {}
N 290 -1100 290 -1060 {}
N 460 -1160 460 -1200 {}
N 460 -1100 460 -1060 {}
N 630 -1160 630 -1200 {}
N 630 -1100 630 -1060 {}
N 800 -1160 800 -1200 {}
N 800 -1100 800 -1060 {}
N 970 -1160 970 -1200 {}
N 970 -1100 970 -1060 {}
N 1140 -1160 1140 -1200 {}
N 1140 -1100 1140 -1060 {}
N 1310 -1160 1310 -1200 {}
N 1310 -1100 1310 -1060 {}
N 120 -910 120 -950 {}
N 120 -850 120 -810 {}
N 300 -880 260 -880 {}
N 340 -910 340 -950 {}
N 340 -850 340 -810 {}
N 340 -880 450 -880 {}
N 560 -910 560 -950 {}
N 560 -850 560 -810 {}
N 740 -880 700 -880 {}
N 780 -850 780 -810 {}
N 780 -910 780 -950 {}
N 780 -880 890 -880 {}
N 120 -650 120 -690 {}
N 120 -590 120 -550 {}
N 120 -480 120 -520 {}
N 120 -420 120 -380 {}
N 120 -310 120 -350 {}
N 120 -250 120 -210 {}
N 120 -140 120 -180 {}
N 120 -80 120 -40 {}
N 120 30 120 -10 {}
N 120 90 120 130 {}
N 1680 -1100 1720 -1100 {}
N 1600 -1160 1600 -1200 {}
N 1600 -1040 1600 -1000 {}
N 2160 -1100 2200 -1100 {}
N 2000 -1100 1870 -1100 {}
N 2000 -1080 1960 -1080 {}
N 2080 -1160 2080 -1200 {}
N 2080 -1040 2080 -1000 {}
N 2450 -1190 2450 -1230 {}
N 2450 -1130 2450 -1090 {}
N 2410 -1160 2370 -1160 {}
N 2410 -1140 2370 -1140 {}
N 2450 -990 2450 -1030 {}
N 2450 -930 2450 -890 {}
N 2410 -960 2370 -960 {}
N 2410 -940 2370 -940 {}
N 1600 -730 1600 -770 {}
N 1600 -670 1600 -630 {}
N 1560 -700 1520 -700 {}
N 1560 -680 1520 -680 {}
N 1850 -680 1850 -720 {}
N 1850 -620 1850 -580 {}
N 2150 -680 2150 -720 {}
N 2150 -620 2150 -580 {}
N 2400 -660 2360 -660 {}
N 2400 -630 2360 -630 {}
N 2400 -600 2360 -600 {}
N 2400 -570 2360 -570 {}
N 2400 -540 2360 -540 {}
N 2600 -645 2640 -645 {}
N 2500 -720 2500 -760 {}
N 2500 -480 2500 -440 {}
N 2750 -630 2750 -670 {}
N 2750 -570 2750 -530 {}
N 1600 -310 1600 -350 {}
N 1600 -250 1600 -210 {}
N 1560 -280 1520 -280 {}
N 1560 -260 1520 -260 {}
N 1600 -90 1600 -130 {}
N 1600 -30 1600 10 {}
N 1560 -60 1520 -60 {}
N 1560 -40 1520 -40 {}
N 1850 -230 1850 -270 {}
N 1850 -170 1850 -130 {}
N 2150 -230 2150 -270 {}
N 2150 -170 2150 -130 {}
N 2400 -230 2400 -270 {}
N 2400 -170 2400 -130 {}
N 2650 -230 2650 -270 {}
N 2650 -170 2650 -130 {}
T {TB_CMP  -  the one output as S2 level and comparator threshold through one decision} 60 -1330 0 0 0.7 0.7 {}
T {SUPPLY + BIAS} 60 -1260 0 0 0.4 0.4 {}
T {I_B = 12.36 uA} 250 -1010 0 0 0.3 0.3 {layer=4}
T {CONTROLS} 60 -740 0 0 0.4 0.4 {}
T {DUT + NODE SELECT} 1500 -1260 0 0 0.4 0.4 {}
T {CELL + COMPARATOR} 1500 -820 0 0 0.4 0.4 {}
T {C_S 54.52 fF} 1890 -550 0 0 0.3 0.3 {layer=4}
T {NEIGHBOUR: S2 closes at TK (agg 0: never)} 1500 -400 0 0 0.4 0.4 {}
C {devices/vsource.sym} 120 -1130 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1200 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1060 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/isource.sym} 290 -1130 0 0 {name=IREF value="\{IF\}"}
C {devices/lab_pin.sym} 290 -1200 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 290 -1060 0 0 {name=l4 sig_type=std_logic lab=ib}
C {devices/vsource.sym} 460 -1130 0 0 {name=VDD_BIAS value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -1200 0 0 {name=l5 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 460 -1060 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1130 0 0 {name=VCLK value="0" savecurrent=false}
C {devices/lab_pin.sym} 630 -1200 0 0 {name=l7 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 630 -1060 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 800 -1130 0 0 {name=VCB value="2" savecurrent=false}
C {devices/lab_pin.sym} 800 -1200 0 0 {name=l9 sig_type=std_logic lab=cb}
C {devices/lab_pin.sym} 800 -1060 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/vsource.sym} 970 -1130 0 0 {name=VCI value="0" savecurrent=false}
C {devices/lab_pin.sym} 970 -1200 0 0 {name=l11 sig_type=std_logic lab=ci}
C {devices/lab_pin.sym} 970 -1060 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1140 -1130 0 0 {name=VREFI value="1.65" savecurrent=false}
C {devices/lab_pin.sym} 1140 -1200 0 0 {name=l13 sig_type=std_logic lab=vrefi}
C {devices/lab_pin.sym} 1140 -1060 0 0 {name=l14 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1310 -1130 0 0 {name=VTOPA0 value="\{TOPA0\}" savecurrent=false}
C {devices/lab_pin.sym} 1310 -1200 0 0 {name=l15 sig_type=std_logic lab=vtopa0}
C {devices/lab_pin.sym} 1310 -1060 0 0 {name=l16 sig_type=std_logic lab=0}
C {devices/isource.sym} 120 -880 0 0 {name=IREFN value="\{IREFC\}"}
C {devices/lab_pin.sym} 120 -950 0 0 {name=l17 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 120 -810 0 0 {name=l18 sig_type=std_logic lab=nbias}
C {symbols/nfet_03v3.sym} 320 -880 0 0 {name=XREFN
L=1u W=20u nf=10 m=1
model=nfet_03v3 spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 260 -880 0 0 {name=l19 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -950 0 0 {name=l20 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -810 0 0 {name=l21 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 450 -880 0 1 {name=l22 sig_type=std_logic lab=0}
C {devices/isource.sym} 560 -880 0 0 {name=IREFP value="\{IREFC\}"}
C {devices/lab_pin.sym} 560 -950 0 0 {name=l23 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 560 -810 0 0 {name=l24 sig_type=std_logic lab=0}
C {symbols/pfet_03v3.sym} 760 -880 0 0 {name=XREFP
L=0.28u W=1u nf=1 m=1
model=pfet_03v3 spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 700 -880 0 0 {name=l25 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 780 -810 0 0 {name=l26 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 780 -950 0 0 {name=l27 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 890 -880 0 1 {name=l28 sig_type=std_logic lab=vddb}
C {devices/vsource.sym} 120 -620 0 0 {name=VS2 value="PWL(0 \{VDD\} \{TS\} \{VDD\} \{TS+0.1n\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 -690 0 0 {name=l29 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 120 -550 0 0 {name=l30 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -450 0 0 {name=VBOT value="PWL(0 \{VDD/2\} \{TDROP\} \{VDD/2\} \{TDROP+0.1n\} \{VDD/2-VDROP\} \{TR\} \{VDD/2-VDROP\} \{TSTOP\} \{VDD/2-VDROP+SLOPE*(TSTOP-TR)\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -520 0 0 {name=l31 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 120 -380 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -280 0 0 {name=VSPREA value="PWL(0 2 \{TK-5n\} 2 \{TK-4n\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 -350 0 0 {name=l33 sig_type=std_logic lab=sprea}
C {devices/lab_pin.sym} 120 -210 0 0 {name=l34 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -110 0 0 {name=VS2A value="PWL(0 0 \{TK\} 0 \{TK+0.1n\} \{2*AGGON\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -180 0 0 {name=l35 sig_type=std_logic lab=s2a}
C {devices/lab_pin.sym} 120 -40 0 0 {name=l36 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 60 0 0 {name=VBOTA value="PWL(0 \{VBOT0\} \{TK\} \{VBOT0\} \{TK+0.1n\} \{VFEA1\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -10 0 0 {name=l37 sig_type=std_logic lab=botsa}
C {devices/lab_pin.sym} 120 130 0 0 {name=l38 sig_type=std_logic lab=0}
C {midref_div.sym} 1600 -1100 0 0 {name=XD}
C {devices/lab_pin.sym} 1720 -1100 0 1 {name=l39 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1600 -1200 0 0 {name=l40 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1600 -1000 0 0 {name=l41 sig_type=std_logic lab=0}
C {midref_buf.sym} 2080 -1100 0 0 {name=XB}
C {devices/lab_pin.sym} 2200 -1100 0 1 {name=l42 sig_type=std_logic lab=vrefb}
C {devices/lab_pin.sym} 1870 -1100 0 0 {name=l43 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1960 -1080 0 0 {name=l44 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 2080 -1200 0 0 {name=l45 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2080 -1000 0 0 {name=l46 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 2450 -1160 0 0 {name=SWB model=swsel}
C {devices/lab_pin.sym} 2450 -1230 0 0 {name=l47 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2450 -1090 0 0 {name=l48 sig_type=std_logic lab=vrefb}
C {devices/lab_pin.sym} 2370 -1160 0 0 {name=l49 sig_type=std_logic lab=cb}
C {devices/lab_pin.sym} 2370 -1140 0 0 {name=l50 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 2450 -960 0 0 {name=SWI model=swsel}
C {devices/lab_pin.sym} 2450 -1030 0 0 {name=l51 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2450 -890 0 0 {name=l52 sig_type=std_logic lab=vrefi}
C {devices/lab_pin.sym} 2370 -960 0 0 {name=l53 sig_type=std_logic lab=ci}
C {devices/lab_pin.sym} 2370 -940 0 0 {name=l54 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1600 -700 0 0 {name=S2 model=sws2}
C {devices/lab_pin.sym} 1600 -770 0 0 {name=l55 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1600 -630 0 0 {name=l56 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1520 -700 0 0 {name=l57 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1520 -680 0 0 {name=l58 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 1850 -650 0 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 1850 -720 0 0 {name=l59 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1850 -580 0 0 {name=l60 sig_type=std_logic lab=bot}
C {devices/res.sym} 2150 -650 0 0 {name=RLKT value="1e15" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 2150 -720 0 0 {name=l61 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 2150 -580 0 0 {name=l62 sig_type=std_logic lab=0}
C {comparator.sym} 2500 -600 0 0 {name=XCMP}
C {devices/lab_pin.sym} 2360 -660 0 0 {name=l63 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2360 -630 0 0 {name=l64 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 2360 -600 0 0 {name=l65 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2360 -570 0 0 {name=l66 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 2360 -540 0 0 {name=l67 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 2640 -645 0 1 {name=l68 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 2500 -760 0 0 {name=l69 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2500 -440 0 0 {name=l70 sig_type=std_logic lab=0}
C {devices/capa.sym} 2750 -600 0 0 {name=CLOAD value="10f" m=1}
C {devices/lab_pin.sym} 2750 -670 0 0 {name=l71 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 2750 -530 0 0 {name=l72 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1600 -280 0 0 {name=SPREA model=swpre}
C {devices/lab_pin.sym} 1600 -350 0 0 {name=l73 sig_type=std_logic lab=topa}
C {devices/lab_pin.sym} 1600 -210 0 0 {name=l74 sig_type=std_logic lab=vtopa0}
C {devices/lab_pin.sym} 1520 -280 0 0 {name=l75 sig_type=std_logic lab=sprea}
C {devices/lab_pin.sym} 1520 -260 0 0 {name=l76 sig_type=std_logic lab=0}
C {devices/switch_ngspice.sym} 1600 -60 0 0 {name=S2A model=sws2a}
C {devices/lab_pin.sym} 1600 -130 0 0 {name=l77 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1600 10 0 0 {name=l78 sig_type=std_logic lab=topa}
C {devices/lab_pin.sym} 1520 -60 0 0 {name=l79 sig_type=std_logic lab=s2a}
C {devices/lab_pin.sym} 1520 -40 0 0 {name=l80 sig_type=std_logic lab=0}
C {symbols/cap_mim_2f0fF.sym} 1850 -200 0 0 {name=XCSA W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 1850 -270 0 0 {name=l81 sig_type=std_logic lab=topa}
C {devices/lab_pin.sym} 1850 -130 0 0 {name=l82 sig_type=std_logic lab=bota}
C {devices/capa.sym} 2150 -200 0 0 {name=CTOPPA value="\{CTOP\}" m=1}
C {devices/lab_pin.sym} 2150 -270 0 0 {name=l83 sig_type=std_logic lab=topa}
C {devices/lab_pin.sym} 2150 -130 0 0 {name=l84 sig_type=std_logic lab=0}
C {devices/res.sym} 2400 -200 0 0 {name=RLKTA value="1e15" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 2400 -270 0 0 {name=l85 sig_type=std_logic lab=topa}
C {devices/lab_pin.sym} 2400 -130 0 0 {name=l86 sig_type=std_logic lab=0}
C {devices/res.sym} 2650 -200 0 0 {name=RS0A value="\{RS0\}" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 2650 -270 0 0 {name=l87 sig_type=std_logic lab=botsa}
C {devices/lab_pin.sym} 2650 -130 0 0 {name=l88 sig_type=std_logic lab=bota}
C {devices/code_shown.sym} 3000 -1330 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/designs/mixed_signal/comparator/comparator.spice
.temp 27
.param IF=1.23557e-05
.param VDD=3.3
.param CS_W=5u
.param CS_L=5u
.param TCOUNT=50n
.param SLOPE=117187.5
.param TS=0.5u
.param TDROP=0.51u
.param VDROP=0.15
.param TK=0.55u
.param TR=0.85u
.param TSTOP=2.6u
.param RS2=1k
.param IREFC=1.931u
.param CTOP=17.12f
.param RS0=100
.param VBOT0=2.117
.param AGGON=0
.param TOPA0=2.9900
.param VFEA1=2
.options savecurrents reltol=1e-4 gmin=1e-15
.model swsel sw vt=1 vh=0 ron=1 roff=1e14
.model sws2 sw vt=\{VDD/2\} vh=0.05 ron=\{RS2\} roff=1e14
.model swpre sw vt=1 vh=0.1 ron=100 roff=1e14
.model sws2a sw vt=1 vh=0.1 ron=\{RS2\} roff=1e14
.control
set num_threads=1
tran 0.1n 2.6u 0 1n
meas tran v0 avg v(vref) from=0.3u to=0.45u
meas tran td when v(dout)=1.65 fall=1 from=0.85u
let dev = abs(v(vref) - v0)
let tpre = td - 200n
meas tran pkpre max dev from=$&tpre to=$&td
meas tran pkall max dev from=0.5u to=2.6u
meas tran pkhold max dev from=0.54u to=0.85u
meas tran doutmin min v(dout) from=0.54u to=0.85u
let cmp_v0_v = v0
let cmp_td_ns = td * 1e9
let cmp_pkpre_uv = pkpre * 1e6
let cmp_pkall_uv = pkall * 1e6
let cmp_pkhold_mv = pkhold * 1e3
let cmp_doutmin_v = doutmin
print cmp_v0_v
print cmp_td_ns
print cmp_pkpre_uv
print cmp_pkall_uv
print cmp_pkhold_mv
print cmp_doutmin_v
quit
.endc"}
