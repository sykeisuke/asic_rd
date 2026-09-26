# Digital RTL-to-GDS results

Date: 2026-09-25 (8-bit parallel top, **3.3 V library `gf180mcu_as_sc_mcu7t3v3`**;
the 2026-08-11 reference run was the 6-bit sequential top at 5 V:
798 cells, 50297.5 um^2 die)

Tool environment: LibreLane in the pinned IIC-OSIC-TOOLS 2026.07 container
(OpenROAD, Magic, KLayout, Netgen), PDK commit `f6eeac7d` with the 3.3 V
standard cells fetched by `make pdk`.

| Metric | Result |
| --- | ---: |
| Die size | 292.35 um x 310.27 um |
| Die area | 90707 um^2 |
| Core utilization | 37.3 % |
| Routed standard cells | 1508 (4327 instances incl. fill/tap) |
| Sequential cells | 152 |
| Routed wire length | 29114 um |
| Routed vias | 5039 |
| Estimated total power (20 MHz) | 2.76 mW |
| Worst setup slack (all corners) | 42.59 ns |
| Worst hold slack (all corners) | 0.318 ns |

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

The four comparator inputs are constrained as one asynchronous clock group
against the conversion clock (see `physical.sdc`); metastability of the
Gray-capture flops is not covered by STA. IR-drop numbers are provisional
because package source locations are not yet known.
