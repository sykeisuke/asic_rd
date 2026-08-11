# Integrated Wilkinson-slice results

Date: 2026-08-10

Tool environment: IIC-OSIC-TOOLS 2026.07, ngspice 46, GF180MCU
`gf180mcuD`, typical model corner.

## Integrated path

```text
1.2 V input
    -> CMOS transmission-gate sample/hold
    -> held voltage
    -> comparator against internal PMOS-current-source ramp
    -> comparator falling-edge time
    -> 20 MHz-equivalent 6-bit code
```

## Measurements

| Measurement | Result |
| --- | ---: |
| Input voltage | 1.2000 V |
| Held voltage | 1.1961 V |
| Acquisition error | 3.907 mV |
| Conversion time from reset release | 1.6395 us |
| Measured timing code | 32 |
| Ideal code from characterized slope | 31 |
| Code error | +1 count |
| Average analog power | 0.181 mW |

This is the first end-to-end transistor-level demonstration of sample, hold,
ramp, compare, and code formation. It passes the provisional single-point
6-bit baseline.

The analog-only test calculates code from comparator timing. The separate
mixed-signal co-verification now transfers that timing into the synthesizable
6-bit counter and confirms matching code capture. Continuous co-simulation and
metastability modeling remain future work.

## Coarse transfer characterization

An eight-point transistor-level sweep produced:

| Input | Held voltage | Code | Ideal code | Error |
| ---: | ---: | ---: | ---: | ---: |
| 0.4 V | 0.3937 V | 16 | 10 | +6 |
| 0.6 V | 0.5939 V | 17 | 15 | +2 |
| 0.8 V | 0.7942 V | 22 | 20 | +2 |
| 1.0 V | 0.9947 V | 27 | 26 | +1 |
| 1.2 V | 1.1961 V | 32 | 31 | +1 |
| 1.4 V | 1.3987 V | 38 | 36 | +2 |
| 1.5 V | 1.5005 V | 40 | 39 | +1 |
| 1.6 V | 1.6024 V | 43 | 41 | +2 |

The coarse transfer is strictly monotonic and all acquisition errors are below
10 mV. The +6-count error at 0.4 V shows that the current comparator delay and
common-mode behavior do not provide 6-bit accuracy across this range. This
prototype currently demonstrates 6-bit code formation, not 6-bit absolute
accuracy.

A 1.7 V point completed separately with code 46 versus ideal code 44. A 1.8 V
test did not complete reliably in the present simulation window, identifying
the upper comparator common-mode range as another design limit. Dense code-
transition testing is still required before assessing missing codes or DNL.
