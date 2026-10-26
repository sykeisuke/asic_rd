v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {top plate: S0 / S1 side
(driven: vfe, then vramp)} 1150 -900 0 0 0.36 0.36 {layer=13}
T {XCS  MIM 5 x 5 um
54.52 fF = 1.99 fF/um2 x 25 um2
+ 0.238 fF/um x 20 um fringe
(PDK formula, typical)} 1150 -700 0 0 0.36 0.36 {layer=13}
T {bot plate: S2 + comparator inn
(floats from S2 opening to the
end of conversion)} 1150 -470 0 0 0.36 0.36 {layer=13}
T {ibias: icmp_k from bias_gen_s
(3.25 uA sink, design) into the
diode XREFP inside comparator_d} 1700 -790 0 0 0.36 0.36 {layer=13}
T {std-cell flip-flop dfxtn_2 (as_sc_mcu7t3v3)
on dvdd: q falls at the first FALLING
clk edge after dout falls} 1940 -400 0 0 0.36 0.36 {layer=13}
T {complements s0b / s1b / s2b:
P 0.88 / N 0.44 um, L 0.28 um} 250 -170 0 0 0.36 0.36 {layer=13}
T {ATOP_CELL  -  one sampling / conversion cell of analog_top (8-bit true bottom-plate single-slope ADC)} 40 -1560 0 0 0.8 0.8 {}
T {TRACK    S0 and S2 closed: top = vfe (the input), bot = vref (VDD/2). The comparator sits at its trip point.
SAMPLE   S2 opens at TS_k: the charge on C_S is frozen (the sampling instant, the bottom-plate edge).
         S0 opens TNOV = 5 ns later (top isolated), S1 closes after another 5 ns: top = vramp = vrlo.
CONVERT  vramp rises 0.5 -> 2.0 V in 12.8 us; bot follows top by alpha = C_S / (C_S + C_bot) and crosses
         vbl when vramp = vin: dout falls (comparator delay ~6.5 ns), q falls at the next falling cnt_clk edge.
Switches (sw_sN.sch, = ref/switches.spice): S0, S1 TG N 0.5 / P 1.0 um, S2 NMOS 0.36 um, L 0.28 um.} 40 -1480 0 0 0.42 0.42 {}
L 4 250 -1120 640 -1120 {dash=6}
L 4 640 -1120 640 -200 {dash=6}
L 4 640 -200 250 -200 {dash=6}
L 4 250 -200 250 -1120 {dash=6}
T {S0/S1/S2 COMPLEMENTS} 260 -1112 0 0 0.5 0.5 {layer=4}
L 4 700 -1120 1360 -1120 {dash=6}
L 4 1360 -1120 1360 -200 {dash=6}
L 4 1360 -200 700 -200 {dash=6}
L 4 700 -200 700 -1120 {dash=6}
T {SWITCHES + HOLD CAP} 710 -1112 0 0 0.5 0.5 {layer=4}
L 4 1380 -1120 2300 -1120 {dash=6}
L 4 2300 -1120 2300 -200 {dash=6}
L 4 2300 -200 1380 -200 {dash=6}
L 4 1380 -200 1380 -1120 {dash=6}
T {COMPARATOR (comparator_d) + LATCH} 1390 -1112 0 0 0.5 0.5 {layer=4}
N 40 -1000 80 -1000 {lab=vfe}
N 40 -950 80 -950 {lab=vramp}
N 40 -900 80 -900 {lab=s0}
N 40 -850 80 -850 {lab=s1}
N 40 -800 80 -800 {lab=s2}
N 40 -750 80 -750 {lab=vref}
N 40 -700 80 -700 {lab=vbl}
N 40 -650 80 -650 {lab=ibias}
N 40 -600 80 -600 {lab=q}
N 40 -550 80 -550 {lab=clk}
N 40 -500 80 -500 {lab=vdd}
N 40 -450 80 -450 {lab=vss}
N 40 -400 80 -400 {lab=dvdd}
N 40 -350 80 -350 {lab=dvss}
N 400 -990 400 -960 {lab=s0b}
N 400 -960 400 -930 {lab=s0b}
N 400 -960 460 -960 {lab=s0b}
N 340 -1020 360 -1020 {lab=s0}
N 340 -1020 340 -960 {lab=s0}
N 340 -960 340 -900 {lab=s0}
N 340 -900 360 -900 {lab=s0}
N 300 -960 340 -960 {lab=s0}
N 400 -1070 400 -1050 {lab=vdd}
N 400 -1020 430 -1020 {lab=vdd}
N 400 -870 400 -850 {lab=vss}
N 400 -900 430 -900 {lab=vss}
N 400 -690 400 -660 {lab=s1b}
N 400 -660 400 -630 {lab=s1b}
N 400 -660 460 -660 {lab=s1b}
N 340 -720 360 -720 {lab=s1}
N 340 -720 340 -660 {lab=s1}
N 340 -660 340 -600 {lab=s1}
N 340 -600 360 -600 {lab=s1}
N 300 -660 340 -660 {lab=s1}
N 400 -770 400 -750 {lab=vdd}
N 400 -720 430 -720 {lab=vdd}
N 400 -570 400 -550 {lab=vss}
N 400 -600 430 -600 {lab=vss}
N 400 -390 400 -360 {lab=s2b}
N 400 -360 400 -330 {lab=s2b}
N 400 -360 460 -360 {lab=s2b}
N 340 -420 360 -420 {lab=s2}
N 340 -420 340 -360 {lab=s2}
N 340 -360 340 -300 {lab=s2}
N 340 -300 360 -300 {lab=s2}
N 300 -360 340 -360 {lab=s2}
N 400 -470 400 -450 {lab=vdd}
N 400 -420 430 -420 {lab=vdd}
N 400 -270 400 -250 {lab=vss}
N 400 -300 430 -300 {lab=vss}
N 750 -420 800 -420 {lab=vref}
N 880 -510 880 -480 {lab=s2}
N 920 -510 920 -480 {lab=s2b}
N 880 -360 880 -330 {lab=vdd}
N 920 -360 920 -330 {lab=vss}
N 750 -940 800 -940 {lab=vfe}
N 880 -1030 880 -1000 {lab=s0}
N 920 -1030 920 -1000 {lab=s0b}
N 880 -880 880 -850 {lab=vdd}
N 920 -880 920 -850 {lab=vss}
N 750 -720 800 -720 {lab=vramp}
N 880 -810 880 -780 {lab=s1}
N 920 -810 920 -780 {lab=s1b}
N 880 -660 880 -630 {lab=vdd}
N 920 -660 920 -630 {lab=vss}
N 1000 -940 1120 -940 {lab=top}
N 1120 -940 1120 -720 {lab=top}
N 1120 -720 1120 -650 {lab=top}
N 1000 -720 1120 -720 {lab=top}
N 1120 -590 1120 -500 {lab=bot}
N 1120 -500 1120 -420 {lab=bot}
N 1000 -420 1120 -420 {lab=bot}
N 1120 -500 1500 -500 {lab=bot}
N 1440 -580 1500 -580 {lab=vbl}
N 1580 -720 1580 -660 {lab=ibias}
N 1640 -690 1640 -660 {lab=vdd}
N 1640 -420 1640 -390 {lab=vss}
N 1740 -540 1800 -540 {lab=dout}
N 1800 -540 1960 -540 {lab=dout}
N 1910 -500 1960 -500 {lab=clk}
N 2160 -540 2220 -540 {lab=q}
N 2060 -630 2060 -600 {lab=dvdd}
N 2060 -440 2060 -410 {lab=dvss}
C {devices/ipin.sym} 40 -1000 0 0 {name=p_vfe lab=vfe sim_pinnumber=1}
C {devices/lab_pin.sym} 80 -1000 0 1 {name=l1 sig_type=std_logic lab=vfe}
C {devices/ipin.sym} 40 -950 0 0 {name=p_vramp lab=vramp sim_pinnumber=2}
C {devices/lab_pin.sym} 80 -950 0 1 {name=l2 sig_type=std_logic lab=vramp}
C {devices/ipin.sym} 40 -900 0 0 {name=p_s0 lab=s0 sim_pinnumber=3}
C {devices/lab_pin.sym} 80 -900 0 1 {name=l3 sig_type=std_logic lab=s0}
C {devices/ipin.sym} 40 -850 0 0 {name=p_s1 lab=s1 sim_pinnumber=4}
C {devices/lab_pin.sym} 80 -850 0 1 {name=l4 sig_type=std_logic lab=s1}
C {devices/ipin.sym} 40 -800 0 0 {name=p_s2 lab=s2 sim_pinnumber=5}
C {devices/lab_pin.sym} 80 -800 0 1 {name=l5 sig_type=std_logic lab=s2}
C {devices/ipin.sym} 40 -750 0 0 {name=p_vref lab=vref sim_pinnumber=6}
C {devices/lab_pin.sym} 80 -750 0 1 {name=l6 sig_type=std_logic lab=vref}
C {devices/ipin.sym} 40 -700 0 0 {name=p_vbl lab=vbl sim_pinnumber=7}
C {devices/lab_pin.sym} 80 -700 0 1 {name=l7 sig_type=std_logic lab=vbl}
C {devices/ipin.sym} 40 -650 0 0 {name=p_ibias lab=ibias sim_pinnumber=8}
C {devices/lab_pin.sym} 80 -650 0 1 {name=l8 sig_type=std_logic lab=ibias}
C {devices/opin.sym} 40 -600 0 1 {name=p_q lab=q sim_pinnumber=9}
C {devices/lab_pin.sym} 80 -600 0 1 {name=l9 sig_type=std_logic lab=q}
C {devices/ipin.sym} 40 -550 0 0 {name=p_clk lab=clk sim_pinnumber=10}
C {devices/lab_pin.sym} 80 -550 0 1 {name=l10 sig_type=std_logic lab=clk}
C {devices/iopin.sym} 40 -500 0 1 {name=p_vdd lab=vdd sim_pinnumber=11}
C {devices/lab_pin.sym} 80 -500 0 1 {name=l11 sig_type=std_logic lab=vdd}
C {devices/iopin.sym} 40 -450 0 1 {name=p_vss lab=vss sim_pinnumber=12}
C {devices/lab_pin.sym} 80 -450 0 1 {name=l12 sig_type=std_logic lab=vss}
C {devices/iopin.sym} 40 -400 0 1 {name=p_dvdd lab=dvdd sim_pinnumber=13}
C {devices/lab_pin.sym} 80 -400 0 1 {name=l13 sig_type=std_logic lab=dvdd}
C {devices/iopin.sym} 40 -350 0 1 {name=p_dvss lab=dvss sim_pinnumber=14}
C {devices/lab_pin.sym} 80 -350 0 1 {name=l14 sig_type=std_logic lab=dvss}
C {symbols/pfet_03v3.sym} 380 -1020 0 0 {name=XI0P
L=0.28u
W=0.88u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 380 -900 0 0 {name=XI0N
L=0.28u
W=0.44u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 460 -960 0 1 {name=l15 sig_type=std_logic lab=s0b}
C {devices/lab_pin.sym} 300 -960 0 0 {name=l16 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 400 -1070 0 0 {name=l17 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 430 -1020 0 1 {name=l18 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 -850 0 0 {name=l19 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 430 -900 0 1 {name=l20 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 380 -720 0 0 {name=XI1P
L=0.28u
W=0.88u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 380 -600 0 0 {name=XI1N
L=0.28u
W=0.44u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 460 -660 0 1 {name=l21 sig_type=std_logic lab=s1b}
C {devices/lab_pin.sym} 300 -660 0 0 {name=l22 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 400 -770 0 0 {name=l23 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 430 -720 0 1 {name=l24 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 -550 0 0 {name=l25 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 430 -600 0 1 {name=l26 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 380 -420 0 0 {name=XI2P
L=0.28u
W=0.88u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 380 -300 0 0 {name=XI2N
L=0.28u
W=0.44u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 460 -360 0 1 {name=l27 sig_type=std_logic lab=s2b}
C {devices/lab_pin.sym} 300 -360 0 0 {name=l28 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 400 -470 0 0 {name=l29 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 430 -420 0 1 {name=l30 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 400 -250 0 0 {name=l31 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 430 -300 0 1 {name=l32 sig_type=std_logic lab=vss}
C {sw_s2.sym} 900 -420 0 0 {name=XS2}
C {devices/lab_pin.sym} 750 -420 0 0 {name=l33 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 880 -510 0 0 {name=l34 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 920 -510 0 1 {name=l35 sig_type=std_logic lab=s2b}
C {devices/lab_pin.sym} 880 -330 0 0 {name=l36 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 -330 0 1 {name=l37 sig_type=std_logic lab=vss}
C {sw_s0.sym} 900 -940 0 0 {name=XS0}
C {devices/lab_pin.sym} 750 -940 0 0 {name=l38 sig_type=std_logic lab=vfe}
C {devices/lab_pin.sym} 880 -1030 0 0 {name=l39 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 920 -1030 0 1 {name=l40 sig_type=std_logic lab=s0b}
C {devices/lab_pin.sym} 880 -850 0 0 {name=l41 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 -850 0 1 {name=l42 sig_type=std_logic lab=vss}
C {sw_s1.sym} 900 -720 0 0 {name=XS1}
C {devices/lab_pin.sym} 750 -720 0 0 {name=l43 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 880 -810 0 0 {name=l44 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 920 -810 0 1 {name=l45 sig_type=std_logic lab=s1b}
C {devices/lab_pin.sym} 880 -630 0 0 {name=l46 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 920 -630 0 1 {name=l47 sig_type=std_logic lab=vss}
C {symbols/cap_mim_2f0fF.sym} 1120 -620 2 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {comparator_d.sym} 1620 -540 0 0 {name=XCMP}
C {devices/lab_pin.sym} 1440 -580 0 0 {name=l48 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1580 -720 0 0 {name=l49 sig_type=std_logic lab=ibias}
C {devices/lab_pin.sym} 1640 -690 0 0 {name=l50 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1640 -390 0 0 {name=l51 sig_type=std_logic lab=vss}
C {latch.sym} 2060 -520 0 0 {name=XFF}
C {devices/lab_pin.sym} 1800 -540 0 1 {name=l52 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1910 -500 0 0 {name=l53 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2220 -540 0 1 {name=l54 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 2060 -630 0 0 {name=l55 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 2060 -410 0 0 {name=l56 sig_type=std_logic lab=dvss}
C {devices/lab_pin.sym} 1120 -940 0 1 {name=l57 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1120 -420 0 1 {name=l58 sig_type=std_logic lab=bot}
C {devices/title.sym} 40 0 0 0 {name=l999 author="ASIC R&D - mixed_signal/Analog_top - atop_cell"}
