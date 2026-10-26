# Analog_top: conceptual pin list

**Analog_top_v4 (2026-10-10):** `VRLO` is no longer a pin. It is made inside
the macro by `vrlo_ref` (ADR 0018, 0020); the `VRLO` row below and its count
in the analog pin budget are historical. The rest of this list is as copied.

**Analog_top (2026-10-13):** one VDD/2 buffer (`midref`, ADR 0021). `vbl` is
the `vref` net: the `XVBL` row and the `vbl` bus below are historical, and
`bias_gen` has no `ivbl` output.

Copied into Analog_top_v3 on 2026-10-10 with only the plate names swapped
(v3: `bot[i]` = S2 / comparator side, floating; `top[i]` = S0 / S1 side,
driven). Otherwise the 2026-10-07 text below is unchanged.

Date: 2026-10-07. This is conceptual. It has not been netlisted, simulated
or drawn. The same list in machine-readable form is in [`pins.csv`](pins.csv).
The floorplan and rationale are in [`v2_record/README_v2.md`](v2_record/README_v2.md).

Conventions used throughout:

- **Dir** is seen from the analog macro.
- **Status**:
  - `core`: the net exists today in a recorded deck, and the value is read
    from that deck or its run.
  - `proposed`: the net is needed for spec §7.3 test access or for chip
    integration, and no circuit exists for it yet.
  - `open`: the net is needed, but where it comes from is undecided.
- Bus indices `[3:0]` are the cell number. Cell `i` keeps the same index on
  every bus.
- Every signal that crosses into the macro from the digital macro changes
  supply domain. Both domains are 3.3 V and the ground is common, so no
  level shifter is needed, but the receiving side gets a buffer
  (TOPDOWN §2).

## 1. Supplies (4 pins)

| Pin | Dir | Domain | Nominal | Feeds | Notes | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `AVDD` | supply | AVDD | 3.3 V | cells (switch inverters, comparators), `bias_gen_K`, `bias_gen_C`, both `midref_b`, `ramp_gen`, `bias_gen_R` | Comes from the re-typed `bidir[43:42]` pair through a dedicated strap and never through the core ring (TOPDOWN §4). NOISE_BUDGET: <= 2 uV/rtHz below ~300 kHz | core |
| `AVSS` | supply | common GND | 0 V | the same blocks | All grounds are common on the COB breakout (TOP_LEVEL_INTERFACE) | core |
| `DVDD` | supply | VDD core | 3.3 V | 4 x `tspc_dff`, clock spine, control receivers | NOISE_BUDGET L7 / `cmp_tspc` S11: the latch is not on AVDD | core |
| `DVSS` | supply | common GND | 0 V | same | — | core |

## 2. Analog signal pins (2 core + test, see §4)

| Pin | Dir | Range / value | Internal net and load | Driven by | Timing | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `VIN` | A in | 0.5-2.0 V (8-bit range, LSB 5.859 mV) | `vfe` bus to the `a` side of 4 x S0 TG (NMOS 0.50/0.28 + PMOS 1.00/0.28, drawn junctions), each charging `top[i]` (54.52 fF plus parasitics) | `analog[0]` pad, then the CDM strip | Tracking: S0 R_on <= 5.59 kohm, tau 313 ps against a 650 ps budget (`switches.spice`). The board driver has to settle 4 x C_S plus the pad and the bus | core |
| `VRLO` | A in | 0.5 V (`VR_LO`) | `vrlo`: the `ramp_gen` OTA's + input. **Gate only, no DC current** (`ramp_gen.spice`) | **open**: board pad, divider + decap, or a third buffer | Static. Its noise and offset appear as ramp offset in every code | open |

## 3. Digital pins (14 in, 4 out)

### 3.1 Inputs from the digital macro (or the debug pads)

| Pin | Width | Level | Function | Load inside the macro | Timing (bench values, `unit_cell_bps/CONTRACT.md`) | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `S2[3:0]` | 4 | 0 / AVDD, **HIGH = closed** | Bottom-plate reset switch: `vref` to `bot[i]`. **Its falling edge is the sampling instant of cell i** | 1 min inverter (N 0.44 / P 0.88, L 0.28) + gate of the S2 NMOS 0.36/0.28 | Track while high. Falls at `TS` (300 ns in the bench; 10/50/90/130 ns for the frozen 4-cell schedule). Edges 100 ps in the bench | core |
| `S0[3:0]` | 4 | 0 / AVDD, HIGH = closed | Input TG: `vfe` to `top[i]` | 1 min inverter + S0 TG gates | Opens at `TISO` = S2 fall + `TNOV` (5 ns). `TNOV` sets the dynamic error and moves the offset by about 1 LSB, so it is kept as a separate line (TOPDOWN §1, §3.3 `S0_DBG`) | core |
| `S1[3:0]` | 4 | 0 / AVDD, HIGH = closed | Ramp TG: `vramp` to `top[i]` | 1 min inverter + S1 TG gates | Closes at `TCONN` = TISO + 5 ns while `vramp` = `VRLO` (ramp still in reset). Stays closed through the conversion | core |
| `RAMP_RST` | 1 | 0 / AVDD, **HIGH = reset** | `ramp_gen` `rst`: shorts CI, so `vramp` = `vrlo` | gate of `XRST` | Falls at `TR` = 400 ns to start the ramp. 0.5 -> 2.0 V in `TRAMP` = 12.8 us plus a 20-count overrun. Recovery after reset is 578 ns (`ramp-gen` run) | core |
| `CNT_CLK` | 1 | 0 / DVDD | Count clock to the 4 TSPC latches. **The latch samples on the FALLING edge**, and the Gray counter in the digital macro increments on the rising edge (half a count apart, NOISE_BUDGET L2) | 4 x TSPC clock gates (XN2, XP6, XN4, XP8) plus the spine | 20 MHz, `TCOUNT` = 50 ns. Edge rate up to 6 ns verified at typical (8 ns at ss/0/3.0, 4 ns at ff/85/3.6) | core |

The S0, S1 and S2 inputs are 12 lines. The complements are made inside
each cell by three minimum inverters. The pin carries one line per switch
and never a complement (CONTRACT.md).

### 3.2 Outputs to the digital macro

| Pin | Width | Level | Function | Drive | Timing | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `Q[3:0]` | 4 | 0 / DVDD | TSPC `q` of cell i, which is the comparator decision retimed to `CNT_CLK`. It is HIGH before the crossing and makes **one monotonic fall** at the first `CNT_CLK` fall after `dout[i]` falls. It is `compare_high` of `digital/wilkinson_gray_counter`, and its falling edge is that block's capture clock. The RTL is unchanged | Driver into 50 fF (XN10 1.0 / XP11 2.0 um) | clock-to-q 0.77-1.25 ns, q fall 0.57-0.71 ns into 50 fF (`runs/cmp-tspc/20261006T053805Z`). Aperture jitter 1.7 ps | core |

## 4. Test access (proposed; spec §7.3 and TOPDOWN §3.3)

None of these exist as circuits. Each one names what it costs the signal
path.

| Pin | Dir | Function | Implementation idea | Cost / risk to the core | Spec §7.3 item |
| --- | --- | --- | --- | --- | --- |
| `EXT_RAMP` | A in | External ramp injected in place of `ramp_gen` | TG pair in front of the `vramp` bus, selected by `RAMP_SEL` | A series R into every S1 path. Size it against the ramp-lag figure in `switches.spice` (7.0 uV with today's S1) | External ramp input |
| `RAMP_SEL` | D in | 0 = internal ramp, 1 = `EXT_RAMP` | Config bit from the digital macro | — | same |
| `AMON` | A out | Buffered monitor: `vramp`, `vref`, `vbl`, or the replica cell's bottom plate | Unity-gain buffer behind an analog mux, selected by `AMON_SEL[1:0]` | The mux leakage and C must not sit on a signal cell's `bot` | Ramp monitor, VHOLD observation |
| `AMON_SEL[1:0]` | D in | Monitor select | Config bits | — | same |
| `ATEST` | A io | Bias current in/out on `pbias_k` / `pbias_c` / `pbias_r`, replica MOS, MIM/MOM replica, standalone comparator input | Analog test mux, off by default | Any gate-connected path needs the CDM network | Replica structure, comparator standalone |
| `CMP_SA_OUT` | D out | Output of a standalone replica `cmp` + TSPC with `inn` from `ATEST` and `inp` on `vbl` | A fifth comparator copy in the test zone. The four signal comparators stay untouched | Area only | Comparator standalone mode |
| `BIAS_EN` | D in | Enable for `bias_gen_K`, `bias_gen_C` and `bias_gen_R` (power-down) | Would need a disable path in the beta multiplier that keeps the start-up working | No block has one today. It changes `bias_gen`, which needs re-verification | Safe power-up (§9.1) |
| `REP_*` | A io | Replica cell (S0/S1/S2 + MIM + cmp) with its bottom plate buffered to `AMON` | A fifth cell placed after cell 3, on the same buses | It adds 1 load to `vfe`, `vramp`, `vref`, `vbl` and `pbias_k`. The four signal cells keep their alpha | VHOLD observation |

`VREF` and `VBL` are deliberately **not** pins. They are on-chip VDD/2
buffers. To sweep them from the board, as TOPDOWN §3.3 planned, an override
TG on each with its own pad would be needed. That costs two analog pads
the ring does not have spare, so the proposal monitors them through `AMON`
instead.

## 5. Internal nets, which are not pins

These are listed because the floorplan is drawn around them.

| Net | Count | From -> to | Value / character | Floorplan rule |
| --- | --- | --- | --- | --- |
| `vfe` | 1 bus | `VIN` pad -> 4 x S0 `a` | follows VIN | Short and wide. It enters from the north |
| `vramp` | 1 bus | `ramp_gen` -> 4 x S1 `a` (and 2 pF `XCO`) | 0.5 -> 2.0 V, 117.2 kV/s | One trunk along the south of the cells, away from `bot[i]` |
| `vref` | 1 bus | `XVREF` (`midref_b`) -> 4 x S2 `a` | 1.65 V (VDD/2). Takes an 82 fC kick per S2 | Decap near the cells |
| `vbl` | 1 bus | `XVBL` (`midref_b`) -> 4 x cmp `inp` | 1.65 V. The comparator decision kicks it (4.64 mV with v2; not measured with v3) | Star vs bus is open (README §4 #3) |
| `pbias_k` | 1 line | `bias_gen_K` (dedicated, **not designed**) -> 4 x cmp `pbias` | 1.931 uA per tail finger nominal. >= 1.20x at ss/85 C, >= 1.10x at ss/27 C (ADR 0015) | Shared only by the comparators, so it is a crosstalk path with `vbl` |
| `pbias_c` | 1 line | `bias_gen_C` -> 2 x `midref_b` `pbias` | PMOS gate line, 3.1314 uA leg | **Never shared with the ramp** (ADR 0012) or the comparators (ADR 0015) |
| `pbias_r` | 1 line | `bias_gen_R` -> `ramp_gen` `pbias` | the same design, a separate instance | Stays inside the ramp block |
| `nbias_c`, `nbias_r` (and `bias_gen_K`'s own, if it has one) | 1 each | inside each generator | start-up sense | Local. The cmp `nbias` port is a no-connect |
| `bot[i]` | 4 | MIM bottom plate <-> S2 `b` <-> cmp `inn` | **Floating, high impedance** during conversion | No digital line over or beside it |
| `top[i]` | 4 | MIM top plate <-> S0 `b`, S1 `b` | always driven | Take the larger-parasitic MIM electrode |
| `dout[i]` | 4 | cmp `dout` -> TSPC `d` | Falls at the crossing. Load 1.9 fF | One short vertical hop into the latch strip |
| `s0b`, `s1b`, `s2b` `[i]` | 12 | inverters inside each cell | complements | Local |

## 6. Pin count

| Group | Core | Proposed test |
| --- | ---: | ---: |
| Supplies | 4 | — |
| Analog in/out | 2 (`VIN`, `VRLO`) | 3 (`EXT_RAMP`, `AMON`, `ATEST`) |
| Digital in | 14 (`S0/S1/S2[3:0]`, `RAMP_RST`, `CNT_CLK`) | 4 (`RAMP_SEL`, `AMON_SEL[1:0]`, `BIAS_EN`) |
| Digital out | 4 (`Q[3:0]`) | 1 (`CMP_SA_OUT`) |
| **Total** | **24** | **+8** (+ replica cell nets inside) |

At chip level, the analog pads this uses are `VIN`, `EXT_RAMP`, `AMON` and
`ATEST`, plus `VRLO` if it comes from the board. That is 4 or 5 of the 6
analog pads. Two analog pads freed by on-chip `VREF`/`VBL` are left for
the rest.
