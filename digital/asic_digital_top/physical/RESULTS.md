# Digital RTL-to-GDS results

Date: 2026-08-11

Tool environment: LibreLane 3.1.0.dev2, OpenROAD, Magic, KLayout, Netgen, and
GF180MCU `gf180mcu_fd_sc_mcu7t5v0`.

| Metric | Result |
| --- | ---: |
| Die size | 215.49 um x 233.41 um |
| Die area | 50297.5 um^2 |
| Core utilization | 39.50% |
| Routed standard cells | 798 |
| Sequential cells | 101 |
| Routed wire length | 14792 um |
| Routed vias | 2784 |
| Estimated total power | 6.13 mW |
| Worst setup slack across reported corners | 39.21 ns |
| Worst hold slack across reported corners | 0.336 ns |

Signoff-oriented checks from the reference run:

| Check | Result |
| --- | --- |
| Detailed-route DRC | PASS, 0 violations |
| Antenna | PASS, 0 violations |
| Critical disconnected pins | PASS, 0 |
| Magic DRC | PASS, 0 errors |
| KLayout DRC | PASS, 0 errors |
| Netgen LVS | PASS, 0 errors |
| Setup / hold | PASS, 0 violations |
| Max slew / capacitance | PASS, 0 violations |

The two reported floating nets are the special `VDD` and `VSS` nets, which are
connected by the generated power grid. The 315 lint warnings arise from missing
timescales in PDK standard-cell simulation models, not project RTL. IR-drop
numbers are provisional because package source locations are not yet known.
