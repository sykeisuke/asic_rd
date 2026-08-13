# Prototype verification matrix

Date: 2026-08-13

| Domain | Verification | Status | Reproducible target |
| --- | --- | --- | --- |
| Sampling | Ideal, NMOS-only, and transmission-gate comparison | PASS | `make sampling-cell` |
| Sampling | Four sequential cells | PASS | `make four-cell` |
| Read mux | Settling and charge sharing | PASS | `make four-cell-mux` |
| Comparator | Nominal transient and range | PASS | `make comparator` |
| Comparator | Static offset separation | PASS | `make comparator-offset` |
| Ramp | Reset, slope, linearity, power | PASS | `make ramp-generator` |
| ADC | Single 6-bit Wilkinson slice | PASS | `make wilkinson-slice` |
| ADC | Eight-point transfer | PASS | `make transfer` |
| Array ADC | Four sequential conversions | PASS | `make four-cell-wilkinson` |
| CDC | Gray comparator-edge capture | PASS | `make gray-counter` |
| Mixed signal | Four SPICE timings into RTL | PASS | `make four-cell-cosim` |
| CDC | Comparator clock phase sweep | PASS | `make phase-sweep` |
| Readout | Four codes through serial output | PASS | `make digital-top` |
| Digital layout | GF180 GDS, DRC, LVS, post-route STA | PASS | `make digital-physical` |
| Analog PVT | Process, voltage, temperature matrix | OPEN | TBD |
| Mismatch | Comparator Monte Carlo | OPEN | TBD |
| Analog layout | DRC/LVS/extracted SCA + comparator + ramp | OPEN | TBD |
| Chip top | Analog/digital integration and pad ring | BLOCKED | MPW constraints |
| Package/PCB | Package and evaluation board | BLOCKED | provider package |
| Fabrication | MPW submission and silicon test | BLOCKED | provider schedule |
