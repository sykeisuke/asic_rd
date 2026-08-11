# Four-cell analog-to-RTL co-verification

This deterministic file bridge connects the full GF180 transistor-level
four-cell macro to the synthesizable controller and counter:

1. ngspice measures all four comparator crossing intervals;
2. AWK converts those intervals and analog codes into a Verilog include;
3. the RTL controller generates reset, mux-select, and ramp-release sequencing;
4. the testbench applies each comparator edge after its measured analog delay;
5. the controller must store the same four codes reported by ngspice.

Run:

```sh
make four-cell-cosim
```

This flow verifies polarity, ordering, clock quantization, and packed result
storage. It remains a file-based bridge rather than a continuous mixed-signal
simulator, and it does not model comparator metastability near a clock edge.
