#!/usr/bin/env python3
"""Design-space exploration behind the MOM unit capacitor's geometry.

    python3 mom_sweep.py

A MOM capacitor's value comes from extraction, so picking its geometry
means drawing candidates and extracting all of them. This builds the
grid, signs each candidate off against the PDK's own DRC deck and runs
both extraction engines over it, so the unit cell `mom_cap.CELLS["MOMU"]`
freezes is a point on a measured surface rather than an assertion.

Three axes, chosen because each answers a question that changes the cell:

  nf, lf      finger pairs and finger length -- how the value scales, and
              which geometries reach the 15-16 fF window that rule
              MIM.8a's 25 um2 FuseTop floor puts out of MIM's reach
  metal stack M1-M4 against M2-M4: what leaving metal1 out of the cell
              costs in capacitance and saves in substrate coupling, since
              metal1 is both the densest coupling layer and the one
              nearest the substrate. metal5 is the thick 11K top metal in
              this 5LM stack and is checked against MT.1/MT.2a at
              0.44/0.46 um, so it carries no fingers -- see mom_cap.py
  weave       shifting alternate layers by one finger, trading the
              vertical same-net stack for interlayer plate capacitance
"""

import itertools
import os
import sys

import mom_cap
import pex
import signoff

GRID_NF = (4, 5, 6, 7)
GRID_LF = (3.0, 4.0, 5.0)
#- the two stack/weave variants are probed at one geometry each rather
#- than over the whole grid: they answer a yes/no question about the
#- construction, not a scaling question
VARIANTS = ((5, 4.0, (2, 3, 4), False), (5, 4.0, (1, 2, 3, 4), True))


def case(nf, lf, layers, weave):
    tag = "w" if weave else ""
    return (f"MOMS{nf}L{int(lf * 10)}M{layers[0]}{layers[-1]}{tag}",
            nf, lf, layers, weave)


def main(argv):
    cases = [case(nf, lf, (1, 2, 3, 4), False)
             for nf, lf in itertools.product(GRID_NF, GRID_LF)]
    cases += [case(*v) for v in VARIANTS]

    #- Candidates are build output, not deliverables: they stay out of
    #- physical/final_views/gds/ so `make drc` and `make lvs` with no CELL
    #- keep walking only the cells this project actually ships.
    gds_dir = os.path.join(pex.WORK, "mom-sweep")
    os.makedirs(gds_dir, exist_ok=True)
    for name, nf, lf, layers, weave in cases:
        c, w, h = mom_cap.mom_cap(name=name, nf=nf, lf=lf, layers=layers,
                                  weave=weave)
        gds = os.path.join(gds_dir, name + ".gds")
        c.write_gds(gds)

        geom, _ = signoff.drc(name, "all,-density", "drc", gds=gds)
        out_dir = os.path.join(pex.WORK, f"{name}-pex")
        os.makedirs(out_dir, exist_ok=True)
        pex.run_kpex(name, "2.5D", out_dir, gds=gds)
        pex.run_kpex(name, "fastercap", out_dir, gds=gds)
        c25, _ = pex.read_caps(out_dir, name, "2.5D")
        cfc, _ = pex.read_caps(out_dir, name, "fastercap")

        ab_fc = cfc.get(("A", "B"), 0.0)
        ab_25 = c25.get(("A", "B"), 0.0)
        sub_fc = cfc.get(("A", "VSUBS"), 0.0)
        area = w * h
        low = name.lower()
        print(f"{low}_drc = {sum(geom.values())}")
        print(f"{low}_area_um2 = {area:.3f}")
        print(f"{low}_c_ab_fc = {ab_fc:.6e}")
        print(f"{low}_c_ab_25d = {ab_25:.6e}")
        print(f"{low}_c_asub_fc = {sub_fc:.6e}")
        print(f"{low}_density_ff_um2 = {ab_fc * 1e15 / area:.4f}")
        print(f"{low}_spread = {abs(ab_fc - ab_25) / ab_fc:.6e}"
              if ab_fc else f"{low}_spread = 1")
        sys.stdout.flush()

    print(f"sweep_points = {len(cases)}")


if __name__ == "__main__":
    main(sys.argv[1:])
