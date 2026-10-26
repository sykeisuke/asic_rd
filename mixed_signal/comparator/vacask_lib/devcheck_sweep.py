"""Geometry sweep of the ngspice-vs-VACASK model check.

    python3 vacask_lib/devcheck_sweep.py [corner] [tol]

Builds one ngspice deck and one VACASK netlist with the SAME list of
(device, L, W, nf, m) instances, each with its own drain source at a fixed
bias, runs both simulators, and prints the relative drain-current deviation
per geometry plus one PASS/FAIL line. The six-device tb_vacask_devcheck is
the gate; this sweep is the diagnostic that says WHICH bin or which finger
count disagrees when the gate fails. Runs from the block directory and
writes only under work/.
"""
import os
import re
import subprocess
import sys

from rawfile import rawread

GEOMS = [
    # dev, L um, W um, nf, m
    ("nfet_03v3", 0.28, 0.8, 1, 1), ("nfet_03v3", 0.28, 4.0, 4, 1),
    ("nfet_03v3", 0.5, 2.0, 1, 1), ("nfet_03v3", 0.5, 12.0, 3, 1),
    ("nfet_03v3", 0.5, 30.0, 8, 1), ("nfet_03v3", 1.0, 20.0, 10, 1),
    ("nfet_03v3", 2.0, 1.0, 1, 2), ("nfet_03v3", 8.0, 20.0, 1, 1),
    ("pfet_03v3", 0.28, 0.8, 1, 1), ("pfet_03v3", 0.28, 4.24, 1, 1),
    ("pfet_03v3", 0.5, 5.0, 1, 1), ("pfet_03v3", 0.5, 12.0, 1, 1),
    ("pfet_03v3", 0.5, 30.8, 1, 1), ("pfet_03v3", 0.5, 30.8, 8, 1),
    ("pfet_03v3", 1.0, 20.0, 1, 1), ("pfet_03v3", 1.0, 20.0, 10, 1),
    ("pfet_03v3", 1.0, 90.5, 20, 1), ("pfet_03v3", 2.0, 12.0, 1, 1),
    ("pfet_03v3", 8.0, 20.0, 1, 1),
]
VDD = 3.3


def main():
    corner = sys.argv[1] if len(sys.argv) > 1 else "typical"
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.02
    ng = ["* devcheck sweep, ngspice side (generated)",
          ".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice",
          f".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {corner}",
          f"VDD vdd 0 {VDD}", "VGN gn 0 1.0", "VGP gp 0 2.3"]
    va = ["devcheck sweep, VACASK side (generated)", "ground 0",
          f'include "gf180_03v3_{corner}.inc"', "model vsource vsource",
          f"vdd (vdd 0) vsource dc={VDD}", "vgn (gn 0) vsource dc=1.0",
          "vgp (gp 0) vsource dc=2.3"]
    prints, saves = [], []
    for i, (dev, l, w, nf, m) in enumerate(GEOMS):
        if dev.startswith("n"):
            ng += [f"VD{i} d{i} 0 1.0", f"X{i} d{i} gn 0 0 {dev} L={l}u W={w}u nf={nf} m={m}"]
            va += [f"vd{i} (d{i} 0) vsource dc=1.0",
                   f"x{i} (d{i} gn 0 0) {dev} l={l}u w={w}u nf={nf} m={m}"]
        else:
            ng += [f"VD{i} d{i} 0 2.3", f"X{i} d{i} gp vdd vdd {dev} L={l}u W={w}u nf={nf} m={m}"]
            va += [f"vd{i} (d{i} 0) vsource dc=2.3",
                   f"x{i} (d{i} gp vdd vdd) {dev} l={l}u w={w}u nf={nf} m={m}"]
        prints.append(f"let id_{i} = i(vd{i})\nprint id_{i}")
        saves.append(f"i(vd{i})")
    ng += [".control", "op"] + prints + ["quit", ".endc", ".end"]
    va += ["control", "  var mm=0", "  options temp=27", "  save " + " ".join(saves),
           "  analysis dcs op", "endc"]
    os.makedirs("work", exist_ok=True)
    with open("work/dcs.spice", "w") as f:
        f.write("\n".join(ng) + "\n")
    with open("work/dcs.sim", "w") as f:
        f.write("\n".join(va) + "\n")
    subprocess.run(["ngspice", "-b", "-o", "work/dcs_ngspice.log", "work/dcs.spice"],
                   capture_output=True)
    r = subprocess.run(["vacask", "dcs.sim"], cwd="work", capture_output=True, text=True)
    if not os.path.exists("work/dcs.raw"):
        print("FAIL: VACASK produced no dcs.raw")
        print(r.stdout[-2000:])
        return 1
    vals = {}
    with open("work/dcs_ngspice.log") as f:
        for line in f:
            mm = re.match(r"^\s*id_(\d+)\s*=\s*([-+0-9.eE]+)", line)
            if mm:
                vals[int(mm.group(1))] = abs(float(mm.group(2)))
    plot = rawread("work/dcs.raw").get()
    worst = 0.0
    for i, (dev, l, w, nf, m) in enumerate(GEOMS):
        a = vals.get(i)
        b = abs(float(plot[f"vd{i}:flow(br)"][0]))
        if a is None:
            print(f"FAIL: ngspice gave no current for geometry {i}")
            return 1
        dev_rel = abs(a - b) / a
        worst = max(worst, dev_rel)
        print(f"REPORT: {dev} L={l}u W={w}u nf={nf} m={m}: ngspice {a:.4e} A, "
              f"vacask {b:.4e} A, dev {dev_rel*100:.3f} %")
    print(f"devcheck_sweep_worst_rel_dev = {worst:.4e}")
    if worst <= tol:
        print(f"PASS: VACASK matches ngspice on {len(GEOMS)} geometries to "
              f"{worst*100:.2f} % ({corner})")
        return 0
    print(f"FAIL: VACASK deviates from ngspice by {worst*100:.2f} % on at least one "
          f"geometry ({corner})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
