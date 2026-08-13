# GF180 sampling-cell baseline

This experiment is the first analog block from the prototype specification. It
uses a 3.3 V GF180 NMOS as a sampling switch and a 1 pF ideal hold capacitor.
The baseline is intentionally simple: its measured limitations will guide the
transmission-gate and physical-capacitor versions.

Run:

```sh
make sampling-cell
```

The automated transient test reports:

- acquisition error immediately before the sampling switch opens;
- clock feedthrough around the falling clock edge;
- held-voltage droop during the remainder of the hold interval.

Generated waveforms and measurements are written under `work/` and are not
tracked by Git. This test uses the typical model corner. PVT and Monte Carlo
coverage will be added after the baseline topology and capacitor choice are
reviewed.

Open `sampling_cell.sch` in Xschem to inspect the circuit. The controlled
batch test is `sampling_cell.spice`; numerical results and the resulting
design decision are recorded in [`RESULTS.md`](RESULTS.md).

The same command first runs `ideal_sampling_cell.spice` as an ideal-switch
reference, then runs `transmission_gate.spice`, which adds a PMOS switch
and complementary clock for a like-for-like comparison with the NMOS baseline.

For the guided Xschem exercise, open `sampling_cell_tg.sch`. It shows the
provisional transmission-gate topology and plots `VIN`, `VHOLD`, `SAMPLE`, and
`SAMPLE_B`. The detailed Japanese lab procedure is in
[`SAMPLING_CELL_LAB_JP.md`](SAMPLING_CELL_LAB_JP.md).
