# Digital top synthesis and timing results

Date: 2026-08-11

Functional simulation converts four cells, stores codes `16, 20, 27, 35`, and
reconstructs the same packed 24-bit word through the serial output.

| Metric | Result |
| --- | ---: |
| Total mapped cells | 415 |
| Total Liberty area | 12896.8000 um^2 |
| Target conversion clock | 20 MHz |
| Estimated minimum conversion-clock period | 7.45 ns |
| Estimated maximum conversion-clock frequency | 134.16 MHz |
| Worst setup slack | 40.6084 ns |
| Worst hold slack | 0.8286 ns |
| Total negative slack | 0.00 ns |

The comparator-event and conversion-clock domains are declared asynchronous.
The reported pre-layout timing therefore covers synchronous paths but does not
prove metastability resolution at the Gray capture boundary. Post-placement
clock skew, routing parasitics, and provider signoff constraints remain.
