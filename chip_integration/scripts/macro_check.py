#!/usr/bin/env python3
"""Checks on the analog macro before it goes into the chip (step 3).

    python3 scripts/macro_check.py

1. KLayout DRC with the PDK's own deck (gf180mcu.drc, variant gf180mcuD),
   every rule except density: the verdict, `wsa_analog_top_drc_violations`.
2. The density rules alone, reported and not judged: they are "over the
   entire die" and no single cell meets them; the chip's fill does.
3. LibreLane's own Magic get_bbox.tcl on the GDS: the four PR-boundary
   fields Magic.StreamOut needs (`wsa_analog_top_magic_bbox_fields = 4`).

Reports go to work/macro_check/; only counts are printed.
"""

import os
import subprocess
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "wsa_analog_top"
GDS = os.path.join(HERE, "work", "macros", NAME, "gds", NAME + ".gds")
WORK = os.path.join(HERE, "work", "macro_check")
DECK = "/foss/pdks/gf180mcuD/libs.tech/klayout/tech/drc/gf180mcu.drc"
MAGICRC = "/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc"


def drc(decks, tag):
    rep = os.path.join(WORK, f"{NAME}-{tag}.lyrdb")
    r = subprocess.run(["klayout", "-b", "-r", DECK, "-rd", "input=" + GDS,
                        "-rd", "report=" + rep, "-rd", "variant=gf180mcuD",
                        "-rd", "topcell=" + NAME, "-rd", "run_mode=deep",
                        "-rd", "decks=" + decks],
                       cwd=WORK, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    with open(os.path.join(WORK, f"{NAME}-{tag}.log"), "w") as f:
        f.write(r.stdout)
    if "DRC RESULT" not in r.stdout:
        raise SystemExit(f"FAIL: KLayout DRC ({tag}) did not finish")
    by = {}
    for it in ET.parse(rep).getroot().iter("item"):
        c = (it.findtext("category") or "?").strip("'")
        by[c] = by.get(c, 0) + 1
    return by


def bbox():
    import librelane
    tcl = os.path.join(os.path.dirname(librelane.__file__), "scripts", "magic",
                       "get_bbox.tcl")
    env = dict(os.environ, _GDS_IN=GDS, _MACRO_NAME_IN=NAME)
    r = subprocess.run(["magic", "-dnull", "-noconsole", "-rcfile", MAGICRC, tcl],
                       env=env, stdin=subprocess.DEVNULL, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return [ln for ln in r.stdout.splitlines()
            if ln.startswith("%OL_METRIC_I ") and ln.split()[1] in
            ("llx", "lly", "urx", "ury")]


def main():
    os.makedirs(WORK, exist_ok=True)
    geom = drc("all,-density", "drc")
    for c, n in sorted(geom.items()):
        print(f"REPORT: {NAME} DRC {c}: {n}")
    print(f"{NAME}_drc_violations = {sum(geom.values())}")
    dens = drc("density", "density")
    print(f"{NAME}_density_violations = {sum(dens.values())}")
    if dens:
        print(f"REPORT: {NAME} density rules (die-level, the chip fill resolves): "
              + ", ".join(sorted(dens)))
    lines = bbox()
    for ln in lines:
        print("REPORT: magic bbox " + ln.split(None, 1)[1])
    print(f"{NAME}_magic_bbox_fields = {len(lines)}")


if __name__ == "__main__":
    main()
