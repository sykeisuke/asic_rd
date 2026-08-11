.PHONY: check nmos-dc sampling-cell comparator ramp-generator wilkinson-slice counter vnc stop

check:
	./scripts/eda-check.sh

nmos-dc:
	./scripts/run-nmos-dc.sh

sampling-cell:
	./scripts/run-sampling-cell.sh

comparator:
	./scripts/run-comparator.sh

ramp-generator:
	./scripts/run-ramp-generator.sh

wilkinson-slice:
	./scripts/run-wilkinson-slice.sh

counter:
	./scripts/run-counter.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh
