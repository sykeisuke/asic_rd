# Digital top synthesis and timing results

Date: 2026-11-03 (Analog_top v7 interface: `acq`, synchronous capture; the
2026-10-28 top with the switch sequence and delay lines mapped to 585
cells / 19139.9 um^2, the 2026-09-18 asynchronous-capture top to 625 cells
/ 19963.1 um^2 at 5 V, the 2026-08-11 6-bit sequential top to 415 cells /
12896.8 um^2)

Functional simulation drops `acq`, converts four cells in
parallel (comparators deciding in counts 16, 20, 27, 200), stores the codes
and reconstructs the packed 32-bit word through the serial output; the
testbench models the cells' negative-edge latches.

| Metric | Result |
| --- | ---: |
| Total mapped cells (`gf180mcu_as_sc_mcu7t3v3`) | 392 |
| Total Liberty area | 14756.1 um^2 |
| Target conversion clock | 20 MHz |
| Estimated minimum conversion-clock period | 2.87 ns |
| Total negative slack | 0.00 ns |

Single clock; `q[3:0]` are synchronous data inputs (latched in the analog
cell on the falling edge, half a period of margin).
