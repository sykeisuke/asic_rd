* tb_params.inc -- levels and the periodic, clock-synchronous timeline of the
* cell_trannoise bench. One file, read by ct_bench.py (the VACASK and the
* ngspice bench), ct_extract.py and ct_reduce.py (record times, the clock edges).
* Overrides on the command line: POS, NREC, TFIRST, NCNT.
*
* One cell of Analog_top (atop_cell: S0/S1/S2 + their control inverters,
* 54.52 fF MIM, comparator_d, latch = gf180mcu_as_sc_mcu7t3v3__dfxtn_2) on
* ramp_simple_d, read by path from ../Analog_top/analog_top.spice. Ideal:
* AVDD, DVDD, VREF (= the comparator's VBL input, one node as in v5), VR_LO,
* VIN, the two bias currents, the switch controls and the count clock.
*
* Every control is periodic with PCONV, a WHOLE number of counts, so every
* record sees the count clock at the same phase (the macro's: one 20 MHz
* clock, TR on a rising edge). Per record, from its start t0 = TFIRST + n PCONV
* (t0 is a rising clock edge):
*   t0              S2 opens: the sample (bot = the comparator's plate frozen at VREF)
*   t0 + TNOV       S0 opens (top isolated from VIN)
*   t0 + 2 TNOV     S1 closes: top = vramp = VR_LO
*   TR = t0 + TRREL ramp_rst falls: ramp and count start, on a rising clock edge
*                   (TRREL = 300 ns: the macro's TS3 -> TR, vrlo_ref's R6, ADR 0018)
*   TE = TR + NCNT TCOUNT   S1 opens (end of this record's conversion window)
*   TE + 5 ns       ramp_rst rises (vramp back to VR_LO)
*   TE + 10 ns      S0 and S2 close: track for TTRACK
* The latch samples dout on the FALLING clock edges, TR + TCOUNT/2 + k TCOUNT;
* q falls on the first one after the decision: code = k (Analog_top's
* code = floor((t_qfall - TR) / TCOUNT)).
*
* POS is the held level in LSB above VR_LO. The `align` step of ct.sh moves it
* from the nominal mid-code (16.5, 240.5) so that the NOISELESS decision (dout's
* VDD/2 fall) lands on a falling clock edge: then noise alone decides whether
* q falls on that edge (Clk, code k) or on the next (Clk+1, code k+1).

.param VDD=3.3
.param VMID='VDD/2'
.param NBITS=8
.param NCODE='2**NBITS'
.param TCOUNT=50n
.param VR_LO=0.5
.param VR_HI=2.0
.param LSB='(VR_HI-VR_LO)/NCODE'
.param SLOPE='LSB/TCOUNT'

* ideal bias currents (design values of the blocks; the same as ../cell_trannoise_bkp/cell_trannoise)
*   IREF_CMP   comparator/data/sizing.json iref, into comparator_d's XREFP
*   IREF_RAMP  bias_gen/bg.py I_RAMP_NOM, into ramp_simple_d's L 1 um diode XRD
.param IREF_CMP=1.93077u
.param IREF_RAMP=3.1314u

* the held level, in LSB above VR_LO (ct.sh align overrides it)
.param POS=16.5
.param VIN='VR_LO+POS*LSB'

* the record
.param TEDGE=100p
.param TNOV=5n
.param TRREL=300n
.param NCNT='floor(POS)+8'
.param TTRACK=470n
.param PCONV='ceil((TRREL+NCNT*TCOUNT+10n+TTRACK)/TCOUNT)*TCOUNT'
.param NREC=3
.param TFIRST=1u
.param TSTOP='TFIRST+(NREC-1)*PCONV+TRREL+NCNT*TCOUNT+80n'
* the count clock runs from TCLK0 (a whole number of counts before TFIRST; the
* noisy benches hold it low through the flicker warm-up and start it 1 us early)
.param TCLK0='TFIRST-ceil(min(TFIRST,1u)/TCOUNT)*TCOUNT'

* the latch's capture load on q (digital capture pins + wire, as Analog_top CQ)
.param CQ=40f
