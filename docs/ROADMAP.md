# Roadmap

The controlled first-prototype scope is defined in
[`PROTOTYPE_SPECIFICATION.md`](PROTOTYPE_SPECIFICATION.md). Performance work
shall not displace its Must-level flow and observability requirements.

## Phase 0: Freeze external constraints

- [x] Select wafer.space GF180MCU Run 3 as the MPW route.
- [x] Record the published 2026-12-16 clean-GDS deadline and Q2 2027 shipment.
- [x] Provider contact (2026-08-30): wafer.space issues no written
  confirmations and performs DRC-only checking; acceptance authority is the
  automated precheck and COB checks on platform.wafer.space. Gate A was
  redefined accordingly in
  [`PDK_PAD_SUPPLY_FREEZE.md`](PDK_PAD_SUPPLY_FREEZE.md).
- [x] Confirm the PDK/template commits against the public template `main`
  (matched as of 2026-08-30; re-verify at purchase and before submission).
- [ ] Decide the early-bird purchase (2026-09-30 deadline) with the
  collaboration.
- [x] Padring experiment (platform-verified 2026-08-31): the `0p5x1` ring
  with `bidir[43:42]` re-typed as a second core `vdd/vss` pair passes the
  platform.wafer.space CoB precheck (Check #800, precheck 1.7.3: pad mask,
  antenna, Magic and KLayout DRC all clean). The "Not Manufacturable"
  verdict stems only from empty-core minimum-density errors, which fill
  insertion resolves in a real build. The AVDD-separation plan is therefore
  frozen (all grounds are common on the default COB breakout, so only `AVDD`
  is separately measured).
- Freeze the reference container and tool versions.

Exit criterion: a passing padring-experiment GDS, a purchased slot, and a
reproducible tool environment.

## Phase 1: Analog flow bring-up

- Simulate GF180 NMOS and PMOS DC curves.
- Simulate an inverter and current mirror across process, voltage, temperature.
- Create one layout and pass DRC and LVS.
- Archive commands and result summaries in Git.

Exit criterion: another Mac or Linux host can reproduce the results.

## Phase 2: Wilkinson building blocks

- Sampling switch and hold capacitor.
- Low-offset comparator with a controllable test input.
- Global or local ramp generator and ramp monitor.
- Counter/latch interface and metastability characterization.
- PVT and Monte Carlo characterization.

Exit criterion: a transistor-level ADC slice meets an agreed resolution,
conversion-time, power, and area budget.

Progress: the typical-corner NMOS sampling-cell baseline and transmission-gate
comparison are automated. The transmission gate is the provisional topology;
input-range, PVT, clock-skew, sizing, and physical-capacitor studies remain.
The continuous-time comparator baseline passes provisional 6-bit limits with
rail-to-rail output; offset separation and 8-bit improvement remain.
The PMOS-current-source ramp baseline is automated and passes typical-corner
reset, slope, coarse-linearity, and power limits using an external bias.
The three analog blocks are integrated in a single-point Wilkinson-slice test;
timing-derived 6-bit code formation passes within one count. Physical RTL
counter/capture integration and a multi-point transfer test remain.
The synthesizable 6-bit counter/capture RTL is implemented with self-checking
simulation and generic Yosys synthesis. GF180 cell mapping, timing, and the
analog comparator crossing strategy remain before mixed-signal integration.
File-based mixed-signal co-verification now transfers the measured GF180
comparator timing into the real counter RTL and checks matching code capture.
Clock-phase and metastability studies remain.
An eight-point transistor-level input sweep now checks coarse transfer
monotonicity, sampling error, and code error. Dense transition testing is still
required before making a no-missing-code claim.
The PMOS-input comparator alternative extends measurable operation to 1.8 V
and reduces the 0.4 V error, but worsens high-range delay error. Both NMOS and
PMOS variants remain candidate test structures pending offset/delay separation.
Nominal DC trip-point sweeps show 8-12 mV static error for both variants, much
smaller than the worst dynamic code error. Dynamic settling is now the primary
comparator optimization target; mismatch Monte Carlo remains outstanding.
A 2 pF/10 MHz slow-ramp option reduced the worst tested low-end error by only
one count while doubling conversion time, so the 1 pF/20 MHz baseline is kept
and architecture work moves to four-cell integration.
Four replicated transmission-gate cells now have automated sequential-capture,
4-to-1 analog-mux, and shared Wilkinson-conversion tests. A single ramp and
comparator convert all four cells in 2.9 us slots; the measured codes are
monotonic and within three counts of the provisional ideal values. A
synthesizable controller now sequences bus reset, mux settle, ramp release, and
counter capture for four cells and stores all four 6-bit results. File-based
co-verification transfers all four transistor-level crossing times into that
controller and checks identical packed codes. A +/-2 ns phase sweep identifies
cell 2 only 500 ps from a conversion-clock boundary. Buffered readout
optimization and transistor-level metastability characterization remain. The
production digital path now uses Gray-coded comparator-edge capture and a
24-bit synchronous serial readout. GF180 mapping and 20 MHz pre-layout STA pass
for the integrated digital top.

Architecture revision 2026-09-18 (spec 0.6-draft): the design review with
the collaborating IC-design group removed the analog MUX (comparator per cell,
parallel conversion), fixed the hold capacitor at the smallest drawable MIM
(54.5 fF), adopted bottom-plate sampling with the ramp applied to the
capacitor (fixed comparator reference), and set the ADC to 8 bit. Done since:
parallel 8-bit controller and 32-bit digital top with self-checking tests,
GF180 mapping, and 20 MHz STA (`make parallel-controller`, `make digital-top`);
bottom-plate cell study showing that the comparator must sense the
first-frozen plate (pedestal spread 0.09 mV, gain error -0.02 %, versus 2-4 LSB
signal-dependent pedestal and +9 % gain error when sensing the input-side
plate) — `make bottom-plate-cell`. Remaining in Phase 2: comparator spec
re-derivation (transient noise, fixed trip), ramp generator for the capacitor
load, on-chip bottom-first switch delay, new mixed-signal co-simulation.

## Phase 3: Test macro

- Small sampling array.
- Wilkinson conversion and digital readout.
- Standalone test access for switch, comparator, ramp, and clock.
- Extracted post-layout simulation.

Exit criterion: DRC/LVS-clean macro with a documented verification matrix.

Progress: the integrated digital top now completes a reproducible GF180
RTL-to-GDS flow. Post-route multi-corner STA, antenna checks, detailed-routing
DRC, Magic DRC, KLayout DRC, and Netgen LVS all pass with zero violations. The
analog macro layout and extracted analog simulation remain before this phase
can close. Digital-on-top integration is proven (2026-09-25): an analog hard
macro built from the gdsfactory generator (GDS/LEF/lib/blackbox/SPICE views)
is placed, powered and routed by LibreLane with zero DRC/LVS/timing/antenna
violations (`experiments/digital_on_top`).

## Phase 4: Tape-out integration

- Pad ring, ESD, power domains, decoupling, and seal-ring constraints.
- Top-level mixed-signal integration and package/PCB co-design.
- Provider signoff and final reproducibility run.

## Scale constraint for Tape-out 3 (recorded 2026-09-18)

The first drawn GF180 unit cell (input gate, 54.5 fF MIM over the comparator,
comparator, buffers; no routing) measures 28 x 22 um = 616 um^2, dominated by
the comparator. Scaling estimates against the provider's slots (0.5x1 core
4.46 mm^2, 1x1 core ~12.9 mm^2):

| Array | Cells | Cell area only | Fits |
| --- | ---: | ---: | --- |
| 8 ch x 32768 (IRSX) | 262k | ~160 mm^2 | no |
| 1 ch x 32768 | 33k | ~20 mm^2 | no (1x1) |
| 8 ch x 2048 | 16k | ~10 mm^2 | marginal (1x1) |
| 1 ch x 4096 | 4k | ~2.5 mm^2 | yes (0.5x1) |

Consequences: (1) the Tape-out 3 depth must be derived from the required
*time* depth (trigger latency x sampling rate) and the measured cell area,
not copied from IRSX; (2) GF180's 3.3 V devices (min L 0.28 um) offer no
shrink path, so an IRSX-class 8 x 32k array at multi-GSa/s implies a finer
node (open: IHP SG13G2 130 nm; closed: commercial 65-130 nm) — a decision for
the Tape-out 3 gate, while the architecture, calibration scheme, and flow
developed here carry over; (3) a compact comparator is the main area lever
(the register/latch bank is shared per conversion window and does not scale
with cell count).
