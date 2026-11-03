# latch: the clocked latch after comparator, as a standard cell

The PDK's own negative-edge flip-flop from the frozen 3.3 V library,
`gf180mcu_as_sc_mcu7t3v3__dfxtn_2`, in place of the hand-made TSPC
(`../latch_bkp/cmp_tspc`, untouched). It sits between `comparator`'s `dout` and the Gray
capture of `digital/wilkinson_gray_counter`, which stays unchanged.

- It samples `dout` on the **falling** edge of the 20 MHz count clock.
- q is the capture clock and drives 50 fF directly: **no buffer** (0.20 ns
  fall typical, 0.27 ns worst against 2.15 ns).
- q falls **exactly once** for any crossing time, bisected to 1 fs from the
  sampling edge at three corner cells. The master latch regenerates, so the
  TSPC's keeper problem does not arise.
- Power is 6.2 µW per latch at typical, in both d states (the TSPC: 2.5 µW
  before the crossing, 0.01 µW after). In `Analog_top_v3` DVDD is 19.0 µW for
  four latches against 3.2 µW.

Requirements, derivations and results: **[`SPEC.md`](SPEC.md)**. Decision:
`docs/decisions/0019-standard-cell-clocked-latch.md`. Record:
`runs/cmp-scff/20261010T185415Z` (37 PASS, 0 FAIL; copy in `results/`).

![latch, xschem](assets/latch_xschem.svg)

```text
.subckt latch d clk q vdd vss          q = d at the falling edge of clk; vdd/vss = digital supply
XFF vdd vdd vss vss clk d q gf180mcu_as_sc_mcu7t3v3__dfxtn_2      (VDD VNW VPW VSS CLK D Q)
.ends latch
```

## The library

`gf180mcu_as_sc_mcu7t3v3` is not in the image's `/foss/pdks`. Install it once:

```sh
./scripts/sim.sh pdk-libs     # ciel enable f6eeac7d --include-libraries all into $HOME/pdks
```

This installs the same pinned commit, outside the repository, and checks that
its ngspice models are byte-identical to the image's. Every deck here includes
`/foss/pdk_libs/gf180mcuD/libs.ref/gf180mcu_as_sc_mcu7t3v3/spice/gf180mcu_as_sc_mcu7t3v3.spice`;
`container.sh` mounts `$PDK_LIBS_ROOT` there read-only. There is no `dffnq`
in this library (that name is the `fd_sc` libraries'); `dfxtn_2` is its only
negative-edge flop.

## Run it

```sh
./scripts/sim.sh latch                                # everything (~15 min)
./scripts/sim.sh latch PHASES='drive aperture check'  # explore drive slew aperture kick schematic check
./container.sh 'python3 bench.py drive'                  # one bench, tables in data/
```

## Benches

| Bench | File | What it shows | Gate (SPEC.md) |
| --- | --- | --- | --- |
| explore | `tb_drive.spice`, `scff_variants.spice` | `dfxtn_2` alone, + `buff_2`, + `buff_4` into 50 fF at four cells | the flop alone meets S4 everywhere: no buffer |
| drive | `tb_drive.spice` | four cells (typical, ss 0 C 3.0 V, ff 85 C 3.6 V, ss 85 C 3.0 V); d moves both ways in both clock phases; power, leakage; `tspc_dff` on the same bench for reference | S2-S5 |
| slew | `tb_drive.spice` | clock edges 0.2-8 ns at four cells | S6 (1 ns); limit reported (8 ns at every cell) |
| aperture | `tb_aperture.spice` | `dout`'s edge swept across the sampling edge, bisected to 1 fs, then 1e-10..1e-15 s either side; slow d at three cells, fast d at typical | S7: one fall, no rise, no runt, stays low |
| kick | `tb_kick.spice` | `comparator` (on its XREFP diode, 1.681 x 1.931 uA) + latch on the cell's charge path, codes 4/64/128/250 x 8 phases, clock on/off; `tspc_dff` and 10 fF as references | S10, S12 |
| schematic | `latch.sch`, `tb_*.sch`, `schematic.sh` | xschem netlists `latch.sch` back to `latch.spice`; the three testbench drawings netlist, render and reproduce their hand benches (`xtb.py`) | instance and port order equal; every bench instance present; figures within 10 ps (50 ps for kick) |

## Drawings

`tb_sch.py` writes one xschem testbench per bench, each at the nominal case
`bench.py` renders the template with (typical, 27 C, 3.3 V, clock edge 0.5 ns
and d edge 10.4 ns 10-90 %, q into 50 fF): `tb_drive.sch` (the drive
timeline), `tb_aperture.sch` (d's edge at DT = 0 from the sampling edge at
125 ns) and `tb_kick.sch` (`comparator` + `latch` on the cell's charge path,
VIN at code 64 = 0.875 V, count clock running). The DUT is `latch.sym`, so
xschem netlists `latch.sch` into the bench; `tb_kick.sch` places
`../comparator/comparator.sym` through `xschemrc`, so the comparator in that
netlist is `comparator.sch`, not the deck. The TSPC reference and the `LOAD`
variants of `tb_kick.spice` stay in the deck. A code block on each sheet
carries the model and library lines, the parameters and a `.control` block
with the bench's main figures.

`schematic.sh` proves them: `check-tb.awk` finds every instance of the bench
in the xschem netlist with its nodes (xschem drops an instance silently when
a symbol is missing), the sheets are rendered to `assets/tb_*_xschem.png` /
`.svg`, and `xtb.py` simulates each xschem netlist and the hand bench at the
same case: drive clock-to-q and q fall, aperture fall / rise counts, edge,
clock-to-q and q fall agree within 10 ps (measured <= 0.06 ps); kick
`t_cross`, `t_dout`, `t_q` and the dout fall agree within 50 ps once the PDK
symbols' S/D junction geometry (which the hand deck lacks) is stripped from
the comparator (measured <= 8 ps); as drawn, that geometry adds +0.44 ns to
`t_dout` (+0.54 ns comparator delay) and +75 ps to the dout fall, reported
in `data/xtb.csv`, together with the plate step across the sampling edge
before the crossing (+-1 uV = 0.0002 LSB, the numerical floor at reltol 1e-4). Record: `runs/latch/20261031T021440Z` (22 PASS, 0 FAIL).

![tb_drive, xschem](assets/tb_drive_xschem.svg)
![tb_aperture, xschem](assets/tb_aperture_xschem.svg)
![tb_kick, xschem](assets/tb_kick_xschem.svg)

## Files

| File | What it is |
| --- | --- |
| `latch.spice` | the subcircuit (one library cell) |
| `latch.sch`, `latch.sym` | xschem schematic and symbol (the TSPC's pin order) |
| `tb_sch.py` -> `tb_drive.sch`, `tb_aperture.sch`, `tb_kick.sch` | xschem testbench drawings of the three benches at their nominal case (generated; see Drawings) |
| `xschemrc` | symbol path: the PDK, this folder, `../comparator` (so `tb_kick.sch` places `comparator.sym` and xschem descends into `comparator.sch`) |
| `check-tb.awk`, `xtb.py` | the testbench netlists checked instance by instance, then simulated against the hand benches -> `data/xtb.csv` |
| `gf180mcu_as_sc_mcu7t3v3__dfxtn_2.sym` | xschem primitive symbol of the library cell (the PDK ships none for this library) |
| `scff_variants.spice` | the buffer candidates for `explore` |
| `SPEC.md` | requirements, buffer decision, results, what is not covered |
| `bench.py` | renders the bench templates, runs ngspice in parallel, reduces each run to a CSV row |
| `tb_*.spice` | bench templates |
| `check-*.awk` | PASS / FAIL / REPORT on the tables |
| `run.sh`, `container.sh`, `schematic.sh` | the flow; `scripts/run-latch.sh` and `make latch` call `run.sh`; `schematic.sh` also runs `tb_sch.py`, `check-tb.awk` and `xtb.py` |
| `data/` | `explore.csv`, `drive.csv`, `drive_tspc.csv`, `slew.csv`, `aperture.csv`, `kick.csv`, `kick_runs.csv`, `xtb.csv` |
| `results/` | copy of the cited `metrics.json` |

Reads outside this folder, read-only and by path: the PDK models, the
library's SPICE view (`/foss/pdk_libs`), `../comparator/comparator.spice`
and `ref/tspc_dff.spice` (references in the drive and kick benches), and
`../comparator/comparator.sym` / `comparator.sch` (the comparator drawing in `tb_kick.sch`).
