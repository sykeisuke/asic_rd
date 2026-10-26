* tb_measure.inc -- analysis, measures and waveform output of the functional
* record (tb_analog_top.spice includes it last). Owned by func.sh; the measure
* names are what data/func_measures.txt carries, what func_reduce.py and
* check-func.awk read, and what xtb.sh compares against. Rename here, rename
* there.
*
* gmin 1e-15: at the default 1e-12 the simulator drains every floating top
* plate through S2's drain junction by 1e-12 x v(top) (0.3-1.6 pA, measured in
* ../Analog_top_bkp/unit_cell_bps/switches/), a false level-dependent error of ~0.04 LSB
* (../Analog_top_bkp/unit_cell_bps/tb_unit_cell_bps.spice). reltol 1e-4 as in that bench.
.options reltol=1e-4 gmin=1e-15
* 0.1 ns print step, 2 ns ceiling: the count clock edges are 100 ps and the
* ramp moves 0.23 mV (0.04 LSB) per 2 ns, so no crossing is interpolated over
* more than 0.04 LSB.
.tran 0.1n {TSTOP} 0 2n
* the bias generator's output devices (their drain currents ARE the bias
* currents: sinks XOC0..3 / XOR from the pbias diodes, sources XOV / XOB into
* the buffers' ib) and its core branch; the reducer reads them from the CSV
.save all @m.xdut.xbg.xoc0.m0[id] @m.xdut.xbg.xoc1.m0[id] @m.xdut.xbg.xoc2.m0[id]
+ @m.xdut.xbg.xoc3.m0[id] @m.xdut.xbg.xor.m0[id] @m.xdut.xbg.xov.m0[id]
+ @m.xdut.xbg.xob.m0[id] @m.xdut.xbg.xmn1.m0[id]

* ---------------------------------------------------------------------------
* The timeline itself, echoed so the reducer and the checker never re-derive
* it (p_ = parameter; a measure must not share a name with a .param)
* ---------------------------------------------------------------------------
.measure tran p_vdd PARAM='VDD'
.measure tran p_lsb PARAM='LSB'
.measure tran p_slope PARAM='SLOPE'
.measure tran p_tcount PARAM='TCOUNT'
.measure tran p_vr_lo PARAM='VR_LO'
.measure tran p_vr_hi PARAM='VR_HI'
.measure tran p_cs PARAM='CS_C'
.measure tran p_tpwr PARAM='TPWR'
.measure tran p_t0 PARAM='T0'
.measure tran p_tnov PARAM='TNOV'
.measure tran p_tspace PARAM='TSPACE'
.measure tran p_tstep PARAM='TSTEP'
.measure tran p_tedge PARAM='TEDGE'
.measure tran p_ts0 PARAM='TS0'
.measure tran p_ts1 PARAM='TS1'
.measure tran p_ts2 PARAM='TS2'
.measure tran p_ts3 PARAM='TS3'
.measure tran p_tr PARAM='TR'
.measure tran p_te PARAM='TE'
.measure tran p_tovr PARAM='TOVR'
.measure tran p_tstop PARAM='TSTOP'
.measure tran p_tclk0 PARAM='TCLK0'
.measure tran p_pos0 PARAM='POS0'
.measure tran p_pos1 PARAM='POS1'
.measure tran p_pos2 PARAM='POS2'
.measure tran p_pos3 PARAM='POS3'
.measure tran p_vin0 PARAM='VIN0'
.measure tran p_vin1 PARAM='VIN1'
.measure tran p_vin2 PARAM='VIN2'
.measure tran p_vin3 PARAM='VIN3'

* ---------------------------------------------------------------------------
* Power-up: the supplies, then every bias / reference node at T0, at the first
* sample TS0 and at the end of the ramp TE (the reducer adds settling times)
* ---------------------------------------------------------------------------
.measure tran t_avdd90 WHEN v(avdd)='0.9*VDD' RISE=1
.measure tran t_dvdd90 WHEN v(dvdd)='0.9*VDD' RISE=1
.measure tran pbias0_at_t0 FIND v(xdut.pbias0) AT={T0}
.measure tran pbias1_at_t0 FIND v(xdut.pbias1) AT={T0}
.measure tran pbias2_at_t0 FIND v(xdut.pbias2) AT={T0}
.measure tran pbias3_at_t0 FIND v(xdut.pbias3) AT={T0}
.measure tran pbias_r_at_t0 FIND v(xdut.pbias_r) AT={T0}
.measure tran vmid_at_t0 FIND v(xdut.vmid) AT={T0}
.measure tran vref_at_t0 FIND v(xdut.vref) AT={T0}
.measure tran vbl_at_t0 FIND v(xdut.vbl) AT={T0}
.measure tran vramp_at_t0 FIND v(xdut.vramp) AT={T0}
.measure tran pbias0_at_ts0 FIND v(xdut.pbias0) AT={TS0}
.measure tran pbias1_at_ts0 FIND v(xdut.pbias1) AT={TS0}
.measure tran pbias2_at_ts0 FIND v(xdut.pbias2) AT={TS0}
.measure tran pbias3_at_ts0 FIND v(xdut.pbias3) AT={TS0}
.measure tran pbias_r_at_ts0 FIND v(xdut.pbias_r) AT={TS0}
.measure tran vmid_at_ts0 FIND v(xdut.vmid) AT={TS0}
.measure tran vref_at_ts0 FIND v(xdut.vref) AT={TS0}
.measure tran vbl_at_ts0 FIND v(xdut.vbl) AT={TS0}
.measure tran vramp_at_ts0 FIND v(xdut.vramp) AT={TS0}
.measure tran pbias0_at_te FIND v(xdut.pbias0) AT={TE}
.measure tran pbias1_at_te FIND v(xdut.pbias1) AT={TE}
.measure tran pbias2_at_te FIND v(xdut.pbias2) AT={TE}
.measure tran pbias3_at_te FIND v(xdut.pbias3) AT={TE}
.measure tran pbias_r_at_tr FIND v(xdut.pbias_r) AT={TR}
.measure tran pbias_r_at_te FIND v(xdut.pbias_r) AT={TE}
.measure tran vmid_at_te FIND v(xdut.vmid) AT={TE}
.measure tran vref_at_te FIND v(xdut.vref) AT={TE}
.measure tran vbl_at_te FIND v(xdut.vbl) AT={TE}
* VDD/2 error of the buffers at the first sample (common to VREF and VBL)
.measure tran vref_err_ts0 PARAM='vref_at_ts0-VMID'
.measure tran vbl_err_ts0 PARAM='vbl_at_ts0-VMID'
.measure tran vbl_vref_ts0 PARAM='vbl_at_ts0-vref_at_ts0'
* VBL over the conversion: kicks from the four decisions
.measure tran vbl_min MIN v(xdut.vbl) FROM={TR} TO={TE+TOVR}
.measure tran vbl_max MAX v(xdut.vbl) FROM={TR} TO={TE+TOVR}
.measure tran vbl_at_tr FIND v(xdut.vbl) AT={TR}

* ---------------------------------------------------------------------------
* Ramp: reset level, the release step, the end of the ramp and the overrun
* (slope, gain and INL come from the CSV in func_reduce.py)
* ---------------------------------------------------------------------------
.measure tran vramp_at_tr FIND v(xdut.vramp) AT={TR}
.measure tran vramp_at_tr5 FIND v(xdut.vramp) AT={TR+5n}
.measure tran vramp_at_te FIND v(xdut.vramp) AT={TE}
.measure tran vramp_at_tovr FIND v(xdut.vramp) AT={TE+TOVR}
.measure tran vramp_at_tstop FIND v(xdut.vramp) AT={TSTOP-1n}
.measure tran t_ramp_hi WHEN v(xdut.vramp)='VR_HI' RISE=1 TD={TR}
.measure tran n_ramp_hi PARAM='(t_ramp_hi-TR)/TCOUNT'

* ---------------------------------------------------------------------------
* Per cell k. Sample: S2 opens at TS_k (the sample), S0 at TS_k+TNOV, S1
* closes at TS_k+2TNOV, vin steps at TS_k+TSTEP. Conversion: top rises
* through vbl, dout falls, q falls at the next cnt_clk falling edge.
*   ped_top   top 2 ns after S2 opened minus top at TS_k: S2's injection
*   *_iso     plates just before S1 closes (S0 open, plates floating)
*   *_con     plates 20 ns after S1 closed (bot driven by vramp)
*   err_x     (analog crossing - TR)/TCOUNT - POS_k: continuous, LSB
*   err_d     the same from dout's fall (adds the comparator delay)
*   bps_err   vramp (= bot) at the crossing minus vin, LSB: what the plate
*             charge, S2's pedestal and VBL - VREF add, ramp-independent
*   refd      VBL at the crossing minus VREF at the sample
* ---------------------------------------------------------------------------
.measure tran vin_ts0 FIND v(vin) AT={TS0}
.measure tran vref_ts_0 FIND v(xdut.vref) AT={TS0}
.measure tran vbot_ts0 FIND v(xdut.xc0.bot) AT={TS0}
.measure tran vtop_ts0 FIND v(xdut.xc0.top) AT={TS0}
.measure tran vtop_s2_0 FIND v(xdut.xc0.top) AT={TS0+2n}
.measure tran ped_top0 PARAM='vtop_s2_0-vtop_ts0'
.measure tran vtop_iso0 FIND v(xdut.xc0.top) AT={TS0+2*TNOV-0.5n}
.measure tran vbot_iso0 FIND v(xdut.xc0.bot) AT={TS0+2*TNOV-0.5n}
.measure tran vtop_con0 FIND v(xdut.xc0.top) AT={TS0+2*TNOV+20n}
.measure tran vbot_con0 FIND v(xdut.xc0.bot) AT={TS0+2*TNOV+20n}
.measure tran vtop_tr0 FIND v(xdut.xc0.top) AT={TR}
.measure tran vbot_tr0 FIND v(xdut.xc0.bot) AT={TR}
.measure tran dout_tr0 FIND v(xdut.xc0.dout) AT={TR}
.measure tran q_tr0 FIND v(q0) AT={TR}
.measure tran t_top0 WHEN v(xdut.xc0.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbot_top0 FIND v(xdut.xc0.bot) WHEN v(xdut.xc0.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbl_top0 FIND v(xdut.vbl) WHEN v(xdut.xc0.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran t_dout0 WHEN v(xdut.xc0.dout)='VDD/2' FALL=1 TD={TR}
.measure tran t_d90_0 WHEN v(xdut.xc0.dout)='0.9*VDD' FALL=1 TD={TR}
.measure tran t_d10_0 WHEN v(xdut.xc0.dout)='0.1*VDD' FALL=1 TD={TR}
.measure tran t_q0 WHEN v(q0)='VDD/2' FALL=1 TD={TR}
.measure tran dout_tf0 PARAM='t_d10_0-t_d90_0'
.measure tran cmp_delay0 PARAM='t_dout0-t_top0'
.measure tran q_delay0 PARAM='t_q0-t_dout0'
.measure tran code0 PARAM='floor((t_q0-TR)/TCOUNT)'
.measure tran code_ideal0 PARAM='floor((VIN0-VR_LO)/LSB)'
.measure tran code_err0 PARAM='code0-code_ideal0'
.measure tran err_x0 PARAM='(t_top0-TR)/TCOUNT-POS0'
.measure tran err_d0 PARAM='(t_dout0-TR)/TCOUNT-POS0'
.measure tran bps_err0 PARAM='(vbot_top0-VIN0)/LSB'
.measure tran alpha0 PARAM='(vbl_top0-vtop_tr0)/(vbot_top0-vbot_tr0)'
.measure tran refd0 PARAM='vbl_top0-vref_ts_0'
.measure tran vtop_min0 MIN v(xdut.xc0.top) FROM={TS0+2*TNOV+20n} TO={TSTOP}
.measure tran vtop_max0 MAX v(xdut.xc0.top) FROM={TS0+2*TNOV+20n} TO={TSTOP}

.measure tran vin_ts1 FIND v(vin) AT={TS1}
.measure tran vref_ts_1 FIND v(xdut.vref) AT={TS1}
.measure tran vbot_ts1 FIND v(xdut.xc1.bot) AT={TS1}
.measure tran vtop_ts1 FIND v(xdut.xc1.top) AT={TS1}
.measure tran vtop_s2_1 FIND v(xdut.xc1.top) AT={TS1+2n}
.measure tran ped_top1 PARAM='vtop_s2_1-vtop_ts1'
.measure tran vtop_iso1 FIND v(xdut.xc1.top) AT={TS1+2*TNOV-0.5n}
.measure tran vbot_iso1 FIND v(xdut.xc1.bot) AT={TS1+2*TNOV-0.5n}
.measure tran vtop_con1 FIND v(xdut.xc1.top) AT={TS1+2*TNOV+20n}
.measure tran vbot_con1 FIND v(xdut.xc1.bot) AT={TS1+2*TNOV+20n}
.measure tran vtop_tr1 FIND v(xdut.xc1.top) AT={TR}
.measure tran vbot_tr1 FIND v(xdut.xc1.bot) AT={TR}
.measure tran dout_tr1 FIND v(xdut.xc1.dout) AT={TR}
.measure tran q_tr1 FIND v(q1) AT={TR}
.measure tran t_top1 WHEN v(xdut.xc1.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbot_top1 FIND v(xdut.xc1.bot) WHEN v(xdut.xc1.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbl_top1 FIND v(xdut.vbl) WHEN v(xdut.xc1.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran t_dout1 WHEN v(xdut.xc1.dout)='VDD/2' FALL=1 TD={TR}
.measure tran t_d90_1 WHEN v(xdut.xc1.dout)='0.9*VDD' FALL=1 TD={TR}
.measure tran t_d10_1 WHEN v(xdut.xc1.dout)='0.1*VDD' FALL=1 TD={TR}
.measure tran t_q1 WHEN v(q1)='VDD/2' FALL=1 TD={TR}
.measure tran dout_tf1 PARAM='t_d10_1-t_d90_1'
.measure tran cmp_delay1 PARAM='t_dout1-t_top1'
.measure tran q_delay1 PARAM='t_q1-t_dout1'
.measure tran code1 PARAM='floor((t_q1-TR)/TCOUNT)'
.measure tran code_ideal1 PARAM='floor((VIN1-VR_LO)/LSB)'
.measure tran code_err1 PARAM='code1-code_ideal1'
.measure tran err_x1 PARAM='(t_top1-TR)/TCOUNT-POS1'
.measure tran err_d1 PARAM='(t_dout1-TR)/TCOUNT-POS1'
.measure tran bps_err1 PARAM='(vbot_top1-VIN1)/LSB'
.measure tran alpha1 PARAM='(vbl_top1-vtop_tr1)/(vbot_top1-vbot_tr1)'
.measure tran refd1 PARAM='vbl_top1-vref_ts_1'
.measure tran vtop_min1 MIN v(xdut.xc1.top) FROM={TS1+2*TNOV+20n} TO={TSTOP}
.measure tran vtop_max1 MAX v(xdut.xc1.top) FROM={TS1+2*TNOV+20n} TO={TSTOP}

.measure tran vin_ts2 FIND v(vin) AT={TS2}
.measure tran vref_ts_2 FIND v(xdut.vref) AT={TS2}
.measure tran vbot_ts2 FIND v(xdut.xc2.bot) AT={TS2}
.measure tran vtop_ts2 FIND v(xdut.xc2.top) AT={TS2}
.measure tran vtop_s2_2 FIND v(xdut.xc2.top) AT={TS2+2n}
.measure tran ped_top2 PARAM='vtop_s2_2-vtop_ts2'
.measure tran vtop_iso2 FIND v(xdut.xc2.top) AT={TS2+2*TNOV-0.5n}
.measure tran vbot_iso2 FIND v(xdut.xc2.bot) AT={TS2+2*TNOV-0.5n}
.measure tran vtop_con2 FIND v(xdut.xc2.top) AT={TS2+2*TNOV+20n}
.measure tran vbot_con2 FIND v(xdut.xc2.bot) AT={TS2+2*TNOV+20n}
.measure tran vtop_tr2 FIND v(xdut.xc2.top) AT={TR}
.measure tran vbot_tr2 FIND v(xdut.xc2.bot) AT={TR}
.measure tran dout_tr2 FIND v(xdut.xc2.dout) AT={TR}
.measure tran q_tr2 FIND v(q2) AT={TR}
.measure tran t_top2 WHEN v(xdut.xc2.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbot_top2 FIND v(xdut.xc2.bot) WHEN v(xdut.xc2.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbl_top2 FIND v(xdut.vbl) WHEN v(xdut.xc2.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran t_dout2 WHEN v(xdut.xc2.dout)='VDD/2' FALL=1 TD={TR}
.measure tran t_d90_2 WHEN v(xdut.xc2.dout)='0.9*VDD' FALL=1 TD={TR}
.measure tran t_d10_2 WHEN v(xdut.xc2.dout)='0.1*VDD' FALL=1 TD={TR}
.measure tran t_q2 WHEN v(q2)='VDD/2' FALL=1 TD={TR}
.measure tran dout_tf2 PARAM='t_d10_2-t_d90_2'
.measure tran cmp_delay2 PARAM='t_dout2-t_top2'
.measure tran q_delay2 PARAM='t_q2-t_dout2'
.measure tran code2 PARAM='floor((t_q2-TR)/TCOUNT)'
.measure tran code_ideal2 PARAM='floor((VIN2-VR_LO)/LSB)'
.measure tran code_err2 PARAM='code2-code_ideal2'
.measure tran err_x2 PARAM='(t_top2-TR)/TCOUNT-POS2'
.measure tran err_d2 PARAM='(t_dout2-TR)/TCOUNT-POS2'
.measure tran bps_err2 PARAM='(vbot_top2-VIN2)/LSB'
.measure tran alpha2 PARAM='(vbl_top2-vtop_tr2)/(vbot_top2-vbot_tr2)'
.measure tran refd2 PARAM='vbl_top2-vref_ts_2'
.measure tran vtop_min2 MIN v(xdut.xc2.top) FROM={TS2+2*TNOV+20n} TO={TSTOP}
.measure tran vtop_max2 MAX v(xdut.xc2.top) FROM={TS2+2*TNOV+20n} TO={TSTOP}

.measure tran vin_ts3 FIND v(vin) AT={TS3}
.measure tran vref_ts_3 FIND v(xdut.vref) AT={TS3}
.measure tran vbot_ts3 FIND v(xdut.xc3.bot) AT={TS3}
.measure tran vtop_ts3 FIND v(xdut.xc3.top) AT={TS3}
.measure tran vtop_s2_3 FIND v(xdut.xc3.top) AT={TS3+2n}
.measure tran ped_top3 PARAM='vtop_s2_3-vtop_ts3'
.measure tran vtop_iso3 FIND v(xdut.xc3.top) AT={TS3+2*TNOV-0.5n}
.measure tran vbot_iso3 FIND v(xdut.xc3.bot) AT={TS3+2*TNOV-0.5n}
.measure tran vtop_con3 FIND v(xdut.xc3.top) AT={TS3+2*TNOV+20n}
.measure tran vbot_con3 FIND v(xdut.xc3.bot) AT={TS3+2*TNOV+20n}
.measure tran vtop_tr3 FIND v(xdut.xc3.top) AT={TR}
.measure tran vbot_tr3 FIND v(xdut.xc3.bot) AT={TR}
.measure tran dout_tr3 FIND v(xdut.xc3.dout) AT={TR}
.measure tran q_tr3 FIND v(q3) AT={TR}
.measure tran t_top3 WHEN v(xdut.xc3.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbot_top3 FIND v(xdut.xc3.bot) WHEN v(xdut.xc3.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran vbl_top3 FIND v(xdut.vbl) WHEN v(xdut.xc3.top)=v(xdut.vbl) RISE=1 TD={TR}
.measure tran t_dout3 WHEN v(xdut.xc3.dout)='VDD/2' FALL=1 TD={TR}
.measure tran t_d90_3 WHEN v(xdut.xc3.dout)='0.9*VDD' FALL=1 TD={TR}
.measure tran t_d10_3 WHEN v(xdut.xc3.dout)='0.1*VDD' FALL=1 TD={TR}
.measure tran t_q3 WHEN v(q3)='VDD/2' FALL=1 TD={TR}
.measure tran dout_tf3 PARAM='t_d10_3-t_d90_3'
.measure tran cmp_delay3 PARAM='t_dout3-t_top3'
.measure tran q_delay3 PARAM='t_q3-t_dout3'
.measure tran code3 PARAM='floor((t_q3-TR)/TCOUNT)'
.measure tran code_ideal3 PARAM='floor((VIN3-VR_LO)/LSB)'
.measure tran code_err3 PARAM='code3-code_ideal3'
.measure tran err_x3 PARAM='(t_top3-TR)/TCOUNT-POS3'
.measure tran err_d3 PARAM='(t_dout3-TR)/TCOUNT-POS3'
.measure tran bps_err3 PARAM='(vbot_top3-VIN3)/LSB'
.measure tran alpha3 PARAM='(vbl_top3-vtop_tr3)/(vbot_top3-vbot_tr3)'
.measure tran refd3 PARAM='vbl_top3-vref_ts_3'
.measure tran vtop_min3 MIN v(xdut.xc3.top) FROM={TS3+2*TNOV+20n} TO={TSTOP}
.measure tran vtop_max3 MAX v(xdut.xc3.top) FROM={TS3+2*TNOV+20n} TO={TSTOP}

* ---------------------------------------------------------------------------
* Power over the ramp [TR, TE]. The VM* ammeters split AVDD per block:
*   bg    bias_gen core, startup and the two SOURCE outputs (2 x ib into
*         the buffers); the sink outputs' currents are drawn from the cells'
*         and the ramp's supplies through their pbias diodes
*   ref   the shared divider and both midref_buf (their ib arrives from bg)
*   ramp  ramp_simple's source and its pbias diode XRD (iramp)
*   c<k>  cell k: comparator, its pbias diode (icmp_k), switch inverters
* DVDD: the four TSPC latches and their 40 fF loads (the clock source's own
* power into the latch clock pins is not on DVDD).
* ---------------------------------------------------------------------------
.measure tran i_avdd AVG i(vavdd) FROM={TR} TO={TE}
.measure tran i_dvdd AVG i(vdvdd) FROM={TR} TO={TE}
.measure tran i_bg AVG i(v.xdut.vmbg) FROM={TR} TO={TE}
.measure tran i_ref AVG i(v.xdut.vmref) FROM={TR} TO={TE}
.measure tran i_ramp AVG i(v.xdut.vmramp) FROM={TR} TO={TE}
.measure tran i_c0 AVG i(v.xdut.vmc0) FROM={TR} TO={TE}
.measure tran i_c1 AVG i(v.xdut.vmc1) FROM={TR} TO={TE}
.measure tran i_c2 AVG i(v.xdut.vmc2) FROM={TR} TO={TE}
.measure tran i_c3 AVG i(v.xdut.vmc3) FROM={TR} TO={TE}
.measure tran pw_avdd PARAM='-VDD*i_avdd'
.measure tran pw_dvdd PARAM='-VDD*i_dvdd'
.measure tran pw_total PARAM='pw_avdd+pw_dvdd'
.measure tran pw_bg PARAM='VDD*i_bg'
.measure tran pw_ref PARAM='VDD*i_ref'
.measure tran pw_ramp PARAM='VDD*i_ramp'
.measure tran pw_c0 PARAM='VDD*i_c0'
.measure tran pw_c1 PARAM='VDD*i_c1'
.measure tran pw_c2 PARAM='VDD*i_c2'
.measure tran pw_c3 PARAM='VDD*i_c3'
.measure tran pw_cells PARAM='pw_c0+pw_c1+pw_c2+pw_c3'
.measure tran pw_split_err PARAM='pw_avdd-pw_bg-pw_ref-pw_ramp-pw_cells'
* the tracking state before the samples, for comparison: [T0, TS0] (top =
* vref, so every comparator sits at its own trip point)
.measure tran i_avdd_idle AVG i(vavdd) FROM={T0} TO={TS0}
.measure tran i_dvdd_idle AVG i(vdvdd) FROM={T0} TO={TS0}
.measure tran i_bg_idle AVG i(v.xdut.vmbg) FROM={T0} TO={TS0}
.measure tran i_ref_idle AVG i(v.xdut.vmref) FROM={T0} TO={TS0}
.measure tran i_ramp_idle AVG i(v.xdut.vmramp) FROM={T0} TO={TS0}
.measure tran i_c0_idle AVG i(v.xdut.vmc0) FROM={T0} TO={TS0}
.measure tran i_c1_idle AVG i(v.xdut.vmc1) FROM={T0} TO={TS0}
.measure tran i_c2_idle AVG i(v.xdut.vmc2) FROM={T0} TO={TS0}
.measure tran i_c3_idle AVG i(v.xdut.vmc3) FROM={T0} TO={TS0}
.measure tran pw_avdd_idle PARAM='-VDD*i_avdd_idle'
.measure tran pw_dvdd_idle PARAM='-VDD*i_dvdd_idle'
.measure tran pw_bg_idle PARAM='VDD*i_bg_idle'
.measure tran pw_ref_idle PARAM='VDD*i_ref_idle'
.measure tran pw_ramp_idle PARAM='VDD*i_ramp_idle'
.measure tran pw_cells_idle PARAM='VDD*(i_c0_idle+i_c1_idle+i_c2_idle+i_c3_idle)'
* each cell after its decision (dout low), last 500 ns before TSTOP
.measure tran i_c0_post AVG i(v.xdut.vmc0) FROM={TSTOP-500n} TO={TSTOP}
.measure tran pw_c0_post PARAM='VDD*i_c0_post'

.control
set num_threads=1
set wr_singlescale
set wr_vecnames
run
wrdata wave.csv v(avdd) v(dvdd) v(vin) v(ramp_rst) v(cnt_clk) v(xdut.pbias0) v(xdut.pbias1) v(xdut.pbias2) v(xdut.pbias3) v(xdut.pbias_r) v(xdut.vmid) v(xdut.vref) v(xdut.vbl) v(xdut.vramp) v(xdut.xc0.top) v(xdut.xc0.bot) v(xdut.xc0.dout) v(q0) v(s0_0) v(s1_0) v(s2_0) v(xdut.xc1.top) v(xdut.xc1.bot) v(xdut.xc1.dout) v(q1) v(s0_1) v(s1_1) v(s2_1) v(xdut.xc2.top) v(xdut.xc2.bot) v(xdut.xc2.dout) v(q2) v(s0_2) v(s1_2) v(s2_2) v(xdut.xc3.top) v(xdut.xc3.bot) v(xdut.xc3.dout) v(q3) v(s0_3) v(s1_3) v(s2_3) i(vavdd) i(vdvdd) i(v.xdut.vmbg) i(v.xdut.vmref) i(v.xdut.vmramp) i(v.xdut.vmc0) i(v.xdut.vmc1) i(v.xdut.vmc2) i(v.xdut.vmc3) @m.xdut.xbg.xoc0.m0[id] @m.xdut.xbg.xoc1.m0[id] @m.xdut.xbg.xoc2.m0[id] @m.xdut.xbg.xoc3.m0[id] @m.xdut.xbg.xor.m0[id] @m.xdut.xbg.xov.m0[id] @m.xdut.xbg.xob.m0[id] @m.xdut.xbg.xmn1.m0[id]
quit
.endc
