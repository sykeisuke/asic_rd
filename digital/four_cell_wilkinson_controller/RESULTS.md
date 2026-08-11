# Four-cell controller results

Date: 2026-08-10

The self-checking RTL simulation uses the four transistor-level conversion
codes (`16, 20, 27, 35`) and verifies:

- one-hot cell selection;
- bus reset and ramp reset sequencing;
- four consecutive counter captures;
- packed 24-bit code storage;
- one-cycle `done` behavior and return to idle.

Icarus Verilog functional simulation passes. The controller and its instantiated
6-bit counter map together to the GF180 `mcu7t5v0` standard-cell library at TT,
25 C, 3.3 V.

| Metric | Result |
| --- | ---: |
| Controller-local cells | 169 |
| Counter cells | 53 |
| Total mapped cells | 222 |
| Controller-local Liberty area | 5749.2288 um^2 |
| Total Liberty area | 7547.0976 um^2 |

These are pre-placement synthesis estimates. Clock distribution, routing,
power grid, physical-only cells, and placement whitespace are excluded.
