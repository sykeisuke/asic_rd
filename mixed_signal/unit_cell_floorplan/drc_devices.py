#!/usr/bin/env python3
"""DRC each transistor primitive of every cell on its own.

    ./container.sh 'python3 drc_devices.py'

Every device the floorplans place is written as a standalone GDS and run
through the PDK deck, so a violation is attributed to a primitive rather
than to a 600 um2 cell.  This is what the analog_layout flow does for its
cicpy primitives (`make cicpy-layout`); here it is the same idea for the
gdsfactory generator plus the gate bars floorplan.py draws on it.
"""
import os
import xml.etree.ElementTree as ET

import floorplan as FP

os.makedirs(os.path.join(FP.WORK, "devices"), exist_ok=True)
seen = {}
for name, (kind, sz, tag) in FP.CELLS.items():
    CMP, sizing, sw = FP.comparator_for(tag)
    wn, wp = (sw["drawn"]["wn_um"], sw["drawn"]["wp_um"]) if sw else (0.22, 0.44)
    devs = dict(CMP)
    devs["TGN"] = ("nfet", FP.L_SW_UM, wn, 1)
    devs["TGP"] = ("pfet", FP.L_SW_UM, wp, 1)
    kin, lin, win, nfin = CMP["XINP"]
    kld, lld, wld, nfld = CMP["XLOADD"]
    devs["PAIR"] = (kin, lin, 2 * win, 2 * nfin, FP.interdigitate(nfin))
    devs["LOADS"] = (kld, lld, 2 * wld, 2 * nfld, "D" + "A" * (2 * nfld) + "D")
    for dn, spec in devs.items():
        if dn in ("XINP", "XINN", "XLOADD", "XLOADM"):
            continue
        key = tuple(spec)
        if key in seen:
            continue
        comp = FP.device(*spec)
        gds = os.path.join(FP.WORK, "devices", comp.name + ".gds")
        comp.write_gds(gds)
        geom, report = FP.signoff.drc(comp.name, "all,-density", "dev", gds=gds)
        seen[key] = sum(geom.values())
        rules = ",".join(f"{k}:{v}" for k, v in sorted(geom.items())) or "none"
        print(f"{comp.name} = {seen[key]}  [{rules}]  from {name}/{dn}")
        if geom and os.path.exists(report):
            for item in list(ET.parse(report).getroot().iter("item"))[:4]:
                cat = (item.findtext("category") or "").strip("'")
                val = [v.text for v in item.iter("value")][0][:90]
                print(f"    {cat}: {val}")
print(f"devices_checked = {len(seen)}")
print(f"devices_failing = {sum(1 for v in seen.values() if v)}")
