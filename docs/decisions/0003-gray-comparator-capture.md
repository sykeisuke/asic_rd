# Decision 0003: Gray-coded asynchronous comparator capture

Date: 2026-08-11

## Status

Provisional production-path baseline.

## Context

The nominal four-cell phase study found one comparator crossing only 500 ps
from a 20 MHz counter edge. Sampling the comparator level with the counter clock
creates a metastability risk and makes the captured code sensitive to clock
phase.

## Decision

Use a synchronous binary counter with a combinational Gray representation.
Capture the Gray word on the falling comparator edge, synchronize a capture
toggle into the main clock domain, and decode the stable captured word there.

## Consequences

At a counter transition only one Gray bit changes, so timing ambiguity is
limited to adjacent codes. The comparator becomes a local clock for capture
flops and therefore needs explicit physical clock treatment. This architecture
reduces multi-bit incoherency but does not eliminate analog metastability; the
prototype shall expose comparator and clock test points for characterization.
