# Tape-out closure blockers

Date: 2026-08-11

The repository now demonstrates the architecture through transistor-level
four-cell conversion, synthesizable control/readout, mixed-signal timing
transfer, and a DRC/LVS-clean digital GDS. It is not yet a tape-out-ready full
chip. The following items cannot be treated as optional:

1. wafer.space GF180MCU Run 3 is selected. Reconfirm its published 2026-12-16
   deadline and obtain written acceptance of PDK commit `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7`,
   the 3.3 V library set, GDS checklist, and precheck version.
2. Select the provider-qualified I/O and ESD cells and freeze the pad ring,
   package, and power domains. The design baseline is `gf180mcu_ocd_io`, but
   analog ESD limits and separate AVDD/digital-core supply support require
   provider confirmation. Validate the provisional `0.5x1` default-ring COB
   plan and reduce analog functions to its six true analog pads.
3. Draw and verify the analog SCA, mux, ramp, comparator, bias, and test-access
   layouts; run extraction and post-layout simulations.
4. Complete PVT and mismatch Monte Carlo verification with frozen devices and
   capacitor structures.
5. Integrate analog macros with the digital LEF/GDS, add external-ramp bypass,
   test modes, decoupling, fill, and top-level DRC/LVS.
6. Design the package/carrier and evaluation PCB after provider pin constraints
   are known.
7. Run provider signoff and archive a clean-checkout submission package.

Changing foundry or standard-cell/I/O libraries after item 2 will invalidate a
substantial part of physical signoff. Provider confirmation is therefore the
next external decision gate.
