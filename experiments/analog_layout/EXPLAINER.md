# What is on this branch, in plain language

Branch `keisuke/analog-explore` — exploration of analog layout with gdsfactory.
Written 2026-09-12 so the work can be followed without reading the code.

## The three checks every layout must pass

- **DRC** (design-rule check): is every shape manufacturable? Widths, spacings,
  enclosures. Run by KLayout with the frozen PDK's rule deck (`run.sh`). Our
  cells pass except for *minimum-density* rules, which only fail because a tiny
  standalone cell has too little metal — a full chip with fill passes them.
- **LVS** (layout vs. schematic): does the drawn circuit equal the simulated one?
  Magic extracts transistors and capacitors from the GDS; Netgen compares them
  with the SPICE netlist we simulated (`lvs.sh`). "Circuits match uniquely" = yes.
- **PEX** (parasitic extraction): what extra resistance/capacitance does the
  layout add, and does the circuit still perform? (`pex.sh` re-runs the
  sampling-cell testbench with the extracted netlist.)

## What was built (all DRC-clean and LVS-matching)

| File | Block | Devices (same sizes as the simulated schematics) |
| --- | --- | --- |
| `sampling_cell.py` | TG sampling cell + 1 pF hold cap | NMOS 10×1 µm, PMOS 10×2 µm, MIM-B 22.4 µm |
| `sampling_array.py` | 4 cells, shared input, M3 power | 4 × above |
| `tg_switch.py` | generic routed TG (any finger count) | used by the MUX |
| `mux4.py` | 4:1 analog MUX + bus-reset NMOS | NMOS 5×1 / PMOS 5×2, reset L=0.5 |
| `ramp_gen.py` | ramp generator | PMOS W1/L2 source, reset NMOS, 1 pF MIM |
| `comparator.py` | comparator, NMOS- and PMOS-input variants | 9 transistors each |

Supporting pieces:

- `fet_fix.py` — the gdsfactory GF180 plugin's transistors violate the Run 3 DRC
  deck (gate-contact metal pads too small / too close). This wrapper flattens the
  plugin cell, removes its body ring, moves the gate contacts out with compliant
  pads, and redraws the ring's side legs as body taps. Works for any finger
  count and gate length (L = 0.28 … 2 µm, incl. wide gates with several contacts).
- `mim_cap.py` — the plugin's MIM cap is MIM-A only; ours is a MIM-B (Metal4 /
  FuseTop / Via4 / Metal5) drawn per the design manual so Magic recognises it.
- `comparator.py` also contains a **column router**: transistors stacked
  vertically, one vertical metal3 bus per net on the right. Any transistor
  circuit can be laid out this way; the comparator passed on the first run.

## Post-layout result for the sampling cell (2026-09-12)

| Measure | pre-layout | post-layout (PEX) |
| --- | --- | --- |
| acquisition error | 3.20 mV | 3.45 mV |
| clock feedthrough | 5.09 mV | 9.32 mV |
| hold droop (30→75 ns) | 0.07 µV | 0.20 mV (to be investigated) |

Extracted parasitics: 15 C, 15 R; the hold node carries 17.5 fF (1.7 % of the
1 pF cap); input↔hold coupling 3.4 fF. Feedthrough nearly doubles — the first
layout-driven number in the project and a real design input (larger hold cap,
dummy switch, or layout symmetry are the usual remedies).

## How to reproduce

```sh
make tools                                                     # once
experiments/analog_layout/run.sh experiments/analog_layout/sampling_cell.py sampling_cell_tg   # DRC
experiments/analog_layout/lvs.sh work/sampling_cell_tg.gds sampling_cell_tg sampling_cell_tg_sch.spice
experiments/analog_layout/pex.sh                                # PEX + pre/post comparison
```

## Open items

- Density rules need fill at chip level; not a cell-level problem.
- Hold droop in the PEX run looks too large — check the extracted MIM model /
  substrate nodes before trusting it.
- Assembling the blocks into one analog macro (with LEF for LibreLane), the
  test-access MUX (truth table not frozen), and chip-top integration remain.
- Transient-noise simulation: VACASK is in the container but its GF180 support
  (`gf180tovc.py`) is only in newer upstream versions — see the project notes.
