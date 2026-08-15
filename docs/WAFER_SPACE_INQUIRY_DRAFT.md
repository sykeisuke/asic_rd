# wafer.space Run 3 Technical Confirmation Draft

To: `info@wafer.space`
Subject: GF180MCU Run 3 confirmation: 3.3 V mixed-signal libraries, ESD, and power pads

Dear wafer.space team,

We are preparing a one-channel mixed-signal waveform-sampling ASIC for
GF180MCU Run 3. Our provisional choice is the `0p5x1` default pad ring with
the chip-on-board option. Before freezing schematics and the pad ring, could
you please confirm the following?

1. Is PDK/Ciel commit `f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7`
   the required or accepted Run 3 version?
2. Is project-template commit `0de7e394337a1f7f5303ac7a3681bf2481b58176`
   an accepted Run 3 baseline?
3. Is this all-3.3 V library combination accepted for fabrication, precheck,
   and COB?
   - Standard cells: `gf180mcu_as_sc_mcu7t3v3`
   - Pad library: `gf180mcu_ocd_io`
4. Are the following I/O cells accepted at that PDK commit?
   - `gf180mcu_ocd_io__in_c`, `in_s`, `bi_24t`, `asig_5p0`
   - `gf180mcu_ocd_io__vdd`, `vss`, `dvdd`, `dvss`
5. For `gf180mcu_ocd_io__asig_5p0`, what ESD topology/rating, clamp range,
   leakage, and input capacitance apply? Is it suitable for both analog input
   and buffered monitor output?
6. The current `0p5x1` template has one core `VDD/VSS` pair and seven I/O
   `DVDD/DVSS` pairs. Can a signal-pad position be changed to another core
   power pair so analog-core and digital-core current can be measured
   separately while retaining compatibility with the default COB board?
7. If not, which supported default-ring/slot configuration provides separate
   analog-core, digital-core, and I/O supplies with at least six analog pads?
8. Must the default power-pad positions and nets remain unchanged for COB?
   Could you provide the COB breakout-board schematic and connector pinout?
9. Please confirm nominal/absolute-maximum rail voltages and required power-up sequence.
10. Which precheck image/version and final signoff checklist are authoritative for Run 3?

Our present nominal rail plan is `AVDD = digital-core VDD = IOVDD = 3.3 V`,
with separate analog and digital current measurement if the supported pad ring
allows it.

Thank you,

Keisuke Yoshihara
University of Hawaii
