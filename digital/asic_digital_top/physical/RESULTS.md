# Digital RTL-to-GDS results

Date: 2026-10-28 (digital top for the Analog_top interface: sampling
sequencer with delay lines, synchronous `q` capture; **3.3 V library
`gf180mcu_as_sc_mcu7t3v3`**. The 2026-09-25 asynchronous-capture run was
292 x 310 um with 1508 standard cells; the 2026-08-11 reference run the 6-bit
sequential top at 5 V: 798 cells, 50297.5 um^2 die)

Tool environment: LibreLane in the pinned IIC-OSIC-TOOLS 2026.07 container
(OpenROAD, Magic, KLayout, Netgen), PDK commit `f6eeac7d` with the 3.3 V
standard cells fetched by `make pdk`.

| Metric | Result |
| --- | ---: |
| Die size | 274.11 um x 292.03 um |
| Die area | 80048 um^2 |
| Core utilization | 36.4 % |
| Routed standard cells | 1324 (3808 instances incl. fill/tap; 148 delay-line stages) |
| Sequential cells | 112 |
| Routed wire length | 22833 um |
| Routed vias | 4057 |
| Estimated total power (20 MHz) | 1.99 mW |
| Worst setup slack (all corners) | 29.47 ns |
| Worst hold slack (all corners) | 0.373 ns |

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
the macro. The cell switch timing (5 ns / 10 ns) comes from kept delay-line
cells, not from STA. IR-drop numbers are provisional
because package source locations are not yet known.
