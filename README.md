# IRSX-like ASIC R&D

Research repository for a one-channel waveform-sampling ASIC prototype with an
on-chip Wilkinson ADC, targeting the GF180MCU process and a future MPW shuttle.

## Current phase

The controlled scope and silicon acceptance criteria are defined in
[`docs/PROTOTYPE_SPECIFICATION.md`](docs/PROTOTYPE_SPECIFICATION.md).

The first objective is not the complete ASIC. It is a reproducible analog flow:

1. Pin the foundry, PDK variant, and MPW submission constraints.
2. Run a GF180 transistor DC simulation from the command line.
3. Reproduce the same circuit in Xschem.
4. Lay out the device/test cell and pass DRC and LVS.
5. Build and characterize a comparator, ramp generator, and sampling switch.
6. Integrate those blocks into a small Wilkinson ADC test macro.

## Repository layout

- `docs/`: roadmap, decisions, MPW constraints, and measurements.
- `simulations/`: schematic/netlist simulations and generated results.
- `scripts/`: environment and reproducibility checks.
- `src/`: design sources, added once the selected PDK flow is operational.

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

Start the browser-based analog design desktop:

```sh
make vnc
```

Then open <http://localhost:8080/?password=abc123>. Stop it with `make stop`.

The reference environment will use a version-pinned Linux container on macOS.
Do not install or copy a PDK into Git; record its source and exact revision in
`docs/decisions/` instead.
