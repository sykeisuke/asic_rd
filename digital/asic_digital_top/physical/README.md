# GF180 digital physical design

LibreLane runs the integrated digital top through synthesis, floorplanning,
placement, CTS, routing, extraction, multi-corner STA, stream-out, DRC, and LVS.

```sh
make digital-physical
```

The reproducible configuration uses GF180MCU `gf180mcuD` with the frozen
3.3 V library `gf180mcu_as_sc_mcu7t3v3` (fetched into `.eda-tools/pdk` by
`make pdk`, since the container image ships only the 5 V cells). `final_views/` stores the reviewed GDS, LEF,
DEF, gate-level netlist, render, and metrics from the reference run. Full run
directories are generated locally and excluded from Git.

This block has no pad ring. Pad-ring integration (digital-on-top with the
analog hard macros) is exercised in `experiments/digital_on_top/` and in the
provider-template fork.
