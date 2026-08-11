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

The code is currently calculated from comparator timing rather than captured
by physical digital logic. Before calling the slice functionally complete, add
a 6-bit RTL counter/capture block, verify its standalone behavior, and connect
its interface to the analog comparator model. A multi-point transfer test is
also required to measure monotonicity and missing codes.
