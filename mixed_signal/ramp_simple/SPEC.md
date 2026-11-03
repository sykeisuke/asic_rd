# ramp_simple -- specification of the shared ramp (capacitor + reset switch)

Date: 2026-10-28 (revised the same day: the ramp current is an ideal source
for now and the I/C current source `../ic_source` supplies it next; the
PMOS mirror at L 8 um, its diode and the finger trim left the cell, user
decision). The three decisions for the user are in section 5.

Labels: **[U]** user decision, **[C]** contract (the specification and the
accepted ADRs), **[P]** PDK data (model cards, the per-um characterisation
`runs/bottom-plate-spec-tech`), **[M]** measured (a run named), **[A]**
assumed (to be confirmed or replaced), **[D]** derived by the chain written
before it.

## 1. What the ramp has to do

The ADC (`docs/PROTOTYPE_SPECIFICATION.md` 0.7-draft, ADR 0005 / 0024) [C]:
8 bits over the 0.5-2.0 V input window, one 20 MHz clock, four cells
converting in parallel on one broadcast ramp applied to the bottom plates
through S1, each comparator tripping at the fixed VREF = VDD/2.

| Symbol | Value | Chain |
| --- | --- | --- |
| LSB | (64.5 mV + 1.5 V + 87.9 mV) / (255 x 0.982) = **6.599 mV** (227 codes over the window; was 1.5 V / 256) | [U, D] ADR 0025 |
| TCOUNT, F_CLK | 50 ns, 20 MHz | [C] one clock |
| SLOPE | LSB / TCOUNT = 131.97 mV/us | [D] |
| end of the ramp | the controller's overflow + its 3 DRAIN cycles = count 259 (the bench's 20-count overrun is gone) | [C] ADR 0025 |

The comparator's in-cell code offset ranges -4.5..+11.5 old LSB
(-26..+67 mV, ADR 0015) [M]: a cell that trips early can only get a code if
the ramp is already below its level when the count starts, so the ramp
starts **64.5 mV (11 old LSB, 9.77 LSB) below the window** [D] (the
pre-roll, in scope [U]).

**The principle that sets the current (I/C) [U, D].** The ramp's slope is
I / C. A current defined by the same capacitor type tracks it: I = C_UNIT x
V_REF x F_CLK, one unit MIM (the cells' 5 um square, 54.52 fF [P]) charged
to V_REF and discharged every clock period. On a ramp capacitor of N such
units the slope is V_REF x F_CLK / N: a unit-count ratio, the 20 MHz clock
and a supply ratio; no resistor and no transistor current enters it. With
V_REF = 5/33 AVDD = 0.5 V (the same tap ratio as VR_LO [C]) the current is
0.545 uA and N = 74 (rounded down) puts the slope at 1 LSB per count + 0.49 % with the cells' load counted (recipe s.2-3; 83 on the old grid). The beta-multiplier bias of ADR 0017 (0.74-1.62x
over PVT, 0.44 %/% of AVDD) is not used for the ramp [U].

## 2. Interface (frozen by this specification)

| Port | Direction | What it is |
| --- | --- | --- |
| `vramp` | out | the ramp; the I/C source's output current enters here; every cell's S1 hangs on it |
| `rst` | in | 0 / VDD; HIGH = reset (vramp held at vrlo); falls at TR on a rising clock edge, TR >= TS3 + 300 ns [C, ADR 0018 R6]; rises after the overrun |
| `vrlo` | in | the reset level, from `vrlo_ref`; sinks the ramp current while `rst` is high and the end-of-ramp dump (vrlo_ref R2, R3) |
| `vss` | | AVSS (the capacitor's bottom plate, the switch's body) |

Subcircuit `ramp_simple vramp rst vrlo vss`. The count starts at TR; code k
is the k-th falling clock edge after TR at which the latch takes a fallen
dout (`Analog_top/tb_params.inc`).

## 3. Requirements

| R | Requirement | Value | Label |
| --- | --- | --- | --- |
| R1 | Slope | V_REF x F_CLK / N = SLOPE; N is rounded DOWN so the design slope is on the fast side (+0.49 % at N = 74: R3 forbids a slow ramp); at the design current the measured slope equals the design slope within 0.5 % (the cells' load and the switch's junction) | [D] |
| R2 | Reset level (pre-roll) | VR_LO = 0.5 V - 64.5 mV = **0.4355 V** nominal (9.77 LSB); the count starts at the release; an offset-free cell reads 9 for VIN = 0.5 V | [D]; [U] scope |
| R3 | Count budget | the valid codes 0..254 (255 = timeout) cover VR_LO .. 2.088 V = the pre-roll, the 0.5-2.0 V window and the +3 sigma offset (87.9 mV) even when the ramp is 1.8 % slow against the grid (the LSB is derived so, ADR 0025). The 1.8 % is split: the source's slowest current 2.0 % below the design current [A] on the design slope's +0.49 % leaves 0.28 % for the cell's own deviation (`size_slow_margin_cell_pct` >= 0) | [D]; [U] ADR 0025 |
| R4 | Ramp reach and top | vramp at count 255 >= **2.088 V** at the design current and at 0.98x; the ramp ends at count 259 (2.145 V). Sensed-node maximum VREF + alpha (top - VIN_min) = **3.08 V** at alpha 0.87: over the 3.0 V allocation, under the 3.3 V devices (reported, ADR 0025; the allocation is the analog owner's open item, spec s.5.3) | [D]; alpha [P] |
| R5 | Tracking | the slope follows the MIM over process and temperature through the I/C source's C_UNIT (its current at the MIM corners is 0.600 / 0.491 uA against the ramp's 4.40 / 3.60 pF per 4 pF [P]); the residual gain error is the cells' load (not a MIM, 1.6 % of C) and the unit ratio's rounding, both calibrated by the transfer measurement (spec s.6). No trim word | [D] |
| R6 | Linearity | ramp INL end-point over the conversion window <= **0.2 LSB** for the cell alone (the switch's junction C(V) and the MIM's voltage coefficient: measured 0.0005 LSB on an ideal current); the current source's own output resistance is the I/C source's requirement: a bow of 0.05 LSB needs 2.0 Gohm at 0.55 uA (0.15 LSB: 0.67 Gohm), `size_src_rout_*`; in the conversion, real minus ideal ramp (`adc4`) <= **0.30 LSB** (the comparator-ramp interaction of R9 included; was 0.1) | [A] cell; [U] conversion, ADR 0025 |
| R7 | Load | per cell: C_S 54.52 fF [P] in series with the comparator plate's capacitance plus the S1 / S0 junctions: **19 fF average over a conversion** [M, `adc4`], ~13 fF far from the trip and up to ~35 fF near it [D]. Four cells now; the Tape-out 2/3 arrays re-size N and the I/C ratio by this rule (spec s.5.2) | [C] [P] [M] |
| R7a | Load dependence | slope change from 4 to 16 and to 64 cells reported (the cells add to C: -5.3 / -21.8 % with a fixed current [M]) | reported |
| R8 | Reset level accuracy | (a) the static drop I x Ron(XRST) <= **0.5 LSB** at 1.1x current and the worst Ron over PVT; (b) the S1 charge left on vramp at TR <= 0.05 LSB (vrlo_ref R5), tau = Ron x C_total <= **30 ns** | [A] (a); [C] (b) |
| R9 | Trip-kick crosstalk | a decided cell's comparator keeps pulling charge out of vramp after its decision (its gain node descends with the ramp through the input pair's C_GD) and the capacitor stores it; three aggressors on a later cell <= **0.30 LSB** (`adc4`, real minus ideal ramp, aggressors 0.25 / 1 / 4 / 16 / 64 LSB early; accepted, funded from ADR 0013's reserve) | [U] ADR 0025 |
| R10 | Post-decision and clock-edge kick | <= 0.01 LSB on vramp per decided cell (measured 0.0003 LSB, `runs/cell-trannoise/20261028T092739Z`) | [A], [M] |
| R11 | Recovery | after the end-of-ramp reset (4.6 pF from 2.05 V: 7.5 pC into vrlo_ref), vramp back within 0.05 LSB 1 us after `rst` rises (vrlo_ref R4) | [C] vrlo_ref |
| R12 | Noise | the cell's own noise is the reset kT/C (0.005 LSB [D]); the current source's noise allocation is 0.07 + 0.11 LSB (ADR 0013: "ramp core" + "ramp bias"), handed to the I/C source | [C] |
| R13 | Supply | the slope is ratiometric to AVDD through V_REF (1 %/%), as VR_LO and VREF are; the cell's own sensitivity (junction, MIM) <= 0.1 %/% | [D]; [A] |
| R14 | Area | N x 25 um2 of MIM (2075 um2 at N = 83) over the cells; the switch | [D] |
| R15 | PVT | R1, R4, R6, R8a and the start at 45 cells (5 corners x 0/27/85 C x 3.0/3.3/3.6 V) on the design current at the typical MIM; at the MIM corners the slope with a fixed current is reported (what the I/C source tracks) | [A] |
| R16 | Length | every L <= 0.36 um (the switch 0.28 um); no long device remains in the cell | rule |

## 4. Derivations behind the table

**R2, the pre-roll level.** A comparator with offset -x LSB trips when
vramp = VIN - x LSB. If vramp starts at VIN_min, every cell with a negative
offset has already tripped at the release for VIN near 0.5 V and reads 0.
Starting the ramp 11 LSB lower puts the trip of the -10.5 LSB cell 0.5 LSB
after the release. The only physical way to start lower is a lower reset
level: vrlo_ref's tap (decision 5.2).

**R3, the count budget.** With the count from the release, VIN = 2.0 V in an
offset-free cell reads 267 and a +3 sigma cell 282: an 8-bit code with the
20-count overrun reaches 275 (decision 5.1).

**R1/R5, the unit ratio.** I / C_total = SLOPE with I = C_UNIT V_REF F_CLK
gives N = V_REF F_CLK / SLOPE - (C_load + C_rst) / C_UNIT = 85.3 - 1.4 =
83.9 -> 83, rounded DOWN so that the rounding never makes the ramp slow (R3); the design slope is +1.1 % fast, a constant gain term. The MIM part of C_total (98.3 %) tracks C_UNIT exactly in ratio; the cells' 76 fF and the switch's junction do not (a 1.6 % gain
term, constant). The LSB at typical is then 5.92 mV (+1.1 % against the grid, `size_slope_err_design_pct`; the slow margin left for the source is 2.9 %).

**R6, the source's output resistance.** A current source of output
resistance r_out across the swing delivers I (1 - V / (I r_out)); the bow is
V_swing / (I r_out) x 32 LSB [D]. For 0.05 LSB at 0.55 uA: r_out >= 2.0 Gohm,
which a single transistor does not reach (the L 8 um mirror measured
0.73 Gohm [M, `../ramp_gen`]): the I/C source's output stage is a cascode or
a regulated one. Handed to `../ic_source` (section 6).

## 5. Decisions (user, 2026-10-29, ADR 0025)

1. **Code budget with the pre-roll (R3): 8-bit codes, wider LSB.** The
   payload stays 32 bits. LSB = (pre-roll 64.5 mV + 1.5 V + offset margin
   87.9 mV) / (255 x 0.982) = 6.60 mV [U, D]: the slowest ramp the budget
   allows covers the whole 0.5-2.0 V window and the +3 sigma offset in the
   255 valid codes (227 codes over the window). VR_LO stays 0.4355 V (the
   pre-roll is fixed in volts); N re-sizes to ~74 units. Rejected: losing
   the top 11 codes (the window is a requirement), a 9-bit count (payload
   change). Applied in `rs_common.py` (N = 74); `adc4` carries the grid into
   the macro's bench per case; the macro's own `tb_params.inc` follows at
   integration.
2. **The pre-roll level: vrlo_ref re-tapped on its own divider** to
   0.4355 V nominal (amends ADR 0018, re-runs `vrlo-ref`). The I/C source
   keeps its own 5/33 divider for V_REF.
3. **The trip-kick crosstalk is accepted** (R9 and the in-conversion part
   of R6, one mechanism): allocation 0.10 -> 0.30 LSB [U], funded from the
   PVT / PEX reserve of ADR 0013 (0.30 -> 0.10). The adc4 bench adds a
   64 LSB-early aggressor case to bound the maximum before the gate is
   trusted. Rejected: opening a decided cell's S1, a gain-node clamp, more
   units.

## 6. What this specification hands to the I/C current source

| Item | Value | From |
| --- | --- | --- |
| current | C_UNIT x V_REF x F_CLK = 0.545 uA at typical (0.600 / 0.491 uA at the MIM ss / ff corners) | R1/R5 |
| reference | V_REF = 5/33 AVDD = 0.5 V; a divider tap, no current drawn by the reference input | R5 |
| clock | the 20 MHz count clock, two non-overlapping phases made inside the source | [C] |
| output resistance | >= 2.0 Gohm at the ramp node (0.05 LSB bow) or >= 0.67 Gohm (0.15 LSB) over 0.44-2.05 V of swing | R6 |
| noise | <= 0.11 LSB rms at code 255 from 1 Hz through the ramp's integration kernel (ADR 0013's "ramp bias" share; the "ramp core" 0.07 share is also free) | R12 |
| supply | ratiometric through V_REF; the loop's own rejection of the 20 MHz switching at the output: the ripple at vramp <= 0.05 LSB | R13 |
| disturbance | the switching must not reach VR_LO or VREF: the reference capacitor switches against the source's own node, not the shared references | R8 |
| slow limit | the slowest current (mismatch 3 sigma + PVT + clock duty) <= 2.0 % below the design current | R3 [A], ADR 0025 |
| start-up | current within 1 % of its final value from a cold supply; the macro's T0 grows to match (ic_source R7: 60 us) | [C] Analog_top; [U] |
| load on vramp | the output device's drain junction adds to C_total (counted in N) | R7 |

## 7. Not covered

- The external ramp injection / bypass and the ramp monitor (spec s.7.1,
  s.7.3): open items [U].
- Layout and extraction (PEX); the VACASK transient noise of the ramp (the
  cell bench's `ramp` group after integration).
