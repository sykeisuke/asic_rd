# Project handoff — design-team onboarding

Date: 2026-08-31

Audience: new design-team members joining the Tape-out 1 effort (first
reader: the first design-team member starting September 2026).

## 1. What this project is

A waveform-sampling ASIC prototype with an on-chip Wilkinson ADC on the
GF180MCU 180 nm process, targeting the **wafer.space GF180MCU Run 3** MPW.
Tape-out 1 is deliberately small — the goal is a reproducible end-to-end flow
(spec → schematic → simulation → layout → signoff → fabrication →
measurement), not performance:

```text
1 analog channel
-> 4 sampling cells (transmission gates, 1 pF hold caps)
-> 4-to-1 analog MUX
-> shared ramp + comparator (Wilkinson)
-> 6-bit Gray-coded counter capture
-> four 6-bit registers
-> 24-bit synchronous serial readout
```

The long-term objective (multi-GSa/s, 8 channels, 12-bit — an IRSX-class
sampler for physics instrumentation) is documented in the specification but
is explicitly **not** a Tape-out 1 pass/fail criterion.

Roles: the project lead owns the specification and requirements; the design
team executes the circuit design. The controlled English documents in this
repository are the single source of truth for scope and interfaces. The
Japanese documents are educational translations intended for future
Japanese-speaking students; they are not a working channel and do not
override the English versions.

## 2. Hard deadlines (wafer.space Run 3, reconfirm at purchase)

| Milestone | Date |
| --- | --- |
| Early-bird pricing ($4k for the 0.5x1 slot) | **2026-09-30** |
| Slot purchase deadline | 2026-12-09 |
| Clean-GDS submission deadline | **2026-12-16** |
| Silicon delivered | Q2 2027 |

## 3. Read these, in this order

1. [`PROTOTYPE_SPECIFICATION.md`](PROTOTYPE_SPECIFICATION.md) — the controlled
   scope: architecture, Must/Target/Stretch requirements, frozen technology
   choices.
2. [`lecture/ASIC_Lab_Handbook_EN.md`](lecture/ASIC_Lab_Handbook_EN.md) — the
   hands-on lab sequence. **Start at Lab 0 and satisfy each acceptance check
   before moving on**; it walks through the exact tools and circuits of this
   project.
3. [`VERIFICATION_MATRIX.md`](VERIFICATION_MATRIX.md) — what is verified and
   the exact `make` target that reproduces each result.
4. [`ROADMAP.md`](ROADMAP.md) — phase status; Phase 0 (external constraints)
   is essentially closed, Phases 2–3 are where design work continues.
5. [`PDK_PAD_SUPPLY_FREEZE.md`](PDK_PAD_SUPPLY_FREEZE.md) — frozen technology
   baseline (PDK commit, 3.3 V libraries, pads) and how each provider
   question was resolved.
6. [`TAPEOUT_BLOCKERS.md`](TAPEOUT_BLOCKERS.md) — the non-optional work
   between here and tape-out.
7. [`decisions/`](decisions/) — why each major choice was made (ADR style).

## 4. State of the project (2026-08-31)

**Done and reproducible** (all pre-layout, typical corner):

- GF180 transistor-level simulations of every analog block: sampling cell,
  4-cell array, analog MUX, ramp generator, comparator (NMOS and PMOS
  variants), single Wilkinson slice, 8-point transfer, and 4-cell sequential
  conversion. Each has a numeric pass/fail check and a `make` target.
- Synthesizable RTL: Gray-coded counter capture, 4-cell controller, 24-bit
  serial readout, integrated `asic_digital_top` — self-checking testbenches,
  GF180 mapping, 20 MHz pre-layout STA.
- File-based mixed-signal co-verification: measured SPICE comparator timings
  drive the real RTL; a ±2 ns clock-phase sweep identified cell 2 as having
  only ~500 ps of CDC margin (known open issue).
- A complete RTL-to-GDS LibreLane flow of the digital top with zero DRC/LVS
  violations — **but at 5 V (`gf180mcu_fd_sc_mcu7t5v0`), as flow evidence
  only**. It must be regenerated at 3.3 V (see next section).
- CI (GitHub Actions): every PR runs the RTL/co-simulation suite in the
  pinned container; the full analog regression runs weekly and on demand.

**Gate A (provider constraints) — resolved 2026-08:**

- wafer.space issues no written confirmations and no design support; the
  authority is the automated precheck and CoB checks on
  <https://platform.wafer.space>. Community help: the provider Discord
  (public archive at <https://discord.wafer.space>).
- Frozen baseline: PDK/Ciel commit `f6eeac7d`, template commit `0de7e394`,
  `gf180mcu_as_sc_mcu7t3v3` cells + `gf180mcu_ocd_io` pads, everything 3.3 V,
  `0.5x1` slot + chip-on-board (COB) packaging.
- **All grounds are common on the default COB breakout** → only `AVDD` can be
  separately measured. A padring experiment (template fork, branch
  `avdd-core-pair-experiment`) re-typed two bidir positions into a second
  core `vdd/vss` pair and **passed the platform's CoB pad-mask check and all
  DRC** (platform Check #800; the "Not Manufacturable" verdict is only the
  empty-core minimum-density artifact, resolved by fill in a real build).
  Experiment GDS: [release `padring-experiment-v1`](https://github.com/sykeisuke/asic_rd/releases/tag/padring-experiment-v1).
- Analog pad ESD: `asig` pads carry HBM diodes to DVDD/DVSS only. Design
  rule adopted from the GF180 DRM: add local CDM secondary protection (diode
  perimeter > 25 um, series poly R > 50 ohm) at every gate-connected pad.
- Platform project exists: Manufacturing ID `G803UHWS` (0.5x1, CoB, private).

## 5. Highest-priority open work (proposed order)

1. **Retarget the digital physical flow to 3.3 V** (`gf180mcu_as_sc_mcu7t3v3`)
   and regenerate GDS/STA/DRC/LVS — do this before any new digital work so
   nothing is built twice.
2. **Comparator mismatch Monte Carlo and PVT matrix** — the two OPEN rows in
   the verification matrix. The comparator's dynamic settling (+6 counts at
   0.4 V input; unreliable at 1.8 V) is the main analog optimization target;
   both NMOS and PMOS input variants are candidates for silicon test
   structures.
3. **Dense transfer test** before any no-missing-code claim.
4. **Analog layout** (sampling cells, MUX, ramp, comparator, bias, test
   access) with DRC/LVS/PEX and post-layout simulation — the critical-path
   item for the December deadline.
5. **Test-MUX truth table freeze** — the logical interface exceeds the six
   true analog pads; monitor/bias functions must be multiplexed (see
   [`TOP_LEVEL_INTERFACE.md`](TOP_LEVEL_INTERFACE.md)).
6. Cell 2 CDC margin (~500 ps) — phase-specification or sequencing fix plus
   transistor-level metastability characterization.

## 6. Environment and daily workflow

Everything runs in one pinned Docker container (IIC-OSIC-TOOLS 2026.07,
pinned by tag **and** digest in `scripts/eda-common.sh`) — macOS or Linux
hosts both work; no tool installation beyond Docker:

```sh
./scripts/check-host.sh   # host sanity (macOS)
make check                # verify the pinned EDA environment
make nmos-dc              # first GF180 simulation (Lab 0)
make course-regression    # everything pre-layout
make vnc                  # browser-based Xschem/Magic desktop (see README)
```

Workflow rules (see README "Working agreement"):

- The English specification is the controlled scope; update the verification
  matrix when a requirement changes.
- Develop on a branch; merge to `main` only through a reviewed PR. CI must
  be green.
- Every change ships with its reproducing command, acceptance criterion, and
  evidence.
- Never commit PDK files, `work/`, `runs/`, RAW files, or credentials.
- The repository is released under Apache-2.0 (decided 2026-08-31, full open
  publication); contributions are accepted under the same license.

## 7. Channels

- GitHub issues/PRs in this repository — primary technical record.
- wafer.space Discord (<https://discord.gg/43y2t53jpE>): `#cob`, `#analog`,
  `#digital`, `#questions`, `#project-template`. Searchable public archive:
  <https://discord.wafer.space>. Two questions are currently posted (pad
  re-typing precedent in `#cob`; `asig_5p0` silicon experience in `#analog`).
- platform.wafer.space — automated precheck/CoB checks (the project lead
  holds the account).
