v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1210 120 -1250 {}
N 120 -1150 120 -1110 {}
N 360 -1210 360 -1250 {}
N 360 -1150 360 -1110 {}
N 120 -810 120 -850 {}
N 120 -750 120 -710 {}
N 1400 -1180 1360 -1180 {}
N 1400 -1140 1360 -1140 {}
N 1600 -1180 1640 -1180 {}
N 1500 -1240 1500 -1280 {}
N 1500 -1080 1500 -1040 {}
N 1740 -1210 1740 -1250 {}
N 1740 -1150 1740 -1110 {}
T {TB_DRIVE  -  latch alone, 20 MHz clock, d moves in both clock phases, q into 50 fF} 60 -1360 0 0 0.7 0.7 {}
T {SUPPLY / CLOCK / D} 40 -1292 0 0 0.45 0.45 {layer=4}
T {clk 10-90 % 0.5 ns} 40 -1010 0 0 0.3 0.3 {layer=4}
T {d 10-90 % 10.4 ns} 40 -960 0 0 0.3 0.3 {layer=4}
T {DUT} 1360 -1292 0 0 0.45 0.45 {layer=4}
T {CQ = 50 fF} 1780 -1090 0 0 0.3 0.3 {layer=4}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDVDD value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 360 -1180 0 0 {name=VCLK value="PULSE(\{VDD\} 0 \{TCOUNT/2-TCE/2\} \{TCE\} \{TCE\} \{TCOUNT/2-TCE\} \{TCOUNT\})" savecurrent=false}
C {devices/lab_pin.sym} 360 -1250 0 0 {name=l3 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 360 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -780 0 0 {name=VD value="PWL(0 \{VDD\} \{412.5n-TDF/2\} \{VDD\} \{412.5n+TDF/2\} 0 \{587.5n-TDF/2\} 0 \{587.5n+TDF/2\} \{VDD\} \{787.5n-TDF/2\} \{VDD\} \{787.5n+TDF/2\} 0 \{962.5n-TDF/2\} 0 \{962.5n+TDF/2\} \{VDD\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -850 0 0 {name=l5 sig_type=std_logic lab=d}
C {devices/lab_pin.sym} 120 -710 0 0 {name=l6 sig_type=std_logic lab=0}
C {latch.sym} 1500 -1160 0 0 {name=XL}
C {devices/lab_pin.sym} 1360 -1180 0 0 {name=l7 sig_type=std_logic lab=d}
C {devices/lab_pin.sym} 1360 -1140 0 0 {name=l8 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1640 -1180 0 1 {name=l9 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 1500 -1280 0 0 {name=l10 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 1500 -1040 0 0 {name=l11 sig_type=std_logic lab=0}
C {devices/capa.sym} 1740 -1180 0 0 {name=CQ value=50f m=1}
C {devices/lab_pin.sym} 1740 -1250 0 0 {name=l12 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 1740 -1110 0 0 {name=l13 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 60 -640 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.include /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice
.param VDD=3.3
.param TCOUNT=50n
.param TCE=6.250000e-10
.param TDF=1.300000e-08
.param TSTOP=1100n
.temp 27
.csparam cs_vdd=\{VDD\}
.options savecurrents reltol=1e-4
.tran 5p \{TSTOP\} 0 20p
.control
run
let half = $&cs_vdd / 2
let hi90 = 0.9 * $&cs_vdd
let lo10 = 0.1 * $&cs_vdd
meas tran t_edge when v(clk)=$&half fall=1 td=413e-9
meas tran t_q when v(q)=$&half fall=1 td=100e-9
meas tran t_q90 when v(q)=$&hi90 fall=1 td=100e-9
meas tran t_q10 when v(q)=$&lo10 fall=1 td=100e-9
let tcq = t_q - t_edge
let q_fall = t_q10 - t_q90
set numdgt=10
echo RESULT_BEGIN
print tcq q_fall t_edge t_q
echo RESULT_END
quit
.endc"}
