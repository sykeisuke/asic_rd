# Provisional top-level interface

Date: 2026-08-14

This interface freezes logical intent only. Pad cells, pad order, voltage
domains, ESD structures, and package pin numbers remain provider-dependent.

Provider baseline: wafer.space GF180MCU Run 3. The provisional physical target
is the `0.5x1` default pad ring with COB packaging: 56 signal I/Os, including
six documented analog pads, plus 16 power pads. See
[`decisions/0004-wafer-space-run3.md`](decisions/0004-wafer-space-run3.md).

## Digital control and readout

| Signal | Direction | Purpose |
| --- | --- | --- |
| `clk` | input | 10-20 MHz nominal conversion/readout clock |
| `rst_n` | input | Active-low global digital reset |
| `start` | input | Start four-cell conversion sequence |
| `compare_high` | analog-to-digital | Comparator state; falling edge captures Gray count |
| `shift_en` | input | Shift one result bit on rising `clk` |
| `serial_data` | output | LSB-first 24-bit result stream |
| `data_ready` | output | Result word loaded and available |
| `conversion_busy` | output | Four-cell sequence in progress |
| `conversion_done` | output | One-cycle completion pulse |
| `mux_select[3:0]` | digital-to-analog | One-hot analog storage-cell selection |
| `ramp_reset` | digital-to-analog | Active-high ramp reset |
| `bus_reset` | digital-to-analog | Active-high comparator-input bus reset |
| `active_cell[1:0]` | output/test | Current conversion cell index |

The routed digital macro exposes 19 scalar signal pins corresponding to this
table. Internal analog-control outputs will normally connect to the analog
macro rather than external pads; test multiplexing is still required.

## Required analog and test pads

The default half-width ring provides six true analog pads. The logical
interface must therefore be reduced to the following physical-pad budget.

| Priority | Physical pad candidate | Functions |
| --- | --- | --- |
| Must | `analog_in` | Sampling-array input |
| Must | `external_ramp_in` | External-ramp bypass |
| Debug | `analog_mon_0` | Buffered `VHOLD[0]` or MUX-selected held voltage |
| Debug | `analog_mon_1` | Buffered internal ramp or MUX bus |
| Debug | `comparator_test_p` | Comparator positive test input |
| Debug | `analog_test_mux` | Comparator negative test input or selected bias control/monitor |

`comparator_out_mon` is a digital output. `sample_clock_in` is a digital input.
Comparator and ramp bias functions shall share `analog_test_mux` or use
internally generated settings unless provider review makes more analog pads
available. The test-MUX truth table must be frozen before pad-ring integration.

## Power domains

Separate externally measurable analog and digital currents remain a design
requirement. The published default ring describes 8 `DVDD` and 8 `DVSS` pads,
so wafer.space must confirm whether and how those pads may be partitioned into
`AVDD/AVSS`, `DVDD/DVSS`, and any I/O supply domain. Final voltages, crossings,
clamps, and ESD ownership remain open until that answer and the qualified pad
set are received.
