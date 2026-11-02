#!/usr/bin/env python3
"""Summarise a LEF macro: size, every pin (direction, use, layer, the
bounding box of its shapes per layer, shape count) and the obstruction
bbox per layer. A LEF is megabytes of rectangles; this is the part the
chip integration needs.

    python3 lef_probe.py <file.lef> [MACRO ...]
"""
import re
import sys


def main(path, want):
    macro = pin = None
    in_obs = False
    layer = None
    out = {}
    for raw in open(path, errors="replace"):
        t = raw.split()
        if not t:
            continue
        k = t[0]
        if k == "MACRO":
            macro = t[1]
            out[macro] = {"size": None, "pins": {}, "obs": {}, "order": []}
            pin = None
            in_obs = False
        elif macro is None:
            continue
        elif k == "SIZE":
            out[macro]["size"] = (t[1], t[3])
        elif k == "PIN":
            pin = t[1]
            out[macro]["pins"][pin] = {"dir": "", "use": "", "layers": {}}
            out[macro]["order"].append(pin)
        elif k == "DIRECTION" and pin:
            out[macro]["pins"][pin]["dir"] = t[1]
        elif k == "USE" and pin:
            out[macro]["pins"][pin]["use"] = t[1]
        elif k == "OBS":
            in_obs = True
            pin = None
        elif k == "LAYER":
            layer = t[1]
        elif k == "RECT" and (pin or in_obs):
            x0, y0, x1, y1 = (float(v) for v in t[1:5] if v != "MASK")
            tgt = (out[macro]["obs"] if in_obs else out[macro]["pins"][pin]["layers"])
            b = tgt.setdefault(layer, [1e18, 1e18, -1e18, -1e18, 0])
            b[0] = min(b[0], x0); b[1] = min(b[1], y0)
            b[2] = max(b[2], x1); b[3] = max(b[3], y1); b[4] += 1
        elif k == "END" and len(t) > 1:
            if pin and t[1] == pin:
                pin = None
            elif t[1] == macro:
                macro = None
                in_obs = False
        elif k == "END" and in_obs:
            in_obs = False
    for m, d in out.items():
        if want and m not in want:
            continue
        print(f"MACRO {m} size {d['size']}")
        for p in d["order"]:
            pd = d["pins"][p]
            for ly, b in pd["layers"].items():
                print(f"  PIN {p} {pd['dir']} {pd['use']} {ly} "
                      f"{b[0]:.3f},{b[1]:.3f} {b[2]:.3f},{b[3]:.3f} n={b[4]}")
        for ly, b in d["obs"].items():
            print(f"  OBS {ly} {b[0]:.3f},{b[1]:.3f} {b[2]:.3f},{b[3]:.3f} n={b[4]}")


if __name__ == "__main__":
    main(sys.argv[1], set(sys.argv[2:]))
