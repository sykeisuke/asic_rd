# GF180 four-cell sampling array

This block replicates the provisional CMOS transmission-gate sampling cell four
times. Four non-overlapping sample controls capture 0.5 V, 0.8 V, 1.1 V, and
1.4 V input levels into separate 1 pF hold capacitors.

Run:

```sh
make four-cell
```

The self-check verifies less than 10 mV acquisition error per cell and confirms
that the four stored values remain in the expected cell order.

The sequential 4-to-1 analog readout mux test is run separately:

```sh
make four-cell-mux
```

It models a 20 fF comparator-input bus, resets that bus before readout, and
measures both mux settling error and destructive charge-sharing disturbance.
The provisional flow gate is 30 mV maximum mux error and 35 mV maximum hold
disturbance. These are integration limits, not final ADC accuracy targets.
