# Digital RTL-to-GDS results

Date: 2026-11-03 (digital top for the Analog_top v7 interface: `acq`
instead of the switch sequence, no delay lines, synchronous `q` capture;
**3.3 V library `gf180mcu_as_sc_mcu7t3v3`**, PDK `792ef670`. The
2026-10-28 run with the delay lines was 274 x 292 um with 1324 standard
cells; the 2026-09-25 asynchronous-capture run 292 x 310 um with 1508; the
2026-08-11 reference run the 6-bit sequential top at 5 V: 798 cells,
50297.5 um^2 die)

Tool environment: LibreLane in the pinned IIC-OSIC-TOOLS 2026.07 container
(OpenROAD, Magic, KLayout, Netgen), PDK commit `792ef670` with the 3.3 V
standard cells fetched by `make pdk`.

| Metric | Result |
| --- | ---: |
| Die size | 239.44 um x 257.36 um |
| Die area | 61622 um^2 |
| Core utilization | 37.0 % |
| Routed standard cells | 954 (2832 instances incl. fill/tap) |
| Sequential cells | 108 |
| Routed wire length | 19517 um |
| Routed vias | 3347 |
| Estimated total power (20 MHz) | 1.46 mW |
| Worst setup slack (all corners) | 43.25 ns |
| Worst hold slack (all corners) | 0.364 ns |

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

Single clock: `q[3:0]` are synchronous data inputs (latched on the falling
edge inside the analog cells, ADR 0010); `cnt_clk` is the clock forwarded to
the macro, `acq` a registered output from which the macro's own sequencer
makes the cell switch timing (ADR 0027), so nothing in this block is
PVT-dependent beyond STA. IR-drop numbers are provisional
because package source locations are not yet known.
