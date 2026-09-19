# Bottom-plate cell results

Date: 2026-09-18. Typical corner, 27 C, 3.3 V. CHOLD = 54.5 fF (ideal linear
capacitor standing in for the MIM), 3 fF lumped parasitic on each plate,
minimum-width transmission gates (W = 1 um top/bottom switches, W = 2 um
ramp-connect), ideal ramp 117.19 mV/us (1.5 V / 256 counts at 20 MHz).
Input-referred pedestal = stored error after removing the fitted gain.

| Variant | Gain error | Linearity (LSB) | Pedestal mean | Pedestal spread 0.5-2.0 V | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| A: ramp on bottom, sense top, bottom-first | +9.0 % | 1.12 | +27 mV | 10.6 mV (1.8 LSB) | FAIL |
| B: ramp on bottom, sense top, top-first | +10.4 % | 2.61 | +20 mV | 23.3 mV (4.0 LSB) | FAIL |
| **C: ramp on top, sense frozen bottom plate, bottom-first** | **-0.02 %** | **0.008** | **-7.8 mV** | **0.09 mV (0.015 LSB)** | **PASS** |

(Variant A/B rows exclude the 2.0 V point, where the stored level already
exceeds the 2.0 V comparator reference and no crossing exists; that is a
reference-choice artifact of the top-sensed arrangement, not a device effect.)

## Interpretation

1. **Bottom-plate sampling only removes the signal-dependent charge injection
   if the comparator senses the plate whose switch opened first.** In
   variants A/B the top switch (VIN side) opens onto a floating node and its
   injection, which depends on VIN through the switch overdrive, stays on the
   sensed node: 10-23 mV of signal-dependent pedestal, i.e. 2-4 LSB of
   non-linearity at 8 bit. In variant C the bottom switch sits at a constant
   2.0 V, so its injection is a constant -7.8 mV pedestal (0.09 mV spread);
   the top switch's injection is later absorbed by the ramp driver and never
   reaches the sensed node.
2. **Variant C also cancels the parasitic gain error.** With the ramp and the
   input entering through the same capacitor divider C/(C+Cp), the crossing
   condition reduces to v_ramp = VIN independent of Cp: gain error -0.02 %
   versus +9-10 % when the ramp and the comparator share the top node. This
   removes the per-cell gain calibration that the 54.5 fF cell would otherwise
   need (Cp is the comparator input and varies cell to cell).
3. **Comparator requirement:** in variant C the sensed node swings from
   ~0.15 V (VIN = 2.0 V) up to the 2.0 V trip point during conversion, so the
   input pair must stay functional over that range but its offset only
   matters at 2.0 V (fixed common mode at the trip). An NMOS-input pair is
   natural for a 2.0 V trip point; the PMOS choice made for a moving trip
   point should be re-derived.
4. **Ramp generator load:** the ramp drives the top nodes of all cells through
   the connect switches: about 4 x (54.5 fF + parasitics) in Tape-out 1.
5. **Consequence for the architecture text:** "ramp on the bottom plate" in
   the 2026-09-18 meeting should be read as "ramp on the plate opposite to
   the one that is frozen first and sensed". Which physical MIM plate (M4 or
   M5/FuseTop) plays which role is a layout choice; electrically the sensed
   plate must be the one with the constant-potential switch.

## Not covered here

kT/C and comparator noise (transient-noise simulation of the chosen
comparator is the next step, per the 2026-09-18 review), MIM model instead of
the ideal capacitor, PVT and mismatch, the real ramp generator, and droop over
the conversion (leakage on a 54.5 fF node over 13 us should be checked with
the extracted junctions once the cell layout exists).
