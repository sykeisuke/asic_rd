# ic_source -- specification of the I/C current source for the ramp

Date: 2026-10-28. Derived from the ramp's hand-over (`../ramp_simple/SPEC.md`
s.6) and the ADC grid; no number is fitted to an existing design. Labels:
**[U]** user decision, **[C]** contract (the specification, the accepted ADRs,
the ramp's hand-over), **[P]** PDK data, **[M]** measured (a run named),
**[A]** assumed, **[D]** derived.

## 1. What the source has to do

The ramp (`../ramp_simple`) is N = 83 unit MIMs (the cells' 5 um square,
54.52 fF each) charged by a constant current; its slope must be one LSB per
count, 117.19 mV/us, and must stay there over process and temperature with
no trim word [U, 2026-10-28]. A current that tracks a MIM can only be made
from a MIM [D]: one unit MIM C_UNIT charged to V_REF and discharged every
clock period draws, on average,

    I = C_UNIT x V_REF x F_CLK = 54.52 fF x 0.500 V x 20 MHz = 0.5452 uA

so the slope is I / (N C_UNIT) = V_REF x F_CLK / N: a unit-count ratio, the
one 20 MHz clock [C] and a supply ratio. V_REF = 5/33 AVDD, the tap ratio
VR_LO uses [C], so the slope is ratiometric to AVDD like the rest of the ADC.
The beta-multiplier bias (0.74-1.62x over PVT, 0.44 %/% of AVDD, ADR 0017)
is not used for the ramp [U]; it only biases this block's amplifier.

## 2. Interface (frozen by this specification)

Subcircuit `ic_source iout ibias clk avdd avss dvdd dvss`.

| Port | What it is |
| --- | --- |
| `iout` | the current, into the ramp node (`vramp`, 0.4355..2.053 V over a conversion [C]) |
| `ibias` | bias_gen's ramp sink, 3.25 uA, into this block's 10-finger diode (the geometry the old ramp's `XRD` had, so bias_gen's load is unchanged) [C] |
| `clk` | the 20 MHz count clock `cnt_clk`, on DVDD [C] |
| `avdd avss` | the analog supply: the divider, the amplifier, the pass mirror, the switched capacitor |
| `dvdd dvss` | the digital supply: the non-overlap phase generator (standard cells), as the cells' latches [C, ADR 0019] |

## 3. Requirements

| R | Requirement | Value | Label |
| --- | --- | --- | --- |
| R1 | Current | I = C_UNIT x V_REF x F_CLK within **1.5 %** at typical (the switches' charge and the loop's static error are a constant, calibrated by the transfer measurement); the regulated node within 2 mV of V_REF | [A] |
| R2 | Tracking | the current follows C_UNIT at the MIM corners (ss / ff, +-10 %) within **1.0 %** of the ratio; over 45 PVT cells (5 corners x 0/27/85 C x 3.0/3.3/3.6 V, the resistor corner tied to the process corner) the deviation from the ratiometric ideal stays within **1.0 %** of its mean | [A] |
| R3 | Output resistance | >= **2.0 Gohm** at the ramp node over 0.4355..2.053 V (a 0.05 LSB bow, ramp R6); the cascode keeps the pass device's V_SD fixed while the ramp moves | [C] |
| R4 | Ripple | the 20 MHz current ripple integrated on the ramp's 4.6 pF: <= **0.05 LSB** at the ramp node | [C] |
| R5 | Noise | the output current's noise from 1 Hz through the ramp's 13.8 us integration kernel: <= **0.11 LSB** rms at code 255 (ADR 0013's "ramp bias" share; the "ramp core" 0.07 is free) | [C] |
| R6 | Loop | phase margin >= **60 deg** at typical and at the PVT extremes, the ramp node at its reset and top levels | [A] |
| R7 | Start-up | the current within 1 % of its final value <= **60 us** after a cold supply, every PVT cell and every mismatch draw (silicon is powered for milliseconds before a record, so only the benches wait; was 10 us with the chopper, 30 us for the chopper-free design until its first Monte Carlo showed a tail to 49 us, set to 60 us by the user 2026-10-29, s.4) | [U] |
| R8 | Headroom | every loop and pass device saturated (V_DS - Vdsat >= 0) at every PVT cell with the ramp at 1.2 V; reported at the reset and top levels | [A] |
| R9 | Clock duty | current change <= **0.2 % per %** of duty between 45 and 55 % (the sampled charge is C_UNIT x V_A at the end of phi1; with phi1 ending at the midpoint of the ripple the first-order term vanishes at 50 % duty; the residual is the ripple C_UNIT / (C_F + C_UNIT)) | [A] [D] |
| R10 | Supply | ratiometric: the current error changes <= **0.5 %** between AVDD 3.0 and 3.6 V | [A] |
| R11 | References | the switched capacitor and the phase generator touch no shared reference: own divider (V_REF) and own Vgs-referenced cascode biases, the switching node is the block's own | [C] ramp R8 |
| R12 | Power | <= **80 uW** AVDD + DVDD, the bias diode and the 20 MHz phase generator included | [A] |
| R13 | Mismatch | 3 sigma of the current over mismatch draws <= **2.0 %**; and the slow sum (3 sigma + the PVT cells below the mean + a 2 % clock-duty error x R9) inside the ramp's **2.0 %** slow allocation (ramp_simple R3, ADR 0025: the design slope's rounding then leaves the cell its own margin; was 2.9 %). No chopper (user, 2026-10-29: keep the design simple): the budget is split 0.4 % sigma to the loop offset (2.0 mV at V_REF) and 0.4 % to the pass mirror, and both are met by device area | [A] [D] |
| R14 | Length | every L <= 1 um; L above 0.36 um only with a reason: the pass mirror, the OTA pair, its fold sinks and loads at 1 um (matching, R13), the cascodes at 0.5 um (headroom) | rule |

## 4. Derivations behind the table

**R1, the loop.** A folded-cascode OTA (PMOS input, PMOS cascode-mirror
load) compares node a with V_REF and drives the gate of the pass device XM1
whose drain feeds node a; the switched capacitor removes C_UNIT x V_A per
period. The OTA's natural output sits one |Vgs| below AVDD, where the pass
gate needs to be, so the loop's static error is the OTA's offset over its
gain (measured 0.2 mV at 50 dB of loop gain). XMO, identical to XM1 on an
identical degeneration, delivers the same current.

**R3, the pass mirror.** Degeneration (8 strips, 0.28 V) and a cascode give
r_out = r_o (1 + gm R_s) x gm_c r_oc: 67-81 Gohm measured at typical against
the 2 Gohm the ramp needs; the degeneration also bounds the start-up current
and sets R13's mirror share (sigma(dI/I) = sigma(dVt) / (I/gm + I R_s) <=
0.4 %: 16 fingers, 0.38 % by Pelgrom).
The cascode gate V_CASP comes from a Vgs-referenced stack (AVDD minus a wide
weak-inversion PMOS diode minus a diode of the cascode's geometry), so the
pass device keeps V_SD = |Vgs_D1| - I R_s ~ 0.4-0.5 V at every corner; a
divider tap cannot follow Vt (tap 18 put the pass device 0.6 V into triode
at ss / 0 C / 3.0 V and tap 11 put the OTA's fold sinks into triode there).
V_CASN likewise: Vgs of the cascode's geometry plus a wide NMOS diode, so
the fold node sits one weak Vgs above avss.

**R6/R9, the compensation.** The node-a pole p_A = F_CLK C_UNIT /
(C_F + C_UNIT + C_par) and the gate node's capacitor C_g set the loop's
unity frequency omega_u = gm_in gm1' / (g_A C_g) ~ gm_in / C_g; C_F = 4
units (625 kHz with the parasitics) and omega_u <= p_A / 4.4 (C_g = 79
units). The large ratio is the price of the matched OTA: its fold carries
only 0.054 uA, so the fold and mirror nodes add poles near 2 MHz (p_A / 2.5
measured 51 deg at ff / 85 C / 3.6 V, p_A / 4 59.8 deg). C_F = 4 keeps R9
at C_UNIT / (C_F + C_UNIT) = 0.2 % per % by hand, 0.155 measured (the pair's
gate adds to C_F). The ripple at node a is symmetric about the regulated
value, so the pair's odd nonlinearity does not rectify it [D].

**R7, start-up.** Two stacked minimum PMOS diodes pre-charge the gate node
to AVDD - 2|Vt|; the OTA slews the rest at I_sink / C_g. Slew is
I_sink / C_g = (I_sink / I_pair) n U_T omega_u: a weak-inversion pair (for
matching) and a small fold (for the sinks' offset share) make it ~0.05 V/us,
so the start takes ~20-26 us, and up to ~50 us in the mismatch tail (a
draw whose offset leaves less slew current). Only the benches see it (silicon is powered
for milliseconds before a record); a start-up boost would cost devices, the
chopper (10 us) cost twelve switches, a flop and six cells.

**R13, the offset by area (no chopper).** A loop offset V_os is a current
error V_os / V_REF. With one-finger devices the Monte Carlo showed sigma
25 mV = 4.9 % of I, almost all in the loop: the fold sinks (each carrying
the pair half plus the fold current, so gm_n / gm_in = 2) and the pair.
Input-referred, sigma(V_os)^2 = sigma_pair^2 + (gm_n / gm_in sigma_sink)^2 +
(gm_l / gm_in sigma_load)^2. The sizer makes the sink current 2/3 of a bias
finger (the fold 1/6, so gm_n / gm_in = 1.47 and gm_l / gm_in = 0.32) and
gives the pair and the sinks the smallest common finger count (2 um fingers,
L 1 um) that meets 2.0 mV: 28 fingers each, 1.93 mV by Pelgrom. Measured
(100 draws, the first record of this design): loop share 0.50 %, mirror
0.29 %, switched capacitor 0.09 %, total 3 sigma 1.60 %. The weak-inversion
pair also cuts the source's 1/f noise: R5 0.019 LSB (0.10 with the
one-finger pair).

## 5. Decisions for the user

1. The macro's bench waits T0 = 3 us for the references; this source needs
   ~22 us at typical, up to ~29 us over PVT and ~50 us in the mismatch
   tail (R7): when the source is integrated, either raise T0 to 60 us in
   `Analog_top/tb_params.inc` or
   start the bench with the gate node pre-set (`.ic` on vg). Silicon is
   powered for milliseconds before a record.
2. The clock duty cycle of the FPGA-driven 20 MHz clock is assumed
   50 +-2 % [A]; R9 makes a 2 % duty error a 0.3 % slope error, calibrated
   with the rest.
3. The phase generator uses the library's smallest cells (`inv_2`,
   `nor2_2`, there is no `_1`): 26 uW on DVDD at 20 MHz, more than the
   analog part. A transistor-level generator would halve it; not done.

## 6. Not covered

Layout and extraction; the VACASK transient noise of the source (the cell
bench's `ramp` group after integration); integration into `ramp_simple`'s
four-cell bench and into the macro (next).
