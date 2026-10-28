.PHONY: check tools pdk analog-regression course-regression nmos-dc nmos-width sampling-cell four-cell four-cell-mux four-cell-wilkinson comparator comparator-range comparator-offset ramp-generator wilkinson-slice transfer counter gray-counter controller parallel-controller digital-top digital-physical cosim four-cell-cosim phase-sweep layout drc lvs gf-inverter top-placement comparator-pvt comparator-schematic latch midrail-ref bias-gen vrlo-ref ramp-gen analog-top cell-trannoise chip-floorplan vnc stop

check:
	./scripts/eda-check.sh

tools:
	./scripts/eda-tools.sh

pdk:
	./scripts/eda-pdk.sh

analog-regression: nmos-dc nmos-width sampling-cell four-cell four-cell-mux ramp-generator comparator comparator-range comparator-offset wilkinson-slice transfer four-cell-wilkinson

course-regression: analog-regression counter gray-counter controller parallel-controller digital-top cosim four-cell-cosim phase-sweep

nmos-dc:
	./scripts/run-nmos-dc.sh

nmos-width:
	./scripts/run-nmos-width.sh

sampling-cell:
	./scripts/run-sampling-cell.sh

four-cell:
	./scripts/run-four-cell.sh

four-cell-mux:
	./scripts/run-four-cell-mux.sh

four-cell-wilkinson:
	./scripts/run-four-cell-wilkinson.sh

comparator:
	./scripts/run-comparator.sh

comparator-range:
	./scripts/run-comparator-range.sh

comparator-offset:
	./scripts/run-comparator-offset.sh

ramp-generator:
	./scripts/run-ramp-generator.sh

wilkinson-slice:
	./scripts/run-wilkinson-slice.sh

transfer:
	./scripts/run-transfer.sh

counter:
	./scripts/run-counter.sh

gray-counter:
	./scripts/run-gray-counter.sh

parallel-controller:
	./scripts/run-parallel-controller.sh

controller:
	./scripts/run-controller.sh

digital-top:
	./scripts/run-digital-top.sh

digital-physical:
	./scripts/run-digital-physical.sh

layout:
	./scripts/run-layout.sh $(CELL)

drc:
	./scripts/run-drc.sh $(CELL)

lvs:
	./scripts/run-lvs.sh $(CELL) $(SPICE)

gf-inverter:
	./scripts/run-gf-inverter.sh

top-placement:
	./scripts/run-top-placement.sh $(STAGE)

cosim:
	./scripts/run-cosim.sh

four-cell-cosim:
	./scripts/run-four-cell-cosim.sh

phase-sweep:
	./scripts/run-four-cell-phase-sweep.sh

# ---- 8-bit analog blocks, one folder each under mixed_signal/ (spec 0.7:
# ---- true bottom-plate cells, one 20 MHz clock, 20 MSa/s). `comparator`
# ---- above runs mixed_signal/comparator. Blocks that use the frozen 3.3 V
# ---- libraries (latch, analog-top, cell-trannoise, chip-floorplan) need
# ---- `make pdk` first (scripts/eda-common.sh, PDK_LIBS_ROOT).

# Comparator over PVT / Monte Carlo / VACASK noise; its xschem views.
comparator-pvt:
	./scripts/run-comparator-pvt.sh

comparator-schematic:
	./scripts/run-comparator-schematic.sh

# Clocked latch `latch`: one gf180mcu_as_sc_mcu7t3v3 dfxtn_2 negative-edge flop.
latch:
	./scripts/run-latch.sh

# VDD/2 reference `midref`, one buffer for VREF and VBL.
midrail-ref:
	./scripts/run-midrail-ref.sh

# Bias generator `bias_gen`, current outputs.
bias-gen:
	./scripts/run-bias-gen.sh

# VR_LO (0.5 V) shunt regulator for the ramp's reset.
vrlo-ref:
	./scripts/run-vrlo-ref.sh

# Ramp generators ramp_gen / ramp_simple.
ramp-gen:
	./scripts/run-ramp-gen.sh

# The analog macro `analog_top` (mixed_signal/Analog_top): four cells, ramp,
# bias, VDD/2 and VR_LO references.
analog-top:
	./scripts/run-analog-top.sh

# One Analog_top cell, VACASK transient noise (slow: hours; STEPS=reduce
# re-judges the cached runs).
cell-trannoise:
	./scripts/run-cell-trannoise.sh

# Chip floorplan: the Analog_top macro + digital top in the 1x0p5 ring.
chip-floorplan:
	./scripts/run-chip-floorplan.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh
