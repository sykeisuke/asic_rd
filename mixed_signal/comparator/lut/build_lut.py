"""Assemble a pygmid-compatible gm/Id lookup table from ngspice techsweep output.

Consumes the flat text emitted by techsweep_<device>.spice and writes a
4-D table (L x VGS x VDS x VSB) as a pickle that pygmid's Lookup class
loads directly.

The capacitance/conductance assembly follows Boris Murmann's GF180MCU
converter (Book-on-gm-ID-design, starter_files_open_source_tools/
gf180mcuD/techsweep_txt_to_mat.ipynb) exactly:

    CGG = cgg + cgdo + cgso
    CGB = -cgb
    CGD = -cgd + cgdo
    CGS = -cgs + cgso
    CDD = cdd + capbd + cgdo
    CSS = css + capbs + cgso

Array axis order [L, VGS, VDS, VSB] matches that converter and is what
pygmid's interpolation expects. Rather than trusting ngspice's emission
order, every sample is scatter-indexed using the L/VGS/VDS/VSB it carries
in its own row, and the build fails unless every grid slot is filled
exactly once.

Usage: python3 build_lut.py <device> <W_um> <NFING>
"""

import pickle
import sys

import numpy as np

# Column order written by the techsweep deck's wrdata call. Column 0 is the
# wrdata single-scale column (the dc sweep abscissa) and is discarded.
COLUMNS = [
    "scale", "vg", "vd", "vb", "l",
    "id", "vth", "gm", "gmbs", "gds",
    "cgg", "cgs", "cgd", "cgb",
    "cdd", "css", "cgdo", "cgso",
    "capbd", "capbs",
]

# Grid the deck sweeps; must stay in step with techsweep_<device>.spice.
L_GRID = np.array(
    [0.28, 0.30, 0.32, 0.34, 0.36]
)
VGS_GRID = np.round(np.arange(0.0, 3.3 + 1e-9, 0.025), 6)
VDS_GRID = np.round(np.arange(0.0, 3.3 + 1e-9, 0.025), 6)
VSB_GRID = np.array([0.0, 0.2, 0.4])


def load_raw(path):
    raw = np.loadtxt(path)
    if raw.shape[1] != len(COLUMNS):
        raise SystemExit(
            f"FAIL: {path} has {raw.shape[1]} columns, expected {len(COLUMNS)}"
        )
    return {name: raw[:, i] for i, name in enumerate(COLUMNS)}


def axis_index(values, grid, label):
    """Map each sample's own recorded bias/geometry onto its grid index."""
    idx = np.abs(values[:, None] - grid[None, :]).argmin(axis=1)
    if not np.allclose(values, grid[idx], atol=2e-3):
        worst = np.max(np.abs(values - grid[idx]))
        raise SystemExit(
            f"FAIL: {label} values are off-grid (worst mismatch {worst:.4g})"
        )
    return idx


def diagnose(path):
    """Report the raw file's actual column layout through the flow's stdout."""
    raw = np.loadtxt(path, max_rows=40000)
    print(f"INFO: diagnose shape {raw.shape}")
    for i in range(raw.shape[1]):
        col = raw[:, i]
        u = np.unique(col)
        name = COLUMNS[i] if i < len(COLUMNS) else f"col{i}"
        print(
            f"INFO: col{i:02d} ({name}) nuniq={u.size} "
            f"first3={col[:3]} min={col.min():.6g} max={col.max():.6g}"
        )


def main():
    if sys.argv[1] == "--diagnose":
        diagnose(sys.argv[2])
        return
    device, w_um, nfing = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
    path = f"../work/lut/techsweep_{device}.txt"

    d = load_raw(path)
    nl, nvgs, nvds, nvsb = len(L_GRID), len(VGS_GRID), len(VDS_GRID), len(VSB_GRID)
    shape = (nl, nvgs, nvds, nvsb)

    # Each sample carries its own L/VGS/VDS/VSB, so place it by index rather
    # than trusting any emission order.
    il = axis_index(np.round(d["l"] * 1e6, 2), L_GRID, f"{device} L")
    ig = axis_index(d["vg"], VGS_GRID, f"{device} VGS")
    idr = axis_index(d["vd"], VDS_GRID, f"{device} VDS")
    ib = axis_index(np.abs(d["vb"]), VSB_GRID, f"{device} VSB")

    flat = np.ravel_multi_index((il, ig, idr, ib), shape)
    counts = np.bincount(flat, minlength=int(np.prod(shape)))
    if counts.min() != 1 or counts.max() != 1:
        raise SystemExit(
            f"FAIL: {device} grid coverage is not exactly 1 sample per slot "
            f"(min {counts.min()}, max {counts.max()})"
        )
    print(f"INFO: {device} grid_coverage every slot filled exactly once")

    def R(name):
        out = np.empty(shape, dtype=np.float64)
        out.flat[flat] = d[name]
        return out

    cgdo, cgso = R("cgdo"), R("cgso")

    # pygmid indexes both device types by positive VGS/VDS magnitudes, so ID
    # and VT are stored as magnitudes. Which raw sign BSIM reports depends on
    # the deck's terminal polarity, so detect it from a strongly-on
    # saturation slice instead of hardcoding a per-device-type guess, and
    # report it so the choice is auditable.
    def as_magnitude(name, arr):
        on = (VGS_GRID > 2.0)[None, :, None, None] & (
            (VDS_GRID > 1.0)[None, None, :, None]
        )
        med = np.median(arr[np.broadcast_to(on, arr.shape)])
        sign = -1.0 if med < 0 else 1.0
        print(f"{device}_sign_{name.lower()} = {sign:.0f}")
        return sign * arr

    table = {
        "INFO": f"GlobalFoundries gf180mcuD, {device}, BSIM4, ngspice techsweep",
        "CORNER": "NOM",
        "TEMP": 300.0,
        "NFING": nfing,
        "W": w_um * 1e-6,
        "L": L_GRID,
        "VGS": VGS_GRID,
        "VDS": VDS_GRID,
        "VSB": VSB_GRID,
        "ID": as_magnitude("ID", R("id")),
        "VT": as_magnitude("VT", R("vth")),
        "GM": R("gm"),
        "GMB": R("gmbs"),
        "GDS": R("gds"),
        "CGG": R("cgg") + cgdo + cgso,
        "CGB": -R("cgb"),
        "CGD": -R("cgd") + cgdo,
        "CGS": -R("cgs") + cgso,
        "CDD": R("cdd") + R("capbd") + cgdo,
        "CSS": R("css") + R("capbs") + cgso,
    }

    # Physical sanity at a mid-rail saturation slice, reported as checker
    # lines so the verdict lands in metrics.json rather than only in a log.
    vds_mid = int(np.argmin(np.abs(VDS_GRID - 1.65)))
    gm, idd = table["GM"][:, :, vds_mid, 0], table["ID"][:, :, vds_mid, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        gm_id = np.where(idd > 0, gm / np.maximum(idd, 1e-18), np.nan)
    peak = np.nanmax(gm_id)
    print(f"{device}_peak_gm_id = {peak:.4f}")

    on = VGS_GRID > 1.5
    for name in ("ID", "VT", "GM", "GDS", "CGG", "CGS", "CDD", "CSS"):
        block = table[name][:, on, vds_mid, 0]
        print(f"{device}_min_{name.lower()}_on = {np.min(block):.6g}")

    out = f"../work/lut/{device}.pkl"
    with open(out, "wb") as f:
        pickle.dump(table, f)
    total = nl * nvgs * nvds * nvsb
    print(f"{device}_table_points = {total}")
    print(f"INFO: {device} table_written {out}")


if __name__ == "__main__":
    main()
