"""Reduce one transient-noise run (tn.raw in its directory) to one row per
conversion: each cell's dout falling time after TR and vramp at the count
boundaries k = 4, 64, 128, 192, 255.

    python3 tn_extract.py <run_dir> <nper>       -> <run_dir>/conv.csv
"""
import os
import sys

import numpy as np
from rawfile import rawread

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tn_bench import TS0, P, TCOUNT, VDD, timeline  # noqa: E402

KS = (4, 64, 128, 192, 255)


def main():
    d, nper = sys.argv[1], int(sys.argv[2])
    p = rawread(os.path.join(d, "tn.raw")).get()
    t = np.asarray(p["time"])
    vr = np.asarray(p["vramp"])
    douts = [np.asarray(p["dout%d" % i]) for i in range(4)]
    e = timeline(nper)
    rows = []
    for n in range(nper):
        tr = TS0 + n * P + e["rst_fall"]
        te = TS0 + n * P + e["s1_open"]
        if te > t[-1]:
            break
        row = [n]
        for dv in douts:
            w = np.where((t >= tr) & (t <= te))[0]
            x, y = t[w], dv[w]
            if y[0] < VDD / 2:
                row.append(np.nan)            # not armed at TR
                continue
            j = np.where((y[:-1] >= VDD / 2) & (y[1:] < VDD / 2))[0]
            if not j.size:
                row.append(np.nan)
                continue
            j = j[0]
            tc = x[j] + (y[j] - VDD / 2) / (y[j] - y[j + 1]) * (x[j + 1] - x[j])
            row.append(tc - tr)
        for k in KS:
            row.append(np.interp(tr + k * TCOUNT, t, vr))
        rows.append(row)
    hdr = "n," + ",".join("t%d" % i for i in range(4)) + "," + ",".join("v%d" % k for k in KS)
    np.savetxt(os.path.join(d, "conv.csv"), np.array(rows), delimiter=",", header=hdr, comments="", fmt="%.12g")
    print("tn_extract_conversions = %d" % len(rows))


if __name__ == "__main__":
    main()
