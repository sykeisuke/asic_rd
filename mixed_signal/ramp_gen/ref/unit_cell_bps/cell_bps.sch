v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {cell_bps -- the unit cell proper: .subckt unit_cell_bps of mixed_signal/Analog_top_bkp/unit_cell_bps/unit_cell_bps.spice.
XI0N/XI0P, XI1N/XI1P, XI2N/XI2P: minimum inverters making s0b/s1b/s2b (controls are 0/VDD, HIGH = closed).
XS0 vfe->bot, XS1 vramp->bot (TGs, sw_s0/sw_s1), XS2 vref->top (single NMOS, sw_s2) from switches.spice.
XCS: 5 x 5 um MIM = 54.52 fF, top = comparator side. RLKT/RLKB: DC paths for the floating plates.
XCMP: cmp_updt (inp = vbl, inn = top). Netlists back to the deck: run.sh phase schematic.} 100 -900 0 0 0.3 0.3 {}
T {control inverters} 200 -720 0 0 0.35 0.35 {layer=13}
T {switches and hold capacitor} 900 -720 0 0 0.35 0.35 {layer=13}
T {comparator} 1900 -720 0 0 0.35 0.35 {layer=13}
C {devices/ipin.sym} 100 -600 0 0 {name=p1 lab=vfe}
C {devices/ipin.sym} 100 -570 0 0 {name=p2 lab=vramp}
C {devices/ipin.sym} 100 -540 0 0 {name=p3 lab=s0}
C {devices/ipin.sym} 100 -510 0 0 {name=p4 lab=s1}
C {devices/ipin.sym} 100 -480 0 0 {name=p5 lab=s2}
C {devices/ipin.sym} 100 -450 0 0 {name=p6 lab=vref}
C {devices/ipin.sym} 100 -420 0 0 {name=p7 lab=vbl}
C {devices/opin.sym} 100 -390 0 0 {name=p8 lab=dout}
C {devices/ipin.sym} 100 -360 0 0 {name=p9 lab=clk}
C {devices/ipin.sym} 100 -330 0 0 {name=p10 lab=pbias}
C {devices/ipin.sym} 100 -300 0 0 {name=p11 lab=nbias}
C {devices/iopin.sym} 100 -270 0 0 {name=p12 lab=vdd}
C {devices/iopin.sym} 100 -240 0 0 {name=p13 lab=vss}
C {symbols/pfet_03v3.sym} 300 -600 0 0 {name=XI0P
L=0.28u
W=0.88u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 320 -570 0 1 {name=l1 sig_type=std_logic lab=s0b}
C {devices/lab_pin.sym} 280 -600 0 0 {name=l2 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 320 -630 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 320 -600 0 1 {name=l4 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 300 -400 0 0 {name=XI0N
L=0.28u
W=0.44u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 320 -430 0 1 {name=l5 sig_type=std_logic lab=s0b}
C {devices/lab_pin.sym} 280 -400 0 0 {name=l6 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 320 -370 0 1 {name=l7 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 320 -400 0 1 {name=l8 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 500 -600 0 0 {name=XI1P
L=0.28u
W=0.88u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 520 -570 0 1 {name=l9 sig_type=std_logic lab=s1b}
C {devices/lab_pin.sym} 480 -600 0 0 {name=l10 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 520 -630 0 1 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 520 -600 0 1 {name=l12 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 500 -400 0 0 {name=XI1N
L=0.28u
W=0.44u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 520 -430 0 1 {name=l13 sig_type=std_logic lab=s1b}
C {devices/lab_pin.sym} 480 -400 0 0 {name=l14 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 520 -370 0 1 {name=l15 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 520 -400 0 1 {name=l16 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 700 -600 0 0 {name=XI2P
L=0.28u
W=0.88u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 720 -570 0 1 {name=l17 sig_type=std_logic lab=s2b}
C {devices/lab_pin.sym} 680 -600 0 0 {name=l18 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 720 -630 0 1 {name=l19 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 720 -600 0 1 {name=l20 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 700 -400 0 0 {name=XI2N
L=0.28u
W=0.44u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 720 -430 0 1 {name=l21 sig_type=std_logic lab=s2b}
C {devices/lab_pin.sym} 680 -400 0 0 {name=l22 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 720 -370 0 1 {name=l23 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 -400 0 1 {name=l24 sig_type=std_logic lab=vss}
C {sw_blk.sym} 1000 -600 0 0 {name=XS0 model=sw_s0}
C {devices/lab_pin.sym} 920 -620 0 0 {name=l25 sig_type=std_logic lab=vfe}
C {devices/lab_pin.sym} 1080 -620 0 1 {name=l26 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 980 -660 0 0 {name=l27 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 1020 -660 0 1 {name=l28 sig_type=std_logic lab=s0b}
C {devices/lab_pin.sym} 980 -540 0 0 {name=l29 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1020 -540 0 1 {name=l30 sig_type=std_logic lab=vss}
C {sw_blk.sym} 1000 -380 0 0 {name=XS1 model=sw_s1}
C {devices/lab_pin.sym} 920 -400 0 0 {name=l31 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1080 -400 0 1 {name=l32 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 980 -440 0 0 {name=l33 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 1020 -440 0 1 {name=l34 sig_type=std_logic lab=s1b}
C {devices/lab_pin.sym} 980 -320 0 0 {name=l35 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1020 -320 0 1 {name=l36 sig_type=std_logic lab=vss}
C {sw_blk.sym} 1500 -600 0 0 {name=XS2 model=sw_s2}
C {devices/lab_pin.sym} 1420 -620 0 0 {name=l37 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 1580 -620 0 1 {name=l38 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1480 -660 0 0 {name=l39 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 1520 -660 0 1 {name=l40 sig_type=std_logic lab=s2b}
C {devices/lab_pin.sym} 1480 -540 0 0 {name=l41 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1520 -540 0 1 {name=l42 sig_type=std_logic lab=vss}
C {symbols/cap_mim_2f0fF.sym} 1300 -480 0 0 {name=XCS W=5u L=5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 1300 -450 0 1 {name=l43 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 1300 -510 0 1 {name=l44 sig_type=std_logic lab=top}
C {devices/res.sym} 1200 -220 0 0 {name=RLKB value=1e15 footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 1200 -250 0 1 {name=l45 sig_type=std_logic lab=bot}
C {devices/lab_pin.sym} 1200 -190 0 1 {name=l46 sig_type=std_logic lab=vss}
C {devices/res.sym} 1500 -220 0 0 {name=RLKT value=1e15 footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 1500 -250 0 1 {name=l47 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 1500 -190 0 1 {name=l48 sig_type=std_logic lab=vss}
C {cmp_blk.sym} 2000 -400 0 0 {name=XCMP model=cmp}
C {devices/lab_pin.sym} 1900 -460 0 0 {name=l49 sig_type=std_logic lab=vbl}
C {devices/lab_pin.sym} 1900 -430 0 0 {name=l50 sig_type=std_logic lab=top}
C {devices/lab_pin.sym} 2100 -445 0 1 {name=l51 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1900 -400 0 0 {name=l52 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2000 -520 0 1 {name=l53 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 2000 -280 0 1 {name=l54 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1900 -370 0 0 {name=l55 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1900 -340 0 0 {name=l56 sig_type=std_logic lab=pbias}
