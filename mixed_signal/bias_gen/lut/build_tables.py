"""Pack the techsweep output into a gm/Id table.

    python3 build_tables.py <ts.txt> <ts.idx> <out.npz>

ts.txt holds one row per (VDS, VGS) point, columns
    scale vg vd id gm gds vth vdsat
in blocks of len(VGS) x len(VDS) rows, one block per (L, W, VSB) in the
order ts.idx lists. The npz holds arrays indexed [L, W, VSB, VDS, VGS] of
|id|, gm, gds, |vth|, |vdsat| and the grids. Every value is a magnitude.
"""
import sys

import numpy as np

VGS = np.round(np.arange(0.0, 2.2 + 1e-9, 0.01), 4)
VDS = np.round(np.arange(0.2, 2.6 + 1e-9, 0.2), 4)


def num(tok):
    tok = tok.strip()
    scale = {"u": 1e-6, "n": 1e-9, "m": 1e-3}
    return float(tok[:-1]) * scale[tok[-1]] if tok[-1] in scale else float(tok)


def main():
    txt, idx, out = sys.argv[1:4]
    raw = np.loadtxt(txt)
    blocks = [tuple(num(t) for t in line.split()[1:4]) for line in open(idx) if line.startswith("BLOCK")]
    n = len(VGS) * len(VDS)
    if raw.shape[0] != n * len(blocks) or raw.shape[1] != 8:
        raise SystemExit(f"FAIL: {txt}: {raw.shape} rows/cols, expected {n * len(blocks)} x 8")
    L = sorted({b[0] for b in blocks})
    W = sorted({b[1] for b in blocks})
    B = sorted({abs(b[2]) for b in blocks})
    shape = (len(L), len(W), len(B), len(VDS), len(VGS))
    arr = {k: np.full(shape, np.nan) for k in ("id", "gm", "gds", "vth", "vdsat")}
    for k, (l, w, b) in enumerate(blocks):
        blk = raw[k * n:(k + 1) * n]
        vg = np.round(np.abs(blk[:, 1]), 4)
        vd = np.round(np.abs(blk[:, 2]), 4)
        iv = np.searchsorted(VGS, vg)
        idd = np.searchsorted(VDS, vd)
        if not (np.allclose(VGS[iv], vg) and np.allclose(VDS[idd], vd)):
            raise SystemExit(f"FAIL: block {k} grid mismatch")
        il, iw, ib = L.index(l), W.index(w), B.index(abs(b))
        for col, key in ((3, "id"), (4, "gm"), (5, "gds"), (6, "vth"), (7, "vdsat")):
            arr[key][il, iw, ib, idd, iv] = np.abs(blk[:, col])
    for key, a in arr.items():
        if np.isnan(a).any():
            raise SystemExit(f"FAIL: {key} has {int(np.isnan(a).sum())} unfilled points")
    np.savez(out, L=np.array(L), W=np.array(W), VSB=np.array(B), VDS=VDS, VGS=VGS, **arr)
    print(f"table {out}: L {L} W {W} VSB {B}, {len(blocks)} blocks")


if __name__ == "__main__":
    main()
