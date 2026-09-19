# Bottom-plate sampling cell (54.5 fF, GF180 3.3 V devices)

Transistor-level study of the Tape-out 1 storage cell after the 2026-09-18
decisions: **54.5 fF hold capacitor** (smallest drawable MIM), **bottom-plate
sampling** (the capacitor switch at a fixed potential opens first), and the
**ramp applied to the capacitor** so that every per-cell comparator trips at
a fixed reference instead of comparing two moving inputs.

The testbench sweeps the sampled level over 0.5-2.0 V with an ideal 20 MHz /
8-bit ramp (1.5 V in 12.8 us), minimum-width transmission gates, and lumped
parasitics (3 fF on each capacitor node, standing in for the comparator input
and switch junctions), and reports for each level:

- the crossing time and the derived code;
- the input-referred pedestal (charge injection + feedthrough) after removing
  the fitted gain;
- the gain relative to the ideal slope and the linearity (max residual from a
  straight line).

Three variants are run, because *which plate is sensed* turns out to decide
whether bottom-plate sampling delivers its promise:

| Variant | Ramp on | Comparator senses | Switch order |
| --- | --- | --- | --- |
| A | bottom plate | top node (VIN side) | bottom switch first |
| B | bottom plate | top node | top switch first (conventional) |
| **C (recommended)** | **top node** | **bottom plate (frozen first)** | bottom switch first |

Acceptance (provisional, applied to variant C): monotonic codes, linearity
<= 0.25 LSB, input-referred pedestal spread over the input range <= 2 mV.

```sh
make bottom-plate-cell
```

Outputs: `work/*_summary.txt` (one per variant), `work/*.csv` waveforms at
VIN = 1.2 V. Results and interpretation: [`RESULTS.md`](RESULTS.md).
