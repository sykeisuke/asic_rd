v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 250 -200 250 -120 {}
N 250 -200 320 -200 {}
N 250 -120 280 -120 {}
N 320 -1100 320 -1010 {}
N 320 -1100 1450 -1100 {}
N 320 -950 320 -560 {}
N 320 -560 320 -200 {}
N 320 -200 320 -150 {}
N 320 -200 410 -200 {}
N 320 -90 320 0 {}
N 320 0 480 0 {}
N 410 -200 410 -120 {}
N 410 -120 440 -120 {}
N 480 -600 480 -150 {}
N 480 -600 560 -600 {}
N 480 -90 480 0 {}
N 480 0 1320 0 {}
N 560 -600 700 -600 {}
N 700 -1050 700 -710 {}
N 700 -1050 1020 -1050 {}
N 700 -650 700 -600 {}
N 700 -600 1020 -600 {}
N 930 -680 980 -680 {}
N 1020 -1050 1020 -710 {}
N 1020 -1050 2000 -1050 {}
N 1020 -650 1020 -600 {}
N 1020 -600 1230 -600 {}
N 1230 -840 1230 -600 {}
N 1230 -840 1280 -840 {}
N 1250 -380 1250 -300 {}
N 1250 -380 1320 -380 {}
N 1250 -300 1280 -300 {}
N 1320 -900 1320 -870 {}
N 1320 -900 1380 -900 {}
N 1320 -810 1320 -640 {}
N 1320 -640 1320 -380 {}
N 1320 -380 1320 -330 {}
N 1320 -380 1510 -380 {}
N 1320 -270 1320 0 {}
N 1320 0 1580 0 {}
N 1380 -900 1450 -900 {}
N 1450 -1100 1450 -1010 {}
N 1450 -1100 1920 -1100 {}
N 1450 -950 1450 -900 {}
N 1450 -900 1580 -900 {}
N 1510 -840 1540 -840 {}
N 1510 -380 1510 -300 {}
N 1510 -300 1540 -300 {}
N 1580 -900 1580 -870 {}
N 1580 -810 1580 -700 {}
N 1580 -700 1580 -600 {}
N 1580 -600 1580 -460 {}
N 1580 -600 1650 -600 {}
N 1580 -460 1580 -330 {}
N 1580 -460 1850 -460 {}
N 1580 -270 1580 0 {}
N 1580 0 1920 0 {}
N 1710 -600 1740 -600 {}
N 1740 -600 1770 -600 {}
N 1830 -600 1920 -600 {}
N 1850 -460 1850 -300 {}
N 1850 -300 1880 -300 {}
N 1920 -1100 1920 -1010 {}
N 1920 -950 1920 -700 {}
N 1920 -700 1920 -600 {}
N 1920 -700 2000 -700 {}
N 1920 -600 1920 -330 {}
N 1920 -270 1920 0 {}
N 1920 0 2150 0 {}
N 2000 -1050 2000 -700 {}
N 2000 -700 2150 -700 {}
N 2150 -700 2150 -430 {}
N 2150 -700 2300 -700 {}
N 2150 -370 2150 0 {}
T {ramp_gen -- shared single-slope ramp for the 8-bit true bottom-plate cells (.subckt ramp_gen, ramp_gen.spice)
MILLER INTEGRATOR: the slope current I_INT = C_INT x SLOPE (0.469 uA into 4.0 pF -> 117.19 mV/us) is pulled out of the
virtual ground vx, which the OTA holds at vrlo = 0.5 V. vramp = vx + Q/C_INT rises linearly; the cells hang on the driven
output. rst high: XRST shorts XCI, vramp = vx = vrlo. pbias: the ramp's OWN bias_gen (ADR 0012). Sizes: data/ramp_gen_params.spice.} 40 -1460 0 0 0.32 0.32 {}
T {slope current} 220 -1180 0 0 0.40 0.40 {layer=13}
T {integrator + reset} 640 -1180 0 0 0.40 0.40 {layer=13}
T {OTA stage 1} 1250 -1180 0 0 0.40 0.40 {layer=13}
T {stage 2, compensation, output} 1700 -1180 0 0 0.40 0.40 {layer=13}
T {feedback: vramp -> XCI / XRST -> vx} 980 -1080 0 0 0.25 0.25 {layer=4}
C {devices/opin.sym} 40 -900 0 0 {name=p_vramp lab=vramp}
C {devices/ipin.sym} 40 -860 0 0 {name=p_rst lab=rst}
C {devices/ipin.sym} 40 -820 0 0 {name=p_vrlo lab=vrlo}
C {devices/ipin.sym} 40 -780 0 0 {name=p_pbias lab=pbias}
C {devices/iopin.sym} 40 -740 0 0 {name=p_vdd lab=vdd}
C {devices/iopin.sym} 40 -700 0 0 {name=p_vss lab=vss}
C {devices/lab_pin.sym} 320 -1100 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 320 0 0 0 {name=l2 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 300 -980 0 0 {name=XPS
L="\{RG_LPS\}"
W="\{RG_WPS\}"
nf="\{RG_NFPS\}"
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 280 -980 0 0 {name=l3 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 320 -980 0 1 {name=l4 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 300 -120 0 0 {name=XND
L="\{RG_LN\}"
W="\{RG_KD*RG_WNS\}"
nf="\{RG_NFND\}"
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 320 -120 0 1 {name=l5 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} 460 -120 0 0 {name=XNS
L="\{RG_LN\}"
W="\{RG_WNS\}"
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 480 -120 0 1 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 320 -560 0 1 {name=l7 sig_type=std_logic lab=nd}
C {devices/lab_pin.sym} 560 -600 0 1 {name=l8 sig_type=std_logic lab=vx}
C {symbols/cap_mim_2f0fF.sym} 700 -680 0 0 {name=XCI W="\{RG_CIW\}" L="\{RG_CIW\}" model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {symbols/nfet_03v3.sym} 1000 -680 0 0 {name=XRST
L=0.28u
W="\{RG_WRST\}"
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1020 -680 0 1 {name=l9 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 930 -680 0 0 {name=l10 sig_type=std_logic lab=rst}
C {symbols/pfet_03v3.sym} 1430 -980 0 0 {name=XM7
L=1u
W="\{RG_WT\}"
nf="\{RG_NFT\}"
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1410 -980 0 0 {name=l11 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1450 -980 0 1 {name=l12 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1380 -900 0 1 {name=l13 sig_type=std_logic lab=tail}
C {symbols/pfet_03v3.sym} 1300 -840 0 0 {name=XM1
L="\{RG_L1\}"
W="\{RG_W1\}"
nf="\{RG_NF1\}"
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1320 -840 0 1 {name=l14 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 1560 -840 0 0 {name=XM2
L="\{RG_L1\}"
W="\{RG_W1\}"
nf="\{RG_NF1\}"
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1580 -840 0 1 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1510 -840 0 0 {name=l16 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 1320 -640 0 1 {name=l17 sig_type=std_logic lab=d1}
C {devices/lab_pin.sym} 1580 -700 0 1 {name=l18 sig_type=std_logic lab=d2}
C {symbols/nfet_03v3.sym} 1300 -300 0 0 {name=XM3
L="\{RG_L3\}"
W="\{RG_W3\}"
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1320 -300 0 1 {name=l19 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} 1560 -300 0 0 {name=XM4
L="\{RG_L3\}"
W="\{RG_W3\}"
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1580 -300 0 1 {name=l20 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 1900 -980 0 0 {name=XM6
L=1u
W="\{RG_W6\}"
nf="\{RG_NF6\}"
m="\{RG_M6\}"
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1880 -980 0 0 {name=l21 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1920 -980 0 1 {name=l22 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 1900 -300 0 0 {name=XM5
L="\{RG_L5\}"
W="\{RG_W5\}"
nf="\{RG_NF5\}"
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 1920 -300 0 1 {name=l23 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u.sym} 1680 -600 3 0 {name=XRZ
W=1u
L="\{RG_RZL\}"
model=ppolyf_u
spiceprefix=""
m=1}
C {devices/lab_pin.sym} 1680 -580 0 1 {name=l24 sig_type=std_logic lab=vss}
C {symbols/cap_mim_2f0fF.sym} 1800 -600 1 0 {name=XCC W="\{RG_CCW\}" L="\{RG_CCW\}" model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 1740 -600 0 1 {name=l25 sig_type=std_logic lab=cz}
C {devices/lab_pin.sym} 2300 -700 0 1 {name=l26 sig_type=std_logic lab=vramp}
C {symbols/cap_mim_2f0fF.sym} 2150 -400 0 0 {name=XCO W="\{RG_COW\}" L="\{RG_COW\}" model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
