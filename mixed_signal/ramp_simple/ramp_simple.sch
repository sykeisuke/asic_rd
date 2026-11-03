v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 300 -300 500 -300 {}
N 300 -180 460 -180 {}
N 300 -120 500 -120 {}
N 300 -40 640 -40 {}
N 500 -300 500 -210 {}
N 500 -300 880 -300 {}
N 500 -180 640 -180 {}
N 500 -150 500 -120 {}
N 640 -180 640 -40 {}
N 640 -40 880 -40 {}
N 880 -300 880 -210 {}
N 880 -300 1300 -300 {}
N 880 -150 880 -40 {}
N 880 -40 1300 -40 {}
T {RAMP_SIMPLE  -  ramp capacitor + reset switch to VR_LO; the current from the I/C source} 60 -500 0 0 0.70 0.70 {}
T {layout: MIM (M4-M5) beside the cells' vramp bus, the reset switch at the vrlo end} 60 -460 0 0 0.35 0.35 {}
T {reset to VR_LO} 400 -370 0 0 0.45 0.45 {layer=13}
T {C = 73 x 54.52 fF = 3.98 pF} 1000 -110 0 0 0.45 0.45 {layer=4}
T {ramp capacitor} 800 -370 0 0 0.45 0.45 {layer=13}
T {I = 0.545 uA} 1080 -340 0 0 0.45 0.45 {layer=4}
C {devices/opin.sym} 1300 -300 0 0 {name=p_vramp lab=vramp}
C {devices/iopin.sym} 1300 -40 0 0 {name=p_vss lab=vss}
C {symbols/nfet_03v3.sym} 480 -180 0 0 {name=XRST
L=0.28u
W=0.500u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/ipin.sym} 300 -120 0 0 {name=p_vrlo lab=vrlo}
C {devices/ipin.sym} 300 -180 0 0 {name=p_rst lab=rst}
C {symbols/cap_mim_2f0fF.sym} 880 -180 0 0 {name=XCR W=5.000u L=5.000u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=73}
