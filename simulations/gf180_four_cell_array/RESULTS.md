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

This result does not include an analog readout mux. Connecting a selected cell
to the comparator may introduce charge sharing and additional droop, so mux
loading must be measured before integrating the Wilkinson conversion sequence.
