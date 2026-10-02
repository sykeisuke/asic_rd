#!/usr/bin/env python3
"""The chip's KLayout DRC and XOR results as REPORT lines.

    python3 drc_summary.py librelane/runs/chip_top

Per report database (the KLayout DRC deck's, the Magic/KLayout XOR's):
violations per rule/layer, and the first few locations of each, in um,
so a violation can be tied to what drew it. No log is read.
"""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

PER_RULE = 4


def items(path):
    root = ET.parse(path).getroot()
    for it in root.iter("item"):
        cat = (it.findtext("category") or "?").strip("'")
        vals = " ".join(v.text or "" for v in it.iter("value"))
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", vals)]
        loc = ""
        if len(nums) >= 2:
            xs, ys = nums[0::2], nums[1::2]
            loc = f"({min(xs):.2f},{min(ys):.2f})-({max(xs):.2f},{max(ys):.2f})"
        yield cat, loc


def main(run):
    reps = sorted(glob.glob(os.path.join(run, "*-klayout-drc", "reports", "*.xml")) +
                  glob.glob(os.path.join(run, "*-klayout-drc", "reports", "*.lyrdb")) +
                  glob.glob(os.path.join(run, "*-klayout-xor", "*.xml")))
    for rep in reps:
        tag = os.path.basename(os.path.dirname(rep)) if "reports" in rep \
            else os.path.basename(os.path.dirname(rep))
        by = {}
        for cat, loc in items(rep):
            by.setdefault(cat, []).append(loc)
        for cat, locs in sorted(by.items()):
            print(f"REPORT: {tag} {cat}: {len(locs)} at "
                  f"{'; '.join(locs[:PER_RULE])}")


if __name__ == "__main__":
    main(sys.argv[1])
