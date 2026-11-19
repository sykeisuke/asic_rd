"""comparator characterization in ngspice, with the base comparator in its
base hookup run through the same code for a side-by-side record.

    ./container.sh 'PHASE=verify python3 -u bench.py'      typical: delay, polarity, noise, MC
    ./container.sh 'PHASE=lin python3 -u bench.py'         offset signal-independence (ADR 0015 gate)
    ./container.sh 'PHASE=bias python3 -u bench.py'        bias multiple needed for 12.5 ns (reported):
                                                           sw at all 45 PVT cells (data/bias_req.csv, the
                                                           requirement ../bias_gen checks), base at 4 cells

Variants (one netlist source each, all ideal bias into one tail finger):
  base      comparator_core.spice's `comparator_core`, plate on inn (the macro before 2026-11-17), dout falls
  sw        comparator.spice, plate on inp, reference on inn, dout falls (one more inverter)
  sw_noinv  `comparator_core` with the plate on inp and no added inverter: dout RISES (cost of the inverter)

Grid: ADR 0025, LSB = 6.701613 mV x VDD / 3.3, VR_LO = 7/55 VDD (both ratiometric to
AVDD: ic_source's reference is 5/33 AVDD, vrlo_ref's 7/55 AVDD). TCOUNT = 50 ns.
`base_old` re-runs the base comparator on the grid of its own record (LSB 5.859375 mV,
VR_LO 0.5 V) as a harness check against runs/comparator/20261106T033213Z.

Every phase prints name = value lines (and writes data/values_<phase>.txt);
check-comparator.awk turns them into PASS / FAIL lines. REPORT lines are
findings that are not judged.
"""
import csv
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
BASE_SRC = os.path.join(BLOCK, "comparator_core.spice")
SW_SRC = os.path.join(BLOCK, "comparator.spice")

VDD_NOM = 3.3
LSB_GRID = 6.701613e-3          # [D] ADR 0025 / ../ramp_simple grid, at AVDD = 3.3 V
OLD_LSB, OLD_VRLO = 1.5 / 256, 0.5   # the grid of the 10-device comparator's record
TCOUNT = 50e-9                  # [C] 20 MHz
C_LOAD = 10e-15                 # [U] dout load (latch + wire), ADR 0015
DELAY_MAX = 12.5e-9             # [U] 1/4 count from the static trip, ADR 0015
I_F = 1.93077e-6                # [M] data/sizing.json i_f: the ideal current per tail finger
I_MACRO = 3.25e-6               # [M] the comparator's bias in Analog_top (bias_gen output, spec s.4)
MACRO_SCALE = I_MACRO / I_F     # 1.683
REFP = "XREFP pbias pbias vddb vddb pfet_03v3 L=0.28u W=1u nf=1 m=1"   # one tail finger, as the 10-device comparator's benches
JOBS = int(os.environ.get("JOBS", "8"))
N_MC = int(os.environ.get("N_MC", "200"))
NOMINAL = ("typical", 27.0, 3.3)
LEVELS = (("c4", 4.5), ("plat", 40.5), ("mid", 128.5), ("top", 250.5))

VARIANTS = {
    "base": dict(sub="comparator_core", src=BASE_SRC, plate_pin="inn", edge="fall"),
    "sw": dict(sub="comparator", src=SW_SRC, plate_pin="inp", edge="fall"),
    "sw_noinv": dict(sub="comparator_core", src=BASE_SRC, plate_pin="inp", edge="rise"),
}


# ------------------------------------------------------------ netlists and decks
def subckt_text(src):
    t = open(src).read()
    return t[t.index(".subckt"):]


def add_geom(line):
    """The drain/source geometry the PDK's xschem MOS symbols write (as
    size.py's dev() with DUT_GEOM=1)."""
    w = float(re.search(r"\bW=([0-9.]+)u", line).group(1)) * 1e-6
    nf = int(re.search(r"\bnf=(\d+)", line).group(1))
    nd, ns = (nf + 1) // 2, (nf + 2) // 2
    return line + (f" ad={nd * w / nf * 0.18e-6:.4g} pd={2 * nd * (w / nf + 0.18e-6):.4g}"
                   f" as={ns * w / nf * 0.18e-6:.4g} ps={2 * ns * (w / nf + 0.18e-6):.4g}"
                   f" nrd={0.18e-6 / w:.4g} nrs={0.18e-6 / w:.4g}")


def write_dut(d, var, geom):
    text = subckt_text(VARIANTS[var]["src"])
    if geom:
        text = "\n".join(add_geom(l) if l.startswith("X") else l for l in text.splitlines()) + "\n"
    p = os.path.join(d, "dut.spice")
    open(p, "w").write(text)
    return p


def hook(var, plate, ref, out, inst):
    v = VARIANTS[var]
    a, b = (plate, ref) if v["plate_pin"] == "inp" else (ref, plate)
    return f"{inst} {a} {b} {out} clk vdd 0 nbias pbias {v['sub']}"


def grid(cell, which="new"):
    vdd = cell[2]
    if which == "old":
        return OLD_LSB, OLD_VRLO
    return LSB_GRID * vdd / VDD_NOM, 7.0 / 55.0 * vdd


def cell_subs(cell):
    corner, temp, vdd = cell
    vcm = vdd / 2.0
    return {"CORNER": corner, "MIMCORNER": corner if corner in ("ff", "ss") else "typical",
            "TEMP": "%g" % temp, "VDD": "%g" % vdd, "VCM": "%.6g" % vcm,
            "VLO50": "%.6g" % (vcm - 0.05), "VHI50": "%.6g" % (vcm + 0.05),
            "VLO70": "%.6g" % (vcm - 0.07), "VHI70": "%.6g" % (vcm + 0.07),
            "CLOAD": "%.4g" % C_LOAD, "REFP": REFP}


def run_deck(d, deck, subs, timeout, rndseed=None, out_name=None, raw=False):
    text = open(os.path.join(BLOCK, deck)).read()
    for k, v in subs.items():
        text = text.replace(f"@{k}@", v)
    left = re.findall(r"@[A-Z0-9_]+@", text)
    if left:
        raise RuntimeError(f"{deck}: unreplaced {sorted(set(left))}")
    name = out_name or deck
    open(os.path.join(d, name), "w").write(text)
    with open(os.path.join(d, ".spiceinit"), "w") as h:      # one OpenMP thread
        h.write("set num_threads=1\n" + (f"set rndseed={rndseed}\n" if rndseed is not None else ""))
    out = name.replace(".spice", ".out")
    try:
        subprocess.run(["ngspice", "-b", "-o", out, name], cwd=d, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout,
                       env=dict(os.environ, OMP_NUM_THREADS="1"))
        o = open(os.path.join(d, out), errors="replace").read()
    except (subprocess.TimeoutExpired, OSError):
        return ""
    if raw:
        return o
    if "RESULT_BEGIN" in o:
        return o.split("RESULT_BEGIN")[-1].split("RESULT_END")[0]
    err = [l.strip() for l in o.splitlines() if re.search(r"error|failed|not found", l, re.I)][:4]
    print(f"REPORT: deck {os.path.relpath(d, BLOCK)}/{name} gave no result: {' | '.join(err)[:400]}")
    return ""


def grab(blk, key):
    m = re.search(r"^\s*%s\s*=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)" % key, blk, re.M)
    return float(m.group(1)) if m else float("nan")


# ------------------------------------------------------------ one level
TRAN_KEYS = ("delay_vref", "delay_dyn", "edge", "ped_counts", "armed", "p_avg", "vplate_tr", "t_dout")


def static_trip(d, var, cell, scale, dut):
    c = cell_subs(cell)
    c.update(DUT=dut, IREF="%.6g" % (I_F * scale), EDGE=VARIANTS[var]["edge"],
             XDC=hook(var, "vdc", "vref", "doutdc", "XDC"))
    return grab(run_deck(d, "tb_dc.spice", c, 300), "vtrip")


def wave_analysis(d, var, cell, lsb, t_cs):
    """Polarity: dout crossings of VDD/2 after TR, their direction, plate
    direction, and alpha = dV(plate)/dV(drv) over the 200 ns before the plate
    crosses the static trip."""
    p = os.path.join(d, "wave.txt")
    if not os.path.exists(p):
        return {}
    a = np.loadtxt(p)
    t, vd, vp = a[:, 0], a[:, 1], a[:, 2]
    half = cell[2] / 2.0
    m = t >= 400e-9
    s = np.sign(vd[m] - half)
    s[s == 0] = 1
    ch = np.nonzero(np.diff(s))[0]
    dirs = [int(np.sign(s[i + 1] - s[i])) for i in ch]
    res = dict(ncross=float(len(ch)), dir=float(dirs[0]) if dirs else 0.0,
               ndir_wrong=float(sum(1 for x in dirs if x != (-1 if VARIANTS[var]["edge"] == "fall" else 1))),
               plate_rise=float(vp[-1] - np.interp(400e-9, t, vp)),
               plate_end=float(vp[-1]))
    if np.isfinite(t_cs):
        slope = lsb / TCOUNT
        v1, v0 = np.interp(t_cs, t, vp), np.interp(t_cs - 200e-9, t, vp)
        res["alpha_trip"] = float((v1 - v0) / (slope * 200e-9))
        res["plate_slope_mv_ns"] = float((v1 - v0) / 200e-9 * 1e3 * 1e-9)
    os.remove(p)   # keep work/ small
    return res


def level(job):
    """job: dict(var, cell, lt, k, scale, geom, grid, phase, wr, window, seed)"""
    var, cell, lt, k, scale = job["var"], job["cell"], job["lt"], job["k"], job["scale"]
    tag = "%s_%s_%g_%g_g%d_x%g_%s%s" % ((var,) + cell + (job["geom"], scale, lt, job.get("suffix", "")))
    d = os.path.join(BLOCK, "work", job["phase"], tag)
    os.makedirs(d, exist_ok=True)
    dut = write_dut(d, var, job["geom"])
    lsb, vrlo = grid(cell, job["grid"])
    res = {key: float("nan") for key in TRAN_KEYS}
    seed = job.get("seed")
    if seed is None:
        vtrip = static_trip(d, var, cell, scale, dut)
    else:
        vtrip = cell[2] / 2.0            # the lin phase measures from VREF, not from a trip
    res["vtrip_v"] = vtrip
    if not np.isfinite(vtrip):
        return job, res
    c = cell_subs(cell)
    vin = vrlo + k * lsb
    tstop = 400e-9 + (job["window"] if job.get("window") else k * TCOUNT + 400e-9)
    mism = ""
    if seed is not None:
        mism = ".param sw_stat_mismatch=%d\n.options seed=%d" % (1 if job["mc_on"] else 0, seed)
    c.update(DUT=dut, IREF="%.6g" % (I_F * scale), VIN="%.9g" % vin, VRLO="%.9g" % vrlo, LSB="%.9g" % lsb,
             TSTOP="%.6g" % tstop, VTRIP="%.6f" % vtrip, EDGE=VARIANTS[var]["edge"],
             LVLA="hi90" if VARIANTS[var]["edge"] == "fall" else "lo10",
             LVLB="lo10" if VARIANTS[var]["edge"] == "fall" else "hi90",
             XDUT=hook(var, "plate", "vref", "dout", "XDUT"), MISMATCH=mism,
             WRDATA="wrdata wave.txt v(dout) v(plate)" if job.get("wr") else "")
    blk = run_deck(d, "tb_tran.spice", c, 3600, rndseed=seed)
    for key in TRAN_KEYS:
        res[key] = grab(blk, key)
    if job.get("wr"):
        t_cs = res["t_dout"] - res["delay_dyn"] if np.isfinite(res["delay_dyn"]) else float("nan")
        res.update(wave_analysis(d, var, cell, lsb, t_cs))
    return job, res


def noise(var):
    d = os.path.join(BLOCK, "work", "verify", f"{var}_nz")
    os.makedirs(d, exist_ok=True)
    c = cell_subs(NOMINAL)
    vcm = c["VCM"]
    if VARIANTS[var]["plate_pin"] == "inn":       # base: dout falls as inn rises -> feed back to inn
        net = (f"VSIG inp 0 DC {vcm} AC 1\nCFB inn 0 1\nLFB dout inn 1T\n"
               f"XDUT inp inn dout clk vdd 0 nbias pbias {VARIANTS[var]['sub']}")
    else:                                          # sw: dout falls as inp rises -> feed back to inp
        net = (f"VSIG inn 0 DC {vcm} AC 1\nCFB inp 0 1\nLFB dout inp 1T\n"
               f"XDUT inp inn dout clk vdd 0 nbias pbias {VARIANTS[var]['sub']}")
    c.update(DUT=write_dut(d, var, 0), IREF="%.6g" % I_F, NZNET=net)
    blk = run_deck(d, "tb_nz.spice", c, 600)
    return {k: grab(blk, k) for k in ("ota_gain_vv", "ota_pole_hz", "nz_own_vin", "nz_lo_vin", "nz_ugb_vin", "op_i_vdd")}


def mc(var):
    d = os.path.join(BLOCK, "work", "verify", f"{var}_mc")
    os.makedirs(d, exist_ok=True)
    c = cell_subs(NOMINAL)
    c.update(DUT=write_dut(d, var, 0), IREF="%.6g" % I_F, NMC=str(N_MC), SEED="20261117",
             EDGE=VARIANTS[var]["edge"], XMC=hook(var, "vsw", "vrefx", "dout", "XDUT"))
    out = run_deck(d, "tb_mc.spice", c, 7200, raw=True)
    nom = re.findall(r"^vos_nom\s*=\s*([-+0-9.eE]+)", out, re.M)
    ks = np.array([float(x) for x in re.findall(r"^vos_k\s*=\s*([-+0-9.eE]+)", out, re.M)])
    return (float(nom[0]) if nom else float("nan")), ks


# ------------------------------------------------------------ output
class Out:
    def __init__(self, phase):
        self.path = os.path.join(BLOCK, "data", f"values_{phase}.txt")
        self.h = open(self.path, "w")

    def val(self, name, v):
        line = f"{name} = {v:.6g}"
        print(line)
        self.h.write(line + "\n")

    def rep(self, text):
        print("REPORT: " + text)

    def close(self):
        self.h.close()


def fns(x):
    return "%.2f" % (x * 1e9) if np.isfinite(x) else "nan"


# ------------------------------------------------------------ phases
def phase_verify():
    o = Out("verify")
    base_job = dict(cell=NOMINAL, k=0, scale=1.0, geom=0, grid="new", phase="verify", wr=True)
    jobs = []
    for var in ("base", "sw", "sw_noinv"):
        for lt, k in LEVELS:
            # the whole conversion: TR .. count 260, so the plate's over-voltage tail is in the polarity check
            jobs.append(dict(base_job, var=var, lt=lt, k=k, window=260 * TCOUNT))
        jobs.append(dict(base_job, var=var, lt="mac", k=40.5, scale=MACRO_SCALE, window=None))
    for lt, k in LEVELS[:2]:
        jobs.append(dict(base_job, var="base", lt="old" + lt, k=k, grid="old", wr=False, window=None))
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        f_lv = [ex.submit(level, j) for j in jobs]
        f_nz = {v: ex.submit(noise, v) for v in ("base", "sw")}
        f_mc = {v: ex.submit(mc, v) for v in ("base", "sw")}
        lv = [f.result() for f in f_lv]
        nz = {v: f.result() for v, f in f_nz.items()}
        mcr = {v: f.result() for v, f in f_mc.items()}
    r = {}
    for job, res in lv:
        name = job["var"] if job["grid"] == "new" else "base"
        r[(name, job["lt"])] = res
        for key, v in res.items():
            o.val(f"{name}_{job['lt']}_{key}", v)
    alpha = {}
    for var in ("base", "sw", "sw_noinv"):
        dd = np.array([r[(var, lt)]["delay_dyn"] for lt, _ in LEVELS])
        o.val(f"{var}_delay_max", np.nanmax(dd) if np.any(np.isfinite(dd)) else float("nan"))
        o.val(f"{var}_delay_min", np.nanmin(dd) if np.any(np.isfinite(dd)) else float("nan"))
        o.val(f"{var}_delay_spread", np.ptp(dd) if np.all(np.isfinite(dd)) else float("nan"))
        o.val(f"{var}_delay_n", float(np.sum(np.isfinite(dd))))
        ed = np.array([r[(var, lt)]["edge"] for lt, _ in LEVELS])
        o.val(f"{var}_edge_max", np.nanmax(ed) if np.any(np.isfinite(ed)) else float("nan"))
        pc = np.array([r[(var, lt)]["ped_counts"] for lt, _ in LEVELS])
        o.val(f"{var}_latency_ns_mean", float(np.nanmean(pc)) * TCOUNT * 1e9)
        pw = np.array([r[(var, lt)]["p_avg"] for lt, _ in LEVELS])
        o.val(f"{var}_p_avg_max", np.nanmax(pw))
        a = np.array([r[(var, lt)].get("alpha_trip", np.nan) for lt, _ in LEVELS])
        alpha[var] = float(np.nanmean(a))
        o.val(f"{var}_alpha_trip_mean", alpha[var])
        o.rep(f"{var}: delay from the static trip {fns(np.nanmin(dd))}..{fns(np.nanmax(dd))} ns over 4.5-250.5 LSB; "
              f"latency from the ideal ramp crossing {np.nanmean(pc) * TCOUNT * 1e9:.2f} ns; dout "
              f"{VARIANTS[var]['edge']} 10-90 % {fns(np.nanmax(ed))} ns; mean supply power TCONN..crossing "
              f"{np.nanmax(pw) * 1e6:.1f} uW; alpha at the trip {alpha[var]:.3f}; at the macro bias "
              f"({MACRO_SCALE:.3f}x) {fns(r[(var, 'mac')]['delay_dyn'])} ns")
    for var in ("base", "sw"):
        for key, v in nz[var].items():
            o.val(f"{var}_{key}", v)
        vnom, ks = mcr[var]
        ks = ks[np.isfinite(ks)]
        sig = float(np.std(ks, ddof=1)) if ks.size > 2 else float("nan")
        o.val(f"{var}_mc_samples", float(ks.size))
        o.val(f"{var}_mc_n", float(N_MC))
        o.val(f"{var}_mc_vos_nominal_v", vnom)
        o.val(f"{var}_mc_vos_mean_v", float(np.mean(ks)) if ks.size else float("nan"))
        o.val(f"{var}_mc_sigma_vos_v", sig)
        lsb = LSB_GRID
        o.val(f"{var}_mc_sigma_in_lsb", sig / alpha[var] / lsb if alpha[var] > 0 else float("nan"))
        o.rep(f"{var}: sigma(Vos) {sig * 1e3:.2f} mV at the pins ({ks.size} of {N_MC} samples) = "
              f"{sig / alpha[var] / lsb:.2f} LSB at the ADC input with the bench's alpha {alpha[var]:.3f}; "
              f"noise {nz[var]['nz_own_vin'] * 1e3:.3f} mV at the pins = {nz[var]['nz_own_vin'] / alpha[var] / lsb:.3f} LSB")
    o.close()


def phase_lin():
    o = Out("lin")
    cells = [(c.split(":")[0], float(c.split(":")[1]), float(c.split(":")[2]))
             for c in os.environ.get("LIN_CELLS", "typical:27:3.3 ss:85:3.0 ff:85:3.6").split()]
    n = int(os.environ.get("LIN_SAMPLES", "30"))
    variants = os.environ.get("LIN_VARIANTS", "sw base").split()
    seed0 = 20261007
    jobs = [dict(var=var, cell=cell, lt="l%g" % lvl, k=lvl, scale=1.0, geom=0, grid="new", phase="lin",
                 wr=False, window=28 * TCOUNT + lvl * TCOUNT, seed=seed0 + k, mc_on=k > 0, suffix="_k%03d" % k, kk=k)
            for var in variants for cell in cells for k in range(n + 1) for _, lvl in LEVELS]
    o.rep(f"offset signal-independence: {len(variants)} variants x {len(cells)} cells x ({n} samples + nominal) "
          f"x 4 levels = {len(jobs)} transients")
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        res = list(ex.map(level, jobs))
    rows = []
    for job, r in res:
        rows.append((job["var"], "%s_%g_%g" % job["cell"], job["kk"], job["k"], r["delay_vref"], r["armed"]))
    with open(os.path.join(BLOCK, "data", "offset_lin.csv"), "w") as h:
        h.write("variant,cell,sample,level_lsb,delay_vref_s,code_offset_lsb,armed\n")
        for v, c, k, lvl, dv, arm in rows:
            h.write("%s,%s,%d,%g,%.6g,%.6g,%.4g\n" % (v, c, k, lvl, dv, dv / TCOUNT, arm))
    lvls = [l for _, l in LEVELS]
    for var in variants:
        for cell in cells:
            tag = "%s_%g_%g" % cell
            m = {}
            for v, c, k, lvl, dv, arm in rows:
                if v == var and c == tag:
                    m.setdefault(k, {})[lvl] = dv / TCOUNT
            nom = m.get(0, {})
            nom_spread = (max(nom.values()) - min(nom.values())) if len(nom) == 4 and all(np.isfinite(list(nom.values()))) else float("nan")
            spreads, means, dead, unmeasured = [], [], 0, 0
            for k in range(1, n + 1):
                v = {l: m.get(k, {}).get(l, float("nan")) for l in lvls}
                upper = [v[l] for l in lvls[1:]]
                if not all(np.isfinite(upper)):
                    unmeasured += 1
                    continue
                if not np.isfinite(v[lvls[0]]):
                    dead += 1
                got = [x for x in v.values() if np.isfinite(x)]
                spreads.append(max(got) - min(got))
                means.append(float(np.mean(got)))
            spreads, means = np.array(spreads), np.array(means)
            t = ("%s_%s" % (var, tag)).replace(".", "p")
            o.val(f"lin_{t}_worst_level_spread_lsb", float(spreads.max()) if spreads.size else float("nan"))
            o.val(f"lin_{t}_mean_level_spread_lsb", float(spreads.mean()) if spreads.size else float("nan"))
            o.val(f"lin_{t}_nominal_level_spread_lsb", nom_spread)
            o.val(f"lin_{t}_code_offset_mean_lsb", float(means.mean()) if means.size else float("nan"))
            o.val(f"lin_{t}_code_offset_sigma_lsb", float(np.std(means, ddof=1)) if means.size > 2 else float("nan"))
            o.val(f"lin_{t}_code_offset_min_lsb", float(means.min()) if means.size else float("nan"))
            o.val(f"lin_{t}_code_offset_max_lsb", float(means.max()) if means.size else float("nan"))
            o.val(f"lin_{t}_unmeasured", float(unmeasured))
            o.val(f"lin_{t}_dead_zone", float(dead))
            o.val(f"lin_{t}_samples", float(spreads.size))
    o.close()


def phase_bias():
    o = Out("bias")
    # sw (the macro's comparator): every PVT cell, 5 corners x 0/27/85 C x 3.0/3.3/3.6 V, as the
    # 10-device comparator's bias_req.py did; base (the core, plate on inn): the four named cells
    named = [(c.split(":")[0], float(c.split(":")[1]), float(c.split(":")[2]))
             for c in os.environ.get("BIAS_CELLS", "typical:27:3.3 ss:85:3.0 ss:85:3.3 ss:85:3.6").split()]
    full = [(c, t, v) for c in "typical ss ff sf fs".split() for t in (0.0, 27.0, 85.0) for v in (3.0, 3.3, 3.6)]
    scales = [float(x) for x in os.environ.get("BIAS_SCALES", "0.8 1 1.2 1.4 1.6 1.683 1.8 2 2.5 3 4").split()]
    variants = os.environ.get("BIAS_VARIANTS", "base sw").split()
    vcells = {var: (full if var == "sw" and os.environ.get("BIAS_FULL", "1") == "1" else named) for var in variants}
    jobs = [dict(var=var, cell=cell, lt=lt, k=k, scale=sc, geom=g, grid="new", phase="bias", wr=False, window=None)
            for var in variants for g in (0, 1) for cell in vcells[var] for sc in scales for lt, k in LEVELS[:2]]
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        res = list(ex.map(level, jobs))
    got = {(j["var"], j["geom"], j["cell"], j["scale"], j["lt"]): r for j, r in res}
    rows = []
    for var in variants:
        for g in (0, 1):
            for cell in vcells[var]:
                d = {sc: max(got[(var, g, cell, sc, "c4")]["delay_dyn"], got[(var, g, cell, sc, "plat")]["delay_dyn"])
                     for sc in scales}
                req = float("nan")
                for sc in sorted(scales):
                    if all(np.isfinite(d[x]) and d[x] <= DELAY_MAX for x in scales if x >= sc):
                        req = sc
                        break
                tag = ("%s_%s_%g_%g_%s" % (var, cell[0], cell[1], cell[2], "geom" if g else "deck")).replace(".", "p")
                if cell in named:                  # per-cell values for the named cells only
                    o.val(f"bias_{tag}_req_scale", req)
                    o.val(f"bias_{tag}_delay_1x", d.get(1.0, float("nan")))
                    o.val(f"bias_{tag}_delay_macro", d.get(round(MACRO_SCALE, 3), float("nan")))
                rows.append(dict(variant=var, geom=g, cell="%s_%g_%g" % cell, req_scale=req,
                                 **{"delay_x%g" % sc: d[sc] for sc in scales}))
            rs = [x for x in rows if x["variant"] == var and x["geom"] == g]
            worst = max(rs, key=lambda x: x["req_scale"] if np.isfinite(x["req_scale"]) else 1e9)
            gt = "geom" if g else "deck"
            rq = np.array([x["req_scale"] for x in rs])
            o.val(f"bias_{var}_{gt}_cells", float(len(rs)))
            o.val(f"bias_{var}_{gt}_req_max", worst["req_scale"])
            o.val(f"bias_{var}_{gt}_unresolved", float(np.sum(~np.isfinite(rq))))
            o.val(f"bias_{var}_{gt}_over_macro", float(np.sum(~np.isfinite(rq) | (rq > MACRO_SCALE))))
            o.rep(f"{var} ({'drawn S/D geometry' if g else 'controlled deck'}), {len(rs)} PVT cells: delay <= 12.5 ns "
                  f"at 4.5 and 40.5 LSB needs at most {worst['req_scale']:g}x of {I_F * 1e6:.4g} uA per finger at "
                  f"{worst['cell']} (the macro's 3.25 uA = {MACRO_SCALE:.3f}x); "
                  + ", ".join(f"{x['cell']} {x['req_scale']:g}x" for x in rs if (x['cell'] in
                              ["%s_%g_%g" % c for c in named]) or not (x['req_scale'] <= 1.2)))
    keys = list(rows[0].keys())
    with open(os.path.join(BLOCK, "data", "bias_req.csv"), "w") as h:
        w = csv.writer(h)
        w.writerow(keys)
        for x in rows:
            w.writerow([x[k] if isinstance(x[k], str) else "%.6g" % x[k] for k in keys])
    o.close()


def main():
    ph = os.environ.get("PHASE", "verify")
    os.makedirs(os.path.join(BLOCK, "data"), exist_ok=True)
    {"verify": phase_verify, "lin": phase_lin, "bias": phase_bias}[ph]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
