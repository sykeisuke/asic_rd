# Prototype verification matrix

Date: 2026-10-08 (architecture 0.6: parallel conversion, bottom-plate sampling, 8 bit)

| Domain | Verification | Status | Reproducible target |
| --- | --- | --- | --- |
| Sampling | Ideal, NMOS-only, and transmission-gate comparison | PASS | `make sampling-cell` |
| Sampling | Four sequential cells (1 pF, v0.5 cell) | PASS (legacy) | `make four-cell` |
| Sampling | Bottom-plate cell, 54.5 fF: sensed-plate rule, pedestal, gain, linearity (method study) | PASS (the exploration branch `keisuke/analog-explore`; the design team owns the cell) | branch-only |
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
| Digital layout | GF180 GDS, DRC, LVS, post-route STA (8-bit top, 3.3 V `gf180mcu_as_sc_mcu7t3v3`) | PASS | `make digital-physical` |
| Analog PVT | Process, voltage, temperature matrix | OPEN | TBD |
| Mismatch | Comparator Monte Carlo | OPEN (design-team result 2026-09-18: sigma 2.75 mV, not yet in repo) | TBD |
| Noise | Comparator transient noise vs kT/C (54.5 fF -> 275 uV) | OPEN | TBD |
| Mixed signal | Parallel controller driven by bottom-plate cell crossing times | OPEN | TBD |
| Analog layout | DRC/LVS/extracted SCA + comparator + ramp | OPEN | TBD |
| Pad ring | `0p5x1` CoB ring with second core pair: platform precheck (pad mask, DRC, antenna) | PASS (density: empty-core artifact) | `run-experiment.sh` in template fork, platform Check #800 |
| Integration | Digital-on-top rehearsal with one generator-made analog hard macro, 3.3 V (no pad ring) | PASS (exploration branch `keisuke/analog-explore`, `experiments/digital_on_top`) | branch-only |
| Chip top | Design-team flow from a clean checkout of `main`: pad ring + 8-bit digital top + three analog hard macros regenerated from their generators (`CMP`, `INV` by cicpy, `INV_GF` by gdsfactory), hand-drawn analog pad wires, 5 V cells / `fd_io`: macro DRC 0, `INV`/`INV_GF` macro LVS match (`CMP` LVS-open, ADR 0006); routing DRC 0, setup/hold 0 violations all corners, KLayout `gf180mcu.drc` 0, Netgen LVS 0, XOR 0, antenna 0, density after fill 0; max slew/cap/fanout 237/103/8 reported, not judged | PASS (5 V cells / `fd_io`, not the frozen libraries) | `make tools layout gf-inverter top-placement` (`runs/top-placement/20261008T194016Z`) |
| Chip top | Pad ring + 8-bit digital top + one analog hard macro, 3.3 V / `ocd_io`, `bi_a` analog pads, provider precheck incl. COB pad mask clear | PASS (template fork branch `digital-on-top-chip-core`; placeholder comparator) | fork `run-chip.sh` |
| Chip top | Real analog macros (bottom-plate cells, 0.6 comparators, ramp), fill, top DRC/LVS | OPEN | analog layout first |
| Package/PCB | Evaluation board mating the provider COB mezzanine | OPEN | Run 3 COB pinout revision |
| Pad ring | `1x0p5` ring with second core pair (`bidir[45:44]`) + 8-bit top + macro: DRC/LVS/antenna/density/timing clean | PASS incl. provider precheck with COB pad mask (fork branch `slot-1x0p5`) | fork `SLOT=1x0p5 ./run-chip.sh` |
| Fabrication | MPW submission and silicon test | BLOCKED | `1x0.5` slot purchase (deadline 2026-12-09) |
