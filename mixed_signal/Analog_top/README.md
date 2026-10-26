# Analog_top: the analog macro with one VDD/2 buffer

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
./scripts/sim.sh analog-top                      # schematic func op xtb pwr (~3 min)
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
