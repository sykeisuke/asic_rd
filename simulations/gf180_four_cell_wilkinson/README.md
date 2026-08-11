# GF180 four-cell Wilkinson macro

This transistor-level integration test combines four transmission-gate sample
cells, a resettable 4-to-1 analog mux, one shared ramp generator, and one shared
continuous-time comparator. The cells are converted sequentially in 2.9 us
slots.

Run:

```sh
make four-cell-wilkinson
```

The provisional complete-flow gate requires four comparator crossings,
strictly monotonic 6-bit codes, no more than three counts of error relative to
the nominal input/slope prediction, and less than 200 uW average analog-core
power. These relaxed limits demonstrate integration and are not final ADC
linearity specifications.
