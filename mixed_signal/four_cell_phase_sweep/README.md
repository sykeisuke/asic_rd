# Four-cell comparator clock-phase sweep

This test shifts all four transistor-level comparator crossing intervals around
the 20 MHz conversion-clock phase. It runs the real RTL controller repeatedly
at offsets from -2 ns to +2 ns and checks the captured codes against ideal
50 ns quantization.

Run:

```sh
make phase-sweep
```

The sweep identifies crossings close to a counter edge. RTL simulation can
locate the code boundary but cannot model analog metastability or resolution
time; transistor-level latch and standard-cell timing analysis remain required.
