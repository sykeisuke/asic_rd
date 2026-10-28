* tb_ramp_adc4_ctl -- timeline, parameters, measures and analysis of the
* xschem testbench tb_ramp_adc4.sch (included by its code block).
*
* The run directory provides case.spice:
*   POS0..POS3   the four levels, in LSB above VR_LO (vin_i = VR_LO + POS_i LSB)
*   RAMP_REAL    1 = the cells see ramp_gen's vramp, 0 = the ideal PWL ramp
*   TPRE         rst falls TPRE before TR (0 = the contract: ramp starts at TR)
*   VRLO_TRIM    added to vrlo (V); vrlo = VR_LO - SLOPE x TPRE + VRLO_TRIM
*
* Timeline (unit_cell_bps CONTRACT.md, shifted by T0 for the cold start):
*   0 .. TPWR  vdd 0 -> 3.3 V; s0, s2 high (track), s1 low, rst high (reset)
*   TS         S2 opens (the sample); TISO S0 opens; TCONN S1 closes
*   TR - TPRE  rst falls: the ramp leaves vrlo
*   TR         the count starts; TE = TR + 256 TCOUNT; 20-count overrun
.include case.spice
.param VDD=3.3
.param NCODE=256
.param TCOUNT=50n
.param VR_LO=0.5
.param VR_HI=2.0
.param LSB='(VR_HI-VR_LO)/NCODE'
.param TRAMP='NCODE*TCOUNT'
.param SLOPE='(VR_HI-VR_LO)/TRAMP'
.param VIN0='VR_LO+POS0*LSB'
.param VIN1='VR_LO+POS1*LSB'
.param VIN2='VR_LO+POS2*LSB'
.param VIN3='VR_LO+POS3*LSB'
.param TPWR=100n
.param T0=7u
.param TEDGE=100p
.param TS='T0+300n'
.param TNOV=5n
.param TISO='TS+TNOV'
.param TCONN='TS+2*TNOV'
.param TR='T0+400n'
.param TE='TR+TRAMP'
.param TOVR='20*TCOUNT'
.param VR_OVR='VR_HI+SLOPE*TOVR'
.param TSTOP='TE+TOVR+100n'
.param VRLO_V='VR_LO-SLOPE*TPRE+VRLO_TRIM'
.param RSEL_REAL='RAMP_REAL*1e-3+(1-RAMP_REAL)*1e12'
.param RSEL_IDEAL='RAMP_REAL*1e12+(1-RAMP_REAL)*1e-3'

* gmin 1e-15: the floating top plates (unit_cell_bps tb, switches/)
.options reltol=1e-4 gmin=1e-15 savecurrents
.tran 0.1n {TSTOP} 0 2n

.measure tran vin0 PARAM='VIN0'
.measure tran vin1 PARAM='VIN1'
.measure tran vin2 PARAM='VIN2'
.measure tran vin3 PARAM='VIN3'
.measure tran ramp_real PARAM='RAMP_REAL'
.measure tran tpre PARAM='TPRE'
* the ramp as the cells see it
.measure tran vr_tconn FIND v(vr_cell) AT={TCONN-1n}
.measure tran vr_kick_max MAX v(vr_cell) FROM={TCONN} TO={TR}
.measure tran vr_tr FIND v(vr_cell) AT={TR}
.measure tran vr_te FIND v(vr_cell) AT={TE}
.measure tran vr_ovr FIND v(vr_cell) AT={TE+TOVR}
.measure tran vref_ts FIND v(vref) AT={TS}
.measure tran vbl_tr FIND v(vbl) AT={TR}
.measure tran pbias_tr FIND v(pbias) AT={TR}
.measure tran pbias_min MIN v(pbias) FROM={TR} TO={TE+TOVR}
.measure tran pbias_max MAX v(pbias) FROM={TR} TO={TE+TOVR}
* per cell: the analog crossing, the decision, the code
.measure tran t_top0 WHEN v(xc0.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran t_top1 WHEN v(xc1.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran t_top2 WHEN v(xc2.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran t_top3 WHEN v(xc3.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran t_dout0 WHEN v(dout0)='VDD/2' FALL=1 TD={TR}
.measure tran t_dout1 WHEN v(dout1)='VDD/2' FALL=1 TD={TR}
.measure tran t_dout2 WHEN v(dout2)='VDD/2' FALL=1 TD={TR}
.measure tran t_dout3 WHEN v(dout3)='VDD/2' FALL=1 TD={TR}
.measure tran dout0_tr FIND v(dout0) AT={TR}
.measure tran dout1_tr FIND v(dout1) AT={TR}
.measure tran dout2_tr FIND v(dout2) AT={TR}
.measure tran dout3_tr FIND v(dout3) AT={TR}
.measure tran vr_top0 FIND v(vr_cell) WHEN v(xc0.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran vr_top1 FIND v(vr_cell) WHEN v(xc1.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran vr_top2 FIND v(vr_cell) WHEN v(xc2.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran vr_top3 FIND v(vr_cell) WHEN v(xc3.top)=v(vbl) RISE=1 TD={TR-TPRE}
.measure tran t_trip0 PARAM='t_dout0-TR'
.measure tran t_trip1 PARAM='t_dout1-TR'
.measure tran t_trip2 PARAM='t_dout2-TR'
.measure tran t_trip3 PARAM='t_dout3-TR'
.measure tran code0 PARAM='floor(t_trip0/TCOUNT)'
.measure tran code1 PARAM='floor(t_trip1/TCOUNT)'
.measure tran code2 PARAM='floor(t_trip2/TCOUNT)'
.measure tran code3 PARAM='floor(t_trip3/TCOUNT)'
.measure tran err0 PARAM='(t_trip0-(VIN0-VR_LO)/SLOPE)/TCOUNT'
.measure tran err1 PARAM='(t_trip1-(VIN1-VR_LO)/SLOPE)/TCOUNT'
.measure tran err2 PARAM='(t_trip2-(VIN2-VR_LO)/SLOPE)/TCOUNT'
.measure tran err3 PARAM='(t_trip3-(VIN3-VR_LO)/SLOPE)/TCOUNT'
* power over the ramp, per block
.measure tran i_ramp AVG i(vmramp) FROM={TR} TO={TE}
.measure tran i_cells AVG i(vmcell) FROM={TR} TO={TE}
.measure tran i_bias AVG i(vmbias) FROM={TR} TO={TE}
.measure tran p_ramp PARAM='VDD*i_ramp'
.measure tran p_cells PARAM='VDD*i_cells'
.measure tran p_bias PARAM='VDD*i_bias'

.control
set num_threads=1
set wr_singlescale
set wr_vecnames
run
wrdata wave.csv v(vr_cell) v(vramp) v(videal) v(dout0) v(dout1) v(dout2) v(dout3) v(xc0.top) v(xc1.top) v(xc2.top) v(xc3.top) v(vbl) v(rst) v(s1) v(pbias)
quit
.endc
