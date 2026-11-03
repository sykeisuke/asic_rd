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
N 220 -530 220 -490 {}
N 180 -560 140 -560 {}
N 220 -590 220 -630 {}
N 220 -560 330 -560 {}
N 720 -560 760 -560 {}
N 560 -560 520 -560 {}
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
T {TB_NOISE  -  output noise of vrlo_ref in reset, 1 Hz - 1 GHz, and AVDD -> vrlo} 40 -1240 0 0 0.7 0.7 {}
T {SUPPLY (AC 1) + BIAS + NOISE INPUT} 60 -1120 0 0 0.45 0.45 {}
T {DUT} 560 -760 0 0 0.45 0.45 {}
T {RAMP LOAD (../ramp_gen) + four cells' CEQ} 1000 -760 0 0 0.45 0.45 {}
T {I_B = 1.37 uA} 260 -880 0 0 0.35 0.35 {layer=4}
T {I_RD = 3.25 uA} 430 -880 0 0 0.35 0.35 {layer=4}
T {7/55 AVDD} 560 -410 0 0 0.35 0.35 {layer=4}
T {CEQ = 4 x 40 fF} 1380 -410 0 0 0.35 0.35 {layer=4}
C {devices/vsource.sym} 120 -980 0 0 {name=VAVDD value="DC 3.3 AC 1" savecurrent=false}
C {devices/isource.sym} 290 -980 0 0 {name=IB value="1.37e-06"}
C {vrlo_ref.sym} 640 -560 0 0 {name=XREG}
C {devices/isource.sym} 460 -980 0 0 {name=IRD value="3.2512e-06"}
C {symbols/pfet_03v3.sym} 200 -560 0 0 {name=XRD
L=1u
W=20u
nf=10
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {ramp_simple.sym} 1120 -560 0 0 {name=XRAMP}
C {devices/capa.sym} 1420 -560 0 0 {name=CEQ value="\{4*4e-14\}" m=1}
C {devices/vsource.sym} 630 -980 0 0 {name=VNIN value="DC 0 AC 1" savecurrent=false}
C {devices/res.sym} 800 -980 0 0 {name=RNIN value="1g" m=1}
C {devices/lab_pin.sym} 120 -1050 0 0 {name=l1 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 120 -910 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 290 -1050 0 0 {name=l3 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 290 -910 0 0 {name=l4 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 460 -1050 0 0 {name=l5 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 460 -910 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 630 -1050 0 0 {name=l7 sig_type=std_logic lab=nin}
C {devices/lab_pin.sym} 630 -910 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 800 -1050 0 0 {name=l9 sig_type=std_logic lab=nin}
C {devices/lab_pin.sym} 800 -910 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 220 -490 0 0 {name=l11 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 140 -560 0 0 {name=l12 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 220 -630 0 0 {name=l13 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 330 -560 0 1 {name=l14 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 760 -560 0 1 {name=l15 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 520 -560 0 0 {name=l16 sig_type=std_logic lab=ib}
C {devices/lab_pin.sym} 640 -660 0 0 {name=l17 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 640 -460 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1280 -560 0 1 {name=l19 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 960 -560 0 0 {name=l20 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 960 -620 0 0 {name=l21 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 960 -500 0 0 {name=l22 sig_type=std_logic lab=pbias_r}
C {devices/lab_pin.sym} 1120 -720 0 0 {name=l23 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1120 -400 0 0 {name=l24 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 1420 -630 0 0 {name=l25 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1420 -490 0 0 {name=l26 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 40 -300 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice
.temp 27
.options gmin=1e-15
.control
set num_threads=1
set wr_singlescale
noise v(vrlo) VNIN dec 20 1 1g
setplot noise1
wrdata nz_vrlo.txt onoise_spectrum
setplot const
noise v(vramp) VNIN dec 20 1 1g
setplot noise3
wrdata nz_vramp.txt onoise_spectrum
setplot const
ac dec 10 1 1g
wrdata psr.txt vm(vrlo)
quit
.endc"}
