# sample_seq: the on-chip sampling sequencer, requirements

Date: 2026-10-31. Cell `sample_seq` (ports `acq clk s2_0..3 s0_0..3 s1_0..3
vdd vss`), on DVDD. It closes the open item of the specification (§5.1 Must:
"the HOLD_REF-before-SAMPLE order is generated on chip"; §13 0.7-draft:
"the on-chip sequencer that derives the sampling controls from the clock is
not designed yet"). Decision record: ADR 0027.

Labels: [U] user, [C] contract, [P] PDK, [M] measured, [A] assumed, [D] derived.

## Inputs and outputs

| Pin | Meaning |
| --- | --- |
| `clk` | the 20 MHz count clock, the one clock of the chip (ADR 0024) [C] |
| `acq` | the digital controller's `acquire` level (1 = track), from a flop on `clk`'s rising edge [C] |
| `s2_k` | cell k's bottom-plate switch to VREF (S2 = HOLD_REF), HIGH = closed |
| `s0_k` | cell k's input transmission gate (S0 = SAMPLE) |
| `s1_k` | cell k's ramp connection (S1 = RAMP_CONNECT, per cell) |

The cell's own inverters (`atop_cell` XI0/XI1/XI2, AVDD) make the
complements; the sequencer drives only the true controls.

## Requirements

| # | Requirement | Gate |
| --- | --- | --- |
| Q1 | Order per cell. Entry: S2 opens, then S0 opens, then S1 closes. Re-entry (acq high again): S1 opens before S0 closes. [C] spec §5.1 | every PVT cell |
| Q2 | S2 → S0 open and S0 open → S1 closed, at least 5 ns each (VDD/2 crossings); re-entry S1 open → S0 closed also at least 5 ns [U] (user, 2026-10-30) | min over 45 PVT cells and both duty cycles ≥ 5.0 ns |
| Q3 | S0 open ≤ 15 ns after the clock edge (the top plate is isolated well before the macro bench's vin step at +20 ns); S2 open → S1 closed ≤ 25 ns (inside half a period) [A] | max over PVT |
| Q4 | Cell k samples at the k-th rising edge after the edge that sees `acq` low: the four S2 openings one period (50 ns) apart within 0.05 ns [C] ADR 0024, tolerance [A] | every PVT cell |
| Q5 | S2 opens ≤ 2 ns after the clock's rising edge (the sampling instant is the clock edge plus a fixed, cell-independent delay) [A] | every PVT cell |
| Q6 | The controls track (s2 = s0 = 1, s1 = 0) from a cold supply with `acq` high, and each control moves exactly once per direction per record (no glitch) [C] | every run |
| Q7 | No clock edge inside the sequencer while every cell is settled (tracking, or holding through the conversion): the delay line is gated [A] (no DVDD activity of the sequencer during the ramp) | every run |
| Q8 | DVDD power and energy per record (reported) | — |

## Not covered

Mismatch (the delay line averages ~20 cells per stage; no Monte Carlo of the
standard cells here), layout / route skew and PEX (Q2's sizer aims 0.25 ns
above 5 ns for them [A]), substrate coupling of DVDD edges into the cells.
