# Decision 0001: Baseline analog flow

Status: proposed

## Decision

Use GF180MCU as the baseline process. Use a pinned Linux container on the Mac
for Xschem, ngspice/Xyce, Magic, Netgen, and KLayout. Treat the MPW provider's
accepted PDK release and signoff decks as authoritative.

## Reasoning

Analog device models, layout rules, I/O cells, and signoff decks are coupled to
the process. Pinning them before circuit implementation reduces migration and
requalification work. A container provides a reproducible environment across
Apple Silicon Macs and Linux machines.

## Open items

- wafer.space early-2027 run schedule is not yet confirmed.
- Exact GF180MCU variant and PDK revision are not yet confirmed by the provider.
- Container image and digest are not yet selected.
- Package, pad ring, and high-speed analog I/O constraints are not yet frozen.

