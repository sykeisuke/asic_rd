v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {bias_gen_s: bias generator} 60 -220 0 0 0.3 0.3 {layer=13}
T {midref_div: VDD/2 divider} 500 -220 0 0 0.3 0.3 {layer=13}
T {midref_buf: VDD/2 buffer} 820 -220 0 0 0.3 0.3 {layer=13}
T {vrlo_ref: VR_LO regulator} 1200 -220 0 0 0.3 0.3 {layer=13}
T {ic_source: I/C ramp current} 1660 -220 0 0 0.3 0.3 {layer=13}
T {ramp_simple: ramp capacitor + reset} 2160 -220 0 0 0.3 0.3 {layer=13}
T {comparator_d: comparator} 60 180 0 0 0.3 0.3 {layer=13}
T {latch: D flip-flop} 500 180 0 0 0.3 0.3 {layer=13}
T {sw_s0 / sw_s1: TG switch} 820 180 0 0 0.3 0.3 {layer=13}
T {sw_s2: NMOS switch} 1160 180 0 0 0.3 0.3 {layer=13}
T {atop_cell: unit cell} 1720 400 0 0 0.3 0.3 {layer=13}
T {ANALOG_TOP  -  SUB-BLOCK SYMBOLS} 0 -700 0 0 0.8 0.8 {}

C {bias_gen_s.sym} 200 -400 0 0 {name=XBG}
C {midref_div.sym} 640 -400 0 0 {name=XDIV}
C {midref_buf.sym} 960 -400 0 0 {name=XVREF}
C {vrlo_ref.sym} 1340 -400 0 0 {name=XVRLO}
C {ic_source.sym} 1800 -400 0 0 {name=XIC}
C {ramp_simple.sym} 2300 -400 0 0 {name=XRAMP}
C {comparator_d.sym} 200 0 0 0 {name=XCMP}
C {latch.sym} 640 0 0 0 {name=XFF}
C {sw_s0.sym} 960 0 0 0 {name=XS0}
C {sw_s2.sym} 1300 0 0 0 {name=XS2}
C {atop_cell.sym} 1860 140 0 0 {name=XC0}
C {devices/title.sym} 0 500 0 0 {name=l999 author="ASIC R&D - mixed_signal/Analog_top - symbol_gallery"}
