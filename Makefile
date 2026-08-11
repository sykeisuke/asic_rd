.PHONY: check nmos-dc sampling-cell vnc stop

check:
	./scripts/eda-check.sh

nmos-dc:
	./scripts/run-nmos-dc.sh

sampling-cell:
	./scripts/run-sampling-cell.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh
