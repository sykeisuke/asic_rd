# ramp_gen -- design recipe

From the ADC's top-level numbers to every W and L of `ramp_gen.spice`.
Labels: **[D]** derived from contract numbers by the chain written before it,
**[P]** PDK data (gm/Id tables, model cards, simulation of a single device),
**[A]** assumed: a judgement or an allocation, to be confirmed or replaced.
The sizer `size_ramp.py` carries the same chain in code and writes
`data/ramp_gen_params.spice`; the measured results are in `RESULTS.md`.

## 1. What the ramp has to do

Contract (`../ramp_gen/ref/unit_cell_bps/CONTRACT.md`): 8 bits over VR_LO = 0.5 V to
VR_HI = 2.0 V, LSB = 5.859 mV, TCOUNT = 50 ns, SLOPE = LSB / TCOUNT =
**117.19 mV/us**, 20-count overrun to VR_OVR = 2.117 V; S1 connects every
cell's bottom plate to the ramp at TCONN = TR - 90 ns with the ramp held at
VR_LO; the count starts at TR. Error budget at the ADC input: noise
<= 0.25 LSB rms, err spread and INL <= 0.25 LSB, gain 1 +- 0.5/256 (ideal ramp).

What the ramp sees, per cell [D]: the bottom plate (C_S = 54.52 fF in series
with the top plate's ~8 fF, plus S0/S1 junctions and the MIM bottom-plate
parasitic) is about **10 fF** [A, rounded up from 7 fF series + junctions].
Two disturbances come from every cell:

- **the S1-connection kick**: at TCONN the bottom plate moves from vin to
  VR_LO, so 10 fF x (vin - 0.5 V) = up to **15 fC per full-scale cell** lands on
  the ramp node, 90 ns before the count starts;
- **the trip kick**: when a comparator decides, its gain node slews ~2.7 V and
  XINN's C_GD (0.42 fF, `cmp_bps.spice`) pushes ~1.1 fC into the top plate,
  most of which (C_S / (C_S + C_top) = 0.87) reaches the bottom plate, i.e.
  the ramp.

| # | Requirement | Value | Label |
| --- | --- | --- | --- |
| R1 | Range | VR_LO -> VR_OVR = 0.5 -> 2.117 V, held at VR_LO from track until TR | contract |
| R2 | Slope | 117.19 mV/us at typical, a trim / calibration knob for process | contract / [A] |
| R3 | Linearity | ramp INL <= 0.05 LSB (a fifth of the 0.25 LSB linearity budget, the rest is the cell's) | [A] |
| R4 | Load independence | slope and INL the same for 4 and for 64+ cells (the array will grow) | [D] from the user's scaling requirement |
| R5 | Start | the start transient over by code 4 (inside the dead zone of SPEC_BPS item 13) | [D] |
| R6 | S1 kick | the kick of 4 full-scale cells (60 fC) <= 5 LSB at the reset level, and its residue not seen above the dead zone | [D] / [A] |
| R7 | Crosstalk | one cell's trip or S1 charge moves another cell's code by <= 0.1 LSB (SPEC_BPS item 20 applied to the ramp) | [A] |
| R8 | Noise | the ramp's own noise <= 0.10 LSB rms at code 255 from F_LO = 1 Hz; with the shared bias <= 0.15; channel total (with kT/C 0.051, comparator 0.024) <= 0.25 | [A] allocation of the contract budget |
| R9 | Recovery | back at VR_LO within 1 us of the end-of-ramp reset (dead time between conversions) | [A] |
| R10 | Supply | slope change <= 0.2 %/% of VDD | [A] |
| R11 | Bias | every current a mirror of the shared pbias line (bias_gen's 3.1314 uA leg) | contract |
| R12 | Power | <= 100 uW for the shared generator | [A] |

## 2. Topology: why a Miller integrator

Three numbers decide it [D]:

1. **Kicks on an integrating capacitor are permanent.** A current source
   charging a grounded C_R (the classic Wilkinson ramp) integrates every kick:
   a trip kick of 1.1 fC x 0.87 on C_R = 3 pF shifts the ramp by 0.32 mV =
   0.055 LSB for every cell that converts later. Four cells: up to 0.17 LSB
   on the last one. 128 cells: tens of LSB. With a driven output the same
   charge is absorbed and the trajectory recovers.
2. **The load adds to C_R.** 128 cells x 10 fF = 1.3 pF, comparable to C_R,
   and the comparators' input capacitance changes state at the trip, so the
   slope would depend on how many cells have already tripped (a pattern-
   dependent gain).
3. **The current source sees the swing.** A grounded C_R puts the 1.6 V ramp
   across the source; linearity then rests on its output impedance and on
   the voltage dependence of every junction on the node (the reset switch
   was the measured INL limit in `simulations/gf180_ramp_topology`).

The integrator removes all three: the slope current is drawn out of a
virtual ground vx that never moves (so neither the sink's output
impedance nor any junction on vx enters), the cells hang on the driven
output, and the slope is I_INT / C_INT whatever the load. Its costs, all
sized below: an OTA (power, noise, its own flicker), a velocity error
(the OTA input must carry Cc x SLOPE, a constant offset while ramping),
and a slew limit on the end-of-ramp collapse.

## 3. Sizing chain

Every number below is printed by `size_ramp.py` (`data/sizing.json`) and
re-derived by the flow's `size` phase, which fails if it does not reproduce
`data/ramp_gen_params.spice`.

### 3.1 Integrating capacitor and slope current

- **C_INT = 4.0 pF** [A, the top of the 2-4 pF window]. Every noise term of
  the slope current scales as 1/sqrt(I_INT) at fixed inversion level (thermal:
  S_I / I^2 = 4kT gamma (gm/Id) / I; flicker: the area grows with I at fixed
  L and gm/Id), and I_INT = C_INT x SLOPE, so the largest capacitor is the
  quietest. MIM 2f0, 44.6 um square; the model gives 4.0011 pF [P] (an AC
  probe in the sizer; the area formula agrees to 30 ppm).
- **I_INT = 0.4689 uA** [D]. Solved by bisection on the slave width in an
  operating point at the **virtual ground the ramp actually holds**: while
  ramping, the OTA input carries the velocity error Cc x SLOPE / gm1 =
  4.59 mV, so vx sits that much below its reset value, and the sink's V_DS
  with it. Sized at the reset vx, the slope came out 0.09-0.11 % slow (the
  sink is ~0.24 V above Vdsat, where 5 mV is 0.1 % of current).

### 3.2 The current chain (sets the slope and its noise)

| Device | Role | Choice | Why |
| --- | --- | --- | --- |
| XNS | sink on vx | NMOS L = 20 um, W 1.51 um, gm/Id 5.75, Vdsat 0.256 V | lowest gm/Id that keeps > 0.2 V of saturation margin at V_DS = 0.5 V [P]; L = 20 um for area (flicker) [D] |
| XND | its diode | KD = 4 x XNS (W 6.04 um) | the diode's thermal and flicker enter at 1/KD of its own [D] |
| XPS | pbias slave | PMOS L = 4 um, W 50.1 um, 2.0 uA | 16x the area of an L = 1 um slave at the same current: its flicker enters 1:1 in relative terms [D] |

The bias generator behind pbias is not the ramp's to size. Its relative
current noise enters 1:1: 0.080 LSB at code 255 from 1 Hz, the largest single
term (XMP2's flicker alone is 0.053; RESULTS s.3). It must be a **dedicated
bias_gen instance** (RESULTS s.4): on the comparators' shared line a decision
glitch (~0.5 mV) reaches the slope current and the integrator keeps it.

### 3.3 The OTA

| Quantity | Value | Chain |
| --- | --- | --- |
| crossover F_U | 4.06 MHz (3.5 MHz measured) | [D] the velocity error S/(2 pi F_U) = 4.6 mV = 0.8 LSB settles in ~2 counts, and the S1 kick decays by e^-2 before the count starts |
| Cc | 0.50 pF MIM, 15.6 um | [A] |
| gm1 | 12.7 uS = 2 pi F_U Cc | [D] |
| input pair XM1/XM2 | PMOS L = 4 um, W 11.3 um, gm/Id 10, 1.27 uA each | [D] input CM 0.5 V needs PMOS; gm/Id 10 sets the slew I_TAIL/Cc = 5 V/us (R9); L = 8 um cut 4 % of the noise and cost 13 deg of reset-mode phase margin (explore/area.sh) |
| mirror XM3/XM4 | NMOS L = 12 um, W 1.66 um, gm/Id 5 | [D] its flicker was the largest OTA term at L = 8 um; 12 um takes the OTA from 0.086 to 0.071 LSB for 6 deg of phase margin, 16 um buys 0.006 more for 5 deg more (explore/area2.sh) |
| stage 2 XM5 | NMOS L = 1 um, W 9.3 um, gm/Id 12, 13.5 uA | [D] p2 = gm5 / C_L >= 3.0 F_U at C_L = 2.04 pF |
| load XM6 | pbias slave, W 86.4 um (one instance below the 100 um bin limit) | [D] carries I5 plus the output current I_INT + C_L x SLOPE |
| Rz | ppolyf_u 1 x 29.7 um, 10.4 kohm = 1.6 / gm5 | [D] zero in the left half plane; 1.2 / gm5 and p2 = 2.2 F_U gave 60 deg but a 23 % undershoot after the S1 kick (explore/damp.sh) |
| C_OUT | 2.0 pF MIM, 31.5 um | [D] R6: 60 fC of S1 charge (4 full-scale cells) <= 5 LSB. The varactor cap_nmos_03v3_b, twice as dense, stalls the transient at the sample edge in its behavioural model |
| XRST | NMOS 0.5 / 0.28 um | [D] small: its channel charge (~1.4 fC) is a 0.2 mV pedestal on 4 pF; its junctions sit on driven or fixed nodes, so they add no INL (the limit of the grounded-capacitor ramp) |

Supply current 18.5 uA predicted, 60 uW measured during the ramp, plus
~20 uW for the dedicated bias generator.

### 3.4 What was tried and rejected (explore/)

| Option | Result | Verdict |
| --- | --- | --- |
| p2 = 2.2 F_U, Rz = 1.2 / gm2 | PM 60 deg, S1-kick undershoot 23 % | replaced by 3.0 / 1.6: PM 65 deg (66 at L3 = 8 um) |
| pair L = 8 / 12 um | -4 % / -21 % OTA noise, reset PM 52 / 14 deg | rejected |
| mirror L = 16 / 24 um | OTA 0.065 / 0.067 LSB, PM 54 / 52 deg | L = 12 um kept |
| C_OUT 4 / 6 pF, F_U 6 MHz | crosstalk unchanged at 1 LSB (+0.16), +26 to +64 uW | the crosstalk was not the kick charge: it was the shared pbias |
| ramp on its own bias_gen | crosstalk share 0.000 / -0.004 LSB (1 / 4 LSB) | **adopted**, with C_OUT 2 pF |
