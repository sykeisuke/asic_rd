# Ramp-generator baseline results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, ngspice 46, GF180MCU
`gf180mcuD`, typical model corner.

## Conditions

- Ramp capacitor: ideal 1 pF.
- Current source: `pfet_03v3`, `L=2 um`, `W=1 um`.
- PMOS gate bias: external 2.2 V.
- Reset switch: `nfet_03v3`, `L=0.5 um`, `W=10 um`.
- Characterized ramp range: 0.6-1.8 V.

## Measurements

| Measurement | Result | Provisional limit |
| --- | ---: | ---: |
| Reset level | 0.182 mV | less than 10 mV |
| Average ramp slope | 0.768 V/us | 0.5-2.0 V/us |
| Half-range slope mismatch | 0.331% | less than 2% |
| Average power | 2.55 uW | less than 0.1 mW |

The block passes the typical-corner functional baseline. The slope is suitable
for a deliberately slow first Wilkinson conversion and can be adjusted through
bias voltage, source geometry, or capacitance.

The result is pre-layout and uses an ideal capacitor and ideal external bias.
PVT sensitivity, capacitor implementation, reset charge injection, output
buffer loading, startup, and bias generation must be characterized before
block freeze.
