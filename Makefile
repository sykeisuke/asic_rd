.PHONY: check nmos-dc vnc stop

check:
	./scripts/eda-check.sh

nmos-dc:
	./scripts/run-nmos-dc.sh

vnc:
	./scripts/eda-vnc.sh

stop:
	./scripts/eda-stop.sh

