# 0008: gdsfactory cells on the gf180mcu plugin drop the plugin's gate pads

Date: 2026-09-21

Status: accepted (exploration; the cicpy flow of ADR 0006 remains the
analog layout baseline)

## Context

`make tools` installs the `gf180mcu==1.0.0` gdsfactory PDK plugin. Its
`nfet`/`pfet` factories draw the transistor the way the PDK's Magic and
KLayout pcells do, including a contacted M1 pad on the poly pad at both
ends of every finger. A first inverter built from them
(`mixed_signal/analog_layout/misc/`, cell `INV_GF`, the devices of
`spice/INV.spice`) passed KLayout LVS but failed `gf180mcu.drc` with 54
violations: `M1.2a` x40, `M1.3` x6, `M1.1` x8.

The `M1.1` hits were this cell's (a stepped source extension). The other
46 are the plugin's: each pad is 0.115 um beside an S/D column and
0.175 um above its end, 0.209 um corner to corner, and `gf180mcu.drc`
measures `M1.2a` (0.23 um) as a Euclidean distance. Pads a cell leaves
unconnected are 0.34 x 0.23 um, below `M1.3`'s 0.1452 um^2. The plugin
documents itself as matching Magic's geometry; Magic's DRC does not
measure corners. This is the same class of disagreement as `NW.2b_LV` on
the cicpy comparator, and one more reason KLayout owns the verdict.

## Decision

A cell drawn on the plugin uses each transistor **without** the plugin's
gate-contact pads: from a flattened copy, every M1 and contact shape lying
wholly outside the `COMP` is dropped, the poly pads are kept, and the cell
contacts the gate itself on a poly bridge over the finger ends, placed
0.30 um clear of the S/D columns. The plugin is not edited; the cell code
carries the filter (`_without_gate_pads` in
`misc/gfp_misc/cells/inverter.py`).

Coordinates are read back from the plugin's polygons rather than typed
in, so the filter and the routing follow a change of width or finger
count.

## Consequences

- `INV_GF` is `gf180mcu.drc` clean apart from the die-density rules, LVS
  matches `misc/INV_GF.spice` with `--combine`, and every net is M1 and
  poly; no via. Evidence: `./scripts/sim.sh gf-inverter`,
  `runs/gf-inverter/20260921T204828Z/metrics.json`
  (`inv_gf_drc_violations = 0`, `inv_gf_lvs_match = 1`).
- Any other cell built from the plugin's FETs must apply the same filter
  or accept the `M1.2a` failures; the plugin's factories are not usable
  as-is under this project's signoff.
- The folder doubles as a GDSFactory+ 2.0 project (`pyproject.toml`,
  `[tool.gdsfactoryplus]`). The extension's indexer lists the factory
  (`gfp_factories = 1` in the same run); the extension's GUI, venv and
  hosted checks were not exercised and are not part of any verdict.
- This is exploration under specification §12/§13. The cicpy generator
  of ADR 0006 stays the way analog blocks are laid out until a cell here
  is chosen for silicon, which would be its own decision.
