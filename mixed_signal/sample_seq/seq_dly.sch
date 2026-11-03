v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {SEQ_DLY  -  one delay stage, 22 x dlybuff_2} 0 -260 0 0 0.70 0.70 {}
T {layout: one row, abutted, the same orientation} 0 -200 0 0 0.40 0.40 {}
C {devices/ipin.sym} -200 -100 0 0 {name=p_a lab=a sim_pinnumber=1}
C {devices/opin.sym} -200 -60 0 0 {name=p_y lab=y sim_pinnumber=2}
C {devices/iopin.sym} -200 -20 0 0 {name=p_vdd lab=vdd sim_pinnumber=3}
C {devices/iopin.sym} -200 20 0 0 {name=p_vss lab=vss sim_pinnumber=4}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 100 40 0 0 {name=XD1}
C {devices/lab_pin.sym} 0 40 0 0 {name=l1 sig_type=std_logic lab=a}
C {devices/lab_pin.sym} 200 40 0 1 {name=l2 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 80 -20 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -20 0 1 {name=l4 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 100 0 0 {name=l5 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 120 100 0 1 {name=l6 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 380 40 0 0 {name=XD2}
C {devices/lab_pin.sym} 280 40 0 0 {name=l7 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 480 40 0 1 {name=l8 sig_type=std_logic lab=d2}
C {devices/lab_pin.sym} 360 -20 0 0 {name=l9 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 -20 0 1 {name=l10 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 360 100 0 0 {name=l11 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 400 100 0 1 {name=l12 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 660 40 0 0 {name=XD3}
C {devices/lab_pin.sym} 560 40 0 0 {name=l13 sig_type=std_logic lab=d2}
C {devices/lab_pin.sym} 760 40 0 1 {name=l14 sig_type=std_logic lab=d3}
C {devices/lab_pin.sym} 640 -20 0 0 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 680 -20 0 1 {name=l16 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 640 100 0 0 {name=l17 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 680 100 0 1 {name=l18 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 940 40 0 0 {name=XD4}
C {devices/lab_pin.sym} 840 40 0 0 {name=l19 sig_type=std_logic lab=d3}
C {devices/lab_pin.sym} 1040 40 0 1 {name=l20 sig_type=std_logic lab=d4}
C {devices/lab_pin.sym} 920 -20 0 0 {name=l21 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 960 -20 0 1 {name=l22 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 100 0 0 {name=l23 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 960 100 0 1 {name=l24 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1220 40 0 0 {name=XD5}
C {devices/lab_pin.sym} 1120 40 0 0 {name=l25 sig_type=std_logic lab=d4}
C {devices/lab_pin.sym} 1320 40 0 1 {name=l26 sig_type=std_logic lab=d5}
C {devices/lab_pin.sym} 1200 -20 0 0 {name=l27 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1240 -20 0 1 {name=l28 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 100 0 0 {name=l29 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1240 100 0 1 {name=l30 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1500 40 0 0 {name=XD6}
C {devices/lab_pin.sym} 1400 40 0 0 {name=l31 sig_type=std_logic lab=d5}
C {devices/lab_pin.sym} 1600 40 0 1 {name=l32 sig_type=std_logic lab=d6}
C {devices/lab_pin.sym} 1480 -20 0 0 {name=l33 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1520 -20 0 1 {name=l34 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 100 0 0 {name=l35 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1520 100 0 1 {name=l36 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1780 40 0 0 {name=XD7}
C {devices/lab_pin.sym} 1680 40 0 0 {name=l37 sig_type=std_logic lab=d6}
C {devices/lab_pin.sym} 1880 40 0 1 {name=l38 sig_type=std_logic lab=d7}
C {devices/lab_pin.sym} 1760 -20 0 0 {name=l39 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1800 -20 0 1 {name=l40 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1760 100 0 0 {name=l41 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1800 100 0 1 {name=l42 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 2060 40 0 0 {name=XD8}
C {devices/lab_pin.sym} 1960 40 0 0 {name=l43 sig_type=std_logic lab=d7}
C {devices/lab_pin.sym} 2160 40 0 1 {name=l44 sig_type=std_logic lab=d8}
C {devices/lab_pin.sym} 2040 -20 0 0 {name=l45 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2080 -20 0 1 {name=l46 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2040 100 0 0 {name=l47 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 2080 100 0 1 {name=l48 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 100 300 0 0 {name=XD9}
C {devices/lab_pin.sym} 0 300 0 0 {name=l49 sig_type=std_logic lab=d8}
C {devices/lab_pin.sym} 200 300 0 1 {name=l50 sig_type=std_logic lab=d9}
C {devices/lab_pin.sym} 80 240 0 0 {name=l51 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 240 0 1 {name=l52 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 360 0 0 {name=l53 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 120 360 0 1 {name=l54 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 380 300 0 0 {name=XD10}
C {devices/lab_pin.sym} 280 300 0 0 {name=l55 sig_type=std_logic lab=d9}
C {devices/lab_pin.sym} 480 300 0 1 {name=l56 sig_type=std_logic lab=d10}
C {devices/lab_pin.sym} 360 240 0 0 {name=l57 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 240 0 1 {name=l58 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 360 360 0 0 {name=l59 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 400 360 0 1 {name=l60 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 660 300 0 0 {name=XD11}
C {devices/lab_pin.sym} 560 300 0 0 {name=l61 sig_type=std_logic lab=d10}
C {devices/lab_pin.sym} 760 300 0 1 {name=l62 sig_type=std_logic lab=d11}
C {devices/lab_pin.sym} 640 240 0 0 {name=l63 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 680 240 0 1 {name=l64 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 640 360 0 0 {name=l65 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 680 360 0 1 {name=l66 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 940 300 0 0 {name=XD12}
C {devices/lab_pin.sym} 840 300 0 0 {name=l67 sig_type=std_logic lab=d11}
C {devices/lab_pin.sym} 1040 300 0 1 {name=l68 sig_type=std_logic lab=d12}
C {devices/lab_pin.sym} 920 240 0 0 {name=l69 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 960 240 0 1 {name=l70 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 360 0 0 {name=l71 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 960 360 0 1 {name=l72 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1220 300 0 0 {name=XD13}
C {devices/lab_pin.sym} 1120 300 0 0 {name=l73 sig_type=std_logic lab=d12}
C {devices/lab_pin.sym} 1320 300 0 1 {name=l74 sig_type=std_logic lab=d13}
C {devices/lab_pin.sym} 1200 240 0 0 {name=l75 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1240 240 0 1 {name=l76 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 360 0 0 {name=l77 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1240 360 0 1 {name=l78 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1500 300 0 0 {name=XD14}
C {devices/lab_pin.sym} 1400 300 0 0 {name=l79 sig_type=std_logic lab=d13}
C {devices/lab_pin.sym} 1600 300 0 1 {name=l80 sig_type=std_logic lab=d14}
C {devices/lab_pin.sym} 1480 240 0 0 {name=l81 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1520 240 0 1 {name=l82 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 360 0 0 {name=l83 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1520 360 0 1 {name=l84 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1780 300 0 0 {name=XD15}
C {devices/lab_pin.sym} 1680 300 0 0 {name=l85 sig_type=std_logic lab=d14}
C {devices/lab_pin.sym} 1880 300 0 1 {name=l86 sig_type=std_logic lab=d15}
C {devices/lab_pin.sym} 1760 240 0 0 {name=l87 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1800 240 0 1 {name=l88 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1760 360 0 0 {name=l89 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1800 360 0 1 {name=l90 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 2060 300 0 0 {name=XD16}
C {devices/lab_pin.sym} 1960 300 0 0 {name=l91 sig_type=std_logic lab=d15}
C {devices/lab_pin.sym} 2160 300 0 1 {name=l92 sig_type=std_logic lab=d16}
C {devices/lab_pin.sym} 2040 240 0 0 {name=l93 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2080 240 0 1 {name=l94 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2040 360 0 0 {name=l95 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 2080 360 0 1 {name=l96 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 100 560 0 0 {name=XD17}
C {devices/lab_pin.sym} 0 560 0 0 {name=l97 sig_type=std_logic lab=d16}
C {devices/lab_pin.sym} 200 560 0 1 {name=l98 sig_type=std_logic lab=d17}
C {devices/lab_pin.sym} 80 500 0 0 {name=l99 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 500 0 1 {name=l100 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 80 620 0 0 {name=l101 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 120 620 0 1 {name=l102 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 380 560 0 0 {name=XD18}
C {devices/lab_pin.sym} 280 560 0 0 {name=l103 sig_type=std_logic lab=d17}
C {devices/lab_pin.sym} 480 560 0 1 {name=l104 sig_type=std_logic lab=d18}
C {devices/lab_pin.sym} 360 500 0 0 {name=l105 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 500 0 1 {name=l106 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 360 620 0 0 {name=l107 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 400 620 0 1 {name=l108 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 660 560 0 0 {name=XD19}
C {devices/lab_pin.sym} 560 560 0 0 {name=l109 sig_type=std_logic lab=d18}
C {devices/lab_pin.sym} 760 560 0 1 {name=l110 sig_type=std_logic lab=d19}
C {devices/lab_pin.sym} 640 500 0 0 {name=l111 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 680 500 0 1 {name=l112 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 640 620 0 0 {name=l113 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 680 620 0 1 {name=l114 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 940 560 0 0 {name=XD20}
C {devices/lab_pin.sym} 840 560 0 0 {name=l115 sig_type=std_logic lab=d19}
C {devices/lab_pin.sym} 1040 560 0 1 {name=l116 sig_type=std_logic lab=d20}
C {devices/lab_pin.sym} 920 500 0 0 {name=l117 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 960 500 0 1 {name=l118 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 620 0 0 {name=l119 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 960 620 0 1 {name=l120 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1220 560 0 0 {name=XD21}
C {devices/lab_pin.sym} 1120 560 0 0 {name=l121 sig_type=std_logic lab=d20}
C {devices/lab_pin.sym} 1320 560 0 1 {name=l122 sig_type=std_logic lab=d21}
C {devices/lab_pin.sym} 1200 500 0 0 {name=l123 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1240 500 0 1 {name=l124 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 620 0 0 {name=l125 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1240 620 0 1 {name=l126 sig_type=std_logic lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dlybuff_2.sym} 1500 560 0 0 {name=XD22}
C {devices/lab_pin.sym} 1400 560 0 0 {name=l127 sig_type=std_logic lab=d21}
C {devices/lab_pin.sym} 1600 560 0 1 {name=l128 sig_type=std_logic lab=y}
C {devices/lab_pin.sym} 1480 500 0 0 {name=l129 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1520 500 0 1 {name=l130 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1480 620 0 0 {name=l131 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1520 620 0 1 {name=l132 sig_type=std_logic lab=vss}
