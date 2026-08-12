# GF180 NMOS width experiment

This experiment is a copy of the baseline NMOS DC sweep with the device width
changed to `W=3 um` (`L=0.28 um`). It demonstrates how transistor width changes
the drain-current family while keeping the same `VDS` and `VGS` sweeps.

Run it from the Xschem GUI:

```text
Save -> Netlist -> Simulate -> Ctrl+click "Load simulation results"
```

The schematic writes `nmos_dc.raw` in Xschem's `$netlist_dir`; the launcher
loads the same file. The graph uses `i(vd) -1 *`, `x1=0`, `x2=3.3`, and
`y2=0.0012`. Since the expected maximum current is around 1.5 mA, increase
`y2` to approximately `0.0018` to see the complete upper curve.

Generated RAW files and netlists are not design sources and should not be
committed.
