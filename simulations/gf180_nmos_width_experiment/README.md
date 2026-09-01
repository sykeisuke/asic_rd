# GF180 NMOS width experiment

This experiment is a copy of the baseline NMOS DC sweep with the device width
changed to `W=5 um` (`L=0.28 um`, baseline `W=1 um`). It demonstrates how
transistor width scales the drain-current family while keeping the same `VDS`
and `VGS` sweeps.

Both sources carry the same width and are checked against each other by the
run script:

- `nmos_dc.sch` — Xschem schematic (`M1`, `W=5u`), graph `y2=0.003`.
- `nmos_dc.spice` — hand-written ngspice netlist (`XMN`, `W=5u`), writes
  `work/nmos_id_vds.csv`.

## Reproducible run

```sh
make nmos-width
```

The script netlists the schematic, runs both netlists in the pinned
container, verifies that both contain `W=5u`, and prints the peak drain
current. Typical-corner result (2026-09-01): **2.55 mA** at `VGS=VDS=3.3 V`,
about five times the `W=1 um` baseline, as expected for a width scaling.

## Interactive run

From the Xschem GUI (`make vnc`):

```text
Save -> Netlist -> Simulate -> Ctrl+click "Load simulation results"
```

The schematic writes `nmos_dc.raw` in Xschem's `$netlist_dir`; the launcher
loads the same file. The graph uses `i(vd) -1 *`, `x1=0`, `x2=3.3`, and
`y2=0.003`, which fits the 2.55 mA peak with margin. When you change `W`
again, rescale `y2` roughly in proportion and update both netlist sources and
this README together.

Generated RAW files and `work/` outputs are not design sources and are not
committed.
