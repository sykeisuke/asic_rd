# ic_source -- design recipe

From `SPEC.md` to the devices of `ic_source.spice`. Labels as in the spec.
`size_ic.py` carries the chain in code and WRITES the netlist and
`data/sizing.json`; the `size` phase of `make ic-source` re-derives both and
fails if they differ. Tables: the block's own gm/Id tables (`lut/`, L 0.28 /
0.5 / 1 um, finger W 1 / 2 / 4 um, VSB 0 / 0.2 V) and the PDK resistor
characterisation (`data/res_char.csv`).

## 1. The current [D]

C_UNIT by an AC probe of the model card at V_REF / 2: 54.52 fF typical,
59.97 / 49.07 fF at the MIM ss / ff corners [P]. I = C_UNIT x V_REF x F_CLK
= 0.5452 uA; at the MIM corners 0.600 / 0.491 uA, which is what the ramp's
array needs there.

## 2. The divider and the cascode biases [D]

33 strips of `ppolyf_u_3k` 1 x 20 um (63.3 kohm each at 27 C [P]), 1.58 uA,
tap 5 = V_REF = 0.500 V with 8 units of MIM (kT/C 64 uV, tau 0.1 us) [A].
The cascode biases are NOT divider taps (a ratio of AVDD cannot follow the
thresholds over the corners: the first draft's taps put the pass device and
the OTA's fold sinks into triode at ss / 0 C / 3.0 V). V_CASP = AVDD -
|Vgs(XPD1: 4 x 2 um, L 0.5 um, weak inversion at 0.325 uA)| - |Vgs(XPD2:
the cascode's geometry)| = 1.78 V typical, so the pass device's V_SD under
its cascode is |Vgs_D1| - I R_s + (|Vgs_D2| - |Vgs_c|) = 0.49 V and the
output cascode stays saturated up to 2.47 V (ramp top 2.053). V_CASN =
Vgs(XND1: the NMOS cascode's geometry) + Vgs(XND2: 4 um wide) = 1.35 V, the
fold node 0.64 V above avss (sinks' margin 0.55 V). Each stack takes one
finger of the bias ladder (0.325 uA).

## 3. The pass mirror [D]

PMOS, L 1 um (the recorded exception: matching), 2 um fingers. The finger
count and the degeneration come from the mismatch rule
sigma(dI/I) = sigma(dVt) / (I/gm + I R_s) <= 0.4 % (R13's mirror share) with
I R_s <= 0.26 V, the pass device's headroom under its cascode at
ss / 85 C / 3.0 V (measured -3 mV at 0.31 V): 16 fingers, 8 strips in SERIES
(0.28 V;  would parallel them: the first draft lost its degeneration
that way and showed a 1.1 MHz loop with 34 deg of margin), sigma 0.38 %.
The strips are one arrayed instance per resistor (`XRS1[7:0]`, xschem's
vector instance; the divider likewise `XRU[27:0]` over vref and `XRL[4:0]`
under it), so each chain is one symbol on the sheet.
Cascodes L 0.5 um, 4 x 2 um (a low |Vgs_c| for the pass device's headroom).

## 4. The OTA [D]

Folded cascode, no chopper (user, 2026-10-29: keep the design simple). A
loop offset V_os is a current error V_os / V_REF, so R13's loop share
(0.4 %) is sigma(V_os) <= 2.0 mV, input-referred

    sigma(V_os)^2 = sigma_pair^2 + (gm_n / gm_in sigma_sink)^2 + (gm_l / gm_in sigma_load)^2

- tail: one finger of the bias ladder (0.325 uA, the pair 0.1625 uA each);
- fold sinks: copies of an NMOS diode fed by one bias finger, sink : diode
  = 2 : 3 fingers, so each sink carries 0.217 uA and the fold 0.054 uA
  (gm_n / gm_in 1.47; with the sinks at a whole bias finger the ratio is 2
  and the sinks dominate: the 25 mV of the one-finger draft);
- pair and sinks: L 1 um, 2 um fingers, the smallest common finger count
  meeting 2.0 mV: 28 (pair 1.0 mV, sinks 1.4 mV after the gm ratio);
  the diode 42 fingers;
- PMOS mirror load: L 1 um, 4 x 2 um (gm_l / gm_in 0.32), cascodes 0.5 um.

Predicted 1.93 mV (0.39 %), with the mirror 0.54 % total sigma. The fold's
small current is what this costs: poles near 2 MHz (s.5) and a slow start
(s.6).

## 5. The compensation [D]

p_A = F_CLK C_UNIT / (C_F + C_UNIT + C_par) with C_F = 4 units and 5 fF of
parasitics: 625 kHz. omega_u <= p_A / 4.4 and omega_u = gm_in / C_g with
gm_in from the table (3.8 uS, the pair in weak inversion): C_g = 79 units
(4.31 pF). The ratio is large because the fold and the load mirror run at
0.054 uA: p_A / 2.5 gave 57 deg typical / 51 deg at ff / 85 C / 3.6 V,
p_A / 4 gave 65 / 59.8 deg. C_F sets R9: C_UNIT / (C_F + C_UNIT) = 0.2 % per
% of duty by hand, 0.155 measured (the pair's gate adds to C_F).

## 6. Start-up and switches [A]

Two stacked minimum PMOS diodes (0.22 / 0.36 um) from AVDD to vg; the OTA
slews the rest at I_sink / C_g ~ 0.05 V/us: 22 us typical, up to ~26 us
over PVT (R7, 60 us). Switches
NMOS 0.3 / 0.28 um (R_on x C_UNIT ~ 0.5 ns against the 25 ns phase; their
junctions on the switched node add to C_UNIT: 0.5 um wide switches gave
+1.5 % of current, 0.3 um +0.7 %, a constant). The
phases from the frozen library's `inv_2` and two cross-coupled `nor2_2`
with two-inverter delays on each feedback: phi1 = clk & !phi2,
phi2 = !clk & !phi1.

## 7. Layout intent (the sheet's `layout:` line)

The switched unit MIM beside the ramp's 83-unit array (same unit, same
orientation, same surroundings, a dummy ring shared with the array); XM1 and
XMO interdigitated with their strips as two identical units; XIA / XIR and
XN1 / XN2 each one interdigitated common-centroid row with end dummies; the
divider as
one row of 33 identical strips with dummies at both ends; the phase
generator and its DVDD routing away from node a.
