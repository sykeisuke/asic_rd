# Wilkinson mixed-signal co-verification

This test connects the transistor-level analog slice to the synthesizable
6-bit counter through reproducible file-based co-verification:

1. ngspice runs the GF180 sample/hold, ramp, and comparator.
2. The measured conversion time and timing-derived code are extracted.
3. An RTL stimulus include is generated automatically.
4. Icarus Verilog drives the comparator transition at that measured time.
5. The real counter RTL must capture the same code.

Run:

```sh
make cosim
```

This is not a continuous analog/digital event-driven simulator. It is a
deterministic bridge between the two verified domains and is sufficient to
check timing convention, clock phase, counter quantization, and interface
polarity. A later top-level flow may replace it with an RNM or dedicated
mixed-signal simulator if one is available.
