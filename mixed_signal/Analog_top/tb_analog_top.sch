v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {CQ = 40 fF} 3480 -560 0 0 0.36 0.36 {layer=4}
T {TB_ANALOG_TOP  -  one four-cell record of the analog macro from a cold supply} 120 -1900 0 0 0.8 0.8 {}
T {SUPPLIES / RAMP_RST / CNT_CLK} 40 -1680 0 0 0.5 0.5 {layer=4}
T {S2_k} 760 -1680 0 0 0.5 0.5 {layer=4}
T {S0_k} 1480 -1680 0 0 0.5 0.5 {layer=4}
T {S1_k} 2200 -1680 0 0 0.5 0.5 {layer=4}
T {VIN} 40 -540 0 0 0.5 0.5 {layer=4}
N 120 -1560 120 -1530 {lab=avdd}
N 120 -1470 120 -1440 {lab=0}
N 120 -1360 120 -1330 {lab=dvdd}
N 120 -1270 120 -1240 {lab=0}
N 120 -1160 120 -1130 {lab=cnt_clk}
N 120 -1070 120 -1040 {lab=0}
N 840 -1560 840 -1530 {lab=ramp_rst}
N 840 -1470 840 -1440 {lab=0}
N 840 -1360 840 -1330 {lab=acq}
N 840 -1270 840 -1240 {lab=0}
N 120 -440 120 -410 {lab=vin}
N 120 -350 120 -320 {lab=0}
N 2990 -1045 3050 -1045 {lab=vin}
N 2990 -1015 3050 -1015 {lab=ramp_rst}
N 2990 -985 3050 -985 {lab=cnt_clk}
N 2990 -955 3050 -955 {lab=acq}
N 3350 -1045 3410 -1045 {lab=q0}
N 3350 -1015 3410 -1015 {lab=q1}
N 3350 -985 3410 -985 {lab=q2}
N 3350 -955 3410 -955 {lab=q3}
N 3075 -1095 3135 -1095 {lab=avdd}
N 3075 -905 3135 -905 {lab=0}
N 3265 -1095 3325 -1095 {lab=dvdd}
N 3265 -905 3325 -905 {lab=0}
N 3560 -760 3560 -730 {lab=q0}
N 3560 -670 3560 -640 {lab=0}
N 3700 -760 3700 -730 {lab=q1}
N 3700 -670 3700 -640 {lab=0}
N 3840 -760 3840 -730 {lab=q2}
N 3840 -670 3840 -640 {lab=0}
N 3980 -760 3980 -730 {lab=q3}
N 3980 -670 3980 -640 {lab=0}
C {devices/vsource.sym} 120 -1500 0 0 {name=VAVDD value="PWL(0 0 \{TPWR\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -1560 0 0 {name=l1 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 120 -1440 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -1300 0 0 {name=VDVDD value="PWL(0 0 \{TPWR\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -1360 0 0 {name=l3 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 120 -1240 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -1100 0 0 {name=VCLK value="PULSE(0 \{VDD\} \{TCLK0\} \{TEDGE\} \{TEDGE\} \{TCOUNT/2-TEDGE\} \{TCOUNT\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -1160 0 0 {name=l5 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 120 -1040 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 840 -1500 0 0 {name=VRST value="PWL(0 0 \{TPWR\} \{VDD\} \{TR\} \{VDD\} \{TR+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 840 -1560 0 0 {name=l7 sig_type=std_logic lab=ramp_rst}
C {devices/lab_pin.sym} 840 -1440 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 840 -1300 0 0 {name=VACQ value="PWL(0 0 \{TPWR\} \{VDD\} \{TACQ\} \{VDD\} \{TACQ+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 840 -1360 0 0 {name=l9 sig_type=std_logic lab=acq}
C {devices/lab_pin.sym} 840 -1240 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -380 0 0 {name=VVIN value="PWL(0 \{VIN0\} \{TS0+TSTEP\} \{VIN0\} \{TS0+TSTEP+TEDGE\} \{VIN1\} \{TS1+TSTEP\} \{VIN1\} \{TS1+TSTEP+TEDGE\} \{VIN2\} \{TS2+TSTEP\} \{VIN2\} \{TS2+TSTEP+TEDGE\} \{VIN3\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -440 0 0 {name=l11 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 120 -320 0 0 {name=l12 sig_type=std_logic lab=0}
C {analog_top.sym} 3200 -1000 0 0 {name=XDUT}
C {devices/lab_pin.sym} 2990 -1045 0 0 {name=l13 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 2990 -1015 0 0 {name=l14 sig_type=std_logic lab=ramp_rst}
C {devices/lab_pin.sym} 2990 -985 0 0 {name=l15 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 2990 -955 0 0 {name=l16 sig_type=std_logic lab=acq}
C {devices/lab_pin.sym} 3410 -1045 0 1 {name=l17 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 3410 -1015 0 1 {name=l18 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 3410 -985 0 1 {name=l19 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 3410 -955 0 1 {name=l20 sig_type=std_logic lab=q3}
C {devices/lab_pin.sym} 3075 -1095 0 0 {name=l21 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 3075 -905 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 3325 -1095 0 1 {name=l23 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 3325 -905 0 1 {name=l24 sig_type=std_logic lab=0}
C {devices/capa.sym} 3560 -700 0 0 {name=CQ0 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3560 -760 0 0 {name=l25 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 3560 -640 0 0 {name=l26 sig_type=std_logic lab=0}
C {devices/capa.sym} 3700 -700 0 0 {name=CQ1 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3700 -760 0 0 {name=l27 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 3700 -640 0 0 {name=l28 sig_type=std_logic lab=0}
C {devices/capa.sym} 3840 -700 0 0 {name=CQ2 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3840 -760 0 0 {name=l29 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 3840 -640 0 0 {name=l30 sig_type=std_logic lab=0}
C {devices/capa.sym} 3980 -700 0 0 {name=CQ3 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3980 -760 0 0 {name=l31 sig_type=std_logic lab=q3}
C {devices/lab_pin.sym} 3980 -640 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 4300 -1500 0 0 {name=MODELS only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice"}
C {devices/code_shown.sym} 4300 -1150 0 0 {name=BENCH only_toplevel=false value=".include /foss/designs/mixed_signal/Analog_top/tb_params.inc
.include /foss/designs/mixed_signal/Analog_top/tb_measure.inc"}
C {devices/code_shown.sym} 4300 -850 0 0 {name=SIM_AIDS only_toplevel=false value=".options rshunt=1e15"}
C {devices/title.sym} 120 100 0 0 {name=l999 author="ASIC R&D - mixed_signal/Analog_top - tb_analog_top"}
