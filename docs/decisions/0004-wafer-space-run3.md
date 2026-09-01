# Decision 0004: wafer.space GF180MCU Run 3

Status: accepted

Date: 2026-08-14

## Decision

Use wafer.space as the MPW provider for Tape-out 1 and target its GF180MCU Run 3.
The provider currently publishes these milestones:

| Milestone | Published date |
| --- | --- |
| Early-bird deadline | 2026-09-30, 11:59 PM AoE |
| Purchase deadline | 2026-12-09, 11:59 PM AoE |
| Clean-GDS submission deadline | 2026-12-16, 11:59 PM AoE |
| Parts shipped | Q2 2027 |

Dates must be reconfirmed with wafer.space before purchase. Source:
[wafer.space Run 3 page](https://wafer.space/), accessed 2026-08-14.

## Provisional slot and packaging choice

Use `0.5x1` half-width with the default pad ring and chip-on-board (COB) add-on
as the planning baseline. This is not frozen until analog area and pad mapping
pass review.

Published default-ring resources are:

| Resource | `0.5x1` baseline |
| --- | --- |
| Die size | 1.94 mm x 5.12 mm |
| Core area | 1.05 mm x 4.24 mm = 4.46 mm2 |
| Signal I/O | 56 total: 44 bidirectional, 6 input, 6 analog |
| Power pads | 16: 8 DVDD and 8 DVSS |
| Process features | Five metal layers, MIM/MOS capacitors, poly/high-res resistors |

The COB option requires the default pad ring. Source:
[wafer.space slot documentation](https://mithro.github.io/gf180mcu-project-template/).

## Reasoning

Tape-out 1 requires several true analog pads for `VIN`, external-ramp injection,
and internal-node monitoring. Among the published default rings, the half-width
slot provides six analog pads and 4.46 mm2 of core area. The current provisional
analog interface exceeds six signals, so monitor and bias functions must be
multiplexed or reduced before schematic freeze.

## Technology baseline frozen after template review

- Provider template commit: `0de7e394337a1f7f5303ac7a3681bf2481b58176`.
- PDK/Ciel commit: `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7`.
- Process: `gf180mcuD`.
- Analog, digital-core, and I/O nominal voltage: 3.3 V.
- Digital cells: `gf180mcu_as_sc_mcu7t3v3`.
- Pad library: `gf180mcu_ocd_io`.

These are the design baseline. Run 3 acceptance, ESD performance, and physical
power-domain implementation still require written provider confirmation; see
[`../PDK_PAD_SUPPLY_FREEZE.md`](../PDK_PAD_SUPPLY_FREEZE.md).

## Required confirmation

- Exact accepted `gf180mcuD` PDK commit and provider precheck version.
- Qualified I/O/ESD cells, voltage domains, analog-pad limits, and pad models.
- Whether separate analog and digital supply domains are supported by the
  default ring, which is currently documented as `DVDD/DVSS` pads.
- Allowed reassignment of default bidirectional/input pads and exact COB pin map.
- COB board schematic, connector/pinout, current limits, and analog bandwidth.
- GDS top-cell name, seal-ring ownership, density/fill, waiver, and license rules.

## Update 2026-08-31: how the confirmations were resolved

wafer.space (Tim Ansell, 2026-08-30) stated that it issues no written
confirmations and provides no design support: it performs DRC checking only,
gives no IP or cross-compatibility guarantees, and grants COB packaging to any
design passing the CoB checks on platform.wafer.space. The "Required
confirmation" list above was therefore closed by public-repository evidence,
conservative design rules, and an empirical padring experiment; the record is
in [`../PDK_PAD_SUPPLY_FREEZE.md`](../PDK_PAD_SUPPLY_FREEZE.md). Key outcomes:

- PDK/template commits match the public template `main` pin (re-verify at
  purchase and before submission).
- The `0.5x1` default ring with `bidir[43:42]` re-typed into a second core
  `vdd/vss` pair passed the platform CoB precheck (Check #800, precheck
  1.7.3); the slot and packaging choice is now frozen, not provisional.
- All grounds are common on the default COB breakout; only `AVDD` is
  separately measurable.
- Analog-pad ESD is handled by GF180MCU DRM design rules, not provider data.
- The top cell is `chip_top`; precheck enforces origin, DBU, slot size,
  density, antenna, and DRC. Density is a hard failure, so fill is required.
- License: Apache-2.0 adopted for this repository (full open publication).
