v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {3.25 uA} 648 -1002 0 0 0.3 0.3 {layer=4}
T {3.25 uA} 648 -974 0 0 0.3 0.3 {layer=4}
T {3.25 uA} 648 -946 0 0 0.3 0.3 {layer=4}
T {3.25 uA} 648 -918 0 0 0.3 0.3 {layer=4}
T {3.25 uA} 648 -890 0 0 0.3 0.3 {layer=4}
T {11.2 uA} 648 -862 0 0 0.3 0.3 {layer=4}
T {1.53 uA} 648 -834 0 0 0.3 0.3 {layer=4}
T {0.5452 uA} 1968 -1102 0 0 0.3 0.3 {layer=4}
L 4 2480 -380 4880 -380 {dash=6}
L 4 4880 -380 4880 420 {dash=6}
L 4 4880 420 2480 420 {dash=6}
L 4 2480 420 2480 -380 {dash=6}
T {SAMPLING SEQUENCER (DVDD)} 2490 -372 0 0 0.5 0.5 {layer=4}
L 4 320 -1300 760 -1300 {dash=6}
L 4 760 -1300 760 -480 {dash=6}
L 4 760 -480 320 -480 {dash=6}
L 4 320 -480 320 -1300 {dash=6}
T {BIAS} 330 -1292 0 0 0.5 0.5 {layer=4}
L 4 800 -1300 1440 -1300 {dash=6}
L 4 1440 -1300 1440 -480 {dash=6}
L 4 1440 -480 800 -480 {dash=6}
L 4 800 -480 800 -1300 {dash=6}
T {REF (VDD/2): vref = vbl} 810 -1292 0 0 0.5 0.5 {layer=4}
L 4 1480 -1300 2440 -1300 {dash=6}
L 4 2440 -1300 2440 -480 {dash=6}
L 4 2440 -480 1480 -480 {dash=6}
L 4 1480 -480 1480 -1300 {dash=6}
T {RAMP (I/C source) + VR_LO} 1490 -1292 0 0 0.5 0.5 {layer=4}
L 4 2480 -1300 4880 -1300 {dash=6}
L 4 4880 -1300 4880 -480 {dash=6}
L 4 4880 -480 2480 -480 {dash=6}
L 4 2480 -480 2480 -1300 {dash=6}
T {FOUR CELLS} 2490 -1292 0 0 0.5 0.5 {layer=4}
T {ANALOG_TOP  -  analog macro: four bottom-plate cells on one shared ramp} 40 -1560 0 0 0.8 0.8 {}
N 40 -1240 80 -1240 {lab=vin}
N 40 -1195 80 -1195 {lab=ramp_rst}
N 40 -1150 80 -1150 {lab=cnt_clk}
N 40 -1105 80 -1105 {lab=acq}
N 40 -1060 80 -1060 {lab=q0}
N 40 -1015 80 -1015 {lab=q1}
N 40 -970 80 -970 {lab=q2}
N 40 -925 80 -925 {lab=q3}
N 40 -880 80 -880 {lab=avdd}
N 40 -835 80 -835 {lab=avss}
N 40 -790 80 -790 {lab=dvdd}
N 40 -745 80 -745 {lab=dvss}
N 300 -1380 520 -1380 {lab=avdd}
N 520 -1380 1060 -1380 {lab=avdd}
N 1060 -1380 1580 -1380 {lab=avdd}
N 1580 -1380 1880 -1380 {lab=avdd}
N 1880 -1380 2740 -1380 {lab=avdd}
N 2740 -1380 3360 -1380 {lab=avdd}
N 3360 -1380 3980 -1380 {lab=avdd}
N 3980 -1380 4600 -1380 {lab=avdd}
N 520 -1380 520 -1350 {lab=avdd}
N 520 -1290 520 -1260 {lab=avdd_bg}
N 1060 -1380 1060 -1350 {lab=avdd}
N 1060 -1290 1060 -1260 {lab=avdd_ref}
N 1580 -1380 1580 -1350 {lab=avdd}
N 1580 -1290 1580 -1260 {lab=avdd_vrlo}
N 1880 -1380 1880 -1350 {lab=avdd}
N 1880 -1290 1880 -1260 {lab=avdd_ramp}
N 2740 -1380 2740 -1350 {lab=avdd}
N 2740 -1290 2740 -1260 {lab=avdd_c0}
N 3360 -1380 3360 -1350 {lab=avdd}
N 3360 -1290 3360 -1260 {lab=avdd_c1}
N 3980 -1380 3980 -1350 {lab=avdd}
N 3980 -1290 3980 -1260 {lab=avdd_c2}
N 4600 -1380 4600 -1350 {lab=avdd}
N 4600 -1290 4600 -1260 {lab=avdd_c3}
N 520 -1060 520 -1020 {lab=avdd_bg}
N 520 -740 520 -700 {lab=avss}
N 640 -980 700 -980 {lab=pbias0}
N 640 -952 700 -952 {lab=pbias1}
N 640 -924 700 -924 {lab=pbias2}
N 640 -896 700 -896 {lab=pbias3}
N 640 -868 700 -868 {lab=pbias_r}
N 640 -840 700 -840 {lab=ivref}
N 640 -812 700 -812 {lab=ivrlo}
N 920 -1120 920 -1080 {lab=avdd_ref}
N 920 -920 920 -880 {lab=avss}
N 1280 -1000 1340 -1000 {lab=vref}
N 1080 -960 1120 -960 {lab=ivref}
N 1200 -1110 1200 -1070 {lab=avdd_ref}
N 1200 -930 1200 -890 {lab=avss}
N 1000 -1000 1060 -1000 {lab=vmid}
N 1060 -1000 1120 -1000 {lab=vmid}
N 1830 -665 1890 -665 {lab=vrlo}
N 1510 -615 1570 -615 {lab=ivrlo}
N 1700 -815 1700 -775 {lab=avdd_vrlo}
N 1700 -555 1700 -515 {lab=avss}
N 1580 -1120 1640 -1120 {lab=pbias_r}
N 1580 -1040 1640 -1040 {lab=cnt_clk}
N 1960 -1080 2020 -1080 {lab=vramp}
N 1760 -1240 1760 -1200 {lab=avdd_ramp}
N 1840 -1240 1840 -1200 {lab=dvdd}
N 1760 -960 1760 -920 {lab=avss}
N 1840 -960 1840 -920 {lab=dvss}
N 1900 -800 1960 -800 {lab=ramp_rst}
N 1900 -720 1960 -720 {lab=vrlo}
N 2240 -800 2300 -800 {lab=vramp}
N 2100 -640 2100 -600 {lab=avss}
N 2490 -960 2550 -960 {lab=vin}
N 2490 -920 2550 -920 {lab=vramp}
N 2490 -880 2550 -880 {lab=s0_0}
N 2490 -840 2550 -840 {lab=s1_0}
N 2490 -800 2550 -800 {lab=s2_0}
N 2490 -760 2550 -760 {lab=vref}
N 2490 -720 2550 -720 {lab=vref}
N 2490 -680 2550 -680 {lab=pbias0}
N 2930 -960 2990 -960 {lab=q0}
N 2490 -640 2550 -640 {lab=cnt_clk}
N 2655 -1060 2655 -1020 {lab=avdd_c0}
N 2655 -580 2655 -540 {lab=avss}
N 2825 -1060 2825 -1020 {lab=dvdd}
N 2825 -580 2825 -540 {lab=dvss}
N 3110 -960 3170 -960 {lab=vin}
N 3110 -920 3170 -920 {lab=vramp}
N 3110 -880 3170 -880 {lab=s0_1}
N 3110 -840 3170 -840 {lab=s1_1}
N 3110 -800 3170 -800 {lab=s2_1}
N 3110 -760 3170 -760 {lab=vref}
N 3110 -720 3170 -720 {lab=vref}
N 3110 -680 3170 -680 {lab=pbias1}
N 3550 -960 3610 -960 {lab=q1}
N 3110 -640 3170 -640 {lab=cnt_clk}
N 3275 -1060 3275 -1020 {lab=avdd_c1}
N 3275 -580 3275 -540 {lab=avss}
N 3445 -1060 3445 -1020 {lab=dvdd}
N 3445 -580 3445 -540 {lab=dvss}
N 3730 -960 3790 -960 {lab=vin}
N 3730 -920 3790 -920 {lab=vramp}
N 3730 -880 3790 -880 {lab=s0_2}
N 3730 -840 3790 -840 {lab=s1_2}
N 3730 -800 3790 -800 {lab=s2_2}
N 3730 -760 3790 -760 {lab=vref}
N 3730 -720 3790 -720 {lab=vref}
N 3730 -680 3790 -680 {lab=pbias2}
N 4170 -960 4230 -960 {lab=q2}
N 3730 -640 3790 -640 {lab=cnt_clk}
N 3895 -1060 3895 -1020 {lab=avdd_c2}
N 3895 -580 3895 -540 {lab=avss}
N 4065 -1060 4065 -1020 {lab=dvdd}
N 4065 -580 4065 -540 {lab=dvss}
N 4350 -960 4410 -960 {lab=vin}
N 4350 -920 4410 -920 {lab=vramp}
N 4350 -880 4410 -880 {lab=s0_3}
N 4350 -840 4410 -840 {lab=s1_3}
N 4350 -800 4410 -800 {lab=s2_3}
N 4350 -760 4410 -760 {lab=vref}
N 4350 -720 4410 -720 {lab=vref}
N 4350 -680 4410 -680 {lab=pbias3}
N 4790 -960 4850 -960 {lab=q3}
N 4350 -640 4410 -640 {lab=cnt_clk}
N 4515 -1060 4515 -1020 {lab=avdd_c3}
N 4515 -580 4515 -540 {lab=avss}
N 4685 -1060 4685 -1020 {lab=dvdd}
N 4685 -580 4685 -540 {lab=dvss}
N 3520 20 3580 20 {lab=acq}
N 3520 60 3580 60 {lab=cnt_clk}
N 3780 -180 3840 -180 {lab=s2_0}
N 3780 -140 3840 -140 {lab=s2_1}
N 3780 -100 3840 -100 {lab=s2_2}
N 3780 -60 3840 -60 {lab=s2_3}
N 3780 -20 3840 -20 {lab=s0_0}
N 3780 20 3840 20 {lab=s0_1}
N 3780 60 3840 60 {lab=s0_2}
N 3780 100 3840 100 {lab=s0_3}
N 3780 140 3840 140 {lab=s1_0}
N 3780 180 3840 180 {lab=s1_1}
N 3780 220 3840 220 {lab=s1_2}
N 3780 260 3840 260 {lab=s1_3}
N 3680 -280 3680 -240 {lab=dvdd}
N 3680 320 3680 360 {lab=dvss}
C {devices/ipin.sym} 40 -1240 0 0 {name=p_vin lab=vin sim_pinnumber=1}
C {devices/lab_pin.sym} 80 -1240 0 1 {name=l1 sig_type=std_logic lab=vin}
C {devices/ipin.sym} 40 -1195 0 0 {name=p_ramp_rst lab=ramp_rst sim_pinnumber=2}
C {devices/lab_pin.sym} 80 -1195 0 1 {name=l2 sig_type=std_logic lab=ramp_rst}
C {devices/ipin.sym} 40 -1150 0 0 {name=p_cnt_clk lab=cnt_clk sim_pinnumber=3}
C {devices/lab_pin.sym} 80 -1150 0 1 {name=l3 sig_type=std_logic lab=cnt_clk}
C {devices/ipin.sym} 40 -1105 0 0 {name=p_acq lab=acq sim_pinnumber=4}
C {devices/lab_pin.sym} 80 -1105 0 1 {name=l4 sig_type=std_logic lab=acq}
C {devices/opin.sym} 40 -1060 0 1 {name=p_q0 lab=q0 sim_pinnumber=5}
C {devices/lab_pin.sym} 80 -1060 0 1 {name=l5 sig_type=std_logic lab=q0}
C {devices/opin.sym} 40 -1015 0 1 {name=p_q1 lab=q1 sim_pinnumber=6}
C {devices/lab_pin.sym} 80 -1015 0 1 {name=l6 sig_type=std_logic lab=q1}
C {devices/opin.sym} 40 -970 0 1 {name=p_q2 lab=q2 sim_pinnumber=7}
C {devices/lab_pin.sym} 80 -970 0 1 {name=l7 sig_type=std_logic lab=q2}
C {devices/opin.sym} 40 -925 0 1 {name=p_q3 lab=q3 sim_pinnumber=8}
C {devices/lab_pin.sym} 80 -925 0 1 {name=l8 sig_type=std_logic lab=q3}
C {devices/iopin.sym} 40 -880 0 1 {name=p_avdd lab=avdd sim_pinnumber=9}
C {devices/lab_pin.sym} 80 -880 0 1 {name=l9 sig_type=std_logic lab=avdd}
C {devices/iopin.sym} 40 -835 0 1 {name=p_avss lab=avss sim_pinnumber=10}
C {devices/lab_pin.sym} 80 -835 0 1 {name=l10 sig_type=std_logic lab=avss}
C {devices/iopin.sym} 40 -790 0 1 {name=p_dvdd lab=dvdd sim_pinnumber=11}
C {devices/lab_pin.sym} 80 -790 0 1 {name=l11 sig_type=std_logic lab=dvdd}
C {devices/iopin.sym} 40 -745 0 1 {name=p_dvss lab=dvss sim_pinnumber=12}
C {devices/lab_pin.sym} 80 -745 0 1 {name=l12 sig_type=std_logic lab=dvss}
C {devices/lab_pin.sym} 300 -1380 0 0 {name=l13 sig_type=std_logic lab=avdd}
C {devices/ammeter.sym} 520 -1320 0 0 {name=VMBG savecurrent=false}
C {devices/lab_pin.sym} 520 -1260 0 0 {name=l14 sig_type=std_logic lab=avdd_bg}
C {devices/ammeter.sym} 1060 -1320 0 0 {name=VMREF savecurrent=false}
C {devices/lab_pin.sym} 1060 -1260 0 0 {name=l15 sig_type=std_logic lab=avdd_ref}
C {devices/ammeter.sym} 1580 -1320 0 0 {name=VMVRLO savecurrent=false}
C {devices/lab_pin.sym} 1580 -1260 0 0 {name=l16 sig_type=std_logic lab=avdd_vrlo}
C {devices/ammeter.sym} 1880 -1320 0 0 {name=VMRAMP savecurrent=false}
C {devices/lab_pin.sym} 1880 -1260 0 0 {name=l17 sig_type=std_logic lab=avdd_ramp}
C {devices/ammeter.sym} 2740 -1320 0 0 {name=VMC0 savecurrent=false}
C {devices/lab_pin.sym} 2740 -1260 0 0 {name=l18 sig_type=std_logic lab=avdd_c0}
C {devices/ammeter.sym} 3360 -1320 0 0 {name=VMC1 savecurrent=false}
C {devices/lab_pin.sym} 3360 -1260 0 0 {name=l19 sig_type=std_logic lab=avdd_c1}
C {devices/ammeter.sym} 3980 -1320 0 0 {name=VMC2 savecurrent=false}
C {devices/lab_pin.sym} 3980 -1260 0 0 {name=l20 sig_type=std_logic lab=avdd_c2}
C {devices/ammeter.sym} 4600 -1320 0 0 {name=VMC3 savecurrent=false}
C {devices/lab_pin.sym} 4600 -1260 0 0 {name=l21 sig_type=std_logic lab=avdd_c3}
C {bias_gen_s.sym} 520 -900 0 0 {name=XBG}
C {devices/lab_pin.sym} 520 -1060 0 0 {name=l22 sig_type=std_logic lab=avdd_bg}
C {devices/lab_pin.sym} 520 -700 0 0 {name=l23 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 700 -980 0 1 {name=l24 sig_type=std_logic lab=pbias0}
C {devices/lab_pin.sym} 700 -952 0 1 {name=l25 sig_type=std_logic lab=pbias1}
C {devices/lab_pin.sym} 700 -924 0 1 {name=l26 sig_type=std_logic lab=pbias2}
C {devices/lab_pin.sym} 700 -896 0 1 {name=l27 sig_type=std_logic lab=pbias3}
C {devices/lab_pin.sym} 700 -868 0 1 {name=l28 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 700 -840 0 1 {name=l29 sig_type=std_logic lab=ivref}
C {devices/lab_pin.sym} 700 -812 0 1 {name=l30 sig_type=std_logic lab=ivrlo}
C {midref_div.sym} 920 -1000 0 0 {name=XDIV}
C {devices/lab_pin.sym} 920 -1120 0 0 {name=l31 sig_type=std_logic lab=avdd_ref}
C {devices/lab_pin.sym} 920 -880 0 0 {name=l32 sig_type=std_logic lab=avss}
C {midref_buf.sym} 1200 -1000 0 0 {name=XVREF}
C {devices/lab_pin.sym} 1340 -1000 0 1 {name=l33 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1080 -960 0 0 {name=l34 sig_type=std_logic lab=ivref}
C {devices/lab_pin.sym} 1200 -1110 0 0 {name=l35 sig_type=std_logic lab=avdd_ref}
C {devices/lab_pin.sym} 1200 -890 0 0 {name=l36 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1060 -1000 0 0 {name=l37 sig_type=std_logic lab=vmid}
C {vrlo_ref.sym} 1700 -665 0 0 {name=XVRLO}
C {devices/lab_pin.sym} 1890 -665 0 1 {name=l38 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 1510 -615 0 0 {name=l39 sig_type=std_logic lab=ivrlo}
C {devices/lab_pin.sym} 1700 -815 0 0 {name=l40 sig_type=std_logic lab=avdd_vrlo}
C {devices/lab_pin.sym} 1700 -515 0 0 {name=l41 sig_type=std_logic lab=avss}
C {ic_source.sym} 1800 -1080 0 0 {name=XIC}
C {devices/lab_pin.sym} 1580 -1120 0 0 {name=l42 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 1580 -1040 0 0 {name=l43 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 2020 -1080 0 1 {name=l44 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1760 -1240 0 0 {name=l45 sig_type=std_logic lab=avdd_ramp}
C {devices/lab_pin.sym} 1840 -1240 0 1 {name=l46 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 1760 -920 0 0 {name=l47 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1840 -920 0 1 {name=l48 sig_type=std_logic lab=dvss}
C {ramp_simple.sym} 2100 -760 0 0 {name=XRAMP}
C {devices/lab_pin.sym} 1900 -800 0 0 {name=l49 sig_type=std_logic lab=ramp_rst}
C {devices/lab_pin.sym} 1900 -720 0 0 {name=l50 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 2300 -800 0 1 {name=l51 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2100 -600 0 0 {name=l52 sig_type=std_logic lab=avss}
C {atop_cell.sym} 2740 -800 0 0 {name=XC0}
C {devices/lab_pin.sym} 2490 -960 0 0 {name=l53 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 2490 -920 0 0 {name=l54 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2490 -880 0 0 {name=l55 sig_type=std_logic lab=s0_0}
C {devices/lab_pin.sym} 2490 -840 0 0 {name=l56 sig_type=std_logic lab=s1_0}
C {devices/lab_pin.sym} 2490 -800 0 0 {name=l57 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 2490 -760 0 0 {name=l58 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2490 -720 0 0 {name=l59 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2490 -680 0 0 {name=l60 sig_type=std_logic lab=pbias0}
C {devices/lab_pin.sym} 2990 -960 0 1 {name=l61 sig_type=std_logic lab=q0}
C {devices/lab_pin.sym} 2490 -640 0 0 {name=l62 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 2655 -1060 0 0 {name=l63 sig_type=std_logic lab=avdd_c0}
C {devices/lab_pin.sym} 2655 -540 0 0 {name=l64 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 2825 -1060 0 0 {name=l65 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 2825 -540 0 0 {name=l66 sig_type=std_logic lab=dvss}
C {atop_cell.sym} 3360 -800 0 0 {name=XC1}
C {devices/lab_pin.sym} 3110 -960 0 0 {name=l67 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 3110 -920 0 0 {name=l68 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 3110 -880 0 0 {name=l69 sig_type=std_logic lab=s0_1}
C {devices/lab_pin.sym} 3110 -840 0 0 {name=l70 sig_type=std_logic lab=s1_1}
C {devices/lab_pin.sym} 3110 -800 0 0 {name=l71 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 3110 -760 0 0 {name=l72 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 3110 -720 0 0 {name=l73 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 3110 -680 0 0 {name=l74 sig_type=std_logic lab=pbias1}
C {devices/lab_pin.sym} 3610 -960 0 1 {name=l75 sig_type=std_logic lab=q1}
C {devices/lab_pin.sym} 3110 -640 0 0 {name=l76 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 3275 -1060 0 0 {name=l77 sig_type=std_logic lab=avdd_c1}
C {devices/lab_pin.sym} 3275 -540 0 0 {name=l78 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 3445 -1060 0 0 {name=l79 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 3445 -540 0 0 {name=l80 sig_type=std_logic lab=dvss}
C {atop_cell.sym} 3980 -800 0 0 {name=XC2}
C {devices/lab_pin.sym} 3730 -960 0 0 {name=l81 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 3730 -920 0 0 {name=l82 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 3730 -880 0 0 {name=l83 sig_type=std_logic lab=s0_2}
C {devices/lab_pin.sym} 3730 -840 0 0 {name=l84 sig_type=std_logic lab=s1_2}
C {devices/lab_pin.sym} 3730 -800 0 0 {name=l85 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 3730 -760 0 0 {name=l86 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 3730 -720 0 0 {name=l87 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 3730 -680 0 0 {name=l88 sig_type=std_logic lab=pbias2}
C {devices/lab_pin.sym} 4230 -960 0 1 {name=l89 sig_type=std_logic lab=q2}
C {devices/lab_pin.sym} 3730 -640 0 0 {name=l90 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 3895 -1060 0 0 {name=l91 sig_type=std_logic lab=avdd_c2}
C {devices/lab_pin.sym} 3895 -540 0 0 {name=l92 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 4065 -1060 0 0 {name=l93 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 4065 -540 0 0 {name=l94 sig_type=std_logic lab=dvss}
C {atop_cell.sym} 4600 -800 0 0 {name=XC3}
C {devices/lab_pin.sym} 4350 -960 0 0 {name=l95 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 4350 -920 0 0 {name=l96 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 4350 -880 0 0 {name=l97 sig_type=std_logic lab=s0_3}
C {devices/lab_pin.sym} 4350 -840 0 0 {name=l98 sig_type=std_logic lab=s1_3}
C {devices/lab_pin.sym} 4350 -800 0 0 {name=l99 sig_type=std_logic lab=s2_3}
C {devices/lab_pin.sym} 4350 -760 0 0 {name=l100 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 4350 -720 0 0 {name=l101 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 4350 -680 0 0 {name=l102 sig_type=std_logic lab=pbias3}
C {devices/lab_pin.sym} 4850 -960 0 1 {name=l103 sig_type=std_logic lab=q3}
C {devices/lab_pin.sym} 4350 -640 0 0 {name=l104 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 4515 -1060 0 0 {name=l105 sig_type=std_logic lab=avdd_c3}
C {devices/lab_pin.sym} 4515 -540 0 0 {name=l106 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 4685 -1060 0 0 {name=l107 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 4685 -540 0 0 {name=l108 sig_type=std_logic lab=dvss}
C {sample_seq.sym} 3680 40 0 0 {name=XSEQ}
C {devices/lab_pin.sym} 3520 20 0 0 {name=l109 sig_type=std_logic lab=acq}
C {devices/lab_pin.sym} 3520 60 0 0 {name=l110 sig_type=std_logic lab=cnt_clk}
C {devices/lab_pin.sym} 3840 -180 0 1 {name=l111 sig_type=std_logic lab=s2_0}
C {devices/lab_pin.sym} 3840 -140 0 1 {name=l112 sig_type=std_logic lab=s2_1}
C {devices/lab_pin.sym} 3840 -100 0 1 {name=l113 sig_type=std_logic lab=s2_2}
C {devices/lab_pin.sym} 3840 -60 0 1 {name=l114 sig_type=std_logic lab=s2_3}
C {devices/lab_pin.sym} 3840 -20 0 1 {name=l115 sig_type=std_logic lab=s0_0}
C {devices/lab_pin.sym} 3840 20 0 1 {name=l116 sig_type=std_logic lab=s0_1}
C {devices/lab_pin.sym} 3840 60 0 1 {name=l117 sig_type=std_logic lab=s0_2}
C {devices/lab_pin.sym} 3840 100 0 1 {name=l118 sig_type=std_logic lab=s0_3}
C {devices/lab_pin.sym} 3840 140 0 1 {name=l119 sig_type=std_logic lab=s1_0}
C {devices/lab_pin.sym} 3840 180 0 1 {name=l120 sig_type=std_logic lab=s1_1}
C {devices/lab_pin.sym} 3840 220 0 1 {name=l121 sig_type=std_logic lab=s1_2}
C {devices/lab_pin.sym} 3840 260 0 1 {name=l122 sig_type=std_logic lab=s1_3}
C {devices/lab_pin.sym} 3680 -280 0 1 {name=l123 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 3680 360 0 1 {name=l124 sig_type=std_logic lab=dvss}
C {devices/title.sym} 40 -120 0 0 {name=l999 author="ASIC R&D - mixed_signal/Analog_top - analog_top"}
