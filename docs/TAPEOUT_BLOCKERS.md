# Tape-out closure blockers

Date: 2026-08-31 (originally 2026-08-11)

The repository now demonstrates the architecture through transistor-level
four-cell conversion, synthesizable control/readout, mixed-signal timing
transfer, and a DRC/LVS-clean digital GDS. It is not yet a tape-out-ready full
chip. The following items cannot be treated as optional:

1. wafer.space GF180MCU Run 3 is selected. Updated 2026-08-30: the provider
   issues no written confirmations (DRC-only checking, no IP guarantees), so
   acceptance of PDK commit `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7`, the
   3.3 V library set, and the pad ring is established by passing the
   automated precheck and COB checks on platform.wafer.space. The PDK/template
   commits match the public template `main` as of 2026-08-30; re-verify at
   purchase (early-bird 2026-09-30) and before submission.
2. Pad ring, package, and power domains are frozen: the `0p5x1` ring with a
   second core `vdd/vss` pair (`bidir[43:42]` positions) passed the platform
   CoB precheck on 2026-08-31. All grounds are common on the default COB
   breakout, so only `AVDD` is separately measurable. Analog ESD follows the
   conservative GF180MCU DRM rules (HBM-only pads plus local CDM secondary
   protection) instead of provider data. Remaining: reduce analog functions
   to the six true analog pads (test-MUX truth table) and design the
   `AVDD`/digital-core domain crossings and clamps.
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
substantial part of physical signoff. The slot purchase (early-bird
2026-09-30) is therefore the next external decision gate; the technical
provider constraints are closed.
