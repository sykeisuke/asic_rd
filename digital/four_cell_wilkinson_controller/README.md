# Four-cell Wilkinson controller

This synthesizable controller sequences a shared Wilkinson conversion macro:

1. deselect all cells and reset the mux bus and ramp;
2. select one sample cell and allow the analog bus to settle;
3. release the ramp and start the 6-bit counter;
4. capture the comparator crossing code;
5. repeat for four cells and pulse `done`.

The four codes are exposed as `{cell3, cell2, cell1, cell0}` in one 24-bit bus.
Run functional verification and GF180 technology mapping with:

```sh
make controller
```

`compare_high` crosses from the analog comparator into the clocked digital
domain. Synchronization and metastability characterization are still required
before signoff.
