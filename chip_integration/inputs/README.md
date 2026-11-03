# inputs/ — the three things the chip is built from

The flow reads **only** this folder (plus the PDK and the frozen
libraries in the container). Each sub-folder is a plain copy of one input,
so the chip can be rebuilt without anything else in the repository.
`MANIFEST.sha256` lists every file. `scripts/run.sh` checks the folder
against it before each run (`inputs_manifest_ok = 1`).
`scripts/fetch_inputs.sh` is the one script that refreshes the copies.

| Sub-folder | What | Copied from | Made by |
| --- | --- | --- | --- |
| `digital/` | hardened digital top `asic_digital_top`: GDS, LEF, gate netlist, its SDC, its own metrics and render | `digital/asic_digital_top/physical/final_views/` (+ `physical/physical.sdc`) | `make digital-physical` (LibreLane RTL-to-GDS, `gf180mcu_as_sc_mcu7t3v3`; record `runs/digital-physical/20261023T095022Z`: DRC 0, LVS 0, setup/hold 0) |
| `analog/` | analog top `wsa_analog_top`: GDS + pin contract (`*.pins.csv`: name, direction, use, status) | `mixed_signal/top_placement/work/macros/wsa_analog_top/` | `mixed_signal/top_placement/analog_macro.py` |
| `template/` | wafer.space template files: 1x0p5 slot (die, core, pad order), the template's Chip-flow config, PDN script, SDC, render layer colours, top-level Verilog, and the five provider ID cells (`ip/`: QR code, shuttle ID, project ID, marker, logo) | `github.com/wafer-space/gf180mcu-project-template` at `0de7e394337a1f7f5303ac7a3681bf2481b58176` (`COMMIT`; the pin is `config/wafer_space_run3.mk`) | wafer.space (Apache-2.0, `template/LICENSE`) |

## The analog GDS is a placeholder

No `Analog_top` block has layout yet. `wsa_analog_top.gds` comes from the
generator that `mixed_signal/top_placement` uses. It draws only these:

- the outline (PR boundary on 0/0);
- the 30 pins of the interface contract;
- the AVDD/AVSS rings and the bus channel;
- the ten MIM capacitors that meet the MIM rules.

It has **no transistors and no resistors**. Everything this flow proves
about the analog macro (KLayout DRC 0, chip LVS) proves the integration,
not the analog design. When real analog layout exists, replace it:

```sh
ANALOG_GDS=/path/analog_top.gds ANALOG_PINS=/path/analog_top.pins.csv \
    chip_integration/scripts/fetch_inputs.sh
```

The replacement must keep these:

- top cell `wsa_analog_top`;
- a PR boundary on GDS 0/0 starting at the origin;
- every pin as a shape on `<metal>/10` with a text label on top of it;
- the same pin names and edges: `librelane/analog_routes.tcl` and
  `librelane/power_routes.tcl` look the pins up by name.

The contract CSV gives what a GDS cannot carry: each pin's direction and
use, and the port order.

## The template files

`template/` keeps the provider's originals untouched, for reference and
diff. The flow's adapted copies live in `../librelane/` and `../src/`:

| Template original | Adapted copy | What changed |
| --- | --- | --- |
| `librelane/slots/slot_1x0p5.yaml` | `librelane/slot_1x0p5.yaml` | only the re-typed instances renamed (`bidir[45]` → `avdd_pad`, `bidir[44]` → `avss_pad`, `analog[3]` → `analog3_pad`) |
| `librelane/config.yaml` | `librelane/config.yaml` | the 3.3 V library set, the two hard macros, obstructions for the drawn wires, `PAD_CFG`, bi_a pad terminals |
| `librelane/pdn/pdn_cfg.tcl` | `librelane/pdn_cfg.tcl` | SRAM grids removed, macro grid on the digital top only, the two drawn-wiring hooks |
| `librelane/macros/macros_3v3.yaml` | `librelane/macros.yaml` | the ID cells at the same locations, plus the two hard macros |
| `librelane/chip_top.sdc` | `librelane/chip_top.sdc` | 20 MHz clock, asynchronous capture clocks |
| `src/chip_top.sv`, `chip_core.sv`, `slot_defines.svh` | `src/` | the pad map of this chip and the glue to the two macros |
| (LibreLane's own pad ring script) | `librelane/pad_cfg.tcl` | AVDD rail-break cells on both sides of `avdd_pad` |
