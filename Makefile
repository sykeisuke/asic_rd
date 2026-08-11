.PHONY: check nmos-dc sampling-cell four-cell four-cell-mux four-cell-wilkinson comparator comparator-range comparator-offset ramp-generator wilkinson-slice transfer counter controller cosim four-cell-cosim vnc stop

check:
	./scripts/eda-check.sh

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

controller:
	./scripts/run-controller.sh

cosim:
	./scripts/run-cosim.sh

four-cell-cosim:
	./scripts/run-four-cell-cosim.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh
