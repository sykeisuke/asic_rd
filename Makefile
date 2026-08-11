.PHONY: check nmos-dc sampling-cell comparator comparator-range ramp-generator wilkinson-slice transfer counter cosim vnc stop

check:
	./scripts/eda-check.sh

nmos-dc:
	./scripts/run-nmos-dc.sh

sampling-cell:
	./scripts/run-sampling-cell.sh

comparator:
	./scripts/run-comparator.sh

comparator-range:
	./scripts/run-comparator-range.sh

ramp-generator:
	./scripts/run-ramp-generator.sh

wilkinson-slice:
	./scripts/run-wilkinson-slice.sh

transfer:
	./scripts/run-transfer.sh

counter:
	./scripts/run-counter.sh

cosim:
	./scripts/run-cosim.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh
