# 0009: Digital-on-top chip assembly on the wafer.space template

Date: 2026-09-24

Status: accepted (flow demonstration; the pad library and standard-cell
library deviations below stay open items of `PDK_PAD_SUPPLY_FREEZE.md`)

## Context

The chip has to be one GDS: the provider's pad ring and ID macros, the
digital top (`digital/asic_digital_top`), and the analog cells
(`mixed_signal/analog_layout`). Two ways to assemble it are usual:

- **analog on top** -- draw the top by hand, drop the digital block in
  as a hardened macro, route the few connections manually;
- **digital on top** -- the template's LibreLane `Chip` flow owns the
  top. The digital logic is soft, the analog cells are hard macros with
  LEF abstracts, and the router makes every connection.

The template (`wafer-space/gf180mcu-project-template`, frozen commit
`0de7e394`) is built for the second: `chip_top.sv` is the pad ring,
`chip_core.sv` the design, and `config.yaml` already places hard macros
(the ID cells, SRAMs) and connects their power through
`PDN_MACRO_CONNECTIONS`.

The analog cells were not usable as macros as drawn. Their ports are
Metal2 labels inside dense Metal2, there is no LEF, and a 6 um tall cell
falls between the top-level Metal5 power straps (75 um pitch), so PDN
cannot reach its supply.

## Decision

Digital on top, in `mixed_signal/top_placement/`, with the template's
files adapted rather than forked:

1. **The digital top is used as is.** Its four RTL files are read from
   `digital/` unchanged; `chip_core.sv` instantiates `asic_digital_top`
   and wires it to pads and macros. It is synthesised with the chip, not
   as a pre-hardened macro, so there is one timing run over the real pad
   and macro boundary.
2. **Each analog cell becomes a hard macro by wrapping, not editing.**
   `macros.py` places the cell unchanged in a 90 um tall wrapper, lands a
   Via2 on each signal pin and runs a Metal3 stub to the macro edge (the
   LEF pin), and brings VDD/VSS up to full-height Metal4 straps. 90 um
   guarantees one VDD and one VSS Metal5 strap crosses them wherever the
   macro sits. Metal1-4 are obstructed over the cell so nothing is
   routed across the analog devices. The wrapper is signed off on its
   own with the PDK deck (`gf180mcu.drc`) and, for `INV`, KLayout LVS
   against the cell's own netlist -- a stub that shorted or dropped a
   pin would fail there, in seconds rather than after a full-chip run.
3. **The test mode is in the core, outside the digital top.** A pad
   (`test_mode`) selects whether the Gray capture sees the comparator or
   a pad (`ext_compare`), which is specification 7.3's "digital test
   mode independent of the analog crossing" without changing the frozen
   digital top.
4. **The five analog pad-to-macro wires are drawn, not routed.**
   `librelane/analog_routes.tcl`, sourced from the PDN script, draws each
   as fixed special wiring: Metal2 down from the pad's `ASIG5V` finger,
   under the Metal3 core ring, a Metal3 jog at its own height, Metal2 to
   the macro edge, Via2 onto the pin (straight down, no jog, where the
   pin lies within a finger). Routing them was tried and measured:
   - `OpenROAD.PadRing` (`place_io_terminals`) marks every analog pad net
     special and the routers skip special nets -- the first full run
     left all five unrouted (Netgen: 5 extra layout nets);
   - with the flag cleared, detailed routing aborted inside the flow in
     every attempt (an `frAccessPoint` index out of range after "Post
     process initialize RPin region query"), with the top-level terminal
     on the bond pad or moved onto a Metal2 finger, on 22 threads or 1,
     while the same step re-run standalone from its saved config and
     state routed all five with 0 DRC errors. The cause was not found;
     drawing the wires removes the dependence on it.
   Drawn wires are also what an analog net wants: short, 1.2 um wide,
   no resizer buffers and no router-inserted antenna diodes.
5. **Magic DRC is not run** on the chip; KLayout `gf180mcu.drc` is the
   verdict (CLAUDE.md). LVS is the flow's Netgen LVS against the powered
   netlist, with the analog macros as black boxes -- it proves the chip's
   wiring to the macros, not the macros' insides.

## Consequences

- **Pad and cell library are not the frozen ones.** The container's PDK
  (`/foss/pdks`, the pinned commit) ships `gf180mcu_fd_io` and
  `gf180mcu_fd_sc_mcu7t5v0` only; `gf180mcu_ocd_io` and
  `gf180mcu_as_sc_mcu7t3v3` have LibreLane configs there but no
  `libs.ref` views. The chip therefore uses the template's defaults, the
  same 5 V-characterised library the digital top already uses (the
  recorded deviation). With `fd_io` the core and I/O supplies are one
  domain, so the separate `AVDD` pair of the frozen `0p5x1` ring is
  **not** built here. Retargeting needs those libraries installed at the
  pinned commit (`ciel enable ... --include-libraries all`, as the
  template's Makefile does) -- a separate change.
- **The comparator macro is a placeholder.** `CMP` is DRC-clean but its
  signal nets are unrouted (ADR 0006), so `wsa_cmp` gives the comparator
  its place, pins and power on the chip, not a working comparator. The
  test mode is what makes the digital path measurable regardless.
- **No CDM secondary protection** is drawn between the analog pads and
  the gates they reach (`vin`, `vramp`, `vbias`, `A`). The ESD design
  rule of `PDK_PAD_SUPPLY_FREEZE.md` (WS-05) is open for this chip.
- The provider ID macros are fetched from the template at the pinned
  commit into `work/template` at build time, not committed.
