# latch: the clocked latch after comparator, from the standard-cell library

Date: 2026-10-10. Replaces `../latch_bkp/cmp_tspc/tspc_dff` (ADR 0014) between
`comparator`'s `dout` and the Gray capture of
`digital/wilkinson_gray_counter`, which stays unchanged. Decision record:
`docs/decisions/0019-standard-cell-clocked-latch.md`.

Labels: **[D]** derived here, **[P]** PDK or library data, **[M]** measured
(a named record), **[A]** assumed or allocated, **[U]** decided by the user.

## 1. What changed and why

- **The user's request [U] (2026-10-10).** Use the PDK's standard-cell flip-flop
  instead of the hand-made TSPC. It must be re-proved that q falls only once,
  must drive the 50 fF load (with a couple of buffer cells if not), must sit
  next to the comparator, and its power is to be measured ("okay, use the
  standard cell" even if it is higher).
- **Library [P].** The frozen digital library is `gf180mcu_as_sc_mcu7t3v3`
  (`docs/PDK_PAD_SUPPLY_FREEZE.md`). The image's `/foss/pdks` has no views of
  it; `make pdk-libs` installs the full library set of the SAME pinned commit
  (`f6eeac7d`) outside the repository (`$HOME/pdks`, mounted read-only at
  `/foss/pdk_libs`), and checks that its ngspice models are byte-identical to
  the image's (`runs/pdk-libs/20261010T113456Z`).
- **The cell [P].** The library has exactly one negative-edge D flip-flop,
  `gf180mcu_as_sc_mcu7t3v3__dfxtn_2`: static master-slave with clocked-inverter
  feedback in both latches, an internal clock inverter pair, and a 2-finger
  output stage; 26 devices, 59.27 um2 (liberty `area`). There is no `dffnq`
  cell here: `dffnq` is the `gf180mcu_fd_sc_*` naming. The SPICE view is the
  library's extracted netlist (drawn S/D geometry, no wiring capacitance).
- **Ports [D].** `latch d clk q vdd vss`, the TSPC's, so it drops into
  `atop_cell` unchanged. Inside: `VNW = vdd`, `VPW = vss`.
- **Placement [U].** One latch per cell, inside `atop_cell` next to its
  comparator, on the digital supply. The 50 fF is the far load (capture-flop
  clock pins and wire); `dout` stays a short local wire into 3.6 fF.

## 2. Requirements (the TSPC's S1-S12, unchanged)

| # | Item | Requirement | Source |
| --- | --- | --- | --- |
| S1 | Sampling edge | the falling edge of the count clock; no clkb at the latch | L2, [U] |
| S2 | Function | q = d at each falling edge, for d moving in either direction in either clock phase; no other q edge | [D] |
| S3 | Load on `dout` | <= 10 fF | L5 |
| S4 | Output | into 50 fF: clock-to-q <= 20 ns; q 90-10 % fall <= 2.15 ns | load [U]; ../latch_bkp/cmp_tspc/SPEC.md S4 |
| S5 | Static levels | q within 1.0 V of its rail in every static state | [U] |
| S6 | Clock edge | S2-S5 hold for clock edges up to 1.0 ns 10-90 % at every corner cell | [A], clock-tree requirement |
| S7 | Near the sampling edge | for any crossing time q falls exactly once, never rises, does not dip towards VDD/2 + 0.3 V before its fall, stays below VDD/2 - 0.3 V after it, and crosses VDD/2 < 75 ns after the deciding edge | [D] (the TSPC's keeper reason) |
| S10 | Kick | code-dependent part of what the latch and its clock do to the decision <= 0.01 LSB | L6 |
| S11 | Supply | the latch on the digital supply | L7 |
| S12 | Comparator in place | with `comparator`, q falls at the first sampling edge after `dout` at every code and phase | [D] |

S8 (hold with the clock stopped high) is met by construction: both latches of
`dfxtn_2` are static [P]. S9 (aperture jitter) was not re-measured; see s.5.

The `d` edge used in every bench is `comparator`'s slowest `dout` fall over
PVT, 10.4 ns 10-90 % [M] (`runs/comparator-updt-v3-pvt/20261007T024232Z`),
plus a 1 ns fast edge for the aperture.

## 3. Buffer: not needed

`bench.py explore` puts three candidates through the drive bench at typical,
ss 0 C 3.0 V, ff 85 C 3.6 V and ss 85 C 3.0 V (`data/explore.csv`):

| Candidate | q 90-10 % fall into 50 fF | clock-to-q (fall) | clocked power, typical |
| --- | --- | --- | --- |
| `dfxtn_2` alone | 0.20 ns typ, 0.27 ns worst (ss 85 C) | 0.49 ns typ, 0.67 ns worst | 6.20 uW |
| + `buff_2` | 0.19 / 0.26 ns | 0.58 / 0.80 ns | 6.20 uW |
| + `buff_4` | 0.13 / 0.18 ns | 0.58 / 0.81 ns | 6.20 uW |

The cell's own output stage (2 x 1.38 / 1.0 um, L 0.28 um) meets the 2.15 ns
limit with 8x margin at the worst cell, so **no buffer** is added [D]. A buffer
would only add delay and area.

## 4. Results (record in RESULTS.md)

- **One fall (S7) [M].** Aperture bench, `d`'s edge bisected onto the decision
  boundary to 1 fs and placed 1e-10 .. 1e-15 s either side: q falls exactly
  once, never rises and stays low in every run, at typical, ss 0 C 3.0 V and
  ff 85 C 3.6 V (slow `d`) and typical (fast `d`). The worst clock-to-q, at the
  boundary itself, is 1.27 ns (ss 0 C); the resolution time constant is
  22-28 ps (TSPC: 1.2 ns, with a 20 ns single fall). The master latch is
  regenerative, so the TSPC's failure mode (a part-charged dynamic node held for
  a half period) does not exist here, and no keeper is needed. Within 1 fs of
  the boundary at ff 85 C q sags by 0.46 V before it falls (3.14 V, far above
  the 2.1 V runt limit): the slave passing the metastable master's level for
  ~0.1 ns. 180 runs in all (`runs/cmp-scff/20261010T185415Z`).
- **Drive (S2-S5) [M].** All four cells: four correct q edges, clock-to-q
  0.44-0.67 ns, q fall 0.19-0.27 ns into 50 fF, load on `dout` 3.55-3.63 fF
  (TSPC 1.9 fF), static levels within 0.3 mV of the rails.
- **Clock edge (S6) [M].** Every edge up to 8 ns (the largest tested) passes at
  all four cells (TSPC: 6 / 8 / 4 ns).
- **Kick (S10, S12) [M].** With `comparator` on the cell's charge path: the
  clock's kick at the sampling edge is -61.5 .. -63.5 ps over codes 4 / 64 /
  128 / 250, so the code-dependent part is 1.0 ps = 2.05e-5 LSB (limit 0.01);
  the common -62.5 ps (1.25e-3 LSB) is pedestal. q fell at the right edge in
  all 32 clock-running runs. `comparator` delay in that bench 21.87 ns with
  `latch`, 21.78 ns with `tspc_dff`, 22.22 ns into the 10 fF it was sized
  for; `dout` fall 5.68 / 5.62 / 5.77 ns.
- **Power [M].** The user's 0.8 uW figure for the TSPC was an estimate. Measured
  on the same drive bench (0.5 ns clock edges, q static):

  | | d high (before the crossing) | d low (after) | leakage |
  | --- | --- | --- | --- |
  | `latch` (dfxtn_2), typical | 6.20 uW | 6.23 uW | 1.6 nA |
  | `tspc_dff`, typical | 2.50 uW | 0.01 uW | 1.3 nA |
  | `latch`, ff 85 C 3.6 V | 9.44 uW | 9.40 uW | 8.7 nA |

  The static flop toggles its internal clock inverters and four clocked
  inverters every cycle whatever d is: about 310 fJ per cycle. The TSPC burns
  power only while d = 1 (its qb glitch) and almost none after the decision.
  In the macro (`Analog_top_v3`, 0.1 ns clock edges, 40 fF q loads) DVDD is
  19.0 uW for four latches against 3.2 uW with the TSPC: +15.8 uW, 1.7 % of
  the macro's 951 uW. The user accepted a higher figure [U].
- **Area [P].** 59.27 um2 per latch (cell boundary, taps excluded). The TSPC
  had no layout.

## 5. What is not covered

- **No VACASK aperture-jitter bench (S9).** The TSPC's was 3.4e-5 LSB against
  0.010. The regenerative static master resolves in ~25 ps, so its noise
  window is no larger. This is an argument, not a measurement.
- **Corners.** Drive and clock edge at four cells, aperture at three, kick at
  typical only. No mismatch, no PEX (the cell netlist is the library's
  extraction without wiring capacitance), no clock-wire coupling to the top
  plate.
- **Layout.** The library cell is placed as a hard cell; the macro has no
  layout yet. The tap rule of the row (`tap_2`) applies when it is placed.
