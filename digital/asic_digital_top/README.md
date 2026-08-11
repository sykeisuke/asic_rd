# ASIC digital top and serial readout

The digital top integrates the four-cell conversion controller, Gray-coded
capture counter, and a 24-bit synchronous shift register. Conversion completion
loads `{cell3, cell2, cell1, cell0}` automatically. `serial_data` then shifts
LSB-first while `shift_en` is asserted on rising `clk` edges.

Run:

```sh
make digital-top
```

The test covers four conversion captures and complete 24-bit reconstruction at
the external serial interface, followed by GF180 technology mapping.
