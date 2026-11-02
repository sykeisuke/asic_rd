# Parallel controller results

Date: 2026-10-28 (Analog_top interface; the asynchronous Gray-capture
version of 2026-09-18 mapped to 437 cells / 14883.5 um^2 at 5 V)

Self-checking RTL simulation (Icarus, 20 MHz) with the cell latch modelled
as a negative-edge flop on `q <= dout`, four conversions:

1. Analog_top's functional record: comparators deciding just after
   16.5 / 80.5 / 160.5 / 240.5 counts give codes 17 / 81 / 161 / 241
   (the latch rule `floor((t_qfall - TR) / TCOUNT)`);
2. decisions 10 ns before and after a falling clock edge (codes 20 and 21),
   two equal codes, and an early one;
3. one cell never crossing: 255 and `timeout = 0100`, the others kept;
4. decisions in the last count (255) and the first (0).

Each run also checks the sampling sequence: `s2` edges one clock apart,
`s0` opening 4-6 ns after `s2`, `s1` closing 9-11 ns after `s2`, `ramp_rst`
falling 6 clocks after `s2[3]`, and the return to track after `done`.

GF180 `gf180mcu_as_sc_mcu7t3v3` mapping (pre-placement, inside the digital
top): 585 cells / 19140 um^2, of which 148 are the kept `dlybuff_2` delay
stages (4 cells x (12 + 25)).
