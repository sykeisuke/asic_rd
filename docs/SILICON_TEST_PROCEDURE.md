# Tape-out 1 Silicon Test Procedure

Version: 0.1
Applies to: one-channel, four-cell, 6-bit Wilkinson ASIC

## 1. Purpose and safety

This procedure brings up packaged or wire-bonded Tape-out 1 silicon in stages.
Complete each phase before enabling the next subsystem.

- Use an ESD-controlled bench, grounded instruments, and a wrist strap.
- Power the applicable I/O rail before applying a signal; never drive an unpowered pin.
- Provider pad/PDK voltage limits and power sequencing override this document.
- Use current-limited supplies. Approve initial limits from the design estimate and bare-board measurements.
- Stop immediately for overcurrent, wrong rail voltage, heating, oscillation, or an unstable bond.
- Check that instrument grounds cannot short different board nodes.

## 2. Required preparation

Have the schematic, PCB layout, pinout, bond map, voltage table, current-limited
supplies, DMM, oscilloscope, logic analyzer, DC/low-frequency source, clock
source, FPGA firmware, host software, expected pre-silicon waveforms, and a
measurement log. Record chip/board IDs, Git revisions, instruments, settings,
temperature, and raw-data locations.

## 3. Phase 0: Unpowered inspection

1. Photograph the die, bonds, package, and PCB under magnification.
2. Verify every regulator and clock on the board before installing the ASIC.
3. Measure each supply-to-ground resistance and compare it with the design and bare board.
4. Check for shorts between adjacent pins, supplies, and grounds.
5. Verify connectors, jumpers, series resistors, and test-point population.

**Pass:** no visible fault or unexpected short, and all unloaded rails are in range.

## 4. Phase 1: Staged power-up

1. Hold clocks and inputs at 0 V or high impedance.
2. Enable I/O, digital, and analog rails in the provider-required order with current limits.
3. Record every rail voltage and quiescent current.
4. Repeat after 30 seconds, 2 minutes, and 10 minutes; check temperature and drift.
5. Compare current with reset asserted and released.

**Stop:** current limit reached, current above twice the estimate, rail droop above
5%, local heating, or increasing current. Return to resistance and assembly checks.

## 5. Phase 2: Digital-only test

With the analog input and internal ramp disabled:

1. Verify reset, status, and divided-clock monitor.
2. Start at a low clock and verify the 6-bit counter from 0 through 63.
3. Emulate comparator crossings and capture known codes into all four registers.
4. Verify the 24-bit `{cell3, cell2, cell1, cell0}` payload, bit order, and active edge.
5. Increase the conversion clock in steps to 20 MHz and repeat.

**Pass:** reset, counting, capture, addressing, and serial data match every vector.

## 6. Phase 3: Comparator and external ramp

Apply known DC levels in comparator standalone mode. Sweep a slow external ramp,
measure output crossings, delay, and repeatability, then enable counter capture.
Increasing input voltage must produce a non-decreasing crossing time and code.

## 7. Phase 4: Sampling-cell tests

Track and hold a safe DC input on cell 0, then measure acquisition error, edge
disturbance, and droop through the `VHOLD` monitor. Repeat from 0.4 to 1.6 V for
all four cells and at several hold times. Record per-cell pedestal, gain, and
leakage differences.

**Pass:** at least one cell holds the input, and differences among all cells can
be measured and archived.

## 8. Phase 5: Integrated four-cell conversion

1. Begin with DC or a low-frequency input and drive `SAMPLE[0:3]` at 40 ns spacing.
2. After acquisition, select cells 0 through 3 sequentially through the MUX.
3. Use the external ramp and independent 20 MHz conversion clock to acquire four 6-bit codes.
4. Save `VIN`, accessible `VHOLD`, `MUX_BUS`, `VRAMP`, `COMPARE_OUT`, reset, and serial data.
5. Sweep the input and verify cell order and non-decreasing codes.
6. Repeat with the internal ramp and compare it with the external reference.

**Pass:** four samples are read at the correct addresses with consistent codes,
or test access conclusively isolates a fault to sampling, MUX, ramp, comparator,
counter, or readout.

## 9. Phase 6: ADC, speed, and bandwidth characterization

1. Sweep DC input finely to measure transitions, missing codes, and monotonicity.
2. Calculate DNL/INL only after collecting enough low-noise input points.
3. Reduce the 40 ns sampling interval gradually; define the measured limit where error rises sharply.
4. Raise sine-input frequency and evaluate amplitude loss, phase, and code error.
5. Repeat pedestal, gain, ramp slope, and offset within qualified supply/temperature ranges.
6. Store per-cell pedestal, gain, and time offsets as calibration data.

Tape-out 1 prioritizes demonstrating 6-bit conversion, a 25 MSa/s baseline, and
a 10 MHz measurement target. One first-silicon die cannot guarantee Tape-out 2
or Tape-out 3 performance.

## 10. Measurement record

| Field | Record |
| --- | --- |
| Device | Wafer/lot, die ID, package, board ID |
| Revision | ASIC, PCB, FPGA, and software Git commit/tag |
| Environment | Date, temperature, humidity, instruments, calibration date |
| Supplies | Set/measured voltage, current limit, measured current |
| Clocks | Sampling pulse width/spacing, conversion frequency, amplitude |
| Stimulus | Type, amplitude, offset, frequency |
| Result | Pass/fail, waveforms, raw data, analysis script |
| Deviation | Specification difference, stop condition, suspected cause, next test |

Preserve raw data unchanged. Archive it with analysis, photographs, oscilloscope
settings, and scripts in a directory keyed by device ID.
