v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {ctlb: not connected} 340 -255 0 0 0.32 0.32 {layer=4}
T {vdd: not connected} 120 265 0 0 0.32 0.32 {layer=4}
T {SW_S2  -  S2  vref -> bot (bottom plate), single NMOS; ctlb unused} 80 -560 0 0 0.6 0.6 {}
N 280 120 370 120 {lab=a}
N 430 120 520 120 {lab=b}
N 400 60 400 120 {lab=vss}
N 400 160 400 220 {lab=ctl}
N 320 220 400 220 {lab=ctl}
N 160 120 280 120 {lab=a}
N 520 120 640 120 {lab=b}
C {symbols/nfet_03v3.sym} 400 140 1 1 {name=XN
L=0.28u
W=0.36u
nf=1
m=1
ad=0.1584p
as=0.1584p
pd=1.60u
ps=1.60u
model=nfet_03v3
spiceprefix=""
hide_texts=true
format="@spiceprefix@name @pinlist @model L=@L W=@W nf=@nf m=@m ad=@ad as=@as pd=@pd ps=@ps"}
C {devices/lab_pin.sym} 400 60 0 1 {name=l1 sig_type=std_logic lab=vss}
C {devices/ipin.sym} 320 220 0 0 {name=pctl lab=ctl sim_pinnumber=3}
C {devices/ipin.sym} 320 -220 0 0 {name=pctlb lab=ctlb sim_pinnumber=4}
C {devices/iopin.sym} 160 120 0 0 {name=pa lab=a sim_pinnumber=1}
C {devices/iopin.sym} 640 120 0 1 {name=pb lab=b sim_pinnumber=2}
C {devices/iopin.sym} 80 300 0 0 {name=pvdd lab=vdd sim_pinnumber=5}
C {devices/iopin.sym} 80 340 0 0 {name=pvss lab=vss sim_pinnumber=6}
C {devices/title.sym} 0 460 0 0 {name=l99 author="ASIC R&D - mixed_signal/Analog_top - sw_s2"}
