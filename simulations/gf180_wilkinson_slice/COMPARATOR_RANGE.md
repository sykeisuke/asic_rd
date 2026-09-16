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

## Update 2026-09-16: 0.5–2.2 V with a widened ramp window

The original slice testbench holds the ramp for 2.7 µs, which caps the ramp at
about 2.0 V (0.7675 V/µs). Inputs at or above 2.0 V therefore never completed —
a testbench artifact, not a comparator limit. `make comparator-range-wide`
extends the ramp/hold windows (3.6 µs / 4 µs, transient 3.9 µs) and sweeps both
input-pair variants over the proposed IRSX-like window and beyond.

| Input | NMOS pair: code (ideal) / error / power | PMOS pair: code (ideal) / error / power |
| ---: | --- | --- |
| 0.5 V | 16 (13) / **+3** / 0.02 mW | 14 (13) / +1 / 0.51 mW |
| 1.2 V | 32 (31) / +1 / 0.18 mW | 34 (31) / +3 / 0.35 mW |
| 1.8 V | 48 (46) / +2 / 0.27 mW | 52 (46) / +6 / 0.28 mW |
| 2.0 V | 54 (52) / +2 / 0.32 mW | 58 (52) / **+6** / 0.24 mW |
| 2.1 V | 57 (54) / +3 / 0.34 mW | 61 (54) / +7 / 0.21 mW |
| 2.2 V | 59 (57) / +2 / 0.34 mW | 64 (57) / +7 / 0.17 mW |

Observations:

- Both variants complete conversions up to 2.2 V once the ramp window is wide
  enough; neither has a common-mode cut-off inside 0.5–2.2 V.
- Over the proposed **0.5–2.0 V** window the NMOS pair's error spans +1…+3
  (2-count spread; the +3 at 0.5 V is the weak-inversion low end), while the PMOS
  pair's error grows monotonically from +1 to +6 (5-count spread) as the input
  approaches its common-mode ceiling.
- A constant offset is trivially calibrated; a spread this large is a gain/INL
  error and is the quantity to minimise. On this data the NMOS pair is the
  better fit for 0.5–2.0 V on a 3.3 V supply, the PMOS pair for windows that
  extend below 0.5 V.
- The window position is a free variable on a 3.3 V supply (the front end sets
  the baseline). A 1.5 V span placed at 0.9–2.4 V would suit the NMOS pair;
  0.3–1.8 V would suit the PMOS pair. Decide the window and the variant together.
- NMOS power at 0.5 V (22 µW) shows the pair is barely on; its delay there is
  what produces the +3.
