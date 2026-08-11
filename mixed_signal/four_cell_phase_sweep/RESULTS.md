# Comparator clock-phase sweep results

Date: 2026-08-10

The nominal cell-2 crossing is 1,399,500 ps after ramp release, only 500 ps
before a 20 MHz counter edge. Shifting all analog crossing times gives:

| Offset | Codes (cell 0, 1, 2, 3) |
| ---: | --- |
| -2000 ps | 16, 20, 27, 35 |
| -1000 ps | 16, 20, 27, 35 |
| -600 ps | 16, 20, 27, 35 |
| -400 ps | 16, 20, 27, 35 |
| 0 ps | 16, 20, 27, 35 |
| +400 ps | 16, 20, 27, 35 |
| +600 ps | 16, 20, 28, 35 |
| +1000 ps | 16, 20, 28, 35 |
| +2000 ps | 16, 20, 28, 35 |

Cell 2 changes by one count between +400 ps and +600 ps, exactly at its
predicted +500 ps clock boundary. The other three cells remain unchanged over
this sweep. Cell 2 therefore has effectively no comfortable timing margin at
the nominal phase and is the priority case for CDC/metastability treatment.
