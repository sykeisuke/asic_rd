# Comparator static trip-point results

Date: 2026-08-10

The comparator inputs were driven symmetrically around a fixed common-mode
voltage while differential voltage was swept from -100 mV to +100 mV. The trip
point is the differential input where the restored digital output crosses
half-supply.

## Typical-corner results

| Common mode | NMOS input pair | PMOS input pair |
| ---: | ---: | ---: |
| 0.4 V | -10.644 mV | +12.057 mV |
| 1.2 V | -7.776 mV | +9.236 mV |
| 1.8 V | -8.108 mV | +8.463 mV |

For a 2.5 V, 6-bit range, one LSB is 39.06 mV. The nominal static trip errors
therefore correspond to approximately 0.2-0.3 LSB. They cannot explain the
largest integrated dynamic errors of six counts.

## Conclusion

Dynamic propagation and settling delay, especially near input common-mode
limits, dominates the present transfer error. Comparator improvement should
prioritize dynamic response or a slower conversion clock relative to the ramp,
while preserving power and range. Monte Carlo mismatch is not included here
and may increase the static offset substantially.
