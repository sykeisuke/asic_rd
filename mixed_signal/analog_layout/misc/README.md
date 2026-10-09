# misc/: gdsfactory layouts, GDSFactory+ project

Hand-placed analog cells drawn in Python with [gdsfactory](https://gdsfactory.github.io/gdsfactory/)
on the `gf180mcu` PDK plugin (`make tools` installs the pinned
`gf180mcu==1.0.0` next to the cicpy add-on). The folder is laid out as a
[GDSFactory+ 2.0](https://news.gdsfactory.com/introducing-gdsfactory-plus-2-0/)
project so the VS Code extension can open it; the reproducible path is the
make target, which runs the same factory inside the pinned container and
signs it off with the PDK's own KLayout decks.

```sh
make gf-inverter                  # draw INV_GF, render, KLayout DRC + LVS
./scripts/sim.sh gf-inverter      # same, recorded in runs/gf-inverter/latest/metrics.json
./scripts/sim.sh gf-comparator    # CMP_LP: draw, DRC, LVS, pin check, extraction
```

| | |
| --- | --- |
| `gfp_misc/cells/inverter.py` | the cell: `INV_GF`, a `@gf.cell` factory |
| `gfp_misc/cells/comparator.py` | the cell: `CMP_LP`, the 8-bit minimum-power comparator of `../../comparator_lp/cmp_lp.spice` |
| `INV_GF.spice` | LVS reference, the devices of `../spice/INV.spice` |
| `build.py` | headless build of either cell (`python3 build.py [CMP_LP]`); generates `CMP_LP`'s LVS reference from `cmp_lp.spice`; `--control` writes the swapped-pin control |
| `extract.py` | kpex extraction of `CMP_LP` into the drop-in `build/CMP_LP_pex.spice`; `--names` is the pin/net-name check |
| `check-gf-inverter.awk`, `check-gf-comparator.awk` | the PASS/FAIL lines |
| `pyproject.toml` | GDSFactory+ project settings (`[tool.gdsfactoryplus.pdk] name = "gf180mcu"`) |
| `build/` | build output, git-ignored: `gds/`, `render/`, `CMP_LP.spice` (LVS reference), `CMP_LP_pex.spice` (extracted) |

## State

| Cell | Devices | Size | DRC (`gf180mcu.drc`, density apart) | LVS |
| --- | --- | --- | --- | --- |
| `INV_GF` | nfet_03v3 3u/0.28u nf=2, pfet_03v3 6u/0.28u nf=2 | 3.7 x 9.63 um (35.6 um^2) | clean | **matches** `misc/INV_GF.spice` |
| `CMP_LP` | the 13 transistors of `cmp_lp.spice` | 60.51 x 20.91 um (1265 um^2) | clean | **matches** `build/CMP_LP.spice`, pin names checked |

Run of 2026-09-21: `runs/gf-inverter/20260921T204828Z/metrics.json`,
`pass: true`, `inv_gf_drc_violations = 0`, `inv_gf_lvs_match = 1`,
`gfp_factories = 1`. The seven die-density rules (`M1.4`..`MT.3`, `PL.8`)
are reported, not judged, as everywhere else in this block.

The cicpy INV of the same netlist is 8.7 x 5.1 um: cicpy puts both
devices in one row with M2 straps over guard rings, this cell stacks
them with M1 rails and taps, standard-cell style.

## The cell

```text
        VDD rail (M1) over an N+ well tap
   |  |  pfet 2 x 3.0 um, source columns run up to the rail
   |  |  poly bridge over the finger ends, gate contact left of the device
 A |  |Y  <- channel: A on M1 down the left edge, Y on M1 up the centre
   |  |  poly bridge, gate contact
   |  |  nfet 2 x 1.5 um, source columns run down to the rail
        VSS rail (M1) over a P+ substrate tap
```

Every coordinate is read back from the plugin's polygons (`COMP` extent,
the M1 source/drain columns, the poly extent), so `INV_GF(w_n=..., nf=...)`
moves the routing with the devices. With default arguments the cell is
named `INV_GF`, the name the netlist and signoff use.

## Finding: the plugin's transistors are not `gf180mcu.drc` clean

The plugin's `nfet`/`pfet` put a contacted M1 pad on the poly pad at
**both** ends of every finger. That M1 sits 0.115 um beside the S/D column
and 0.175 um above its end, 0.209 um corner to corner. `gf180mcu.drc`
checks `M1.2a` (0.23 um) as a Euclidean distance, so every pad fails it;
the pads a cell does not wire up fail `M1.3` (min area, 0.078 < 0.1452 um^2)
as well. Measured on the first version of this cell, which used the pads:
54 violations, `M1.2a:40, M1.3:6` plus 8 `M1.1` of my own. The plugin is
written to "match Magic VLSI geometry", and Magic's DRC does not measure
corner to corner: the same trap as `NW.2b_LV` on the cicpy comparator.

`INV_GF` therefore takes each transistor without those pads: M1 and
contact shapes lying wholly outside the `COMP` are dropped from a
flattened copy (`_without_gate_pads`), the poly pads stay, and the gate is
contacted on the poly bridge 0.30 um clear of the columns. With that, all
routing is M1 and the cell is clean. Recorded in
[ADR 0008](../../../docs/decisions/0008-gdsfactory-plugin-cells.md).

## Using the GDSFactory+ extension

The extension (`gdsfactory.gdsfactoryplus`, 2.0.406, installed in the WSL
VS Code server) works on a folder whose root holds a `pyproject.toml` with
a `[tool.gdsfactoryplus]` table. Open **this folder** as the workspace, not
the repository root. It then creates `.venv` from the dependencies here
(`uv`, network, and a GDSFactory+ subscription), lists every `@gf.cell`
it finds under `gfp_misc/` in its cell tree, and shows the GDS of a
selected factory in its layout view. Its own DRC/LVS run on a hosted
service and are not a signoff for this project: KLayout's decks through
`make gf-inverter` are.

What has been verified without the GUI: the extension's indexer, the
`gfp` binary the extension ships, lists `gfp_misc.cells.inverter.INV_GF`
as a factory with its seven parameters. `scripts/run-gf-inverter.sh` runs
it when the extension is present and prints the result as a PASS line
(`gfp_factories = 1`); without the extension the step is a `REPORT`, not
a failure. What has **not** been verified: `.venv` creation, the layout
viewer and the hosted checks. Those are GUI actions.

## The comparator, `CMP_LP`

The minimum-power, 8-bit comparator of `../../comparator_lp/cmp_lp.spice`,
all 13 transistors, drawn with the same pad-stripped plugin FETs and wired
the same way each time: poly bridge, contact row and M1 gate strap on one
side; source columns out to an M1 strap or rail on the other; via1 on each
drain column into an M2 strap. Run of 2026-09-24:
`runs/gf-comparator/20260925T041246Z/metrics.json`, `pass: true`.

```text
    vdd rail (M1) over the n-well tap ----------------------------------
    P2          XRPB   XTAIL              XBST                 | pbias
    P1                 XINP     XINN      XBUF2  XBUF4         |
    N    XCLMP  XRPN   XLOADD   XLOADM    XBUF1  XBUF3         |
    vss rail (M1) over the substrate tap -------------------------------
```

| Pin | Layer, place |
| --- | --- |
| `inp`, `inn`, `pbias` | M3, top edge |
| `dout` | M3, right edge |
| `vdd`, `vss` | M1 rails, full width |

`clk` and `nbias` are ports of `cmp_lp.spice` that no device uses; they
are not drawn, and the extracted netlist keeps them as unconnected ports.
The internal nets `left tail outa outb rep bst` carry M2 labels so that
the extracted netlist uses the names the benches probe. XCLMP (body =
`outa`) sits in its own n-well with an N+ tap on `outa`.

Three things differ from `cmp_lp.spice`, on purpose (ADR 0010):
XLOADD/XLOADM, XTAIL and XBST are drawn with 10, 10 and 8 fingers, because
the recipe's `W/nf` is off the 5 nm grid for them (total W unchanged);
COUTA is not drawn (it stood in for the parasitics); clk/nbias as above.

**LVS does not check pin names.** KLayout's compare pairs top-level nets
by topology: a copy of the GDS with `inp` and `inn` swapped still
"matches". The flow therefore compares the LVS extraction with the
reference net name by net name (`extract.py --names`) and requires that
swapped control to fail it.

### Using the extracted netlist

`build/CMP_LP_pex.spice` is `.subckt cmp inp inn dout clk vdd vss nbias pbias`,
the same name, ports, instance names (XINP..XBUF4) and internal nodes as
`cmp_lp.spice`, with the 54 kpex capacitances and the two n-well
junctions (linear, typical zero bias) in place of COUTA. The
comparator_lp benches take it through `run.sh`'s `DUT` switch, under a
separate run record so the pre-layout `latest` stays as it is:

```sh
cd mixed_signal/comparator_lp
DUT=../analog_layout/misc/build/CMP_LP_pex.spice TARGET=comparator-lp-pex \
  PHASES='offset ramp ac noise' ./run.sh
```

Those are the ngspice phases. The VACASK phases (`vnoise`, `mc`) translate
`cmp_lp.spice` itself and do not follow `DUT`. **The extracted netlist
has not been simulated.** Extracted load on `outa`: 17.8 fF of wiring
plus 29.5 fF of clamp-well junction (zero bias), against the recipe's
assumed 20 + 15 fF.

Adding a cell: one `@gf.cell` function in a new file under
`gfp_misc/cells/`, a netlist beside `INV_GF.spice`, and a `scripts/run-*.sh`
plus `Makefile` target that builds and signs it off the same way.
