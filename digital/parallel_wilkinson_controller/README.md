# Parallel Wilkinson controller (Analog_top interface, synchronous capture)

The digital side of the 8-bit true bottom-plate ADC of
[`mixed_signal/Analog_top`](../../mixed_signal/Analog_top/README.md)
(its `PIN_LIST.md` and `tb_params.inc` are the contract):

- **Sampling sequence** (all switches HIGH = closed). From `start`, one cell
  per clock: `s2[k]` falls at TS_k = TS_0 + k x 50 ns (the sampling instant;
  bottom plate frozen); `s0[k]` (input gate) opens TNOV = 5 ns later and
  `s1[k]` (ramp gate) closes 2 TNOV = 10 ns later, both from fixed delay
  lines ([`delay_line.v`](delay_line.v): 12 and 25 `dlybuff_2` stages, about
  0.40 ns each at typical).
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
  ramp is reset, `s1` opens, and on the next clock `s2`/`s0` close again
  (`done` pulses once). Codes are packed `{cell3, cell2, cell1, cell0}`.

Parameters: `WIDTH` 8, `CELLS` 4, `TR_CYCLES` 6, `S0_STAGES` 12,
`S1_STAGES` 25, `Q_FALLS_AT_CROSSING` 1 (set 0 if the comparator inputs are
swapped and `q` rises at the crossing instead). The delay-line length is the only PVT-dependent timing
(about +-40 % on TNOV); it moves a per-cell offset of about 1 LSB that the
pedestal calibration removes.

```sh
make parallel-controller
```

History: asynchronous Gray capture with `acquire`/`ramp_connect` outputs
until 2026-10-28 (commits up to `b74752b`); sequential MUX controller before
2026-09-18 (`digital/legacy`).
