# ASIC digital top and serial readout

The digital top integrates the parallel Wilkinson controller (sampling
sequence `s0/s1/s2[3:0]` and `ramp_rst` for the Analog_top macro, shared
8-bit counter, synchronous sampling of the cells' latched flags `q[3:0]`)
and a 32-bit synchronous shift register; `cnt_clk` forwards the conversion
clock to the macro's latches. Conversion completion loads
`{cell3, cell2, cell1, cell0}` (8 bits each) automatically. `serial_data`
then shifts LSB-first while `shift_en` is asserted on rising `clk` edges.
`conversion_timeout[3:0]` flags cells whose comparator never crossed (their
code reads `255`).

Run:

```sh
make digital-top
```

The test converts four cells in parallel (codes 16, 20, 27, 200), checks the
timeout flags, reconstructs the 32-bit frame at the serial interface, and then
maps the design to GF180 cells and runs 20 MHz pre-layout STA.

History: until 2026-10-28 the capture was asynchronous (`compare_high[3:0]`
as local capture clocks, Gray coding) with `acquire`/`ramp_connect`
outputs; until 2026-09-18 this top used the sequential 4-to-1 analog-MUX
controller with 6-bit codes and a 24-bit frame
(`digital/legacy/four_cell_wilkinson_controller`, kept for the legacy mixed-signal
co-simulations).
