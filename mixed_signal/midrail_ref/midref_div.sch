v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {MIDREF_DIV  -  VDD/2 divider} 40 -900 0 0 0.6 0.6 {}
T {layout: XRT / XRB identical, ratio set by matching} 40 -840 0 0 0.36 0.36 {}
T {204.1 kOhm} 215 -598 0 0 0.36 0.36 {layer=4}
T {204.1 kOhm} 60 -205 0 0 0.36 0.36 {layer=4}
T {C = 43.1 fF} 335 -282 0 0 0.36 0.36 {layer=4}
N 200 -700 200 -580 {lab=vdd}
N 200 -520 200 -400 {lab=vin}
N 200 -400 200 -280 {lab=vin}
N 200 -220 200 -100 {lab=vss}
N 200 -400 320 -400 {lab=vin}
N 320 -400 420 -400 {lab=vin}
N 220 -550 260 -550 {lab=vss}
N 220 -250 260 -250 {lab=vss}
N 320 -400 320 -340 {lab=vin}
N 320 -280 320 -100 {lab=vss}
N 60 -700 200 -700 {lab=vdd}
N 60 -100 200 -100 {lab=vss}
N 200 -100 320 -100 {lab=vss}
C {devices/iopin.sym} 60 -700 0 1 {name=pvdd lab=vdd sim_pinnumber=2}
C {devices/iopin.sym} 60 -100 0 1 {name=pvss lab=vss sim_pinnumber=3}
C {devices/opin.sym} 420 -400 0 0 {name=pvin lab=vin sim_pinnumber=1}
C {devices/lab_pin.sym} 260 -550 0 1 {name=l1 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 260 -250 0 1 {name=l2 sig_type=std_logic lab=vss}
C {symbols/ppolyf_u_3k.sym} 200 -550 2 0 {name=XRT
W=1u
L=64.98u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/ppolyf_u_3k.sym} 200 -250 2 0 {name=XRB
W=1u
L=64.98u
model=ppolyf_u_3k
spiceprefix=""
m=1}
C {symbols/cap_mim_2f0fF.sym} 320 -310 0 0 {name=XCT W=4.423u L=4.423u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/title.sym} 0 140 0 0 {name=l99 author="ASIC R&D - mixed_signal/midrail_ref - midref_div"}
