v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1010 120 -1050 {}
N 120 -950 120 -910 {}
N 290 -1010 290 -1050 {}
N 290 -950 290 -910 {}
N 460 -1010 460 -1050 {}
N 460 -950 460 -910 {}
N 630 -1010 630 -1050 {}
N 630 -950 630 -910 {}
N 800 -1010 800 -1050 {}
N 800 -950 800 -910 {}
N 970 -1010 970 -1050 {}
N 970 -950 970 -910 {}
N 220 -530 220 -490 {}
N 180 -560 140 -560 {}
N 220 -590 220 -630 {}
N 220 -560 330 -560 {}
N 720 -560 760 -560 {}
N 560 -540 520 -540 {}
N 560 -580 520 -580 {}
N 640 -620 640 -660 {}
N 640 -500 640 -460 {}
N 1240 -560 1280 -560 {}
N 1000 -560 960 -560 {}
N 1000 -620 960 -620 {}
N 1000 -500 960 -500 {}
N 1120 -680 1120 -720 {}
N 1120 -440 1120 -400 {}
N 1420 -590 1420 -630 {}
N 1420 -530 1420 -490 {}
N 1580 -590 1580 -630 {}
N 1580 -530 1580 -490 {}
T {TB_LOOP  -  loop gain of vrlo_ref by voltage injection at XM1's gate, RST = 1} 40 -1240 0 0 0.7 0.7 {}
T {SUPPLY + BIAS + INJECTION} 60 -1120 0 0 0.45 0.45 {}
T {DUT  loop broken, fb = XM1 gate} 480 -760 0 0 0.45 0.45 {}
T {RAMP LOAD (../ramp_gen) + four cells' CEQ} 1060 -760 0 0 0.45 0.45 {}
T {I_B = 1.37 uA} 260 -880 0 0 0.35 0.35 {layer=4}
T {I_RD = 3.25 uA} 430 -880 0 0 0.35 0.35 {layer=4}
T {CEQ = 4 x 40 fF} 1380 -410 0 0 0.35 0.35 {layer=4}
C {devices/vsource.sym} 120 -980 0 0 {name=VAVDD value="3.3" savecurrent=false}
C {devices/isource.sym} 290 -980 0 0 {name=IB value="1.37e-06"}
C {vrlo_ref_lb.sym} 640 -560 0 0 {name=XREG}
C {devices/vsource.sym} 970 -980 0 0 {name=VINJ value="DC 0 AC 1" savecurrent=false}
C {devices/isource.sym} 460 -980 0 0 {name=IRD value="3.2512e-06"}
C {symbols/pfet_03v3.sym} 200 -560 0 0 {name=XRD
L=1u
W=20u
nf=10
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/vsource.sym} 630 -980 0 0 {name=VRST value="\{1*3.3\}" savecurrent=false}
C {ramp_simple.sym} 1120 -560 0 0 {name=XRAMP}
C {devices/capa.sym} 1420 -560 0 0 {name=CEQ value="\{4*4e-14\}" m=1}
C {devices/res.sym} 1580 -560 0 0 {name=RHOLD value="1g" m=1}
C {devices/vsource.sym} 800 -980 0 0 {name=VHOLD value="1.3" savecurrent=false}
C {devices/lab_pin.sym} 120 -1050 0 0 {name=l1 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 120 -910 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 290 -1050 0 0 {name=l3 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 290 -910 0 0 {name=l4 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 460 -1050 0 0 {name=l5 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 460 -910 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 630 -1050 0 0 {name=l7 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 630 -910 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 800 -1050 0 0 {name=l9 sig_type=std_logic lab=vhold}
C {devices/lab_pin.sym} 800 -910 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 970 -1050 0 0 {name=l11 sig_type=std_logic lab=fb}
C {devices/lab_pin.sym} 970 -910 0 0 {name=l12 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 220 -490 0 0 {name=l13 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 140 -560 0 0 {name=l14 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 220 -630 0 0 {name=l15 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 330 -560 0 1 {name=l16 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 760 -560 0 1 {name=l17 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 520 -540 0 0 {name=l18 sig_type=std_logic lab=fb}
C {devices/lab_pin.sym} 520 -580 0 0 {name=l19 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 640 -660 0 0 {name=l20 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 640 -460 0 0 {name=l21 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1280 -560 0 1 {name=l22 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 960 -560 0 0 {name=l23 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 960 -620 0 0 {name=l24 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 960 -500 0 0 {name=l25 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 1120 -720 0 0 {name=l26 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1120 -400 0 0 {name=l27 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1420 -630 0 0 {name=l28 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1420 -490 0 0 {name=l29 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1580 -630 0 0 {name=l30 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1580 -490 0 0 {name=l31 sig_type=std_logic lab=vhold}
C {devices/code_shown.sym} 40 -300 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice
.include /foss/designs/mixed_signal/vrlo_ref/work/dut_lb.spice
.temp 27
.options gmin=1e-15
.control
set num_threads=1
op
ac dec 40 10 10g
let t = -v(vrlo)/v(fb)
let tdb = db(t)
let tph = 180/pi*cph(t)
meas ac ugb_hz WHEN tdb=0 FALL=1
meas ac ph_ugb FIND tph AT=ugb_hz
let pm = 180 + ph_ugb
let pmr = pm - 360*floor((pm+180)/360)
echo pm_deg = $&pmr
meas ac t0_db FIND tdb AT=10
quit
.endc"}
