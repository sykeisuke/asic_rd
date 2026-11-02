# ADR 0010: Synchronous capture — the comparator is latched inside the analog cell

Date: 2026-10-09 (decision); 2026-10-28 (interface fixed to Analog_top).
Status: accepted (project lead, on the collaborating group's recommendation
of 2026-10-02).

## Context

Until now the comparator output was used as a local capture clock inside
the digital block: a Gray-coded counter word was latched on the comparator's
falling edge and a toggle synchronizer returned the event to the conversion
clock domain (ADR 0003). That hands an analog, possibly metastable signal to
place-and-route as a clock net, needs special timing constraints, leaves
the metastability behaviour outside STA, and would mean thousands of such
clock nets in a Tape-out 3 array.

## Decision

- The **analog cell takes the conversion clock** (`cnt_clk`) and contains
  the latch after its comparator: `mixed_signal/latch`, the library's
  negative-edge flop `dfxtn_2` (ADR 0019). Its output `q[i]` is HIGH before
  the crossing and falls once at the first falling clock edge after the
  comparator decides.
- The digital block samples `q[3:0]` on every rising edge and records, per
  cell, the count at the edge that first sees `q[i]` low, which equals
  `floor((t_qfall_i - TR) / TCOUNT)` (`Analog_top/tb_params.inc`). No Gray
  coding, no clock-domain crossing in the digital block.
- The digital block also generates the cell switch sequence (`s2`, then
  `s0` 5 ns later, then `s1` 5 ns after that, one cell per clock) and the
  ramp reset (TR = TS_3 + 6 clocks), so the whole timeline comes from one
  20 MHz clock and a `start`.
- Code resolution is unchanged (one conversion-clock period); the latch's
  falling-edge sampling places the decision instants half a period after
  the rising edges.

## Consequences

- `digital/parallel_wilkinson_controller`: capture replaced by flag
  sampling; a sampling sequencer and two delay lines per cell (12 and 25
  `dlybuff_2` stages, about 0.40 ns each) added. The only PVT-dependent
  timing is the delay line (about +-40 % on TNOV), which moves a per-cell
  offset of about 1 LSB that the pedestal calibration removes; a trimmable
  or board-adjustable TNOV is a possible refinement.
- Analog side: `cnt_clk` pin, one `dfxtn_2` per cell; the comparator
  output never leaves the macro.
- `mixed_signal/top_placement`: `chip_core` latches the comparator output on
  the falling edge as a stand-in until the Analog_top macro is placed.
- Supersedes ADR 0003 (Gray comparator capture) for the production path;
  the single-channel Gray counter stays as a legacy reference block.
