v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SAMPLE_SEQ  -  sampling sequencer, S2 / S0 / S1 of four cells from one clock} 0 -860 0 0 0.70 0.70 {}
T {layout: delay line shared; each seq_cell next to its atop_cell} 0 -800 0 0 0.40 0.40 {}
T {clock gate} 60 -660 0 0 0.45 0.45 {layer=13}
T {delay line, c5 = c0 + D, c10 = c5 + D} 60 -300 0 0 0.45 0.45 {layer=13}
T {cells, 50 ns apart (S2 flops are the token chain)} 60 20 0 0 0.45 0.45 {layer=13}
C {devices/ipin.sym} -300 -560 0 0 {name=p_acq lab=acq sim_pinnumber=1}
C {devices/ipin.sym} -300 -520 0 0 {name=p_clk lab=clk sim_pinnumber=2}
C {devices/opin.sym} -300 -480 0 0 {name=p_s2_0 lab=s2_0 sim_pinnumber=3}
C {devices/opin.sym} -300 -440 0 0 {name=p_s2_1 lab=s2_1 sim_pinnumber=4}
C {devices/opin.sym} -300 -400 0 0 {name=p_s2_2 lab=s2_2 sim_pinnumber=5}
C {devices/opin.sym} -300 -360 0 0 {name=p_s2_3 lab=s2_3 sim_pinnumber=6}
C {devices/opin.sym} -300 -320 0 0 {name=p_s0_0 lab=s0_0 sim_pinnumber=7}
C {devices/opin.sym} -300 -280 0 0 {name=p_s0_1 lab=s0_1 sim_pinnumber=8}
C {devices/opin.sym} -300 -240 0 0 {name=p_s0_2 lab=s0_2 sim_pinnumber=9}
C {devices/opin.sym} -300 -200 0 0 {name=p_s0_3 lab=s0_3 sim_pinnumber=10}
C {devices/opin.sym} -300 -160 0 0 {name=p_s1_0 lab=s1_0 sim_pinnumber=11}
C {devices/opin.sym} -300 -120 0 0 {name=p_s1_1 lab=s1_1 sim_pinnumber=12}
C {devices/opin.sym} -300 -80 0 0 {name=p_s1_2 lab=s1_2 sim_pinnumber=13}
C {devices/opin.sym} -300 -40 0 0 {name=p_s1_3 lab=s1_3 sim_pinnumber=14}
C {devices/iopin.sym} -300 0 0 0 {name=p_vdd lab=vdd sim_pinnumber=15}
C {devices/iopin.sym} -300 40 0 0 {name=p_vss lab=vss sim_pinnumber=16}
C {gf180mcu_as_sc_mcu7t3v3__nand4_2.sym} 160 -440 0 0 {name=XEN}
C {devices/lab_pin.sym} 60 -500 0 0 {name=l1 sig_type=std_logic lab=done_0}
C {devices/lab_pin.sym} 60 -460 0 0 {name=l2 sig_type=std_logic lab=done_1}
C {devices/lab_pin.sym} 60 -420 0 0 {name=l3 sig_type=std_logic lab=done_2}
C {devices/lab_pin.sym} 60 -380 0 0 {name=l4 sig_type=std_logic lab=done_3}
C {devices/lab_pin.sym} 260 -440 0 1 {name=l5 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 140 -560 0 0 {name=l6 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 180 -560 0 1 {name=l7 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 -320 0 0 {name=l8 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 180 -320 0 1 {name=l9 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlxtn_2.sym} 460 -440 0 0 {name=XLG}
C {devices/lab_pin.sym} 360 -460 0 0 {name=l10 sig_type=std_logic lab=en}
C {devices/lab_pin.sym} 360 -420 0 0 {name=l11 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 560 -440 0 1 {name=l12 sig_type=std_logic lab=en_l}
C {devices/lab_pin.sym} 440 -520 0 0 {name=l13 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 480 -520 0 1 {name=l14 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 440 -360 0 0 {name=l15 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 480 -360 0 1 {name=l16 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__and2_2.sym} 760 -440 0 0 {name=XAG}
C {devices/lab_pin.sym} 660 -460 0 0 {name=l17 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 660 -420 0 0 {name=l18 sig_type=std_logic lab=en_l}
C {devices/lab_pin.sym} 860 -440 0 1 {name=l19 sig_type=std_logic lab=gclk}
C {devices/lab_pin.sym} 740 -520 0 0 {name=l20 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 780 -520 0 1 {name=l21 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 740 -360 0 0 {name=l22 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 780 -360 0 1 {name=l23 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__clkbuff_4.sym} 160 -160 0 0 {name=XB0}
C {devices/lab_pin.sym} 60 -160 0 0 {name=l24 sig_type=std_logic lab=gclk}
C {devices/lab_pin.sym} 260 -160 0 1 {name=l25 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 140 -220 0 0 {name=l26 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 180 -220 0 1 {name=l27 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 -100 0 0 {name=l28 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 180 -100 0 1 {name=l29 sig_type=std_logic lab=vss}
C {seq_dly.sym} 520 -160 0 0 {name=XL1}
C {devices/lab_pin.sym} 420 -160 0 0 {name=l30 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 620 -160 0 1 {name=l31 sig_type=std_logic lab=c5r}
C {devices/lab_pin.sym} 520 -220 0 0 {name=l32 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 520 -100 0 0 {name=l33 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__clkbuff_4.sym} 880 -160 0 0 {name=XB5}
C {devices/lab_pin.sym} 780 -160 0 0 {name=l34 sig_type=std_logic lab=c5r}
C {devices/lab_pin.sym} 980 -160 0 1 {name=l35 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 860 -220 0 0 {name=l36 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -220 0 1 {name=l37 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 860 -100 0 0 {name=l38 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 900 -100 0 1 {name=l39 sig_type=std_logic lab=vss}
C {seq_dly.sym} 1240 -160 0 0 {name=XL2}
C {devices/lab_pin.sym} 1140 -160 0 0 {name=l40 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 1340 -160 0 1 {name=l41 sig_type=std_logic lab=c10r}
C {devices/lab_pin.sym} 1240 -220 0 0 {name=l42 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1240 -100 0 0 {name=l43 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__clkbuff_4.sym} 1600 -160 0 0 {name=XB10}
C {devices/lab_pin.sym} 1500 -160 0 0 {name=l44 sig_type=std_logic lab=c10r}
C {devices/lab_pin.sym} 1700 -160 0 1 {name=l45 sig_type=std_logic lab=c10}
C {devices/lab_pin.sym} 1580 -220 0 0 {name=l46 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1620 -220 0 1 {name=l47 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1580 -100 0 0 {name=l48 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1620 -100 0 1 {name=l49 sig_type=std_logic lab=vss}
C {seq_cell.sym} 200 200 0 0 {name=XC0}
C {devices/lab_pin.sym} 100 140 0 0 {name=l50 sig_type=std_logic lab=acq}
C {devices/lab_pin.sym} 100 180 0 0 {name=l51 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 100 220 0 0 {name=l52 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 100 260 0 0 {name=l53 sig_type=std_logic lab=c10}
C {devices/lab_pin.sym} 300 140 0 1 {name=l54 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 300 180 0 1 {name=l55 sig_type=std_logic lab=s0_0}
C {devices/lab_pin.sym} 300 220 0 1 {name=l56 sig_type=std_logic lab=s1_0}
C {devices/lab_pin.sym} 300 260 0 1 {name=l57 sig_type=std_logic lab=done_0}
C {devices/lab_pin.sym} 200 80 0 0 {name=l58 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 200 320 0 0 {name=l59 sig_type=std_logic lab=vss}
C {seq_cell.sym} 580 200 0 0 {name=XC1}
C {devices/lab_pin.sym} 480 140 0 0 {name=l60 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 480 180 0 0 {name=l61 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 480 220 0 0 {name=l62 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 480 260 0 0 {name=l63 sig_type=std_logic lab=c10}
C {devices/lab_pin.sym} 680 140 0 1 {name=l64 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 680 180 0 1 {name=l65 sig_type=std_logic lab=s0_1}
C {devices/lab_pin.sym} 680 220 0 1 {name=l66 sig_type=std_logic lab=s1_1}
C {devices/lab_pin.sym} 680 260 0 1 {name=l67 sig_type=std_logic lab=done_1}
C {devices/lab_pin.sym} 580 80 0 0 {name=l68 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 580 320 0 0 {name=l69 sig_type=std_logic lab=vss}
C {seq_cell.sym} 960 200 0 0 {name=XC2}
C {devices/lab_pin.sym} 860 140 0 0 {name=l70 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 860 180 0 0 {name=l71 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 860 220 0 0 {name=l72 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 860 260 0 0 {name=l73 sig_type=std_logic lab=c10}
C {devices/lab_pin.sym} 1060 140 0 1 {name=l74 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 1060 180 0 1 {name=l75 sig_type=std_logic lab=s0_2}
C {devices/lab_pin.sym} 1060 220 0 1 {name=l76 sig_type=std_logic lab=s1_2}
C {devices/lab_pin.sym} 1060 260 0 1 {name=l77 sig_type=std_logic lab=done_2}
C {devices/lab_pin.sym} 960 80 0 0 {name=l78 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 960 320 0 0 {name=l79 sig_type=std_logic lab=vss}
C {seq_cell.sym} 1340 200 0 0 {name=XC3}
C {devices/lab_pin.sym} 1240 140 0 0 {name=l80 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 1240 180 0 0 {name=l81 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 1240 220 0 0 {name=l82 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 1240 260 0 0 {name=l83 sig_type=std_logic lab=c10}
C {devices/lab_pin.sym} 1440 140 0 1 {name=l84 sig_type=std_logic lab=s2_3}
C {devices/lab_pin.sym} 1440 180 0 1 {name=l85 sig_type=std_logic lab=s0_3}
C {devices/lab_pin.sym} 1440 220 0 1 {name=l86 sig_type=std_logic lab=s1_3}
C {devices/lab_pin.sym} 1440 260 0 1 {name=l87 sig_type=std_logic lab=done_3}
C {devices/lab_pin.sym} 1340 80 0 0 {name=l88 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1340 320 0 0 {name=l89 sig_type=std_logic lab=vss}
