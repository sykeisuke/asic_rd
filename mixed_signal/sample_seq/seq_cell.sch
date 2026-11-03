v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SEQ_CELL  -  one cell's S2 / S0 / S1 phases, a flop per phase} 0 -360 0 0 0.70 0.70 {}
T {layout: next to its cell, the three flops in one row} 0 -300 0 0 0.40 0.40 {}
T {S2 (sampling)} 60 -190 0 0 0.45 0.45 {layer=13}
T {S0} 420 -190 0 0 0.45 0.45 {layer=13}
T {S1} 780 -190 0 0 0.45 0.45 {layer=13}
T {settled} 60 110 0 0 0.45 0.45 {layer=13}
C {devices/ipin.sym} -260 -140 0 0 {name=p_tin lab=tin sim_pinnumber=1}
C {devices/ipin.sym} -260 -100 0 0 {name=p_c0 lab=c0 sim_pinnumber=2}
C {devices/ipin.sym} -260 -60 0 0 {name=p_c5 lab=c5 sim_pinnumber=3}
C {devices/ipin.sym} -260 -20 0 0 {name=p_c10 lab=c10 sim_pinnumber=4}
C {devices/opin.sym} -260 20 0 0 {name=p_s2 lab=s2 sim_pinnumber=5}
C {devices/opin.sym} -260 60 0 0 {name=p_s0 lab=s0 sim_pinnumber=6}
C {devices/opin.sym} -260 100 0 0 {name=p_s1 lab=s1 sim_pinnumber=7}
C {devices/iopin.sym} -260 140 0 0 {name=p_done lab=done sim_pinnumber=8}
C {devices/iopin.sym} -260 180 0 0 {name=p_vdd lab=vdd sim_pinnumber=9}
C {devices/iopin.sym} -260 220 0 0 {name=p_vss lab=vss sim_pinnumber=10}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 120 0 0 0 {name=XFA}
C {devices/lab_pin.sym} 20 -20 0 0 {name=l1 sig_type=std_logic lab=tin}
C {devices/lab_pin.sym} 20 20 0 0 {name=l2 sig_type=std_logic lab=c0}
C {devices/lab_pin.sym} 220 0 0 1 {name=l3 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 100 -80 0 0 {name=l4 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 -80 0 1 {name=l5 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 100 80 0 0 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 140 80 0 1 {name=l7 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 480 0 0 0 {name=XFB}
C {devices/lab_pin.sym} 380 -20 0 0 {name=l8 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 380 20 0 0 {name=l9 sig_type=std_logic lab=c5}
C {devices/lab_pin.sym} 580 0 0 1 {name=l10 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 460 -80 0 0 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 500 -80 0 1 {name=l12 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 460 80 0 0 {name=l13 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 500 80 0 1 {name=l14 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dfxtp_2.sym} 840 0 0 0 {name=XFC}
C {devices/lab_pin.sym} 740 -20 0 0 {name=l15 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 740 20 0 0 {name=l16 sig_type=std_logic lab=c10}
C {devices/lab_pin.sym} 940 0 0 1 {name=l17 sig_type=std_logic lab=qc}
C {devices/lab_pin.sym} 820 -80 0 0 {name=l18 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 860 -80 0 1 {name=l19 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 820 80 0 0 {name=l20 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 860 80 0 1 {name=l21 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__nor2_2.sym} 1140 0 0 0 {name=XNR}
C {devices/lab_pin.sym} 1060 -20 0 0 {name=l22 sig_type=std_logic lab=qc}
C {devices/lab_pin.sym} 1060 20 0 0 {name=l23 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1220 0 0 1 {name=l24 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 1120 -60 0 0 {name=l25 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1160 -60 0 1 {name=l26 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1120 60 0 0 {name=l27 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1160 60 0 1 {name=l28 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__xor2_2.sym} 120 300 0 0 {name=XX1}
C {devices/lab_pin.sym} 20 280 0 0 {name=l29 sig_type=std_logic lab=tin}
C {devices/lab_pin.sym} 20 320 0 0 {name=l30 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 220 300 0 1 {name=l31 sig_type=std_logic lab=x1}
C {devices/lab_pin.sym} 100 220 0 0 {name=l32 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 220 0 1 {name=l33 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 100 380 0 0 {name=l34 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 140 380 0 1 {name=l35 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__xor2_2.sym} 420 300 0 0 {name=XX2}
C {devices/lab_pin.sym} 320 280 0 0 {name=l36 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 320 320 0 0 {name=l37 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 520 300 0 1 {name=l38 sig_type=std_logic lab=x2}
C {devices/lab_pin.sym} 400 220 0 0 {name=l39 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 440 220 0 1 {name=l40 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 380 0 0 {name=l41 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 440 380 0 1 {name=l42 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__xor2_2.sym} 720 300 0 0 {name=XX3}
C {devices/lab_pin.sym} 620 280 0 0 {name=l43 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 620 320 0 0 {name=l44 sig_type=std_logic lab=qc}
C {devices/lab_pin.sym} 820 300 0 1 {name=l45 sig_type=std_logic lab=x3}
C {devices/lab_pin.sym} 700 220 0 0 {name=l46 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 740 220 0 1 {name=l47 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 700 380 0 0 {name=l48 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 740 380 0 1 {name=l49 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__nor3_2.sym} 1020 300 0 0 {name=XND}
C {devices/lab_pin.sym} 920 260 0 0 {name=l50 sig_type=std_logic lab=x1}
C {devices/lab_pin.sym} 920 300 0 0 {name=l51 sig_type=std_logic lab=x2}
C {devices/lab_pin.sym} 920 340 0 0 {name=l52 sig_type=std_logic lab=x3}
C {devices/lab_pin.sym} 1120 300 0 1 {name=l53 sig_type=std_logic lab=done}
C {devices/lab_pin.sym} 1000 200 0 0 {name=l54 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1040 200 0 1 {name=l55 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1000 400 0 0 {name=l56 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1040 400 0 1 {name=l57 sig_type=std_logic lab=vss}
