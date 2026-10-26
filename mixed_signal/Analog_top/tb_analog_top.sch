v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SIMULATION AID (testbench only, not in the macro):
rshunt = 1e15 ohm from EVERY node to ground. Each bottom plate floats
from S2 opening to the end of the record, and at t = 0 every switch is
open, so the MIM plates have no DC path at the initial operating point.
The macro carries no leak resistor (since v3). 1e-15 S x 3.3 V = 3.3 fA.} 4300 -760 0 0 0.36 0.36 {layer=4}
T {CQ0..CQ3 = CQ = 40 fF: the capture load on each q
(digital capture pins + wire, tb_params.inc)} 3480 -560 0 0 0.36 0.36 {layer=13}
T {TB_ANALOG_TOP  -  one four-cell record of the analog macro (v5: every analog block inside, one VDD/2 buffer) from a cold supply} 120 -2160 0 0 0.8 0.8 {}
T {The circuit of tb_analog_top.spice, drawn by tb_sch.py from that deck: power-up, four samples 50 ns apart (TS0..TS3 = 3.30 .. 3.42 us),
the shared ramp from TR = 3.72 us = TS3 + 300 ns (256 counts of 50 ns + 20 overrun) and the four trips. Levels: vin = 0.5 V + (16.5 / 80.5 / 160.5 / 240.5) LSB, LSB = 1.5 V / 256.
Per cell k: S2_k falls at TS_k (THE SAMPLE), S0_k 5 ns later (isolate the top plate), S1_k rises 5 ns after that (top plate onto vramp); vin steps 20 ns after TS_k.
Timeline and levels: tb_params.inc. Measures, analysis, output: tb_measure.inc. XDUT = analog_top.sym; xschem descends into analog_top.sch and every block below it.
xtb.sh simulates this netlist and compares every measure with the hand bench (func phase): the drawing reproduces the deck.
Since v4: no vrlo source. vrlo is made inside the macro by vrlo_ref (5/33 AVDD, ADR 0018), biased by bias_gen_s; the only ideal sources are the supplies, vin, the switch controls, ramp_rst and cnt_clk.} 120 -2070 0 0 0.42 0.42 {}
T {SUPPLIES / RAMP_RST / CNT_CLK} 40 -1680 0 0 0.5 0.5 {layer=4}
T {S2_k (opens first: sample)} 760 -1680 0 0 0.5 0.5 {layer=4}
T {S0_k (isolate)} 1480 -1680 0 0 0.5 0.5 {layer=4}
T {S1_k (top -> vramp)} 2200 -1680 0 0 0.5 0.5 {layer=4}
T {VIN: one level per cell} 40 -540 0 0 0.5 0.5 {layer=4}
T {avdd 0 -> 3.3 V in TPWR = 100 ns (cold start)} 200 -1520 0 0 0.36 0.36 {layer=13}
T {dvdd, same ramp (latches only)} 200 -1320 0 0 0.36 0.36 {layer=13}
T {ramp_rst HIGH until TR = 3.72 us (TS3 + 300 ns)} 200 -1120 0 0 0.36 0.36 {layer=13}
T {cnt_clk 20 MHz, rising edge at TR} 200 -920 0 0 0.36 0.36 {layer=13}
N 120 -1560 120 -1530 {lab=avdd}
N 120 -1470 120 -1440 {lab=0}
N 120 -1360 120 -1330 {lab=dvdd}
N 120 -1270 120 -1240 {lab=0}
N 120 -1160 120 -1130 {lab=ramp_rst}
N 120 -1070 120 -1040 {lab=0}
N 120 -960 120 -930 {lab=cnt_clk}
N 120 -870 120 -840 {lab=0}
N 840 -1560 840 -1530 {lab=s2_0}
N 840 -1470 840 -1440 {lab=0}
N 840 -1360 840 -1330 {lab=s2_1}
N 840 -1270 840 -1240 {lab=0}
N 840 -1160 840 -1130 {lab=s2_2}
N 840 -1070 840 -1040 {lab=0}
N 840 -960 840 -930 {lab=s2_3}
N 840 -870 840 -840 {lab=0}
N 1560 -1560 1560 -1530 {lab=s0_0}
N 1560 -1470 1560 -1440 {lab=0}
N 1560 -1360 1560 -1330 {lab=s0_1}
N 1560 -1270 1560 -1240 {lab=0}
N 1560 -1160 1560 -1130 {lab=s0_2}
N 1560 -1070 1560 -1040 {lab=0}
N 1560 -960 1560 -930 {lab=s0_3}
N 1560 -870 1560 -840 {lab=0}
N 2280 -1560 2280 -1530 {lab=s1_0}
N 2280 -1470 2280 -1440 {lab=0}
N 2280 -1360 2280 -1330 {lab=s1_1}
N 2280 -1270 2280 -1240 {lab=0}
N 2280 -1160 2280 -1130 {lab=s1_2}
N 2280 -1070 2280 -1040 {lab=0}
N 2280 -960 2280 -930 {lab=s1_3}
N 2280 -870 2280 -840 {lab=0}
N 120 -440 120 -410 {lab=vin}
N 120 -350 120 -320 {lab=0}
N 2990 -1210 3050 -1210 {lab=vin}
N 2990 -1180 3050 -1180 {lab=ramp_rst}
N 2990 -1150 3050 -1150 {lab=cnt_clk}
N 2990 -1120 3050 -1120 {lab=s0_0}
N 2990 -1090 3050 -1090 {lab=s0_1}
N 2990 -1060 3050 -1060 {lab=s0_2}
N 2990 -1030 3050 -1030 {lab=s0_3}
N 2990 -1000 3050 -1000 {lab=s1_0}
N 2990 -970 3050 -970 {lab=s1_1}
N 2990 -940 3050 -940 {lab=s1_2}
N 2990 -910 3050 -910 {lab=s1_3}
N 2990 -880 3050 -880 {lab=s2_0}
N 2990 -850 3050 -850 {lab=s2_1}
N 2990 -820 3050 -820 {lab=s2_2}
N 2990 -790 3050 -790 {lab=s2_3}
N 3350 -1210 3410 -1210 {lab=q0}
N 3350 -1180 3410 -1180 {lab=q1}
N 3350 -1150 3410 -1150 {lab=q2}
N 3350 -1120 3410 -1120 {lab=q3}
N 3075 -1260 3135 -1260 {lab=avdd}
N 3075 -740 3135 -740 {lab=0}
N 3265 -1260 3325 -1260 {lab=dvdd}
N 3265 -740 3325 -740 {lab=0}
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
C {devices/vsource.sym} 120 -1100 0 0 {name=VRST value="PWL(0 0 \{TPWR\} \{VDD\} \{TR\} \{VDD\} \{TR+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 120 -1160 0 0 {name=l5 sig_type=std_logic lab=ramp_rst}
C {devices/lab_pin.sym} 120 -1040 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -900 0 0 {name=VCLK value="PULSE(0 \{VDD\} \{TCLK0\} \{TEDGE\} \{TEDGE\} \{TCOUNT/2-TEDGE\} \{TCOUNT\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -960 0 0 {name=l7 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 120 -840 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 840 -1500 0 0 {name=VS2_0 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS0\} \{VDD\} \{TS0+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 840 -1560 0 0 {name=l9 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 840 -1440 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/vsource.sym} 840 -1300 0 0 {name=VS2_1 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS1\} \{VDD\} \{TS1+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 840 -1360 0 0 {name=l11 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 840 -1240 0 0 {name=l12 sig_type=std_logic lab=0}
C {devices/vsource.sym} 840 -1100 0 0 {name=VS2_2 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS2\} \{VDD\} \{TS2+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 840 -1160 0 0 {name=l13 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 840 -1040 0 0 {name=l14 sig_type=std_logic lab=0}
C {devices/vsource.sym} 840 -900 0 0 {name=VS2_3 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS3\} \{VDD\} \{TS3+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 840 -960 0 0 {name=l15 sig_type=std_logic lab=s2_3}
C {devices/lab_pin.sym} 840 -840 0 0 {name=l16 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1560 -1500 0 0 {name=VS0_0 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS0+TNOV\} \{VDD\} \{TS0+TNOV+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 1560 -1560 0 0 {name=l17 sig_type=std_logic lab=s0_0}
C {devices/lab_pin.sym} 1560 -1440 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1560 -1300 0 0 {name=VS0_1 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS1+TNOV\} \{VDD\} \{TS1+TNOV+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 1560 -1360 0 0 {name=l19 sig_type=std_logic lab=s0_1}
C {devices/lab_pin.sym} 1560 -1240 0 0 {name=l20 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1560 -1100 0 0 {name=VS0_2 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS2+TNOV\} \{VDD\} \{TS2+TNOV+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 1560 -1160 0 0 {name=l21 sig_type=std_logic lab=s0_2}
C {devices/lab_pin.sym} 1560 -1040 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/vsource.sym} 1560 -900 0 0 {name=VS0_3 value="PWL(0 0 \{TPWR\} \{VDD\} \{TS3+TNOV\} \{VDD\} \{TS3+TNOV+TEDGE\} 0)" savecurrent=false}
C {devices/lab_pin.sym} 1560 -960 0 0 {name=l23 sig_type=std_logic lab=s0_3}
C {devices/lab_pin.sym} 1560 -840 0 0 {name=l24 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2280 -1500 0 0 {name=VS1_0 value="PWL(0 0 \{TS0+2*TNOV\} 0 \{TS0+2*TNOV+TEDGE\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 2280 -1560 0 0 {name=l25 sig_type=std_logic lab=s1_0}
C {devices/lab_pin.sym} 2280 -1440 0 0 {name=l26 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2280 -1300 0 0 {name=VS1_1 value="PWL(0 0 \{TS1+2*TNOV\} 0 \{TS1+2*TNOV+TEDGE\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 2280 -1360 0 0 {name=l27 sig_type=std_logic lab=s1_1}
C {devices/lab_pin.sym} 2280 -1240 0 0 {name=l28 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2280 -1100 0 0 {name=VS1_2 value="PWL(0 0 \{TS2+2*TNOV\} 0 \{TS2+2*TNOV+TEDGE\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 2280 -1160 0 0 {name=l29 sig_type=std_logic lab=s1_2}
C {devices/lab_pin.sym} 2280 -1040 0 0 {name=l30 sig_type=std_logic lab=0}
C {devices/vsource.sym} 2280 -900 0 0 {name=VS1_3 value="PWL(0 0 \{TS3+2*TNOV\} 0 \{TS3+2*TNOV+TEDGE\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 2280 -960 0 0 {name=l31 sig_type=std_logic lab=s1_3}
C {devices/lab_pin.sym} 2280 -840 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -380 0 0 {name=VVIN value="PWL(0 \{VIN0\} \{TS0+TSTEP\} \{VIN0\} \{TS0+TSTEP+TEDGE\} \{VIN1\} \{TS1+TSTEP\} \{VIN1\} \{TS1+TSTEP+TEDGE\} \{VIN2\} \{TS2+TSTEP\} \{VIN2\} \{TS2+TSTEP+TEDGE\} \{VIN3\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -440 0 0 {name=l33 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 120 -320 0 0 {name=l34 sig_type=std_logic lab=0}
C {analog_top.sym} 3200 -1000 0 0 {name=XDUT}
C {devices/lab_pin.sym} 2990 -1210 0 0 {name=l35 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 2990 -1180 0 0 {name=l36 sig_type=std_logic lab=ramp_rst}
C {devices/lab_pin.sym} 2990 -1150 0 0 {name=l37 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 2990 -1120 0 0 {name=l38 sig_type=std_logic lab=s0_0}
C {devices/lab_pin.sym} 2990 -1090 0 0 {name=l39 sig_type=std_logic lab=s0_1}
C {devices/lab_pin.sym} 2990 -1060 0 0 {name=l40 sig_type=std_logic lab=s0_2}
C {devices/lab_pin.sym} 2990 -1030 0 0 {name=l41 sig_type=std_logic lab=s0_3}
C {devices/lab_pin.sym} 2990 -1000 0 0 {name=l42 sig_type=std_logic lab=s1_0}
C {devices/lab_pin.sym} 2990 -970 0 0 {name=l43 sig_type=std_logic lab=s1_1}
C {devices/lab_pin.sym} 2990 -940 0 0 {name=l44 sig_type=std_logic lab=s1_2}
C {devices/lab_pin.sym} 2990 -910 0 0 {name=l45 sig_type=std_logic lab=s1_3}
C {devices/lab_pin.sym} 2990 -880 0 0 {name=l46 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 2990 -850 0 0 {name=l47 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 2990 -820 0 0 {name=l48 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 2990 -790 0 0 {name=l49 sig_type=std_logic lab=s2_3}
C {devices/lab_pin.sym} 3410 -1210 0 1 {name=l50 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 3410 -1180 0 1 {name=l51 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 3410 -1150 0 1 {name=l52 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 3410 -1120 0 1 {name=l53 sig_type=std_logic lab=q3}
C {devices/lab_pin.sym} 3075 -1260 0 0 {name=l54 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 3075 -740 0 0 {name=l55 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 3325 -1260 0 1 {name=l56 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 3325 -740 0 1 {name=l57 sig_type=std_logic lab=0}
C {devices/capa.sym} 3560 -700 0 0 {name=CQ0 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3560 -760 0 0 {name=l58 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 3560 -640 0 0 {name=l59 sig_type=std_logic lab=0}
C {devices/capa.sym} 3700 -700 0 0 {name=CQ1 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3700 -760 0 0 {name=l60 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 3700 -640 0 0 {name=l61 sig_type=std_logic lab=0}
C {devices/capa.sym} 3840 -700 0 0 {name=CQ2 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3840 -760 0 0 {name=l62 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 3840 -640 0 0 {name=l63 sig_type=std_logic lab=0}
C {devices/capa.sym} 3980 -700 0 0 {name=CQ3 value=\{CQ\} m=1}
C {devices/lab_pin.sym} 3980 -760 0 0 {name=l64 sig_type=std_logic lab=q3}
C {devices/lab_pin.sym} 3980 -640 0 0 {name=l65 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 4300 -1500 0 0 {name=MODELS only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice"}
C {devices/code_shown.sym} 4300 -1150 0 0 {name=BENCH only_toplevel=false value=".include /foss/designs/mixed_signal/Analog_top/tb_params.inc
.include /foss/designs/mixed_signal/Analog_top/tb_measure.inc"}
C {devices/code_shown.sym} 4300 -850 0 0 {name=SIM_AIDS only_toplevel=false value=".options rshunt=1e15"}
C {devices/title.sym} 120 100 0 0 {name=l999 author="ASIC R&D - mixed_signal/Analog_top - tb_analog_top"}
