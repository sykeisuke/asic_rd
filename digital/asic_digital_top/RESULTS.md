# Digital top synthesis and timing results

Date: 2026-10-09 (8-bit parallel architecture with synchronous capture; the
2026-09-18 asynchronous-capture top mapped to 625 cells / 19963.1 um^2 on
the 5 V library, the 2026-08-11 6-bit sequential top to 415 cells /
12896.8 um^2)

Functional simulation converts four cells in parallel, stores codes
`16, 20, 27, 200`, and reconstructs the same packed 32-bit word through the
serial output. The testbench models the analog cell latch (flag raised at
the clock edge that ends the crossing cycle).

| Metric | Result |
| --- | ---: |
| Total mapped cells (`gf180mcu_as_sc_mcu7t3v3`) | 506 |
| Total Liberty area | 16437.7 um^2 |
| Target conversion clock | 20 MHz |
| Estimated minimum conversion-clock period | 2.83 ns |
| Total negative slack | 0.00 ns |

The four `crossed` inputs are ordinary synchronous data inputs (the latch
sits in the analog cell), so the block is single-clock and fully covered by
STA; no comparator-clocked flops remain.
