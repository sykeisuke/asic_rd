# Counter synthesis results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, Icarus Verilog, Yosys 0.67,
GF180MCU `gf180mcuD`.

## Functional verification

The self-checking RTL simulation passes:

- code 32 capture matching the integrated analog-slice timing;
- zero-length conversion capture;
- one-cycle `valid` pulse;
- saturation at code 63 with `overflow` when no crossing occurs.

## GF180 technology mapping

Library: `gf180mcu_fd_sc_mcu7t5v0`, TT, 25 C, 3.3 V.

| Metric | Result |
| --- | ---: |
| Mapped cells | 53 |
| D flip-flops | 15 |
| Liberty cell area | 1797.8688 um^2 |
| Sequential area fraction | 62.27% |
| Yosys structural problems | 0 |

The mapped netlist is generated under `work/` and is intentionally not tracked.
Physical area after placement will be larger because this figure excludes
routing, whitespace, tap/end-cap requirements, and power distribution.
