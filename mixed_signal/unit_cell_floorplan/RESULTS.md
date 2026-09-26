# Unit cell floorplan, MIM over against MOM beside: results

Date: 2026-09-18 (third revision: cells rebuilt around comparators sized
INTO their own hold capacitor, `../comparator_unit_cell`; second revision
2026-09-17 moved to the DCIC layout method; first version was a dense
placement)

Tool environment: IIC-OSIC-TOOLS 2026.07, GF180MCU `gf180mcuD` (5LM, 11K top
metal, MIM option B), gdsfactory 9.40.2 with the pinned `gf180mcu` 1.0.0
plugin for the transistor generator, KLayout `gf180mcu.drc` at variant
`gf180mcuD`, `run_mode=deep`, density decks reported and not judged.

Run: `./run.sh` -> `work/floorplan.txt`, fourteen checks, all PASS. Layouts
in `physical/final_views/gds/UC_*.gds`, renders under `render/`, annotated
floorplans under `svg/`, the comparison page `report.html`.
`drc_devices.py` runs every transistor primitive through the deck on its
own. The comparator sizings and their bench come from
`../comparator_unit_cell` (its RESULTS.md has the electrical story).

## 0. What is being designed, and against which spec

The project replicates the IRSX signal path -- a switched-capacitor sampling
array in which every storage cell carries its own comparator and one
Wilkinson ramp converts all cells in parallel -- scaled down for a first
tape-out and meant to grow back to the IRSX class:

| | Tape-out 1 as frozen | Studied here (8-bit retarget) | IRSX-class target |
| --- | --- | --- | --- |
| Resolution | 6 bit | **8 bit**, 1 LSB = 5.859 mV | **12 bit**, 1 LSB = 366 uV |
| Input range | 0.4-1.6 V | **0.5-2.0 V** (the IRSX conversion window) | same |
| Sampling rate | 25 MSa/s | **25 MSa/s baseline; 100 MHz is the most the 8-bit cell holds**; 200 MHz drawn | **multi-GSa/s (2.2 GSa/s quoted)**, 500 MHz bandwidth |
| Storage cell | 4 cells behind a mux | **comparator per cell, no mux** | 128+ cells x 8 channels |
| Hold capacitor | 1 pF | **smallest that works**: MIM floor 54.5 fF or MOM 15.6 fF | 125 fF for kT/C <= 1/2 LSB12 |
| Comparator | shared, sized into 1 pF | **re-sized into the cell's capacitor** (this revision) | a 12-bit per-cell design |

Sources: `docs/PROTOTYPE_SPECIFICATION.md` §12, `docs/EIGHT_BIT_RETARGET.md`,
`simulations/gf180_sampling_unit_cell` (125 fF is the smallest grid point
that carries to 12 bits), `mixed_signal/comparator` (the recorded
comparator), `../comparator_unit_cell` (the re-sized ones).

## 1. The answer

| | `UC_MIM` | `UC_MOM` | `UC_MIM_125` | `UC_MOM_125` |
| --- | ---: | ---: | ---: | ---: |
| Comparator (sized into) | `mim55` (54.5 fF) | `mom16` (17 fF) | `mim125` (125 fF) | `mim125` |
| Hold capacitor | 5 x 5 um MIM, **54.5 fF** | 1 `MOMU`, **15.6 fF** | 7.69 um MIM, **125 fF** | 8 `MOMU`, **125 fF** |
| Hold node incl. the pair's gate | 72.7 fF | **35.2 fF** | 141 fF | 152 fF |
| Where | over TAIL A/B, M4/FuseTop/M5 | band under the p-well row, M1-M4 | over TAIL A/B, inside the PMOS block | band under the p-well row |
| Capacitor silicon | **0** | 27.5 um² + its band | **0** | 219.6 um² + its band |
| M4/M5 footprint incl. keep-out | 77.9 um² | none | 132.7 um² | none |
| Switch WN/WP, 200 MHz, 8 b, on the node | 0.52 / 1.04 um | 0.25 / 0.50 um | 1.00 / 2.00 um | 1.00 / 2.00 um |
| Device area, 10 transistors + 4 dummies | 273.9 um² | 272.8 um² | 267.5 um² | 267.5 um² |
| **Cell, PR boundary** | **22.10 x 28.36 = 626.8 um²** | **22.14 x 34.02 = 753.2 um²** | **22.34 x 27.50 = 614.4 um²** | **23.74 x 38.82 = 921.6 um²** |
| Same cell around the 1 pF-sized `cmp_p5t_8b` (rev. 2) | 715.7 | 734.8 | 715.7 | 1047.8 |
| MOM / MIM | | **1.20** (+126 um²) | | **1.50** (+307 um²) |
| Bench, calibrated residual of the comparator on this node | 0.44 LSB8 (`cmp_p5t_8b` on the same cap: 0.067) | 0.47 (0.085) | 0.16 (0.059) | -- |
| DRC, `gf180mcu.drc` minus density | **0** | **0** | **0** | **0** |

Five things the table says:

1. **The smaller comparator shrinks the cell 12 % and takes the MOM's free
   ride with it.** Around the 1 pF-sized comparator the MOM fit in the
   p-well row's spare width; around `mom16` the mirror row (10 fingers of
   4.28 um plus dummies, 14.1 um) is the widest thing in the cell, so the
   MOM gets a band of its own and costs 126 um², 20 %. The MIM is free in
   every version, at 54.5 and at 125 fF: both lie inside the PMOS block's
   outline.
2. **The comparator's gate is itself a hold capacitor.** The `mom16` pair's
   Cgg is 18 fF, on a 17 fF MOM: the "15 fF cell" is a 35 fF node, and its
   switch (0.25 um) and kT/C follow the sum. With the recorded comparator's
   45 fF the same MOM cell is a 62 fF node. Any capacitor comparison at this
   scale is a comparison of C_cap + C_in.
3. **Smaller is electrically worse here.** `../comparator_unit_cell` measured
   the re-sized comparators on the mux-free bench: 2.6-2.9x less kickback,
   2.3-4.5x more delay spread, and after the per-cell straight-line
   calibration 0.44-0.47 LSB8 of residual and three codes of error where the
   1 pF-sized `cmp_p5t_8b` leaves 0.06-0.085 LSB8 and one code on the same
   capacitors. Kickback is mostly a constant plus a 0.3 % gain error, which
   the calibration removes; delay spread is INL, which it does not. The 90 um²
   the resize saves buys nothing the cell can use.
4. **At the 12-bit capacitor the MIM wins on area outright.** Eight MOM
   units add 307 um², 50 %, in two abutted rows under the p-well block; the
   125 fF MIM grows over the tail and the cell is the smallest of the four.
5. **The switch follows the node, not the capacitor, and never the
   floorplan.** 0.25 / 0.52 / 1.00 um at 200 MHz on the three nodes; all
   0.22 um at 25 MHz. Its area is under 1 % of any cell.

## 2. Why the transistors are the size they are

Every transistor in these cells comes from `comparator/size_p5t.py`, the
gm/Id design-space tool that produced the recorded `cmp_p5t_8b`, run by
path and unmodified by `../comparator_unit_cell/size_uc.py` with one input
changed: the kickback budget expressed as charge on the cell's own
capacitor. The tool's kick proxy is calibrated to the reference design's
measured kick into 1 pF, so the hold capacitance cancels out of the proxy;
sizing into 17-125 fF is `KICK_BUDGET = 1.465 mV x C_hold / 1 pF`.

| Sized into | Input pair | Mirror load | Tail | Bias | C_in | Predicted kick into C_hold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 17 fF, `mom16` | 12.4 um / 0.4, nf 3, gm/Id 18.7 | 21.4 um / 0.6, nf 5, gm/Id 22.1 | 49.6 um / 1.0, nf 12 | 2.31 uA, I_REF 1.87 uA, 2.48:1 | 18.1 fF | 28.3 mV = 4.8 LSB |
| 54.5 fF, `mim55` | same | same | same | same | 18.1 fF | 8.85 mV = 1.5 LSB |
| 125 fF, `mim125` | 8.9 um / 0.5, nf 2, gm/Id 16.7 | 4.5 um / 0.5, nf 1, gm/Id 18.6 | 74.1 um / 1.0, nf 19 | 2.30 uA, I_REF 1.24 uA, 3.70:1 | 15.9 fF | 3.89 mV = 0.66 LSB |
| 1 pF, recorded `cmp_p5t_8b` | 30.8 um / 0.5, nf 8, gm/Id 17.5 | 12.4 um / 0.5, nf 3, gm/Id 18.6 | 90.5 um / 1.0, nf 20 | 6.30 uA, I_REF 2.78 uA, 4.52:1 | about 45 fF | 1.59 mV into 1 pF |

Why each value came out as it did:

- **The tool found no feasible design at any capacitor** and fell back to
  its minimax rule -- the design whose worst budget ratio is smallest: 19x
  on kick at 17 fF, 6x on kick at 54.5 fF, 2.8x on spread at 125 fF.
  Kickback is proportional to W_in and delay spread to 1/(W_in x I_D/W): the
  pair's width serves the two budgeted terms in opposite directions, so the
  topology has no feasible point. That was already the recorded design's
  finding at 1 pF (1.9x); the small capacitors make it 3-10x worse.
- **At 17 and 54.5 fF the pair went to the matching floor and stopped.**
  12.4 um at L = 0.4 um is the narrowest device that satisfies the tool's
  4 um² gate-area floor (`WL_MIN_IN`, sizing practice against Vth mismatch)
  at the shortest L in its grid, where I_D/W is highest and the width for a
  given current smallest. Both capacitors get the same design because once
  kick dominates the minimax, its argmin does not depend on the budget's
  scale. The kick-charge floor of this topology is about 0.45 fC: 8 mV on
  54.5 fF, 5.5x the budget before anything else is considered.
- **The mirror load went wide (21.4 um, gm/Id 22) at 17-54.5 fF**: a higher
  (gm/Id)_load lowers the diode-node swing that Cgd couples onto the hold
  node, the second kick lever, at the price of C_outa and speed. The bench
  exposed the price: 131 ns of delay spread against 42 ns predicted; the
  tool's spread model was validated only up to (gm/Id)_load of 19.
- **At 125 fF** the kick ratio no longer dominates and the minimax moves to
  a balanced design: L = 0.5, a small load (4.5 um), a longer tail at lower
  I_REF; measured 0.69 LSB of kick and 0.16 LSB of calibrated residual.
- **Finger counts** are the tool's `nf = clip(round(W / 4 um), 1, 20)`: a
  4 um finger, DCIC's "a few um". The tail is drawn as two halves of the
  same finger (6 + 6, 10 + 9). **BUF2**'s nf = 1 is hard-coded in the tool
  and its width follows the sampled inverter ratio (9.9 and 7.57 um here);
  a single 9.9 um finger is a 10 um tall device, so the floorplan fingers it
  with the same 4 um rule -- a named layout liberty. BUF1/3/4 (4/8/16 um,
  nf 4) are inherited unchanged from the first Wilkinson slice.
- **Branch currents fell to 2.3 uA** because at fixed gm/Id a narrower device
  carries less current; the tail followed as a mirror ratio, so the bias
  reference (`mixed_signal/bias_reference`, 2.78 uA into a 20 um diode leg)
  would be re-sized with it. Measured cell power did not fall (125 uW
  against 83 uW): the slow decision and the skewed first inverter dominate.

## 3. The floorplan, and where each rule comes from

Section 4.5 of Pretl's *Design of Complex ICs* (iic-jku.github.io/design-complex-ic).
Rule, then what was done:

| DCIC | In this floorplan |
| --- | --- |
| 4.5.1 "split ... into multiple parallel devices (fingers) ... of limited length (a few um)" | the tool's 4 um fingers, kept; BUF2 fingered by the same rule |
| 4.5.2 "constructed from identical unit devices ... of equal width (and equal L)" | INP/INN one diffusion row of identical fingers; LOADD/LOADM likewise |
| "same direction ... avoid mirroring" | every finger vertical, current top to bottom; tail halves stacked, not mirrored |
| "surrounded by similar structures ... spend dummy elements (fig. 50)" | one dummy finger at each end of the pair and of the mirror, own tie pad |
| "share the centre source diffusion ... differential pair or current mirror" | the pair's tail node and the mirror's vss are the shared diffusions |
| "common-centroid arrangements (fig. 52 b, linear ABBA)" | pair `D ABBAAB D` (odd counts get the closest mirror-symmetric order), A gates on a top bar, B gates on a bottom bar; the mirror shares one gate net, its A/B split is in the drain straps |
| "avoid low-level metal routing over sensitive devices" | the MIM over the tail, never over the pair |
| 4.5.3 pins, supplies, wiring channels | input left (TG N under TG P), output right (BUF2/BUF4 over BUF1/BUF3), `ramp` to the pair's right end, `pbias` from the top; VDD rail on the n-well ring, VSS rail on the p-well ring; 2 um channel between the wells |
| 4.3.4 MOM lower metals / MIM density | MOMU as characterized (M1-M4); MIM 2.0 fF/um² against 0.57 |

```text
                       VDD rail on the n-well ring
   +-------------------------------------------------------+
   |        TAIL half B  6 x 4.13u / 1.0            | BUF2 |  n-well
   | TG P   TAIL half A  6 x 4.13u / 1.0                   |  one ring
   |        INP/INN  D A B B A A B D          | BUF4       |  bulk vdd
   +-------------------------------------------------------+
   . . . . . wiring channel 2.1 um: outa, left, tail, pbias . .
   +-------------------------------------------------------+
   | TG N   LOADD/LOADM  D A B A B A B A B A B D   | BUF1 |  p-well
   |                                               | BUF3 |  one ring
   |        [ MOMU 5.3 x 5.2, UC_MOM only ]                |  bulk vss
   +-------------------------------------------------------+
                       VSS rail on the p-well ring
   <- vin, clk_sample                          dout, ramp ->
```

With the small comparator the mirror row is the widest row, so the cell is
width-limited by the p-well block and the MOM's two candidate spots are
compared by the area they add (beside the buffer NMOS, or a band under the
row); the cheaper one is taken and recorded (`mom_spot`). History of the
cell: dense placement of the 1 pF-sized comparator, no matching rules,
615 um²; DCIC rules around the same comparator, 716 um² (+16 %); DCIC rules
around the comparator sized into its capacitor, 627 um² for the MIM cell --
smaller, and electrically worse.

## 4. Switch sizing, for the record

`tau = (T_track - T_edge) / ((N+1) ln 2)`, `Ron_max = tau / C_node`,
`WN = 2710 ohm.um / Ron_max` (measured worst case over 0.5-2.0 V), `WP = 2 WN`,
clamp at 0.22 um; C_node = C_hold + Cgg of the input pair.

| Node | C_hold + C_in = C_node | 8 b 25 MHz | 8 b 100 MHz | 8 b 200 MHz (drawn) | 12 b 200 MHz | 500 MHz bandwidth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MOM, `mom16` | 17.0 + 18.1 = 35.2 fF | 0.22* | 0.22* | **0.25** | 0.36 | 0.30 |
| MIM 54.5 fF, `mim55` | 54.5 + 18.1 = 72.7 fF | 0.22* | 0.26 | **0.52** | 0.74 | 0.62 |
| MIM 125 fF, `mim125` | 125 + 15.9 = 140.9 fF | 0.22* | 0.49 | **1.00** | 1.44 | 1.20 |

WN in um, `*` clamped. At 2.2 GSa/s half-period settling would ask for 2-7 um
gates whose injection the sampling study already ruled out at 200 MHz; a
GSa/s cell tracks over a long write window (IRSX) and is sized to bandwidth.

## 5. Does the cell carry to 12 bits and 2.2 GSa/s?

| Term | 8 bits, 25-100 MHz (now) | 12 bits, GSa/s (target) |
| --- | --- | --- |
| kT/C on C_hold | irrelevant (<= 0.09 LSB8) | 15.6 fF 1.41 LSB12; 54.5 fF 0.75; **125 fF 0.50** |
| Capacitor area | MOM +20 %, MIM 0 | **MIM 0, MOM +50 %** |
| Switch | 0.22-0.52 um on the node | bandwidth-sized 0.3-1.2 um, write-window timing |
| Comparator | the 1 pF-sized 5T: 0.06-0.09 LSB8 calibrated residual on 17-125 fF; the re-sized one 0.16-0.47 | a 12-bit per-cell comparator is a different design; a source follower in front of the pair removes the kick-charge floor; rows and channel carry over, widths will not |
| Array | -- | 128 x 8 x 83 uW = 85 mW of comparators; power gating or a lower tail current |
| Upper metals | MIM takes 78-133 um² of M4/M5 per cell, both plates out through M5 (MIMTM.10) | array buses route around a MIM per cell; MOM leaves M5 free |

Verdict for the IRSX-class cell: **MIM, 125 fF, over the tail, with the
comparator selected on kick span and delay spread rather than absolute
kick** -- which today means the 1 pF-sized `cmp_p5t_8b`, not the re-sized
ones.

## 6. What had to be fixed to reach zero violations

All inside the PDK's transistor generator or placement collisions; all
handled in `floorplan.py`, and `drc_devices.py` now checks every primitive
standalone:

| Rule | Cause | Fix |
| --- | --- | --- |
| `M1.3`, `M1.2a` | generator's poly-contact M1 caps under the minimum area, and 0.175 um from S/D M1 at L = 0.28 | gate bars (poly, contacts, M1) drawn here, 0.24 um clear of the active |
| `M1.3` on the switch | S/D pads on a 0.22-0.52 um finger under 0.1444 um² | stretched to 0.15 um² |
| `*_OFFGRID` | 2.5 nm bbox half-extent moved instances off the 5 nm grid | every move snapped |
| `CO.4` | ring size on the 5 nm grid, one bar 0.065 um over its contacts | ring sizes a multiple of 10 nm |
| `PL.3a` | on the ABBA pair, the other net's poly ends 0.085 um from a gate bar | two-bar devices place bars 0.40 um clear |
| `CO.1/3/7`, `NP.5a`, `PL.4_LV` | with the small comparator the mirror row is wider than the pair row and the switch NMOS, placed under the switch PMOS, landed on the mirror | TG N stands clear of the mirror as well |

The plugin's `cap_mim` draws the MIM-A stack on M2/M3 whatever its arguments
say; the MIM is drawn from the `MIMTM` rules (`work/mim_rules.md`).

## 7. Open

- **No routing.** Placement, wells, rings and gate bars only; the areas are
  floors.
- **Re-state the sizing objective** as kick span + delay spread and re-run;
  `size_p5t.py` computes everything needed except the span. Own block.
- **Topology**: a source follower between the hold node and the pair
  (`sfbuf`) removes the 0.45 fC kick floor; one more PMOS row in the
  floorplan.
- **Bias reference**: the re-sized designs want 1.24-1.87 uA into the 20 um
  diode leg; `bias_reference` was sized for 2.78 uA.
- **LVS** needs a routed netlist; the MIM's device recognition needs its
  `MIM_L_MK` checked; the MOM has no device.
- **The p-well row limits the width** with the small comparator; a 2 x 6
  mirror arrangement would trade height for width. Not explored.
