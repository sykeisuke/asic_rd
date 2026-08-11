# Four-cell Wilkinson integration results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, ngspice 46, GF180MCU
`gf180mcuD`, typical model corner.

One ramp and comparator converted four previously sampled cells in sequential
2.9 us slots. A 50 ns count period maps each crossing time to a 6-bit code.

| Cell | Nominal input | Mux level before ramp | Conversion time | Code | Ideal code | Error |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.5 V | 0.456612 V | 0.831984 us | 16 | 13 | +3 |
| 1 | 0.8 V | 0.734986 V | 1.040260 us | 20 | 20 | 0 |
| 2 | 1.1 V | 1.014740 V | 1.399500 us | 27 | 28 | -1 |
| 3 | 1.4 V | 1.296100 V | 1.771850 us | 35 | 36 | -1 |

Average analog-core power over the four conversions is 112.13 uW. All four
crossings are detected, the output is monotonic, and the maximum absolute code
error is three counts. The first cell shows the largest dynamic error because
comparator delay is a larger fraction of its short conversion time.

The shared comparator loads the mux more strongly than the earlier standalone
20 fF bus model, reducing each selected voltage. A buffered mux output and
low-level comparator-delay calibration remain important accuracy improvements.
