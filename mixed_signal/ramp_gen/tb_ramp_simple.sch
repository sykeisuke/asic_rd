v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 140 -700 140 -670 {}
N 140 -610 140 -580 {}
N 140 -420 140 -390 {}
N 140 -330 140 -300 {}
N 560 -740 560 -700 {}
N 560 -580 560 -540 {}
N 640 -660 700 -660 {}
N 640 -620 700 -620 {}
N 820 -620 880 -620 {}
N 820 -560 880 -560 {}
N 820 -500 880 -500 {}
N 820 -420 820 -390 {}
N 820 -330 820 -300 {}
N 1000 -720 1000 -680 {}
N 1000 -440 1000 -400 {}
N 1120 -560 1180 -560 {}
N 1180 -560 1400 -560 {}
N 1400 -560 1400 -470 {}
N 1400 -560 2000 -560 {}
N 1400 -410 1400 -340 {}
N 2000 -560 2000 -470 {}
N 2000 -410 2000 -340 {}
T {TB_RAMP_SIMPLE  -  ramp_simple alone on its bias_gen, cell load and S1 kick} 60 -900 0 0 0.70 0.70 {}
T {supply and bias} 60 -780 0 0 0.45 0.45 {layer=13}
T {reset and start level} 60 -480 0 0 0.45 0.45 {layer=13}
T {ramp generator (DUT)} 820 -780 0 0 0.45 0.45 {layer=13}
T {cell load and S1 kick} 1340 -780 0 0 0.45 0.45 {layer=13}
T {NCELL = 4} 1440 -545 0 0 0.35 0.35 {layer=4}
T {10 fF per cell} 1440 -515 0 0 0.35 0.35 {layer=4}
T {VKICK 2.0 V} 2040 -460 0 0 0.35 0.35 {layer=4}
C {devices/vsource.sym} 140 -640 0 0 {name=VDD_SOURCE value="PWL(0 0 \{TPWR\} \{VDD*VDDX\} \{TSTOP\} \{VDD*VDDX\})" savecurrent=false}
C {devices/lab_pin.sym} 140 -700 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 -580 0 1 {name=l2 sig_type=std_logic lab=0}
C {../ramp_gen/ref/unit_cell_bps/bias_blk.sym} 560 -640 0 0 {name=XBIAS model=bias_gen}
C {devices/lab_pin.sym} 560 -740 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 -540 0 1 {name=l4 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 700 -660 0 1 {name=l5 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -620 0 1 {name=l6 sig_type=std_logic lab=nbias}
C {devices/vsource.sym} 140 -360 0 0 {name=VRST value="PWL(0 0 \{TPWR\} \{VDD\} \{TR-TPRE\} \{VDD\} \{TR-TPRE+100p\} 0 \{TRST2\} 0 \{TRST2+100p\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 140 -420 0 1 {name=l7 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 140 -300 0 1 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 820 -360 0 0 {name=VRLO value="\{VR_LO-SLOPE*TPRE\}" savecurrent=false}
C {devices/lab_pin.sym} 820 -420 0 1 {name=l9 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 820 -300 0 1 {name=l10 sig_type=std_logic lab=0}
C {ramp_simple.sym} 1000 -560 0 0 {name=XRG}
C {devices/lab_pin.sym} 820 -620 0 0 {name=l11 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 820 -560 0 0 {name=l12 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 820 -500 0 0 {name=l13 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1000 -720 0 1 {name=l14 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1000 -400 0 1 {name=l15 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1180 -560 0 1 {name=l16 sig_type=std_logic lab=vramp}
C {devices/capa.sym} 1400 -440 0 0 {name=CL value="\{NCELL*CLOAD_CELL+1f\}" m=1}
C {devices/lab_pin.sym} 1400 -340 0 1 {name=l17 sig_type=std_logic lab=0}
C {devices/isource.sym} 2000 -440 2 0 {name=IKICK value="PULSE(0 \{QKICK/1n\} \{TCONN\} 100p 100p 0.9n 1)" savecurrent=false}
C {devices/lab_pin.sym} 2000 -340 0 1 {name=l18 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 60 -160 0 0 {name=MODELS only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice moscap_typical
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice"}
C {devices/code_shown.sym} 60 60 0 0 {name=PARAMS only_toplevel=false value=".param VDD=3.3
.param TCOUNT=50n
.param VR_LO=0.5
.param VR_HI=2.0
.param LSB='(VR_HI-VR_LO)/256'
.param TRAMP='256*TCOUNT'
.param SLOPE='(VR_HI-VR_LO)/TRAMP'
.param CLOAD_CELL=10f
.param NCELL=4
.param VKICK=2.0
.param VDDX=1
.param TPRE=0
.param TPWR=100n
.param T0=1u
.param TS='T0+300n'
.param TCONN='TS+10n'
.param TR='T0+400n'
.param TE='TR+TRAMP'
.param TOVR='20*TCOUNT'
.param TRST2='TE+TOVR+50n'
.param TSTOP='TRST2+600n'
.param QKICK='NCELL*CLOAD_CELL*(VKICK-VR_LO)'"}
C {devices/code_shown.sym} 1000 -160 0 0 {name=MEASURES only_toplevel=false value=".options reltol=1e-5 abstol=1e-13 vntol=1e-7 gmin=1e-15 savecurrents
.tran 0.2n \{TSTOP\} 0 2n
.save v(vramp) v(vrlo) v(rst) v(pbias) i(vdd_source)
.save @m.xrg.xps.m0[vds] @m.xrg.xps.m0[vdsat] @m.xrg.xps.m0[id]
.measure tran vr_tconn FIND v(vramp) AT=\{TCONN\}
.measure tran vr_kick_max MAX v(vramp) FROM=\{TCONN\} TO=\{TR\}
.measure tran vr_tr FIND v(vramp) AT=\{TR\}
.measure tran vr_te FIND v(vramp) AT=\{TE\}
.measure tran vr_ovr FIND v(vramp) AT=\{TE+TOVR\}
.measure tran i_ps AVG @m.xrg.xps.m0[id] FROM=\{TR\} TO=\{TE\}
.measure tran i_total AVG i(vdd_source) FROM=\{TR\} TO=\{TE\}
.measure tran ps_vds_top FIND @m.xrg.xps.m0[vds] AT=\{TE+TOVR\}
.measure tran ps_vdsat FIND @m.xrg.xps.m0[vdsat] AT=\{TE+TOVR\}
.measure tran ps_margin PARAM='abs(ps_vds_top)-abs(ps_vdsat)'
.measure tran pbias_tr FIND v(pbias) AT=\{TR\}
.control
set num_threads=1
set wr_singlescale
set wr_vecnames
run
wrdata ramp.csv v(vramp) v(vrlo) v(rst) v(pbias)
quit
.endc"}
