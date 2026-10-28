v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {bias_gen_s: constant-gm reference;
one current-source glyph per output
(arrow in = sink, out = source)} 60 -220 0 0 0.3 0.3 {layer=13}
T {midref_div: R + R from vdd,
mid tap VDD/2 with decap} 500 -220 0 0 0.3 0.3 {layer=13}
T {midref_buf: unity-gain
follower (x1), ib = bias} 820 -220 0 0 0.3 0.3 {layer=13}
T {vrlo_ref: 5/33 tap driving a
shunt regulator on vrlo} 1200 -220 0 0 0.3 0.3 {layer=13}
T {ramp_simple_d: sawtooth,
I / C from vrlo, rst = reset} 1660 -220 0 0 0.3 0.3 {layer=13}
T {comparator_d: comparator,
bias diode inside} 60 180 0 0 0.3 0.3 {layer=13}
T {latch: D flip-flop,
falling-edge clock} 500 180 0 0 0.3 0.3 {layer=13}
T {sw_s0 / sw_s1: transmission
gate (bubble = ctlb)} 820 180 0 0 0.3 0.3 {layer=13}
T {sw_s2: NMOS switch} 1160 180 0 0 0.3 0.3 {layer=13}
T {atop_cell: unit cell box with its
S/H -> C -> CMP -> DFF path} 1720 400 0 0 0.3 0.3 {layer=13}
T {ANALOG_TOP_V5  -  SUB-BLOCK SYMBOLS (symbols.py; analog_top.sym itself stays a rectangle)} 0 -700 0 0 0.8 0.8 {}

C {bias_gen_s.sym} 200 -400 0 0 {name=XBG}
C {midref_div.sym} 640 -400 0 0 {name=XDIV}
C {midref_buf.sym} 960 -400 0 0 {name=XVREF}
C {vrlo_ref.sym} 1340 -400 0 0 {name=XVRLO}
C {ramp_simple_d.sym} 1800 -400 0 0 {name=XRAMP}
C {comparator_d.sym} 200 0 0 0 {name=XCMP}
C {latch.sym} 640 0 0 0 {name=XFF}
C {sw_s0.sym} 960 0 0 0 {name=XS0}
C {sw_s2.sym} 1300 0 0 0 {name=XS2}
C {atop_cell.sym} 1860 140 0 0 {name=XC0}
C {devices/title.sym} 0 500 0 0 {name=l999 author="ASIC R&D - mixed_signal/Analog_top - symbol_gallery"}
