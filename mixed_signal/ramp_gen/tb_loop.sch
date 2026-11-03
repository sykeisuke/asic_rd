v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 140 -700 140 -670 {}
N 140 -610 140 -580 {}
N 140 -420 140 -390 {}
N 140 -330 140 -300 {}
N 560 -740 560 -700 {}
N 560 -580 560 -540 {}
N 640 -660 700 -660 {}
N 640 -620 700 -620 {}
N 820 -620 880 -620 {}
N 820 -560 880 -560 {}
N 820 -500 880 -500 {}
N 820 -420 820 -390 {}
N 820 -330 820 -300 {}
N 940 -440 940 -360 {}
N 940 -360 940 -280 {}
N 940 -280 970 -280 {}
N 1000 -720 1000 -680 {}
N 1000 -440 1000 -400 {}
N 1030 -280 1060 -280 {}
N 1060 -440 1060 -400 {}
N 1060 -400 1060 -300 {}
N 1060 -400 1160 -400 {}
N 1060 -300 1060 -280 {}
N 1120 -560 1180 -560 {}
N 1160 -400 1160 -380 {}
N 1160 -320 1160 -280 {}
N 1180 -560 1640 -560 {}
N 1640 -560 1640 -490 {}
N 1640 -560 1900 -560 {}
N 1640 -430 1640 -380 {}
N 1900 -560 1900 -510 {}
N 1900 -450 1900 -420 {}
N 1900 -420 1900 -390 {}
N 1900 -330 1900 -300 {}
N 1900 -300 1900 -270 {}
N 1900 -210 1900 -180 {}
T {TB_LOOP  -  loop gain of ramp_gen, Middlebrook double injection at the OTA input} 60 -900 0 0 0.70 0.70 {}
T {supply and bias} 60 -780 0 0 0.45 0.45 {layer=13}
T {reset and start level} 60 -480 0 0 0.45 0.45 {layer=13}
T {ramp generator, loop broken at XM1's gate} 820 -780 0 0 0.45 0.45 {layer=13}
T {MODE = 1 (reset)} 820 -740 0 0 0.35 0.35 {layer=4}
T {Middlebrook injection} 560 -240 0 0 0.45 0.45 {layer=13}
T {load; DC path of MODE 0} 1620 -780 0 0 0.45 0.45 {layer=13}
T {NCELL = 4} 1660 -700 0 0 0.35 0.35 {layer=4}
C {devices/vsource.sym} 140 -640 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 140 -700 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 140 -580 0 1 {name=l2 sig_type=std_logic lab=0}
C {../ramp_gen/ref/unit_cell_bps/bias_blk.sym} 560 -640 0 0 {name=XBIAS model=bias_gen}
C {devices/lab_pin.sym} 560 -740 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 560 -540 0 1 {name=l4 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 700 -660 0 1 {name=l5 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -620 0 1 {name=l6 sig_type=std_logic lab=nbias}
C {devices/vsource.sym} 140 -360 0 0 {name=VRST value="\{MODE*VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 140 -420 0 1 {name=l7 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 140 -300 0 1 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 820 -360 0 0 {name=VRLO value="0.5" savecurrent=false}
C {devices/lab_pin.sym} 820 -420 0 1 {name=l9 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 820 -300 0 1 {name=l10 sig_type=std_logic lab=0}
C {ramp_gen_lb.sym} 1000 -560 0 0 {name=XRG model=ramp_gen_lb}
C {devices/lab_pin.sym} 820 -620 0 0 {name=l11 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 820 -560 0 0 {name=l12 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 820 -500 0 0 {name=l13 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1000 -720 0 1 {name=l14 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1000 -400 0 1 {name=l15 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1180 -560 0 1 {name=l16 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 940 -360 0 0 {name=l17 sig_type=std_logic lab=vx}
C {devices/lab_pin.sym} 1060 -300 0 1 {name=l18 sig_type=std_logic lab=vxg}
C {devices/vsource.sym} 1000 -280 1 0 {name=VP value="DC 0 AC 1" savecurrent=false}
C {devices/isource.sym} 1160 -350 2 0 {name=IP value="DC 0 AC 0" savecurrent=false}
C {devices/lab_pin.sym} 1160 -280 0 1 {name=l19 sig_type=std_logic lab=0}
C {devices/capa.sym} 1640 -460 0 0 {name=CL value="\{NCELL*CLOAD_CELL+1f\}" m=1}
C {devices/lab_pin.sym} 1640 -380 0 1 {name=l20 sig_type=std_logic lab=0}
C {devices/ind.sym} 1900 -480 0 0 {name=LDC value="\{1e9*(1-MODE)+1e-9\}" m=1}
C {devices/lab_pin.sym} 1900 -420 0 1 {name=l21 sig_type=std_logic lab=nl}
C {devices/vsource.sym} 1900 -360 0 0 {name=VOP_SRC value="\{(VOP-0.5)*(1-MODE)\}" savecurrent=false}
C {devices/lab_pin.sym} 1900 -300 0 1 {name=l22 sig_type=std_logic lab=vxo}
C {devices/res.sym} 1900 -240 0 0 {name=RDCX value="\{1+1e15*MODE\}" m=1}
C {devices/lab_pin.sym} 1900 -180 0 1 {name=l23 sig_type=std_logic lab=vx}
C {devices/code_shown.sym} 60 -160 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice moscap_typical
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/work/ramp_gen_lb.spice
.param VDD=3.3
.param CLOAD_CELL=10f
.param MODE=1
.param VOP=0.5
.param NCELL=4
.options gmin=1e-15
.control
set num_threads=1
set wr_singlescale
set wr_vecnames
op
let op_vramp = v(vramp)
let op_vx = v(vx)
print op_vramp op_vx
ac dec 40 1k 1G
let tv = -v(vx)/v(vxg)
setplot const
alter VP acmag=0
alter IP acmag=1
ac dec 40 1k 1G
let ipr = i(vp)
let ti = -ipr/(1-ipr)
let tv = ac1.tv
let t = (tv*ti-1)/(tv+ti+2)
let tmag = db(t)
let tph = 180/pi*cph(t)
wrdata loop.csv tmag tph
quit
.endc"}
