# Waveform-Sampling ASIC R&D

Research repository for a waveform-sampling ASIC prototype with an on-chip
Wilkinson ADC, targeting the GF180MCU process and a future wafer.space MPW run.

## Primary documentation

- [Prototype specification (English)](docs/PROTOTYPE_SPECIFICATION.md)
- [ASIC Lab Handbook (English, Markdown)](docs/lecture/ASIC_Lab_Handbook_EN.md)
- [ASIC Lab Handbook (English, PDF)](docs/lecture/ASIC_Lab_Handbook_EN.pdf)
- [ASIC Lab Handbook (English, DOCX)](docs/lecture/ASIC_Lab_Handbook_EN.docx)
- [First-silicon test procedure (English)](docs/SILICON_TEST_PROCEDURE.md)

These English documents are the controlled starting point for design
collaboration.

## Supporting Japanese documentation

- [Prototype specification (Japanese)](docs/PROTOTYPE_SPECIFICATION_JP.md)
- [ASIC Lab Handbook (Japanese, Markdown)](docs/lecture/ASIC_Lab_Handbook_JP.md)
- [ASIC Lab Handbook (Japanese, PDF)](docs/lecture/ASIC_Lab_Handbook_JP.pdf)
- [First-silicon test procedure (Japanese)](docs/SILICON_TEST_PROCEDURE_JP.md)

Start with Lab 0 in the English handbook and satisfy each acceptance check
before moving to the next lab.

## Current status

The repository demonstrates this reproducible path:

1. GF180 transistor-level sampling, mux, ramp, and comparator simulation.
2. Four-cell sequential Wilkinson conversion.
3. Gray-coded comparator-edge capture and controller RTL.
4. File-based four-cell analog-to-RTL co-verification.
5. Slow synchronous 24-bit serial readout.
6. GF180 synthesis, STA, routed GDS, DRC, and LVS for the digital top.

The digital physical block is complete as a flow demonstration. Analog layout,
pad-ring integration, package/PCB design, and provider signoff remain before a
full-chip tape-out. See [Tape-out blockers](docs/TAPEOUT_BLOCKERS.md) and the
[verification matrix](docs/VERIFICATION_MATRIX.md).

## Repository layout

- `docs/`: specifications, roadmap, decisions, MPW constraints, and procedures.
- `simulations/`: schematic/netlist simulations and generated results.
- `scripts/`: environment and reproducibility checks.
- `digital/`: counters, controller, serial readout, and physical views.
- `mixed_signal/`: deterministic SPICE-to-RTL bridges and phase sweeps.

## Getting started

Run the host check:

```sh
./scripts/check-host.sh
```

Run Docker through the project wrapper:

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

Re-run the handbook's pre-layout simulations and RTL checks:

```sh
make course-regression
```

Start the browser-based analog design desktop:

```sh
cp .env.example .env
# Edit .env and set ASIC_RD_VNC_PASSWORD before the first start.
make vnc
```

Open <http://localhost:8080/> and use the locally configured VNC credential.
Stop the environment with `make stop`.

The reference environment uses a version-pinned Linux container on macOS. Do
not copy a PDK into Git; record its source and exact revision in
`docs/decisions/`.

## Working agreement

- Treat the English specification as the controlled scope and interface source.
- Develop on a branch and use a pull request for review before merging to `main`.
- Include the reproducing command, acceptance criterion, and evidence with each change.
- Update the verification matrix when a requirement or interface changes.
- Do not commit PDK files, `work/`, `runs/`, RAW files, or local credentials.

No reuse license has been selected yet. Until a `LICENSE` file is approved,
this repository is shared for project collaboration, not as a general IP grant.
