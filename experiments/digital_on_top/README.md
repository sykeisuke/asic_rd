# Digital-on-top integration experiment (LibreLane + analog hard macro)

Goal: understand and reproduce the way the wafer.space template integrates
foundry macros (its SRAM example) so that our own analog blocks can be
dropped into the digital P&R flow as hard macros, and prove it with a simple
analog cell. Design-review recommendation of 2026-09-18: digital-on-top (the
P&R tool routes to the analog blocks; iterations are fast once the flow runs).

## What the template does for its SRAM (macros_3v3.yaml)

A macro is a `MACROS:` entry in the LibreLane config with these views:

| Key | View | Who consumes it |
| --- | --- | --- |
| `gds` | full layout | KLayout/Magic stream-out, DRC, LVS extraction |
| `lef` | abstract: size, pin shapes, obstructions | OpenROAD floorplan, placement, routing |
| `vh` | Verilog blackbox | Yosys (so the instance survives synthesis) |
| `lib` | Liberty (timing or pins-only) | OpenSTA linking / timing |
| `spice` (or `nl`) | transistor netlist | Netgen LVS |
| `instances` | fixed `location` / `orientation` per instance | floorplan (macro placement) |

plus `PDN_MACRO_CONNECTIONS` ("inst VDD VSS pin_vdd pin_vss") and a macro
grid in the PDN script (`pdn/pdn_3v3_sram.tcl`) that lays Metal4 straps over
the macro's Metal3 power bars and connects Metal4-Metal3. Foundry-cell DRC
false positives are handled with `MAGIC_GDS_FLATGLOB`.

## What this experiment adds

`make_macro.sh` turns the gdsfactory minimum comparator
(`experiments/analog_layout/comparator.py min`, DRC/LVS clean, 11.3 x 52.2 um)
into the same set of views:

- GDS: the generator's output.
- LEF: Magic `port makeall` + `lef write -hide` (pins from the M3 pin labels,
  everything else as obstructions), then `make_macro_views.py` adds
  `DIRECTION`/`USE` and drops the well layers from `OBS`.
- lib: pins-only Liberty stub with `pg_pin`s (no timing; the comparator
  output is a clock source in the SDC, so no arcs are needed).
- Verilog blackbox with power pins under `USE_POWER_PINS`.
- SPICE: the LVS reference subcircuit.

`mixed_top.v` instantiates the 8-bit parallel `asic_digital_top` and one
`comparator_min` (its output drives `compare_high[0]`; cells 1..3 keep
external comparator inputs). `config.yaml` places the macro at (200, 60) in a
300 x 300 um die; `pdn_cfg.tcl` is LibreLane's default PDN plus a macro grid
with two 0.44 um Metal4 straps centred on the macro's vdd/vss Metal3 bars.

```sh
experiments/digital_on_top/make_macro.sh   # build macro/ views (container)
experiments/digital_on_top/run.sh          # LibreLane RTL-to-GDS of mixed_top
```

Results: see [`RESULTS.md`](RESULTS.md).
