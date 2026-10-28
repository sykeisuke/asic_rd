v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {tb_ramp_simple_adc4 -- the shared ramp generator (ramp_simple) driving four 8-bit true bottom-plate unit cells (cell_bps: S0/S1/S2, 54.52 fF MIM, cmp_bps)
on the shared bias generator and the two FVF VDD/2 buffers. Every cell samples its own DC level vin_i at TS, connects its bottom plate to vr_cell at TCONN and converts:
dout_i falls when the ramp passes vin_i; code_i = floor((t_dout_i - TR) / TCOUNT) against floor((vin_i - 0.5 V) / LSB), LSB = 1.5 V / 256.
RREAL / RIDEAL select the real ramp or an ideal one (RAMP_REAL in case.spice): the difference is the ramp generator's own contribution.
Timeline, measures, analysis: tb_ramp_adc4_ctl.inc. run.sh netlists this drawing and simulates it.} 60 -1500 0 0 0.32 0.32 {}
C {devices/code_shown.sym} 60 -1320 0 0 {name=MODELS only_toplevel=false value="* models (typical) and the blocks behind the primitive symbols, by path
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice moscap_typical
.include /foss/designs/mixed_signal/ramp_gen/ref/comparator_updt/cmp_updt.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/midrail_ref/data/midrail_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/midrail_ref/ref_fvf_biased.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/unit_cell_bps/switches.spice
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice
* timeline, sources' parameters, measures, analysis
.include /foss/designs/mixed_signal/ramp_gen/tb_ramp_adc4_ctl.inc"}
T {supply (cold start) and current meters} 60 -900 0 0 0.40 0.40 {layer=13}
C {devices/vsource.sym} 100 -760 0 0 {name=VDD_SOURCE value="PWL(0 0 \{TPWR\} \{VDD\} \{TSTOP\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 100 -790 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 100 -730 0 1 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 260 -760 0 0 {name=VMRAMP value="0" savecurrent=false}
C {devices/lab_pin.sym} 260 -790 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 260 -730 0 1 {name=l4 sig_type=std_logic lab=vdd_ramp}
C {devices/vsource.sym} 420 -760 0 0 {name=VMCELL value="0" savecurrent=false}
C {devices/lab_pin.sym} 420 -790 0 1 {name=l5 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 420 -730 0 1 {name=l6 sig_type=std_logic lab=vdd_cell}
C {devices/vsource.sym} 580 -760 0 0 {name=VMBIAS value="0" savecurrent=false}
C {devices/lab_pin.sym} 580 -790 0 1 {name=l7 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 580 -730 0 1 {name=l8 sig_type=std_logic lab=vdd_bias}
T {bias and references} 60 -560 0 0 0.40 0.40 {layer=13}
C {../ramp_gen/ref/unit_cell_bps/bias_blk.sym} 200 -400 0 0 {name=XBIAS model=bias_gen}
C {devices/lab_pin.sym} 200 -460 0 1 {name=l9 sig_type=std_logic lab=vdd_bias}
C {devices/lab_pin.sym} 200 -340 0 1 {name=l10 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 280 -420 0 1 {name=l11 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 280 -380 0 1 {name=l12 sig_type=std_logic lab=nbias}
C {../ramp_gen/ref/midrail_ref/midref_b.sym} 520 -440 0 0 {name=XVREF model=midref_b}
C {devices/lab_pin.sym} 600 -440 0 1 {name=l13 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 440 -440 0 0 {name=l14 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 520 -500 0 1 {name=l15 sig_type=std_logic lab=vdd_bias}
C {devices/lab_pin.sym} 520 -380 0 1 {name=l16 sig_type=std_logic lab=0}
C {../ramp_gen/ref/midrail_ref/midref_b.sym} 520 -240 0 0 {name=XVBL model=midref_b}
C {devices/lab_pin.sym} 600 -240 0 1 {name=l17 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 440 -240 0 0 {name=l18 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 520 -300 0 1 {name=l19 sig_type=std_logic lab=vdd_bias}
C {devices/lab_pin.sym} 520 -180 0 1 {name=l20 sig_type=std_logic lab=0}
T {the ramp generator (DUT) and the real / ideal selector} 800 -900 0 0 0.40 0.40 {layer=13}
C {ramp_simple.sym} 1000 -700 0 0 {name=XRG}
C {devices/lab_pin.sym} 1120 -700 0 1 {name=l21 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 880 -700 0 0 {name=l22 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 880 -760 0 0 {name=l23 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 880 -640 0 0 {name=l24 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 1000 -820 0 1 {name=l25 sig_type=std_logic lab=vdd_ramp}
C {devices/lab_pin.sym} 1000 -580 0 1 {name=l26 sig_type=std_logic lab=0}
C {../ramp_gen/ref/unit_cell_bps/bias_blk.sym} 1000 -1000 0 0 {name=XBIASR model=bias_gen}
C {devices/lab_pin.sym} 1000 -1060 0 1 {name=l27 sig_type=std_logic lab=vdd_ramp}
C {devices/lab_pin.sym} 1000 -940 0 1 {name=l28 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1080 -1020 0 1 {name=l29 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 1080 -980 0 1 {name=l30 sig_type=std_logic lab=nbias_r}
C {devices/vsource.sym} 820 -460 0 0 {name=VRLO value="\{VRLO_V\}" savecurrent=false}
C {devices/lab_pin.sym} 820 -490 0 1 {name=l31 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 820 -430 0 1 {name=l32 sig_type=std_logic lab=0}
C {devices/vsource.sym} 940 -460 0 0 {name=VRST value="PWL(0 0 \{TPWR\} \{VDD\} \{TR-TPRE\} \{VDD\} \{TR-TPRE+TEDGE\} 0 \{TSTOP\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 940 -490 0 1 {name=l33 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 940 -430 0 1 {name=l34 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1060 -460 0 0 {name=VIDEAL value="PWL(0 \{VR_LO\} \{TR\} \{VR_LO\} \{TE+TOVR\} \{VR_OVR\} \{TSTOP\} \{VR_OVR\})" savecurrent=false}
C {devices/lab_pin.sym} 1060 -490 0 1 {name=l35 sig_type=std_logic lab=videal}
C {devices/lab_pin.sym} 1060 -430 0 1 {name=l36 sig_type=std_logic lab=0}
C {devices/res.sym} 1240 -700 0 0 {name=RREAL value="\{RSEL_REAL\}" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 1240 -730 0 1 {name=l37 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1240 -670 0 1 {name=l38 sig_type=std_logic lab=vr_cell}
C {devices/res.sym} 1240 -460 0 0 {name=RIDEAL value="\{RSEL_IDEAL\}" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 1240 -490 0 1 {name=l39 sig_type=std_logic lab=videal}
C {devices/lab_pin.sym} 1240 -430 0 1 {name=l40 sig_type=std_logic lab=vr_cell}
T {switch controls (HIGH = closed, shared by the four cells) and the count clock} 800 -300 0 0 0.40 0.40 {layer=13}
C {devices/vsource.sym} 820 -160 0 0 {name=VS2 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS\} \{VDD\} \{TS+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 820 -190 0 1 {name=l41 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 820 -130 0 1 {name=l42 sig_type=std_logic lab=0}
C {devices/vsource.sym} 940 -160 0 0 {name=VS0 value="PWL(0 0 \{TPWR\} \{VDD\} \{TISO\} \{VDD\} \{TISO+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 940 -190 0 1 {name=l43 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 940 -130 0 1 {name=l44 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1060 -160 0 0 {name=VS1 value="PWL(0 0 \{TCONN\} 0 \{TCONN+TEDGE\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 1060 -190 0 1 {name=l45 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 1060 -130 0 1 {name=l46 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1180 -160 0 0 {name=VCLK value="PULSE(0 \{VDD\} \{TR\} \{TEDGE\} \{TEDGE\} \{TCOUNT/2-TEDGE\} \{TCOUNT\})" savecurrent=false}
C {devices/lab_pin.sym} 1180 -190 0 1 {name=l47 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1180 -130 0 1 {name=l48 sig_type=std_logic lab=0}
T {four unit cells: each samples its own level vin_i and trips when the ramp passes it} 1500 -900 0 0 0.40 0.40 {layer=13}
C {../ramp_gen/ref/unit_cell_bps/cell_bps.sym} 1700 -600 0 0 {name=XC0}
C {devices/lab_pin.sym} 1560 -720 0 0 {name=l49 sig_type=std_logic lab=vin0}
C {devices/lab_pin.sym} 1560 -690 0 0 {name=l50 sig_type=std_logic lab=vr_cell}
C {devices/lab_pin.sym} 1560 -660 0 0 {name=l51 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 1560 -630 0 0 {name=l52 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 1560 -600 0 0 {name=l53 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1560 -570 0 0 {name=l54 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1560 -540 0 0 {name=l55 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1840 -720 0 1 {name=l56 sig_type=std_logic lab=dout0}
C {devices/lab_pin.sym} 1840 -690 0 1 {name=l57 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1840 -630 0 1 {name=l58 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1840 -600 0 1 {name=l59 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1700 -760 0 1 {name=l60 sig_type=std_logic lab=vdd_cell}
C {devices/lab_pin.sym} 1700 -440 0 1 {name=l61 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1600 -300 0 0 {name=VIN0 value="\{VIN0\}" savecurrent=false}
C {devices/lab_pin.sym} 1600 -330 0 1 {name=l62 sig_type=std_logic lab=vin0}
C {devices/lab_pin.sym} 1600 -270 0 1 {name=l63 sig_type=std_logic lab=0}
C {devices/capa.sym} 1800 -300 0 0 {name=CL0 value=50f footprint=1206 device="ceramic capacitor" m=1}
C {devices/lab_pin.sym} 1800 -330 0 1 {name=l64 sig_type=std_logic lab=dout0}
C {devices/lab_pin.sym} 1800 -270 0 1 {name=l65 sig_type=std_logic lab=0}
C {../ramp_gen/ref/unit_cell_bps/cell_bps.sym} 2220 -600 0 0 {name=XC1}
C {devices/lab_pin.sym} 2080 -720 0 0 {name=l66 sig_type=std_logic lab=vin1}
C {devices/lab_pin.sym} 2080 -690 0 0 {name=l67 sig_type=std_logic lab=vr_cell}
C {devices/lab_pin.sym} 2080 -660 0 0 {name=l68 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 2080 -630 0 0 {name=l69 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 2080 -600 0 0 {name=l70 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 2080 -570 0 0 {name=l71 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2080 -540 0 0 {name=l72 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 2360 -720 0 1 {name=l73 sig_type=std_logic lab=dout1}
C {devices/lab_pin.sym} 2360 -690 0 1 {name=l74 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2360 -630 0 1 {name=l75 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 2360 -600 0 1 {name=l76 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 2220 -760 0 1 {name=l77 sig_type=std_logic lab=vdd_cell}
C {devices/lab_pin.sym} 2220 -440 0 1 {name=l78 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2120 -300 0 0 {name=VIN1 value="\{VIN1\}" savecurrent=false}
C {devices/lab_pin.sym} 2120 -330 0 1 {name=l79 sig_type=std_logic lab=vin1}
C {devices/lab_pin.sym} 2120 -270 0 1 {name=l80 sig_type=std_logic lab=0}
C {devices/capa.sym} 2320 -300 0 0 {name=CL1 value=50f footprint=1206 device="ceramic capacitor" m=1}
C {devices/lab_pin.sym} 2320 -330 0 1 {name=l81 sig_type=std_logic lab=dout1}
C {devices/lab_pin.sym} 2320 -270 0 1 {name=l82 sig_type=std_logic lab=0}
C {../ramp_gen/ref/unit_cell_bps/cell_bps.sym} 2740 -600 0 0 {name=XC2}
C {devices/lab_pin.sym} 2600 -720 0 0 {name=l83 sig_type=std_logic lab=vin2}
C {devices/lab_pin.sym} 2600 -690 0 0 {name=l84 sig_type=std_logic lab=vr_cell}
C {devices/lab_pin.sym} 2600 -660 0 0 {name=l85 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 2600 -630 0 0 {name=l86 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 2600 -600 0 0 {name=l87 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 2600 -570 0 0 {name=l88 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2600 -540 0 0 {name=l89 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 2880 -720 0 1 {name=l90 sig_type=std_logic lab=dout2}
C {devices/lab_pin.sym} 2880 -690 0 1 {name=l91 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2880 -630 0 1 {name=l92 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 2880 -600 0 1 {name=l93 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 2740 -760 0 1 {name=l94 sig_type=std_logic lab=vdd_cell}
C {devices/lab_pin.sym} 2740 -440 0 1 {name=l95 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2640 -300 0 0 {name=VIN2 value="\{VIN2\}" savecurrent=false}
C {devices/lab_pin.sym} 2640 -330 0 1 {name=l96 sig_type=std_logic lab=vin2}
C {devices/lab_pin.sym} 2640 -270 0 1 {name=l97 sig_type=std_logic lab=0}
C {devices/capa.sym} 2840 -300 0 0 {name=CL2 value=50f footprint=1206 device="ceramic capacitor" m=1}
C {devices/lab_pin.sym} 2840 -330 0 1 {name=l98 sig_type=std_logic lab=dout2}
C {devices/lab_pin.sym} 2840 -270 0 1 {name=l99 sig_type=std_logic lab=0}
C {../ramp_gen/ref/unit_cell_bps/cell_bps.sym} 3260 -600 0 0 {name=XC3}
C {devices/lab_pin.sym} 3120 -720 0 0 {name=l100 sig_type=std_logic lab=vin3}
C {devices/lab_pin.sym} 3120 -690 0 0 {name=l101 sig_type=std_logic lab=vr_cell}
C {devices/lab_pin.sym} 3120 -660 0 0 {name=l102 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 3120 -630 0 0 {name=l103 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 3120 -600 0 0 {name=l104 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 3120 -570 0 0 {name=l105 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 3120 -540 0 0 {name=l106 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 3400 -720 0 1 {name=l107 sig_type=std_logic lab=dout3}
C {devices/lab_pin.sym} 3400 -690 0 1 {name=l108 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 3400 -630 0 1 {name=l109 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 3400 -600 0 1 {name=l110 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 3260 -760 0 1 {name=l111 sig_type=std_logic lab=vdd_cell}
C {devices/lab_pin.sym} 3260 -440 0 1 {name=l112 sig_type=std_logic lab=0}
C {devices/vsource.sym} 3160 -300 0 0 {name=VIN3 value="\{VIN3\}" savecurrent=false}
C {devices/lab_pin.sym} 3160 -330 0 1 {name=l113 sig_type=std_logic lab=vin3}
C {devices/lab_pin.sym} 3160 -270 0 1 {name=l114 sig_type=std_logic lab=0}
C {devices/capa.sym} 3360 -300 0 0 {name=CL3 value=50f footprint=1206 device="ceramic capacitor" m=1}
C {devices/lab_pin.sym} 3360 -330 0 1 {name=l115 sig_type=std_logic lab=dout3}
C {devices/lab_pin.sym} 3360 -270 0 1 {name=l116 sig_type=std_logic lab=0}
