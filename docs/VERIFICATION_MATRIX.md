# Prototype verification matrix

Date: 2026-08-31

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
| Digital layout | Regenerate at 3.3 V (`gf180mcu_as_sc_mcu7t3v3`) | OPEN | `make digital-physical` after retarget |
| Pad ring | `0p5x1` CoB ring with second core pair: platform precheck (pad mask, DRC, antenna) | PASS (density: empty-core artifact) | `run-experiment.sh` in template fork, platform Check #800 |
| Chip top | Analog/digital integration, fill, top DRC/LVS | OPEN | analog layout first |
| Package/PCB | Evaluation board mating the provider COB mezzanine | OPEN | Run 3 COB pinout revision |
| Fabrication | MPW submission and silicon test | BLOCKED | slot purchase (early-bird 2026-09-30) |
