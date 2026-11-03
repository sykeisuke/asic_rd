# Parallel Wilkinson controller (Analog_top v7 interface, synchronous capture)

The digital side of the 8-bit true bottom-plate ADC of
[`mixed_signal/Analog_top`](../../mixed_signal/Analog_top/README.md)
(its `PIN_LIST.md` and `tb_params.inc` are the contract):

- **Acquire** (`acq`, HIGH = track, a flop on the rising edge). From
  `start`, `acq` falls on the next rising edge; the macro's own sequencer
  ([`mixed_signal/sample_seq`](../../mixed_signal/sample_seq/README.md),
  ADR 0027) then opens cell k's S2 at the k-th rising edge after the edge
  that first sees `acq` low (TS_k = TS_0 + k x 50 ns, the sampling instant),
  and orders S0 and S1 after it with at least 5 ns between phases over PVT.
  The controller drives no switch control itself.
- **Ramp and count**: `ramp_rst` falls at TR = TS_3 + 6 clocks (300 ns, the
  reference's recovery requirement), on a rising edge; the 8-bit counter
  starts there.
- **Capture** (ADR 0010): the cell's latch is a negative-edge flop on
  `cnt_clk` fed by the comparator; `q[i]` is high before the crossing and
  falls once at the first falling edge after it. The controller samples
  `q` on every rising edge and records `code_i = count` at the edge that
  first sees `q[i]` low, which equals `floor((t_qfall_i - TR) / TCOUNT)`.
  No Gray coding, no comparator used as a clock.
- **End**: when all cells have crossed, or after one extra cycle at full
  scale (a cell that never crosses reads 255 and sets `timeout[i]`), the
  ramp is reset and on the next clock `acq` returns high: the cells re-enter
  track (the sequencer opens S1 first, then closes S0 / S2); `done` pulses
  once. Codes are packed `{cell3, cell2, cell1, cell0}`.

Parameters: `WIDTH` 8, `CELLS` 4, `TR_CYCLES` 6, `Q_FALLS_AT_CROSSING` 1
(set 0 if the comparator inputs are swapped and `q` rises at the crossing
instead). Everything is on the one 20 MHz clock; the controller has no
PVT-dependent timing.

```sh
make parallel-controller
```

History: `s0/s1/s2[3:0]` switch outputs with on-chip delay lines (12 and 25
`dlybuff_2` stages, [`../legacy/delay_line.v`](../legacy/delay_line.v))
from 2026-10-28 to 2026-11-03; asynchronous Gray capture with
`acquire`/`ramp_connect` outputs until 2026-10-28 (commits up to
`b74752b`); sequential MUX controller before 2026-09-18 (`digital/legacy`).
