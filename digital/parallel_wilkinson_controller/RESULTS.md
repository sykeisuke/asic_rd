# Parallel controller results

Date: 2026-11-03 (Analog_top v7 interface: `acq` instead of the twelve
switch controls; the 2026-10-28 version with delay lines mapped to 585
cells / 19140 um^2 inside the digital top, the asynchronous Gray-capture
version of 2026-09-18 to 437 cells / 14883.5 um^2 at 5 V)

Self-checking RTL simulation (Icarus, 20 MHz) with the macro's sequencer
modelled as a token chain on the rising edge (cell k's S2 opens at the k-th
edge after the edge that sees `acq` low) and the cell latch as a
negative-edge flop on `q <= dout`, four conversions:

1. Analog_top's functional record: comparators deciding just after
   16.5 / 80.5 / 160.5 / 240.5 counts give codes 17 / 81 / 161 / 241
   (the latch rule `floor((t_qfall - TR) / TCOUNT)`);
2. decisions 10 ns before and after a falling clock edge (codes 20 and 21),
   two equal codes, and an early one;
3. one cell never crossing: 255 and `timeout = 0100`, the others kept;
4. decisions in the last count (255) and the first (0).

Each run also checks `acq`: exactly one fall and one rise per conversion,
the fall within 1 ns after a rising edge (so the next edge is TS_0), the
four S2 openings one clock apart from there, `ramp_rst` falling 6 clocks
after S2 of cell 3, `acq` rising only after the ramp is reset, and the
cells back in track after `done`.

GF180 `gf180mcu_as_sc_mcu7t3v3` mapping (pre-placement): 233 cells /
8991.5 um^2 standalone, 236 cells / 9123.3 um^2 inside the digital top (no
kept delay stages any more).
