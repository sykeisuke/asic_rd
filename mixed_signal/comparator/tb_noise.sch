v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -1210 120 -1250 {}
N 120 -1150 120 -1110 {}
N 290 -1210 290 -1250 {}
N 290 -1150 290 -1110 {}
N 460 -1210 460 -1250 {}
N 460 -1150 460 -1110 {}
N 630 -1210 630 -1250 {}
N 630 -1150 630 -1110 {}
N 120 -930 120 -970 {}
N 120 -870 120 -830 {}
N 300 -900 260 -900 {}
N 340 -930 340 -970 {}
N 340 -870 340 -830 {}
N 340 -900 380 -900 {}
N 480 -930 480 -970 {}
N 480 -870 480 -830 {}
N 660 -900 620 -900 {}
N 700 -870 700 -830 {}
N 700 -930 700 -970 {}
N 700 -900 740 -900 {}
N 1100 -790 1100 -830 {}
N 1100 -730 1100 -690 {}
N 1100 -1090 1100 -1130 {}
N 1100 -1030 1100 -990 {}
N 1300 -1060 1260 -1060 {}
N 1300 -1030 1260 -1030 {}
N 1300 -1000 1260 -1000 {}
N 1300 -970 1260 -970 {}
N 1300 -940 1260 -940 {}
N 1500 -1045 1540 -1045 {}
N 1400 -1120 1400 -1160 {}
N 1400 -880 1400 -840 {}
N 1640 -1030 1640 -1070 {}
N 1640 -970 1640 -930 {}
T {tb_noise: input-referred noise of comparator at its decision point (the tb_nz bench)} 60 -1549 0 0 0.7 0.7 {}
T {dout is fed back to inn through 1 TH, which parks the OTA at its own trip; CINN (1 F) AC-grounds inn.
nz_own_vin: output noise on outa from 1 kHz to 10 GHz divided by the DC gain (thermal + 1/f, own band); gate < 1.2 mV.
Measures: ota_gain_vv (|outa / inp| at 10 Hz), nz_own_vin (V rms at the pins).  Gates: block < 1.2 mV rms
   (= 0.25 LSB at the ADC input); this drawing equal to tb_nz.spice within 1 % (xtb.py).
Recorded (runs/comparator-updt-v3-schematic/20261007T232627Z): gain 44.52 V/V, noise 0.168 mV, drawing = bench
   (rel 2e-6); with drawn S/D geometry 0.163 mV.  Typical 27 C, 3.3 V, ideal bias.
Values: LFB 1 TH (DC feedback only, open at AC), CINN 1 F (AC ground of inn), CLOAD 10 fF.
Reproduce: make comparator-schematic.} 60 -1507 0 0 0.4 0.4 {}
L 4 40 -1564 1746 -1564 {}
L 4 1746 -1564 1746 -1290 {}
L 4 1746 -1290 40 -1290 {}
L 4 40 -1290 40 -1564 {}
T {AVDD (comparator) and the bias supply; VINP = DC 1.65 AC 1, VCLK = {VDD}} 60 -1080 0 0 0.32 0.32 {layer=4}
T {pbias: I_B = 1.93 uA design (.param IREF = 1.93077e-06 A, data/sizing.json) into one tail finger (L 0.28u, W 1u), diode-connected: tail 20 uA, pair 10 uA each, starve 9.6 uA design (intent.py); nbias leg (REFN, L 1u W 20u nf 10) unused: no-connect port} 60 -800 0 0 0.32 0.32 {layer=4}
C {devices/vsource.sym} 120 -1180 0 0 {name=VDD_SOURCE value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -1250 0 0 {name=l1 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 120 -1110 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -1180 0 0 {name=VDD_BIAS value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -1250 0 0 {name=l3 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 290 -1110 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 460 -1180 0 0 {name=VINP value="DC 1.65 AC 1" savecurrent=false}
C {devices/lab_pin.sym} 460 -1250 0 0 {name=l5 sig_type=std_logic lab=inp}
C {devices/lab_pin.sym} 460 -1110 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -1180 0 0 {name=VCLK value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 630 -1250 0 0 {name=l7 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 630 -1110 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/isource.sym} 120 -900 0 0 {name=IREFN value="\{IREF\}"}
C {devices/lab_pin.sym} 120 -970 0 0 {name=l9 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 120 -830 0 0 {name=l10 sig_type=std_logic lab=nbias}
C {symbols/nfet_03v3.sym} 320 -900 0 0 {name=REFN
L=1u W=20u nf=10 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 260 -900 0 0 {name=l11 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -970 0 0 {name=l12 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 340 -830 0 0 {name=l13 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 380 -900 0 1 {name=l14 sig_type=std_logic lab=0}
C {devices/isource.sym} 480 -900 0 0 {name=IREFP value="\{IREF\}"}
C {devices/lab_pin.sym} 480 -970 0 0 {name=l15 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 480 -830 0 0 {name=l16 sig_type=std_logic lab=0}
C {symbols/pfet_03v3.sym} 680 -900 0 0 {name=REFP
L=0.28u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 620 -900 0 0 {name=l17 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -830 0 0 {name=l18 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 700 -970 0 0 {name=l19 sig_type=std_logic lab=vddb}
C {devices/lab_pin.sym} 740 -900 0 1 {name=l20 sig_type=std_logic lab=vddb}
C {devices/capa.sym} 1100 -760 0 0 {name=CINN value=1 m=1}
C {devices/lab_pin.sym} 1100 -830 0 0 {name=l21 sig_type=std_logic lab=inn}
C {devices/lab_pin.sym} 1100 -690 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/ind.sym} 1100 -1060 0 0 {name=LFB value=1T m=1}
C {devices/lab_pin.sym} 1100 -1130 0 0 {name=l23 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1100 -990 0 0 {name=l24 sig_type=std_logic lab=inn}
C {comparator.sym} 1400 -1000 0 0 {name=XDUT}
C {devices/lab_pin.sym} 1260 -1060 0 0 {name=l25 sig_type=std_logic lab=inp}
C {devices/lab_pin.sym} 1260 -1030 0 0 {name=l26 sig_type=std_logic lab=inn}
C {devices/lab_pin.sym} 1260 -1000 0 0 {name=l27 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 1260 -970 0 0 {name=l28 sig_type=std_logic lab=nbias}
C {devices/lab_pin.sym} 1260 -940 0 0 {name=l29 sig_type=std_logic lab=pbias}
C {devices/lab_pin.sym} 1540 -1045 0 1 {name=l30 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1400 -1160 0 0 {name=l31 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1400 -840 0 0 {name=l32 sig_type=std_logic lab=0}
C {devices/capa.sym} 1640 -1000 0 0 {name=CLOAD value=10f m=1}
C {devices/lab_pin.sym} 1640 -1070 0 0 {name=l33 sig_type=std_logic lab=dout}
C {devices/lab_pin.sym} 1640 -930 0 0 {name=l34 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1000 -560 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.param VDD=3.3
.param IREF=1.93077e-06   $ data/sizing.json iref: ideal current into one tail finger
.temp 27
.options savecurrents
.control
op
ac dec 20 10 100G
meas ac ota_gain_vv find vm(xdut.outa) at=10
echo \"RESULT_BEGIN\"
print ota_gain_vv
set g = $&ota_gain_vv
noise v(xdut.outa) vinp dec 20 1k 10G
let nz_own_vin = onoise_total / $g
print nz_own_vin
echo \"RESULT_END\"
quit
.endc"}
