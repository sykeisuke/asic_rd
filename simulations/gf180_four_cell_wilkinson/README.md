# GF180 four-cell Wilkinson macro

This transistor-level integration test combines four transmission-gate sample
cells, a resettable 4-to-1 analog mux, one shared ramp generator, and one shared
continuous-time comparator. The cells are converted sequentially in 2.9 us
slots.

Run:

```sh
make four-cell-wilkinson
```

The run produces both a text waveform and a GUI waveform:

- `work/four_cell_wilkinson.csv`: inspect or process with scripts.
- `work/four_cell_wilkinson.raw`: open with GAW from the VNC desktop terminal:

```sh
cd /foss/designs/simulations/gf180_four_cell_wilkinson
gaw work/four_cell_wilkinson.raw
```

In GAW, add `vin`, `hold0` through `hold3`, `mux_bus`, `ramp`, and
`compare_out`. These signals show the complete analog path from acquisition
through sequential Wilkinson conversion.

This macro integrates the transistor-level analog path. The digital counter
and controller are verified separately in RTL and then connected through the
analog-to-digital co-simulation. Simulating all synthesized digital gates and
all analog transistors together is intentionally not the baseline flow because
it is slow and adds little value before layout extraction.

The provisional complete-flow gate requires four comparator crossings,
strictly monotonic 6-bit codes, no more than three counts of error relative to
the nominal input/slope prediction, and less than 200 uW average analog-core
power. These relaxed limits demonstrate integration and are not final ADC
linearity specifications.
