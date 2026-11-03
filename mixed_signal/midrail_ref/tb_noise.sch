v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1160 120 -1200 {}
N 120 -1100 120 -1060 {}
N 290 -1160 290 -1200 {}
N 290 -1100 290 -1060 {}
N 460 -1160 460 -1200 {}
N 460 -1100 460 -1060 {}
N 630 -1160 630 -1200 {}
N 630 -1100 630 -1060 {}
N 800 -1160 800 -1200 {}
N 800 -1100 800 -1060 {}
N 1180 -1100 1220 -1100 {}
N 1100 -1160 1100 -1200 {}
N 1100 -1040 1100 -1000 {}
N 1660 -1100 1700 -1100 {}
N 1500 -1100 1370 -1100 {}
N 1500 -1080 1460 -1080 {}
N 1580 -1160 1580 -1200 {}
N 1580 -1040 1580 -1000 {}
T {TB_NOISE  -  output noise of midref, 10 Hz - 1 GHz, and the tap-to-output transfer} 60 -1330 0 0 0.7 0.7 {}
T {SUPPLY + BIAS} 60 -1260 0 0 0.4 0.4 {}
T {I_B = 12.36 uA} 250 -1010 0 0 0.3 0.3 {layer=4}
T {DUT} 1000 -1260 0 0 0.4 0.4 {}
C {devices/vsource.sym} 120 -1130 0 0 {name=VDD_SOURCE value="3.3" savecurrent=false}
C {devices/lab_pin.sym} 120 -1200 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1060 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/isource.sym} 290 -1130 0 0 {name=IREF value="\{IF\}"}
C {devices/lab_pin.sym} 290 -1200 0 0 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 290 -1060 0 0 {name=l4 sig_type=std_logic lab=ib}
C {devices/vsource.sym} 460 -1130 0 0 {name=VNIN value="DC 0 AC 1" savecurrent=false}
C {devices/lab_pin.sym} 460 -1200 0 0 {name=l5 sig_type=std_logic lab=nin}
C {devices/lab_pin.sym} 460 -1060 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/res.sym} 630 -1130 0 0 {name=RNIN value="1g" footprint=1206 device=resistor m=1}
C {devices/lab_pin.sym} 630 -1200 0 0 {name=l7 sig_type=std_logic lab=nin}
C {devices/lab_pin.sym} 630 -1060 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/isource.sym} 800 -1130 0 0 {name=IINJ value="DC 0 AC 1"}
C {devices/lab_pin.sym} 800 -1200 0 0 {name=l9 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 800 -1060 0 0 {name=l10 sig_type=std_logic lab=vin}
C {midref_div.sym} 1100 -1100 0 0 {name=XD}
C {devices/lab_pin.sym} 1220 -1100 0 1 {name=l11 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1100 -1200 0 0 {name=l12 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1100 -1000 0 0 {name=l13 sig_type=std_logic lab=0}
C {midref_buf.sym} 1580 -1100 0 0 {name=XB}
C {devices/lab_pin.sym} 1700 -1100 0 1 {name=l14 sig_type=std_logic lab=out}
C {devices/lab_pin.sym} 1370 -1100 0 0 {name=l15 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 1460 -1080 0 0 {name=l16 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 1580 -1200 0 0 {name=l17 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1580 -1000 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 800 -900 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.temp 27
.param IF=1.23557e-05
.control
set num_threads=1
set wr_singlescale
noise v(out) VNIN dec 20 10 1g
setplot noise1
wrdata nz_out.txt onoise_spectrum
setplot const
noise v(vin) VNIN dec 20 10 1g
setplot noise3
wrdata nz_tap.txt onoise_spectrum
setplot const
ac dec 20 10 1g
wrdata ac.txt vm(out) vm(vin)
quit
.endc"}
