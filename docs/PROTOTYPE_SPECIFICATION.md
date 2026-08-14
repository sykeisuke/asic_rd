# IRSX-like ASIC Prototype Specification

Version: 0.2 (student baseline)

Date: 2026-08-13

Process baseline: GF180MCU (`gf180mcuD`)

Status: architecture baseline frozen; MPW/provider-dependent items remain open

Language: **English** | [日本語版](PROTOTYPE_SPECIFICATION_JP.md)

## 1. Purpose and document control

This is the controlled specification shared by the student team for Tape-out 1.
The first priority is a reproducible demonstration of the complete flow from
specification and schematic through simulation, layout, signoff, fabrication,
and measurement. Maximum performance is not the primary acceptance criterion.

The laboratory procedure is in [`lecture/README.md`](lecture/README.md), current
verification status is in [`VERIFICATION_MATRIX.md`](VERIFICATION_MATRIX.md),
and unfinished tape-out work is tracked in
[`TAPEOUT_BLOCKERS.md`](TAPEOUT_BLOCKERS.md).

- **Must**: required for Tape-out 1 unless an explicit waiver or scope revision is approved.
- **Target**: an objective whose miss does not by itself invalidate the flow demonstration.
- **Stretch**: attempted only when it does not endanger Must requirements.
- **Demonstrated**: reproducible pre-layout evidence exists in the repository.
- **TBD**: requires an external MPW, PDK, pad, package, or physical-design decision.

## 2. Relationship to the proposal

The proposal begins with a one-channel proof of concept. The longer-term
IRSX-equivalent objective is eight channels with multi-GSa/s sampling,
approximately 25 ps timing, 500 MHz analog bandwidth, a 12-bit Wilkinson ADC,
and FPGA readout. These longer-term capabilities are not Tape-out 1 pass/fail
criteria.

Tape-out 1 retains the IRSX-like signal path at deliberately reduced scale:

```text
1 analog channel
-> 4 sampling cells
-> 4-to-1 analog MUX
-> shared ramp + comparator
-> 6-bit counter capture
-> four 6-bit registers
-> 24-bit synchronous serial readout
```

## 3. Tape-out 1 success definition

Tape-out 1 shall demonstrate this complete chain:

```text
specification
-> schematic
-> pre-layout simulation
-> layout
-> DRC / LVS
-> PEX / post-layout simulation
-> analog + digital top integration
-> pad ring / package / PCB
-> provider submission
-> first-silicon measurement
```

Silicon success includes either correct 4-cell/6-bit operation or conclusive
fault isolation through the required test modes. Achieving 12 bits, 1 GSa/s,
or 500 MHz is not required for Tape-out 1.

## 4. Frozen architecture baseline

| Item | Tape-out 1 Must | Current baseline | Later revision |
| --- | --- | --- | --- |
| Process | Provider-qualified GF180MCU | `gf180mcuD` open PDK | Freeze exact provider revision |
| Analog channels | 1 | 1 | Eight channels, matching the IRSX-level objective |
| Storage depth | 4 cells | Demonstrated | 32-128 cells |
| Sampling switch | Transmission gate | NMOS/PMOS comparison demonstrated | Bootstrapped switch after reliability review |
| Hold capacitor | One per cell | 1 pF simulation baseline | Select PDK capacitor after layout study |
| Read MUX | 4-to-1 analog MUX | Sequential MUX demonstrated | Buffered/deeper array |
| ADC | Shared Wilkinson | Ramp/comparator demonstrated | Parallelism and calibration |
| Resolution | 6 bits | Timing-derived codes demonstrated | 8-10 bits, then 12-bit research |
| Counter capture | 6-bit Gray-safe capture | RTL demonstrated | Higher resolution |
| Result storage | Four 6-bit words | 24-bit packed payload demonstrated | Deeper memory |
| Readout | Slow synchronous CMOS serial | Demonstrated | Framed/high-speed link |
| Ramp | Internal ramp plus external debug path | Internal pre-layout baseline | Programmable/calibrated ramp |
| Clocking | External and board-controllable | 20 MHz conversion baseline | Fast sampling generator |
| Test access | Block isolation and observable nodes | Architecture defined | Final pads TBD |

Cell count, ADC width, payload format, clock-domain boundary, and analog/digital
interfaces are frozen. Changing any of them requires a specification revision
and full regression.

## 5. Functional requirements

### 5.1 Sampling and hold

`VIN` is connected to `VHOLD[i]` through a transmission gate while
`SAMPLE[i]` is active. `CHOLD[i]` retains the sampled voltage after opening.

Must requirements:

- Four cells capture distinguishable input values in the intended order.
- Each cell has explicit complementary switch control.
- Acquisition error, edge disturbance, and hold droop have defined measurements.
- Non-selected cells are not unintentionally overwritten.

The nominal regression stimuli are approximately 0.5, 0.8, 1.1, and 1.4 V.
They are not guaranteed silicon input limits.

### 5.2 Analog selection

A one-hot transmission-gate MUX connects one stored value to `MUX_BUS`.

- No more than one `SEL[i]` is active during conversion.
- A defined bus-reset interval separates cells.
- MUX settling completes before ramp release.
- Disturbance of the source hold capacitor is measured.

### 5.3 Wilkinson conversion

The ramp is reset, one cell is selected, and the counter starts. The comparator
captures the count when `VRAMP` crosses `MUX_BUS`.

```text
ideal_code = floor(crossing_time / conversion_clock_period)
code range = 0 ... 63
```

- Higher held voltage produces a later crossing and non-decreasing code.
- Four conversions complete without loss of cell order.
- Comparator polarity and capture convention are documented.
- A conversion timeout handles no-crossing cases.

The current nominal integrated signature is `16, 20, 27, 35`. It is a
regression result, not an INL/DNL guarantee.

### 5.4 Digital capture and readout

The controller sequence is:

```text
IDLE -> RESET_RAMP -> SELECT -> CONVERT -> CAPTURE -> NEXT -> DONE
```

- Gray-coded count capture is used at the asynchronous comparator boundary.
- Four 6-bit results remain associated with their cell numbers.
- The 24-bit payload is `{cell3, cell2, cell1, cell0}` unless explicitly revised.
- Serial bit order, active edge, frame start, and data-valid timing are documented.
- Reset, timeout, and phase-boundary cases have self-checking tests.

## 6. Provisional electrical targets

Provider-qualified limits override this table.

| Item | Must | Target | Stretch |
| --- | --- | --- | --- |
| Analog input | Safe operation in a characterized unipolar range | Verify 0.4-1.6 V baseline | Wider range with input buffer |
| Sampling rate | Externally controllable functional sampling | Characterize 10-50 MSa/s | 100 MSa/s or higher |
| Input bandwidth | Demonstrate DC/low-frequency sampling | At least 10 MHz measured | At least 50 MHz |
| ADC resolution | Functional 6-bit conversion | Monotonic 6-bit transfer | 8-bit test mode |
| Conversion clock | External CMOS | 20 MHz baseline | Up to 50 MHz after timing review |
| Conversion time | Below controller timeout | Complete four-cell sequence | Reduced dead time |
| Core power | Separate analog/digital measurement | Less than 50 mW excluding I/O | Power modes |
| Readout | Slow synchronous CMOS | FPGA-compatible protocol | Framed serializer |

No value is a silicon guarantee until PVT, mismatch, PEX, package effects, and
measurement uncertainty are included.

## 7. Required implementation and observability

### 7.1 Analog blocks

- Four transmission-gate sampling cells and hold capacitors.
- 4-to-1 analog MUX and bus reset.
- Ramp generator, reset device, bias, and monitor.
- Comparator and output buffer.
- External ramp injection or bypass.
- Required analog biasing and supply decoupling.

### 7.2 Digital blocks

- 6-bit counter and Gray-coded asynchronous capture.
- Four-cell conversion controller.
- Four 6-bit result registers.
- 24-bit synchronous serial readout.
- Reset, test mode, timeout, and status logic.

### 7.3 Mandatory test access

Subject to the final pad budget, the top shall provide:

- Direct or buffered observation of at least one `VHOLD` node.
- External ramp input and buffered internal-ramp monitor.
- Comparator standalone mode and digital output observation.
- Conversion-clock input and divided-clock/status monitor.
- Digital test mode independent of the analog crossing.
- Access to all captured codes.
- Separately measurable analog, digital, and I/O supply currents.
- At least one replica MOS/capacitor characterization structure.

Test access takes priority over additional depth, resolution, or serializer
complexity.

## 8. Verification requirements

### 8.1 Analog

Every analog block included in silicon requires a readable Xschem schematic or
controlled SPICE source, automated nominal measurements, applicable DC/AC/
transient tests, PVT corners, mismatch analysis for sensitive blocks, DRC/LVS
clean layout, and extracted post-layout verification.

```sh
make analog-regression
```

### 8.2 Digital and mixed signal

Every RTL block requires self-checking simulation, GF180 synthesis, timing
analysis, and boundary tests. Measured SPICE crossing times shall drive the
real capture RTL, including conversion-clock phase sweeps.

```sh
make course-regression
```

### 8.3 Physical and top-level signoff

```text
schematic simulation
-> layout
-> DRC
-> extraction
-> LVS
-> PEX simulation
```

LVS proves connectivity, not analog performance. PEX shall repeat sampling
error, hold disturbance, ramp slope/linearity, comparator delay/offset, and
integrated conversion measurements.

The full chip also requires qualified pad/ESD cells, power/substrate review,
analog macro integration, DRC/LVS/antenna/density/ERC/provider checks, and a
clean-checkout build using pinned tools and PDK data.

## 9. Silicon acceptance

Tape-out 1 is a complete-flow success when these are demonstrated or a failure
is conclusively isolated through test access:

1. Safe power-up and measurable analog/digital currents.
2. Functional reset, clocks, status, and serial communication.
3. Acquisition and hold of a DC or low-frequency input by at least one cell.
4. Observable comparator crossing with the external ramp.
5. Counter capture and bit-correct serial readout.
6. A measurable multi-point transfer curve.
7. Four samples associated with the correct cell addresses.
8. Internal-ramp behavior compared with the external reference.
9. Publication of measurements, failures, calibration, and pre-silicon comparison.

## 10. Explicit non-goals for Tape-out 1

- Multi-GSa/s operation or 25 ps timing resolution.
- Validated 500 MHz analog bandwidth.
- Guaranteed 8-, 10-, or 12-bit ADC performance.
- A 32-, 128-, or 512-cell array or IRSX-level eight-channel integration.
- DLL-locked timing, production PMT front end, or high-speed I/O.
- Radiation or production reliability qualification.

## 11. Freeze gates

### Gate A: External constraints

Confirm MPW run/date, die area, PDK revision, supplies, qualified I/O cells,
package/COB option, pad template, and provider deliverables.

### Gate B: Schematic

The 4-cell/6-bit architecture passes `make course-regression`; PVT/mismatch
criteria, interfaces, test modes, timeout, payload, area, power, and pad budgets
are reviewed.

### Gate C: Block layout

Analog and digital blocks are DRC/LVS clean, extracted critical simulations
pass or have reviewed waivers, and macro interfaces are frozen.

### Gate D: Full chip

Pads, power, macros, test structures, fill, and seal-ring constraints are
integrated; full-chip signoff passes; ASIC pinout, bond map, PCB, and FPGA
interface agree.

### Gate E: Release

Provider checklist and clean-clone build pass. GDS/OASIS, netlists, reports,
waivers, checksums, Git tag, and measurement plan are archived.

## 12. Open external decisions

The internal architecture is frozen at four cells and six bits. Remaining
decisions are:

1. MPW provider, run, slot, and deadline.
2. Accepted GF180MCU PDK release and metal stack.
3. Qualified supplies and pad/ESD libraries.
4. Die area, pad count/pitch, seal ring, and density rules.
5. Package, chip-on-board, or wire-bond carrier.
6. Final capacitor type/value after leakage, area, and PEX study.
7. Final comparator variant after PVT/mismatch/post-layout comparison.
8. Ramp ranges and monitor implementation.
9. Formal silicon sampling and conversion-clock limits.
10. Evaluation PCB, FPGA, connectors, and I/O voltage levels.

## 13. Change control

Changes to interfaces, cell count, ADC width, payload, pads, supplies,
reliability, or a Must requirement require a version/date update, written
impact assessment, updates to tests/matrix/Handbook/decision records, and full
regression. Parameter tuning may proceed without an architecture revision only
when interfaces, reliability limits, and Must behavior remain unchanged.
