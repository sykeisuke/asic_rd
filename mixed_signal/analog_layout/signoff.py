#!/usr/bin/env python3
"""KLayout signoff for one analog cell's GDS.

    make drc                     # every cell that has a GDS
    make drc CELL=CMP
    make lvs CELL=CMP
    make lvs CELL=CMP SPICE=../../simulations/gf180_comparator/cmp.spice

Both read `physical/final_views/gds/<CELL>.gds`, which `make layout`
writes.  The decks are the PDK's own, unmodified:

    DRC  /foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc
    LVS  /foss/pdks/gf180mcuD/libs.tech/klayout/tech/lvs/run_lvs.py

DENSITY IS RUN SEPARATELY AND NOT JUDGED.  M1.4 through MT.3 and PL.8
read "coverage over the entire die shall be >30%", which an 8 x 5 um
cell cannot satisfy and which fill satisfies at chip level.  Counting
them as cell violations would make every clean cell look broken, and
hiding them would lose the number, so the deck is run twice: once
without the density deck for the verdict, once with it for the record.

THE LVS NETLIST NEEDS CONVERTING.  KLayout's SPICE reader treats a
leading `X` as a subcircuit instance, not a MOS, so an ngspice netlist
written for gf180mcuD compares against nothing.  The PDK ships the
converter this flow uses.
"""

import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
FINAL = os.path.join(BLOCK, "physical", "final_views")
TECHLIB = "gf180mcuD"
KL = f"/foss/pdks/{TECHLIB}/libs.tech/klayout/tech"
DRC_DECK = f"{KL}/drc/gf180mcu.drc"
LVS_RUNNER = f"{KL}/lvs/run_lvs.py"
SPICE_CONVERT = f"{KL}/lvs/gf180_xschem_klayout_spice_convert.py"

#- gf180mcuD is 5LM, 11K metal top, MIM option B. The DRC deck knows it
#- by name; run_lvs.py takes the same stack as variant D.
DRC_VARIANT = "gf180mcuD"
LVS_VARIANT = "D"


def run(cmd, cwd, log):
    r = subprocess.run(cmd, cwd=cwd, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with open(log, "w") as fo:
        fo.write(r.stdout)
    return r


def gds_of(cell):
    p = os.path.join(FINAL, "gds", cell + ".gds")
    if not os.path.exists(p):
        raise SystemExit(f"no GDS for {cell}. Run: make layout CELL={cell}")
    return p


def count(report):
    """Violations per rule, from the KLayout report database."""
    if not os.path.exists(report):
        return {}
    out = {}
    for item in ET.parse(report).getroot().iter("item"):
        name = (item.findtext("category") or "?").strip("'")
        out[name] = out.get(name, 0) + 1
    return out


def drc(cell, decks, tag, gds=None):
    """`gds` overrides the final_views path, for cells that are build
    output rather than deliverables -- a geometry sweep, say, whose
    candidates must meet the same deck without joining the cell list
    that `make drc` and `make lvs` walk."""
    report = os.path.join(WORK, f"{cell}-{tag}.lyrdb")
    r = run(["klayout", "-b", "-r", DRC_DECK,
             "-rd", "input=" + (gds or gds_of(cell)),
             "-rd", "report=" + report,
             "-rd", "variant=" + DRC_VARIANT,
             "-rd", "topcell=" + cell,
             "-rd", "run_mode=deep",
             "-rd", "decks=" + decks],
            WORK, os.path.join(WORK, f"{cell}-{tag}.log"))
    if "DRC RESULT" not in r.stdout:
        raise SystemExit(f"KLayout DRC did not finish for {cell}; "
                         f"see work/{cell}-{tag}.log")
    return count(report), report


def lvs(cell, netlist, gds=None):
    """Extract the GDS and compare it with `netlist`.

    `gds` overrides the final_views path, the same way `drc` does, for
    cells that are build output rather than deliverables."""
    converted = os.path.join(WORK, f"{cell}-klayout.spice")
    r = run(["python3", SPICE_CONVERT, netlist, "-o", converted], WORK,
            os.path.join(WORK, f"{cell}-spice-convert.log"))
    if not os.path.exists(converted):
        raise SystemExit(f"could not convert {netlist} for KLayout: "
                         f"{r.stdout[-1000:]}")
    rundir = os.path.join(WORK, f"{cell}-lvs")
    shutil.rmtree(rundir, ignore_errors=True)
    #- --combine is not optional here. The layout draws nf fingers as nf
    #- separate transistors and the netlist names one device with nf;
    #- without device combination they are different circuits and LVS
    #- says so (measured on INV, which matches with it).
    r = run(["python3", LVS_RUNNER,
             "--layout=" + (gds or gds_of(cell)),
             "--netlist=" + converted,
             "--variant=" + LVS_VARIANT,
             "--topcell=" + cell,
             "--run_mode=deep", "--combine",
             "--run_dir=" + rundir],
            WORK, os.path.join(WORK, f"{cell}-lvs.log"))
    if "Congratulations! Netlists match" in r.stdout:
        return "match", netlist
    if "Netlists don't match" in r.stdout:
        return "mismatch", netlist
    return "error", netlist


def main(argv):
    if len(argv) < 2:
        raise SystemExit("usage: signoff.py drc|lvs CELL [NETLIST] "
                         "[--gds PATH]")
    #- --gds names a layout outside physical/final_views: a geometry
    #- sweep candidate, or a deliberately broken control cell, neither of
    #- which belongs in the list `make drc` and `make lvs` walk.
    gds = None
    if "--gds" in argv:
        i = argv.index("--gds")
        #- both tools run with cwd=WORK, so a path relative to the block
        #- would resolve one directory too deep
        gds = os.path.abspath(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    what, cell = argv[0], argv[1]
    os.makedirs(WORK, exist_ok=True)
    low = cell.lower()

    if what == "drc":
        geom, report = drc(cell, "all,-density", "drc", gds=gds)
        dens, _ = drc(cell, "density", "density", gds=gds)
        print(f"{low}_drc_violations = {sum(geom.values())}")
        print(f"{low}_drc_rules = "
              f"{','.join(f'{k}:{v}' for k, v in sorted(geom.items())) or 'none'}")
        print(f"{low}_density_violations = {sum(dens.values())}")
        print(f"{low}_density_rules = "
              f"{','.join(sorted(dens)) or 'none'}")
        print(f"{low}_drc_report = 1")
        return

    if what == "lvs":
        netlist = os.path.abspath(argv[2]) if len(argv) > 2 else os.path.join(
            BLOCK, "spice", cell + ".spice")
        if not os.path.exists(netlist):
            raise SystemExit(f"no netlist {netlist}")
        verdict, used = lvs(cell, netlist, gds=gds)
        print(f"{low}_lvs = {verdict}")
        print(f"{low}_lvs_match = {1 if verdict == 'match' else 0}")
        #- which netlist the verdict is about. An LVS result is only
        #- meaningful with the netlist named beside it.
        print(f"{low}_lvs_netlist = {os.path.relpath(used, BLOCK)}")
        return

    raise SystemExit(f"unknown step {what}")


if __name__ == "__main__":
    main(sys.argv[1:])
