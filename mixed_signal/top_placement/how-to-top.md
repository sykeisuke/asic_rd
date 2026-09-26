# How the digital-on-top chip is built

This explains, step by step, how an analog layout ends up inside the
digitally placed-and-routed chip, using the wafer.space
[`gf180mcu-project-template`](https://github.com/wafer-space/gf180mcu-project-template)
(commit `0de7e394`) as the reference. The template does it for two SRAM
macros; this directory does it for three analog cells: the comparator
`CMP`, the cicpy inverter `INV`, and the gdsfactory inverter `INV_GF`.

```sh
make top-placement STAGE=macros   # build the analog macro views and sign them off (minutes)
make top-placement                # macros, then the whole chip (about 20 minutes)
```

The verdict is `runs/top-placement/latest/metrics.json`; results in
[`RESULTS.md`](RESULTS.md), design decisions in ADR 0009. The chip
described here, with all three macros, passed every check in
`runs/top-placement/20260925T050420Z/metrics.json`: wrappers DRC/LVS
clean, and 0 routing DRC, 0 setup/hold violations, 0 KLayout DRC,
0 LVS errors, 0 XOR, 0 antenna and 0 density errors on the full chip.

## The process in six steps

None of this is done by hand. `make top-placement` (or
`./scripts/sim.sh top-placement`, which also records the metrics) runs
all six steps, in order.

**1. Take the pad ring from the wafer.space template.**
The template's pad ring is copied into this directory as
[`src/chip_top.sv`](src/chip_top.sv), and its `0p5x1` die size and pad
order as [`librelane/slot_0p5x1.yaml`](librelane/slot_0p5x1.yaml).
Every run also clones the template at the pinned commit into
`work/template/`, for the provider ID and logo macros
(`scripts/run-top-placement.sh`).

```make
# config/wafer_space_run3.mk
WS_TEMPLATE_COMMIT := 0de7e394337a1f7f5303ac7a3681bf2481b58176
```

**2. Put the digital top inside the pad ring.**
The pad ring instantiates `chip_core` ([`src/chip_core.sv`](src/chip_core.sv)),
and `chip_core` instantiates the unchanged digital RTL. LibreLane
synthesises it and places it as ordinary standard cells.

```systemverilog
// src/chip_core.sv
asic_digital_top u_digital (
    .clk (clk), .rst_n (rst_n), .start (start),
    .compare_high (compare_high), ...
```

**3. Define the boundaries.**
The die is the template's `0p5x1` slot, and the core area inside the pad
ring is where cells and macros may go.

```yaml
# librelane/slot_0p5x1.yaml
DIE_AREA:  [0, 0, 1936, 5122]
CORE_AREA: [442, 442, 1494, 4680]
```

**4. Place and connect the analog cells as hard macros.**
[`macros.py`](macros.py) wraps each analog GDS (`CMP`, `INV`, `INV_GF`) in a
macro with edge pins and power straps. Then:
- [`librelane/macros.yaml`](librelane/macros.yaml) fixes where each macro sits;
- `src/chip_core.sv` connects its pins, the same way as any module.

```yaml
# librelane/macros.yaml
i_chip_core.u_cmp:
  location: [1200, 4540]
  orientation: N
```

**5. Route.**
LibreLane builds the power grid and routes every digital net and every
macro-to-logic net. The five analog pad-to-macro wires are the one
exception. The router skips them (section 4), so
[`librelane/analog_routes.tcl`](librelane/analog_routes.tcl) draws them
before routing.

**6. Run signoff inside LibreLane.**
At the end of the same run, LibreLane checks the chip:
- the PDK's KLayout `gf180mcu.drc` on the full die (Magic DRC is
  switched off in [`librelane/config.yaml`](librelane/config.yaml));
- Netgen LVS;
- antenna, density after fill, and the stream-out XOR.

[`check-top.awk`](check-top.awk) turns the counts into one PASS/FAIL line.

```sh
make top-placement STAGE=macros   # step 4's macro wrappers only, each with its own DRC/LVS (minutes)
make top-placement                # all six steps, about 20 minutes
# verdict: runs/top-placement/latest/metrics.json
```

The sections below go through each step in detail.

---

## 1. What "digital on top" means

The chip's top level is owned by the digital flow (LibreLane). The
digital logic is **soft**: RTL that LibreLane synthesises, places and
routes. Every analog block is a **hard macro**: a finished layout that
LibreLane places at a fixed location as a black box, connects to by its
pins, and copies into the final GDS unchanged. LibreLane never looks
inside a hard macro. It only needs to know its outline, where its pins
are, what it must not route over, and how to power it.

```text
chip_top          pad ring (template)                    src/chip_top.sv
 └─ chip_core     the design                             src/chip_core.sv
     ├─ asic_digital_top   soft logic (RTL, unchanged)   digital/asic_digital_top/
     ├─ u_cmp     hard macro wsa_cmp    ← CMP.gds
     ├─ u_inv     hard macro wsa_inv    ← INV.gds
     └─ u_inv_gf  hard macro wsa_inv_gf ← INV_GF.gds
 + gf180mcu_ws_ip__*   provider ID macros (hard, required)
```

The opposite style, "analog on top", draws the top by hand and drops the
digital block in as one hardened macro. The template is built for
digital on top, and so is this chip.

---

## 2. How the template integrates a macro (the SRAM example)

Five pieces, all in the template. Each has a counterpart here.

### 2.1 The RTL instantiates the macro like any module

`src/chip_core.sv`:

```systemverilog
gf180mcu_fd_ip_sram__sram512x8m8wm1 sram_0 (
    `ifdef USE_POWER_PINS
    .VDD (VDD), .VSS (VSS),
    `endif
    .CLK (clk), .CEN (1'b1), .GWEN (1'b0), .WEN (8'b0),
    .A ('0), .D ('0), .Q (sram_0_out)
);
```

The power pins exist only under `USE_POWER_PINS`. Synthesis and timing
see an unpowered netlist; LVS sees a powered one.

### 2.2 `MACROS` lists the macro's views and where to put it

`librelane/macros/macros_5v.yaml`:

```yaml
MACROS:
  gf180mcu_fd_ip_sram__sram512x8m8wm1:
    gds:  [pdk_dir::libs.ref/gf180mcu_fd_ip_sram/gds/...sram512x8m8wm1.gds]
    lef:  [pdk_dir::libs.ref/gf180mcu_fd_ip_sram/lef/...sram512x8m8wm1.lef]
    vh:   [pdk_dir::libs.ref/gf180mcu_fd_ip_sram/verilog/...__blackbox_pp.v]
    lib:
      "*_tt_025C_5v00": [.../...__tt_025C_5v00.lib]
      "*_ff_n40C_5v50": [...]
      "*_ss_125C_4v50": [...]
    instances:
      i_chip_core.sram_0: {location: [490, 500], orientation: N}
```

The instance name is the flattened hierarchical name:
`i_chip_core` (in `chip_top`) `.` `sram_0` (in `chip_core`).

### 2.3 What each view is for

| View | Used by | What it says |
| --- | --- | --- |
| `vh` black-box Verilog | synthesis, lint | the module exists and has these ports; don't synthesise it |
| `lib` liberty | STA, resizer | pin directions, capacitances, timing arcs (if any) |
| `lef` abstract | floorplan, placement, PDN, routing | outline (`SIZE`), pin shapes and layers (`PIN`), no-go areas (`OBS`) |
| `gds` layout | stream-out, DRC, antenna, XOR | the real geometry, merged into the chip GDS |
| (`spice`) | LVS, if the macro's inside is to be compared | here only used for the wrapper's own LVS |

For the SRAM the PDK ships all of these. **For an analog cell you make
them.** That is the whole job of `macros.py` here (section 3).

### 2.4 Power: `PDN_MACRO_CONNECTIONS` plus a grid that reaches the pins

```yaml
PDN_MACRO_CONNECTIONS:
- "i_chip_core.sram_0 VDD VSS VDD VSS"     # instance, power net, ground net, power pin, ground pin
```

This says which chip nets the macro's power pins belong to. The power
grid also has to physically reach those pins. The template's
`librelane/pdn/pdn_5v_sram.tcl` defines a grid per SRAM instance: extra
Metal4 stripes over the SRAM, connected down to its Metal3 power pins
(`add_pdn_connect -layers "Metal4 Metal3"`) and up to the chip's Metal5
straps.

### 2.5 Everything else is the flow

Once the four pieces above exist, LibreLane's `Chip` flow does the
rest: pad ring, fixed macro placement, standard-cell placement around
the macro, clock tree, routing to the macro's LEF pins, fill, seal
ring, and signoff with the macro's GDS merged in.

---

## 3. The same five pieces for the analog cells

### 3.1 RTL: `src/chip_core.sv`

```systemverilog
wsa_cmp u_cmp (
    `ifdef USE_POWER_PINS
    .VDD (VDD), .VSS (VSS),
    `endif
    .vin (analog[0]), .vramp (analog[1]), .vbias (analog[2]), .dout (cmp_dout)
);

wsa_inv_gf u_inv_gf (
    `ifdef USE_POWER_PINS
    .VDD (VDD), .VSS (VSS),
    `endif
    .A (compare_high), .Y (inv_gf_y)
);
```

Same pattern as the SRAM. `dout` drives the digital capture logic,
`inv_gf_y` drives a pad, and `vin`/`vramp`/`vbias` come from analog pads.

### 3.2 `MACROS`: `librelane/macros.yaml`

```yaml
  wsa_cmp:
    gds: [dir::../work/macros/wsa_cmp/gds/wsa_cmp.gds]
    lef: [dir::../work/macros/wsa_cmp/lef/wsa_cmp.lef]
    vh:  [dir::../work/macros/wsa_cmp/vh/wsa_cmp.v]
    lib: {"*": [dir::../work/macros/wsa_cmp/lib/wsa_cmp.lib]}
    instances:
      i_chip_core.u_cmp: {location: [1200, 4540], orientation: N}
```

The same schema as the SRAM entry. The difference is where the files
come from: `work/macros/`, written by `macros.py` at the start of every
run, instead of the PDK. One liberty file serves all corners (`"*"`),
because it carries no timing.

### 3.3 Making the views: `macros.py`

A drawn analog cell cannot be handed to LibreLane as it is:

| Problem with the raw cell | What the template's SRAM has instead | What `macros.py` does |
| --- | --- | --- |
| no LEF, `.lib` or black-box Verilog | shipped by the PDK | writes all four views, plus a SPICE for the wrapper LVS |
| ports are labels deep inside dense metal (`CMP`: Metal2; `INV_GF`: Metal1 only) | pins on the macro edge | lands a via on each port and runs a Metal3 stub to the **north edge**; the stub is the LEF pin |
| power only on internal metal, cell 6–10 µm tall | Metal3 power rings + a custom PDN grid | brings `VDD`/`VSS` up to **full-height Metal4 straps**; see 3.4 |
| no PR boundary (GDS layer 0/0) | has one | draws the macro outline on 0/0; `Magic.StreamOut` fails without it |
| cell names that can collide (`NFET03V3_W2_L0p28_NF2` in two cells) | unique | prefixes every cell with the macro name |

The cell itself is never modified. It sits inside a wrapper cell:

```text
 macro edge (north) ── Metal3 pin stubs ──┐   ┌── Metal4 VSS strap (full height)
 ┌──────────────────────────────────┬─┼───┼─┐
 │                                  │ │   │ │ ← 90 um tall
 │        (Metal1-4 OBS over        │ │   │ │
 │         the cell +1 um)          │ │   │ │
 │   ┌────────────────────────┐     │ │   │ │
 │   │ the analog cell, as is │ ◄───┘ │   │ │  Via1/Via2 onto each port
 │   └────────────────────────┘       │   │ │  Via2/Via3 onto VDD/VSS
 │                                    │   │ │
 └────────────────────────────────────┴───┴─┘
                      Metal5 chip power straps cross here → Via4 to the Metal4 straps
```

How each port is reached depends on what the cell drew there:

| Landing | Cell | Wrapper adds |
| --- | --- | --- |
| `Metal2` | `CMP` (all ports) | Via2 array on the port's Metal2 → Metal3 pad → stub |
| `Metal3` | `INV` (`A`, `Y` already on Metal3) | the stub overlaps the cell's Metal3; no via |
| `Metal1` | `INV_GF` (everything) | Via1 → Metal2 pad → Via2 beside it (never stacked) → Metal3; a Metal1 patch where the port is narrower than a Via1 (`Y`, 0.23 µm) |

Every coordinate in the `MACROS` table in `macros.py` was read off the
cell's GDS with `probe_pins.py`, not guessed:

```sh
./container.sh 'python3 probe_pins.py ../analog_layout/misc/build/gds/INV_GF.gds'
./container.sh 'python3 probe_pins.py --shapes ../analog_layout/misc/build/gds/INV_GF.gds 34/0'
```

Each wrapper is then signed off **on its own**, in minutes, before any
chip run (`STAGE=macros`):

- KLayout `gf180mcu.drc` on the wrapper (the PDK deck; density apart);
- KLayout LVS of the wrapper against the cell's own netlist. A stub that
  shorted two ports or missed one fails here, not after 20 minutes;
- LibreLane's own `get_bbox.tcl` through Magic, proving the PR boundary
  is readable.

### 3.4 Power: the difference from the SRAM

The template powers the SRAM with a **per-macro PDN grid** that adds
stripes over the SRAM. Here the macro **brings its supply up to Metal4
itself**, so the template's default macro grid is enough:

```tcl
# librelane/pdn_cfg.tcl (from the template, SRAM grids removed)
define_pdn_grid -macro -default -name macro ...
add_pdn_connect -grid macro -layers "Metal4 Metal5"
```

The chip's Metal5 straps run every 75 µm (`PDN_HPITCH`), so a 90 µm tall
macro always has one VDD and one VSS strap crossing its Metal4 straps,
wherever it is placed. `PDN_MACRO_CONNECTIONS` then names the nets,
exactly as for the SRAM:

```yaml
PDN_MACRO_CONNECTIONS:
- "i_chip_core.u_cmp VDD VSS VDD VSS"
- "i_chip_core.u_inv VDD VSS VDD VSS"
- "i_chip_core.u_inv_gf VDD VSS VDD VSS"
```

Either approach works. Straps in the macro make each macro
self-contained, and adding a cell doesn't need a new grid in Tcl.

### 3.5 Timing: `librelane/chip_top.sdc`

The SRAM's liberty has real timing arcs. The analog liberty files have
pin directions and loads only, so STA treats the macros' pins as
unconstrained. The one analog signal that matters to timing is the
comparator output, because it clocks the Gray-code capture registers.
So it is declared as a clock at the macro pin:

```tcl
create_clock -name comparator_event -period 50 [get_pins {i_chip_core.u_cmp/dout}]
```

plus the pad version of it for test mode, both asynchronous to the
conversion clock.

---

## 4. Where analog differs from the SRAM example: the pad nets

The template's analog pads (`gf180mcu_*_io__asig_5p0`) are wired to
nothing in its core. Here five of them go to macro pins, and LibreLane
does not route those nets:

- `OpenROAD.PadRing` puts each analog pad's top-level terminal on its
  bond pad and marks the net **special**. Routers skip special nets, so
  the first chip run came out with those five nets open (LVS: 40 errors).
- Making them routable led to detailed-routing aborts inside the flow
  (details in ADR 0009).

So the five analog wires are **drawn** by `librelane/analog_routes.tcl`,
which the PDN script sources before placement:

```text
pad ASIG5V Metal2 finger (y = 4746 um)
   │ Metal2, 1.2 um, passes under the Metal3 core ring
   ▼
   ●─── Metal3 jog at a height of its own (4650-4671 um) ───●
                                                             │ Metal2
                                                             ▼
                                               Via2 onto the macro's Metal3 pin stub
```

A pin that lies under a pad finger gets one straight Metal2 drop and no
jog. The digital router treats these wires as obstacles. `INV_GF`'s
pins are on core nets, not pad nets, so the router wires them normally,
the same way it wires the SRAM's pins.

| Net kind | Example | Who wires it |
| --- | --- | --- |
| macro pin ↔ core logic | `u_cmp/dout`, `u_inv_gf/A`, `u_inv_gf/Y` | LibreLane router (like the SRAM) |
| analog pad ↔ macro pin | `analog[0]` → `u_cmp/vin` | `analog_routes.tcl`, drawn |
| macro supply | `VDD`, `VSS` | PDN: Metal5 straps → Via4 → macro's Metal4 straps |

---

## 5. Adding another analog cell (the INV_GF steps)

1. **Have a DRC-clean GDS and its SPICE netlist.**
   `INV_GF`: `analog_layout/misc/build/gds/INV_GF.gds` (`make gf-inverter`)
   and `analog_layout/misc/INV_GF.spice`.
2. **Find its ports.** Run `probe_pins.py` on the GDS: each label's
   layer, position, and the metal under it. `INV_GF`: all on Metal1;
   origin at the cell centre; `Y` is 0.23 µm wide.
3. **Describe the wrapper** in `macros.py` `MACROS`: size (90 µm tall),
   where the cell sits, each signal's landing layer and via rectangles,
   and each supply's via/pad rectangles and strap position.
4. **Build and sign off the wrapper alone:** add it to `MACROS=` in
   `build.sh` and to `check-top.awk`, then `make top-placement STAGE=macros`.
   It must pass DRC, LVS against the cell's netlist, and the PR-boundary check.
5. **Instantiate it** in `src/chip_core.sv` (with the `USE_POWER_PINS`
   block), connect its pins, and give any pad output a slot in `bidir_out`.
6. **Place and power it** in `librelane/macros.yaml`: a `MACROS` entry
   pointing at `work/macros/<name>/`, an instance location, and a
   `PDN_MACRO_CONNECTIONS` line.
7. **Run the chip:** `make top-placement` (or `./scripts/sim.sh top-placement`)
   and read `runs/top-placement/latest/metrics.json`.

If a pin goes to an **analog pad** rather than to core logic, the
wrapper must bring it to the macro's **north** edge (the pads are on the
north side), and `analog_routes.tcl` draws the wire. Nothing else needs
changing.

---

## 6. What the run checks

| Stage | Check | Tool |
| --- | --- | --- |
| macros | each wrapper DRC-clean | KLayout `gf180mcu.drc` |
| macros | each wrapper matches its cell's netlist (`CMP` reported only: the cell itself is LVS-open) | KLayout LVS |
| macros | PR boundary readable | Magic + LibreLane `get_bbox.tcl` |
| chip | routing DRC, disconnected pins | OpenROAD |
| chip | setup/hold, every corner | OpenSTA |
| chip | full-die DRC | KLayout `gf180mcu.drc` |
| chip | LVS, macros as black boxes | Magic extraction + Netgen |
| chip | stream-out XOR, antenna, density after fill | KLayout |

When something fails, the `reports` in `metrics.json` carry LibreLane's
error, the failed step's tagged tool messages, and per-rule DRC/XOR
locations or per-net LVS differences. You don't need to open a log.

## 7. Traps met on the way (each cost a run)

| Symptom | Cause | Fix, and where it is caught now |
| --- | --- | --- |
| `Magic.StreamOut`: "Failed to extract PR boundary" | macro GDS without layer 0/0 | wrapper draws it; `STAGE=macros` checks it |
| LVS: 5 extra layout nets, analog macro pins floating | `PadRing` marks analog pad nets special; the router skips them | wires drawn (`analog_routes.tcl`) |
| detailed routing aborts (`frAccessPoint` index) inside the flow only | not found; the step passes when re-run on its own | nets stay special, wires drawn |
| PDN step fails "can't read ::ar_dbu" | LibreLane sources the PDN script inside a proc: no globals | helpers compute what they need |
| KLayout DRC `V2.1`/`V2.2a` + XOR on Via2 | two jog vias 0.4 µm apart | straight drop when the pin is under a pad finger |
| metrics missing from the record | LibreLane writes `metrics.csv` with CRLF | `\r` stripped in `build.sh` |

## 8. Not covered by this chip

- **Libraries:** `gf180mcu_fd_io` and `gf180mcu_fd_sc_mcu7t5v0` (what
  `/foss/pdks` ships), not the frozen `ocd_io` + `as_sc_mcu7t3v3`. So
  there's one supply domain and no separate `AVDD` (ADR 0009).
- **Comparator:** `CMP` is placed with real pins and power, but its
  internal nets are unrouted (ADR 0006), so it doesn't work in silicon.
- **Chip-level checks not run:** no CDM protection on the analog inputs,
  no PEX, no provider precheck.
