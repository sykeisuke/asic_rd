# Analog layout: cicpy generation, KLayout signoff

Schematic-driven analog layout with [cicpy](https://analogicus.com/cicpy/),
Carsten Wulff's Python port of ciccreator. `cicpy spi2mag` reads a SPICE
subcircuit, resolves each device to a Magic cell, places the instances,
routes the nets, and writes `.mag` — which becomes the GDS under
`physical/final_views/`, laid out the way the digital flow's
`final_views/` is.

```sh
make tools                        # once per checkout: installs cicpy 0.3.1
make layout                       # every netlist in spice/
make layout CELL=CMP
make drc    CELL=CMP
make lvs    CELL=CMP
make lvs    CELL=CMP SPICE=simulations/gf180_comparator/comparator.spice
```

Each is also `./scripts/sim.sh layout|drc|lvs`, which records the run in
`runs/<target>/latest/metrics.json`. Nothing here needs a `.mag`, a
`.gds` or a log to be opened.

| | |
| --- | --- |
| `physical/final_views/gds/<CELL>.gds` | the layout |
| `physical/final_views/render/<CELL>.png` | KLayout's picture **of that GDS**, PDK colours |
| `physical/final_views/svg/<CELL>.svg` | cicpy's vector view of its own `.cic` model |

## State

| Cell | Source | DRC | LVS |
| --- | --- | --- | --- |
| `INV` | `spice/INV.spice` | clean, 8.7 × 5.1 µm | **matches** |
| `CMP` | `spice/CMP.spice` | clean, 97.2 × 6.1 µm | **mismatch** — signal nets unrouted |
| `INV_GF` | `misc/gfp_misc/cells/inverter.py` (gdsfactory, not cicpy) | clean, 3.7 × 9.6 µm | **matches** `misc/INV_GF.spice` |
| `CMP_LP` | `misc/gfp_misc/cells/comparator.py` (gdsfactory), circuit `../comparator_lp/cmp_lp.spice` | clean, 60.5 × 20.9 µm | **matches** the reference generated from `cmp_lp.spice`; pin names checked |

`INV_GF` is the same netlist drawn by hand in gdsfactory on the
`gf180mcu` PDK plugin, as a GDSFactory+ project: `make gf-inverter`, see
[`misc/README.md`](misc/README.md) and ADR 0008 for why the plugin's
transistors cannot be used as they come.

`CMP_LP` is the 8-bit minimum-power comparator drawn the same way:
`make gf-comparator` draws it, signs it off, and extracts it into
`misc/build/CMP_LP_pex.spice`, a drop-in for `cmp_lp.spice` (ADR 0010).

`CMP` is the comparator of `simulations/gf180_comparator`, placed and
body-tied. `make lvs` fails on it, and that is the honest state: nine
devices in one row put every net on the same horizontal track, straight
M3 routes short `outa` to `vss`, `left` to `outa` and `tail` to `vss`,
and spreading them over M3/M4/M5 still leaves two shorts. A cell this
size wants a floorplan — rows, channels, named corridors — which is what
cicpy's `SidecarCell` is for.

## Signoff is KLayout's

DRC and LVS use the PDK's own decks, unmodified:

- `/foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc`,
  variant `gf180mcuD` (5LM, 11K metal top, MIM B), `run_mode=deep`
- `/foss/pdks/gf180mcuD/libs.tech/klayout/tech/lvs/run_lvs.py`,
  variant `D` — the same stack

Magic appears only as cicpy's backend: it draws the primitive devices
and converts `.mag` to GDS. It is never asked for a verdict. The two
tools do disagree — Magic passed a `CMP` that `gf180mcu.drc` failed on
`NW.2b_LV`, n-well spacing at different potential.

Three things the KLayout decks need, each of which cost a build to find:

- **Density is run separately and reported, not judged.** `M1.4` through
  `MT.3` and `PL.8` read "coverage over the entire die shall be >30%".
  A few-micron cell cannot satisfy them and fill satisfies them at chip
  level, so `signoff.py` runs the deck twice: `decks=all,-density` for
  the verdict, `decks=density` for the record.
- **The netlist has to be converted.** KLayout's SPICE reader treats a
  leading `X` as a subcircuit instance, not a MOS, so an ngspice netlist
  compares against nothing. The PDK's
  `gf180_xschem_klayout_spice_convert.py` rewrites `X` to `M`.
- **`run_lvs.py --combine` is not optional.** The layout draws `nf`
  fingers as `nf` separate transistors; the netlist names one device
  with `nf`. Without device combination they are different circuits.

## What had to be built for gf180

cicpy ships one primitive provider and it is sky130's:
`cicpy.pdk.register_default_providers()` returns without doing anything
for any other techlib.

### `tech/cic/gf180mcuD.tech`

Layer aliases are gf180mcuD *Magic paint-type* names, because cicpy's
`.mag` reader resolves a `<< name >>` section header through
`Rules.aliasToLayer`. Layer numbers are the calma numbers of the Magic
tech file's `cifoutput style gdsii` section. Design rules come from the
Magic `drc` section.

The unit system is the part that is easy to get wrong. cicpy's reader
computes `file_units / magscale * 100` and calls the result an Ångström.
gf180mcuD writes `magscale 1 10` and one of its file units is 5 nm
(measured: the gate of a `w=2 l=0.5` device is 100 × 400 file units), so
one cicpy unit here is 0.5 nm, not 1 Å. `gamma` is therefore **20**, not
the 100 a sky130 tech file uses, and every rule value is plain
micrometre × 100.

### `cicpy_gf180.py`

Generates a Magic layout for every `nfet_03v3` / `pfet_03v3` instance by
calling the PDK's own device generator, then makes it usable:

- **Magic's gf180 device generator straps nothing.** `gencell ... nf 4`
  draws four transistors sharing a diffusion and five contact columns
  and ties none of them together — extract it and you get four devices
  on four separate nets. The provider adds an M1 bar across each poly
  contact band, and two M2 bars over the diffusion with a via1 into each
  alternating source/drain column.
- **The body needs an M2 landing.** The guard ring is 0.23 µm of M1,
  narrower than a via1, so the router cannot get from the body to the
  source: measured, every supply net stayed open across five route types
  and three of them added violations. The ring is widened in a lane kept
  clear beside the gate bar, and one via1 and an M2 tab take it to the
  edge.
- **`FIXED_BBOX` is not the cell's extent.** The well runs 0.29 µm
  outside it on every side; cicpy spaces instances by the box, so two
  devices 1 µm apart had wells 0.42 µm apart. The box the provider
  publishes is everything the cell draws.
- **`diffcov 90`.** At the default 100 the source/drain contact's M1 cap
  comes within 0.175 µm of the poly contact's M1, and Magic's own device
  fails M1.2a at L = 0.28.

`patch_magic_scale()` also replaces `MagicPrinter`'s sky130 write scale.
cicpy writes `magscale 1 2` and rounds to `angstrom/50`, which quantises
everything it writes to 25 nm here — enough to make a 0.26 µm via1 come
out 0.25 µm. `V1.1` is a **min/max** rule, so that is a violation in
both directions. Writing `magscale 1 10` and rounding to `angstrom/10`
lands the output on the 5 nm manufacturing grid instead.

### `design/GF180_WSA/*.py`

Placement and routing intent per cell. `tie_body()` lives in the
provider module but is called from here, because only the netlist knows
whether a device's body is its own source: `XTAIL tail vbias vss vss`
ties them and `XINP left vin tail vss` must not.

Devices stand 1.5 µm apart, not the 0.6 µm of `NW.2a`: that rule is for
wells at *equal* potential, and nothing proves these are until the
supply is routed. KLayout applies `NW.2b`, 1.4 µm, instead.

## Open

- `CMP` signal routing, and the LVS that depends on it.
- **`make lvs` compares the layout with the netlist it was generated
  from.** That proves the generator did not lose a connection; it does
  not tie the layout to the *simulated* comparator. `spice/CMP.spice`
  differs from `simulations/gf180_comparator/comparator.spice` in one
  way: `XNBUFA` is nf=2 there and nf=4 in the simulation deck, because a
  1.0 µm finger is under the 1.2 µm two M2 source/drain straps need. W
  and L are unchanged; the junction perimeter the model derives from nf
  is not. Re-simulate before the fingering is frozen.
- One guard-ringed transistor per SPICE instance. Area-expensive, with
  no shared diffusion and no common-centroid arrangement — a flow
  demonstration, not a matched analog floorplan.
- No PEX. LVS proves connectivity, not performance.
