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

## Required confirmation

- Exact accepted `gf180mcuD` PDK commit and provider precheck version.
- Qualified I/O/ESD cells, voltage domains, analog-pad limits, and pad models.
- Whether separate analog and digital supply domains are supported by the
  default ring, which is currently documented as `DVDD/DVSS` pads.
- Allowed reassignment of default bidirectional/input pads and exact COB pin map.
- COB board schematic, connector/pinout, current limits, and analog bandwidth.
- GDS top-cell name, seal-ring ownership, density/fill, waiver, and license rules.
