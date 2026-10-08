#!/usr/bin/env python3
"""Generate one analog cell's layout with cicpy.

    make layout            # every cell in spice/
    make layout CELL=CMP

Runs inside the pinned IIC-OSIC-TOOLS container; scripts/run-layout.sh is
the entry point.  Produces, per cell, under physical/final_views/:

    gds/<CELL>.gds        the layout
    render/<CELL>.png     KLayout's picture OF THAT GDS, PDK colours
    svg/<CELL>.svg        cicpy's vector view of its own .cic model

Signoff is separate and is KLayout's: see signoff.py, `make drc`,
`make lvs`.  Magic appears here only as cicpy's backend -- it draws the
primitive devices and converts .mag to GDS -- and is not asked for a
verdict about anything.

Every figure of merit is one `name = value` line on stdout, which
check-layout.awk turns into PASS/FAIL and scripts/sim.sh folds into
metrics.json.
"""

import glob
import os
import re
import shutil
import subprocess
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
FINAL = os.path.join(BLOCK, "physical", "final_views")
LIB = "GF180_WSA"
TECHLIB = "gf180mcuD"
MAGIC_RC = f"/foss/pdks/{TECHLIB}/libs.tech/magic/{TECHLIB}.magicrc"


def run(cmd, cwd, log=None, env=None, stdin=None):
    r = subprocess.run(cmd, cwd=cwd, input=stdin, text=True, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if log:
        with open(log, "w") as fo:
            fo.write(r.stdout)
    return r


def cells():
    return sorted(os.path.basename(p)[:-6]
                  for p in glob.glob(os.path.join(BLOCK, "spice", "*.spice")))


def prepare(wanted):
    """A build starts from the design and the netlists, nothing else.

    The generated primitives live under work/, so a stale one from a
    previous run cannot be picked up as this run's.
    """
    design = os.path.join(WORK, "design", LIB)
    shutil.rmtree(os.path.join(WORK, "design"), ignore_errors=True)
    os.makedirs(design)
    for f in glob.glob(os.path.join(BLOCK, "design", LIB, "*.py")):
        shutil.copy(f, design)
    for cell in wanted:
        shutil.copy(os.path.join(BLOCK, "spice", cell + ".spice"), WORK)
    for d in ("gds", "render", "svg"):
        os.makedirs(os.path.join(FINAL, d), exist_ok=True)
    return design


def spi2mag(cell):
    env = dict(os.environ, PYTHONPATH=BLOCK)
    r = run(["cicpy", "spi2mag", f"{cell}.spice", LIB, cell,
             "--libdir", "design/", "--techlib", TECHLIB,
             "--check-connectivity"],
            WORK, os.path.join(WORK, f"{cell}-spi2mag.log"), env)
    if r.returncode != 0:
        print(r.stdout[-3000:], file=sys.stderr)
        raise SystemExit(f"cicpy spi2mag failed for {cell}")
    m = re.search(r"Route short report for \S+: shorts=(\d+)", r.stdout)
    return int(m.group(1)) if m else -1


def write_gds(design, cell):
    """Magic converts the .mag cicpy wrote into GDS. No verdict is asked."""
    run(["magic", "-noconsole", "-dnull", "-rcfile", MAGIC_RC], design,
        os.path.join(design, f"{cell}-gds.log"),
        stdin="\n".join(["crashbackups stop", "addpath _cicpy_primitives",
                         f"load {cell} -silent", "select top cell",
                         f"gds write {cell}", "quit -noprompt"]) + "\n")
    src = os.path.join(design, cell + ".gds")
    if not os.path.exists(src):
        raise SystemExit(f"magic wrote no GDS for {cell}")
    dst = os.path.join(FINAL, "gds", cell + ".gds")
    shutil.copy(src, dst)
    return os.path.getsize(dst)


def render(cell):
    out = os.path.join(FINAL, "render", cell + ".png")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    r = run(["klayout", "-z",
             "-rd", "input=" + os.path.join(FINAL, "gds", cell + ".gds"),
             "-rd", "out=" + out,
             "-r", os.path.join(BLOCK, "klayout", "render.rb")],
            WORK, os.path.join(WORK, f"{cell}-render.log"), env)
    return os.path.getsize(out) if os.path.exists(out) else 0


def svg(design, cell):
    """cicpy's own view, from the .cic.

    spi2mag writes only the top cell and its cuts into the .cic, so the
    primitives have to be included explicitly or the picture is empty.
    """
    includes = []
    for p in sorted(glob.glob(os.path.join(design, "_cicpy_primitives",
                                           "*.cic"))):
        includes += ["--I", p]
    run(["cicpy", "svg", cell + ".cic",
         os.path.join(BLOCK, "tech", "cic", TECHLIB + ".tech"), cell]
        + includes, design, os.path.join(design, f"{cell}-svg.log"),
        dict(os.environ, PATH=os.environ["PATH"]))
    src = os.path.join(design, cell + "_svg", cell + ".svg")
    if not os.path.exists(src):
        return 0
    dst = os.path.join(FINAL, "svg", cell + ".svg")
    shutil.copy(src, dst)
    return os.path.getsize(dst)


def geometry(design, cell):
    """Cell size and device count, from the .mag cicpy just wrote."""
    text = open(os.path.join(design, cell + ".mag")).read()
    m = re.search(r"FIXED_BBOX\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", text)
    #- one written unit is one Magic internal unit, 5 nm, after
    #- cicpy_gf180.patch_magic_scale
    w = h = 0.0
    if m:
        x1, y1, x2, y2 = (int(v) for v in m.groups())
        w, h = (x2 - x1) * 0.005, (y2 - y1) * 0.005
    return w, h, len(re.findall(r"^use ", text, re.M))


def main(wanted):
    known = cells()
    wanted = [c for c in (wanted or known)]
    for c in wanted:
        if c not in known:
            raise SystemExit(f"no spice/{c}.spice; have {', '.join(known)}")
    os.makedirs(WORK, exist_ok=True)
    design = prepare(wanted)

    print(f"techlib = {TECHLIB}")
    for cell in wanted:
        shorts = spi2mag(cell)
        w, h, devices = geometry(design, cell)
        size = write_gds(design, cell)
        png = render(cell)
        pic = svg(design, cell)
        low = cell.lower()
        print(f"{low}_route_shorts = {shorts}")
        print(f"{low}_devices = {devices}")
        print(f"{low}_width_um = {w:.3f}")
        print(f"{low}_height_um = {h:.3f}")
        print(f"{low}_area_um2 = {w * h:.1f}")
        print(f"{low}_gds_bytes = {size}")
        print(f"{low}_render_bytes = {png}")
        print(f"{low}_svg_bytes = {pic}")
    print(f"cells_built = {len(wanted)}")


if __name__ == "__main__":
    main(sys.argv[1:])
