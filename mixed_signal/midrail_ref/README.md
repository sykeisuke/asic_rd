# midrail_ref: one VDD/2 buffer for VREF and VBL

On 2026-10-13 the user asked for **one output** to drive both VREF and the
comparators' other input (VBL), with the extra branch removed and the cell
recharacterized.

`../midrail_ref_bkp/midrail_ref_v2` (ADR 0016) had one divider and two `midref_buf`: one buffer
for VREF and one for VBL. `midref` keeps the divider and **one** buffer,
device for device. `../midrail_ref_bkp/midrail_ref_v2` is untouched.

```sh
./scripts/sim.sh midrail-ref                         # verify + schematic (~6 min)
./scripts/sim.sh midrail-ref VPHASES='op cmp'        # some verify phases only
```

Decision record: [ADR 0021](../../docs/decisions/0021-one-vdd2-buffer.md). The
macro on it is `../Analog_top`.

Labels: **U** user, **C** contract, **B** noise budget, **M** measured,
**D** derived, **A** assumed, **P** PDK.

## 1. What changed, and what did not

| Item | v2 | v3 |
| --- | --- | --- |
| Buffers | 2 × `midref_buf` on one shared tap | **1** × `midref_buf` |
| Outputs | VREF, VBL (two nodes) | **one** node: VREF = VBL |
| Bias | 2 × 12.36 uA (ideal) | 1 × 12.36 uA |
| Devices | `midref_div` + `midref_buf` | the same subcircuits, every device and size unchanged |
| Power (typical, whole reference, ideal ib) | 494 uW | **260.3 uW** [M] |
| Area (v2 README rules) | 680 um² | **441 um²** (MOS 102.8, poly 182, MIM 156.5) [P] |

**Why the sizing was not redone.** v2's power is set by follower headroom at
ff/85 °C/3.6 V (v2 README §3), not by the load. Settling (16 ns worst against
250 ns) and noise (0.037 against 0.080 LSB) keep their margins with one buffer
driving both. A smaller buffer would not be cheaper.

`midref.spice` holds `midref_div`, `midref_buf` and the bench wrapper
`midref (out ib vdd vss)`: the divider plus the one buffer.

## 2. What the shared node changes, and how each is checked

| Effect | v2 | v3 check |
| --- | --- | --- |
| VBL − VREF offset (pedestal) | σ = √2 × one buffer = 1.35 LSB | **0 by construction**. The buffer offset only moves VDD/2, the common level of plate and comparator: gated on \|mean\| + 3σ ≤ 50 mV |
| VBL crosstalk from VREF's S2 kick | separate node, ≤ 0.5 µV at 250 ns | no object (one node). Replaced by the held-cell check below |
| Noise VBL(decision) − VREF(TS) | device noise independent in the two buffers | one node: the noise below ~1/T_DEC is common to sample and decision and cancels |
| A neighbour's S2 event while a cell holds | landed on VREF only | lands on that cell's comparator inp: `tb_cmp.spice` |

## 3. Verification (verify_v3.py, schematic.sh)

Record: `runs/midref-v3/20261013T213457Z/metrics.json`, **pass**. Typical
unless named; ideal bias current 12.36 uA.

| Gate | Result | Limit |
| --- | --- | --- |
| Follower headroom, 45 PVT cells + 0.69x / 1.77x bias | worst +0.071 V (M4, ff/85 °C/3.6 V) | ≥ 0 |
| IB sources / output diodes headroom | +1.033 V / +0.591 V | ≥ 0 |
| VDD/2 error, 45 cells | worst −8.58 mV (fs/85 °C/3.6 V) | ≤ 50 mV |
| S2 kick, 47 cells × 2 cases | back within ½ LSB in ≤ 16 ns; residual ≤ 0.001 mV at 250/300 ns; peak up to 199 mV | ≤ 250 ns, ≤ 2.93 mV |
| Noise VBL(decision) − VREF(TS), typical / ss85 3.0 / ff0 3.6 | 0.0369 / 0.0369 / 0.0375 LSB | ≤ 0.080 LSB |
| Decision with `comparator` on the shared node | trip shift +0.0004 LSB against an ideal node | ≤ 0.05 LSB |
| Node in the 200 ns before the trip | within 0.3 µV | ≤ ¼ LSB |
| A neighbour's S2 **closing** 50 ns into the hold (both directions), mid code 33.6 LSB / low code 2 LSB | trip moves ≤ 0.0019 / ≤ 0.0000 LSB | ≤ ¼ LSB (v2's crosstalk bound, carried over) [C] |
| MC typical, 200 draws, reproducible | output σ 4.25 mV, mean −4.31 mV, \|mean\| + 3σ 17.1 mV; with the worst PVT error 21.4 mV | ≤ 50 mV [A] |
| MC ff/85/3.6, ss/0/3.0 | \|mean\| + 3σ 20.3 / 14.7 mV | ≤ 50 mV |
| Schematic | `midref_buf.sch` (12) and `midref_div.sch` (3) netlist to `midref.spice` | exact |

**Cross-check.** From the same spectra, the noise of v2's wiring (two buffers
on one tap) reads 0.0386 LSB. That is v2's recorded figure.

**Reported, not gated:**
- Shunts M3/M6 reach −0.135 V at typical/3.0 V/1.77x bias: in triode, as allowed.
- Under mismatch at ff/85/3.6 the followers stay saturated in 197 of 200 draws
  (worst −0.012 V); as in v2.
- **Finding: a neighbour's S2 closing during a hold.** It puts a 168–189 mV
  peak on the shared node.
  - At a **low code (2 LSB)** the sourcing case makes the held cell's dout
    **fall falsely during the hold**. The trip after TR is unchanged. At 33.6
    LSB dout stays high.
  - With two buffers, VBL only saw ~20 mV of such an event (through the tap).
  - **The frozen timeline never does this.** All four cells enter track
    together, before any sample. During a hold the only S2 events are the
    later cells' S2 *openings* (charge injection). `../Analog_top`'s record
    covers those: no early dout or q, armed margin 39 mV.
  - So this is a **timeline constraint** of the shared node: no cell may
    re-enter track (close S2) while another cell holds a low code.

### 3.1 Drawings (tb_sch.py, xtb.py)

The block's xschem views are the two cell sheets and five testbench
drawings, all generated (no hand edits), checked by `schematic.sh`
(`./scripts/sim.sh midrail-ref PHASES=schematic`, ~4 min):

| Drawing | Bench it draws | Fixed at | Proven by |
| --- | --- | --- | --- |
| `midref_buf.sch`, `midref_div.sch` (+ `.sym`) | the cells of `midref.spice` | - | netlist back to the deck device for device, ports in order |
| `tb_op.sch` | `tb_op.spice` | typical / 27 �C, VDD looped 3.0 / 3.3 / 3.6 V | 48 OP / OPX figures equal |
| `tb_kick.sch` | `tb_kick.spice` | typical / 27 �C / 3.3 V, both S2 charge directions | 12 figures equal (peak, residuals, charge, return to � LSB) |
| `tb_cmp.sch` | `tb_cmp.spice` run A | buffer drives the node, VDROP 0.15 V, no neighbour | td and v0: exact with the comparator's S/D geometry stripped; as drawn td +0.54 ns (gate 1 ns) |
| `tb_mc.sch` | `tb_mc.spice` **and** `tb_mchr.spice` | one mismatch draw, `.options seed` 20261008 | the MC line and the HR line of the same draw equal |
| `tb_noise.sch` | `tb_noise.spice` | typical / 27 �C / 3.3 V, 10 Hz-1 GHz | the integrated figures and the spectrum at four frequencies equal |

The DUT on every testbench is `midref_div.sym` + `midref_buf.sym` wired as
the wrapper `midref` (XD, XB); xschem descends into the cell sheets, so the
testbench exercises the drawings. `tb_cmp.sch` places `comparator.sym` from
`../comparator` (through this folder's `xschemrc`), netlisted from the
comparator's own drawing, which carries the PDK symbols' S/D junction
geometry: `xtb.py` therefore runs that netlist twice (geometry stripped,
gated as the others; as drawn, gated at 1 ns on td). `xtb.py` first checks
that each netlist carries exactly the bench's instances (name, nodes, model:
xschem silently drops an instance whose symbol it cannot find), then
simulates the xschem netlist and the hand bench at the same nominal case
and compares (1e-6 relative, or 10 �V / 10 ps / 10 pA / 10 zC absolute).
`midref_sch.py` emits the cell devices in the deck's order so the PDK's
mismatch draws land on the same devices in both netlists. Table:
`data/xtb.csv`; renders `assets/tb_*.png`. Record: `runs/midrail-ref/20261031T022615Z/metrics.json`, **pass** (24 PASS, 0 FAIL).

## 4. Not covered

- The bias generator. In `../Analog_top` `bias_gen_s` gives 11.17 uA =
  0.90x; the 0.69x / 1.77x span covers its PVT spread.
- Divider ratio mismatch: the `ppolyf_u_3k` model has global variation only.
- PEX and layout; VACASK transient noise.
- The settling after all four cells' S2 close at once (the start of tracking).
  v2's one-cell kick gate is kept; the four-cell event was on VREF in v2 too.

## 5. Files

| File | Contents |
| --- | --- |
| `midref.spice` | `midref_div`, `midref_buf` (= midref_v2's), `midref` wrapper |
| `bench.py` | constants and bench helpers (midref_v2's values; one-node noise) |
| `verify_v3.py` | op, opdev, kick, noise, cmp, mc, mchr |
| `tb_op`, `tb_kick`, `tb_noise`, `tb_cmp`, `tb_mc`, `tb_mchr` `.spice` | bench templates (one buffer) |
| `midref_sch.py`, `schematic.sh`, `check-schematic.awk` | drawings from the netlist and their netlist check |
| `midref_buf.sch/.sym`, `midref_div.sch/.sym` | the xschem views; `assets/*.png` |
| `tb_sch.py`, `xtb.py`, `xschemrc` | testbench drawings `tb_op/kick/cmp/mc/noise.sch`, their netlist check and simulation against the hand benches (`data/xtb.csv`) |
| `data/sizing_v2.json` | midref_v2's sizing record (the bias current is read from it) |
| `data/` | `op_devices.csv`, `op_passives.csv`, `verify_kick.json`, `mc_typ.csv` |
| `run.sh`, `container.sh` | entry point |
