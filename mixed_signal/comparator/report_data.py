"""Figures and the compact data record of the comparator search.

    ./container.sh 'python3 report_data.py'

Reads the search records in data/ (stage_a_feasible.csv, stage_a_fails_only_delay.csv,
stage_a_front_s*.csv, stage_b.csv, stage_b_caps.json, calibration.csv/json,
sizing.json) and the verification record results/verify.json; writes
assets/*.png and data/report_data.json (subsampled, for the report page)."""
import csv
import glob
import json
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

B = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(B, "data", *p)
SD_SHARED, SD_END = 0.52, 0.44


def rows(path):
    if not os.path.exists(path):
        return []
    out = []
    for r in csv.DictReader(open(path)):
        out.append({k: (v if k in ("tag", "why") else float(v)) for k, v in r.items()})
    return out


def footprint(w_um, nf, L):
    m = np.ceil(nf / 50.0)
    nfi = nf / m
    return m * w_um * (nfi * L + (nfi - 1) * SD_SHARED + 2 * SD_END)


def v2_reference():
    """../comparator_bkp/comparator_updt_v2 b0004 on the same footprint metric (its gate area was 149 um2)."""
    fp = (2 * footprint(2, 8, 0.28) + 4 * footprint(2, 1, 1.0) + 2 * footprint(2, 2, 1.0)
          + 2 * footprint(2, 31, 1.0))
    return dict(power_uw=64.1, area_um2=round(float(fp), 1), gate_area_um2=149.0, delay_dyn_ns=40.0,
                delay_vbl_ns=-2.5, sigma_lsb=1.277, load_ff=4.89)


def r3(x):
    return None if x is None or not np.isfinite(x) else float("%.4g" % x)


def main():
    feas = rows(D("stage_a_feasible.csv"))
    fdel = rows(D("stage_a_fails_only_delay.csv"))
    fronts = {}
    for p in sorted(glob.glob(D("stage_a_front_s*.csv"))):
        cap = re.search(r"_s([0-9.]+)\.csv$", p).group(1)
        fronts[cap] = rows(p)
    stb, cal = rows(D("stage_b.csv")), rows(D("calibration.csv"))
    caps = json.load(open(D("stage_b_caps.json")))
    calj = json.load(open(D("calibration.json")))
    sel = json.load(open(D("sizing.json")))
    ver = json.load(open(os.path.join(B, "results", "verify.json"))) if os.path.exists(
        os.path.join(B, "results", "verify.json")) else {}
    v2 = v2_reference()
    os.makedirs(os.path.join(B, "assets"), exist_ok=True)
    col = lambda rs, k, s=1.0: np.array([r[k] * s for r in rs])

    # ---- figure: power x area, fronts by sigma cap, ngspice-timed points, selection
    fig, ax = plt.subplots(figsize=(7.4, 4.9))
    ax.scatter(col(feas, "power", 1e6), col(feas, "area"), s=4, c="#c9c8c2", label="feasible, tables (all sigma)")
    shades = {"99": "#86b6ef", "2.5": "#3987e5", "2": "#1c5cab"}
    for cap, rs in fronts.items():
        ax.plot(col(rs, "power", 1e6), col(rs, "area"), "-", c=shades.get(cap, "#2a78d6"), lw=1.6,
                label=f"front, sigma <= {cap if cap != '99' else 'any'} LSB")
    ok = col(stb, "spice_pass") > 0
    ax.scatter(col(stb, "power", 1e6)[ok], col(stb, "area")[ok], s=50, facecolors="none", edgecolors="#1baf7a", lw=1.6,
               label="ngspice: meets every gate")
    ax.scatter(col(stb, "power", 1e6)[~ok], col(stb, "area")[~ok], s=44, marker="x", c="#e34948", label="ngspice: fails")
    ax.scatter([sel["power"] * 1e6], [sel["area"]], s=220, marker="*", c="#eb6834", edgecolors="k", lw=0.6,
               label=f"selected {sel['tag']}", zorder=5)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("power, worst static state [uW]"); ax.set_ylabel("device footprint [um^2]")
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=7.5)
    fig.tight_layout(); fig.savefig(os.path.join(B, "assets", "pareto_power_area.png"), dpi=140); plt.close(fig)

    # ---- figure: power vs sigma (the floor)
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.scatter(col(feas, "sigma_in_lsb"), col(feas, "power", 1e6), s=4, c="#c9c8c2", label="feasible, tables")
    ax.axvline(4 / 3, c="k", ls="--", lw=1); ax.text(4 / 3 + 0.02, ax.get_ylim()[1] * 0.9, "contract 4/3 LSB", fontsize=8)
    ax.scatter([sel["sigma_in_lsb"]], [sel["power"] * 1e6], s=220, marker="*", c="#eb6834", edgecolors="k", lw=0.6,
               label="selected (model)")
    if ver.get("mc_sigma_in_lsb"):
        ax.scatter([ver["mc_sigma_in_lsb"]], [sel["power"] * 1e6], s=60, marker="D", c="#4a3aa7",
                   label="selected, ngspice MC")
    ax.set_yscale("log"); ax.set_xlabel("sigma(Vos) at the ADC input [LSB]"); ax.set_ylabel("power [uW]")
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(B, "assets", "pareto_sigma_power.png"), dpi=140); plt.close(fig)

    # ---- figure: model vs ngspice
    fig, axs = plt.subplots(1, 3, figsize=(10.8, 3.6))
    for ax, (m, s_, lab, sc) in zip(axs, (("delay_c", "plat_delay_dyn", "delay [ns]", 1e9),
                                           ("fall_c", "plat_fall", "dout fall [ns]", 1e9),
                                           ("noise_v", "nz_nz_own_vin", "noise at pins [mV]", 1e3))):
        x, y = col(stb, m, sc), col(stb, s_, sc)
        ax.scatter(x, y, s=18, c="#2a78d6", label="stage B (front)")
        if m != "delay_c" or True:
            xc = col(cal, {"delay_c": "delay_dyn", "fall_c": "t_fall", "noise_v": "noise_v"}[m], sc)
            yc = col(cal, s_, sc)
            ax.scatter(xc, yc, s=12, marker="^", c="#b9b8b2", label="calibration set (raw model)")
        v = np.concatenate([x, y])
        lim = [0, np.nanmax(v[np.isfinite(v)]) * 1.15]
        ax.plot(lim, lim, "k--", lw=0.8); ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_xlabel("model " + lab); ax.set_ylabel("ngspice " + lab); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(B, "assets", "model_vs_ngspice.png"), dpi=140); plt.close(fig)

    # ---- compact record for the page
    rng = np.random.default_rng(1)

    def pick(rs, n):
        return [rs[i] for i in (rng.choice(len(rs), n, replace=False) if len(rs) > n else range(len(rs)))]

    pt = lambda r: dict(p=r3(r["power"] * 1e6), a=r3(r["area"]), s=r3(r["sigma_in_lsb"]),
                        d=r3(r["delay_c"] * 1e9), f=r3(r["fall_c"] * 1e9), n=r3(r["noise_v"] * 1e3))
    out = dict(
        cloud=[pt(r) for r in pick(feas, 2500)],
        fails_delay=[pt(r) for r in pick(fdel, 1500)],
        fronts={cap: [pt(r) for r in rs] for cap, rs in fronts.items()},
        stage_b=[dict(pt(r), tag=r["tag"], ok=int(r["spice_pass"]), why=r["why"], d_sp=r3(r["plat_delay_dyn"] * 1e9),
                      d_c4=r3(r["c4_delay_dyn"] * 1e9), f_sp=r3(r["plat_fall"] * 1e9),
                      n_sp=r3(r["nz_nz_own_vin"] * 1e3), vbl=r3(r["plat_delay_vbl"] * 1e9)) for r in stb],
        calibration=[dict(d=r3(r["delay_dyn"] * 1e9), d_sp=r3(r["plat_delay_dyn"] * 1e9), f=r3(r["t_fall"] * 1e9),
                          f_sp=r3(r["plat_fall"] * 1e9), n=r3(r["noise_v"] * 1e3), n_sp=r3(r["nz_nz_own_vin"] * 1e3),
                          l_ld=r["l_ld"]) for r in cal],
        cal=calj, caps=caps, selected={k: v for k, v in sel.items() if isinstance(v, (int, float, str))},
        verify=ver, v2=v2)
    # ---- PVT, Monte Carlo (both engines), xschem checks, transient noise, renders
    def table(name):
        p = D(name)
        if not os.path.exists(p):
            return []
        return [{k: (v if not re.match(r"^[-+0-9.eE]+$", v) else float(v)) for k, v in r.items()}
                for r in csv.DictReader(open(p))]
    out["pvt"] = table("pvt.csv")
    out["pvt_geom"] = table("pvt_geom.csv")
    out["mc_pvt"] = table("mc_pvt.csv")
    out["vmc"] = table("vmc.csv")
    out["xtb"] = table("xtb.csv")
    out["lin"] = table("offset_lin.csv")
    out["bias"] = table("bias_req.csv")
    tn = D("trannoise_summary.json")
    out["tn"] = json.load(open(tn)) if os.path.exists(tn) else {}
    tp = D("pvt_trannoise.txt")
    out["tn_pvt"] = dict((k, float(v)) for k, v in re.findall(r"^(\w+) = ([-+0-9.eE]+)", open(tp).read(), re.M)) \
        if os.path.exists(tp) else {}
    import base64
    imgs = {}
    for n in ("comparator_xschem", "tb_delay_xschem", "tb_trip_xschem", "tb_noise_xschem", "tb_mc_xschem"):
        p = os.path.join(B, "assets", n + ".png")
        if os.path.exists(p):
            from PIL import Image
            im = Image.open(p).convert("RGB")
            im.thumbnail((1600, 1000))
            import io
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            imgs[n] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    out["img"] = imgs
    json.dump(out, open(D("report_data.json"), "w"), separators=(",", ":"))
    # the report page: report/pareto_page.html with the record embedded
    page = open(os.path.join(B, "report", "pareto_page.html")).read()
    page = page.replace("/*__DATA__*/null", json.dumps(out, separators=(",", ":")))
    open(os.path.join(B, "assets", "comparator_pareto.html"), "w").write(page)
    print("INFO: wrote assets/comparator_pareto.html")
    print(f"report_cloud_points = {len(out['cloud'])}")
    print(f"v2_footprint_um2 = {v2['area_um2']}")
    print("PASS: figures and data/report_data.json written")


if __name__ == "__main__":
    main()
