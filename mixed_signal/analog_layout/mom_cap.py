#!/usr/bin/env python3
"""Parametric MOM (lateral-flux finger) capacitor generator for gf180mcuD.

    python3 mom_cap.py                 # every preset in CELLS
    python3 mom_cap.py MOMU            # one preset

gf180mcuD ships no MOM device: no model, no pcell, no LVS device, no
area-proportional value.  A finger capacitor is therefore not instantiated,
it is *drawn*, and its value comes from extraction rather than from a
model card.  This file is the drawing; `pex.py` is the extraction.

Why this exists.  Rule MIM.8a sets a 25 um2 minimum FuseTop area, so the
smallest MIM that gf180mcuD can draw is 54.5 fF at the 2.0 fF/um2 flavour
(see simulations/gf180_cap_characterization/RESULTS.md).  There is no MIM
below that floor and no shape trick that gets under it.  A metal finger
capacitor has no minimum-area rule -- only metal width, space and area --
so it is the only structure in this PDK that reaches the 10-20 fF decade.

Geometry.  Two interdigitated combs, plate A fed from a spine along the
bottom edge and plate B from a spine along the top edge, repeated on every
metal in `layers` and strapped between layers by via rows in the spines
only.  Fingers carry no vias, so nothing perturbs the coupled edges.

    +-----------------------------------+   B spine
    |  |     |  |     |  |     |  |     |
    |  |  |  |  |  |  |  |  |  |  |  |  |   B fingers down, A fingers up
    |     |  |     |  |     |  |     |  |
    +-----------------------------------+   A spine

    <-------------- W = 2*nf fingers ---->

METAL5 IS NOT AVAILABLE FOR FINGERS.  gf180mcuD is a 5LM stack, which
makes metal5 the top metal: it is the 11K thick layer and the DRC deck
checks it against MT.1/MT.2a, 0.44 um width and 0.46 um space, not the
0.28/0.28 of M2-M4.  Drawing 0.28 um fingers on metal5 produces 35
violations (measured).  The default stack is therefore M1-M4, and metal5
stays free for routing over the cell.
"""

import os
import sys

import gdsfactory as gf
import gf180mcu

gf180mcu.PDK.activate()

BLOCK = os.path.dirname(os.path.abspath(__file__))
GDS = os.path.join(BLOCK, "physical", "final_views", "gds")
SPICE = os.path.join(BLOCK, "spice")
#- Control cells are build output, not deliverables. They stay out of
#- final_views so that `make drc` and `make lvs` with no CELL keep walking
#- only the cells this project ships -- a deliberately shorted cell in
#- that list would make the default LVS target fail by design.
CONTROLS = os.path.join(BLOCK, "work", "controls")

#- gf180mcuD GDS layer numbers, from the pinned gf180mcu gdsfactory PDK.
METAL = {1: (34, 0), 2: (36, 0), 3: (42, 0), 4: (46, 0), 5: (81, 0)}
LABEL = {1: (34, 10), 2: (36, 10), 3: (42, 10), 4: (46, 10), 5: (81, 10)}
VIA = {1: (35, 0), 2: (38, 0), 3: (40, 0), 4: (41, 0)}

#- V<n>.1 fixes the via at exactly 0.26 um square; V<n>.2a wants 0.26 um
#- between vias and V<n>.2b wants 0.36 um once an array is 4x4 or larger.
#- A single row is not an array, but 0.36 um costs nothing here.
VIA_SIZE = 0.26
VIA_PITCH = 0.62


def rect(c, layer, x0, y0, x1, y1):
    c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)


def mom_cap(name="MOMU", nf=5, lf=4.0, wf=0.28, sf=0.28, ws=0.44,
            layers=(1, 2, 3, 4), units=1, gap=0.28, weave=False,
            short=False):
    """One MOM finger capacitor, or `units` of them abutted left to right.

    nf      finger pairs per unit, so 2*nf fingers
    lf      finger length
    wf, sf  finger width and space -- M2.1/M2.2a floor is 0.28/0.28
    ws      spine width, wide enough for a via row plus V.3c end-of-line
    layers  metal levels carrying fingers; 5 is the thick top metal, see
            the module docstring
    units   abutted copies sharing both spines, for the tiling study
    gap     space between the last finger of a unit and the first of the
            next, `sf` making the array indistinguishable from one wider
            cell
    short   bridge the first A finger to the first B finger on the lowest
            layer -- the defect the control cell exists to be caught by.
            NOTE that `lf` cannot be used for this: it sets the finger
            length and the spine position together, so a longer finger
            moves the spine with it and shorts nothing.
    weave   shift the finger pattern by one position on alternate layers,
            so an A finger sits above a B finger instead of above another
            A finger. That trades the vertical same-net stack for plate
            capacitance between layers; run-mom-cap-sweep.sh measures what
            it is worth.
    """
    c = gf.Component()
    pitch = wf + sf
    nfing = 2 * nf
    unit_w = nfing * wf + (nfing - 1) * sf
    total_w = units * unit_w + (units - 1) * gap

    #- A fingers hang from the bottom spine, B fingers from the top one,
    #- each stopping sf short of the opposite spine. The coupled length of
    #- one A/B pair is therefore lf - sf, not lf.
    ya1 = ws
    yf0, yf1 = ws, ws + lf
    yg0, yg1 = ws + sf, ws + lf + sf
    yb0 = ws + lf + sf
    height = yb0 + ws

    for k, lay in enumerate(layers):
        m = METAL[lay]
        rect(c, m, 0, 0.0, total_w, ya1)
        rect(c, m, 0, yb0, total_w, height)
        shift = (k % 2) if weave else 0
        for u in range(units):
            xu = u * (unit_w + gap)
            for i in range(nfing):
                x0 = xu + i * pitch
                if (i + shift) % 2 == 0:
                    rect(c, m, x0, yf0, x0 + wf, yf1)
                else:
                    rect(c, m, x0, yg0, x0 + wf, yg1)
        #- LVS and kpex take net names from text on the *_label layers.
        c.add_label(text="A", position=(total_w / 2, ws / 2), layer=LABEL[lay])
        c.add_label(text="B", position=(total_w / 2, yb0 + ws / 2),
                    layer=LABEL[lay])

    if short:
        #- a metal bridge across the first finger gap, overlapping into
        #- both fingers so the polygons merge. Minimum width, on the
        #- lowest layer, which is what a real particle defect looks like.
        m = METAL[layers[0]]
        yb = ws + lf / 2
        rect(c, m, wf - 0.08, yb, wf + sf + 0.08, yb + 0.28)

    #- Vias in the spines only. Every layer carries the same spine at the
    #- same place, so an A spine always lands on an A spine -- which is
    #- also why `weave` may shift the fingers without breaking the straps.
    for lower in layers[:-1]:
        v = VIA[lower]
        n = int((total_w - 2 * 0.09 - VIA_SIZE) // VIA_PITCH) + 1
        x0 = (total_w - ((n - 1) * VIA_PITCH + VIA_SIZE)) / 2
        for j in range(n):
            x = x0 + j * VIA_PITCH
            for yc in (ws / 2, yb0 + ws / 2):
                rect(c, v, x, yc - VIA_SIZE / 2, x + VIA_SIZE,
                     yc + VIA_SIZE / 2)

    c.name = name
    return c, total_w, height


#- MOMU is the unit cell this block characterizes: the geometry that lands
#- in the 15-16 fF window the MIM floor cannot reach. MOMU2 is two of them
#- abutted at the same finger spacing, which is what says whether the cell
#- tiles into an array or couples to its neighbour.
CELLS = {
    "MOMU": dict(nf=5, lf=4.0),
    "MOMU2": dict(nf=5, lf=4.0, units=2),
    #- Negative control: MOMU with one finger gap bridged. This is the
    #- failure that destroys a finger capacitor while leaving its
    #- footprint, its layer stack and its DRC verdict untouched, so it is
    #- what says which signoff step in this block is actually
    #- discriminating. See RESULTS.md for the answer, which is not the
    #- one this block was written expecting.
    "MOMUX": dict(nf=5, lf=4.0, short=True),
}

#- Control cells: build output, kept out of physical/final_views so
#- they never join the list `make drc` and `make lvs` walk.
SHORTED = ("MOMUX",)


def lvs_netlist(name):
    """A device-free two-net netlist for `make lvs CELL=<name>`.

    There is no MOM device to compare against, so this proves the one
    thing LVS can prove about a finger capacitor and the one thing that
    silently destroys it: A and B are two nets, not one.
    """
    return (f"* {name}: MOM finger capacitor, drawn not instantiated.\n"
            f"* Two plates, no devices. LVS proves A and B stay separate.\n"
            f".subckt {name} A B\n"
            f".ends {name}\n")


def main(argv):
    names = argv or sorted(CELLS)
    for d in (GDS, SPICE, CONTROLS):
        os.makedirs(d, exist_ok=True)
    for name in names:
        if name not in CELLS:
            raise SystemExit(f"unknown cell {name}; have {sorted(CELLS)}")
        params = dict(CELLS[name])
        c, w, h = mom_cap(name=name, **params)
        out = CONTROLS if name in SHORTED else GDS
        spice_out = CONTROLS if name in SHORTED else SPICE
        c.write_gds(os.path.join(out, name + ".gds"))
        with open(os.path.join(spice_out, name + ".spice"), "w") as fo:
            fo.write(lvs_netlist(name))
        low = name.lower()
        nf = params.get("nf", 5)
        units = params.get("units", 1)
        print(f"{low}_width_um = {w:.3f}")
        print(f"{low}_height_um = {h:.3f}")
        print(f"{low}_area_um2 = {w * h:.3f}")
        print(f"{low}_fingers = {2 * nf * units}")
        print(f"{low}_layers = {''.join(str(x) for x in params.get('layers', (1, 2, 3, 4)))}")
        print(f"{low}_gds = 1")
        print(f"{low}_gds_dir = {os.path.relpath(out, BLOCK)}")


if __name__ == "__main__":
    main(sys.argv[1:])
