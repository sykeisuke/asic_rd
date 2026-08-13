# IRSX-like ASIC Prototype Specification

Version: 0.2 (student baseline)

Date: 2026-08-13

Process baseline: GF180MCU (`gf180mcuD`)

Status: architecture baseline frozen; MPW/provider-dependent items remain open

Language: **日本語** | [English version](PROTOTYPE_SPECIFICATION.md)

## 1. この仕様書の役割

本書は、最初のtape-outを目指す学生チームが共有するcontrolled specificationである。
回路を高性能化することより、仕様、回路図、simulation、layout、signoff、fabrication、
measurementまでのcomplete design flowを再現可能な形で実証することを優先する。

正式な学習手順は[`lecture/README.md`](lecture/README.md)、現在の検証状況は
[`VERIFICATION_MATRIX.md`](VERIFICATION_MATRIX.md)、tape-outまでの未完了項目は
[`TAPEOUT_BLOCKERS.md`](TAPEOUT_BLOCKERS.md)を参照する。

この仕様書における用語は次の意味を持つ。

- **Must**: Tape-out 1に必要。満たさない場合はscope変更または明示的waiverが必要。
- **Target**: 設計目標。未達でも原因と測定結果を残せばflow demonstrationは成立し得る。
- **Stretch**: Tape-out 1のMustを危険にせず追加できる場合のみ実装する。
- **Demonstrated**: 現在のrepositoryで再現可能なpre-layout結果が存在する。
- **TBD**: MPW provider、PDK、pad/packageなど外部条件の確定が必要。

## 2. Proposalとの関係

Proposalの長期目標は、1 channel、multi-GSa/s、約25 ps timing、500 MHz analog
bandwidth、12-bit Wilkinson ADC、FPGA readoutである。これらは研究program全体の目標で、
Tape-out 1の合否条件ではない。

Tape-out 1では、同じ基本構造を次の小規模仕様で実証する。

```text
1 analog channel
→ 4 sampling cells
→ 4-to-1 analog MUX
→ shared ramp + comparator
→ 6-bit counter capture
→ four 6-bit registers
→ 24-bit synchronous serial readout
```

速度、分解能、storage depthを意図的に下げる一方、sampling、hold、selection、
Wilkinson conversion、digital capture、readoutというIRSX-like signal pathは保持する。

## 3. Tape-out 1の成功定義

Tape-out 1の第一目的は、次を一度最後まで通すことである。

```text
specification
→ schematic
→ pre-layout simulation
→ layout
→ DRC / LVS
→ PEX / post-layout simulation
→ analog + digital top integration
→ pad ring / package / PCB
→ provider submission
→ first-silicon measurement
```

Silicon acceptanceでは、4-cell/6-bitの絶対精度だけでなく、test modeにより故障箇所を
切り分けられることも成功とみなす。Proposalの12-bit、1 GSa/s、500 MHzを達成することは
Tape-out 1の必須条件ではない。

## 4. Frozen architecture baseline

| Item | Tape-out 1 Must | Current baseline | Later revision |
| --- | --- | --- | --- |
| Process | Provider-qualified GF180MCU | `gf180mcuD` open PDK | Provider decision後にexact revision freeze |
| Analog channels | 1 | 1 | Multi-channel |
| Storage depth | 4 cells | 4 cells demonstrated | 32-128 cells |
| Sampling switch | Transmission gate | NMOS+PMOS comparison demonstrated | Bootstrapped switch after reliability review |
| Hold capacitor | One per cell | 1 pF simulation baseline | PDK capacitor and value after layout study |
| Read MUX | 4-to-1 analog MUX | Sequential MUX demonstrated | Buffered/deeper array |
| ADC | Shared Wilkinson/single-slope | Shared ramp and comparator demonstrated | Parallelism/calibration |
| Resolution | 6 bit | 6-bit timing-derived code demonstrated | 8-10 bit, then 12-bit research |
| Counter | 6-bit Gray-safe capture | RTL demonstrated | Higher resolution |
| Stored result | Four 6-bit words | 24-bit packed result demonstrated | Deeper memory |
| Readout | Slow synchronous CMOS serial | 24-bit serial demonstrated | Framed/high-speed link |
| Ramp | On-chip ramp plus external debug path | On-chip pre-layout baseline demonstrated | Programmable/calibrated ramp |
| Clocking | External, board-controllable | 20 MHz conversion-clock baseline | Fast sampling timing generator |
| Test access | Block isolation and observable nodes | Architecture defined | Final pad assignment TBD |

The baseline values above are frozen for educational and pre-layout integration work. A change to
cell count, ADC width, packed-word format, clock-domain boundary, or analog/digital interface requires
a specification revision and regression update.

## 5. Functional signal path

### 5.1 Sampling phase

`VIN` is connected to one `VHOLD[i]` through a transmission gate while `SAMPLE[i]` is active.
When the switch opens, `CHOLD[i]` stores the sampled voltage.

Must requirements:

- Four cells capture distinguishable input values in the intended order.
- Every cell has an explicit SAMPLE control and complementary switch control.
- Acquisition error, edge disturbance, and hold droop have defined measurements.
- Non-selected cells shall not be unintentionally overwritten.

The current nominal four-cell test stores approximately 0.5, 0.8, 1.1, and 1.4 V. These values are
regression stimuli, not guaranteed silicon input limits.

### 5.2 Selection phase

A one-hot 4-to-1 transmission-gate MUX connects one held voltage to `MUX_BUS`.

Must requirements:

- At most one `SEL[i]` is active during conversion.
- A defined bus-reset interval exists between cells.
- MUX settling completes before ramp release.
- Readout disturbance on the source hold capacitor is measured.

### 5.3 Wilkinson conversion phase

The ramp is reset, one cell is selected, and the 6-bit counter starts. When `VRAMP` crosses
`MUX_BUS`, the comparator produces a capture event. The captured count is the ADC code.

```text
ideal_code = floor(crossing_time / conversion_clock_period)
code range = 0 ... 63
```

Must requirements:

- Higher held voltage produces a later crossing and a non-decreasing code.
- All four conversions complete without cell-order loss.
- Comparator polarity and capture convention are documented.
- Timeout behavior is defined for no-crossing cases.

The current integrated nominal result is `16, 20, 27, 35`. This is a regression signature, not an
INL/DNL guarantee.

### 5.4 Digital capture and readout

Comparator timing crosses into the digital clock domain using Gray-coded count capture. The
controller sequences reset, select, settle, convert, capture, and next-cell operations.

```text
IDLE → RESET_RAMP → SELECT → CONVERT → CAPTURE → NEXT → DONE
```

Must requirements:

- Four 6-bit results are preserved in cell order.
- Packed payload is 24 bits: `{cell3, cell2, cell1, cell0}` unless revised explicitly.
- Serial bit order, active clock edge, frame start, and data-valid timing are documented.
- Reset and conversion timeout have self-checking RTL tests.
- Asynchronous comparator capture is verified near conversion-clock boundaries.

## 6. Electrical targets

Provider-qualified limits always override the provisional values in this section.

| Item | Must | Target | Stretch |
| --- | --- | --- | --- |
| Analog input | Safe unipolar operation in characterized range | Verify 0.4-1.6 V baseline | Wider range with input buffer |
| Sampling rate | Externally controllable functional sampling | 10-50 MSa/s characterization | 100 MSa/s or higher |
| Input bandwidth | DC and low-frequency sampling demonstrated | At least 10 MHz measured | At least 50 MHz |
| ADC resolution | Functional 6-bit conversion | Monotonic 6-bit transfer | 8-bit test mode |
| Conversion clock | External CMOS | 20 MHz baseline | Up to 50 MHz after timing review |
| Conversion time | Measurable and below controller timeout | Four cells within test sequence | Optimized dead time |
| Core power | Separate analog/digital measurement available | Less than 50 mW excluding I/O | Power modes |
| Readout | Slow synchronous CMOS | FPGA-compatible protocol | Framed serializer |

No numerical electrical target becomes a silicon guarantee until PVT, mismatch, PEX, package, and
measurement uncertainty are included.

## 7. Required blocks and test structures

### 7.1 Analog blocks

- Four transmission-gate sampling cells and hold capacitors.
- 4-to-1 analog MUX with bus reset.
- Ramp generator, reset device, bias circuit, and ramp monitor.
- Comparator with output buffer.
- External ramp injection or bypass path.
- Bias and supply decoupling required by the selected implementation.

### 7.2 Digital blocks

- 6-bit counter and Gray-coded asynchronous capture.
- Four-cell conversion controller.
- Four 6-bit result registers.
- 24-bit synchronous serial readout.
- Reset, test-mode, timeout, and status logic.

### 7.3 Mandatory observability

Subject to the final pad budget, the top shall provide:

- Direct or buffered observation of at least one `VHOLD` node.
- External ramp input and buffered internal-ramp monitor.
- Comparator standalone mode and digital output observation.
- Conversion-clock input and divided-clock/status monitor.
- Counter/digital test mode independent of analog crossing.
- Direct or serial access to all captured codes.
- Independently measurable analog, digital, and I/O supply currents.
- At least one replica MOS/capacitor characterization structure.

Test access has priority over extra storage cells, resolution, or serializer complexity.

## 8. Verification requirements

### 8.1 Pre-layout analog

Every analog block included in silicon shall have:

- A readable Xschem schematic or controlled SPICE source and documented hierarchy.
- Nominal DC, AC, and transient tests as applicable.
- Automated measurements and a reproducible command.
- Process, supply, and temperature corner tests.
- Mismatch/Monte Carlo analysis for comparator and matching-sensitive devices.
- A clear distinction between ideal-model, transistor-level, and integrated tests.

Current pre-layout regression is executed with:

```sh
make analog-regression
```

### 8.2 Digital and mixed signal

Every RTL block shall have self-checking simulation, synthesis with the selected GF180 standard-cell
library, and timing analysis. SPICE crossing times shall be transferred into the real capture RTL,
including phase-boundary tests.

```sh
make course-regression
```

### 8.3 Physical verification

Before tape-out, each analog macro and the full-chip top require:

```text
schematic simulation
→ layout
→ DRC
→ extraction
→ LVS
→ PEX simulation
```

LVS PASS proves connectivity, not analog performance. PEX simulations shall repeat the same key
measurements used before layout: sampling error, hold disturbance, ramp slope/linearity, comparator
delay/offset, and integrated conversion code.

### 8.4 Top-level signoff

- Qualified pad/ESD library and reviewed pad ring.
- Analog/digital power domains, substrate strategy, and decoupling review.
- Full-chip DRC, LVS, antenna, density/fill, ERC, and provider checks as applicable.
- Analog macro LEF/GDS integration with the digital block.
- Clean-checkout reproducibility using pinned container and PDK revision.
- Archived reports, tool versions, waivers, and final submission checksum.

## 9. Silicon acceptance tests

The first silicon is a complete-flow success when the following are demonstrated, or when a failure
is isolated conclusively using the required test modes:

1. The packaged die powers safely and analog/digital supply currents are measurable.
2. Reset, control clock, status, and serial communication operate.
3. At least one cell acquires and holds a DC or low-frequency input.
4. The comparator crossing is observable with the external-ramp path.
5. Counter capture returns a code and serial readout preserves its bits.
6. A multi-point transfer curve can be measured.
7. Four stored samples can be associated with the correct cell addresses.
8. Internal-ramp behavior can be compared with the external-ramp reference.
9. Measured results, failures, calibration data, and pre-silicon comparisons are published.

## 10. Explicit non-goals for Tape-out 1

- Multi-GSa/s operation.
- 25 ps timing resolution.
- Validated 500 MHz analog bandwidth.
- Guaranteed 8-, 10-, or 12-bit ADC performance.
- A 32-, 128-, or 512-cell array.
- Multi-channel integration.
- DLL-locked sampling timing.
- Production PMT amplifier/shaper.
- LVDS or high-speed serial I/O.
- Radiation or production reliability qualification.

## 11. Freeze gates

### Gate A: External constraints freeze

- MPW provider/run, submission date, die area, and accepted PDK revision are confirmed.
- Supply options, qualified I/O cells, package/COB option, and pad template are known.
- Provider deliverable and open-source publication requirements are documented.

### Gate B: Schematic freeze

- The frozen 4-cell/6-bit architecture passes `make course-regression`.
- PVT and mismatch plans have pass/fail criteria.
- Top-level interfaces, test modes, clocking, timeout, and packed-word format are reviewed.
- Initial area, power, and pad budgets are credible.

### Gate C: Block layout freeze

- Sampling/MUX, ramp, comparator, bias, and digital blocks are DRC/LVS clean.
- Extracted critical simulations pass or deviations have reviewed waivers.
- Macro abstracts and integration pins are frozen.

### Gate D: Full-chip freeze

- Pad ring, power, analog/digital macros, test structures, fill, and seal-ring constraints are integrated.
- Full-chip signoff passes.
- ASIC pinout, package/bond map, PCB, and FPGA interface agree.

### Gate E: Tape-out release

- Provider checklist and clean-clone build pass.
- Final GDS/OASIS, netlists, reports, waivers, checksums, and Git tag are archived.
- Measurement plan and board bring-up safety limits are approved.

## 12. Open external decisions

The internal architecture is frozen at 4 cells and 6 bits. The remaining decisions are external or
physical-design dependent:

1. Exact MPW provider, run date, slot, and submission deadline.
2. Exact accepted GF180MCU PDK release and metal stack.
3. Qualified core/analog/I/O supply and pad/ESD libraries.
4. Die area, pad count, pad pitch, seal ring, and density/fill requirements.
5. Package, chip-on-board, or wire-bond carrier option.
6. Final capacitor device/type and value after area, leakage, and PEX study.
7. Final comparator variant after PVT/mismatch and post-layout comparison.
8. External/internal ramp voltage range and monitor-pad implementation.
9. Formal sampling and conversion clock limits for silicon testing.
10. Evaluation PCB, FPGA board, connectors, and final I/O protocol voltage levels.

## 13. Change control

This document controls Tape-out 1 scope. A change affecting interfaces, cell count, ADC width,
payload format, pad count, supply domain, device reliability, or any Must requirement requires:

1. Version and date update.
2. Written reason and impact assessment.
3. Update of tests, verification matrix, Handbook, and relevant decision record.
4. Full regression before merge.

Parameter tuning within a block may proceed without an architecture revision only when its interface,
reliability limits, and Must behavior remain unchanged.
