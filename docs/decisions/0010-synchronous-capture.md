# ADR 0010: Synchronous capture — the comparator is latched inside the analog cell

Date: 2026-10-09. Status: accepted (project lead, on the collaborating
group's recommendation of 2026-10-02).

## Context

Until now the comparator output was used as a local capture clock inside
the digital block: a Gray-coded counter word was latched on the comparator's
falling edge and a toggle synchronizer returned the event to the conversion
clock domain (ADR 0003). That hands an analog, possibly metastable signal to
place-and-route as a clock net, needs special timing constraints, leaves
the metastability behaviour outside STA, and would mean thousands of such
clock nets in a Tape-out 3 array.

## Decision

- The **analog cell takes the conversion clock** and contains the latch
  (one flip-flop; two if a synchronizer is wanted) after its comparator.
  The cell's digital output is a synchronous flag `crossed[i]`: 1 once the
  ramp has passed the stored sample.
- The digital block samples the four flags every clock and records, per
  cell, the count of the cycle in which the crossing happened:
  `code = count_at_sample - CAPTURE_LATENCY` (latency 1 for one flip-flop,
  2 for two). No Gray coding, no clock-domain crossing in the digital block.
- Code resolution is unchanged (one conversion-clock period either way).

## Consequences

- `digital/parallel_wilkinson_controller`: capture logic replaced by flag
  sampling; the digital top shrinks from 625 to 506 cells; the SDC has a
  single clock and no false-path group.
- Analog cell interface: +1 clock pin, +1-2 flip-flops per cell; the
  comparator output never leaves the cell as a raw net.
- `mixed_signal/top_placement`: `chip_core` latches the comparator output
  as a stand-in until the cell carries the latch.
- Supersedes ADR 0003 (Gray comparator capture) for the production path;
  the single-channel Gray counter stays as a legacy reference block.
