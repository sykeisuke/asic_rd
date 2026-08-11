# ADR 0002: Keep the 1 pF, 20 MHz conversion baseline

Date: 2026-08-10

Status: Accepted for the first integrated prototype

## Context

The nominal NMOS-input comparator shows up to +6 counts of dynamic error at a
0.4 V input. Static trip-point characterization accounts for less than one
6-bit LSB, so a slower ramp and conversion clock were evaluated to reduce
propagation delay in count units without changing the nominal voltage per code.

The alternative doubled the ramp capacitor from 1 pF to 2 pF and doubled the
count period from 50 ns to 100 ns.

## Results

| Input | Baseline error | Slow-ramp error | Slow conversion time |
| ---: | ---: | ---: | ---: |
| 0.4 V | +6 | +5 | 1.557 us |
| 1.2 V | +1 | +1 | 3.203 us |
| 1.6 V | +2 | +1 | 4.268 us |

The low-end improvement was only one count while conversion time approximately
doubled. Mid- and upper-range accuracy changed little.

## Decision

Keep the 1 pF ramp capacitor and nominal 20 MHz count clock as the schematic
baseline. Do not spend the current schedule optimizing resolution through ramp
speed alone. Preserve NMOS and PMOS comparator test structures and move to the
four-cell integration needed for the complete-flow demonstration.

Revisit ramp speed after PVT, mismatch, extracted capacitance, and measured
silicon establish whether the final error is calibratable.
