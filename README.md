# IRSX-like ASIC R&D

Research repository for a one-channel waveform-sampling ASIC prototype with an
on-chip Wilkinson ADC, targeting the GF180MCU process and a future MPW shuttle.

## Current status

The controlled scope and silicon acceptance criteria are defined in
[`docs/PROTOTYPE_SPECIFICATION.md`](docs/PROTOTYPE_SPECIFICATION.md).

The repository now demonstrates the following reproducible path:

1. GF180 transistor-level sampling, mux, ramp, and comparator simulation.
2. Four-cell sequential Wilkinson conversion.
3. Gray-coded comparator-edge capture and controller RTL.
4. File-based four-cell analog-to-RTL co-verification.
5. Slow synchronous 24-bit serial readout.
6. GF180 synthesis, STA, routed GDS, DRC, and LVS for the digital top.

The digital physical block is complete as a flow demonstration. Analog layout,
pad-ring integration, package/PCB design, and provider signoff remain before a
full-chip tape-out. See [`docs/TAPEOUT_BLOCKERS.md`](docs/TAPEOUT_BLOCKERS.md)
and [`docs/VERIFICATION_MATRIX.md`](docs/VERIFICATION_MATRIX.md).

## Repository layout

- `docs/`: roadmap, decisions, MPW constraints, and measurements.
- `simulations/`: schematic/netlist simulations and generated results.
- `scripts/`: environment and reproducibility checks.
- `digital/`: counters, controller, serial readout, and physical views.
- `mixed_signal/`: deterministic SPICE-to-RTL bridges and phase sweeps.

## Start here

Run the host check:

```sh
./scripts/check-host.sh
```

Run Docker through the project wrapper so the setup does not depend on a
system-wide CLI symlink:

```sh
./scripts/docker.sh --version
```

Verify the pinned EDA environment and run the first GF180 simulation:

```sh
make check
make nmos-dc
```

Run the integrated milestones:

```sh
make four-cell-wilkinson
make four-cell-cosim
make phase-sweep
make digital-top
make digital-physical
```

Start the browser-based analog design desktop:

```sh
make vnc
```

Then open <http://localhost:8080/?password=abc123>. Stop it with `make stop`.

The reference environment will use a version-pinned Linux container on macOS.
Do not install or copy a PDK into Git; record its source and exact revision in
`docs/decisions/` instead.
