# ADR 0006: cicpy for schematic-driven analog layout, with a gf180mcuD primitive provider written here

Date: 2026-09-11

Status: Proposed

Does not supersede any earlier record. Opens the analog-layout row of
`docs/VERIFICATION_MATRIX.md`, which had no reproducible target at all.

## Context

Specification §8.3 requires every analog block in silicon to reach
DRC/LVS-clean layout and extracted verification, and Gate C (§11) will not
close without it. Nothing in the repository drew analog layout: the only
physical flow was `digital-physical`, which is LibreLane over standard
cells, and the matrix row "Analog layout / DRC/LVS/extracted SCA +
comparator + ramp" read OPEN with no target.

The layout constraint in `CLAUDE.md` is that GDS is opaque here — what
works is scripted generation kept in git, with the binary treated as build
output. That rules out drawing cells in Magic's GUI, which is invisible to
this workflow and drifts silently.

[cicpy](https://analogicus.com/cicpy/) is the Python port of ciccreator:
`cicpy spi2mag` takes a SPICE subcircuit, a technology rules file and a
library of primitive Magic cells, and writes placed and routed `.mag` and
`.cic`. The intent lives in a Python sidecar beside the design, which is
text, in git, and reviewable.

## Decision

cicpy 0.3.1, pinned in `.eda-tools` by `make tools` alongside the existing
gf180mcu gdsfactory plugin, is the analog layout generator. **KLayout, not
Magic, is the signoff tool.** Generation and signoff are separate targets,
because they answer different questions and one of them takes a netlist:

```sh
make layout [CELL=X]                    generate: GDS, render, SVG
make drc    [CELL=X]                    gf180mcu.drc
make lvs    [CELL=X] [SPICE=netlist]    run_lvs.py, against a netlist you name
```

The block lives at `mixed_signal/analog_layout`, and its GDS sits under
`physical/final_views/` the way the digital flow's does. Everything
gf180-specific in it is written in this repository, because cicpy has no
gf180 support: `cicpy.pdk.register_default_providers()` returns without
doing anything for any techlib that does not start with "sky130".

Magic is allowed only as cicpy's backend — it draws the primitive devices
and converts `.mag` to GDS — and is never asked for a verdict. The decks
are the PDK's own KLayout ones, unmodified:
`libs.tech/klayout/tech/drc/gf180mcu.drc` at variant `gf180mcuD`, and
`libs.tech/klayout/tech/lvs/run_lvs.py` at the matching variant `D`.

## What the measurements changed

Three things were not what the plan assumed, and each is recorded in the
code that works around it.

**Magic's gf180mcuD device generator straps nothing, and is not DRC clean
at minimum gate length.** `magic::gencell gf180mcu::nfet_03v3 ... nf 4`
draws four transistors sharing a diffusion and five contact columns and
ties none of them together; extracting the cell yields four separate
devices on four nets, not one four-finger device. Checked on its own, its
output carries 2 to 20 violations per device — M1.3 minimum area on the
poly contacts, and at L = 0.28 an M1.2a spacing failure between the poly
contact's metal and the source/drain contact cap. So a "primitive library"
had to be generated, strapped and re-checked rather than used. All nine
devices the two cells need are now 0 violations
(`primitive_*_drc` in `metrics.json`).

**cicpy's unit system is sky130's in two places, and both are wrong here
by a factor of five.** Its `.mag` reader calls `file_units/magscale*100`
an Ångström; gf180mcuD writes `magscale 1 10` and one of its file units is
5 nm, so one cicpy unit is 0.5 nm. The technology file therefore uses
`gamma: 20`. Its writer emits `magscale 1 2` and rounds to
`angstrom/50`, which quantises output to 25 nm — enough that a 0.26 µm
via1 comes out 0.25 µm and fails V1.1. `cicpy_gf180.patch_magic_scale()`
narrows that to the 5 nm manufacturing grid.

**Magic's DRC is a subset, and the two tools disagree on a real cell.**
Magic passed `CMP` with 0 violations; `gf180mcu.drc` failed it twice on
`NW.2b_LV` — n-well spacing at *different* potential, 1.4 µm, where
Magic had checked only the 0.6 µm equipotential rule. The devices now
stand 1.5 µm apart. Three things the KLayout decks need, each of which
cost a build to find: the density rules say "over the entire die" and no
cell satisfies them, so they are run separately and reported rather than
judged; KLayout's SPICE reader treats a leading `X` as a subcircuit, so
the netlist goes through the PDK's own converter first; and `run_lvs.py`
needs `--combine`, or `nf` fingers drawn as separate transistors never
match one device with `nf`.

## Consequences

`INV` is DRC clean and LVS clean at 8.7 × 5.1 µm — the first analog cell in
this project with a layout artifact behind it.

`CMP`, the comparator of `simulations/gf180_comparator`, is placed,
body-tied and DRC clean at 97.2 × 6.1 µm, and its signal routing is open.
Nine devices in one row put every net on the same horizontal track:
straight M3 connectivity routes short `outa` to `vss`, `left` to `outa`
and `tail` to `vss`, and spreading the nets over M3/M4/M5 still leaves two
shorts and adds six violations. Closing it needs a floorplan — rows,
channels and named corridors — which is what cicpy's `SidecarCell` is for
and is the next piece of work, not a parameter change.

**`make lvs` compares the layout with the netlist it was generated from.**
That proves the generator did not lose a connection; it does not tie the
layout to the simulated comparator. `SPICE=` exists so the comparison can
be pointed at a netlist the layout was *not* built from, which is the one
that proves something.

Two smaller consequences to carry:

- `CMP.spice` draws `XNBUFA` with nf=2 where `comparator.spice` simulates
  nf=4, because a 1.0 µm finger is under the 1.2 µm that two M2
  source/drain straps need. W and L are unchanged; the junction perimeter
  the model derives from nf is not. Re-simulate before the fingering is
  frozen.
- Device layout is one guard-ringed transistor per SPICE instance. That is
  area-expensive and gives no shared diffusion or common-centroid
  arrangement, so it is a flow demonstration, not a matched analog
  floorplan. The differential pair and the current mirror will want
  `SidecarCell` stacks before they are taped out.

Neither `INV` nor `CMP` has PEX. LVS proves connectivity, not performance,
and §8.3 still requires extracted simulation before Gate C.

## Alternatives considered

**KLayout Python generators**, already used elsewhere in this project for
layout scripting. Rejected as the primary path because they produce
geometry, not a schematic-driven netlist-to-layout flow: the connection
back to the SPICE the analog blocks are verified against would have to be
written from scratch, and LVS would compare a layout to a netlist nothing
tied together.

**Drawing the cells in Magic or xschem's GUI.** Rejected under the GUI
boundary rule in `CLAUDE.md`: it is invisible to this workflow and cannot
be regenerated from a clean checkout.

**Magic DRC and netgen LVS as the verdict**, which is what this flow used
first. Rejected once the two decks were compared on the same cell: see
above.

**Waiting for upstream gf180 support in cicpy.** There is none and none is
announced. The provider written here is about 400 lines and is the smaller
commitment.
