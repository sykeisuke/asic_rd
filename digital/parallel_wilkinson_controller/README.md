# Parallel Wilkinson controller (Tape-out 1 architecture, 2026-09-18)

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
| CONVERT | 0 | 1 | 0 | Ramp runs, counter counts; each comparator falling edge captures the Gray word |
| DRAIN | 0 | 1 | 1 | Counter reached full scale; late capture events still synchronize |

Per cell, the comparator edge is a local capture clock (Gray word latched on
the falling edge, toggle-synchronized back into the 20 MHz domain, decoded to
binary). A cell that never crosses saturates to `255` and raises its
`timeout[i]` flag. Results are packed as `{cell3, cell2, cell1, cell0}` in
one 32-bit bus.

The ordering of the switches inside a cell (bottom-plate switch opens before
the top switch) is an analog sampling-sequencer function; this controller only
owns the acquire/convert mode and the ramp.

Run functional verification and GF180 technology mapping with:

```sh
make parallel-controller
```
