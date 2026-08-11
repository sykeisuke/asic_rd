# Sampling-cell baseline results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, ngspice 46, GF180MCU
`gf180mcuD`, typical model corner.

## Circuit

- Switch: `nfet_03v3`, `L=0.28 um`, total `W=10 um`, `nf=10`.
- Hold capacitance: ideal 1 pF.
- Input: 1.2 V common-mode, 0.6 V amplitude, 5 MHz sine.
- Sample control: 0-3.3 V, open transition at 25.1 ns.

## Measurements

| Measurement | Result | Provisional baseline limit |
| --- | ---: | ---: |
| Acquisition error | 4.379 mV | less than 20 mV |
| Clock feedthrough | 12.180 mV | less than 30 mV |
| Hold droop over 45 ns | 0.144 uV | less than 1 mV |

The baseline passes its provisional functional limits. However, 12.18 mV of
clock feedthrough is larger than one LSB for an 8-bit conversion over a 2.5 V
range (approximately 9.77 mV). This is not an 8-bit-ready sampling cell.

These numbers are pre-layout and use an ideal capacitor. They are not silicon
predictions until PVT, mismatch, extracted parasitics, and a physical GF180
capacitor implementation have been included.

## Transmission-gate comparison

A second simulation placed a `pfet_03v3` (`W=20 um`, `nf=10`) in parallel
with the baseline NMOS and drove it with the complementary sample clock.

| Measurement | NMOS switch | Transmission gate | Change |
| --- | ---: | ---: | ---: |
| Acquisition error | 4.379 mV | 3.204 mV | -26.8% |
| Clock feedthrough | 12.180 mV | 5.088 mV | -58.2% |
| Hold droop over 45 ns | 0.144 uV | 0.070 uV | -51.5% |

The transmission gate is the provisional sampling-switch choice. Its measured
clock feedthrough is below one nominal 8-bit LSB for a 2.5 V conversion range.
The NMOS-only switch remains useful as a compact reference test structure.

Before topology freeze, the comparison must be repeated across input voltage,
PVT corners, clock skew, device sizing, and a realizable GF180 capacitor.
