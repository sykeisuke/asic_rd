v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 300 -480 300 -440 {lab=VIN}
N 260 -410 220 -410 {lab=SAMPLE}
N 300 -380 300 -330 {lab=VHOLD}
N 300 -330 300 -290 {lab=VHOLD}
N 300 -230 300 -190 {lab=0}
N 300 -410 380 -410 {lab=0}
C {symbols/nfet_03v3.sym} 280 -410 0 0 {name=M1
L=0.28u
W=10u
nf=10
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X}
C {devices/capa.sym} 300 -260 0 0 {name=C1
m=1
value=1p
footprint=1206
device="ceramic capacitor"}
C {devices/lab_pin.sym} 300 -480 0 0 {name=l1 sig_type=std_logic lab=VIN}
C {devices/lab_pin.sym} 220 -410 0 0 {name=l2 sig_type=std_logic lab=SAMPLE}
C {devices/lab_pin.sym} 300 -330 0 1 {name=l3 sig_type=std_logic lab=VHOLD}
C {devices/gnd.sym} 300 -190 0 0 {name=l4 lab=0}
C {devices/gnd.sym} 380 -410 0 0 {name=l5 lab=0}
C {devices/code_shown.sym} 500 -470 0 0 {name=MODELS only_toplevel=true
format="tcleval( @value )"
value="
.include $::180MCU_MODELS/design.ngspice
.lib $::180MCU_MODELS/sm141064.ngspice typical
"}
C {devices/code_shown.sym} 500 -280 0 0 {name=STIMULUS only_toplevel=true
value="
VIN VIN 0 SIN(1.2 0.6 5MEG)
VCLK SAMPLE 0 PULSE(0 3.3 5n 100p 100p 20n 100n)
RLEAK VHOLD 0 1T
.tran 5p 80n
.control
run
write work/sampling_cell_xschem.raw
quit
.endc
"}
C {devices/title.sym} 160 -30 0 0 {name=l6 author="ASIC R&D"}
