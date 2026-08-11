# Tape-out closure blockers

Date: 2026-08-11

The repository now demonstrates the architecture through transistor-level
four-cell conversion, synthesizable control/readout, mixed-signal timing
transfer, and a DRC/LVS-clean digital GDS. It is not yet a tape-out-ready full
chip. The following items cannot be treated as optional:

1. Confirm the MPW provider, accepted GF180 PDK commit, supply option, slot,
   submission date, and deliverable checklist.
2. Select the provider-qualified I/O and ESD cells and freeze the pad ring,
   package, and power domains.
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
