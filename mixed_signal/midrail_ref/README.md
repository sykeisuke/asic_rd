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
| `data/sizing_v2.json` | midref_v2's sizing record (the bias current is read from it) |
| `data/` | `op_devices.csv`, `op_passives.csv`, `verify_kick.json`, `mc_typ.csv` |
| `run.sh`, `container.sh` | entry point |
