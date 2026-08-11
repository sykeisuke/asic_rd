# Roadmap

The controlled first-prototype scope is defined in
[`PROTOTYPE_SPECIFICATION.md`](PROTOTYPE_SPECIFICATION.md). Performance work
shall not displace its Must-level flow and observability requirements.

## Phase 0: Freeze external constraints

- Confirm the wafer.space run expected for an early-2027 submission.
- Obtain the exact GF180MCU variant and accepted PDK release.
- Confirm slot size, pad ring, I/O count, packaging, and signoff requirements.
- Freeze the reference container and tool versions.

Exit criterion: a written submission-constraint sheet and a reproducible tool
environment.

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

## Phase 3: Test macro

- Small sampling array.
- Wilkinson conversion and digital readout.
- Standalone test access for switch, comparator, ramp, and clock.
- Extracted post-layout simulation.

Exit criterion: DRC/LVS-clean macro with a documented verification matrix.

## Phase 4: Tape-out integration

- Pad ring, ESD, power domains, decoupling, and seal-ring constraints.
- Top-level mixed-signal integration and package/PCB co-design.
- Provider signoff and final reproducibility run.
