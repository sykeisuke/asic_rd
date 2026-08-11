# IRSX-like ASIC Prototype Specification

Version: 0.1 (draft)

Date: 2026-08-10

Process baseline: GF180MCU (`gf180mcuD`)

## 1. Purpose

The first prototype shall demonstrate a complete, reproducible mixed-signal
ASIC design flow. Peak detector performance is not the primary tape-out
criterion. The project is successful when a small waveform-sampling and
Wilkinson-conversion signal path can be designed, verified, fabricated, and
measured with enough internal access to identify failures.

The demonstrated flow shall include:

1. Architecture and specification control.
2. Transistor-level schematic design and simulation.
3. RTL design and mixed-signal integration.
4. Layout, DRC, LVS, extraction, and post-layout simulation.
5. Pad-ring and top-level integration.
6. Reproducible GDS/OASIS submission package generation.
7. Evaluation PCB, FPGA control/readout, and first-silicon measurements.
8. Open-source release of design sources, tests, and reports.

## 2. Relationship to the proposal

The proposal described a one-channel, multi-GSa/s waveform digitizer with
approximately 25 ps timing resolution, 500 MHz analog bandwidth, a 12-bit
Wilkinson ADC, less than 125 mW/channel, and FPGA readout over a high-speed
link. These remain long-term research goals, not pass/fail requirements for
the first prototype.

This specification deliberately reduces speed, resolution, array depth, and
I/O complexity while retaining the architectural path from analog sampling
through digitization and digital readout.

## 3. Success levels

Requirements are classified as follows:

- **Must**: required for first-prototype tape-out or flow completion.
- **Target**: design objective, but failure to meet the number does not by
  itself invalidate the complete-flow demonstration.
- **Stretch**: included only if schedule, area, and verification maturity
  permit.

## 4. Prototype architecture

The minimum integrated signal path is:

```text
Analog input
    -> sampling switch
    -> small storage-capacitor array
    -> cell selection
    -> comparator against a voltage ramp
    -> counter capture / result latch
    -> slow CMOS serial readout
    -> FPGA or host test controller
```

The ramp and critical internal nodes shall be externally accessible in test
modes. This allows the comparator, storage array, counter, and readout to be
tested independently if the on-chip ramp generator does not perform as
expected.

## 5. Top-level specifications

| Item | Must | Target | Stretch |
| --- | --- | --- | --- |
| Process | GF180MCU `gf180mcuD` | MPW-provider-qualified revision | - |
| Signal channels | 1 | 1 | 2 replicated test channels |
| Storage depth | 4 cells | 8 cells | 16 cells |
| Sampling clock | External, single-ended CMOS | 10-50 MSa/s | 100 MSa/s or higher |
| Sampling timing | Functional capture with documented aperture | Characterize cell-to-cell timing | On-chip delay line |
| Analog input | Unipolar voltage input within characterized safe range | 0.3-2.8 V nominal range | Dedicated fast input buffer |
| Input bandwidth | Demonstrate sampled sine/pulse response | At least 10 MHz | At least 50 MHz |
| ADC architecture | Wilkinson / single-slope | Wilkinson with internal ramp | Multi-cell parallel conversion |
| ADC resolution | 6-bit functional conversion | 8-bit monotonic conversion | 10-bit characterization |
| ADC linearity | Transfer curve measurable | No missing codes at 8 bit | DNL/INL within 1 LSB |
| Ramp source | External ramp input and bypass path | On-chip ramp generator | Programmable slope/current |
| Conversion clock | External CMOS clock | 10-50 MHz | 100 MHz |
| Readout | Slow synchronous serial CMOS | SPI-like interface | Framed serializer |
| Power | Measurable by separated supplies | Less than 50 mW core, excluding I/O | Power-gated modes |
| Package/interface | Provider-supported pad ring and package/COB | Evaluation PCB | High-speed package study |

Numerical target values may be revised after initial device, capacitor, and
comparator characterization. Any revision shall be recorded in Git before the
affected block is frozen.

## 6. Required functional blocks

### 6.1 Sampling cell

Each cell shall contain a GF180-compatible sampling switch and storage
capacitor. The first design may use a single NMOS switch; a transmission gate
or bootstrapped switch is a target only after reliability and voltage limits
are reviewed.

Required simulations:

- Acquisition and hold transient response.
- Droop versus hold time.
- Signal-dependent charge injection.
- Clock feedthrough.
- Process, supply, and temperature corners.

### 6.2 Storage array and selection

At least four cells shall be addressable. Sampling and readout may be
sequential; simultaneous high-speed write and conversion are not required.
Gray-code addressing, deep circular buffers, and DLL-based timing are outside
the first-prototype minimum scope.

### 6.3 Comparator

The comparator shall detect the crossing between a held sample and the ramp.
The design shall prioritize observable operation and input range over minimum
delay or power.

Must-characterize quantities:

- Input common-mode range.
- Input-referred offset, including Monte Carlo mismatch.
- Propagation delay versus overdrive.
- Kickback onto the held sample and ramp.
- Static or dynamic power, as applicable.

A nominal simulated offset below 20 mV is an initial target, not a tape-out
pass/fail limit.

### 6.4 Ramp generator

The chip shall accept an external voltage ramp. An on-chip current-source and
capacitor ramp generator is a target block and shall have a monitor pad or
buffered test output. The external ramp path is mandatory for debug and shall
remain usable independently of the internal generator.

### 6.5 Counter and capture logic

The digital block shall count an external conversion clock and capture the
count at the comparator transition. Six bits are required; eight bits are the
target. The RTL shall have a standalone simulation and synthesis test.

### 6.6 Control and readout

The minimum interface shall use ordinary CMOS pads and a low-speed synchronous
protocol. Required operations are reset, sample, start conversion, select
cell, and shift/read conversion data. LVDS and a high-speed serializer are not
required for the first prototype.

## 7. Test and debug requirements

The following observability is mandatory, subject to pad availability:

- Direct or buffered sampling-cell output for at least one cell.
- External ramp input.
- Buffered internal-ramp monitor.
- Comparator standalone input mode and digital output.
- Conversion clock input and divided-clock monitor.
- Counter test mode independent of the analog comparator.
- Scan or direct access to captured ADC code.
- Separate analog, digital, and I/O supply current measurement points.
- At least one replica device/capacitor or analog characterization structure.

Test access takes priority over storage depth and serializer complexity.

## 8. Electrical and reliability constraints

- Device types, terminal voltages, and pad cells shall comply with the exact
  MPW-qualified GF180MCU PDK revision.
- No node may exceed foundry oxide, junction, or ESD limits in normal or test
  modes.
- Clock and analog input ranges shall be documented at top level.
- Analog and digital supplies shall be independently filterable on the PCB.
- All asynchronous external controls entering digital logic shall be
  synchronized or constrained by the test protocol.
- Unused inputs shall have defined bias states.

Absolute voltage limits remain TBD until the MPW provider and I/O library are
frozen.

## 9. Verification requirements

### 9.1 Analog blocks

Every tape-out analog block shall have:

- A standalone Xschem schematic and ngspice testbench.
- Nominal DC, AC, and transient tests as applicable.
- Process, voltage, and temperature corner tests.
- Monte Carlo mismatch analysis for matching-sensitive blocks.
- Defined measurements and automated pass/report output.
- DRC-clean and LVS-clean layout.
- Extracted post-layout simulation for its primary function.

### 9.2 Digital blocks

Every tape-out RTL block shall have:

- Self-checking simulation.
- Reset and boundary-condition tests.
- Synthesis with the selected GF180 standard-cell library.
- Timing analysis at the intended slow operating clock.
- Gate-level or equivalent post-synthesis verification before integration.

### 9.3 Top level

Top-level signoff shall include:

- Pad-ring and power-domain review.
- Full-chip DRC and LVS.
- Antenna, density/fill, and provider-specific checks where required.
- Extracted simulation of critical analog paths.
- Mixed-signal functional test of sample, convert, capture, and readout.
- Reproducible build from a clean checkout using pinned tools and PDK data.

## 10. Silicon acceptance plan

The first silicon is considered a complete-flow success when all of the
following are demonstrated or conclusively diagnosed through test access:

1. The packaged die powers safely with measurable analog and digital currents.
2. Reset, control, clock, and readout communication operate.
3. At least one sampling cell acquires and holds a DC or low-frequency input.
4. The comparator crossing can be observed using the external ramp path.
5. The counter capture and serial readout return a conversion code.
6. A multi-point ADC transfer curve can be measured.
7. At least four stored samples can be read and associated with their cell
   addresses, or the exact failing stage can be isolated using test modes.
8. Pre-silicon and measured results are published with the design sources.

Meeting the proposal's eventual speed, bandwidth, timing, or 12-bit resolution
is not required for first-silicon acceptance.

## 11. Explicit non-goals for the first prototype

- Multi-GSa/s operation.
- 25 ps timing resolution.
- 500 MHz validated analog bandwidth.
- Guaranteed 12-bit ADC performance.
- A 128- or 512-cell storage array.
- Eight-channel integration.
- DLL-locked sampling timing.
- Production-quality PMT amplifier and shaper.
- LVDS output or a high-speed serializer.
- Radiation qualification or production reliability qualification.

These items remain candidates for later revisions after the basic flow and
silicon measurement loop are established.

## 12. Milestones and freeze gates

### Gate A: Specification freeze

- Resolve the open decisions in Section 13.
- Confirm MPW provider, PDK revision, pad ring, and available I/O count.
- Approve Must/Target/Stretch classifications.

### Gate B: Block schematic freeze

- Sampling cell, comparator, ramp, and counter pass standalone tests.
- Initial area and pad budget are credible.

### Gate C: Block layout freeze

- Required blocks are DRC/LVS clean.
- Primary extracted simulations pass or deviations are documented.

### Gate D: Top-level freeze

- Full-chip integration and debug modes are verified.
- PCB and package pinout are reviewed together with the ASIC pinout.

### Gate E: Tape-out release

- Provider signoff checklist is complete.
- Clean-clone reproducibility run passes.
- Final GDS/OASIS and reports are tagged in Git.

## 13. Open decisions

The following shall be resolved before Gate A:

1. Exact MPW run, submission date, die slot, and PDK revision.
2. Package/COB option and mandatory pad-ring template.
3. Core, analog, and I/O supply voltages.
4. Four versus eight storage cells.
5. Six-bit minimum versus eight-bit-only counter implementation.
6. External clock frequency used as the formal target.
7. Capacitor type and nominal storage capacitance.
8. Static versus dynamic comparator architecture.
9. Internal ramp implementation and external-ramp voltage range.
10. FPGA/evaluation-board choice and final readout pin protocol.

## 14. Change control

This document is the controlled specification for the first prototype. A
change that affects interfaces, pad count, supply domains, device reliability,
or a Must requirement requires a version update and review. Performance
targets may be refined as characterization data becomes available, provided
the complete-flow objective and silicon observability are preserved.

