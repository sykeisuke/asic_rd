#!/usr/bin/env python3
"""The chip LVS result as REPORT lines, from Netgen's JSON report.

    python3 lvs_summary.py librelane/runs/chip_top

For every circuit Netgen compared: the pair of names, and whether its
nets, devices and pins matched; for the ones that did not, the first
few unmatched nets and pins, with the side (layout/schematic) each is
missing from. No log is read; lvs.netgen.json is Netgen's structured
report.
"""

import glob
import json
import os
import sys

LIMIT = 12


def names(entries):
    """Netgen lists unmatched items as [[layout...], [schematic...]]
    groups; flatten to 'name' strings, keeping which side they came
    from."""
    out = []
    for group in entries or []:
        if not isinstance(group, list) or len(group) != 2:
            continue
        for side, items in zip(("layout", "schematic"), group):
            for it in items or []:
                if isinstance(it, list) and it:
                    it = it[0]
                if isinstance(it, dict):
                    it = it.get("name", str(it))
                out.append(f"{side}:{it}")
    return out


def main(run):
    rep = sorted(glob.glob(os.path.join(run, "*-netgen-lvs", "reports",
                                        "lvs.netgen.json")))
    if not rep:
        print("REPORT: lvs: no lvs.netgen.json in the run")
        return
    data = json.load(open(rep[-1]))
    bad = 0
    for c in data if isinstance(data, list) else [data]:
        if not isinstance(c, dict):
            continue
        pair = "/".join(str(n) for n in c.get("name", ["?"]))
        issues = []
        for key in ("badnets", "badelements"):
            if c.get(key):
                issues.append(f"{key}={len(c[key])}")
        pins = c.get("pins")
        pin_bad = []
        if isinstance(pins, list) and len(pins) == 2:
            lay, sch = pins
            for a, b in zip(lay, sch):
                if a != b:
                    pin_bad.append(f"{a}<->{b}")
        if pin_bad:
            issues.append(f"pin_mismatch={len(pin_bad)}")
        for k in ("devices", "nets"):
            v = c.get(k)
            if isinstance(v, list) and len(v) == 2 and v[0] != v[1]:
                issues.append(f"{k}={v[0]}/{v[1]}")
        if not issues:
            continue
        bad += 1
        print(f"REPORT: lvs {pair}: {' '.join(issues)}")
        if c.get("badnets"):
            print(f"REPORT: lvs {pair} unmatched nets: "
                  f"{', '.join(names(c['badnets'])[:LIMIT])}")
        if c.get("badelements"):
            print(f"REPORT: lvs {pair} unmatched devices: "
                  f"{', '.join(names(c['badelements'])[:LIMIT])}")
        if pin_bad:
            print(f"REPORT: lvs {pair} pins: {', '.join(pin_bad[:LIMIT])}")
    print(f"lvs_circuits_mismatched = {bad}")


if __name__ == "__main__":
    main(sys.argv[1])
