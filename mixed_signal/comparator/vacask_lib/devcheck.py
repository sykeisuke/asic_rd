"""Compare ngspice and VACASK drain currents on the model-import check.

    python3 vacask_lib/devcheck.py work/devcheck_ngspice.log work/devcheck.raw [tol]

The ngspice log carries `id_n1 = ...` lines from tb_vacask_devcheck.spice;
the raw file is VACASK's `devcheck.raw` from tb_devcheck.sim. Sign
conventions differ (ngspice reports the source current, VACASK the branch
flow into the source's positive terminal), so magnitudes are compared.
Prints one PASS/FAIL line and the per-device deviation, so a disagreement
comes with its location.
"""
import re
import sys

from rawfile import rawread

NAMES = ["n1", "n2", "n3", "p1", "p2", "p3"]


def main():
    log, raw = sys.argv[1], sys.argv[2]
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
    ng = {}
    with open(log) as f:
        for line in f:
            m = re.match(r"^\s*id_(\w+)\s*=\s*([-+0-9.eE]+)", line)
            if m:
                ng[m.group(1)] = abs(float(m.group(2)))
    plot = rawread(raw).get()
    worst = 0.0
    for n in NAMES:
        va = abs(float(plot[f"vd{n}:flow(br)"][0]))
        if n not in ng:
            print(f"FAIL: ngspice log has no id_{n}")
            return 1
        dev = abs(va - ng[n]) / ng[n]
        worst = max(worst, dev)
        print(f"devcheck_{n}_ngspice_a = {ng[n]:.6e}")
        print(f"devcheck_{n}_vacask_a = {va:.6e}")
        print(f"devcheck_{n}_rel_dev = {dev:.4e}")
    print(f"devcheck_worst_rel_dev = {worst:.4e}")
    if worst <= tol:
        print(f"PASS: VACASK reproduces ngspice drain currents on six GF180 devices to "
              f"{worst*100:.2f} % (tolerance {tol*100:.0f} %)")
        return 0
    print(f"FAIL: VACASK and ngspice disagree by {worst*100:.2f} % on at least one device "
          f"(tolerance {tol*100:.0f} %); VACASK results in this block are not trustworthy")
    return 1


if __name__ == "__main__":
    sys.exit(main())
