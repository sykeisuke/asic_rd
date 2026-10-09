# Digital RTL-to-GDS results

Date: 2026-10-09 (8-bit parallel top with synchronous capture, **3.3 V
library `gf180mcu_as_sc_mcu7t3v3`**; the 2026-09-25 asynchronous-capture run
was 292 x 310 um with 1508 standard cells; the 2026-08-11 reference run the
6-bit sequential top at 5 V: 798 cells, 50297.5 um^2 die)

Tool environment: LibreLane in the pinned IIC-OSIC-TOOLS 2026.07 container
(OpenROAD, Magic, KLayout, Netgen), PDK commit `f6eeac7d` with the 3.3 V
standard cells fetched by `make pdk`.

| Metric | Result |
| --- | ---: |
| Die size | 247.625 um x 265.545 um |
| Die area | 65756 um^2 |
| Core utilization | 36.4 % |
| Routed standard cells | 1059 (3061 instances incl. fill/tap) |
| Sequential cells | 103 |
| Routed wire length | 21804 um |
| Routed vias | 3671 |
| Estimated total power (20 MHz) | 1.04 mW |
| Worst setup slack (all corners) | 43.07 ns |
| Worst hold slack (all corners) | 0.476 ns |

Signoff-oriented checks:

| Check | Result |
| --- | --- |
| Detailed-route DRC | PASS, 0 violations |
| Antenna | PASS, 0 violating nets / pins |
| Critical disconnected pins | PASS, 0 |
| Magic DRC | PASS, 0 errors |
| KLayout DRC | PASS, 0 errors |
| Netgen LVS | PASS, 0 errors |
| Setup / hold (9 corner-RC combinations) | PASS, 0 violations |
| Max slew | PASS, 0 violations |

The four `crossed` inputs are synchronous data inputs (the latch sits in the
analog cell, ADR 0010), so the block is single-clock and fully covered by
STA. IR-drop numbers are provisional
because package source locations are not yet known.
