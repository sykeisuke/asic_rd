# GF180 integrated Wilkinson slice

This simulation connects the provisional transmission-gate sampling cell,
on-chip PMOS-current-source ramp, and continuous-time comparator. A held 1.2 V
input is converted into a 6-bit code using a nominal 20 MHz count period.

Run:

```sh
make wilkinson-slice
```

The current test derives the code from measured comparator timing. It proves
the integrated analog signal path, but does not yet contain a synthesized
counter or capture latch. Those digital blocks are the next integration step.

Generated waveforms and measurements under `work/` are not tracked by Git.
