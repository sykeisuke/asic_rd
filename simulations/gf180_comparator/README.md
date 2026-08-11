# GF180 Wilkinson comparator baseline

This block compares a held sample voltage with an external Wilkinson ramp. It
uses an NMOS differential pair, PMOS current-mirror load, and two CMOS output
inverters. The output is high while `ramp < sample` and falls when the ramp
crosses the sample voltage.

Run:

```sh
make comparator
```

The test uses a 1.2 V/us ramp and measures crossing delay, output rails, and
average core power. Generated files under `work/` are not tracked by Git.

This is a functional continuous-time baseline, not a frozen architecture.
Offset Monte Carlo, PVT, kickback, common-mode range, and preamplifier or latch
alternatives remain required before block freeze.
