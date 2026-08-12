# Simulation Guide

This project verifies the prototype in layers. A small simulation is not a
substitute for the integrated simulation: it isolates failures before the
blocks are connected.

## Analog simulations

| Command | Circuit under test | Main outputs | Purpose |
| --- | --- | --- | --- |
| `make nmos-dc` | One GF180 NMOS | `nmos_dc.raw`, CSV | Learn the PDK model and Id-Vds behavior |
| `make sampling-cell` | One sampling switch and one transmission gate | CSV, measurements | Check acquisition error, feedthrough, and droop |
| `make four-cell` | Four sampling cells | CSV, measurements | Check that four different samples are stored |
| `make four-cell-mux` | Four cells plus analog MUX | CSV, measurements | Check sequential selection and read disturbance |
| `make comparator` | Transistor comparator | CSV, measurements | Check crossing delay, output levels, and power |
| `make comparator-range` | Comparator over input range | range CSV | Check monotonic conversion over useful inputs |
| `make comparator-offset` | NMOS/PMOS comparator variants | offset CSV | Estimate systematic trip-point offset |
| `make ramp-generator` | Reset switch, current source, capacitor | CSV, measurements | Check reset level, ramp slope, and power |
| `make wilkinson-slice` | One sample cell, ramp, comparator | CSV, measurements | Check one complete 6-bit conversion slice |
| `make transfer` | Wilkinson slice at eight input values | `transfer.csv` | Check coarse ADC transfer monotonicity |
| `make four-cell-wilkinson` | Four cells, MUX, shared ramp, comparator | CSV, RAW, measurements | Integrated transistor-level analog verification |

## Viewing the integrated analog simulation

Run the integrated test from the Mac terminal:

```sh
make four-cell-wilkinson
```

Then use a terminal inside the VNC Linux desktop:

```sh
cd /foss/designs/simulations/gf180_four_cell_wilkinson
gaw work/four_cell_wilkinson.raw
```

Add these signals in order:

| Signal | Meaning |
| --- | --- |
| `vin` | Analog input waveform |
| `s0` to `s3` | Sampling commands |
| `hold0` to `hold3` | Voltages stored by the four cells |
| `sel0` to `sel3` | MUX selection commands |
| `mux_bus` | Selected stored voltage sent to the comparator |
| `reset` | Ramp reset command |
| `ramp` | Shared Wilkinson ramp |
| `compare_out` | Comparator decision event |

The expected sequence is input capture, four stable hold voltages, one MUX
selection per conversion slot, a new ramp in every slot, and one comparator
transition when the ramp crosses the selected voltage.

## What "full integration" means here

`make four-cell-wilkinson` is the current integrated transistor-level analog
simulation. It includes the entire prototype analog signal path, but it does
not place the RTL counter and controller inside ngspice. The measured crossing
time is converted to a 6-bit code using the counter period.

The next verification layer is `make four-cell-cosim`. It passes analog crossing
events to the RTL counter/controller simulation. This mixed abstraction is the
practical full-system test for the present prototype.

A literal full-chip transistor simulation containing extracted analog devices
and every synthesized digital gate is normally reserved for selected final
checks. Before tape-out, the important additions are post-layout extracted
simulation of the analog blocks and top-level checks of pads, supplies, clocks,
resets, and interfaces.

## Recommended order

1. Run the block simulation after editing a circuit.
2. Run `make wilkinson-slice` after changing the sampler, ramp, or comparator.
3. Run `make four-cell-wilkinson` after changing the integrated analog path.
4. Run `make four-cell-cosim` after changing analog/digital interfaces.
5. Run the complete regression before committing a milestone.
