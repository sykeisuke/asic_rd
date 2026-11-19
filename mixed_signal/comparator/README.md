# comparator: the Wilkinson cell's comparator

The comparator of the 8-bit true bottom-plate cell: a PMOS-input 5T OTA, a
current-starved inverter and two inverters, 12 devices, every L <= 0.36 um.
It senses the floating plate on **inp** against VREF = VDD/2 on **inn**; dout
**falls once** at the decision, which is the latch / Gray capture convention
of spec s.5.3. Analog_top uses its macro form `comparator_d`.

## Folder layout

| Part | Files |
| --- | --- |
| cell `comparator` | `comparator.spice` (`.subckt comparator inp inn dout clk vdd vss nbias pbias`), `comparator.sch` / `.sym` |
| macro form `comparator_d` | `comparator_d.spice` (`.subckt comparator_d inp inn ibias dout vdd vss`: the cell + its bias diode XREFP) |
| sized core `comparator_core` | `comparator_core.spice`: the 10 devices (OTA, starved inverter, inverter), written by `size.py` |
| core sizing | `size.py` (gm/Id search over the block's own short-L tables, `lut/`), `size_p5t.py`, `tb_sel.spice`, `tb_sel_dc.spice`, `data/sizing.json`, `DESIGN_RECIPE.md` |
| cell from the core | `derive.py`: the core's 10 devices line for line (its output node renamed `outc`) + XBUF5 / XBUF6, copies of XBUF3 / XBUF4 |

Two steps make the netlist: `size.py` sizes the core (the search is recorded;
`PHASES='size'` re-selects it and checks the file), `derive.py` adds the
inverter. Neither output is hand-edited.

Why the plate is on inp: there the plate drives XINP, whose drain is the
mirror's diode node, and no longer sees the Miller capacitance of the gain
node (alpha at the trip 0.38 -> 0.84); the cell's transient noise drops
(x0.74 / x0.83, `../cell_trannoise_swap/COMPARISON.md`). The added inverter
keeps dout falling.

History: until 2026-11-18 this folder held the 10-device comparator (cell
`cmp`, plate on inn); that folder, its benches, REPORT and layout PEX are
frozen in `../comparator_bkp/comparator_10dev/`. The plate-on-inp version
was developed as `comparator_sw/` (now `../comparator_bkp/comparator_sw/`).

## Run it

```sh
./scripts/sim.sh comparator                          # derive check, typical gates, offset_lin, bias requirement (~1 h)
./scripts/sim.sh comparator PHASES='derive verify'   # netlist check + typical gates only (minutes)
./scripts/sim.sh comparator PHASES='lut size'        # rebuild the gm/Id tables, re-select the core from the record
./scripts/sim.sh comparator-schematic                # xschem views: generate, netlist back, testbenches, renders
./scripts/sim.sh comparator-pvt                      # 45 PVT cells, MC, offset_lin, VACASK MC + noise (hours, detached)
./container.sh 'python3 derive.py'                   # regenerate the cell netlists after a change of the core
```

## What is measured

Three variants through the same benches (ideal bias, 10 fF on dout, ADR 0025
grid):

| variant | netlist | hookup | dout at the decision |
| --- | --- | --- | --- |
| `sw` | `comparator.spice` (`comparator`) | plate on inp | falls (the gated cell) |
| `base` | `comparator_core.spice` (`comparator_core`) | plate on inn (the macro before 2026-11-17) | falls |
| `sw_noinv` | `comparator_core` | plate on inp | rises (no inverter) |

Gates (ADR 0015 plus polarity) and what is only reported:
`check-comparator.awk`.

## Files

| File | What it is |
| --- | --- |
| `bench.py` | phases `verify`, `lin`, `bias`; writes `data/values_<phase>.txt`, `data/offset_lin.csv`, `data/bias_req.csv` |
| `pvt.py` | PVT, MC and offset_lin over corners (`run-pvt.sh`) |
| `tb_tran.spice` / `tb_dc.spice` / `tb_nz.spice` / `tb_mc.spice` | charge path (54.52 fF MIM, ramp at the ADR 0025 slope), static trip, noise, Monte Carlo |
| `check-comparator.awk` | the gates: one PASS / FAIL line each |
| `stage_vacask.py`, `vacask.sh`, `trannoise.py`, `vacask_lib/` | VACASK MC and transient noise, staged in `work/va` |
| `comparator_sch.py`, `tb_sch.py` | generate `comparator.sch` / `.sym` and the four `tb_*.sch` |
| `intent.py`, `intent_core.py`, `intent_op.py` | the currents on the drawings (core allocation + output inverters) and their check |
| `xtb.py`, `check-schematic.awk` | drawn testbenches against their decks; the drawing against `comparator.spice` |
| `run.sh`, `run-pvt.sh`, `schematic.sh`, `container.sh` | the flows (`make comparator`, `comparator-pvt`, `comparator-schematic`) |
