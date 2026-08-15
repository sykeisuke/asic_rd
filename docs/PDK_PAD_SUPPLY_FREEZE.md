# PDK, Pad, ESD, and Supply Freeze

Date: 2026-08-14

Provider: wafer.space GF180MCU Run 3

This sheet separates design choices that can be frozen from public provider
files from items that require written wafer.space confirmation.
The same values are machine-readable in
[`../config/wafer_space_run3.mk`](../config/wafer_space_run3.mk).

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

Until wafer.space responds, use 3.3 V in all simulations but do not freeze the
physical power net topology or start the final pad ring.

## ESD status

Use only the I/O/ESD structures included in the selected provider-supported pad
library. Do not create custom ESD structures for Tape-out 1. Public template
support proves that the cells can be instantiated by the flow; it does not by
itself establish the analog pad's guaranteed ESD level, allowed voltage/current,
input capacitance, leakage, or suitability for the COB service.

## Information required from wafer.space

This is the controlled information list, not an email draft. Record each
written answer, response date, provider contact, and supporting file or URL in
the table below before closing Gate A.

| ID | Required information | Status | Evidence |
| --- | --- | --- | --- |
| WS-01 | Exact accepted PDK/Ciel commit | [ ] | Pending |
| WS-02 | Accepted project-template commit | [ ] | Pending |
| WS-03 | Approved 3.3 V standard-cell and I/O-library combination | [ ] | Pending |
| WS-04 | Accepted I/O cell names and signoff views | [ ] | Pending |
| WS-05 | Analog-pad ESD, clamp, leakage, and capacitance limits | [ ] | Pending |
| WS-06 | Permission to add a core supply pair in the `0p5x1` ring | [ ] | Pending |
| WS-07 | Alternative slot/ring if separate supplies are unsupported | [ ] | Pending |
| WS-08 | COB fixed pad constraints, schematic, and connector pinout | [ ] | Pending |
| WS-09 | Rail limits and required power-up sequence | [ ] | Pending |
| WS-10 | Authoritative precheck image and signoff checklist | [ ] | Pending |

### Detailed acceptance questions

1. Is PDK/Ciel commit `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7`
   the required Run 3 submission version? If not, provide the exact commit.
2. Is template commit `0de7e394337a1f7f5303ac7a3681bf2481b58176`
   an accepted Run 3 baseline?
3. Is the 3.3 V combination `gf180mcu_as_sc_mcu7t3v3` plus
   `gf180mcu_ocd_io` accepted for fabrication, precheck, and COB?
4. Are `gf180mcu_ocd_io__in_c`, `in_s`, `bi_24t`, `asig_5p0`, `vdd/vss`,
   and `dvdd/dvss` the accepted cell names and views at that commit?
5. What ESD topology/rating, clamp range, leakage, and capacitance apply to
   `gf180mcu_ocd_io__asig_5p0`? Is it approved for analog input and monitor output?
6. For `0p5x1` COB, may a signal-pad position be replaced by an additional
   `vdd/vss` cell to create separately measurable AVDD and digital-core VDD?
7. If not, which supported slot/default-ring configuration permits separate
   analog-core, digital-core, and I/O supplies while retaining at least six
   analog signal pads?
8. Must all default power-pad positions and nets remain unchanged for the COB
   breakout PCB? Provide its schematic and connector pinout.
9. What are the nominal and absolute-maximum values for core and I/O rails,
   and what power-up sequence is required?
10. Which local precheck image/version and signoff checks are authoritative for Run 3?

## Exit criterion

Gate A closes only when the provider response is stored in the repository and
the specification, pad map, power-domain schematic, and PCB assumptions agree.
