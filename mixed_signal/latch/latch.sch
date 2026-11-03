v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 160 -420 300 -420 {lab=d}
N 160 -380 300 -380 {lab=clk}
N 500 -420 640 -420 {lab=q}
N 380 -540 380 -480 {lab=vdd}
N 420 -540 420 -480 {lab=vdd}
N 380 -540 420 -540 {lab=vdd}
N 160 -540 380 -540 {lab=vdd}
N 380 -320 380 -260 {lab=vss}
N 420 -320 420 -260 {lab=vss}
N 380 -260 420 -260 {lab=vss}
N 160 -260 380 -260 {lab=vss}
C {gf180mcu_as_sc_mcu7t3v3__dfxtn_2.sym} 400 -400 0 0 {name=XFF}
C {devices/iopin.sym} 160 -540 0 1 {name=pvdd lab=vdd}
C {devices/iopin.sym} 160 -260 0 1 {name=pvss lab=vss}
C {devices/ipin.sym} 160 -420 0 0 {name=pd lab=d}
C {devices/ipin.sym} 160 -380 0 0 {name=pclk lab=clk}
C {devices/opin.sym} 640 -420 0 0 {name=pq lab=q}
T {LATCH  -  negative-edge flip-flop gf180mcu_as_sc_mcu7t3v3__dfxtn_2} 100 -700 0 0 0.6 0.6 {}
