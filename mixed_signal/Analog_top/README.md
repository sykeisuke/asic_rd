# Analog_top: the analog macro, v7 (switch controls made on chip)

Date: 2026-11-01. v6 with the sampling sequencer `../sample_seq` inside
(ADR 0027): the twelve switch controls `s2_k` / `s0_k` / `s1_k` are no longer
ports; one instance `XSEQ` (82 frozen standard cells on DVDD) makes them from
the count clock and the new port `acq` (the controller's `acquire` level).
Cell k's S2 opens ~0.7 ns after the k-th clock edge after `acq` falls, S0
one stage delay later, S1 closes one stage delay after that, each stage
>= 5 ns at every PVT cell (the block's record). v6 is archived in
`../Analog_top_bkp/Analog_top_v6` (local) and `data/v6_ref/`.

## v7: what changed against v6

`check_equiv.py` proves it on every run:

1. **Ports:** v6's 23 - the 12 switch controls + `acq` (after `cnt_clk`) = 12:
   `vin ramp_rst cnt_clk acq q0..q3 avdd avss dvdd dvss`.
2. **Devices:** 383 = v6's 301 + sample_seq's 82 standard cells (44
   `dlybuff_2`, 12 `dfxtp_2`, 12 `xor2_2`, 4 `nor3_2`, 4 `nor2_2`, 3
   `clkbuff_4`, `nand4_2`, `dlxtn_2`, `and2_2`); every v6 device keeps its
   path, model and parameters; all 232 v6 nets match one-to-one, the 12
   controls renamed from ports to internal nets (declared). `atop_cell` is
   unchanged.
3. **Bench:** the twelve ideal PWL sources are gone; `VACQ` falls at TACQ =
   TS0 - TSPACE + 2 ns. `TNOV` is replaced by `TSEQ` = 25 ns (S1 closed by
   then at every PVT cell); the plates "before S1" are read as `s1_k`
   passes 10 % VDD, "after S1" at TS_k + TSEQ + 10 ns, the S2 pedestal at
   TS_k + 3 ns. New gate `sequencer` in `check-func.awk`.

| Quantity | v6 (ideal controls) | v7 (sample_seq) |
| --- | --- | --- |
| S2 opens after the clock edge TS_k | 0 (ideal) | 0.658-0.676 ns |
| S2 -> S0 / S0 -> S1 | 5 / 5 ns (ideal) | 7.298-7.335 / 7.376-7.408 ns |
| Cell spacing | 50 ns | 50 ns within 0.017 ns |
| S0 open before vin steps (TS_k + 20 ns) | 15 ns | 11.99 ns |
| Codes for 16.5 / 80.5 / 160.5 / 240.5 LSB | 17 / 81 / 160 / 239 | **17 / 81 / 160 / 239** (identical) |
| Trip (dout from TR), cells 0..3 | | -0.014 / -0.018 / -0.016 / -0.014 counts |
| Plate error spread | 0.038 LSB | 0.032 LSB |
| Transfer offset / gain error | +0.780 LSB / -0.951 % | +0.764 LSB / -0.951 % |
| S2 pedestal on bot | | -3.09 .. -3.14 mV (now read 3 ns after the edge) |
| Armed margin at TR | 47.2 mV | 47.1 mV |
| Power over the ramp | 811.6 uW (DVDD 41.6) | 815.4 uW (DVDD 45.3: the clock gate's clock pins) |

Records (typical, 27 C, 3.3 V): `runs/analog-top/20261101T005241Z`
(`./scripts/sim.sh analog-top REGEN=1`: schematic, op, xtb, pwr pass, 73
checks; its func phase failed in `func_reduce.py`, which still read the
controls as top-level waves, fixed) and `runs/analog-top/20261101T021910Z`
(`PHASES=func`: 13/13). The block: `runs/sample-seq/20261031T231843Z` (40/40).

Not done in v7: corners of the macro with the sequencer (the block has its
own 45-cell PVT record), the controller's CONNECT_CYCLES (2) against the
macro's need of 4 sampling cycles + 300 ns before the ramp release (ADR
0027), the chip placeholder's pins (`../top_placement/analog_macro.py`).

---

# Analog_top: the analog macro, v6 (I/C-fed ramp on the ADR 0025 grid)

Date: 2026-10-30. v5 with the ramp of ADR 0025: `../ramp_simple` (73 unit MIMs
+ reset switch) fed by the I/C current source `../ic_source`, `vrlo_ref` at
7/55 AVDD = 0.420 V (the pre-roll reset level), the 6.70 mV grid, T0 = 60 us,
the ramp ending at count 259. Decision record:
[ADR 0026](../../docs/decisions/0026-analog-top-ic-ramp.md). v5 is archived in
`../Analog_top_bkp/Analog_top_v5` (local) and `data/v5_ref/` (its netlist and
functional / power record); the v5 text of this README follows below s.v6.

## v6: what changed against v5

`check_equiv.py` proves it on every run (both macros flattened to devices,
nets matched by their (device, terminal) pin sets):

1. **Ramp.** `ramp_simple_d` (L 8 um PMOS source XPS, its diode XRD, 4 pF MIM
   XCR, XRST) is gone. `XRAMP vramp ramp_rst vrlo avss ramp_simple` and
   `XIC vramp pbias_r cnt_clk avdd_ramp avss dvdd dvss ic_source` replace it:
   bias_gen_s's ramp sink (3.25 uA) into ic_source's diode, the count clock,
   AVDD through VMRAMP, its standard-cell phase generator on DVDD. Both are
   the blocks' own drawings through `xschemrc`; `ramp_simple` is checked
   against its deck, `ic_source` by its own checker (88 devices).
2. **vrlo_ref** re-tapped (ADR 0025 / 0018): 33 -> 55 identical strips, tap
   7/55; every other vrlo_ref device unchanged.
3. **Device count:** 301 = v5's 193 - 4 - 33 strips + 2 + 88 + 55 strips; the
   106 nets of the kept devices match v5's one-to-one, no rename; the new
   devices touch only vramp, ramp_rst, vrlo, pbias_r, cnt_clk, avdd_ramp,
   avss, dvdd, dvss. Ports unchanged.
4. **Timeline** (`tb_params.inc`): LSB 6.701613 mV, VR_LO = 7/55 VDD, VR_HI =
   VR_LO + 256 LSB, T0 = 60 us, TOVR = 3 counts; the input positions 16.5 /
   80.5 / 160.5 / 240.5 LSB above VR_LO are v5's.

Record `runs/analog-top/20261030T193110Z` (`./scripts/sim.sh analog-top`,
83/83, typical, 27 C, 3.3 V); the drawings' final spacing
`runs/analog-top/20261030T202020Z` (schematic 32/32, `analog_top.spice`
unchanged).

| Quantity | v5 | v6 |
| --- | --- | --- |
| Codes for positions 16.5 / 80.5 / 160.5 / 240.5 LSB | 17 / 79 / 157 / 235 (5.86 mV) | **17 / 81 / 160 / 239** (6.70 mV) |
| Transfer gain error / offset | -2.60 % / +0.84 LSB | -0.95 % / +0.78 LSB (the I/C source's +0.94 %) |
| Transfer fit residual, max | | 0.063 LSB (gate 0.5) |
| Plate error spread over the cells | 0.038 LSB | 0.038 LSB (gate 0.25) |
| vramp at TR | 0.5024 V | 0.4228 V |
| vrlo at TR vs its tap | | +0.96 mV (gate 11.72 mV) |
| Settled (1 mV) | | vrlo 16.4 us, vramp 19.2 us (T0 60 us) |
| Ramp INL in the macro (best fit / end point) | 0.038 LSB | 0.118 / 0.165 LSB (the comparator-ramp interaction, ADR 0025 allocation 0.30) |
| Armed margin at TR | | 47.2 mV |
| Bottom plates, S1 closing to TSTOP | | 0.52 .. 3.00 V |
| **Power over the ramp** | **780.4 uW** | **811.6 uW** |
| ramp block AVDD (ic_source; v5 ramp_simple_d) | 12.4 uW | 24.2 uW (divider 1.58 + diode 3.26 + pass 2 x 0.55 + OTA 1.4 uA) |
| DVDD (latches; v6 + ic_source's phase generator) | 19.0 uW | 41.6 uW |
| Tracking AVDD | 1456.6 uW | 1466.4 uW |

The xschem testbench reproduces all 258 measures; the op phase records
ic_source's diode XPB (3.256 uA), its pass pair XM1 / XMO (0.5503 uA each,
+0.94 % against C V f) and the ramp MIM (3979.8 fF = 73 x the unit formula).

Not done in v6: corners (typical only; ic_source's own PVT / MC record has
the start-up tail), `cell_trannoise` (step 5, still on ramp_simple_d), PEX.
`ramp_simple_d.sch/.sym/.svg` and `assets/ramp_simple_d.png` are no longer
generated or used.

---

# v5 (archived text): the analog macro with one VDD/2 buffer


Date: 2026-10-13. `../Analog_top_bkp/Analog_top_v4` with the second VDD/2 buffer removed.
v4 is unchanged.

The user asked for one VDD/2 output driving both VREF and the comparators' other
input, with the extra branch removed, the cell recharacterized, and the analog
top updated.

- The cell is `../midrail_ref` (its README).
- Decision record: [ADR 0021](../../docs/decisions/0021-one-vdd2-buffer.md).

## What changed against v4

`check_equiv.py` proves these on every run. It flattens both macros to devices
and matches nets by their (device, terminal) pin sets. Nothing else differs.

1. **One buffer.** `XVBL` (the second `midref_buf`, 12 devices) is gone.
   - The output of `XVREF` is the net `vref`.
   - `vref` reaches every cell's `vref` pin (the S2 track level of the bottom
     plate) **and** its `vbl` pin (the comparator's `inp`).
   - `atop_cell` is unchanged. It keeps both pins; the macro wires both to `vref`.
2. **`bias_gen_s` = bias_gen − XOB + XOL.** XOB sourced `ivbl` into
   XVBL's bias diode, so it goes with XVBL, together with the port `ivbl`.
   - XOL (v4's `ivrlo` output) is unchanged.
   - The sheet is `../bias_gen/bias_gen.sch` with XOB, its pin, wires and
     labels removed and XOL added. `analog_top_sch.py` draws it, and
     `make_refs.py` builds the expected subcircuit from the bias_gen deck.
3. **Device count:** 193 devices = v4's 206 − 12 (`xvbl`) − `xbg.xob`.
   - Every other device has v4's path, model and every parameter.
   - All 138 nets match v4's pin sets with v4's `vbl` and `vref` united.
   - Six nets vanish with the removed devices: `ivbl` and `xvbl`'s internal nets.

The timeline, `tb_params.inc` and the cell are v4's.

## Run

```sh
./scripts/sim.sh analog-top                      # schematic func op xtb pwr (~20 min since v6)
./scripts/sim.sh analog-top PHASES=schematic REGEN=1
```

It needs `make pdk-libs` once, for the standard-cell latch.

| Record | Phases | Result |
| --- | --- | --- |
| `runs/analog-top-v5/20261013T214056Z/metrics.json` | schematic func op xtb pwr | `pass: true`, 56 PASS, 0 FAIL (typical, 27 C, 3.3 V) |

## Functional record (typical), against v4

| Quantity | v4 | v5 |
| --- | --- | --- |
| Codes for mid-codes 16 / 80 / 160 / 240 | 17 / 79 / 157 / 235 | **17 / 79 / 157 / 235** |
| Trip (dout from TR), cells 0..3 | — | +0.000 / +0.094 / +0.054 / +0.022 LSB later |
| Plate error (vramp − vin at the crossing), spread over cells | 0.047 LSB | 0.122 LSB (gate 0.25) |
| VREF at TS1 / TS2 / TS3, from final | −0.78 / −0.68 / −0.34 mV | −0.96 / −0.77 / −0.37 mV |
| vref kick peak in [TS0, TR] | 56.0 mV | 56.4 mV |
| VBL kick peak in [TS0, TR] | 8.2 mV (through the shared tap) | 56.4 mV (it is vref) |
| VBL − VREF at TS0 | 0 (same design, same tap) | 0 by construction |
| Transfer offset / gain error | +0.84 LSB / −2.61 % | +0.88 LSB / −2.61 % |
| Armed margin at TR (smallest bot below vbl) | — | 39.2 mV; no early dout or q |
| **Power over the ramp** | **994.0 uW** | **780.4 uW** (−213.6) |
| refs (divider + buffers) | 380.2 uW | 203.4 uW |
| bias_gen | 101.8 uW | 65.0 uW (no XOB: −11.17 uA) |
| Tracking AVDD | 1670.2 uW | 1456.6 uW |

**Why the trips moved, and why it is harmless.** The vin step at TS_k + 20 ns
lands on the cells still tracking. Their bottom plates hang on `vref` through
S2, so `vref` is kicked, and it is not quite back at the next sample, 20 ns
later.

In v4 the same residual (−0.78 mV) sat on VREF only. VBL recovered on its own
buffer long before the decision.

In v5 the residual is a little larger (−0.96 mV): the node now also carries the
four comparator inputs. It is still sampled into each cell as a per-cell
pedestal. VBL at the decision is back at its level, so this is the plate error's
per-cell offset (reported as `refd_k`). The pedestal calibration removes it.

The spread across cells is 0.122 LSB, inside the 0.25 LSB plate gate. Codes
and order do not change.

**Power.** The ramp-window total drops by 213.6 uW (21.5 %). One buffer
(176.8 uW) and its 11.17 uA bias output (36.8 uW) are gone. The breakdown is
`data/pwr_branches.csv` and `assets/pwr_profile.png`.

## Acceptance (in the checkers)

| Gate | Where | Criterion |
| --- | --- | --- |
| netlist = drawings | `schematic.sh` | `analog_top.spice` byte-equal to what xschem netlists from `analog_top.sch` |
| blocks = decks | `schematic.sh`, `check-schematic.awk`, `make_refs.py` | `midref_div` / `midref_buf` equal `../midrail_ref/midref.spice`; vrlo_ref, switches equal their decks; `ramp_simple_d`, `bias_gen_s`, `comparator_d` equal their block deck with the declared changes; `latch` = its deck |
| clean macro | `schematic.sh` | no RLK / 1e15, no `{param}`; 12 subcircuits, each once |
| = v4 − XVBL − XOB | `check_equiv.py` | as above; no undeclared rename (the tap net is labelled `vmid` as in v4) |
| func | `check-func.awk` | v4's 12 gates (bias, references, vrlo, sample, plate, armed, decision, latch, range, order, transfer, rails) |
| vs v4 | `compare_v4.py` | reported, not gated |
| op | `op_reduce.py` | 1058 measures present, KCL at pb and the comparator tail, one current in the R string, MIM = PDK formula |
| xtb | `check-xtb.awk` | the xschem testbench reproduces all 258 hand-bench measures |
| pwr | `pwr_reduce.py` | ammeters add up to the supply, branches add up to each ammeter |

The `vbl_*` measure names are kept so that the reducer, checker and xtb still
read them. In v5 they measure `v(xdut.vref)`.

## Not done

- **Typical only.** No PVT, mismatch, PEX or transient noise on the macro.
  - v4's `trannoise` phase is not ported; it has no v4 record either.
  - The reference's noise on the shared node is in `../midrail_ref`: 0.037 LSB.
- **Neighbour kick during a hold.** The block bench finds that a neighbour's
  S2 **closing** on the shared node during a hold makes a low-code cell's dout
  fall falsely. The trip after TR is unaffected.
  - The frozen timeline never does this: all cells enter track together and
    only S2 openings happen during holds, which this record covers.
  - A future timeline that re-tracks one cell while others hold must re-check
    this.
- **`bias_gen_s`** was not re-run through bias_gen's 135-cell verify.
  Removing XOB only takes gate load off `pb`.
- **Junction geometry** is still absent on `midref_buf`, `ramp_simple_d`,
  `vrlo_ref`, the switch inverters and XRD (as in v4).
- **Pin list:** `PIN_LIST.md` / `pins.csv` are the conceptual 2026-10-07 list,
  with a v5 note at the top.

## Files

| File | What |
| --- | --- |
| `analog_top_sch.py` | draws `comparator_d`, `ramp_simple_d`, `bias_gen_s` (each derived from its block's drawing), `atop_cell`, `analog_top` and their symbols |
| `make_refs.py` | the expected subcircuits of the three derived cells, from the block decks |
| `check_equiv.py`, `data/v4_ref/` | v5 against the frozen v4 netlist and functional record |
| `tb_analog_top.spice`, `tb_params.inc`, `tb_measure.inc`, `tb_sch.py` | the bench (v4's timeline) and its drawing |
| `func.sh`, `func_reduce.py`, `check-func.awk`, `compare_v4.py`, `plot_func.py` | func phase |
| `op.sh`, `op_devices.py`, `op_bench.py`, `op_reduce.py` | op phase |
| `pwr.sh`, `pwr_bench.py`, `pwr_reduce.py` | pwr phase |
| `schematic.sh`, `sw_*`, `render.sh`, `xtb.sh` | schematic and xtb phases |
| `symbols.py` | function-shaped sub-block symbols (`bias_gen_s` without `ivbl`) |
