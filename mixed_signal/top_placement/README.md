# Top placement: digital-on-top chip on the wafer.space template

The whole chip as one LibreLane run, the way
[`wafer-space/gf180mcu-project-template`](https://github.com/wafer-space/gf180mcu-project-template)
builds one: the template's pad ring (`chip_top`), a core (`chip_core`)
that holds the digital top as soft logic and the analog cells as hard
macros, and the `Chip` flow that places, routes, seals and fills it.
Why this way and not analog on top: ADR 0009.

```sh
make top-placement STAGE=macros   # analog macro wrappers + their DRC/LVS (minutes)
make top-placement                # macros, then the full chip (slow)
./scripts/sim.sh top-placement    # the same, recorded in runs/top-placement/latest/metrics.json
```

## What is where

```text
chip_top.sv    template pad ring, 0p5x1 slot, pad positions unchanged
 └ chip_core.sv   the wiring: pads <-> digital top <-> analog macros
    ├ asic_digital_top   digital/asic_digital_top, RTL unchanged, soft
    ├ wsa_cmp (u_cmp)    hard macro: CMP, the comparator
    ├ wsa_inv (u_inv)    hard macro: INV, the replica inverter (cicpy)
    └ wsa_inv_gf (u_inv_gf) hard macro: INV_GF, the same inverter drawn in gdsfactory
 + gf180mcu_ws_ip__*  provider ID macros and logo (template, required)
```

| File | |
| --- | --- |
| `macros.py` | wraps each analog GDS into a hard macro: GDS, LEF, liberty, black-box Verilog, SPICE |
| `probe_pins.py` | reads a GDS's port labels and metal; the source of every coordinate in `macros.py` |
| `src/chip_top.sv` | the template's pad ring (defines from LibreLane, SRAM removed) |
| `src/chip_core.sv` | pad map, macros, test-mode select, digital top |
| `librelane/config.yaml` | the template's Chip-flow config, adapted |
| `librelane/slot_0p5x1.yaml` | die, core, pad order (template, plus the pad-library define) |
| `librelane/macros.yaml` | placed macros and their power connections |
| `librelane/pdn_cfg.tcl` | the template's PDN script, SRAM grids removed, sources `analog_routes.tcl` |
| `librelane/analog_routes.tcl` | draws the five pad-to-macro analog wires (see below) |
| `librelane/chip_top.sdc` | conversion clock; comparator and ext_compare are latched data inputs |
| `build.sh` / `container.sh` | the in-container half of the run (`macros`, `chip`, `collect` stages) |
| `check-top.awk` | the acceptance criteria |
| `lvs_summary.py`, `drc_summary.py` | Netgen / KLayout DRC / XOR results as REPORT lines: which nets, rules, where |
| `flow-errors.awk`, `step-errors.awk` | a failed run's LibreLane errors and the stopped step's tagged tool messages, as REPORT lines |
| `probe_nets.py` | a net's router-relevant ODB flags and pin geometry; a pad master's pins |

## Pins on the analog cells

A cicpy cell has its ports as Metal2 labels on small Metal2 pieces in the
middle of its own Metal2. `macros.py` does not touch the cell; it puts it
in a wrapper and adds, per port:

- **signal**: a Via2 array on the port's Metal2 (or, where the cell
  already carries the net on Metal3 -- `INV`'s `A` and `Y` -- nothing),
  a Metal3 pad, and a 0.5 um Metal3 stub to the north or south edge.
  The stub is the LEF pin; the chip router connects there.
- **supply**: a Via2 array on the cell's `vdd`/`vss` Metal2, a Metal3
  pad, a Via3 array, and a 4 um Metal4 strap the full 90 um macro height.
  The chip's Metal5 straps are 75 um apart, so any 85 um window holds a
  VDD and a VSS strap; PDN puts Via4 at the crossings.

Metal1-4 are obstructed over the cell (1 um margin): no chip wiring
crosses the analog devices. Metal5 is left open for the power straps.

| Macro | Cell | Size | Signal pins | Wrapper signoff |
| --- | --- | --- | --- | --- |
| `wsa_cmp` | `CMP` | 109.2 x 90 um | `vin` `vramp` `vbias` (N), `dout` (S) | KLayout DRC clean; LVS open because `CMP` is (ADR 0006) |
| `wsa_inv` | `INV` | 14.0 x 90 um | `A` (N), `Y` (N, by a column west of the cell) | KLayout DRC clean; KLayout LVS matches `INV.spice` |
| `wsa_inv_gf` | `INV_GF` (gdsfactory, Metal1-only ports) | 16.0 x 90 um | `A` (N), `Y` (N), on core nets | KLayout DRC clean; KLayout LVS matches `INV_GF.spice` |

Step-by-step explanation, compared with the template's SRAM macros:
[`how-to-top.md`](how-to-top.md).

Every macro-side coordinate came from `probe_pins.py` on the cell's GDS:

```sh
./container.sh 'python3 probe_pins.py ../analog_layout/physical/final_views/gds/CMP.gds'
./container.sh 'python3 probe_pins.py --shapes ../analog_layout/physical/final_views/gds/INV.gds 42/0 36/0'
```

If a cell is regenerated and a port moves, the wrapper's DRC/LVS in
`STAGE=macros` is where that shows up.

## Analog wiring is drawn, not routed

Every other net on the chip is routed by LibreLane. The five analog
nets, pad `ASIG5V` to macro pin, are drawn by `librelane/analog_routes.tcl`
as fixed special wiring before placement: Metal2 down from the pad
finger under the Metal3 core ring, a Metal3 jog at a height of its own
between the macro tops and the core edge, Metal2 down to the macro edge,
a Via2 onto the pin; a pin that lies under a finger gets one straight
drop. 1.2 um wide, no buffers, no router diodes.

The router could not be used for them: `OpenROAD.PadRing` marks analog
pad nets special (so they come out unrouted), and with the flag cleared
detailed routing aborted inside the flow every time. The measurements
are in ADR 0009 and [`RESULTS.md`](RESULTS.md). The script assumes
analog pads on the north edge and macro pins facing them, and stops
the flow rather than draw anything else.

## Running and reading it

`STAGE=macros` takes minutes; the whole chip about 20 minutes on this
host. The verdict is `runs/top-placement/latest/metrics.json`. On a
failure its `reports` carry LibreLane's error, the stopped step's
tagged messages, and per-rule DRC/XOR locations or per-net LVS
differences, so no log needs opening. `STAGE=collect` re-summarises an
existing `librelane/runs/chip_top` without running LibreLane again.

## Pad map

| Pad | Signal | Pad | Signal |
| --- | --- | --- | --- |
| `clk` | conversion clock, 20 MHz | `rst_n` | reset |
| `input[0]` | `start` | `input[2]` | `test_mode` |
| `input[1]` | `shift_en` | `input[3]` | `ext_compare` |
| `bidir[0]` | `serial_data` | `bidir[8]` | `acquire` |
| `bidir[1]` | `data_ready` | `bidir[9]` | `ramp_connect` |
| `bidir[2]` | `conversion_busy` | `bidir[10]` | `ramp_reset` |
| `bidir[3]` | `conversion_done` | `bidir[11]` | comparator output `dout` |
| `bidir[4..7]` | `conversion_timeout[3..0]` | `bidir[12]` | `crossed[0]` as the capture sees it |
| | | `bidir[13]` | `wsa_inv_gf.Y` |

(Pad map updated 2026-10-01 for the 8-bit parallel digital top of spec 0.6
and 2026-10-09 for its synchronous capture: the comparator output is latched
with the conversion clock in `chip_core` as a stand-in for the latch that
belongs in the analog cell. The run recorded in `RESULTS.md` used the
earlier 6-bit MUX top.)
| `analog[0]` | `wsa_cmp.vin` | `analog[3]` | `wsa_inv.A` |
| `analog[1]` | `wsa_cmp.vramp` (external ramp) | `analog[4]` | `wsa_inv.Y` |
| `analog[2]` | `wsa_cmp.vbias` | `analog[5]` | spare |

`bidir[14]` is `wsa_inv_gf.Y`, the gdsfactory inverter driven by
`compare_high`. `bidir[15..43]` are off (no output, no input, pull-down). `test_mode=1`
makes `ext_compare` the Gray-capture edge instead of the comparator:
the digital path is testable whatever the analog does.

`mux_select`, `ramp_reset` and `bus_reset` go to pads because the blocks
they drive (sampling cells, read mux, ramp) have no layout yet. When they
do, they become macros here and those nets become internal wires.

## What this chip is not (yet)

- **Not the frozen libraries.** `gf180mcu_fd_io` and
  `gf180mcu_fd_sc_mcu7t5v0`, because those are what `/foss/pdks` ships;
  so no separate `AVDD` pair. ADR 0009.
- **Not a working comparator.** `CMP`'s signal nets are unrouted inside
  the cell (ADR 0006); `wsa_cmp` is its placeholder with real pins and
  power.
- **No CDM secondary protection** between the analog pads and the gates.
- **Chip LVS treats the analog macros as black boxes**; it proves the
  wiring to them. The wrapper LVS above is what looks inside.

Current results: [`RESULTS.md`](RESULTS.md).
