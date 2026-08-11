# Four-cell sampling-array results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, ngspice 46, GF180MCU
`gf180mcuD`, typical model corner.

Four sequential, non-overlapping transmission-gate apertures sampled distinct
input levels into four ideal 1 pF hold capacitors.

| Cell | Applied input | Held voltage | Acquisition error |
| ---: | ---: | ---: | ---: |
| 0 | 0.5 V | 0.490799 V | 9.201 mV |
| 1 | 0.8 V | 0.792128 V | 7.872 mV |
| 2 | 1.1 V | 1.094365 V | 5.635 mV |
| 3 | 1.4 V | 1.399222 V | 0.778 mV |

All four cells pass the provisional 10 mV acquisition limit and preserve the
expected sample order. The input-dependent error is consistent with the
previous single-cell transmission-gate characterization.

## Sequential analog readout mux

A 4-to-1 transmission-gate mux sequentially connected each cell to a 20 fF
comparator-input bus. An NMOS reset discharges the otherwise-floating bus before
the first selection.

| Cell | Held before readout | Mux output | Mux error | Hold disturbance |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.490862 V | 0.466246 V | 24.615 mV | 31.010 mV |
| 1 | 0.792183 V | 0.779516 V | 12.666 mV | 17.153 mV |
| 2 | 1.094410 V | 1.080060 V | 14.351 mV | 16.453 mV |
| 3 | 1.399230 V | 1.380060 V | 19.165 mV | 17.273 mV |

The mux passes the provisional array-integration limits of 30 mV output error
and 35 mV hold disturbance while preserving channel order. Cell 0 is the worst
case because it first shares charge with the reset bus. The next architecture
iteration should evaluate per-conversion precharge and a source-follower or
buffered readout path; these results do not yet support a final 6-bit INL/DNL
claim.
