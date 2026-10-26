v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 160 -880 480 -880 {}
N 160 -360 360 -360 {}
N 240 -800 440 -800 {}
N 240 -680 320 -680 {}
N 300 -740 360 -740 {}
N 300 -560 360 -560 {}
N 320 -480 360 -480 {}
N 360 -740 360 -710 {}
N 360 -740 480 -740 {}
N 360 -680 400 -680 {}
N 360 -650 360 -560 {}
N 360 -560 360 -510 {}
N 360 -560 480 -560 {}
N 360 -450 360 -360 {}
N 360 -360 580 -360 {}
N 400 -480 480 -480 {}
N 480 -880 480 -830 {}
N 480 -880 860 -880 {}
N 480 -800 520 -800 {}
N 480 -770 480 -740 {}
N 480 -740 580 -740 {}
N 480 -560 480 -480 {}
N 480 -480 540 -480 {}
N 540 -680 580 -680 {}
N 580 -740 580 -710 {}
N 580 -650 580 -600 {}
N 580 -600 580 -510 {}
N 580 -600 680 -600 {}
N 580 -480 620 -480 {}
N 580 -450 580 -360 {}
N 580 -360 860 -360 {}
N 620 -680 700 -680 {}
N 680 -640 680 -600 {}
N 680 -600 800 -600 {}
N 780 -800 820 -800 {}
N 800 -680 800 -600 {}
N 800 -680 820 -680 {}
N 800 -600 800 -520 {}
N 800 -520 820 -520 {}
N 860 -880 860 -830 {}
N 860 -880 1080 -880 {}
N 860 -800 900 -800 {}
N 860 -770 860 -740 {}
N 860 -740 860 -710 {}
N 860 -740 920 -740 {}
N 860 -680 900 -680 {}
N 860 -650 860 -600 {}
N 860 -600 860 -550 {}
N 860 -600 960 -600 {}
N 860 -520 900 -520 {}
N 860 -490 860 -360 {}
N 860 -360 1080 -360 {}
N 960 -640 960 -600 {}
N 960 -600 1020 -600 {}
N 1020 -680 1020 -600 {}
N 1020 -680 1040 -680 {}
N 1020 -600 1020 -520 {}
N 1020 -520 1040 -520 {}
N 1080 -880 1080 -710 {}
N 1080 -880 1240 -880 {}
N 1080 -680 1120 -680 {}
N 1080 -650 1080 -600 {}
N 1080 -600 1080 -550 {}
N 1080 -600 1200 -600 {}
N 1080 -520 1120 -520 {}
N 1080 -490 1080 -360 {}
N 1080 -360 1240 -360 {}
T {33 uA} 235 -850 0 0 0.28 0.28 {layer=4}
T {16 uA*} 615 -850 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 130 -630 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 625 -722 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 150 -452 0 0 0.28 0.28 {layer=4}
T {16.5 uA} 600 -452 0 0 0.28 0.28 {layer=4}
T {37 uA*} 1100 -760 0 0 0.28 0.28 {layer=4}
T {(VBL, VDD/2)} 150 -660 0 0 0.3 0.3 {}
T {(MIM top plate)} 705 -662 0 0 0.3 0.3 {}
T {PMOS 5T OTA} 320 -412 0 0 0.4 0.4 {}
T {starved inverter} 760 -412 0 0 0.4 0.4 {}
T {output inverter} 1000 -412 0 0 0.4 0.4 {}
C {devices/iopin.sym} 160 -880 0 0 {name=pvdd lab=vdd}
C {devices/iopin.sym} 160 -360 0 0 {name=pvss lab=vss}
C {symbols/pfet_03v3.sym} 460 -800 0 0 {name=TAIL
L=0.28u W=11u nf=11 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 520 -800 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {devices/ipin.sym} 240 -800 0 0 {name=pibias lab=ibias}
C {devices/lab_pin.sym} 300 -740 0 0 {name=l2 sig_type=std_logic lab=tail}
C {symbols/pfet_03v3.sym} 340 -680 0 0 {name=INP
L=0.32u W=12u nf=12 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/pfet_03v3.sym} 600 -680 0 1 {name=INN
L=0.32u W=12u nf=12 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {devices/ipin.sym} 240 -680 0 0 {name=pinp lab=inp}
C {devices/ipin.sym} 700 -680 0 1 {name=pinn lab=inn}
C {devices/lab_pin.sym} 400 -680 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 540 -680 0 0 {name=l4 sig_type=std_logic lab=vdd}
C {symbols/nfet_03v3.sym} 380 -480 0 1 {name=LOADD
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {symbols/nfet_03v3.sym} 560 -480 0 0 {name=LOADM
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 300 -560 0 0 {name=l5 sig_type=std_logic lab=left}
C {devices/lab_pin.sym} 320 -480 0 0 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 620 -480 0 1 {name=l7 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 680 -640 0 0 {name=l8 sig_type=std_logic lab=outa}
C {symbols/pfet_03v3.sym} 840 -800 0 0 {name=BST
L=0.28u W=5u nf=5 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/pfet_03v3.sym} 840 -680 0 0 {name=BUF2
L=0.36u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/nfet_03v3.sym} 840 -520 0 0 {name=BUF1
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 920 -740 0 1 {name=l9 sig_type=std_logic lab=bst}
C {devices/lab_pin.sym} 780 -800 0 0 {name=l10 sig_type=std_logic lab=ibias}
C {devices/lab_pin.sym} 900 -800 0 1 {name=l11 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -680 0 1 {name=l12 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -520 0 1 {name=l13 sig_type=std_logic lab=vss}
C {symbols/pfet_03v3.sym} 1060 -680 0 0 {name=BUF4
L=0.36u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
C {symbols/nfet_03v3.sym} 1060 -520 0 0 {name=BUF3
L=0.36u W=0.5u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 960 -640 0 0 {name=l14 sig_type=std_logic lab=outb}
C {devices/lab_pin.sym} 1120 -680 0 1 {name=l15 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 1120 -520 0 1 {name=l16 sig_type=std_logic lab=vss}
C {devices/opin.sym} 1200 -600 0 0 {name=pdout lab=dout}
C {symbols/pfet_03v3.sym} 20 -760 0 0 {name=REFP
L=0.28u W=1u nf=1 m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0 model=pfet_03v3 spiceprefix=X}
N 40 -730 40 -700 {lab=ibias}
N 0 -760 -20 -760 {lab=ibias}
N -20 -760 -20 -700 {lab=ibias}
N -20 -700 40 -700 {lab=ibias}
C {devices/lab_pin.sym} -20 -700 0 0 {name=lv4_1 sig_type=std_logic lab=ibias}
N 40 -790 40 -820 {lab=vdd}
C {devices/lab_pin.sym} 40 -820 0 1 {name=lv4_2 sig_type=std_logic lab=vdd}
N 40 -760 80 -760 {lab=vdd}
C {devices/lab_pin.sym} 80 -760 0 1 {name=lv4_3 sig_type=std_logic lab=vdd}
T {XREFP  pbias diode  1 / 0.28 um
(current in: icmp_k from
bias_gen_v2s, 3.25 uA design)} -170 -660 0 0 0.3 0.3 {layer=13}
T {CMP_UPDT_V3D  -  comparator with its own pbias diode (Analog_top)} 140 -1315 0 0 0.7 0.7 {}
T {The ten devices, wires and bench notes of ../comparator/comparator.sch (ADR 0015), copied by
analog_top_sch.py, plus XREFP: PMOS diode W/L = 1 / 0.28 um, drain = gate = ibias. bias_gen_s SINKS
icmp_k from ibias, so ibias is a CURRENT input; its diode voltage biases XTAIL (11 fingers) and XBST (5).
Pins (subckt order, = the symbol's): inp inn ibias dout vdd vss. The old no-connect ports clk / nbias are gone.
dout is HIGH while inn < inp and falls when inn (the cell's bot plate) rises through inp (vbl).
Every MOS here, XREFP included, uses the PDK symbol's S/D junction geometry template.
Currents next to the devices: design values in THIS macro, I_B = icmp_k = 3.25 uA (1.68 x the comparator's
1.93 uA sizing bias, ADR 0017), the same as on ../comparator/comparator.sch (* during tracking).} 160 -1240 0 0 0.4 0.4 {}
T {Design currents in this macro (I_B = 3.25 uA)} 1350 -865 0 0 0.5 0.5 {}
T {I_B = icmp_k = 3.25 uA into XREFP: bias_gen_s's comparator sink, sized 1.68 x the comparator's
   1.93 uA sizing bias for its worst untrimmed PVT cell (ADR 0017).  Branches: the comparator's sizing
   record x the same ratio (../comparator/intent.py), as on comparator.sch and the CPAD slide.

XTAIL            11 x 1 um, L 0.28      33 uA
XINP / XINN      12 x 1 um, L 0.32      16.5 uA each
XLOADD / XLOADM  1 x 0.5 um, L 0.36     16.5 uA each
XBST             5 x 1 um, L 0.28       16 uA*  (starved inverter)
XBUF4 / XBUF3    1 x 1 / 1 x 0.5 um     37 uA*  (output inverter)
   * during tracking.  XBUF4 is not a sized current: its crowbar as ngspice gives it.
Static power converting (design): 3.3 V x (3.25 + 33) uA = 120 uW (diode + tail).

Simulated static power: converting 107-110 uW, tracking 285 uW in this macro (pwr record, typical);
   converting <= 238 uW over bias_gen's 135 PVT cells (comparator/gain_pvt.py).
The op record puts the tail ~10 % under the design (L 0.28 um channel-length modulation;
   check_intent.py reports it; gm/Id, gds, Vds - Vdsat per device: the op table on analog_top.sch).} 1350 -830 0 0 0.35 0.35 {}
L 4 1330 -880 2461 -880 {}
L 4 2461 -880 2461 -474 {}
L 4 2461 -474 1330 -474 {}
L 4 1330 -474 1330 -880 {}
