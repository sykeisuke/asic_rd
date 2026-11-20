v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SAMPLE_SEQ  -  sampling sequencer, S2 / S0 / S1 of four cells from one clock} 0 -560 0 0 0.70 0.70 {}
T {layout: shift register in one row; each seq_clkgen next to its atop_cell} 0 -500 0 0 0.40 0.40 {}
T {shift register, one track level per cell} 60 -320 0 0 0.45 0.45 {layer=13}
T {clock generators} 60 40 0 0 0.45 0.45 {layer=13}
C {devices/ipin.sym} -300 -380 0 0 {name=p_acq lab=acq sim_pinnumber=1}
C {devices/ipin.sym} -300 -340 0 0 {name=p_clk lab=clk sim_pinnumber=2}
C {devices/opin.sym} -300 -300 0 0 {name=p_s2_0 lab=s2_0 sim_pinnumber=3}
C {devices/opin.sym} -300 -260 0 0 {name=p_s2_1 lab=s2_1 sim_pinnumber=4}
C {devices/opin.sym} -300 -220 0 0 {name=p_s2_2 lab=s2_2 sim_pinnumber=5}
C {devices/opin.sym} -300 -180 0 0 {name=p_s2_3 lab=s2_3 sim_pinnumber=6}
C {devices/opin.sym} -300 -140 0 0 {name=p_s0_0 lab=s0_0 sim_pinnumber=7}
C {devices/opin.sym} -300 -100 0 0 {name=p_s0_1 lab=s0_1 sim_pinnumber=8}
C {devices/opin.sym} -300 -60 0 0 {name=p_s0_2 lab=s0_2 sim_pinnumber=9}
C {devices/opin.sym} -300 -20 0 0 {name=p_s0_3 lab=s0_3 sim_pinnumber=10}
C {devices/opin.sym} -300 20 0 0 {name=p_s1_0 lab=s1_0 sim_pinnumber=11}
C {devices/opin.sym} -300 60 0 0 {name=p_s1_1 lab=s1_1 sim_pinnumber=12}
C {devices/opin.sym} -300 100 0 0 {name=p_s1_2 lab=s1_2 sim_pinnumber=13}
C {devices/opin.sym} -300 140 0 0 {name=p_s1_3 lab=s1_3 sim_pinnumber=14}
C {devices/iopin.sym} -300 180 0 0 {name=p_vdd lab=vdd sim_pinnumber=15}
C {devices/iopin.sym} -300 220 0 0 {name=p_vss lab=vss sim_pinnumber=16}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 160 -160 0 0 {name=XF0}
C {devices/lab_pin.sym} 60 -180 0 0 {name=l1 sig_type=std_logic lab=acq}
C {devices/lab_pin.sym} 60 -140 0 0 {name=l2 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 260 -160 0 1 {name=l3 sig_type=std_logic lab=t0}
C {devices/lab_pin.sym} 140 -240 0 0 {name=l4 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 180 -240 0 1 {name=l5 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 -80 0 0 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 180 -80 0 1 {name=l7 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 540 -160 0 0 {name=XF1}
C {devices/lab_pin.sym} 440 -180 0 0 {name=l8 sig_type=std_logic lab=t0}
C {devices/lab_pin.sym} 440 -140 0 0 {name=l9 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 640 -160 0 1 {name=l10 sig_type=std_logic lab=t1}
C {devices/lab_pin.sym} 520 -240 0 0 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 -240 0 1 {name=l12 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 520 -80 0 0 {name=l13 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 560 -80 0 1 {name=l14 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 920 -160 0 0 {name=XF2}
C {devices/lab_pin.sym} 820 -180 0 0 {name=l15 sig_type=std_logic lab=t1}
C {devices/lab_pin.sym} 820 -140 0 0 {name=l16 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1020 -160 0 1 {name=l17 sig_type=std_logic lab=t2}
C {devices/lab_pin.sym} 900 -240 0 0 {name=l18 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 940 -240 0 1 {name=l19 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -80 0 0 {name=l20 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 940 -80 0 1 {name=l21 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 1300 -160 0 0 {name=XF3}
C {devices/lab_pin.sym} 1200 -180 0 0 {name=l22 sig_type=std_logic lab=t2}
C {devices/lab_pin.sym} 1200 -140 0 0 {name=l23 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1400 -160 0 1 {name=l24 sig_type=std_logic lab=t3}
C {devices/lab_pin.sym} 1280 -240 0 0 {name=l25 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1320 -240 0 1 {name=l26 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1280 -80 0 0 {name=l27 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1320 -80 0 1 {name=l28 sig_type=std_logic lab=vss}
C {seq_clkgen.sym} 160 220 0 0 {name=XG0}
C {devices/lab_pin.sym} 60 220 0 0 {name=l29 sig_type=std_logic lab=t0}
C {devices/lab_pin.sym} 260 180 0 1 {name=l30 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 260 220 0 1 {name=l31 sig_type=std_logic lab=s0_0}
C {devices/lab_pin.sym} 260 260 0 1 {name=l32 sig_type=std_logic lab=s1_0}
C {devices/lab_pin.sym} 160 120 0 0 {name=l33 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 160 320 0 0 {name=l34 sig_type=std_logic lab=vss}
C {seq_clkgen.sym} 540 220 0 0 {name=XG1}
C {devices/lab_pin.sym} 440 220 0 0 {name=l35 sig_type=std_logic lab=t1}
C {devices/lab_pin.sym} 640 180 0 1 {name=l36 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 640 220 0 1 {name=l37 sig_type=std_logic lab=s0_1}
C {devices/lab_pin.sym} 640 260 0 1 {name=l38 sig_type=std_logic lab=s1_1}
C {devices/lab_pin.sym} 540 120 0 0 {name=l39 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 540 320 0 0 {name=l40 sig_type=std_logic lab=vss}
C {seq_clkgen.sym} 920 220 0 0 {name=XG2}
C {devices/lab_pin.sym} 820 220 0 0 {name=l41 sig_type=std_logic lab=t2}
C {devices/lab_pin.sym} 1020 180 0 1 {name=l42 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 1020 220 0 1 {name=l43 sig_type=std_logic lab=s0_2}
C {devices/lab_pin.sym} 1020 260 0 1 {name=l44 sig_type=std_logic lab=s1_2}
C {devices/lab_pin.sym} 920 120 0 0 {name=l45 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 320 0 0 {name=l46 sig_type=std_logic lab=vss}
C {seq_clkgen.sym} 1300 220 0 0 {name=XG3}
C {devices/lab_pin.sym} 1200 220 0 0 {name=l47 sig_type=std_logic lab=t3}
C {devices/lab_pin.sym} 1400 180 0 1 {name=l48 sig_type=std_logic lab=s2_3}
C {devices/lab_pin.sym} 1400 220 0 1 {name=l49 sig_type=std_logic lab=s0_3}
C {devices/lab_pin.sym} 1400 260 0 1 {name=l50 sig_type=std_logic lab=s1_3}
C {devices/lab_pin.sym} 1300 120 0 0 {name=l51 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1300 320 0 0 {name=l52 sig_type=std_logic lab=vss}
