# ramp_simple -- design recipe

From the requirements of `SPEC.md` to the two devices of `ramp_simple.spice`
and to the current the I/C source must deliver. Labels as in the spec. The
sizer `size_simple.py` carries the same chain in code and WRITES the
netlist and `data/sizing.json`; the `size` phase of `make ramp-simple`
re-derives both and fails if they differ.

## 1. The grid

| Quantity | Value | Chain |
| --- | --- | --- |
| LSB, TCOUNT, SLOPE, F_CLK | 5.859 mV, 50 ns, 117.19 mV/us, 20 MHz | [C] spec s.5, ADR 0024 |
| reset level VR_LO | 0.5 V - 11 LSB = 0.4355 V | [D] SPEC R2 |
| ramp top | VR_LO + 276 LSB = 2.053 V | [D] |

## 2. The current: I = C_UNIT x V_REF x F_CLK [D]

The slope must track the ramp capacitor. The only on-chip quantity that
tracks a MIM is another MIM, so the current is made by switching one unit
MIM (the cells' 5 um square, 54.52 fF at 0.5 V [P, the sizer's AC probe])
between V_REF and ground at the clock: I = 54.52 fF x 0.5 V x 20 MHz =
**0.545 uA**. V_REF = 5/33 AVDD, the tap ratio VR_LO already uses [C], so
the slope is ratiometric to AVDD like the rest of the ADC. At the MIM
corners the current is 0.600 / 0.491 uA (`mimcap_ss` / `ff`, +-10 % [P]):
the same +-10 % the ramp capacitor moves, which is the point.

## 3. The ramp capacitor: 83 unit MIMs [D]

I / C_total = SLOPE with C_total = N C_UNIT + NCELL C_CELL + C_RST:
N = V_REF F_CLK / SLOPE - (4 x 19 fF + 0.6 fF) / 54.52 fF = 85.3 - 1.4 =
83.9 -> **83**, rounded DOWN (4.525 pF at the mid-ramp voltage; C_total 4.602 pF): R3 forbids a slow ramp, so the unit rounding leaves the design slope +1.1 % fast (`size_slope_err_design_pct`), a constant gain term, calibrated; the cells' 76 fF is the other part that does not track (1.7 % of C). The source may then be up to 2.9 % slow before R3 is hit. The array matches the hold capacitors and
the reference capacitor unit for unit (same size, same orientation, same
surroundings), which a single 44.6 um square could not.

The C sweep of the first recipe (2..5 pF) stays as the record of why ~4 pF:
the per-decision kick, the reset kT/C and the cells' near-trip load
excursion fall as 1/C, the MIM area and the dump into `vrlo_ref` grow as C
(`size_c*pf_*`). 83 units sit at that knee.

## 4. The reset switch: 0.6 um [D]

The smallest 0.1 um step at which both hold at ss / 85 C / 3.0 V with the
current 10 % high (`size_rst_*`): the static drop I x Ron <= 0.5 LSB (R8a)
and tau = Ron x C_total <= 30 ns (R8b, e^-10 at the 300 ns gap). Its drain
junction on vramp (0.6 fF, 0.12 fF over the swing [P]) is 0.001 LSB of C(V).

## 5. What is handed to the I/C source

See SPEC s.6: 0.545 uA tracking the MIM corners, V_REF = 5/33 AVDD, the
20 MHz clock, output resistance >= 2.0 Gohm for a 0.05 LSB bow (0.67 Gohm
for 0.15), noise <= 0.11 LSB at code 255, ripple at vramp <= 0.05 LSB, no
switching into VR_LO / VREF, settled 1 % before T0.

## 6. Layout intent (the sheet's `layout:` line)

The 83 units (plus one dummy to a 7 x 12 rectangle) of the cells' unit MIM over
the cells, beside the vramp bus, dummy units on the array's edge if the
cells' and the reference unit are not adjacent; the reset switch at the
vrlo end of the bus.
