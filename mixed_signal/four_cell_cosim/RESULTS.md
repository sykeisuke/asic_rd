# Four-cell co-verification results

Date: 2026-08-10

The transistor-level GF180 macro produced crossing intervals of 831,984 ps,
1,040,260 ps, 1,399,500 ps, and 1,771,850 ps. These values were automatically
converted into RTL comparator-edge stimuli without manually entering codes in
the testbench.

The real controller and counter captured `16, 20, 27, 35`, matching the four
ngspice timing-derived codes and preserving cell order in the packed 24-bit
output.

Result: PASS.
