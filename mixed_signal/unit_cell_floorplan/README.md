# Unit cell floorplan: switch + hold capacitor + comparator, MIM against MOM

Four floorplans of the same slope-ADC unit cell (per-cell comparator, no
mux), drawn to scale with the PDK's own device generators and laid out to the
analog layout rules of Pretl's *Design of Complex ICs* (unit fingers, dummies,
ABBA common centroid, symmetry axis, pin-side placement, wiring channel), so
the question "minimum MOM (15.6 fF) beside the comparator, or minimum MIM
(54.5 fF) on top of it -- and what happens at the 125 fF the 12-bit target
needs" is answered by a GDS and a DRC run rather than by a sketch.

| Cell | Capacitor | Result |
| --- | --- | ---: |
| `UC_MIM` | 54.5 fF MIM over the tail | 715.7 um², DRC 0 |
| `UC_MOM` | 1 MOMU beside | 734.8 um², DRC 0 |
| `UC_MIM_125` | 125 fF MIM over the tail | 715.7 um², DRC 0 |
| `UC_MOM_125` | 8 MOMU beside | 1047.8 um², DRC 0 |

```sh
./run.sh                                     # all four: GDS, DRC, render, SVG, report, PASS/FAIL
./container.sh 'python3 floorplan.py UC_MIM' # one cell, raw metrics
FS_MHZ=100 ./run.sh                          # switch re-derived at another rate
```

Everything runs in the pinned IIC-OSIC-TOOLS container through `container.sh`,
which mounts the **main checkout** (this block may sit in a git worktree) and
reaches the assets it reuses by path, never by copy:

| Reused | Path (host) |
| --- | --- |
| Comparator being laid out | `../comparator_unit_cell/cmp_uc_<tag>.spice`: `cmp_p5t_8b` re-sized into each cell's own hold capacitor (`CMP_SOURCE=p5t8b` builds around the recorded `mixed_signal/comparator/cmp_p5t_8b.spice` instead) |
| Switch widths | `../comparator_unit_cell/data/switch_sizing.json` (the sampling-cell rule on C_hold + the comparator's input capacitance) |
| MOM unit capacitor drawing | `mixed_signal/analog_layout/mom_cap.py` (`MOMU`, 15.62 fF, 5.32 x 5.16 um) |
| KLayout DRC signoff | `mixed_signal/analog_layout/signoff.py` (PDK deck, `gf180mcuD`, density reported not judged) |
| Render | `mixed_signal/analog_layout/klayout/render.rb` |
| Switch sizing rule | `simulations/gf180_sampling_unit_cell/design_cell.py` (K = 2710 ohm.um measured) |
| Device pcells | gdsfactory `gf180mcu` plugin from `.eda-tools` (`make tools`) |

Outputs: `physical/final_views/gds/UC_*.gds`, their KLayout renders under
`physical/final_views/render/`, the annotated floorplans under `svg/`, the
comparison page `physical/final_views/report.html`, DRC reports under
`work/`, and `work/floorplan.txt` with one `name = value` line per figure of
merit. `RESULTS.md` is the write-up; `work/sizing_rationale.md` traces every
transistor size back to the comparator's sizing tool; `work/mim_rules.md`
lists the MIM design rules with values.

No Makefile target, no `scripts/run-*.sh`, no VERIFICATION_MATRIX row: this is an
exploratory block and nothing outside this folder was edited.
