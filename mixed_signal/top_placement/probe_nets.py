#!/usr/bin/env python3
"""Why a net was or was not routed: the ODB flags OpenROAD's router
filters on, for the named nets; and, with --master, a cell's pin and
obstruction geometry as the router sees it.

    openroad -python probe_nets.py <chip_top.odb> 'analog_PAD[0]' ...
    openroad -python probe_nets.py <chip_top.odb> --master gf180mcu_fd_io__asig_5p0 ASIG5V

Per net: special, signal type, connected-by-abutment, its terms, and
whether it carries routed wire. Per master pin: every shape (layer, box
in um); then the master's obstructions per layer, merged to a bbox.
"""

import sys

from openroad import Design, Tech

tech = Tech()
design = Design(tech)
design.readDb(sys.argv[1])
block = design.getBlock()
db = design.getTech().getDB()
um = block.getDbUnitsPerMicron()


def fmt(b):
    return (f"{b.xMin() / um:.3f},{b.yMin() / um:.3f} "
            f"{b.xMax() / um:.3f},{b.yMax() / um:.3f}")


if sys.argv[2] == "--master":
    m = db.findMaster(sys.argv[3])
    print(f"master {m.getName()} size {m.getWidth() / um:.3f} x "
          f"{m.getHeight() / um:.3f} type {m.getType()}")
    for mt in m.getMTerms():
        if len(sys.argv) > 4 and mt.getName() not in sys.argv[4:]:
            continue
        for mp in mt.getMPins():
            for b in mp.getGeometry():
                print(f"pin {mt.getName()} {b.getTechLayer().getName()} {fmt(b)}")
    obs = {}
    for b in m.getObstructions():
        ln = b.getTechLayer().getName() if b.getTechLayer() else "via"
        x = obs.setdefault(ln, [None, 0])
        x[1] += 1
        x[0] = b if x[0] is None else x[0]
    for ln, (b, n) in obs.items():
        print(f"obs {ln} shapes={n} first={fmt(b)}")
    sys.exit(0)

for name in sys.argv[2:]:
    net = block.findNet(name)
    if net is None:
        print(f"net {name}: not found")
        continue
    terms = [f"{it.getInst().getName()}/{it.getMTerm().getName()}"
             for it in net.getITerms()]
    terms += [f"PIN {bt.getName()}(special={bt.isSpecial()})"
              for bt in net.getBTerms()]
    wire = net.getWire()
    print(f"net {name}: special={net.isSpecial()} "
          f"sigtype={net.getSigType()} "
          f"abutment={net.isConnectedByAbutment()} "
          f"wire={'yes' if wire is not None else 'no'} "
          f"terms={terms}")
    for bt in net.getBTerms():
        for bp in bt.getBPins():
            for b in bp.getBoxes():
                print(f"  bpin {bt.getName()} {b.getTechLayer().getName()} "
                      f"{fmt(b)} status={bp.getPlacementStatus()}")
    for it in net.getITerms():
        inst = it.getInst()
        x, y = inst.getLocation()
        print(f"  iterm {inst.getName()}/{it.getMTerm().getName()} "
              f"inst at {x / um:.3f},{y / um:.3f} orient={inst.getOrient()}")
