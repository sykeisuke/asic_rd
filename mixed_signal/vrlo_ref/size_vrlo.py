"""size_vrlo.py -- sizing of the VR_LO shunt regulator (README.md s.3).

Stage A  random sample of the free sizes at typical / 27 C / 3.3 V and at
         ss / 85 C / 3.0 V (the binding cell, gates at 0.85x) on
         tb_tran.spice (KS=1 and KS=0 per point): gates start, kick, rec,
         rep, err (vr.tran_gates) at a 0.7x margin, loop phase margin
         (tb_loop.spice, reset and ramp state) >= 45/0.7 deg; power = the regulator's
         supply current incl. its ideal bias x 3.3 V in the reset state;
         area = vr.area_um2.
Stage B  the stage-A passers in power x area order, at the PVT extremes
         (ss/0 C/3.0 V, ff/85 C/3.6 V, ss/85 C/3.0 V, ff/0 C/3.6 V, sf and fs
         at 27 C) and at typical with the ideal bias at 0.69x / 1.77x and the
         ramp current at 0.74x / 1.62x, all gates at 1.0x. The first design
         that passes every cell, and whose Monte Carlo sigma(vrlo) at typical
         (60 draws, tb_mc.spice) is <= 0.85 LSB and whose typical noise is
         <= 0.85 x 0.04 LSB, is selected.

Free sizes (README.md s.3 gives the reasons for the fixed ones):
  IB  unit bias current (one finger of every bias mirror), 0.5-3 uA
  NT  tail fingers 2-12 (I_tail = NT x IB)     NI, LI  input pair fingers 1-8, L 0.5/1/2
  N3  diode-side load fingers 2-12             N5  g-node diode fingers (A ~ N3/N5)
  LL  L of XM3/XM4/XM5/XMS (one mirror)        NS  shunt fingers 2-40
  CDW side of the vrlo MIM decap, 10-70 um (0.2-9.8 pF)
Derived: NK (keep-alive fingers) balances the shunt's mirror-set current
NS/N3 x I_tail/2 against NK x IB + the typical ramp current.
Fixed: LB 1 um, divider units 1 x 20 um ppolyf_u_3k, tap MIM 22.4 um (1 pF).

    ./container.sh 'python3 size_vrlo.py'                      both stages
    ./container.sh 'EVAL=data/sizing.json python3 size_vrlo.py'  one design, typical
Writes data/stage_a.csv, data/stage_b.json, data/sizing.json, work/vrlo_ref.spice
(run.sh compares it with vrlo_ref.spice).
"""
import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import verify_vrlo as V
import vr

N_A = int(os.environ.get("N_A", "800"))
N_B = int(os.environ.get("N_B", "40"))
SEED = int(os.environ.get("SEED", "20261009"))
MARGIN_A = 0.7
A_WORST = ("ss", 85, 3.0)     # every stage-B failure of the first search (600 points) was here
MARGIN_W = 0.85
N_MC_B = 60                   # stage-B mismatch draws (typical); verification runs 200
MC_B_MAX = 0.85               # LSB: vr.SIGMA_MAX_LSB less ~2 standard errors of a 60-draw estimate
NZ_B_MAX = 0.85 * vr.NOISE_MAX_LSB   # typical noise; verification checks three corners at 1.0x
IRAMP_TYP = 0.487e-6          # D: 0.469 uA x 1.0383 (runs/analog-top/20261009T020546Z)
FIXED = dict(LB=1.0, LRU=20.0, CTW=22.4)

B_CELLS = [  # (corner, temp, vdd, bias scale, ramp-current scale)
    ("ss", 0, 3.0, 1.0, 1.0), ("ff", 85, 3.6, 1.0, 1.0), ("ss", 85, 3.0, 1.0, 1.0), ("ff", 0, 3.6, 1.0, 1.0),
    ("sf", 27, 3.3, 1.0, 1.0), ("fs", 27, 3.3, 1.0, 1.0),
    ("typical", 27, 3.3, vr.IBS_SPAN[0], 1.0), ("typical", 27, 3.3, vr.IBS_SPAN[1], 1.0),
    ("typical", 27, 3.3, 1.0, vr.IRS_SPAN[0]), ("typical", 27, 3.3, 1.0, vr.IRS_SPAN[1]),
]


def sample(rng):
    while True:
        s = dict(FIXED)
        s["IB"] = float(np.round(rng.uniform(0.5, 3.0), 2))
        s["NT"] = int(rng.integers(2, 13))
        s["NI"] = int(rng.integers(1, 9))
        s["LI"] = float(rng.choice([0.5, 1.0, 2.0]))
        s["N3"] = int(rng.integers(2, 13))
        s["N5"] = int(rng.integers(1, s["N3"]))
        s["LL"] = float(rng.choice([0.5, 1.0]))
        s["NS"] = int(rng.integers(2, 41))
        s["CDW"] = float(np.round(rng.uniform(10, 70), 1))
        if derive(s):
            return s


def derive(s):
    ib = s["IB"] * 1e-6
    ish = s["NS"] / s["N3"] * s["NT"] * ib / 2
    nk = int(round((ish - IRAMP_TYP) / ib))
    if nk < 1 or nk > 24:
        return False
    s["NK"] = nk
    return True


def evaluate(tag, s, cell=("typical", 27, vr.VDD), ibs=1.0, irs=1.0, margin=1.0):
    txt = vr.netlist(s)
    r = vr.tran_pair(tag, txt, cell[:3], ibs, irs, s["IB"] * 1e-6)
    g = vr.tran_gates(r, cell[2])
    lim = dict(start=vr.EPS, kick=vr.EPS, rec=vr.EPS, rep=vr.EPS, err=vr.VERR_MAX)
    ok = all(np.isfinite(v) and v <= margin * lim[k] for k, (_, v) in g.items())
    # loop phase margin, both reset states; stage A asks PM_MIN / margin (64 deg)
    pm = {}
    for rst in (1, 0):
        lp = vr.loop(tag, txt, cell[:3], ibs, irs, s["IB"] * 1e-6, rst)
        pm[rst] = (lp.get("pm_deg", np.nan), lp.get("ugb_hz", np.nan))
    ok = ok and all(np.isfinite(pm[x][0]) and pm[x][0] >= vr.PM_MIN / margin for x in (1, 0))
    p = r.get("ireg_q", np.nan) * cell[2]
    return dict(ok=ok, power_uw=p * 1e6, **{k: v for k, (_, v) in g.items()},
                pm1=pm[1][0], ugb1_mhz=pm[1][1] / 1e6, pm0=pm[0][0], ugb0_mhz=pm[0][1] / 1e6,
                vr_pk=r.get("vr_pk", np.nan), ireg_r_ua=r.get("ireg_r", np.nan) * 1e6)


def stage_a():
    rng = np.random.default_rng(SEED)
    pts = [sample(rng) for _ in range(N_A)]

    def one(k):
        s = pts[k]
        e = evaluate(os.path.join("a", f"p{k}"), s, margin=MARGIN_A)
        # the binding cell for the kick and the loop speed (first search, README.md s.3)
        w = evaluate(os.path.join("a", f"p{k}w"), s, A_WORST, margin=MARGIN_W)
        e["ok"] = e["ok"] and w["ok"]
        e.update({f"w_{x}": w[x] for x in ("kick", "rec", "err", "pm1", "pm0")})
        return dict(k=k, **s, **e, area_um2=vr.area_um2(s)[0])
    with ThreadPoolExecutor(vr.JOBS) as ex:
        rows = list(ex.map(one, range(N_A)))
    os.makedirs(vr.DATA, exist_ok=True)
    keys = list(rows[0].keys())
    with open(os.path.join(vr.DATA, "stage_a.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)
    ok = [r for r in rows if r["ok"]]
    print(f"stage_a_points = {len(rows)}")
    print(f"stage_a_pass = {len(ok)}")
    for g in ("start", "kick", "rec", "rep", "err"):
        lim = vr.VERR_MAX if g == "err" else vr.EPS
        print(f"REPORT: stage A gate {g}: {sum(1 for r in rows if r[g] <= MARGIN_A * lim)} of {len(rows)} pass")
    return sorted(ok, key=lambda r: r["power_uw"] * r["area_um2"])


def stage_b(cands):
    picked, log = None, []
    for r in cands[:N_B]:
        s = {k: r[k] for k in ("IB", "NT", "NI", "LI", "N3", "N5", "LL", "NS", "NK", "CDW", *FIXED)}

        def one(c):
            return c, evaluate(os.path.join("b", f"p{r['k']}", "%s_%g_%g_%g_%g" % c), s, c[:3], c[3], c[4])
        with ThreadPoolExecutor(vr.JOBS) as ex:
            res = list(ex.map(one, B_CELLS))
        nbad = sum(not e["ok"] for _, e in res)
        sig = nz = np.nan
        if nbad == 0:
            # mismatch: the first selection (p55, LL 0.5 um) read 1.52 LSB in verification
            a = V.mc_draws(vr.netlist(s), s["IB"] * 1e-6, f"b_mc{r['k']}", range(N_MC_B + 1))
            sig = float(np.std(a[1:, 1], ddof=1) / vr.LSB) if a.shape[0] > 2 else np.nan
            nbad += 0 if sig <= MC_B_MAX else 1
            nz = V.noise_lsb(vr.netlist(s), s["IB"] * 1e-6, ("typical", 27, vr.VDD), f"b_nz{r['k']}")
            nbad += 0 if nz <= NZ_B_MAX else 1
        log.append(dict(k=r["k"], power_uw=r["power_uw"], area_um2=r["area_um2"], fails=nbad, mc_sigma_lsb=sig, noise_lsb=nz,
                        cells=[dict(cell=list(c), **e) for c, e in res]))
        print(f"REPORT: stage B p{r['k']}: {r['power_uw']:.1f} uW, {r['area_um2']:.0f} um2, "
              f"{sum(e['ok'] for _, e in res)} of {len(B_CELLS)} cells pass, MC sigma {sig:.3f} LSB "
              f"({N_MC_B} draws, limit {MC_B_MAX}), noise {nz:.4f} LSB (limit {NZ_B_MAX:.3f})")
        if nbad == 0:
            picked = (r, s)
            break
    json.dump(log, open(os.path.join(vr.DATA, "stage_b.json"), "w"), indent=1, default=float)
    return picked


def main():
    if os.environ.get("EVAL"):
        s = json.load(open(os.environ["EVAL"]))
        s = s.get("design", s)
        e = evaluate("eval", s)
        for k, v in e.items():
            print(f"{k} = {v}")
        return 0
    cands = stage_a()
    picked = stage_b(cands)
    if picked is None:
        print("FAIL: size: no stage-A design passes every stage-B cell")
        return 1
    r, s = picked
    a = vr.area_um2(s)
    json.dump(dict(design=s, power_uw=r["power_uw"], area_um2=a[0], area_mos=a[1], area_poly=a[2], area_mim=a[3],
                   stage_a_k=r["k"], seed=SEED, n_a=N_A), open(os.path.join(vr.DATA, "sizing.json"), "w"), indent=1)
    hdr = ("* vrlo_ref -- VR_LO shunt regulator (0.5 V = 5/33 AVDD) for ramp_simple's reset switch.\n"
           "* GENERATED by size_vrlo.py; do not hand-edit. Ports: vrlo ib avdd avss.\n"
           f"* Bias: an IDEAL current IB = {s['IB']:g} uA into ib (one NMOS diode finger, XMBN).\n"
           f"* power {r['power_uw']:.1f} uW (typical, 27 C, 3.3 V, reset state, incl. IB) [M];"
           f" area {a[0]:.0f} um2 (MOS {a[1]:.0f}, poly {a[2]:.0f}, MIM {a[3]:.0f}) [P]\n"
           "* The simulators are the authority, not these lines.\n\n")
    os.makedirs(vr.WORK, exist_ok=True)
    open(os.path.join(vr.WORK, "vrlo_ref.spice"), "w").write(vr.netlist(s, header=hdr))
    print(f"PASS: size: selected stage-A point p{r['k']}: {r['power_uw']:.1f} uW, {a[0]:.0f} um2")
    print(f"size_power_uw = {r['power_uw']:.3f}")
    print(f"size_area_um2 = {a[0]:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
