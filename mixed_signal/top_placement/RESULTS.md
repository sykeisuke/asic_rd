# Top placement: results

Run: `./scripts/sim.sh top-placement`, 2026-09-24 (HST),
`runs/top-placement/20260925T050420Z/metrics.json` — `pass: true`, exit 0.
Three analog macros: `wsa_cmp` (CMP), `wsa_inv` (cicpy INV), `wsa_inv_gf`
(gdsfactory INV_GF, on core nets: `A` = `compare_high`, `Y` → `bidir[14]`).
The previous passing run, with CMP and INV only, was
`runs/top-placement/20260925T022743Z/metrics.json`.
LibreLane v3.1.0.dev2 in the pinned IIC-OSIC-TOOLS image, `gf180mcuD` at
the pinned Ciel commit, `gf180mcu_fd_sc_mcu7t5v0` + `gf180mcu_fd_io`,
slot `0p5x1`, template `0de7e394`.

## Acceptance (`check-top.awk`)

| Criterion | Result |
| --- | --- |
| `wsa_cmp` wrapper, KLayout `gf180mcu.drc` (density apart) | 0 |
| `wsa_inv` wrapper, KLayout `gf180mcu.drc` (density apart) | 0 |
| `wsa_inv` wrapper, KLayout LVS vs `INV.spice` | match |
| `wsa_inv_gf` wrapper, KLayout `gf180mcu.drc` (density apart) | 0 |
| `wsa_inv_gf` wrapper, KLayout LVS vs `INV_GF.spice` | match |
| All three wrappers: PR boundary readable by `Magic.StreamOut` | 4/4 fields |
| LibreLane Chip flow exit / deferred errors | 0 / 0 |
| Chip GDS written | 96.6 MB |
| Detailed routing DRC | 0 |
| Critical disconnected pins | 0 |
| Setup / hold violations, all corners | 0 / 0 |
| KLayout `gf180mcu.drc`, full chip | 0 |
| Netgen LVS, full chip | 0 errors (0 device, 0 net, 0 pin differences) |
| Magic/KLayout stream-out XOR | 0 |
| KLayout antenna | 0 |
| KLayout density, after fill | 0 |

Figures from the same record: worst setup slack 19.16 ns and worst hold
slack 0.31 ns (50 ns conversion clock), 94 070 instances (mostly tap,
endcap, fill and pad spacers), 98.0 mm routed wire, die 1936 × 5122 um.

Reported, not judged: `wsa_cmp` LVS does not match `CMP.spice`, because
the `CMP` cell inside it is LVS-open (ADR 0006); cell-level density on
the wrappers (8, 7 and 7 rules), which chip-level fill resolves.

## What the passing run proves, and what it does not

- The pad ring, the unchanged digital top, and two analog hard macros
  build into one GDS that is DRC-, LVS-, antenna- and density-clean under
  the PDK's KLayout decks, and timing-clean at 20 MHz.
- Chip LVS sees the analog macros as black boxes. It proves every
  macro pin reaches the right pad or core net; the inside of `wsa_inv`
  is covered by its own wrapper LVS, the inside of `wsa_cmp` is not.
- It is not the frozen library set (ADR 0009): `fd_io` and the 5 V
  standard cells, one supply domain, no separate `AVDD`.
- It is not a working comparator (ADR 0006), and there is no CDM
  secondary protection on the analog inputs.
- No PEX or post-layout simulation. Magic DRC was not run (KLayout is
  signoff); the provider's own precheck was not run on this GDS.

## How it got here (runs of 2026-09-24)

| Run | Outcome | Cause | Change |
| --- | --- | --- | --- |
| 1 | stopped in `Magic.StreamOut` | macro GDS had no PR boundary (0/0) | `macros.py` draws one; macro stage checks it with LibreLane's `get_bbox.tcl` |
| 2 | complete; LVS 40 errors | analog pad nets special after `PadRing`, left unrouted | tried clearing the flag |
| 3–5 | aborted in detailed routing | `frAccessPoint` index out of range, in the flow only | wires drawn instead (`librelane/analog_routes.tcl`) |
| 6 | complete; DRC 8, XOR 4 | two jog Via2 arrays 0.4 um apart on `analog_PAD[3]` | straight drop when the pin is under a finger |
| 7 | **pass** (CMP, INV) | | |
| 8 | **pass** (CMP, INV, INV_GF) | | INV_GF added: Metal1 landing in `macros.py`, core-net pins |

The detailed-routing abort never reproduced outside the flow: the same
step re-run with `python3 -m librelane.steps run` from its saved config
and state routed all five analog nets with 0 DRC errors, four times.
Its cause is not known. The drawn wires do not depend on it.

## Artifacts

- `physical/final_views/render/chip_top.png` — KLayout render of the final GDS
- `physical/final_views/metrics.csv`, `metrics.json` — LibreLane's final metrics
- GDS: `librelane/runs/chip_top/final/gds/chip_top.gds` (96 MB, build output, not committed)
