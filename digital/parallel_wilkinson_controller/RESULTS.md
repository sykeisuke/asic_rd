# Parallel controller results

Date: 2026-09-18

Self-checking RTL simulation (Icarus, 20 MHz conversion clock) passes four
conversions:

1. codes `16, 20, 27, 35` on the four cells simultaneously;
2. two equal codes plus a near-full-scale code (`200, 200, 3, 254`);
3. one cell never crossing: code saturates to `255`, `timeout = 0100`, the
   other three codes are kept;
4. a crossing exactly at the last count (`255`) together with `0`, `128`, `1`.

The acquire/connect/convert mode outputs and the single-cycle `done` pulse
are checked in every case.

GF180 `mcu7t5v0` mapping at TT, 25 C, 3.3 V (pre-placement estimate):

| Metric | Result |
| --- | ---: |
| Mapped cells | 437 |
| Liberty area | 14883.5 um^2 |
| of which sequential | 56.8 % |
| Comparator-clocked capture flops (`dffnrnq`) | 36 (4 cells x 8 Gray bits + 4 toggles) |

For comparison the sequential 6-bit MUX controller plus its counter mapped to
264 cells / 8974 um^2. The growth is the four independent capture registers
(8 bit each) and the 8-bit result word per cell.
