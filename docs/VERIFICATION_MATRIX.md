# Prototype verification matrix

Date: 2026-09-18 (architecture 0.6: parallel conversion, bottom-plate sampling, 8 bit)

| Domain | Verification | Status | Reproducible target |
| --- | --- | --- | --- |
| Sampling | Ideal, NMOS-only, and transmission-gate comparison | PASS | `make sampling-cell` |
| Sampling | Four sequential cells (1 pF, v0.5 cell) | PASS (legacy) | `make four-cell` |
| Sampling | Bottom-plate cell, 54.5 fF: sensed-plate rule, pedestal, gain, linearity | PASS | `make bottom-plate-cell` |
| Read mux | Settling and charge sharing | PASS (legacy, MUX removed 2026-09-18) | `make four-cell-mux` |
| Comparator | Nominal transient and range | PASS | `make comparator` |
| Comparator | Static offset separation | PASS | `make comparator-offset` |
| Ramp | Reset, slope, linearity, power | PASS | `make ramp-generator` |
| ADC | Single 6-bit Wilkinson slice (ramp at comparator input) | PASS (legacy) | `make wilkinson-slice` |
| ADC | Eight-point transfer | PASS | `make transfer` |
| Array ADC | Four sequential conversions via MUX | PASS (legacy) | `make four-cell-wilkinson` |
| CDC | Gray comparator-edge capture (single channel reference) | PASS | `make gray-counter` |
| Controller | Parallel 4-cell 8-bit conversion, timeout, last-count capture | PASS | `make parallel-controller` |
| Mixed signal | Four SPICE timings into RTL (sequential controller) | PASS (legacy) | `make four-cell-cosim` |
| CDC | Comparator clock phase sweep (sequential controller) | PASS (legacy) | `make phase-sweep` |
| Readout | Four 8-bit codes through the 32-bit serial output, 20 MHz STA | PASS | `make digital-top` |
| Digital layout | GF180 GDS, DRC, LVS, post-route STA | STALE (6-bit top; rerun with the 8-bit top and 3.3 V library) | `make digital-physical` |
| Analog PVT | Process, voltage, temperature matrix | OPEN | TBD |
| Mismatch | Comparator Monte Carlo | OPEN (design-team result 2026-09-18: sigma 2.75 mV, not yet in repo) | TBD |
| Noise | Comparator transient noise vs kT/C (54.5 fF -> 275 uV) | OPEN | TBD |
| Mixed signal | Parallel controller driven by bottom-plate cell crossing times | OPEN | TBD |
| Analog layout | DRC/LVS/extracted SCA + comparator + ramp | OPEN | TBD |
| Digital layout | Regenerate at 3.3 V (`gf180mcu_as_sc_mcu7t3v3`) | OPEN | `make digital-physical` after retarget |
| Pad ring | `0p5x1` CoB ring with second core pair: platform precheck (pad mask, DRC, antenna) | PASS (density: empty-core artifact) | `run-experiment.sh` in template fork, platform Check #800 |
| Chip top | Analog/digital integration, fill, top DRC/LVS | OPEN | analog layout first |
| Package/PCB | Evaluation board mating the provider COB mezzanine | OPEN | Run 3 COB pinout revision |
| Fabrication | MPW submission and silicon test | BLOCKED | slot purchase (early-bird 2026-09-30) |
