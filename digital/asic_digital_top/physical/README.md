# GF180 digital physical design

LibreLane runs the integrated digital top through synthesis, floorplanning,
placement, CTS, routing, extraction, multi-corner STA, stream-out, DRC, and LVS.

```sh
make digital-physical
```

The reproducible configuration uses GF180MCU `gf180mcuD` with the
`gf180mcu_fd_sc_mcu7t5v0` library. `final_views/` stores the reviewed GDS, LEF,
DEF, gate-level netlist, render, and metrics from the reference run. Full run
directories are generated locally and excluded from Git.

This block has no pad ring and uses the 5 V standard-cell timing views supplied
by the selected library. Final supply/library choice must match the MPW
provider's qualified PDK and I/O policy.
