# 6-bit Wilkinson counter and capture logic

This synthesizable RTL block counts conversion-clock edges while the analog
comparator output is high. It captures the count when the comparator goes low,
pulses `valid`, and saturates at code 63 with `overflow` if no crossing occurs.

Run:

```sh
make counter
```

The self-checking testbench covers code 32 from the integrated analog slice,
zero-length conversion, one-cycle `valid`, and saturation. The same command
runs generic Yosys synthesis and maps the design to GF180 `mcu7t5v0` cells at
the TT, 25 C, 3.3 V liberty corner. Timing analysis remains required before
digital block freeze.

`compare_high` is asynchronous in the eventual chip. This baseline samples it
directly on the conversion clock. Comparator-to-clock metastability and the
chosen synchronization or capture strategy must be resolved during mixed-
signal integration.
