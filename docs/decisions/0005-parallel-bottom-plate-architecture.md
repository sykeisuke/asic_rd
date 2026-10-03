# ADR 0005: Parallel conversion with bottom-plate sampling (Tape-out 1)

Date: 2026-09-18. Status: accepted (design review with the collaborating
IC-design group; recorded here from the meeting record and the design-team
slides of the same day).

## Decisions

1. **No analog MUX.** Every storage cell has its own comparator; one ramp is
   broadcast; the four Tape-out 1 cells convert in parallel. The MUX is not
   part of the IRSX architecture and does not scale.
2. **Hold capacitor = smallest drawable MIM, 54.5 fF** (FuseTop 27.2 um^2
   once Via4 placement/enclosure rules are met; the 25 um^2 rule floor is not
   drawable). Chosen over MOS and MOM because the MIM sits in M4/M5 above the
   comparator and costs no cell area ("unit cell area: MIM none, MOM extra,
   comparator decides"). MOM (0.57 fF/um^2 in M1-M4) is drawable and
   extractable with a field solver despite having no PDK model; MOS
   `cap_nmos` collapses with bias (the accumulation `_b` device is flat but
   uses active area).
3. **Bottom-plate sampling with the ramp applied to the capacitor.** The
   comparator then trips at a fixed reference, so its common-mode-dependent
   offset and its delay-vs-level spread do not enter the transfer function;
   the reference-plate switch opens first so its (signal-independent)
   injection is the only pedestal.
4. **8-bit ADC**, 32-bit frame `{cell3..cell0}`; 25 MSa/s sampling remains a
   board-controlled parameter (50 MSa/s discussed).

## Consequences established in this repository

- RTL: `digital/parallel_wilkinson_controller` (shared 8-bit Gray counter,
  four capture channels, timeout flags) and the 32-bit `asic_digital_top`;
  the sequential controller and its co-simulations are legacy.
- Cell method study (the exploration branch `keisuke/analog-explore`): bottom-plate sampling
  delivers its promise **only if the comparator senses the plate whose switch
  opened first** and the ramp drives the other plate. Then pedestal spread
  is 0.09 mV and gain error -0.02 % (input and ramp share the same
  capacitive divider). Sensing the input-side plate leaves 2-4 LSB of
  signal-dependent pedestal and +9 % parasitic gain error.
- Comparator spec to be re-derived for a fixed trip near 2.0 V (functional
  range vs accuracy); noise budget by transient-noise simulation, not kT/C
  alone (review comment: the comparator's input-referred noise dominates
  kT/C at these capacitor values).
- Ramp generator drives the connected cell nodes (4 x ~60 fF now; scaling
  to nF for 32k cells is a Tape-out 3 design problem).
- Digital-on-top integration preferred by the review (P&R tool routes to
  the analog macros); secondary ESD to be added locally at analog pads.

## Superseded

Spec v0.5 sections 5.1-5.5 (MUX, 1 pF, 6 bit, 24-bit frame), ADR 0002's
operating-point framing (the comparator common mode is now fixed at the trip).
