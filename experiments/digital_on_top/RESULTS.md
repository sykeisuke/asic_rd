# Digital-on-top experiment results

Date: 2026-09-25. LibreLane (IIC-OSIC-TOOLS 2026.07 container), `gf180mcuD`,
standard cells **`gf180mcu_as_sc_mcu7t3v3` (the frozen 3.3 V library, fetched
by `make pdk`)**; first passed with the 5 V library earlier the same day with
identical signoff results. One analog hard macro (`comparator_min`, 11.31 x
52.24 um) placed at (200, 60) in a 300 x 300 um die.

| Metric | Result |
| --- | ---: |
| Instances (std cells, fill, macro) | 4194 |
| Detailed-routing DRC | 0 |
| Magic DRC / KLayout DRC (full decks) | 0 / 0 |
| Netgen LVS (macro via its SPICE view) | 0 errors, 0 device differences |
| Setup / hold violations, 9 corner-RC combinations | 0 / 0 (worst slack 42.9 ns / 0.32 ns) |
| Antenna violating nets / pins | 0 / 0 |
| Macro power connectivity (PSM check) | all VDD/VSS shapes connected |

Rendered layout: [`final_views/mixed_top.png`](final_views/mixed_top.png)
(the macro is the white-halo block at lower right; the router used Metal4/5
over it and reached its Metal3 pins from the top edge). Full metrics:
[`final_views/metrics.csv`](final_views/metrics.csv).

## What it took (each of these cost one failed run)

1. **Lint:** Verilator rejects a register array written from several
   generate blocks with different clocks (`MULTIDRIVEN`); each capture
   channel now owns its flops (commit 2d4fbf7). Yosys had accepted it.
2. **Power ports of the top module must be named after `VDD_NETS`/`GND_NETS`**
   (`VDD`/`VSS`): `Odb.SetPowerConnections` reads the macro's power
   connections from the RTL (`cmp0.vdd -> VDD`) and looks that net up in the
   database; a lowercase `vdd` port does not exist there.
3. **Macro PDN straps need `-pitch` even with `-number_of_straps 1`**, and
   `-offset` is the strap *centreline* measured from the macro edge, not the
   strap's left edge. Misaligned by half a strap width, pdngen inserted no
   Via3 and the IR-drop step reported the macro unconnected.
4. **The macro GDS needs a PR boundary** (Magic `PRBOUND` 63/0; KLayout
   `PR_bndry` 0/0) or `Magic.StreamOut` cannot size it. Magic's `lef write`
   then also uses it as the abutment box.
5. **Exactly one top cell** in the macro GDS: gdsfactory adds a
   `$$$CONTEXT_INFO$$$` cell; KLayout steps refuse layouts with two top
   cells. Pruned in `add_pr_boundary.py`.
6. **`PRIMARY_GDSII_STREAMOUT_TOOL: klayout`** (as in the template): Magic's
   stream-out drags a `PK_$$$CONTEXT_INFO$$$` top cell out of the PDK
   standard-cell GDS, which again breaks the KLayout render/DRC steps.
7. **LEF `ORIGIN` must be (0, 0).** With Magic's default LEF the origin was
   (1.54, 51.64); OpenROAD placed the abstract correctly but the GDS merge
   dropped the cell geometry 52 um lower, on top of the standard cells:
   ~1000 KLayout + ~900 Magic DRC errors and 11 LVS errors, all vanishing
   once the macro GDS was translated so its bounding box starts at (0, 0).

## Rules for our analog macros (derived)

- Generator output -> `add_pr_boundary.py` (prune to one cell, translate to
  origin, add boundary on 0/0 and 63/0) -> Magic `port makeall` +
  `lef write -hide` -> post-process directions/uses -> pins-only `.lib`,
  blackbox `.v`, LVS `.spice`. This is `make_macro.sh`.
- Power pins as vertical Metal3 bars reaching the macro edge; connect them
  with a macro PDN grid of Metal4 straps centred on the bar centres (record
  the centres in the PDN script when the generator changes).
- Signal pins on Metal3 at the boundary are enough; no routing blockage
  above the macro is required (Metal4/5 are free in these cells), which is
  exactly the digital-on-top benefit: the router owns the analog
  connections.
- Top-level power ports `VDD`/`VSS`; macros instantiated with
  `USE_POWER_PINS` power connections; `PDN_MACRO_CONNECTIONS` in addition
  is harmless.

## Chip level: pad ring + 3.3 V library (provider-template fork)

The same recipe inside the wafer.space template (fork branch
`digital-on-top-chip-core`, notes in its `CHIP_EXPERIMENT.md`): `chip_core`
= this digital top + the comparator macro, `0p5x1` ring with the second core
supply pair, `gf180mcu_as_sc_mcu7t3v3`, `gf180mcu_ocd_io`. Run `chip_bia5`:

| Check | Result |
| --- | --- |
| Routing / Magic / KLayout DRC, density | 0 / 0 / 0 / 0 |
| Antenna | 0 |
| Netgen LVS | 0, with the three analog pad-to-macro nets routed |
| Setup / hold, 9 corners (25 MHz pad clock) | 0 / 0 |
| Instances | 180184 (33599 std cells incl. fill, 7 % utilization) |
| wafer.space `gf180mcu-precheck --cob` | slot size and COB pad mask match; density, antenna, Magic DRC, KLayout DRC clear |

Render: [`final_views/chip_top.png`](final_views/chip_top.png).

Additional findings at chip level (details in the fork's notes):

8. **The template's analog pads (`asig_5p0`) are not routable by the
   digital router**: their only pin is the bond pad (2.54 um Metal2 fingers
   inside obstructions), TritonRoute finds no access points and crashes if
   asked. The template leaves those nets SPECIAL and unrouted, and **LVS
   still passes with the macro inputs floating** (the netlist has the same
   nets). Always check the routed DEF for the analog nets.
9. The bidirectional-with-analog pad `bi_a` routes normally through its
   core-side `ANA` pin, but its Liberty lacks that pin: Yosys needs a Verilog
   model, OpenROAD's linker needs a patched Liberty (otherwise it silently
   drops the connection), and the pad-ring terminal list needs the master.
10. Python-API flows need the LibreLane-matched OpenROAD build in PATH; the
    KLayout DRC worker count must fit the Docker VM memory on a full die.

Design question raised for the analog owner: `asig_5p0` (diodes only,
needs a hand-made wide-metal connection or a special-wire step) versus
`bi_a` (router-friendly, but a pass device in the signal path). The spec
currently assumes `asig`.

## Limits of this experiment

- No pad ring (the template's `chip_top` wraps this step; see the
  template-fork branch `digital-on-top-chip-core` for the same recipe inside
  `chip_core` with the 0p5x1 ring); one small macro. Next: the real
  bottom-plate cell / comparator macros as they become available.
- The comparator itself is the v0.5 `cmp_min` (ramp at the input); it is a
  placeholder for the integration recipe, not the 0.6 comparator.
