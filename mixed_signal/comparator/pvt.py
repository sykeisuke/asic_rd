"""PVT and Monte Carlo of comparator in ngspice (the replica of
comparator_bkp/comparator_10dev/pvt_v3.py for the swapped hookup: the plate on inp, VREF on inn,
dout falls through the added inverter), with the base comparator in its base
hookup through the same benches for a side-by-side record.

    ./container.sh 'PHASES="bench mc lin plot" python3 -u pvt.py'   (run-pvt.sh records it)

GRID: process (typical ss ff sf fs) x temperature (0 27 85 C) x supply
(3.0 3.3 3.6 V) = 45 cells, as the 10-device comparator's record. Bias: the IDEAL
1.931 uA into one diode-connected tail finger, constant over PVT (as
comparator_bkp/comparator_10dev/pvt_v3.py); the reference device follows the corner. Grid of
ADR 0025 (bench.py): LSB 6.70 mV x VDD / 3.3, VR_LO 7/55 VDD, 50 ns counts.

Per cell and variant (bench.py's tb_dc / tb_tran / tb_nz, filled for the cell):
  sw    4.5 / 40.5 / 128.5 / 250.5 LSB, each over the WHOLE conversion
        (TR .. count 260): delay from the static trip, from VREF, dout fall,
        arming, power, alpha at the trip, and the polarity of dout
  base  4.5 / 40.5 LSB (the two levels of the 10-device comparator's record)
  both  noise at the pins (1 kHz .. own band), OTA gain / pole, supply
        current at the decision point; the delay at the macro's 3.25 uA
        (1.683 x) at 4.5 / 40.5 LSB (reported)
MC: tb_mc (PDK mismatch) at MC_CELLS, MC_SAMPLES each, sw and base.
LIN: offset signal-independence (bench.py's lin method) at LIN_CELLS, sw.

GATES on sw (comparator_bkp/comparator_10dev/pvt_v3.py's, plus polarity and offset_lin):
  spread    max - min of the delay over the levels <= 5 ns at every cell
  armed     dout high at TR at every cell
  polarity  at every cell and level: dout crosses VDD/2 exactly once over
            TR .. count 260, falling, after the plate crossed the static trip;
            the plate rises
  noise     < 1.2 mV at the pins at every cell
  mc        >= 90 % of the samples cross at every MC cell
  lin       per mismatch sample the code offset moves <= 0.1 LSB over
            4.5 .. 250.5 LSB, every sample decided, at every LIN cell
REPORTED (as the 10-device comparator's record, ADR 0015): the delay from the static
trip at the ideal bias (gated on the bias generator), fall (waived),
sigma(Vos), power; plus the delay at the macro's 3.25 uA.
Writes data/pvt.csv (sw; the columns vacask.sh's tnpvt reads), data/pvt_base.csv,
data/pvt_mc.csv, data/pvt_offset_lin.csv, data/values_pvt.txt, assets/pvt_summary.png.
"""
import csv
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench as B  # noqa: E402

CORNERS = os.environ.get("CORNERS", "typical ss ff sf fs").split()
TEMPS = [float(x) for x in os.environ.get("TEMPS", "0 27 85").split()]
VDDS = [float(x) for x in os.environ.get("VDDS", "3.0 3.3 3.6").split()]
MC_CELLS = os.environ.get(
    "MC_CELLS", "typical:27:3.3 ss:85:3.0 ff:0:3.6 sf:27:3.3 fs:27:3.3 ss:0:3.0 ff:85:3.6").split()
MC_SAMPLES = int(os.environ.get("MC_SAMPLES", 100))
MC_VARIANTS = os.environ.get("MC_VARIANTS", "sw base").split()
LIN_CELLS = os.environ.get("LIN_CELLS", " ".join(MC_CELLS)).split()
LIN_SAMPLES = int(os.environ.get("LIN_SAMPLES", 30))
PHASES = os.environ.get("PHASES", "bench mc lin plot").split()
JOBS = B.JOBS
SW_LEVELS = B.LEVELS                 # c4 plat mid top
BASE_LEVELS = B.LEVELS[:2]           # c4 plat, as comparator_bkp/comparator_10dev/pvt_v3.py
DATA = os.path.join(B.BLOCK, "data")


def tag_of(cell):
    return "%s_%g_%g" % cell


def parse_cell(c):
    a = c.split(":")
    return (a[0], float(a[1]), float(a[2]))


class Out:
    def __init__(self):
        self.h = open(os.path.join(DATA, "values_pvt.txt"), "w")
        self.ok = True

    def val(self, name, v, fmt="%.6g"):
        line = ("%s = " + fmt) % (name, v)
        print(line)
        self.h.write(line + "\n")

    def check(self, name, good, msg):
        self.ok &= bool(good)
        print(f"{'PASS' if good else 'FAIL'}: {name}: {msg}")

    def rep(self, text):
        print("REPORT: " + text)


# ------------------------------------------------------------ cell benches
def noise_cell(job):
    var, cell = job
    d = os.path.join(B.BLOCK, "work", "pvt", f"{var}_{tag_of(cell)}_nz")
    os.makedirs(d, exist_ok=True)
    c = B.cell_subs(cell)
    vcm = c["VCM"]
    sub = B.VARIANTS[var]["sub"]
    if B.VARIANTS[var]["plate_pin"] == "inn":       # base: dout falls as inn rises -> feedback to inn
        net = (f"VSIG inp 0 DC {vcm} AC 1\nCFB inn 0 1\nLFB dout inn 1T\n"
               f"XDUT inp inn dout clk vdd 0 nbias pbias {sub}")
    else:                                            # sw: dout falls as inp rises -> feedback to inp
        net = (f"VSIG inn 0 DC {vcm} AC 1\nCFB inp 0 1\nLFB dout inp 1T\n"
               f"XDUT inp inn dout clk vdd 0 nbias pbias {sub}")
    c.update(DUT=B.write_dut(d, var, 0), IREF="%.6g" % B.I_F, NZNET=net)
    blk = B.run_deck(d, "tb_nz.spice", c, 900)
    return job, {k: B.grab(blk, k) for k in ("ota_gain_vv", "ota_pole_hz", "nz_own_vin", "nz_lo_vin", "op_i_vdd")}


def mc_cell(job):
    var, cell = job
    d = os.path.join(B.BLOCK, "work", "pvt_mc", f"{var}_{tag_of(cell)}")
    os.makedirs(d, exist_ok=True)
    c = B.cell_subs(cell)
    c.update(DUT=B.write_dut(d, var, 0), IREF="%.6g" % B.I_F, NMC=str(MC_SAMPLES), SEED="20261117",
             EDGE=B.VARIANTS[var]["edge"], XMC=B.hook(var, "vsw", "vrefx", "dout", "XDUT"))
    out = B.run_deck(d, "tb_mc.spice", c, 7200, raw=True)
    nom = re.findall(r"^vos_nom\s*=\s*([-+0-9.eE]+)", out, re.M)
    ks = np.array([float(x) for x in re.findall(r"^vos_k\s*=\s*([-+0-9.eE]+)", out, re.M)])
    return job, (float(nom[0]) if nom else float("nan")), ks


def fmt_ns(x):
    return "%.2f" % (x * 1e9) if np.isfinite(x) else "nan"


def nanmax(a):
    a = np.asarray(a, float)
    return float(np.nanmax(a)) if np.any(np.isfinite(a)) else float("nan")


def nanmin(a):
    a = np.asarray(a, float)
    return float(np.nanmin(a)) if np.any(np.isfinite(a)) else float("nan")


def write_csv(path, rows):
    keys = list(rows[0].keys())
    with open(path, "w") as h:
        h.write(",".join(keys) + "\n")
        for r in rows:
            h.write(",".join(r[k] if isinstance(r[k], str) else "%.6g" % r[k] for k in keys) + "\n")


def read_csv(path):
    with open(path) as h:
        rows = list(csv.DictReader(h))
    for r in rows:
        for k, v in r.items():
            if k not in ("tag", "corner", "verdict", "fail_why"):
                r[k] = float(v)
    return rows


# ------------------------------------------------------------ phases
def phase_bench(o, cells):
    base_job = dict(k=0, scale=1.0, geom=0, grid="new", phase="pvt")
    jobs = []
    for cell in cells:
        for lt, k in SW_LEVELS:
            jobs.append(dict(base_job, var="sw", cell=cell, lt=lt, k=k, window=260 * B.TCOUNT, wr=True))
        for lt, k in BASE_LEVELS:
            jobs.append(dict(base_job, var="base", cell=cell, lt=lt, k=k, window=None, wr=True))
        for var in ("sw", "base"):
            for lt, k in BASE_LEVELS:
                jobs.append(dict(base_job, var=var, cell=cell, lt="mac" + lt, k=k, scale=B.MACRO_SCALE,
                                 window=None, wr=False))
    o.rep(f"PVT bench: {len(cells)} cells, {len(jobs)} transients + {2 * len(cells)} noise benches, JOBS={JOBS}; "
          f"ideal bias {B.I_F * 1e6:.4g} uA into one tail finger, constant over PVT; ADR 0025 grid")
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        f_lv = [ex.submit(B.level, j) for j in jobs]
        f_nz = [ex.submit(noise_cell, (v, c)) for c in cells for v in ("sw", "base")]
        lv = [f.result() for f in f_lv]
        nz = {j: r for j, r in (f.result() for f in f_nz)}
    r = {(j["var"], j["cell"], j["lt"]): res for j, res in lv}

    rows = {"sw": [], "base": []}
    for var, levels in (("sw", SW_LEVELS), ("base", BASE_LEVELS)):
        for cell in cells:
            t = tag_of(cell)
            g = lambda lt, key: r[(var, cell, lt)].get(key, float("nan"))
            dd = [g(lt, "delay_dyn") for lt, _ in levels]
            n = nz[(var, cell)]
            row = dict(tag=t, corner=cell[0], temp=cell[1], vdd=cell[2],
                       vtrip_off=g("plat", "vtrip_v") - cell[2] / 2,
                       delay_c4=g("c4", "delay_dyn"), delay_plat=g("plat", "delay_dyn"),
                       delay_max=nanmax(dd), delay_spread=(max(dd) - min(dd)) if np.all(np.isfinite(dd)) else float("nan"),
                       delay_vref=g("plat", "delay_vref"),
                       latency_ns=float(np.nanmean([g(lt, "ped_counts") for lt, _ in levels])) * B.TCOUNT * 1e9,
                       fall=nanmax([g(lt, "edge") for lt, _ in levels]),
                       armed=nanmin([g(lt, "armed") for lt, _ in levels]) / cell[2],
                       p_avg=nanmax([g(lt, "p_avg") for lt, _ in levels]),
                       alpha_trip=float(np.nanmean([g(lt, "alpha_trip") for lt, _ in levels])),
                       noise=n["nz_own_vin"], noise_lo=n["nz_lo_vin"], gain=n["ota_gain_vv"], pole=n["ota_pole_hz"],
                       p_dec=n["op_i_vdd"] * cell[2],
                       delay_macro=max(g("macc4", "delay_dyn"), g("macplat", "delay_dyn")))
            if var == "sw":
                row["delay_mid"] = g("mid", "delay_dyn")
                row["delay_top"] = g("top", "delay_dyn")
                pol, why = True, []
                for lt, _ in levels:
                    nc, dr, d1, pr = g(lt, "ncross"), g(lt, "dir"), g(lt, "delay_dyn"), g(lt, "plate_rise")
                    ok = nc == 1 and dr == -1 and np.isfinite(d1) and d1 > 0 and pr > 0
                    pol &= bool(ok)
                    if not ok:
                        why.append(f"{lt}: {nc:g} crossings dir {dr:g} delay {fmt_ns(d1)} ns plate {pr:+.2f} V")
                row["ncross_max"] = nanmax([g(lt, "ncross") for lt, _ in levels])
                row["plate_rise_min"] = nanmin([g(lt, "plate_rise") for lt, _ in levels])
                row["plate_end_max"] = nanmax([g(lt, "plate_end") for lt, _ in levels])
                row["polarity"] = 1.0 if pol else 0.0
                fails = [] if pol else ["polarity (" + "; ".join(why) + ")"]
                if not (np.isfinite(row["delay_spread"]) and row["delay_spread"] <= 5e-9):
                    fails.append("spread")
                if not row["armed"] >= 0.9:
                    fails.append("armed")
                if not row["noise"] < 1.2e-3:
                    fails.append("noise")
                row["verdict"] = "PASS" if not fails else "FAIL"
                row["fail_why"] = "|".join(fails).replace(",", ";")
                row["delay_le_12p5"] = 1.0 if row["delay_max"] <= B.DELAY_MAX else 0.0
            rows[var].append(row)
    write_csv(os.path.join(DATA, "pvt.csv"), rows["sw"])
    write_csv(os.path.join(DATA, "pvt_base.csv"), rows["base"])

    # ---- gates and reports (sw), comparator_bkp/comparator_10dev/pvt_v3.py's lines + polarity
    sw, bs = rows["sw"], rows["base"]
    f = lambda rs, k: np.array([x[k] for x in rs], float)
    n = len(sw)
    for var, rs in (("sw", sw), ("base", bs)):
        p = "pvt_" if var == "sw" else "pvt_base_"
        dm = f(rs, "delay_max")
        w = int(np.nanargmax(np.where(np.isfinite(dm), dm, np.inf)))
        o.val(p + "delay_max_s", nanmax(dm))
        o.val(p + "delay_min_s", nanmin(dm))
        o.val(p + "delay_le_12p5_cells", float(np.sum(np.isfinite(dm) & (dm <= B.DELAY_MAX))))
        o.val(p + "delay_c4plat_max_s", nanmax(np.fmax(f(rs, "delay_c4"), f(rs, "delay_plat"))))
        o.val(p + "delay_macro_max_s", nanmax(f(rs, "delay_macro")))
        o.val(p + "delay_macro_min_s", nanmin(f(rs, "delay_macro")))
        o.val(p + "spread_max_s", nanmax(f(rs, "delay_spread")))
        o.val(p + "fall_max_s", nanmax(f(rs, "fall")))
        o.val(p + "fall_le_6_cells", float(np.sum(f(rs, "fall") <= 6e-9)))
        o.val(p + "noise_max_v", nanmax(f(rs, "noise")))
        o.val(p + "power_dec_max_w", nanmax(f(rs, "p_dec")))
        o.val(p + "power_avg_max_w", nanmax(f(rs, "p_avg")))
        o.val(p + "latency_max_ns", nanmax(f(rs, "latency_ns")))
        o.val(p + "latency_min_ns", nanmin(f(rs, "latency_ns")))
        o.val(p + "alpha_trip_min", nanmin(f(rs, "alpha_trip")))
        o.val(p + "alpha_trip_max", nanmax(f(rs, "alpha_trip")))
        o.val(p + "trip_offset_min_v", nanmin(f(rs, "vtrip_off")))
        o.val(p + "trip_offset_max_v", nanmax(f(rs, "vtrip_off")))
        o.rep(f"{var}: delay from the static trip at the ideal bias (not gated, ADR 0015) <= 12.5 ns at "
              f"{int(np.sum(np.isfinite(dm) & (dm <= B.DELAY_MAX)))}/{n} cells; range {fmt_ns(nanmin(dm))}.."
              f"{fmt_ns(nanmax(dm))} ns, worst {rs[w]['tag']}; at the macro's 3.25 uA {fmt_ns(nanmin(f(rs, 'delay_macro')))}.."
              f"{fmt_ns(nanmax(f(rs, 'delay_macro')))} ns")
        fl = f(rs, "fall")
        wf = int(np.nanargmax(fl))
        o.rep(f"{var}: dout fall (waived, ADR 0015) <= 6 ns at {int(np.sum(fl <= 6e-9))}/{n} cells; max "
              f"{fmt_ns(nanmax(fl))} ns at {rs[wf]['tag']}")
        o.rep(f"{var}: latency from the ideal ramp crossing {nanmin(f(rs, 'latency_ns')):.2f}..{nanmax(f(rs, 'latency_ns')):.2f} ns; "
              f"alpha at the trip {nanmin(f(rs, 'alpha_trip')):.3f}..{nanmax(f(rs, 'alpha_trip')):.3f}; power TCONN..crossing "
              f"max {nanmax(f(rs, 'p_avg')) * 1e6:.1f} uW, at the decision point max {nanmax(f(rs, 'p_dec')) * 1e6:.1f} uW")
    print(f"pvt_noise_worst_cell = {sw[int(np.nanargmax(f(sw, 'noise')))]['tag']}")
    sp = f(sw, "delay_spread")
    o.check("pvt_spread", np.all(np.isfinite(sp) & (sp <= 5e-9)),
            f"sw level spread (4.5 / 40.5 / 128.5 / 250.5 LSB) max {nanmax(sp) * 1e9:.3f} ns (<= 5)")
    o.check("pvt_armed", np.all(f(sw, "armed") >= 0.9), f"sw dout high at TR at every cell (min {nanmin(f(sw, 'armed')):.3f} VDD)")
    npol = int(np.sum(f(sw, "polarity") == 1))
    bad = [x["tag"] for x in sw if x["polarity"] != 1]
    o.val("pvt_polarity_cells", float(npol))
    o.check("pvt_polarity", npol == n,
            f"sw dout falls exactly once, after the plate crosses the trip, over TR..count 260 at all 4 levels: "
            f"{npol}/{n} cells; max crossings {nanmax(f(sw, 'ncross_max')):g}; plate rise min "
            f"{nanmin(f(sw, 'plate_rise_min')):+.2f} V, plate max {nanmax(f(sw, 'plate_end_max')):.3f} V"
            + (f"; failing {' '.join(bad)}" if bad else ""))
    nzv = f(sw, "noise")
    wn = int(np.nanargmax(nzv))
    o.check("pvt_noise", np.all(nzv < 1.2e-3), f"sw noise at the pins max {nanmax(nzv) * 1e3:.3f} mV at {sw[wn]['tag']} (< 1.2 mV); "
            f"base max {nanmax(f(bs, 'noise')) * 1e3:.3f} mV")
    for x in sorted(sw, key=lambda x: -x["delay_max"])[:5]:
        b = next(y for y in bs if y["tag"] == x["tag"])
        o.rep(f"slowest sw: {x['tag']} delay {fmt_ns(x['delay_max'])} ns (base {fmt_ns(b['delay_max'])}), at 3.25 uA "
              f"{fmt_ns(x['delay_macro'])} ns, fall {fmt_ns(x['fall'])} ns, gain {x['gain']:.1f}, noise {x['noise'] * 1e3:.3f} mV")
    npass = sum(1 for x in sw if x["verdict"] == "PASS")
    o.val("pvt_cells_pass", float(npass))
    o.val("pvt_cells", float(n))
    o.rep(f"per-cell verdict (spread, armed, polarity, noise): {npass}/{n} cells pass"
          + ("; " + "; ".join(f"{x['tag']}: {x['fail_why']}" for x in sw if x["verdict"] != "PASS") if npass < n else ""))
    for corner in CORNERS:
        rs = [x for x in sw if x["corner"] == corner]
        o.rep(f"corner {corner}: {sum(1 for x in rs if x['verdict'] == 'PASS')}/{len(rs)} cells pass; delay at ideal bias "
              f"{fmt_ns(nanmin(f(rs, 'delay_max')))}..{fmt_ns(nanmax(f(rs, 'delay_max')))} ns "
              f"({int(np.sum(f(rs, 'delay_le_12p5')))}/{len(rs)} <= 12.5), at 3.25 uA <= {fmt_ns(nanmax(f(rs, 'delay_macro')))} ns, "
              f"fall <= {fmt_ns(nanmax(f(rs, 'fall')))} ns, noise <= {nanmax(f(rs, 'noise')) * 1e3:.3f} mV")
    return sw, bs


def phase_mc(o, alpha):
    cells = [parse_cell(c) for c in MC_CELLS]
    jobs = [(v, c) for v in MC_VARIANTS for c in cells]
    with ThreadPoolExecutor(max_workers=min(JOBS, len(jobs))) as ex:
        res = list(ex.map(mc_cell, jobs))
    rows = []
    for (var, cell), nom, ks in res:
        ks = ks[np.isfinite(ks)]
        sig = float(np.std(ks, ddof=1)) if ks.size > 2 else float("nan")
        a = alpha.get((var, tag_of(cell)), float("nan"))
        lsb = B.grid(cell)[0]
        rows.append(dict(variant=var, tag=tag_of(cell), n=float(ks.size), vos_nom=nom,
                         vos_mean=float(np.mean(ks)) if ks.size else float("nan"), sigma_v=sig,
                         alpha_trip=a, sigma_lsb=sig / a / lsb if a > 0 else float("nan")))
        o.rep(f"MC {var} {tag_of(cell)}: {ks.size}/{MC_SAMPLES} samples, sigma(Vos) {sig * 1e3:.2f} mV at the pins = "
              f"{sig / a / lsb:.3f} LSB at the ADC input (alpha {a:.3f}, LSB {lsb * 1e3:.3f} mV), mean {np.mean(ks) * 1e3:+.2f} mV")
    write_csv(os.path.join(DATA, "pvt_mc.csv"), rows)
    for var in MC_VARIANTS:
        rs = [x for x in rows if x["variant"] == var]
        p = "mc_pvt_" if var == "sw" else "mc_pvt_base_"
        sv = np.array([x["sigma_v"] for x in rs])
        sl = np.array([x["sigma_lsb"] for x in rs])
        o.val(p + "sigma_max_v", nanmax(sv))
        o.val(p + "sigma_min_v", nanmin(sv))
        o.val(p + "sigma_max_lsb", nanmax(sl))
        o.val(p + "sigma_min_lsb", nanmin(sl))
        o.rep(f"{var} pvt_sigma (not gated, ADR 0015): sigma(Vos) {nanmin(sv) * 1e3:.2f}..{nanmax(sv) * 1e3:.2f} mV at the pins = "
              f"{nanmin(sl):.2f}..{nanmax(sl):.2f} LSB at the ADC input over {len(rs)} corner cells")
    sw = [x for x in rows if x["variant"] == "sw"]
    o.check("pvt_mc", len(sw) > 0 and all(x["n"] >= 0.9 * MC_SAMPLES for x in sw),
            f"sw Monte Carlo complete (>= 90 % of {MC_SAMPLES} samples crossed) at {len(sw)} corner cells "
            f"(min {min((x['n'] for x in sw), default=0):g})")


def phase_lin(o):
    cells = [parse_cell(c) for c in LIN_CELLS]
    n = LIN_SAMPLES
    seed0 = 20261007
    lvls = [l for _, l in B.LEVELS]
    jobs = [dict(var="sw", cell=cell, lt="l%g" % lvl, k=lvl, scale=1.0, geom=0, grid="new", phase="pvt_lin",
                 wr=False, window=28 * B.TCOUNT + lvl * B.TCOUNT, seed=seed0 + k, mc_on=k > 0,
                 suffix="_k%03d" % k, kk=k)
            for cell in cells for k in range(n + 1) for lvl in lvls]
    o.rep(f"offset signal-independence (sw): {len(cells)} cells x ({n} samples + nominal) x 4 levels = {len(jobs)} transients")
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        res = list(ex.map(B.level, jobs))
    with open(os.path.join(DATA, "pvt_offset_lin.csv"), "w") as h:
        h.write("variant,cell,sample,level_lsb,delay_vref_s,code_offset_lsb,armed\n")
        for j, r in res:
            h.write("sw,%s,%d,%g,%.6g,%.6g,%.4g\n" % (tag_of(j["cell"]), j["kk"], j["k"], r["delay_vref"],
                                                     r["delay_vref"] / B.TCOUNT, r["armed"]))
    worst_all, good_all, sig_all = 0.0, True, []
    for cell in cells:
        m = {}
        for j, r in res:
            if j["cell"] == cell:
                m.setdefault(j["kk"], {})[j["k"]] = r["delay_vref"] / B.TCOUNT
        spreads, means, und = [], [], 0
        for k in range(1, n + 1):
            v = [m.get(k, {}).get(l, float("nan")) for l in lvls]
            if not all(np.isfinite(v)):
                und += 1
                continue
            spreads.append(max(v) - min(v))
            means.append(float(np.mean(v)))
        spreads, means = np.array(spreads), np.array(means)
        t = tag_of(cell).replace(".", "p")
        worst = float(spreads.max()) if spreads.size else float("nan")
        sg = float(np.std(means, ddof=1)) if means.size > 2 else float("nan")
        o.val(f"lin_{t}_worst_level_spread_lsb", worst)
        o.val(f"lin_{t}_code_offset_sigma_lsb", sg)
        o.val(f"lin_{t}_undecided", float(und))
        good = np.isfinite(worst) and worst <= 0.1 and und == 0
        good_all &= bool(good)
        if np.isfinite(worst):
            worst_all = max(worst_all, worst)
        sig_all.append(sg)
        o.rep(f"offset_lin sw {tag_of(cell)}: worst level dependence {worst:.4f} LSB over {spreads.size} samples, "
              f"{und} undecided; code offset mean {np.mean(means):+.2f} sigma {sg:.2f} LSB")
    o.val("lin_worst_level_spread_lsb", worst_all)
    o.check("pvt_offset_lin", good_all,
            f"sw code offset moves at most {worst_all:.4f} LSB over 4.5..250.5 LSB at {len(cells)} cells, "
            f"{n} samples each, every sample decided (<= 0.1 LSB); in-cell code-offset sigma "
            f"{nanmin(sig_all):.2f}..{nanmax(sig_all):.2f} LSB")


def phase_plot(sw, bs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
    x = np.arange(len(sw))
    for ax, (k, sc, lab, gate) in zip(axs, (("delay_max", 1e9, "delay from trip [ns]", 12.5),
                                           ("fall", 1e9, "dout fall [ns]", 6.0),
                                           ("noise", 1e3, "noise at pins [mV]", 1.2))):
        ax.scatter(x, [r[k] * sc for r in sw], c="#2a78d6", s=16, label="comparator")
        ax.scatter(x, [r[k] * sc for r in bs], c="#eb6834", s=12, marker="x", label="base")
        if k == "delay_max":
            ax.scatter(x, [r["delay_macro"] * sc for r in sw], c="#1baf7a", s=12, marker="^", label="sw at 3.25 uA")
        ax.axhline(gate, c="k", ls="--", lw=1)
        ax.set_xticks(x[::9])
        ax.set_xticklabels([sw[i]["corner"] for i in x[::9]])
        ax.set_ylabel(lab)
        ax.grid(alpha=0.3)
        top = max(gate, np.nanmax([r[k] * sc for r in sw + bs]))
        ax.set_ylim(0, top * 1.15)
    axs[0].legend(fontsize=7, loc="lower right")
    axs[0].set_title("45 cells: corner x {0,27,85} C x {3.0,3.3,3.6} V", fontsize=9)
    fig.tight_layout()
    os.makedirs(os.path.join(B.BLOCK, "assets"), exist_ok=True)
    fig.savefig(os.path.join(B.BLOCK, "assets", "pvt_summary.png"), dpi=140)
    print("INFO: wrote assets/pvt_summary.png")


def main():
    os.makedirs(DATA, exist_ok=True)
    o = Out()
    cells = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]
    sw = bs = None
    if "bench" in PHASES:
        sw, bs = phase_bench(o, cells)
    elif os.path.exists(os.path.join(DATA, "pvt.csv")):
        sw, bs = read_csv(os.path.join(DATA, "pvt.csv")), read_csv(os.path.join(DATA, "pvt_base.csv"))
    if "mc" in PHASES:
        alpha = {}
        for var, rs in (("sw", sw or []), ("base", bs or [])):
            for x in rs:
                alpha[(var, x["tag"])] = x["alpha_trip"]
        phase_mc(o, alpha)
    if "lin" in PHASES:
        phase_lin(o)
    if "plot" in PHASES and sw:
        phase_plot(sw, bs)
    o.h.close()
    print("PASS: pvt complete" if o.ok else "FAIL: at least one PVT check failed")
    return 0 if o.ok else 1


if __name__ == "__main__":
    sys.exit(main())
