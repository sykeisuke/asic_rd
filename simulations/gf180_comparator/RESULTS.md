# Comparator baseline results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, ngspice 46, GF180MCU
`gf180mcuD`, typical model corner.

## Conditions

- Held sample: 1.2 V.
- Ramp: 0.6-1.8 V in 1 us, or 1.2 V/us.
- Input pair: NMOS, `L=0.5 um`, `W=20 um` per side.
- Load: PMOS current mirror, `L=0.5 um`, `W=40 um` per side.
- Tail bias: 0.85 V.
- Output: two CMOS restoring inverters with 50 fF load.

## Measurements

| Measurement | Result | Provisional limit |
| --- | ---: | ---: |
| Ramp crossing delay | 23.046 ns | less than 40 ns |
| Output high | 3.300 V | greater than 3.0 V |
| Output low | approximately 0 V | less than 0.3 V |
| Average power | 0.184 mW | less than 1 mW |

The equivalent input error from ramp slope and delay is approximately 27.7 mV.
This is below one LSB for a 6-bit, 2.5 V range (39.1 mV), but above one LSB for
an 8-bit range (9.77 mV). The circuit is therefore accepted as a 6-bit
complete-flow baseline, not as the final 8-bit comparator.

Next characterization must separate static offset from propagation delay and
cover common-mode range, PVT, mismatch Monte Carlo, kickback, bias current, and
ramp-slope dependence.
