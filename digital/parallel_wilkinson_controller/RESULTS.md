# Parallel controller results

Date: 2026-10-09 (synchronous capture; the asynchronous Gray-capture version
of 2026-09-18 mapped to 437 cells / 14883.5 um^2)

Self-checking RTL simulation (Icarus, 20 MHz conversion clock; the testbench
models the cell latch, raising each flag at the edge that ends the crossing
cycle) passes five conversions:

1. codes `16, 20, 27, 35` on the four cells simultaneously;
2. two equal codes plus a near-full-scale code (`200, 200, 3, 254`);
3. one cell never crossing: code saturates to `255`, `timeout = 0100`, the
   other three codes are kept;
4. crossings in the last count (`255`) and the first (`0`), with `128`, `1`;
5. all four cells crossing in cycle 0.

The acquire/connect/convert mode outputs and the single-cycle `done` pulse
are checked in every case.

GF180 `gf180mcu_as_sc_mcu7t3v3` mapping (pre-placement, inside the digital
top): the digital top went from 625 to 506 cells and 19963 to 16438 um^2
with the change; no comparator-clocked flops remain.
