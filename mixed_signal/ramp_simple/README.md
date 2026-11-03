# ramp_simple -- the shared ramp: 73 unit MIMs and a reset switch

Cell `ramp_simple` (ports `vramp rst vrlo vss`): the ramp capacitor of the
8-bit bottom-plate ADC as 73 unit MIMs (the cells' 5 um square, 54.52 fF
each, 3.98 pF) and a 0.5 um NMOS reset switch to VR_LO. The ramp current
enters at `vramp` from the I/C current source `../ic_source`
(I = C_UNIT x V_REF x F_CLK = 0.545 uA); in the ramp-alone benches it is
an IDEAL source (user decision 2026-10-28; the PMOS mirror at L 8 um, its
diode and the five-bit finger trim of the first version left the cell), and
the `src` phase runs the macro bench on the real `ic_source`.
The slope is then the unit ratio V_REF x F_CLK / 73 and tracks the MIM.

The grid is ADR 0025's (user, 2026-10-29): 8-bit codes with LSB =
(78.2 mV + 1.5 V + 99.9 mV) / (255 x 0.982) = 6.70 mV, so the valid codes
0..254 cover the pre-roll, the whole 0.5-2.0 V window (224 codes) and the
+3 sigma offset (comparator and vrlo_ref) even on a ramp 1.8 % slow; the
reset level is vrlo_ref's 7/55 tap, 0.420 V (11.7 LSB of pre-roll); the
ramp ends at the controller's overflow + 3 DRAIN counts (count 259); the
comparator-ramp crosstalk is accepted at 0.30 LSB. Earlier records: 83
units on the 5.86 mV grid `runs/ramp-simple/20261028T132201Z`; 74 units
with vrlo_ref still at 0.5 V `runs/ramp-simple/20261030T031227Z`.

Documents: `SPEC.md` (R1-R16, the hand-over to the I/C source in s.6, the
decisions in s.5), `DESIGN_RECIPE.md`, this record. Target
`make ramp-simple` (`./scripts/sim.sh ramp-simple`, phases `size schematic
ramp pvt adc4 src plot check`; a subset re-judges the rest from the
previous phase lines).

## 1. Record (`runs/ramp-simple/20261030T180323Z`, 44 PASS)

Phases `size schematic ramp pvt adc4` from `runs/ramp-simple/20261030T095845Z`
(38/38, on the re-tapped vrlo_ref); `src` from `20261030T173136Z`; the
record re-judged them with the `src` slope gate's direction corrected.
Typical process unless stated; MIM typical; the real `../vrlo_ref` (7/55
tap) as the reset level except where the ideal pre-roll level is named.

| R | Result | Gate | Verdict |
| --- | --- | --- | --- |
| size | 73 units (rounded DOWN), C_total 4.056 pF, I 0.5452 uA, XRST 0.5 um; design slope +0.28 % fast; sizer reproduces the netlist | | PASS |
| schematic | `ramp_simple.sch` netlists back (2 devices, ports in order); `tb_ramp.sch` holds the cell, the ideal current and the three sources | | PASS |
| R3 | the source at its slowest (2.0 % below the design current [A]) on the design slope: 0.9827 of the grid, 0.07 % above the 0.982 the LSB was derived for | >= 0 | PASS (thin) |
| R1 | slope vs the design slope: +0.019 % (both levels) | <= 0.5 % | PASS |
| R6 | ramp INL end-point, ideal current: 0.0005 LSB (both levels) | <= 0.2 | PASS |
| R2 / R8 | start transient settled at count 0 on both levels | <= 11 | PASS |
| R8a | drop at the release: 0.28 LSB (design current), 0.30 (1.1x); sized worst (ss/85/3.0, 1.1x) 0.44 | <= 0.5 | PASS |
| R8b | tau 20.0 ns at ss/85/3.0; S1 charge left at TR 0.09 mV | <= 30 ns; <= 0.34 mV | PASS |
| R11 | recovery into vrlo_ref 426 ns (level after 1.85 mV, vrlo peak +0.74 V at the dump) | <= 1 us | PASS |
| R4 | vramp at count 255: 2.135 V at the design current, 2.101 V at 0.98x | >= 2.100 V | PASS (thin at 0.98x) |
| R4 | end of the ramp (count 259) 2.156 V; sensed node VREF + 0.87 (top - 0.5 V) = 3.09 V | 3.0 V allocation, 3.3 V devices | reported |
| R9 | three injected 0.24 fC decision kicks: 0.009 LSB | <= 0.1 | PASS |
| R15 | PVT 45/45 cells (INL <= 0.0006 LSB, drop <= 0.40 LSB, start 0) | | PASS |
| R5 | slope with a FIXED current at the MIM corners: ss -8.7 %, ff +11.2 % (what the I/C source's C_UNIT tracks) | reported | |
| R7a | 16 cells -5.3 %, 64 cells -22.0 % of slope at a fixed current | reported | |
| adc4 | macro runs converted; transfer monotonic; gain error real vs ideal ramp -0.06 % | <= 1.8 % | PASS |
| R6 | ramp INL in the conversion incl. the comparator-ramp interaction: 0.125 LSB | <= 0.30 [U] | PASS |
| R9 | trip-kick crosstalk, 3 aggressors: 0.006 / 0.027 / 0.107 / 0.278 / **0.283** / 0.272 / 0.187 LSB at 0.25 / 1 / 4 / 16 / 24 / 32 / 64 LSB early | <= 0.30 [U] | PASS (6 % margin) |
| R8b / R9 | S1-connection crosstalk at code 20: 0.052 LSB | <= 0.1 | PASS |
| R2 / R3 | pre-roll level: 0.5 / 1.5 / 2.5 / 4.5 LSB above the reset read 1 / 2 / 3 / 5 (no dead zone); VIN = 0.503 / 1.0 / 1.5 / 1.995 V read 13 / 87 / 162 / 236 | <= 254 | PASS |
| codes | on a 0.5 V level, positions 16.5 / 80.5 / 160.5 / 240.5: 17 / 81 / 161 / 241 | reported | |

### On the real I/C source (`src`, 23 macro runs, T0 = 60 us)

| R | Result | Gate | Verdict |
| --- | --- | --- | --- |
| R3 | slope in the conversion against the ideal ramp: -0.88 % in codes per volt (the source is 0.9 % fast, as `ic_source` records +0.93 % at typical); slope vs the grid +0.96 % | not slower than 1.8 % | PASS |
| R6 | INL in the conversion incl. the source's 20 MHz ripple: 0.121 LSB; offset -0.17 LSB | <= 0.30 [U] | PASS |
| R9 | trip-kick crosstalk, 3 aggressors 24 LSB early: 0.280 LSB | <= 0.30 [U] | PASS |
| R2 / R3 | levels 0.5 / 1.5 / 2.5 / 4.5 LSB above the reset read 1 / 2 / 3 / 5; VIN = 0.503 / 1.0 / 1.5 / 1.995 V read 13 / 87 / 161 / 234; 32-level transfer monotonic | <= 254 | PASS |

The crosstalk is the comparator's: after a decision its gain node keeps
descending with the ramp and pulls charge out of `vramp` through its input
pair's C_GD for about a microsecond, and the capacitor stores it. It is
accepted at 0.30 LSB from ADR 0013's reserve (ADR 0025); typical only.

## 2. What the I/C source has to deliver (SPEC s.6)

| Item | Value |
| --- | --- |
| current | 0.5452 uA at typical; 0.600 / 0.491 uA at the MIM ss / ff corners |
| output resistance | >= 2.04 Gohm for a 0.05 LSB bow, >= 0.68 Gohm for 0.15 LSB |
| noise | <= 0.11 LSB rms at code 255 from 1 Hz through the 13.8 us kernel |
| slow margin | the source's slowest current (mismatch 3 sigma + PVT + clock duty) <= 2.0 % below the design current [A] (ADR 0025); the design slope's +0.28 % then leaves 0.07 % for the cell |
| reset kT/C | 0.005 LSB (the cell's own) |

`../ic_source` meets these (`runs/ic-source/20261030T173136Z`: slowest
1.956 %, r_out 124 Gohm, headroom at the ramp top >= 113 mV); the macro is
the next step (T0 about 60 us for its start-up).

## 3. Findings for other blocks

- The cells load the ramp by 19 fF each on average over a conversion (up to
  ~35 fF near a trip): a share of C that does not track the MIM.
- The comparator's post-decision charge pull (above): 0.283 LSB for three
  aggressors 24 LSB early on a 4.06 pF ramp.
- `vrlo_ref` absorbs the end-of-ramp dump with a 0.74 V peak and is back
  within 1.9 mV in 426 ns.
- The sensed node reaches 3.09 V at the end of the ramp, over R4's 3.0 V
  allocation (under the 3.3 V device rating); open.
- The PDK bins its MOS model by the device's total W; a matched ladder must
  be written `nf=1 m=N` (learned on the former finger trim).

## 4. Files

`ramp_simple.spice` (generated by `size_simple.py`), `data/sizing.json`,
`rs_common.py`, `tb_ramp.py` / `reduce_ramp.py` (the ramp alone),
`pvt_reduce.py`, `adc4.py` (the macro's four-cell bench with the ramp
substituted, `SRC=ic` for the real source), `plot_ramp.py`,
`check-ramp.awk`, `ramp_simple_sch.py` / `sch_lib.py` (drawings),
`phases.sh` / `run.sh` / `container.sh`; figures `assets/ramp_residual.png`,
`assets/pvt.png`, `assets/adc4.png`, `assets/ramp_simple_xschem.png`,
`assets/tb_ramp_xschem.png`.
