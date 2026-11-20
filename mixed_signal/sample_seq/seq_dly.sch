v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 80 -50 80 -20 {}
N 120 -50 120 -20 {}
N 460 -50 460 -20 {}
N 500 -50 500 -20 {}
N 840 -50 840 -20 {}
N 880 -50 880 -20 {}
N 1220 -50 1220 -20 {}
N 1260 -50 1260 -20 {}
T {SEQ_DLY  -  one delay stage, 4 x inv_2} 0 -260 0 0 0.70 0.70 {}
T {layout: one row, abutted, the same orientation} 0 -200 0 0 0.40 0.40 {}
C {devices/ipin.sym} -200 -100 0 0 {name=p_a lab=a sim_pinnumber=1}
C {devices/opin.sym} -200 -60 0 0 {name=p_y lab=y sim_pinnumber=2}
C {devices/iopin.sym} -200 -20 0 0 {name=p_vdd lab=vdd sim_pinnumber=3}
C {devices/iopin.sym} -200 20 0 0 {name=p_vss lab=vss sim_pinnumber=4}
C {gf180mcu_as_sc_mcu7t3v3__inv_2.sym} 100 40 0 0 {name=XD1}
C {devices/lab_pin.sym} 20 40 0 0 {name=l1 sig_type=std_logic lab=a}
C {devices/lab_pin.sym} 180 40 0 1 {name=l2 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 80 -50 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -50 0 1 {name=l4 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 100 0 0 {name=l5 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 120 100 0 1 {name=l6 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__inv_2.sym} 480 40 0 0 {name=XD2}
C {devices/lab_pin.sym} 400 40 0 0 {name=l7 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 560 40 0 1 {name=l8 sig_type=std_logic lab=d2}
C {devices/lab_pin.sym} 460 -50 0 0 {name=l9 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 500 -50 0 1 {name=l10 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 460 100 0 0 {name=l11 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 500 100 0 1 {name=l12 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__inv_2.sym} 860 40 0 0 {name=XD3}
C {devices/lab_pin.sym} 780 40 0 0 {name=l13 sig_type=std_logic lab=d2}
C {devices/lab_pin.sym} 940 40 0 1 {name=l14 sig_type=std_logic lab=d3}
C {devices/lab_pin.sym} 840 -50 0 0 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 880 -50 0 1 {name=l16 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 840 100 0 0 {name=l17 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 880 100 0 1 {name=l18 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__inv_2.sym} 1240 40 0 0 {name=XD4}
C {devices/lab_pin.sym} 1160 40 0 0 {name=l19 sig_type=std_logic lab=d3}
C {devices/lab_pin.sym} 1320 40 0 1 {name=l20 sig_type=std_logic lab=y}
C {devices/lab_pin.sym} 1220 -50 0 0 {name=l21 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1260 -50 0 1 {name=l22 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1220 100 0 0 {name=l23 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1260 100 0 1 {name=l24 sig_type=std_logic lab=vss}
