# GF180 four-cell sampling array

This block replicates the provisional CMOS transmission-gate sampling cell four
times. Four non-overlapping sample controls capture 0.5 V, 0.8 V, 1.1 V, and
1.4 V input levels into separate 1 pF hold capacitors.

Run:

```sh
make four-cell
```

The self-check verifies less than 10 mV acquisition error per cell and confirms
that the four stored values remain in the expected cell order. Cell selection,
Wilkinson conversion sequencing, and digital readout are separate next steps.
