v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -950 120 -990 {}
N 120 -890 120 -850 {}
N 290 -950 290 -990 {}
N 290 -890 290 -850 {}
N 460 -950 460 -990 {}
N 460 -890 460 -850 {}
N 630 -950 630 -990 {}
N 630 -890 630 -850 {}
N 800 -950 800 -990 {}
N 800 -890 800 -850 {}
N 1000 -950 1000 -990 {}
N 1000 -890 1000 -850 {}
N 1170 -950 1170 -990 {}
N 1170 -890 1170 -850 {}
N 120 -690 120 -730 {}
N 120 -630 120 -590 {}
N 120 -490 120 -530 {}
N 120 -430 120 -390 {}
N 120 -290 120 -330 {}
N 120 -230 120 -190 {}
N 120 -90 120 -130 {}
N 120 -30 120 10 {}
N 120 110 120 70 {}
N 120 170 120 210 {}
N 1880 -900 1940 -900 {}
N 1600 -900 1540 -900 {}
N 1600 -820 1540 -820 {}
N 1740 -740 1740 -700 {}
N 2410 -720 2350 -720 {}
N 2410 -680 2350 -680 {}
N 2410 -640 2350 -640 {}
N 2410 -600 2350 -600 {}
N 2410 -560 2350 -560 {}
N 2410 -520 2350 -520 {}
N 2410 -480 2350 -480 {}
N 2410 -440 2350 -440 {}
N 2790 -720 2850 -720 {}
N 2410 -400 2350 -400 {}
N 2515 -780 2455 -780 {}
N 2515 -340 2455 -340 {}
N 2685 -780 2745 -780 {}
N 2685 -340 2745 -340 {}
N 3000 -670 3000 -710 {}
N 3000 -610 3000 -570 {}
T {TB_CELL_TN  -  one bottom-plate cell on ramp_simple, transient noise of a conversion} 40 -1200 0 0 0.7 0.7 {}
T {SUPPLIES / REFS} 40 -1060 0 0 0.5 0.5 {layer=4}
T {CONTROLS} 40 -780 0 0 0.5 0.5 {layer=4}
T {CELL} 1500 -1060 0 0 0.5 0.5 {layer=4}
T {CQ = 40 fF} 3080 -650 0 0 0.36 0.36 {layer=4}
C {devices/vsource.sym} 120 -920 0 0 {name=VAVDD value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 120 -990 0 0 {name=l1 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 120 -850 0 0 {name=l2 sig_type=std_logic lab=0}
C {devices/vsource.sym} 290 -920 0 0 {name=VDVDD value="\{VDD\}" savecurrent=false}
C {devices/lab_pin.sym} 290 -990 0 0 {name=l3 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 290 -850 0 0 {name=l4 sig_type=std_logic lab=0}
C {devices/vsource.sym} 460 -920 0 0 {name=VVREF value="\{VMID\}" savecurrent=false}
C {devices/lab_pin.sym} 460 -990 0 0 {name=l5 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 460 -850 0 0 {name=l6 sig_type=std_logic lab=0}
C {devices/vsource.sym} 630 -920 0 0 {name=VVRLO value="\{VR_LO\}" savecurrent=false}
C {devices/lab_pin.sym} 630 -990 0 0 {name=l7 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 630 -850 0 0 {name=l8 sig_type=std_logic lab=0}
C {devices/vsource.sym} 800 -920 0 0 {name=VVIN value="\{VIN\}" savecurrent=false}
C {devices/lab_pin.sym} 800 -990 0 0 {name=l9 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 800 -850 0 0 {name=l10 sig_type=std_logic lab=0}
C {devices/isource.sym} 1000 -920 0 0 {name=IRAMP value="\{IRAMP\}"}
C {devices/lab_pin.sym} 1000 -990 0 0 {name=l11 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 1000 -850 0 0 {name=l12 sig_type=std_logic lab=vramp}
C {devices/isource.sym} 1170 -920 0 0 {name=ICMP value="\{IREF_CMP\}"}
C {devices/lab_pin.sym} 1170 -990 0 0 {name=l13 sig_type=std_logic lab=ibc}
C {devices/lab_pin.sym} 1170 -850 0 0 {name=l14 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -660 0 0 {name=VS2 value="PULSE(\{VDD\} 0 \{TFIRST\} \{TEDGE\} \{TEDGE\} \{TRREL+NCNT*TCOUNT+10n-TEDGE\} \{PCONV\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -730 0 0 {name=l15 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 120 -590 0 0 {name=l16 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -460 0 0 {name=VS0 value="PULSE(\{VDD\} 0 \{TFIRST+TNOV\} \{TEDGE\} \{TEDGE\} \{TRREL+NCNT*TCOUNT+10n-TEDGE-TNOV\} \{PCONV\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -530 0 0 {name=l17 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 120 -390 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -260 0 0 {name=VS1 value="PULSE(0 \{VDD\} \{TFIRST+2*TNOV\} \{TEDGE\} \{TEDGE\} \{TRREL+NCNT*TCOUNT-2*TNOV-TEDGE\} \{PCONV\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -330 0 0 {name=l19 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 120 -190 0 0 {name=l20 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 -60 0 0 {name=VRST value="PULSE(\{VDD\} 0 \{TFIRST+TRREL\} \{TEDGE\} \{TEDGE\} \{NCNT*TCOUNT+5n-TEDGE\} \{PCONV\})" savecurrent=false}
C {devices/lab_pin.sym} 120 -130 0 0 {name=l21 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 120 10 0 0 {name=l22 sig_type=std_logic lab=0}
C {devices/vsource.sym} 120 140 0 0 {name=VCLK value="PULSE(0 \{VDD\} \{TCLK0\} \{TEDGE\} \{TEDGE\} \{TCOUNT/2-TEDGE\} \{TCOUNT\})" savecurrent=false}
C {devices/lab_pin.sym} 120 70 0 0 {name=l23 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 120 210 0 0 {name=l24 sig_type=std_logic lab=0}
C {ramp_simple.sym} 1740 -860 0 0 {name=XR}
C {devices/lab_pin.sym} 1940 -900 0 1 {name=l25 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 1540 -900 0 0 {name=l26 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 1540 -820 0 0 {name=l27 sig_type=std_logic lab=vrlo}
C {devices/lab_pin.sym} 1740 -700 0 0 {name=l28 sig_type=std_logic lab=0}
C {atop_cell.sym} 2600 -560 0 0 {name=XC}
C {devices/lab_pin.sym} 2350 -720 0 0 {name=l29 sig_type=std_logic lab=vin}
C {devices/lab_pin.sym} 2350 -680 0 0 {name=l30 sig_type=std_logic lab=vramp}
C {devices/lab_pin.sym} 2350 -640 0 0 {name=l31 sig_type=std_logic lab=s0}
C {devices/lab_pin.sym} 2350 -600 0 0 {name=l32 sig_type=std_logic lab=s1}
C {devices/lab_pin.sym} 2350 -560 0 0 {name=l33 sig_type=std_logic lab=s2}
C {devices/lab_pin.sym} 2350 -520 0 0 {name=l34 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2350 -480 0 0 {name=l35 sig_type=std_logic lab=vref}
C {devices/lab_pin.sym} 2350 -440 0 0 {name=l36 sig_type=std_logic lab=ibc}
C {devices/lab_pin.sym} 2850 -720 0 1 {name=l37 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 2350 -400 0 0 {name=l38 sig_type=std_logic lab=clk}
C {devices/lab_pin.sym} 2455 -780 0 0 {name=l39 sig_type=std_logic lab=avdd}
C {devices/lab_pin.sym} 2455 -340 0 0 {name=l40 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 2745 -780 0 1 {name=l41 sig_type=std_logic lab=dvdd}
C {devices/lab_pin.sym} 2745 -340 0 1 {name=l42 sig_type=std_logic lab=0}
C {devices/capa.sym} 3000 -640 0 0 {name=CQ value="\{CQ\}" m=1}
C {devices/lab_pin.sym} 3000 -710 0 0 {name=l43 sig_type=std_logic lab=q}
C {devices/lab_pin.sym} 3000 -570 0 0 {name=l44 sig_type=std_logic lab=0}
C {devices/code_shown.sym} 1000 -150 0 0 {name=CTL only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice
.include /foss/designs/mixed_signal/cell_trannoise/tb_params.inc
.temp 27
.options rshunt=1e15 gmin=1e-15
.csparam cs_tstop=\{TSTOP\}
.control
set filetype=binary
tran 0.1n $&cs_tstop
write tb_cell_tn.raw v(q) v(clk) v(vramp) v(xc.dout) v(xc.bot) v(xc.xcmp.outa) v(xc.xcmp.outb) v(xc.xcmp.bst) v(xc.xcmp.tail) v(xc.xff.xff.a_853_68#) v(xc.xff.xff.a_1315_24#) i(vvrlo)
quit
.endc"}
