v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
B 2 900 -650 1450 -450 {flags=graph
y1=0
y2=2
x1=0
x2=8e-08
node="vin vhold"
color="4 5"
dataset=-1}
B 2 900 -420 1450 -220 {flags=graph
y1=0
y2=3.5
x1=0
x2=8e-08
node="sample sample_b"
color="6 7"
dataset=-1}
N 300 -520 300 -480 {lab=VIN}
N 300 -480 440 -480 {lab=VIN}
N 440 -480 440 -440 {lab=VIN}
N 300 -420 300 -380 {lab=VHOLD}
N 300 -380 440 -380 {lab=VHOLD}
N 370 -380 370 -320 {lab=VHOLD}
N 370 -260 370 -220 {lab=0}
N 260 -450 220 -450 {lab=SAMPLE}
N 400 -410 360 -410 {lab=SAMPLE_B}
N 300 -450 340 -450 {lab=0}
N 440 -410 520 -410 {lab=VDD}
C {symbols/nfet_03v3.sym} 280 -450 0 0 {name=MN
L=0.28u W=10u nf=10 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {symbols/pfet_03v3.sym} 420 -410 0 0 {name=MP
L=0.28u W=20u nf=10 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/capa.sym} 370 -290 0 0 {name=CHOLD m=1 value=1p footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 300 -520 0 0 {name=l1 sig_type=std_logic lab=VIN}
C {devices/lab_pin.sym} 220 -450 0 0 {name=l2 sig_type=std_logic lab=SAMPLE}
C {devices/lab_pin.sym} 360 -410 0 0 {name=l3 sig_type=std_logic lab=SAMPLE_B}
C {devices/lab_pin.sym} 370 -380 0 1 {name=l4 sig_type=std_logic lab=VHOLD}
C {devices/lab_pin.sym} 520 -410 0 1 {name=l5 sig_type=std_logic lab=VDD}
C {devices/gnd.sym} 370 -220 0 0 {name=l6 lab=0}
C {devices/gnd.sym} 340 -450 0 0 {name=l7 lab=0}
C {devices/code_shown.sym} 570 -610 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {devices/code_shown.sym} 570 -370 0 0 {name=STIMULUS only_toplevel=true
value="
VIN VIN 0 SIN(1.2 0.6 5MEG)
VCLK SAMPLE 0 PULSE(0 3.3 5n 100p 100p 20n 100n)
VCLKB SAMPLE_B 0 PULSE(3.3 0 5n 100p 100p 20n 100n)
VDD_SOURCE VDD 0 3.3
RLEAK VHOLD 0 1T
.tran 5p 80n
.control
run
write sampling_cell_tg.raw
quit
.endc
"}
C {devices/title.sym} 160 -30 0 0 {name=l8 author="ASIC R&D - Lab 1 transmission-gate sampling cell"}
C {devices/launcher.sym} 990 -705 0 0 {name=h1
descr="Load VIN, VHOLD, and sampling clocks"
tclcommand="xschem raw_read $netlist_dir/sampling_cell_tg.raw tran"}
T {TRACK: SAMPLE=3.3 V, SAMPLE_B=0 V. VHOLD follows VIN.} 170 -140 0 0 0.35 0.35 {}
T {HOLD: SAMPLE=0 V, SAMPLE_B=3.3 V. VHOLD is isolated on CHOLD.} 170 -100 0 0 0.35 0.35 {}
