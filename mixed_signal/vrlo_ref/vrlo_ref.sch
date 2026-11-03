v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {DIVIDER 48 : 7 units (tap = 7/55 AVDD)} 80 -1000 0 0 0.4 0.4 {}
T {BIAS} 760 -1000 0 0 0.4 0.4 {}
T {OTA (PMOS input, g-node diode XM5)} 1120 -1000 0 0 0.4 0.4 {}
T {SHUNT + KEEP-ALIVE + DECAP} 1760 -1000 0 0 0.4 0.4 {}
T {VRLO_REF  -  0.5 V shunt regulator for the ramp reset} 40 -1200 0 0 0.6 0.6 {}
T {layout: the 55 divider units identical (48 : 7 by matching)} 40 -1140 0 0 0.36 0.36 {}
N 120 -840 160 -840 {lab=avss}
N 120 -780 160 -780 {lab=avss}
N 120 -720 160 -720 {lab=avss}
N 120 -660 160 -660 {lab=avss}
N 120 -600 160 -600 {lab=avss}
N 120 -540 160 -540 {lab=avss}
N 120 -480 160 -480 {lab=avss}
N 120 -420 160 -420 {lab=avss}
N 120 -360 160 -360 {lab=avss}
N 120 -300 160 -300 {lab=avss}
N 120 -240 160 -240 {lab=avss}
N 120 -180 160 -180 {lab=avss}
N 160 -180 200 -180 {lab=avss}
N 160 -240 200 -240 {lab=avss}
N 160 -300 200 -300 {lab=avss}
N 160 -360 200 -360 {lab=avss}
N 160 -420 200 -420 {lab=avss}
N 160 -480 200 -480 {lab=avss}
N 160 -540 200 -540 {lab=avss}
N 160 -600 200 -600 {lab=avss}
N 160 -660 200 -660 {lab=avss}
N 160 -720 200 -720 {lab=avss}
N 160 -780 200 -780 {lab=avss}
N 160 -840 200 -840 {lab=avss}
N 360 -840 400 -840 {lab=avss}
N 360 -780 400 -780 {lab=avss}
N 360 -720 400 -720 {lab=avss}
N 360 -660 400 -660 {lab=avss}
N 360 -600 400 -600 {lab=avss}
N 360 -540 400 -540 {lab=avss}
N 360 -480 400 -480 {lab=avss}
N 360 -420 400 -420 {lab=avss}
N 360 -360 400 -360 {lab=avss}
N 360 -300 400 -300 {lab=avss}
N 360 -240 400 -240 {lab=avss}
N 360 -180 400 -180 {lab=avss}
N 400 -180 440 -180 {lab=avss}
N 400 -240 440 -240 {lab=avss}
N 400 -300 440 -300 {lab=avss}
N 400 -360 440 -360 {lab=avss}
N 400 -420 440 -420 {lab=avss}
N 400 -480 440 -480 {lab=avss}
N 400 -540 440 -540 {lab=avss}
N 400 -600 440 -600 {lab=avss}
N 400 -660 440 -660 {lab=avss}
N 400 -720 440 -720 {lab=avss}
N 400 -780 440 -780 {lab=avss}
N 400 -840 440 -840 {lab=avss}
N 600 -840 640 -840 {lab=avss}
N 600 -780 640 -780 {lab=avss}
N 600 -720 640 -720 {lab=avss}
N 600 -660 640 -660 {lab=avss}
N 600 -600 640 -600 {lab=avss}
N 600 -540 640 -540 {lab=avss}
N 600 -480 640 -480 {lab=avss}
N 100 -900 100 -870 {lab=avdd}
N 100 -150 220 -150 {lab=r12}
N 220 -870 340 -870 {lab=r24}
N 340 -150 460 -150 {lab=r36}
N 460 -870 580 -870 {lab=tap}
N 580 -450 580 -40 {lab=avss}
N 580 -870 700 -870 {lab=tap}
N 700 -870 700 -730 {lab=tap}
N 700 -670 700 -40 {lab=avss}
N 740 -450 860 -450 {lab=ib}
N 860 -450 860 -220 {lab=ib}
N 860 -220 860 -170 {lab=ib}
N 860 -220 940 -220 {lab=ib}
N 940 -220 940 -140 {lab=ib}
N 900 -140 940 -140 {lab=ib}
N 940 -140 1040 -140 {lab=ib}
N 860 -110 860 -40 {lab=avss}
N 1080 -110 1080 -40 {lab=avss}
N 1080 -730 1080 -700 {lab=pb}
N 1080 -700 1080 -450 {lab=pb}
N 1080 -450 1080 -170 {lab=pb}
N 1000 -760 1040 -760 {lab=pb}
N 1000 -760 1000 -700 {lab=pb}
N 1000 -700 1080 -700 {lab=pb}
N 1080 -900 1080 -790 {lab=avdd}
N 820 -140 860 -140 {lab=avss}
N 1080 -140 1120 -140 {lab=avss}
N 1080 -760 1120 -760 {lab=avdd}
N 1460 -730 1460 -700 {lab=ts}
N 1460 -700 1460 -680 {lab=ts}
N 1360 -680 1460 -680 {lab=ts}
N 1460 -680 1560 -680 {lab=ts}
N 1360 -680 1360 -630 {lab=ts}
N 1560 -680 1560 -630 {lab=ts}
N 1460 -900 1460 -790 {lab=avdd}
N 1380 -760 1420 -760 {lab=pb}
N 1280 -600 1320 -600 {lab=tap}
N 1600 -600 1640 -600 {lab=vrlo}
N 1360 -570 1360 -450 {lab=g}
N 1360 -450 1360 -330 {lab=g}
N 1560 -570 1560 -450 {lab=d1}
N 1560 -450 1560 -380 {lab=d1}
N 1560 -380 1560 -330 {lab=d1}
N 1600 -380 1600 -300 {lab=d1}
N 1560 -380 1600 -380 {lab=d1}
N 1320 -300 1320 -230 {lab=d1}
N 1320 -230 1640 -230 {lab=d1}
N 1640 -300 1640 -230 {lab=d1}
N 1600 -300 1640 -300 {lab=d1}
N 1180 -450 1360 -450 {lab=g}
N 1180 -450 1180 -380 {lab=g}
N 1180 -380 1180 -330 {lab=g}
N 1140 -380 1140 -300 {lab=g}
N 1140 -380 1180 -380 {lab=g}
N 1360 -270 1360 -40 {lab=avss}
N 1560 -270 1560 -40 {lab=avss}
N 1180 -270 1180 -40 {lab=avss}
N 1360 -600 1400 -600 {lab=avdd}
N 1520 -600 1560 -600 {lab=avdd}
N 1460 -760 1500 -760 {lab=avdd}
N 1360 -300 1400 -300 {lab=avss}
N 1520 -300 1560 -300 {lab=avss}
N 1180 -300 1220 -300 {lab=avss}
N 1840 -730 1840 -500 {lab=vrlo}
N 1840 -500 1840 -330 {lab=vrlo}
N 1840 -900 1840 -790 {lab=avdd}
N 1840 -270 1840 -40 {lab=avss}
N 1760 -760 1800 -760 {lab=pb}
N 1760 -300 1800 -300 {lab=g}
N 1840 -300 1880 -300 {lab=avss}
N 1840 -760 1880 -760 {lab=avdd}
N 1840 -500 2000 -500 {lab=vrlo}
N 2000 -500 2100 -500 {lab=vrlo}
N 2000 -500 2000 -330 {lab=vrlo}
N 2000 -270 2000 -40 {lab=avss}
N 40 -900 100 -900 {lab=avdd}
N 100 -900 1080 -900 {lab=avdd}
N 1080 -900 1460 -900 {lab=avdd}
N 1460 -900 1840 -900 {lab=avdd}
N 40 -40 580 -40 {lab=avss}
N 580 -40 700 -40 {lab=avss}
N 700 -40 860 -40 {lab=avss}
N 860 -40 1080 -40 {lab=avss}
N 1080 -40 1180 -40 {lab=avss}
N 1180 -40 1360 -40 {lab=avss}
N 1360 -40 1560 -40 {lab=avss}
N 1560 -40 1840 -40 {lab=avss}
N 1840 -40 2000 -40 {lab=avss}
C {symbols/ppolyf_u_3k.sym} 100 -840 2 0 {name=XR1
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -780 2 0 {name=XR2
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -720 2 0 {name=XR3
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -660 2 0 {name=XR4
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -600 2 0 {name=XR5
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -540 2 0 {name=XR6
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -480 2 0 {name=XR7
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -420 2 0 {name=XR8
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -360 2 0 {name=XR9
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -300 2 0 {name=XR10
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -240 2 0 {name=XR11
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 100 -180 2 0 {name=XR12
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -180 0 0 {name=XR13
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -240 0 0 {name=XR14
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -300 0 0 {name=XR15
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -360 0 0 {name=XR16
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -420 0 0 {name=XR17
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -480 0 0 {name=XR18
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -540 0 0 {name=XR19
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -600 0 0 {name=XR20
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -660 0 0 {name=XR21
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -720 0 0 {name=XR22
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -780 0 0 {name=XR23
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 220 -840 0 0 {name=XR24
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -840 2 0 {name=XR25
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -780 2 0 {name=XR26
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -720 2 0 {name=XR27
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -660 2 0 {name=XR28
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -600 2 0 {name=XR29
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -540 2 0 {name=XR30
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -480 2 0 {name=XR31
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -420 2 0 {name=XR32
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -360 2 0 {name=XR33
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -300 2 0 {name=XR34
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -240 2 0 {name=XR35
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 340 -180 2 0 {name=XR36
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -180 0 0 {name=XR37
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -240 0 0 {name=XR38
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -300 0 0 {name=XR39
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -360 0 0 {name=XR40
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -420 0 0 {name=XR41
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -480 0 0 {name=XR42
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -540 0 0 {name=XR43
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -600 0 0 {name=XR44
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -660 0 0 {name=XR45
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -720 0 0 {name=XR46
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -780 0 0 {name=XR47
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 460 -840 0 0 {name=XR48
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -840 2 0 {name=XR49
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -780 2 0 {name=XR50
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -720 2 0 {name=XR51
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -660 2 0 {name=XR52
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -600 2 0 {name=XR53
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -540 2 0 {name=XR54
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 580 -480 2 0 {name=XR55
W=1u
L=20u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/cap_mim_2f0fF.sym} 700 -700 0 0 {name=XCT W=22.4u L=22.4u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {symbols/nfet_03v3.sym} 880 -140 0 1 {name=XMBN
L=1u
W=1u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1060 -140 0 0 {name=XMBN2
L=1u
W=1u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1060 -760 0 0 {name=XMBP
L=1u
W=2u
nf=1
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1440 -760 0 0 {name=XMT
L=1u
W=4u
nf=2
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1820 -760 0 0 {name=XMK
L=1u
W=6u
nf=3
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1580 -600 0 1 {name=XM1
L=0.5u
W=14u
nf=7
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/pfet_03v3.sym} 1340 -600 0 0 {name=XM2
L=0.5u
W=14u
nf=7
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1580 -300 0 1 {name=XM3
L=1u
W=6u
nf=6
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1340 -300 0 0 {name=XM4
L=1u
W=4u
nf=4
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1160 -300 0 0 {name=XM5
L=1u
W=2u
nf=2
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/nfet_03v3.sym} 1820 -300 0 0 {name=XMS
L=1u
W=18u
nf=18
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {symbols/cap_mim_2f0fF.sym} 2000 -300 0 0 {name=XCD W=41.5u L=41.5u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/iopin.sym} 40 -900 0 1 {name=pavdd lab=avdd sim_pinnumber=3}
C {devices/iopin.sym} 40 -40 0 1 {name=pavss lab=avss sim_pinnumber=4}
C {devices/lab_pin.sym} 160 -840 0 1 {name=l1 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -810 0 0 {name=l2 sig_type=std_logic lab=r1}
C {devices/lab_pin.sym} 160 -780 0 1 {name=l3 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -750 0 0 {name=l4 sig_type=std_logic lab=r2}
C {devices/lab_pin.sym} 160 -720 0 1 {name=l5 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -690 0 0 {name=l6 sig_type=std_logic lab=r3}
C {devices/lab_pin.sym} 160 -660 0 1 {name=l7 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -630 0 0 {name=l8 sig_type=std_logic lab=r4}
C {devices/lab_pin.sym} 160 -600 0 1 {name=l9 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -570 0 0 {name=l10 sig_type=std_logic lab=r5}
C {devices/lab_pin.sym} 160 -540 0 1 {name=l11 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -510 0 0 {name=l12 sig_type=std_logic lab=r6}
C {devices/lab_pin.sym} 160 -480 0 1 {name=l13 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -450 0 0 {name=l14 sig_type=std_logic lab=r7}
C {devices/lab_pin.sym} 160 -420 0 1 {name=l15 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -390 0 0 {name=l16 sig_type=std_logic lab=r8}
C {devices/lab_pin.sym} 160 -360 0 1 {name=l17 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -330 0 0 {name=l18 sig_type=std_logic lab=r9}
C {devices/lab_pin.sym} 160 -300 0 1 {name=l19 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -270 0 0 {name=l20 sig_type=std_logic lab=r10}
C {devices/lab_pin.sym} 160 -240 0 1 {name=l21 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -210 0 0 {name=l22 sig_type=std_logic lab=r11}
C {devices/lab_pin.sym} 160 -180 0 1 {name=l23 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 100 -150 0 0 {name=l24 sig_type=std_logic lab=r12}
C {devices/lab_pin.sym} 160 -180 0 0 {name=l25 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -210 0 0 {name=l26 sig_type=std_logic lab=r13}
C {devices/lab_pin.sym} 160 -240 0 0 {name=l27 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -270 0 0 {name=l28 sig_type=std_logic lab=r14}
C {devices/lab_pin.sym} 160 -300 0 0 {name=l29 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -330 0 0 {name=l30 sig_type=std_logic lab=r15}
C {devices/lab_pin.sym} 160 -360 0 0 {name=l31 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -390 0 0 {name=l32 sig_type=std_logic lab=r16}
C {devices/lab_pin.sym} 160 -420 0 0 {name=l33 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -450 0 0 {name=l34 sig_type=std_logic lab=r17}
C {devices/lab_pin.sym} 160 -480 0 0 {name=l35 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -510 0 0 {name=l36 sig_type=std_logic lab=r18}
C {devices/lab_pin.sym} 160 -540 0 0 {name=l37 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -570 0 0 {name=l38 sig_type=std_logic lab=r19}
C {devices/lab_pin.sym} 160 -600 0 0 {name=l39 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -630 0 0 {name=l40 sig_type=std_logic lab=r20}
C {devices/lab_pin.sym} 160 -660 0 0 {name=l41 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -690 0 0 {name=l42 sig_type=std_logic lab=r21}
C {devices/lab_pin.sym} 160 -720 0 0 {name=l43 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -750 0 0 {name=l44 sig_type=std_logic lab=r22}
C {devices/lab_pin.sym} 160 -780 0 0 {name=l45 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -810 0 0 {name=l46 sig_type=std_logic lab=r23}
C {devices/lab_pin.sym} 160 -840 0 0 {name=l47 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 220 -870 0 0 {name=l48 sig_type=std_logic lab=r24}
C {devices/lab_pin.sym} 400 -840 0 1 {name=l49 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -810 0 0 {name=l50 sig_type=std_logic lab=r25}
C {devices/lab_pin.sym} 400 -780 0 1 {name=l51 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -750 0 0 {name=l52 sig_type=std_logic lab=r26}
C {devices/lab_pin.sym} 400 -720 0 1 {name=l53 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -690 0 0 {name=l54 sig_type=std_logic lab=r27}
C {devices/lab_pin.sym} 400 -660 0 1 {name=l55 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -630 0 0 {name=l56 sig_type=std_logic lab=r28}
C {devices/lab_pin.sym} 400 -600 0 1 {name=l57 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -570 0 0 {name=l58 sig_type=std_logic lab=r29}
C {devices/lab_pin.sym} 400 -540 0 1 {name=l59 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -510 0 0 {name=l60 sig_type=std_logic lab=r30}
C {devices/lab_pin.sym} 400 -480 0 1 {name=l61 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -450 0 0 {name=l62 sig_type=std_logic lab=r31}
C {devices/lab_pin.sym} 400 -420 0 1 {name=l63 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -390 0 0 {name=l64 sig_type=std_logic lab=r32}
C {devices/lab_pin.sym} 400 -360 0 1 {name=l65 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -330 0 0 {name=l66 sig_type=std_logic lab=r33}
C {devices/lab_pin.sym} 400 -300 0 1 {name=l67 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -270 0 0 {name=l68 sig_type=std_logic lab=r34}
C {devices/lab_pin.sym} 400 -240 0 1 {name=l69 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -210 0 0 {name=l70 sig_type=std_logic lab=r35}
C {devices/lab_pin.sym} 400 -180 0 1 {name=l71 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 340 -150 0 0 {name=l72 sig_type=std_logic lab=r36}
C {devices/lab_pin.sym} 400 -180 0 0 {name=l73 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -210 0 0 {name=l74 sig_type=std_logic lab=r37}
C {devices/lab_pin.sym} 400 -240 0 0 {name=l75 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -270 0 0 {name=l76 sig_type=std_logic lab=r38}
C {devices/lab_pin.sym} 400 -300 0 0 {name=l77 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -330 0 0 {name=l78 sig_type=std_logic lab=r39}
C {devices/lab_pin.sym} 400 -360 0 0 {name=l79 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -390 0 0 {name=l80 sig_type=std_logic lab=r40}
C {devices/lab_pin.sym} 400 -420 0 0 {name=l81 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -450 0 0 {name=l82 sig_type=std_logic lab=r41}
C {devices/lab_pin.sym} 400 -480 0 0 {name=l83 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -510 0 0 {name=l84 sig_type=std_logic lab=r42}
C {devices/lab_pin.sym} 400 -540 0 0 {name=l85 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -570 0 0 {name=l86 sig_type=std_logic lab=r43}
C {devices/lab_pin.sym} 400 -600 0 0 {name=l87 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -630 0 0 {name=l88 sig_type=std_logic lab=r44}
C {devices/lab_pin.sym} 400 -660 0 0 {name=l89 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -690 0 0 {name=l90 sig_type=std_logic lab=r45}
C {devices/lab_pin.sym} 400 -720 0 0 {name=l91 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -750 0 0 {name=l92 sig_type=std_logic lab=r46}
C {devices/lab_pin.sym} 400 -780 0 0 {name=l93 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 460 -810 0 0 {name=l94 sig_type=std_logic lab=r47}
C {devices/lab_pin.sym} 400 -840 0 0 {name=l95 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 640 -840 0 1 {name=l96 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 580 -810 0 0 {name=l97 sig_type=std_logic lab=r49}
C {devices/lab_pin.sym} 640 -780 0 1 {name=l98 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 580 -750 0 0 {name=l99 sig_type=std_logic lab=r50}
C {devices/lab_pin.sym} 640 -720 0 1 {name=l100 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 580 -690 0 0 {name=l101 sig_type=std_logic lab=r51}
C {devices/lab_pin.sym} 640 -660 0 1 {name=l102 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 580 -630 0 0 {name=l103 sig_type=std_logic lab=r52}
C {devices/lab_pin.sym} 640 -600 0 1 {name=l104 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 580 -570 0 0 {name=l105 sig_type=std_logic lab=r53}
C {devices/lab_pin.sym} 640 -540 0 1 {name=l106 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 580 -510 0 0 {name=l107 sig_type=std_logic lab=r54}
C {devices/lab_pin.sym} 640 -480 0 1 {name=l108 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 700 -870 0 0 {name=l109 sig_type=std_logic lab=tap}
C {devices/ipin.sym} 740 -450 0 0 {name=pib lab=ib sim_pinnumber=2}
C {devices/lab_pin.sym} 820 -140 0 0 {name=l110 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1120 -140 0 1 {name=l111 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1120 -760 0 1 {name=l112 sig_type=std_logic lab=avdd}
C {devices/lab_wire.sym} 1080 -450 0 0 {name=l113 sig_type=std_logic lab=pb}
C {devices/lab_pin.sym} 1380 -760 0 0 {name=l114 sig_type=std_logic lab=pb}
C {devices/lab_pin.sym} 1280 -600 0 0 {name=l115 sig_type=std_logic lab=tap}
C {devices/lab_pin.sym} 1640 -600 0 1 {name=l116 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 1400 -600 0 1 {name=l117 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1520 -600 0 0 {name=l118 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1500 -760 0 1 {name=l119 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1400 -300 0 1 {name=l120 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1520 -300 0 0 {name=l121 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1220 -300 0 1 {name=l122 sig_type=std_logic lab=avss}
C {devices/lab_wire.sym} 1360 -450 0 0 {name=l123 sig_type=std_logic lab=g}
C {devices/lab_wire.sym} 1560 -450 0 0 {name=l124 sig_type=std_logic lab=d1}
C {devices/lab_wire.sym} 1460 -700 0 0 {name=l125 sig_type=std_logic lab=ts}
C {devices/lab_pin.sym} 1760 -760 0 0 {name=l126 sig_type=std_logic lab=pb}
C {devices/lab_pin.sym} 1760 -300 0 0 {name=l127 sig_type=std_logic lab=g}
C {devices/lab_pin.sym} 1880 -300 0 1 {name=l128 sig_type=std_logic lab=avss}
C {devices/lab_pin.sym} 1880 -760 0 1 {name=l129 sig_type=std_logic lab=avdd}
C {devices/opin.sym} 2100 -500 0 0 {name=pvrlo lab=vrlo sim_pinnumber=1}
C {devices/lab_wire.sym} 1840 -500 0 0 {name=l130 sig_type=std_logic lab=vrlo}
C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/vrlo_ref - vrlo_ref"}
