# Digital top synthesis and timing results

Date: 2026-09-18 (8-bit parallel architecture; the 2026-08-11 figures for the
6-bit sequential top were 415 cells / 12896.8 um^2)

Functional simulation converts four cells in parallel, stores codes
`16, 20, 27, 200`, and reconstructs the same packed 32-bit word through the
serial output.

| Metric | Result |
| --- | ---: |
| Total mapped cells | 625 |
| Total Liberty area | 19963.1 um^2 |
| Target conversion clock | 20 MHz |
| Estimated minimum conversion-clock period | 6.67 ns |
| Estimated maximum conversion-clock frequency | 149.8 MHz |
| Worst setup slack | 38.39 ns |
| Worst hold slack | 0.83 ns |
| Total negative slack | 0.00 ns |

The four comparator-event inputs are declared as one asynchronous clock group
against the conversion clock. The reported pre-layout timing covers
synchronous paths but does not prove metastability resolution at the Gray
capture boundary. Post-placement clock skew, routing parasitics, the 3.3 V
library retarget, and provider signoff constraints remain.
