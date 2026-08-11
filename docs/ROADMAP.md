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
