# Comparator input-pair range comparison

Date: 2026-08-10

The original NMOS-input comparator is efficient in the middle of the range but
has large delay error at low common mode and does not reliably complete the
1.8 V integrated-slice test. A PMOS-input alternative was therefore evaluated
with the same sampler, ramp, output buffers, and timing-to-code calculation.

## PMOS-input results

| Input | Timing code | Ideal code | Error | Average analog power |
| ---: | ---: | ---: | ---: | ---: |
| 0.4 V | 11 | 10 | +1 | 0.580 mW |
| 1.2 V | 34 | 31 | +3 | 0.380 mW |
| 1.8 V | 52 | 46 | +6 | 0.272 mW |

The PMOS pair fixes the low-end error and completes at 1.8 V, but its delay
error grows toward the upper range. Increasing tail current did not change the
quantized errors at 0.4 V or 1.2 V and increased power to roughly 1 mW, so that
variant was rejected.

## Provisional decision

Do not replace the NMOS comparator yet. Keep both input-pair variants as
candidate test structures:

- NMOS input pair for the mid-range baseline and lower power.
- PMOS input pair for low-voltage and wider-range observability.

A rail-to-rail or range-selected architecture may combine them later. Before
that added complexity, characterize static input offset separately from ramp
delay and determine whether digital calibration can meet the first-prototype
goal with one comparator.
