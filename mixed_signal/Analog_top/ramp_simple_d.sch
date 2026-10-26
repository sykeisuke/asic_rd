v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 320 -560 320 -470 {}
N 320 -560 480 -560 {}
N 320 -410 320 -300 {}
N 320 -300 460 -300 {}
N 460 -300 460 -210 {}
N 460 -300 720 -300 {}
N 460 -150 460 0 {}
N 640 -180 680 -180 {}
N 720 -300 720 -210 {}
N 720 -300 900 -300 {}
N 720 -150 720 -60 {}
T {current source} 220 -640 0 0 0.45 0.45 {layer=13}
T {integrating capacitor} 380 -380 0 0 0.35 0.35 {layer=13}
T {reset to vrlo} 680 -380 0 0 0.35 0.35 {layer=13}
T {Id 0.475 uA, gm/Id 14.3 S/A} 340 -545 0 0 0.35 0.35 {layer=4}
T {C = 4.00 pF} 480 -140 0 0 0.45 0.45 {layer=4}
T {switch: Ron not recorded} 740 -125 0 0 0.32 0.32 {layer=4}
T {XPS -- current source (pfet_03v3)} 1020 -635 0 0 0.50 0.50 {}
T {L 8.000u  W 23.910u  nf 3  (numbers from data/ramp_simple_params.spice)
Id 0.475 uA   gm/Id 14.28 S/A   rout 730 Mohm
   DC op at vramp = 1.3 V (mid-ramp) on bias_gen, typical 27 C
   (size_simple.py -> data/sizing_simple.json = simple_size_* in runs/ramp-gen/20261003T001715Z)
In the ramp transient: mean Id 0.475 uA; at the overrange top
   |Vds| 1.18 V against Vdsat 0.09 V (margin 1.09 V, simple_nom_ps_*)
Predicted bow from gds over the 1.6 V swing: 0.15 LSB} 1020 -605 0 0 0.38 0.38 {}
L 4 1000 -650 2154 -650 {}
L 4 2154 -650 2154 -419 {}
L 4 2154 -419 1000 -419 {}
L 4 1000 -419 1000 -650 {}
T {XCR -- integrating capacitor} 1020 -380 0 0 0.50 0.50 {}
T {cap_mim_2f0_m4m5_noshield, 44.6 x 44.6 um
C = 4.001 pF: PDK model (mimcap_typical), AC at 1 kHz, 0.8 V bias
   (size_simple.py; simple_size_c in runs/ramp-gen/20261003T001715Z)
check: 1.99 fF/um2 x area + 0.238 fF/um x perimeter = 4.001 pF
Slope current I = C x SLOPE = 0.4689 uA (before the transient trim)} 1020 -350 0 0 0.38 0.38 {}
L 4 1000 -395 1835 -395 {}
L 4 1835 -395 1835 -208 {}
L 4 1835 -208 1000 -208 {}
L 4 1000 -208 1000 -395 {}
T {XRST -- reset switch (nfet_03v3)} 1020 -180 0 0 0.50 0.50 {}
T {W 0.500u  L 0.28u  nf 1; rst high shorts vramp to vrlo
Ron and gm/Id: not recorded (a switch, off during the ramp)
channel charge ~1.4 fC = ~0.2 mV pedestal on 4 pF (same switch
   as ramp_gen's XRST: ramp_gen/DESIGN_RECIPE.md s.3, derived)} 1020 -150 0 0 0.38 0.38 {}
L 4 1000 -195 1766 -195 {}
L 4 1766 -195 1766 -30 {}
L 4 1766 -30 1000 -30 {}
L 4 1000 -30 1000 -195 {}
C {devices/opin.sym} 20 -480 0 0 {name=p_vramp lab=vramp}
C {devices/ipin.sym} 20 -440 0 0 {name=p_rst lab=rst}
C {devices/ipin.sym} 20 -400 0 0 {name=p_vrlo lab=vrlo}
C {devices/ipin.sym} 20 -360 0 0 {name=p_ibias lab=ibias}
C {devices/iopin.sym} 20 -320 0 0 {name=p_vdd lab=vdd}
C {devices/iopin.sym} 20 -280 0 0 {name=p_vss lab=vss}
C {devices/lab_pin.sym} 480 -560 0 1 {name=l1 sig_type=std_logic lab=vdd}
C {symbols/pfet_03v3.sym} 300 -440 0 0 {name=XPS
L=8u
W=23.91u
nf=3
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 280 -440 0 0 {name=l2 sig_type=std_logic lab=ibias}
C {devices/lab_pin.sym} 320 -440 0 1 {name=l3 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 900 -300 0 1 {name=l4 sig_type=std_logic lab=vramp}
C {symbols/cap_mim_2f0fF.sym} 460 -180 0 0 {name=XCR W=44.6u L=44.6u model=cap_mim_2f0_m4m5_noshield spiceprefix="" m=1}
C {devices/lab_pin.sym} 460 0 0 1 {name=l5 sig_type=std_logic lab=vss}
C {symbols/nfet_03v3.sym} 700 -180 0 0 {name=XRST
L=0.28u
W=0.5u
nf=1
m=1
model=nfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
C {devices/lab_pin.sym} 720 -180 0 1 {name=l6 sig_type=std_logic lab=vss}
C {devices/lab_pin.sym} 720 -60 0 1 {name=l7 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 640 -180 0 0 {name=l8 sig_type=std_logic lab=rst}
C {symbols/pfet_03v3.sym} -220 -440 0 0 {name=XRD
L=1u
W=20u
nf=10
m=1
model=pfet_03v3
spiceprefix=""
format="@name @pinlist @model L=@L W=@W nf=@nf m=@m"}
N -200 -410 -200 -380 {lab=ibias}
N -240 -440 -260 -440 {lab=ibias}
N -260 -440 -260 -380 {lab=ibias}
N -260 -380 -200 -380 {lab=ibias}
C {devices/lab_pin.sym} -260 -380 0 0 {name=lv4_1 sig_type=std_logic lab=ibias}
N -200 -470 -200 -500 {lab=vdd}
C {devices/lab_pin.sym} -200 -500 0 1 {name=lv4_2 sig_type=std_logic lab=vdd}
N -200 -440 -160 -440 {lab=vdd}
C {devices/lab_pin.sym} -160 -440 0 1 {name=lv4_3 sig_type=std_logic lab=vdd}
T {XRD  pbias diode
20 / 1 um, nf 10
(current in: iramp from
bias_gen_v2s, 3.25 uA design)} -380 -330 0 0 0.3 0.3 {layer=13}
T {RAMP_SIMPLE_D  -  the shared ramp with its own pbias diode, sizes as numbers (Analog_top)} 20 -1045 0 0 0.7 0.7 {}
T {The three devices, wires and notes of ../ramp_gen/ramp_simple.sch, copied by analog_top_sch.py with every
\{RS_*\} parameter replaced by its value from ../ramp_gen/data/ramp_simple_params.spice: XPS L 8u W 23.91u nf 3,
XCR 44.6u x 44.6u MIM (4.00 pF), XRST W 0.5u L 0.28u. Plus XRD: PMOS diode W/L = 20 / 1 um, nf 10, drain = gate = ibias.
bias_gen_s SINKS iramp from ibias (a CURRENT input); XPS mirrors the diode by (23.91/8) : (20/1) = 0.15x.
Pins (subckt order): vramp rst vrlo ibias vdd vss. vrlo comes from vrlo_ref (5/33 AVDD, ADR 0018).
vramp = vrlo + I t / C: 0.5 -> 2.0 V in 256 counts of 50 ns. rst HIGH holds vramp at vrlo through XRST.
The operating-point notes below are the block's OWN bench (bias_gen); in the macro: the op table on analog_top.sch.} 20 -990 0 0 0.4 0.4 {}
