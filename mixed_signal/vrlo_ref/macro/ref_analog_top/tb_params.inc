* tb_params.inc -- the timeline and levels of the analog_top benches, shared by
* the functional bench (ngspice), the xschem testbench and the VACASK noise
* benches. One record, four cells, from a cold supply.
*
*   0        avdd, dvdd ramp 0 -> VDD in TPWR; every s0_k, s2_k high (track), s1_k low,
*            ramp_rst high (vramp held at vrlo); cnt_clk free-running from TCLK0
*   T0       bias_gen, the references and the ramp have settled
*   TS_k     S2_k opens FIRST: cell k's sample (TS_k = TS0 + k TSPACE, 40 ns = 25 MSa/s)
*   TS_k+TNOV    S0_k opens (isolate)
*   TS_k+2TNOV   S1_k closes: bot_k = vramp = vrlo
*   TS_k+TSTEP   vin steps to the next cell's level (after S0_k opened)
*   TR       ramp_rst falls: ramp and count start (a cnt_clk rising edge)
*   TE       the ideal ramp reaches VR_HI; TOVR = 20-count overrun
*
* q_k falls at the first cnt_clk FALLING edge after the comparator decides:
*   code_k = floor((t_qfall_k - TR) / TCOUNT)

.param VDD=3.3
.param VMID='VDD/2'
.param NBITS=8
.param NCODE='2**NBITS'
.param TCOUNT=50n
.param VR_LO=0.5
.param VR_HI=2.0
.param LSB='(VR_HI-VR_LO)/NCODE'
.param TRAMP='NCODE*TCOUNT'
.param SLOPE='(VR_HI-VR_LO)/TRAMP'
.param CS_C='1.99e-3*5u*5u+2.383e-10*2*(5u+5u)'

* levels: mid-codes 16/80/160/240 (LSB above VR_LO), one per cell
.param POS0=16.5
.param POS1=80.5
.param POS2=160.5
.param POS3=240.5
.param VIN0='VR_LO+POS0*LSB'
.param VIN1='VR_LO+POS1*LSB'
.param VIN2='VR_LO+POS2*LSB'
.param VIN3='VR_LO+POS3*LSB'

* supply ramp and settling before the cells' timeline
.param TPWR=100n
.param T0=3u
.param TEDGE=100p
.param TSPACE=40n
.param TNOV=5n
.param TSTEP=20n
.param TS0='T0+300n'
.param TS1='TS0+TSPACE'
.param TS2='TS0+2*TSPACE'
.param TS3='TS0+3*TSPACE'
.param TR='TS3+100n'
.param TE='TR+TRAMP'
.param TOVR='20*TCOUNT'
.param VR_OVR='VR_HI+SLOPE*TOVR'
.param TSTOP='TE+TOVR+100n'
* the count clock runs from power-up, phased so that a rising edge falls on TR
.param TCLK0='TR-floor((TR-TPWR)/TCOUNT)*TCOUNT'
* the latch's capture load on each q (digital capture pins + wire)
.param CQ=40f
