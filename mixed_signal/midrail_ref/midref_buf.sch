v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {MIDREF_BUF  -  FVF CLASS-AB VDD/2 BUFFER (VREF = VBL of the 8-bit cell, ONE output)} 40 -1500 0 0 0.75 0.75 {}
T {WHAT  Unity-gain class-AB buffer: copies the VDD/2 tap (vin) to out with a low output impedance.
      ONE instance drives VREF and VBL of the 8-bit bottom-plate cell (one node; midref, 2026-10-13).
PINS  vin: divider tap (1.650 V at the bench).   out: VREF = VBL (1.6460 V), MIM XCD to vss.
      ib: bias current IN, 12.36 uA into the NMOS diode XMBN at the bench (in analog_top: bias_gen_s ivref).
      vdd / vss: 3.3 V analog supply (AVDD); 78.87 uA from vdd at the bench (one buffer + its own divider + ib).
CORE  Flipped voltage followers M1 (PMOS) / M4 (NMOS) set p = vin + VSG1 and n = vin - VGS4; shunts M3 / M6
      close the FVF loops; output diodes M2 / M5 (= 1 x M1 / M4) between p and n make out = vin.
      XMIB / XMIT are the follower bias sources (IB), mirrored from ib through XMBN / XMBN2 / XMBP.
CHOICES  every L 0.34-0.36 um; one finger width per flavour (PMOS 2 um, NMOS 0.5 um); whole fingers, gm/Id-sampled
      search, knee of the power x area front. The power is set by follower headroom at ff / 85 C / 3.6 V:
      at short L the shunts need about 30 uA each for their VGS (accepted by the user).
DECISION  ADR 0016 (sizing), ADR 0021 (one output).   REPRODUCE  ./scripts/sim.sh midrail-ref  (make midrail-ref)
NETLIST  midref.spice: midref_v2's devices (size_v2.py), one buffer; these drawings by midref_sch.py.} 60 -1410 0 0 0.42 0.42 {}
T {VALUES ON THIS SHEET (layer-4 tags): ngspice at the block's OWN bench bias,
midref (the buffer + its divider), typical / 27 C / 3.3 V, ideal ib = i_f
(verify_v3.py opdev -> data/op_devices.csv, op_passives.csv).
R and C: PDK-model replicas (R = 1.65 V / I; C from the AC current at 1 MHz).
gm/Id in 1/V, of the BSIM4 instance. In analog_top ib comes from bias_gen_s
at 0.90 x i_f, so in-macro Id and gm/Id differ: measured there, not here.} 1500 -1410 0 0 0.36 0.36 {layer=8}
B 4 40 -1425 2420 -1040 {fill=false dash=4}
T {XMBN (diode)
Id 12.36 uA
gm/Id 4.6} 172 -400 0 0 0.36 0.36 {layer=4}
T {XMBN2
Id 13.96 uA
gm/Id 4.3} 392 -112 0 0 0.36 0.36 {layer=4}
T {XMBP (diode)
Id 13.96 uA
gm/Id 5.2} 392 -722 0 0 0.36 0.36 {layer=4}
T {XM1 follower
Id 13.69 uA
gm/Id 17.3} 752 -800 0 0 0.36 0.36 {layer=4}
T {XMIB (IB)
Id 13.69 uA
gm/Id 4.4} 752 -532 0 0 0.36 0.36 {layer=4}
T {XMIT (IB)
Id 14.99 uA
gm/Id 5.1} 752 -312 0 0 0.36 0.36 {layer=4}
T {XM4 follower
Id 14.99 uA
gm/Id 16.4} 752 -205 0 0 0.36 0.36 {layer=4}
T {XM3 shunt
Id 29.47 uA
gm/Id 3.1} 1300 -805 0 0 0.36 0.36 {layer=4}
T {XM2 out diode
Id 15.79 uA
gm/Id 16.8} 1300 -705 0 0 0.36 0.36 {layer=4}
T {XM5 out diode
Id 15.79 uA
gm/Id 16.2} 1300 -240 0 0 0.36 0.36 {layer=4}
T {XM6 shunt
Id 30.78 uA
gm/Id 2.3} 1300 -150 0 0 0.36 0.36 {layer=4}
T {C = 283.6 fF  (card 283.6 fF)} 1275 -298 0 0 0.36 0.36 {layer=4}
T {DEVICE OPERATING POINT AT THE BENCH BIAS} 1560 -940 0 0 0.5 0.5 {layer=8}
T {typical / 27 C / 3.3 V, ideal ib, ngspice (verify_v3.py opdev -> data/op_devices.csv, op_passives.csv)} 1560 -906 0 0 0.32 0.32 {}
T {device
XMBN
XMBN2
XMBP
XMIB
XMIT
XM1
XM4
XM3
XM6
XM2
XM5} 1560 -860 0 0 0.36 0.36 {}
T {role
bias diode (ib)
bias mirror
bias PMOS diode
IB source, PMOS follower
IB source, NMOS follower
PMOS follower
NMOS follower
PMOS shunt
NMOS shunt
PMOS output diode
NMOS output diode} 1660 -860 0 0 0.36 0.36 {layer=4}
T {Id
12.356 uA
13.962 uA
13.965 uA
13.685 uA
14.990 uA
13.686 uA
14.990 uA
29.472 uA
30.776 uA
15.786 uA
15.786 uA} 1960 -860 0 0 0.36 0.36 {layer=4}
T {gm/Id
4.56
4.34
5.16
4.38
5.08
17.27
16.36
3.07
2.32
16.81
16.18} 2070 -860 0 0 0.36 0.36 {layer=4}
T {|Vgs|
1.000 V
1.000 V
1.089 V
1.000 V
1.089 V
0.999 V
0.865 V
1.313 V
1.312 V
1.003 V
0.861 V} 2160 -860 0 0 0.36 0.36 {layer=4}
T {|Vds|
1.000 V
2.211 V
1.089 V
1.987 V
1.988 V
0.662 V
0.526 V
0.651 V
0.785 V
1.003 V
0.861 V} 2260 -860 0 0 0.36 0.36 {layer=4}
T {Vdsat
0.317 V
0.325 V
0.328 V
0.323 V
0.332 V
0.097 V
0.090 V
0.498 V
0.509 V
0.101 V
0.090 V} 2360 -860 0 0 0.36 0.36 {layer=4}
T {PASSIVES AND NODES (PDK model, ngspice)} 1560 -574 0 0 0.5 0.5 {layer=8}
T {XCD (out-vss)  cap_mim_2f0 11.7u x 11.7u: 283.6 fF
   card check: 1.99 fF/um2 x 136.9 um2 + 0.2383 fF/um x 46.8 um = 283.6 fF
nodes: p 2.649 V, n 0.785 V, out - vin -3.98 mV
divider (XRT / XRB, XCT): see midref_div.sch} 1560 -534 0 0 0.36 0.36 {layer=4}
T {BIAS} 60 -980 0 0 0.4 0.4 {}
T {ib -> diode XMBN -> XMBN2 -> diode XMBP} 60 -950 0 0 0.25 0.25 {}
T {INPUT FOLLOWERS + IB} 760 -980 0 0 0.4 0.4 {}
T {M1 / M4 follow vin; XMIB / XMIT = IB} 760 -950 0 0 0.25 0.25 {}
T {SHUNTS + OUTPUT} 1080 -980 0 0 0.4 0.4 {}
T {M3 / M6 shunt; M2 / M5 = 1 x M1 / M4} 1080 -950 0 0 0.25 0.25 {}
T {IB} 790 -605 0 0 0.35 0.35 {layer=8}
T {IB} 790 -365 0 0 0.35 0.35 {layer=8}
T {p = vin + VSG1} 1190 -735 0 0 0.25 0.25 {layer=8}
T {n = vin - VGS4} 1190 -195 0 0 0.25 0.25 {layer=8}
L 4 715 -1000 715 20 {dash=6}
N 40 -450 160 -450 {lab=ib}
N 160 -450 160 -220 {lab=ib}
N 160 -220 160 -170 {lab=ib}
N 160 -220 240 -220 {lab=ib}
N 240 -220 240 -140 {lab=ib}
N 200 -140 240 -140 {lab=ib}
N 240 -140 340 -140 {lab=ib}
N 160 -110 160 -40 {lab=vss}
N 380 -110 380 -40 {lab=vss}
N 380 -730 380 -700 {lab=pb}
N 380 -700 380 -450 {lab=pb}
N 380 -450 380 -170 {lab=pb}
N 300 -760 340 -760 {lab=pb}
N 300 -760 300 -700 {lab=pb}
N 300 -700 380 -700 {lab=pb}
N 380 -860 380 -790 {lab=vdd}
N 120 -140 160 -140 {lab=vss}
N 380 -140 420 -140 {lab=vss}
N 380 -760 420 -760 {lab=vdd}
N 40 -560 740 -560 {lab=vin}
N 740 -670 740 -560 {lab=vin}
N 740 -560 740 -230 {lab=vin}
N 740 -670 860 -670 {lab=vin}
N 740 -230 860 -230 {lab=vin}
N 900 -640 900 -620 {lab=b}
N 900 -620 900 -600 {lab=b}
N 900 -540 900 -520 {lab=vss}
N 900 -300 900 -280 {lab=a}
N 900 -280 900 -260 {lab=a}
N 900 -380 900 -360 {lab=vdd}
N 820 -570 860 -570 {lab=ib}
N 820 -330 860 -330 {lab=pb}
N 900 -620 1040 -620 {lab=b}
N 1040 -760 1040 -620 {lab=b}
N 1040 -760 1120 -760 {lab=b}
N 900 -280 1040 -280 {lab=a}
N 1040 -280 1040 -140 {lab=a}
N 1040 -140 1120 -140 {lab=a}
N 900 -700 1160 -700 {lab=p}
N 1160 -730 1160 -700 {lab=p}
N 900 -200 1160 -200 {lab=n}
N 1160 -200 1160 -170 {lab=n}
N 1160 -860 1160 -790 {lab=vdd}
N 1160 -110 1160 -40 {lab=vss}
N 1160 -640 1160 -610 {lab=out}
N 1160 -610 1160 -450 {lab=out}
N 1160 -450 1160 -290 {lab=out}
N 1160 -290 1160 -260 {lab=out}
N 1090 -610 1160 -610 {lab=out}
N 1090 -670 1090 -610 {lab=out}
N 1090 -670 1120 -670 {lab=out}
N 1090 -290 1160 -290 {lab=out}
N 1090 -290 1090 -230 {lab=out}
N 1090 -230 1120 -230 {lab=out}
N 1160 -450 1260 -450 {lab=out}
N 1260 -450 1320 -450 {lab=out}
N 1260 -450 1260 -360 {lab=out}
N 1260 -300 1260 -40 {lab=vss}
N 900 -670 940 -670 {lab=vdd}
N 900 -570 940 -570 {lab=vss}
N 900 -330 940 -330 {lab=vdd}
N 900 -230 940 -230 {lab=vss}
N 1160 -760 1200 -760 {lab=vdd}
N 1160 -670 1200 -670 {lab=vdd}
N 1160 -230 1200 -230 {lab=vss}
N 1160 -140 1200 -140 {lab=vss}
N 60 -860 380 -860 {lab=vdd}
N 380 -860 1160 -860 {lab=vdd}
N 60 -40 160 -40 {lab=vss}
N 160 -40 380 -40 {lab=vss}
N 380 -40 1160 -40 {lab=vss}
N 1160 -40 1260 -40 {lab=vss}
C {devices/iopin.sym} 60 -860 0 1 {name=pvdd lab=vdd sim_pinnumber=4}
C {devices/iopin.sym} 60 -40 0 1 {name=pvss lab=vss sim_pinnumber=5}
C {devices/ipin.sym} 40 -450 0 0 {name=pib lab=ib sim_pinnumber=3}
C {devices/ipin.sym} 40 -560 0 0 {name=pvin lab=vin sim_pinnumber=2}
C {devices/opin.sym} 1320 -450 0 0 {name=pout lab=out sim_pinnumber=1}
C {symbols/nfet_03v3.sym} 180 -140 0 1 {name=XMBN
L=0.34u
W=0.5u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 360 -140 0 0 {name=XMBN2
L=0.34u
W=0.5u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 360 -760 0 0 {name=XMBP
L=0.34u
W=2u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 120 -140 0 0 {name=l1 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 420 -140 0 1 {name=l2 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 420 -760 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_wire.sym} 380 -450 0 0 {name=l4 sig_type=std_logic lab=pb}
C {symbols/pfet_03v3.sym} 880 -670 0 0 {name=XM1
L=0.34u
W=40u
nf=20
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 880 -570 0 0 {name=XMIB
L=0.34u
W=0.5u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 880 -330 0 0 {name=XMIT
L=0.34u
W=2u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 880 -230 0 0 {name=XM4
L=0.34u
W=13u
nf=26
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1140 -760 0 0 {name=XM3
L=0.36u
W=2u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1140 -670 0 0 {name=XM2
L=0.34u
W=40u
nf=20
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1140 -230 0 0 {name=XM5
L=0.34u
W=13u
nf=26
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1140 -140 0 0 {name=XM6
L=0.36u
W=0.5u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 900 -520 0 0 {name=l5 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 900 -380 0 1 {name=l6 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 820 -570 0 0 {name=l7 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 820 -330 0 0 {name=l8 sig_type=std_logic lab=pb}
C {symbols/cap_mim_2f0fF.sym} 1260 -330 0 0 {name=XCD W=11.7u L=11.7u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 940 -670 0 1 {name=l9 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 940 -570 0 1 {name=l10 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 940 -330 0 1 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 940 -230 0 1 {name=l12 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 -760 0 1 {name=l13 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 -670 0 1 {name=l14 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1200 -230 0 1 {name=l15 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 1200 -140 0 1 {name=l16 sig_type=std_logic lab=vss}
C {devices/lab_wire.sym} 900 -620 0 0 {name=l17 sig_type=std_logic lab=b}
C {devices/lab_wire.sym} 900 -280 0 0 {name=l18 sig_type=std_logic lab=a}
C {devices/lab_wire.sym} 1160 -700 0 0 {name=l19 sig_type=std_logic lab=p}
C {devices/lab_wire.sym} 1160 -200 0 0 {name=l20 sig_type=std_logic lab=n}
C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/midrail_ref - midref_buf"}
