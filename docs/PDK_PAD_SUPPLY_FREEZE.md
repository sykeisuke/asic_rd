# PDK, Pad, ESD, and Supply Freeze

Date: 2026-08-14 (Gate A redefined 2026-08-30)

Provider: wafer.space GF180MCU Run 3

This sheet separates design choices that can be frozen from public provider
files from items that require validation against the provider's automated
checks.
The same values are machine-readable in
[`../config/wafer_space_run3.mk`](../config/wafer_space_run3.mk).

## Gate A redefinition (2026-08-30)

A direct provider inquiry was answered by wafer.space (Tim Ansell,
2026-08-30) as follows: wafer.space provides no design support and issues no
written confirmations; it performs DRC checking only and gives no guarantee
that any IP works or is cross-compatible; COB packaging is granted to any
design that passes the COB checks on <https://platform.wafer.space>, with all
devices bonded identically to the fixed pad positions.

Gate A therefore no longer waits for written provider answers. Its authority
is replaced by three pillars:

1. **Automated checks are the arbiter.** Acceptance questions are resolved by
   running the candidate GDS (a padring-only build is sufficient) through the
   public `gf180mcu-precheck` and the platform's precheck and COB checks.
2. **ESD is a conservative design rule, not a provider datum.** No analog-pad
   ESD characterization will be provided. The GF180MCU design-manual rules are
   adopted as requirements: analog signal pads carry HBM protection diodes
   only; any pad wired to a gate shall add a local secondary/CDM network
   (CDM diode perimeter greater than 25 um, series poly resistor greater than
   50 ohm) next to the protected devices.
3. **Community evidence replaces qualification data.** Silicon experience with
   the selected cells is gathered from prior-run projects (`ws-run1`,
   `ws-run2` repositories) and the provider's Discord community.

## Frozen design baseline

| Item | Status | Frozen value |
| --- | --- | --- |
| Provider template | [x] | `wafer-space/gf180mcu-project-template` commit `0de7e394337a1f7f5303ac7a3681bf2481b58176` |
| PDK family/variant | [x] | `gf180mcuD`, five metals, 11K top metal |
| PDK/Ciel commit | [x] | `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7` |
| Analog primitive voltage | [x] | 3.3 V `nfet_03v3` / `pfet_03v3` |
| Analog supply target | [x] | `AVDD = 3.3 V`, `AVSS = 0 V` |
| Digital core supply target | [x] | `DVDD_CORE = 3.3 V`, `DVSS_CORE = 0 V` |
| I/O supply target | [x] | `IOVDD = 3.3 V`, `IOVSS = 0 V` |
| Digital standard cells | [x] | `gf180mcu_as_sc_mcu7t3v3` |
| Pad library | [x] design baseline | `gf180mcu_ocd_io` dual-voltage I/O library |
| Slot candidate | [ ] | `0p5x1` default ring plus COB, pending power/ESD answer |

The repository's earlier digital physical result uses
`gf180mcu_fd_sc_mcu7t5v0` and a 5 V physical corner. It is flow evidence only,
not Tape-out 1 signoff. The digital macro must be regenerated and signed off
with `gf180mcu_as_sc_mcu7t3v3`.

## Selected I/O cells

Names follow the provider template's abstraction. Final pin usage and control
ties must be verified against the installed views at the frozen PDK commit.

| Function | Selected cell |
| --- | --- |
| Core power | `gf180mcu_ocd_io__vdd`, `gf180mcu_ocd_io__vss` |
| I/O power | `gf180mcu_ocd_io__dvdd`, `gf180mcu_ocd_io__dvss` |
| Clock/reset input | `gf180mcu_ocd_io__in_c` / `gf180mcu_ocd_io__in_s` after input review |
| Configurable digital I/O/output | `gf180mcu_ocd_io__bi_24t` with fixed control ties |
| Analog signal | `gf180mcu_ocd_io__asig_5p0` as instantiated by the official template |
| Corner/filler/break cells | Provider-template generated cells; do not hand-select before padring build |

## Power-ring conflict requiring provider confirmation

The published `0p5x1` default configuration contains:

```text
Core domain: 1 x VDD pad, 1 x VSS pad
I/O domain:  7 x DVDD pads, 7 x DVSS pads
Analog pads: 6
```

The official template keeps `VDD/VSS` separate from `DVDD/DVSS` when
`gf180mcu_ocd_io` is selected. It does not define separate analog-core and
digital-core rails. Therefore `AVDD` and `DVDD_CORE` cannot yet be claimed as
separately measurable with an unchanged `0p5x1` default ring.

Two findings from the public COB repository
(`wafer-space/chip-on-board-wire-bonded-pcbs`, 2026-08-30) bound this
requirement:

- **All grounds are tied together on the default breakout COB package.**
  Separately measurable `AVSS` is therefore physically impossible with the
  default COB. The supply-separation requirement is reduced to `AVDD` only.
- The Run 1 breakout pad map designates `VDD Core` and `PWR Aux` positions,
  and the COB rules fix only the wirebonding layout, PCB footprint, and
  connector position while leaving traces, signal types, and net assignments
  user-definable. An additional core supply pair therefore appears feasible.

Whether one bidirectional pad position may be re-typed into a second
`gf180mcu_ocd_io__vdd/vss` pair (keeping every bond-pad position unchanged) is
resolved empirically: build the modified padring from the provider template
and pass it through the platform precheck and COB checks. Until that
experiment passes, use 3.3 V in all simulations but do not freeze the physical
power net topology or start the final pad ring.

## ESD status

Use only the I/O/ESD structures included in the selected provider-supported pad
library. Do not create custom ESD structures for Tape-out 1. Public template
support proves that the cells can be instantiated by the flow; it does not by
itself establish the analog pad's guaranteed ESD level, allowed voltage/current,
input capacitance, leakage, or suitability for the COB service.

## Gate A information items and their resolution

Originally a written-confirmation list. Re-scoped 2026-08-30: wafer.space
issues no written confirmations, so each item is closed by public-repository
evidence, by a conservative design rule, or by an automated platform check.

| ID | Required information | Status | Evidence / closure route |
| --- | --- | --- | --- |
| WS-01 | Exact accepted PDK/Ciel commit | [x] public, re-verify at submission | Template `main` Makefile pins `PDK_COMMIT ?= f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7` (matches this repo's freeze). The pin is updated periodically; re-check at purchase and again before submission |
| WS-02 | Accepted project-template commit | [x] public | Frozen commit `0de7e394` is `main` HEAD as of 2026-08-30 |
| WS-03 | Approved 3.3 V standard-cell and I/O-library combination | [~] template-supported | `SCL=gf180mcu_as_sc_mcu7t3v3` and `PAD=gf180mcu_ocd_io` are official template build options (`macros_3v3.yaml`, `pdn_3v3_sram.tcl`). Final acceptance = passing platform precheck; no written approval exists |
| WS-04 | Accepted I/O cell names and signoff views | [x] public | Template `src/chip_top.sv` instantiates exactly `gf180mcu_ocd_io__{vdd,vss,dvdd,dvss,in_s,in_c,bi_24t,asig_5p0}` (clock uses `in_s`; reset and inputs use `in_c`) |
| WS-05 | Analog-pad ESD, clamp, leakage, and capacitance limits | [x] closed by design rule | No data will be provided. Adopt GF180MCU DRM rules: HBM diodes only on `asig` pads; add local CDM secondary protection (diode perimeter > 25 um, poly series R > 50 ohm) at every gate-connected pad; no reliance on characterized limits |
| WS-06 | Extra core supply pair in the `0p5x1` ring | [~] local PASS 2026-08-31 | Padring experiment (template fork, branch `avdd-core-pair-experiment`): `bidir[43:42]` re-typed to a second `gf180mcu_ocd_io__vdd/vss` pair with the 3.3 V library set. `gf180mcu-precheck --cob` passes the COB pad-mask check, KLayout antenna, Magic DRC, and KLayout DRC with zero violations; only empty-core minimum-density artifacts remain. Final confirmation: the platform.wafer.space run |
| WS-07 | Alternative slot/ring if separate supplies are unsupported | [x] fallback documented | `1x1` full slot exposes two `VDD Core` positions and two `PWR Aux` positions on the Run 1 breakout map |
| WS-08 | COB fixed pad constraints, schematic, and connector pinout | [~] public, run-specific | `wafer-space/chip-on-board-wire-bonded-pcbs` publishes the Run 1 `0p5x1` KiCad schematic/PCB, the 74-pad map, and the 70-pin mezzanine connector (LCSC C19089236 / C19089262). Marked run-specific; watch for a Run 3 revision. All grounds are common on the breakout |
| WS-09 | Rail limits and required power-up sequence | [~] datasheet only | GF180MCU PDK datasheet absolute maxima apply; no provider-specific sequencing data exists. Design for simultaneous 3.3 V ramp of all rails |
| WS-10 | Authoritative precheck image and signoff checklist | [x] public | `wafer-space/gf180mcu-precheck` (latest tag 1.7.3) runs top-cell/origin/DBU/layer/slot-size, density, antenna, Magic DRC, and KLayout DRC. The platform's own run at submission is authoritative |

### Remaining community questions

The only items still worth asking (on the provider's Discord, addressed to
prior-run participants rather than to the provider):

1. Has any prior-run project re-typed a bidirectional pad position into an
   extra `vdd/vss` core pair on a default ring and passed the platform COB
   checks?
2. Any silicon experience with `gf180mcu_ocd_io__asig_5p0` as analog input or
   buffered monitor output (leakage, capacitance, ESD behavior)?
3. Any precheck or COB-breakout gotchas for all-3.3 V designs
   (`gf180mcu_as_sc_mcu7t3v3` everywhere)?

## Exit criterion

Gate A closes when (a) the padring experiment GDS — including the extra core
supply pair, or the documented fallback if it fails — passes the public
precheck and the platform precheck/COB checks, (b) the run is purchased, and
(c) the specification, pad map, power-domain schematic, and PCB assumptions
agree with the passing configuration and are recorded in this repository.
