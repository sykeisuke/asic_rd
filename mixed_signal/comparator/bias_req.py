"""Bias-generator requirement from comparator's delay (ngspice).

    ./container.sh 'python3 -u bias_req.py'          (run-pvt.sh phase `bias`)

The 12.5 ns delay misses at the ss cells with the ideal, constant bias
(DESIGN_RECIPE.md s.9). The user's decision (2026-10-07): a bias generator
will supply this comparator. This turns the miss into that generator's
requirement: at every cell, the smallest current, as a multiple of the
nominal 1.931 uA per finger, at which the delay from the static trip is
<= 12.5 ns at 4.5 and 40.5 LSB. It is run as the controlled deck and with the
S/D geometry the schematic draws (closer to layout). The scale multiplies
the reference current, so tail and starve scale together.

REPORTED (not gated): the required scale per cell, its maximum (the
generator must deliver at least this at the slowest cell), and the delay
and fall at 1.0x for reference. Writes data/bias_req.csv.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import size_v3 as S  # noqa: E402

CORNERS = os.environ.get("BIAS_CORNERS", "typical ss ff sf fs").split()
TEMPS = [float(x) for x in os.environ.get("TEMPS", "0 27 85").split()]
VDDS = [float(x) for x in os.environ.get("VDDS", "3.0 3.3 3.6").split()]
SCALES = [float(x) for x in os.environ.get("BIAS_SCALES", "0.8 0.9 1.0 1.05 1.1 1.15 1.2 1.3 1.4").split()]
LEVELS = (("c4", 4.5), ("plat", 40.5))


def main():
    sel = json.load(open(os.path.join(S.BLOCK, "data", "sizing.json")))
    s = {k: sel[k] for k in S.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    cells = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]
    rows = []
    for geom in ("0", "1"):
        os.environ["DUT_GEOM"] = geom          # read by size_v3.dev when the DUT file is written
        sub = "bias_geom" if geom == "1" else "bias"
        jobs = [("%s_%g_%g_x%g" % (cell + (sc,)), s, lt, k, sc, cell, sub)
                for cell in cells for sc in SCALES for lt, k in LEVELS]
        with ThreadPoolExecutor(max_workers=S.JOBS) as ex:
            res = list(ex.map(S.spice_level, jobs))
        got = {(t, lt): r for t, lt, r in res}
        for cell in cells:
            tag = "%s_%g_%g" % cell
            d = {sc: max(got[("%s_x%g" % (tag, sc), "c4")]["delay_dyn"], got[("%s_x%g" % (tag, sc), "plat")]["delay_dyn"])
                 for sc in SCALES}
            f = {sc: got[("%s_x%g" % (tag, sc), "plat")]["fall"] for sc in SCALES}
            ok = [sc for sc in SCALES if np.isfinite(d[sc]) and d[sc] <= S.DELAY_MAX]
            # the smallest scale from which every larger tested scale also meets the gate
            req = float("nan")
            for sc in sorted(SCALES):
                if all(d[x] <= S.DELAY_MAX for x in SCALES if x >= sc and np.isfinite(d[x])):
                    req = sc
                    break
            rows.append(dict(tag=tag, geom=int(geom), req_scale=req, delay_1x=d.get(1.0, np.nan), fall_1x=f.get(1.0, np.nan),
                             **{"delay_x%g" % sc: d[sc] for sc in SCALES}))
    keys = list(rows[0].keys())
    with open(os.path.join(S.BLOCK, "data", "bias_req.csv"), "w") as h:
        h.write(",".join(keys) + "\n")
        for r in rows:
            h.write(",".join(str(r[k]) if isinstance(r[k], str) else "%.6g" % r[k] for k in keys) + "\n")
    for geom in (0, 1):
        rs = [r for r in rows if r["geom"] == geom]
        req = np.array([r["req_scale"] for r in rs])
        worst = rs[int(np.nanargmax(req))]
        name = "drawn S/D geometry" if geom else "controlled deck"
        print(f"bias_req_max_scale_{'geom' if geom else 'deck'} = {np.nanmax(req):.6g}")
        need = [r for r in rs if r["req_scale"] > 1.0]
        print(f"REPORT: bias requirement ({name}): delay <= 12.5 ns needs at least {np.nanmax(req):g}x the nominal "
              f"{sel['i_f']*1e6:.4g} uA at {worst['tag']}; cells needing more than 1.0x: "
              + (", ".join(f"{r['tag']} {r['req_scale']:g}x" for r in need) if need else "none"))
        lo = [r for r in rs if r["req_scale"] <= min(SCALES)]
        print(f"REPORT: ({name}) {len(lo)}/{len(rs)} cells meet 12.5 ns already at {min(SCALES):g}x")
    print("PASS: bias requirement derived (reported, not gated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
