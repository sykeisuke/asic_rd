"""Row floorplan of bias_gen: one PMOS row over one NMOS row, every finger
the same L and W, matched devices interdigitated common-centroid (each row a
palindrome), unmatched startup devices outside the matched block, dummies at
both ends, the shorter row padded with dummies to the longer one's length,
the degeneration resistor as strips beside the rows, the MIM decaps over them.

    ./container.sh 'python3 floorplan.py'            (run.sh phase `floorplan`)

Reads data/sizing.json. Writes data/rows.txt (finger order, one token per
finger), data/floorplan.json (centroid error of every matched device, row
length, footprint) and assets/floorplan.png. Prints the centroid gate.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bg  # noqa: E402

CENTROID_MAX = 0.5          # |centroid - row centre| in finger pitches, matched devices [A]


def interleave(counts):
    """Spread counts {dev: n} over sum(n) slots, each device as evenly as possible
    (largest-deficit first, ties by name for determinism)."""
    total = sum(counts.values())
    placed = {k: 0 for k in counts}
    seq = []
    for i in range(total):
        best = max(counts, key=lambda k: (counts[k] * (i + 1) / total - placed[k], counts[k], k) if placed[k] < counts[k] else (-1e9, 0, k))
        seq.append(best)
        placed[best] += 1
    return seq


def palindrome(counts):
    """A row whose every device is (near) centred: halves interleaved and mirrored,
    the odd fingers in the middle, alternated about the centre."""
    half = {k: v // 2 for k, v in counts.items() if v // 2 > 0}
    odd = sorted([k for k, v in counts.items() if v % 2], key=lambda k: -counts[k])
    left = interleave(half) if half else []
    mid = []
    for i, k in enumerate(odd):
        if i % 2 == 0:
            mid.append(k)
        else:
            mid.insert(0, k)
    return left + mid + left[::-1]


def rows_of(s):
    p_match = {"MP1": s["npm"], "MP2": s["npm"], "OV": s["nm"], "OB": s["nm"]}
    n_match = {"MN1": s["na"], "MN2": s["K"] * s["na"], "OR": s["nr"]}
    n_match.update({f"OC{k}": s["nc"] for k in range(bg.N_CMP)})
    p_core = palindrome(p_match)
    n_core = palindrome(n_match)
    nb = s["nbl"]
    p_start = [f"SB{k + 1}" for k in range(nb)]
    p_row = p_start[: nb // 2] + p_core + p_start[nb // 2:]
    n_row = ["SU4"] + n_core + ["SU5"]
    total = max(len(p_row), len(n_row)) + 4
    def pad(r):
        extra = total - len(r)
        return ["D"] * (extra // 2) + r + ["D"] * (extra - extra // 2)
    return pad(p_row), pad(n_row), p_match, n_match


def centroid_err(row, dev):
    pos = [i for i, t in enumerate(row) if t == dev]
    return float(np.mean(pos) - (len(row) - 1) / 2.0)


def main():
    s = json.load(open(os.path.join(bg.BLOCK, "data", "sizing.json")))
    for k in ("K", "na", "npm", "nc", "nr", "nm", "nbl", "rseg"):
        s[k] = int(s[k])
    p_row, n_row, pm, nm = rows_of(s)
    pitch = s["L"] + bg.FINGER_PITCH_EXTRA
    errs = {d: centroid_err(p_row, d) for d in pm}
    errs.update({d: centroid_err(n_row, d) for d in nm})
    worst = max(errs, key=lambda d: abs(errs[d]))
    length = len(p_row) * pitch
    row_h = s["wf"] + bg.ROW_OVERHEAD
    res_w = s["rseg"] * (bg.RES_W + 1.0)
    foot_w = length + 2.0 + res_w
    foot_h = 2 * row_h
    with open(os.path.join(bg.BLOCK, "data", "rows.txt"), "w") as h:
        h.write("# bias_gen finger order, left to right; D = dummy (gate, source, drain tied to the rail)\n")
        h.write("PMOS " + " ".join(p_row) + "\n")
        h.write("NMOS " + " ".join(n_row) + "\n")
    json.dump(dict(fingers_per_row=len(p_row), dummies_p=p_row.count("D"), dummies_n=n_row.count("D"),
                   pitch_um=pitch, row_length_um=length, row_height_um=row_h, res_strips=s["rseg"],
                   footprint_um=[foot_w, foot_h], footprint_um2=foot_w * foot_h, centroid_err_pitch=errs),
              open(os.path.join(bg.BLOCK, "data", "floorplan.json"), "w"), indent=1)
    print(f"fp_fingers_per_row = {len(p_row)}")
    print(f"fp_dummies_p = {p_row.count('D')}")
    print(f"fp_dummies_n = {n_row.count('D')}")
    print(f"fp_row_length_um = {length:.2f}")
    print(f"fp_footprint_um2 = {foot_w * foot_h:.1f}")
    print(f"fp_centroid_worst_pitch = {abs(errs[worst]):.3f}")
    ok = abs(errs[worst]) <= CENTROID_MAX and len(p_row) == len(n_row)
    print(("PASS" if ok else "FAIL") + f": floorplan: both rows {len(p_row)} fingers, every matched device centred within "
          f"{abs(errs[worst]):.2f} pitch (worst {worst}; bound {CENTROID_MAX})")
    plot(s, p_row, n_row, pitch, row_h, errs)
    return 0 if ok else 1


COLORS = {"MP1": "#1f6fb4", "MP2": "#5aa0d8", "OV": "#e08a1e", "OB": "#f2b766", "MN1": "#1f6fb4", "MN2": "#5aa0d8",
          "OR": "#7a4fb0", "OC0": "#2e9e5b", "OC1": "#55b87c", "OC2": "#2e9e5b", "OC3": "#55b87c", "D": "#c8c8c8"}


NAMES = {"MP1": "core PMOS mirror XMP1", "MP2": "core PMOS diode XMP2", "OV": "midref source XOV", "OB": "midref source XOB",
         "MN1": "core NMOS diode XMN1", "MN2": "core NMOS XMN2 (K x)", "OR": "ramp sink XOR",
         "OC0": "comparator sinks XOC0 / XOC2", "OC1": "comparator sinks XOC1 / XOC3", "D": "dummy", "SB1": "startup"}


def draw_rows(ax, s, p_row, n_row, pitch, row_h, lo, hi, labels):
    from matplotlib.patches import Rectangle
    for y0, row in ((row_h + 0.6, p_row), (0.0, n_row)):
        for i in range(lo, hi):
            t = row[i]
            c = COLORS.get(t, "#d9534f" if t.startswith(("SB", "SU")) else "#999")
            ax.add_patch(Rectangle((i * pitch + 0.08, y0 + 0.4), pitch - 0.16, s["wf"] + 0.6, color=c, lw=0))
            if labels:
                ax.text(i * pitch + pitch / 2, y0 + 0.4 + (s["wf"] + 0.6) / 2, t, ha="center", va="center",
                        fontsize=7, rotation=90, color="white" if t != "D" else "#444")
        ax.add_patch(Rectangle((lo * pitch - 0.3, y0 + 0.1), (hi - lo) * pitch + 0.6, row_h - 0.6, fill=False,
                               ls="--", lw=0.8, ec="#666"))


def plot(s, p_row, n_row, pitch, row_h, errs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle
    n = len(p_row)
    fig, (ax, az) = plt.subplots(2, 1, figsize=(16, 7.5), gridspec_kw=dict(height_ratios=[1, 1.6]))
    # full rows + resistor strips
    draw_rows(ax, s, p_row, n_row, pitch, row_h, 0, n, labels=False)
    x0 = n * pitch + 1.5
    for k in range(int(s["rseg"])):
        ax.add_patch(Rectangle((x0 + k * (bg.RES_W + 1.0), 0.1), bg.RES_W, 2 * row_h + 0.2, color="#b5651d", lw=0))
    ax.text(-1, row_h + 0.6 + row_h / 2, "PMOS row\n(n-well, vdd)", ha="right", va="center", fontsize=8)
    ax.text(-1, row_h / 2, "NMOS row\n(p-sub, vss)", ha="right", va="center", fontsize=8)
    ax.text(x0 + s["rseg"] * (bg.RES_W + 1.0) / 2, 2 * row_h + 1.0, f"R {int(s['rseg'])} x {s['rlen']:.1f} um\n{bg.RES_TYPE}",
            ha="center", fontsize=7)
    lo, hi = n // 2 - 18, n // 2 + 18
    ax.add_patch(Rectangle((lo * pitch, -0.4), (hi - lo) * pitch, 2 * row_h + 1.0, fill=False, ec="k", lw=1.2))
    ax.set_xlim(-22, x0 + s["rseg"] * (bg.RES_W + 1.0) + 2)
    ax.set_ylim(-1, 2 * row_h + 3.0)
    ax.set_aspect("equal")
    ax.axis("off")
    worst = max(abs(v) for v in errs.values())
    ax.set_title(f"bias_gen: one PMOS row over one NMOS row, L {s['L']:g} um, finger W {s['wf']:g} um, {n} fingers per row "
                 f"(pitch {pitch:.2f} um, {n * pitch:.0f} um long); every row a palindrome, worst matched-device centroid "
                 f"error {worst:.2f} pitch; MIM decaps (pb {s['cpb']:g} pF, nb {s['cnb']:g} pF) over the rows", fontsize=9)
    # zoom on the row centre
    draw_rows(az, s, p_row, n_row, pitch, row_h, lo, hi, labels=True)
    az.axvline((n / 2) * pitch, color="k", ls=":", lw=1)
    az.text((n / 2) * pitch, 2 * row_h + 0.9, "row centre (common centroid)", ha="center", fontsize=8)
    az.set_xlim(lo * pitch - 1, hi * pitch + 1)
    az.set_ylim(-0.5, 2 * row_h + 1.6)
    az.set_aspect("equal")
    az.axis("off")
    az.set_title(f"zoom: fingers {lo}..{hi - 1} (boxed above)", fontsize=9)
    keys = ["MP2", "MP1", "OV", "OB", "MN1", "MN2", "OR", "OC0", "OC1", "SB1", "D"]
    handles = [Patch(color=COLORS.get(k, "#d9534f"), label=NAMES[k]) for k in keys]
    az.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=6, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(bg.BLOCK, "assets", "floorplan.png"), dpi=150)


if __name__ == "__main__":
    sys.exit(main())
