.PHONY: check analog-regression course-regression nmos-dc sampling-cell four-cell four-cell-mux four-cell-wilkinson comparator comparator-range comparator-offset ramp-generator wilkinson-slice transfer counter gray-counter controller digital-top digital-physical cosim four-cell-cosim phase-sweep vnc stop

check:
	./scripts/eda-check.sh

analog-regression: nmos-dc sampling-cell four-cell four-cell-mux ramp-generator comparator comparator-range comparator-offset wilkinson-slice transfer four-cell-wilkinson

course-regression: analog-regression counter gray-counter controller digital-top cosim four-cell-cosim phase-sweep

nmos-dc:
	./scripts/run-nmos-dc.sh

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

controller:
	./scripts/run-controller.sh

digital-top:
	./scripts/run-digital-top.sh

digital-physical:
	./scripts/run-digital-physical.sh

cosim:
	./scripts/run-cosim.sh

four-cell-cosim:
	./scripts/run-four-cell-cosim.sh

phase-sweep:
	./scripts/run-four-cell-phase-sweep.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh
