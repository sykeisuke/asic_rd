# Mixed-signal co-verification results

Date: 2026-08-10

The GF180 transistor-level slice produced a 1,639,520 ps conversion interval
and timing-derived code 32 for a 1.2 V input. The generated RTL stimulus drove
the comparator transition at that measured interval. The synthesizable 6-bit
counter captured code 32 without overflow.

Result: PASS.

During bring-up, a 25 ns clock-phase error produced RTL code 33 while the
timing-derived analog code was 32. Aligning the first conversion-clock edge
with the measured ramp-reset release restored code 32. Conversion-start phase
is therefore part of the digital/analog interface contract, not merely a
testbench detail.

The test establishes an automated interface contract between the analog and
digital domains. It does not yet model metastability when the comparator edge
falls close to a conversion-clock edge; clock-phase sweeps are the next CDC
verification requirement.
