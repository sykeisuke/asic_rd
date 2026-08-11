# Provisional top-level interface

Date: 2026-08-11

This interface freezes logical intent only. Pad cells, pad order, voltage
domains, ESD structures, and package pin numbers remain provider-dependent.

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

| Provisional signal | Purpose |
| --- | --- |
| `analog_in` | Sampling-array input |
| `external_ramp_in` | Mandatory external-ramp bypass |
| `internal_ramp_mon` | Buffered internal-ramp monitor |
| `sample_cell0_mon` | Buffered held-voltage monitor |
| `comparator_test_in_p/n` | Standalone comparator characterization |
| `comparator_out_mon` | Comparator digital monitor |
| `sample_clock_in` | External sampling control or test clock |
| `bias_comp` | Comparator bias test/control |
| `bias_ramp` | Ramp-current bias test/control |

## Power domains

At minimum, separate externally measurable `AVDD/AVSS`, `DVDD/DVSS`, and
`IOVDD/IOVSS` domains are required. Final voltages must follow the selected
GF180 core and I/O libraries. Domain crossings, clamps, and ESD ownership are
not frozen until the MPW provider identifies its qualified pad set.
