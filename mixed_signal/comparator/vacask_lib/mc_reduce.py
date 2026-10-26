"""Reduce one VACASK Monte Carlo run (tb_mc.sim.tmpl) to one CSV row.

    python3 vacask_lib/mc_reduce.py work <filetag> <celltag> <corner> <temp> <vdd> <vcm> <samples> >> work/mc_sweep.csv

Reads work/nom_<filetag>.raw (the mismatch-free sweep) and
work/mc_<filetag>.<i>.dc.raw for i = 1..samples; <filetag> is the cell tag
plus the level with dots replaced by p, <celltag> is corner_temp_vdd. In each, inn is swept through
the common mode with inp fixed; the trip point is where dout crosses VDD/2,
found by linear interpolation of the first sign change. trip - VCM is the
input-referred offset of that sample. Prints:

    tag,corner,temp,vdd,common_mode_v,samples,found,vos_nom_v,vos_mean_v,
    vos_sigma_v,vos_min_v,vos_max_v

`found` is how many samples produced a crossing inside the +-40 mV window;
a sample outside it is a finding, not a dropped point, and lowers `found`.
Also writes work/mc_<tag>_offsets.csv (one offset per line) for the
histogram.
"""
import os
import sys

import numpy as np
from rawfile import rawread


def trip(plot, vdd, vcm):
    vin = np.real(np.asarray(plot["inn"]))
    vout = np.real(np.asarray(plot["dout"])) - vdd / 2.0
    idx = np.where(np.diff(np.sign(vout)) != 0)[0]
    if idx.size == 0:
        return float("nan")
    i = idx[0]
    x0, x1, y0, y1 = vin[i], vin[i + 1], vout[i], vout[i + 1]
    return float(x0 + (0.0 - y0) * (x1 - x0) / (y1 - y0) - vcm)


def main():
    wd, ftag, tag, corner, temp, vdd, vcm, samples = sys.argv[1:9]
    vddf, vcmf, n = float(vdd), float(vcm), int(samples)
    nom = trip(rawread(os.path.join(wd, f"nom_{ftag}.raw")).get(), vddf, vcmf)
    offs = []
    for i in range(1, n + 1):
        p = os.path.join(wd, f"mc_{ftag}.{i}.dc.raw")
        if not os.path.exists(p):
            continue
        v = trip(rawread(p).get(), vddf, vcmf)
        if np.isfinite(v):
            offs.append(v)
    offs = np.array(offs)
    with open(os.path.join(wd, f"mc_{ftag}_offsets.csv"), "w") as f:
        f.write("vos_v\n")
        for v in offs:
            f.write(f"{v:.7e}\n")
    if offs.size < 2:
        print(f"{tag},{corner},{temp},{vdd},{vcm},{n},{offs.size},{nom:.6e},nan,nan,nan,nan")
        return 0
    print(f"{tag},{corner},{temp},{vdd},{vcm},{n},{offs.size},{nom:.6e},{offs.mean():.6e},"
          f"{offs.std(ddof=1):.6e},{offs.min():.6e},{offs.max():.6e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
