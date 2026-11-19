v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -180 -20 -80 -20 {}
N 80 -20 120 -20 {}
N 120 -20 120 420 {}
N 120 -20 170 -20 {}
N 120 420 440 420 {}
N 170 -20 180 -20 {}
N 340 -20 430 -20 {}
N 380 20 380 160 {}
N 380 20 440 20 {}
N 380 160 1460 160 {}
N 380 240 380 380 {}
N 380 240 1460 240 {}
N 380 380 440 380 {}
N 430 -20 440 -20 {}
N 600 0 690 0 {}
N 600 400 690 400 {}
N 690 0 700 0 {}
N 690 400 700 400 {}
N 860 0 950 0 {}
N 900 400 990 400 {}
N 950 0 960 0 {}
N 990 400 1000 400 {}
N 1120 0 1210 0 {}
N 1160 400 1250 400 {}
N 1210 0 1220 0 {}
N 1250 400 1260 400 {}
N 1380 0 1470 0 {}
N 1420 400 1510 400 {}
N 1460 160 1540 240 {}
N 1460 240 1540 160 {}
N 1470 0 1480 0 {}
N 1510 400 1520 400 {}
N 1540 160 2560 160 {}
N 1540 240 2860 240 {}
N 1640 0 1690 0 {}
N 1680 400 1770 400 {}
N 1690 -120 1690 0 {}
N 1690 -120 2580 -120 {}
N 1690 0 1730 0 {}
N 1730 0 1740 0 {}
N 1770 400 1780 400 {}
N 1900 0 1950 0 {}
N 1940 400 2030 400 {}
N 1950 -200 1950 0 {}
N 1950 -200 3440 -200 {}
N 1950 0 1990 0 {}
N 1990 0 2000 0 {}
N 2030 400 2040 400 {}
N 2200 0 2290 0 {}
N 2200 400 2250 400 {}
N 2250 400 2250 600 {}
N 2250 400 2290 400 {}
N 2250 600 3440 600 {}
N 2290 0 2300 0 {}
N 2290 400 2300 400 {}
N 2460 0 2560 0 {}
N 2500 400 2590 400 {}
N 2560 0 2560 160 {}
N 2560 0 2650 0 {}
N 2580 -120 2600 -120 {}
N 2590 400 2600 400 {}
N 2600 -120 2600 -40 {}
N 2600 -40 2660 -40 {}
N 2650 0 2660 0 {}
N 2760 400 2850 400 {}
N 2820 -20 2910 -20 {}
N 2850 400 2860 400 {}
N 2860 240 2860 400 {}
N 2910 -20 2920 -20 {}
N 3080 -20 3170 -20 {}
N 3170 -20 3180 -20 {}
N 3340 -20 3440 -20 {}
T {SEQ_CLKGEN  -  two-phase non-overlapping clock generator with early phases} -200 -440 0 0 0.70 0.70 {}
T {layout: phase-1 row over phase-2 row, the three delay stages identical} -200 -380 0 0 0.40 0.40 {}
C {devices/ipin.sym} -180 -20 0 0 {name=p_clkin lab=clkin sim_pinnumber=1}
C {seq_g_inv_2.sym} 0 -20 0 0 {name=XI1 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 170 -20 0 0 {name=l1 sig_type=std_logic lab=clkinb}
C {seq_g_inv_2.sym} 260 -20 0 0 {name=XI2 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 430 -20 0 0 {name=l2 sig_type=std_logic lab=clkinbb}
C {seq_g_nand2_2.sym} 520 0 0 0 {name=XN1 VDD=vdd VSS=vss}
C {seq_g_inv_4.sym} 780 0 0 0 {name=XI3 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 950 0 0 0 {name=l3 sig_type=std_logic lab=m1}
C {seq_g_inv_4.sym} 1040 0 0 0 {name=XI5 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1210 0 0 0 {name=l4 sig_type=std_logic lab=m2}
C {seq_g_inv_4.sym} 1300 0 0 0 {name=XI7 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1470 0 0 0 {name=l5 sig_type=std_logic lab=m3}
C {seq_g_inv_4.sym} 1560 0 0 0 {name=XI9 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1730 0 0 0 {name=l6 sig_type=std_logic lab=a1}
C {seq_g_inv_4.sym} 1820 0 0 0 {name=XI11 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1990 0 0 0 {name=l7 sig_type=std_logic lab=p1e}
C {seq_dly.sym} 2100 0 0 0 {name=XL1}
C {devices/lab_pin.sym} 2100 -60 0 0 {name=l8 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2100 60 0 0 {name=l9 sig_type=std_logic lab=vss}
C {seq_lab_wire.sym} 2290 0 0 0 {name=l10 sig_type=std_logic lab=x1}
C {seq_g_inv_4.sym} 2380 0 0 0 {name=XI13 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 690 0 0 0 {name=l11 sig_type=std_logic lab=n1}
C {seq_g_nand2_2.sym} 2740 -20 0 0 {name=XN3 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 2650 0 0 0 {name=l12 sig_type=std_logic lab=b1}
C {seq_lab_wire.sym} 2580 -120 0 0 {name=l13 sig_type=std_logic lab=a1}
C {devices/opin.sym} 3440 -200 0 0 {name=p_p1e lab=p1e sim_pinnumber=2}
C {seq_g_inv_4.sym} 3000 -20 0 0 {name=XI15 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 3170 -20 0 0 {name=l14 sig_type=std_logic lab=y1b}
C {seq_g_inv_8.sym} 3260 -20 0 0 {name=XI17 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 2910 -20 0 0 {name=l15 sig_type=std_logic lab=y1}
C {devices/opin.sym} 3440 -20 0 0 {name=p_p1 lab=p1 sim_pinnumber=3}
C {seq_g_nand2_2_ba.sym} 520 400 0 0 {name=XN2 VDD=vdd VSS=vss}
C {seq_dly.sym} 800 400 0 0 {name=XL2}
C {devices/lab_pin.sym} 800 340 0 0 {name=l16 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 800 460 0 0 {name=l17 sig_type=std_logic lab=vss}
C {seq_lab_wire.sym} 990 400 0 0 {name=l18 sig_type=std_logic lab=n2d}
C {seq_g_inv_4.sym} 1080 400 0 0 {name=XI4 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1250 400 0 0 {name=l19 sig_type=std_logic lab=k1}
C {seq_g_inv_4.sym} 1340 400 0 0 {name=XI6 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1510 400 0 0 {name=l20 sig_type=std_logic lab=k2}
C {seq_g_inv_4.sym} 1600 400 0 0 {name=XI8 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 1770 400 0 0 {name=l21 sig_type=std_logic lab=k3}
C {seq_g_inv_4.sym} 1860 400 0 0 {name=XI10 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 2030 400 0 0 {name=l22 sig_type=std_logic lab=a2}
C {seq_g_inv_4.sym} 2120 400 0 0 {name=XI12 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 2290 400 0 0 {name=l23 sig_type=std_logic lab=p2e}
C {seq_dly.sym} 2400 400 0 0 {name=XL3}
C {devices/lab_pin.sym} 2400 340 0 0 {name=l24 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2400 460 0 0 {name=l25 sig_type=std_logic lab=vss}
C {seq_lab_wire.sym} 2590 400 0 0 {name=l26 sig_type=std_logic lab=x2}
C {seq_g_inv_4.sym} 2680 400 0 0 {name=XI14 VDD=vdd VSS=vss}
C {seq_lab_wire.sym} 690 400 0 0 {name=l27 sig_type=std_logic lab=n2}
C {devices/opin.sym} 3440 600 0 0 {name=p_p2e lab=p2e sim_pinnumber=4}
C {seq_lab_wire.sym} 2850 400 0 0 {name=l28 sig_type=std_logic lab=b2}
C {devices/iopin.sym} -180 560 0 0 {name=p_vdd lab=vdd sim_pinnumber=5}
C {devices/iopin.sym} -180 600 0 0 {name=p_vss lab=vss sim_pinnumber=6}
