# Parallel Wilkinson controller (Tape-out 1 architecture, 2026-09-18; synchronous capture 2026-10-09)

One shared 8-bit Gray-coded counter, one broadcast ramp, and **one comparator
per storage cell**: all four cells convert simultaneously (IRSX-style). This
replaced the sequential 4-to-1 analog-MUX controller on 2026-09-18, together
with the move to bottom-plate sampling (the ramp is applied to the hold
capacitor's bottom plate and every comparator trips at a fixed reference).

Sequence and analog-mode outputs:

| State | `acquire` | `ramp_connect` | `ramp_reset` | Meaning |
| --- | --- | --- | --- | --- |
| IDLE | 1 | 0 | 1 | Cells may track/hold; bottom plates on the reference via the sampling sequencer |
| CONNECT | 0 | 1 | 1 | Bottom plates connected to the (reset) ramp output and settling |
| CONVERT | 0 | 1 | 0 | Ramp runs, counter counts; the four `crossed` flags are sampled every clock |
| DRAIN | 0 | 1 | 1 | Counter reached full scale; `CAPTURE_LATENCY` more cycles for a flag from the last count |

Capture is synchronous (decided 2026-10-09 on the design review's
recommendation): every analog cell latches its comparator output with the
conversion clock and presents a flag `crossed[i]`; the controller samples the
four flags every clock and records, per cell, the counter value of the cycle
in which the crossing happened (`CAPTURE_LATENCY` = 1 for a single flip-flop
in the cell, 2 for a two-stage synchronizer). No Gray coding, no comparator
used as a clock, no clock-domain crossing in the digital block. A cell whose
flag never rises saturates to `255` and raises `timeout[i]`. Results are
packed as `{cell3, cell2, cell1, cell0}` in one 32-bit bus. The earlier
asynchronous Gray-capture version is in the history up to commit `2d4fbf7`.

The ordering of the switches inside a cell (bottom-plate switch opens before
the top switch) is an analog sampling-sequencer function; this controller only
owns the acquire/convert mode and the ramp.

Run functional verification and GF180 technology mapping with:

```sh
make parallel-controller
```
