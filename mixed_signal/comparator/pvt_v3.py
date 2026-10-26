"""PVT and Monte Carlo of the selected comparator in ngspice.

    ./container.sh 'python3 -u pvt_v3.py'          (run-pvt.sh records it)

GRID: process (typical ss ff sf fs) x temperature (0 27 85 C) x supply
(3.0 3.3 3.6 V) = 45 cells. inp = VBL = VDD/2 at every cell. The bias is the
IDEAL current of data/sizing.json into one diode-connected tail finger,
constant over PVT (user, 2026-10-06: the bias generator is redesigned
later); the reference device itself follows the corner, so pbias does.

Per cell (the v3 benches, templated by size_v3.cell_subs):
  tb_sel_dc + tb_sel  at 4.5 and 40.5 LSB: delay from the static trip, from
                      VBL, dout fall into 10 fF, arming, mean power
  tb_nz               noise at the pins, 1 kHz .. own band; OTA gain, pole;
                      supply current at the decision point
MC: tb_mc (ngspice, PDK mismatch, rndseed fixed) at MC_CELLS, MC_SAMPLES each.

GATES (DESIGN_RECIPE.md s.1) at every cell:
  delay  delay from the static trip <= 12.5 ns at both levels (REPORT at this ideal
         bias; gated on the bias generator, ADR 0015 / 0017)
  spread |c4 - plateau| <= 5 ns
  fall   dout 10-90 % <= 6 ns (REPORT: waived, ADR 0015)
  armed  dout high at TR
  noise  < 1.2 mV at the pins
  mc     (MC cells) >= 90 % of the samples cross; sigma(Vos) / alpha is a REPORT
         (ADR 0015 replaced the 4/3 LSB contract by the signal-independence gate)
Writes data/pvt.csv, data/mc_pvt.csv, assets/pvt_summary.png.
"""
import csv
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import size_v3 as S  # noqa: E402

CORNERS = os.environ.get("CORNERS", "typical ss ff sf fs").split()
TEMPS = [float(x) for x in os.environ.get("TEMPS", "0 27 85").split()]
VDDS = [float(x) for x in os.environ.get("VDDS", "3.0 3.3 3.6").split()]
MC_CELLS = os.environ.get(
    "MC_CELLS", "typical:27:3.3 ss:85:3.0 ff:0:3.6 sf:27:3.3 fs:27:3.3 ss:0:3.0 ff:85:3.6").split()
MC_SAMPLES = int(os.environ.get("MC_SAMPLES", 100))
PHASES = os.environ.get("PHASES", "bench mc plot").split()
LEVELS = (("c4", 4.5), ("plat", 40.5))
# DUT_GEOM=1: the DUT with the S/D geometry its schematic symbols draw (size_v3.dev); records get _geom
SUFFIX = "_geom" if os.environ.get("DUT_GEOM") == "1" else ""


def tag_of(cell):
    return "%s_%g_%g" % cell


def mc_cell(job):
    s, cell = job
    d = os.path.join(S.BLOCK, "work", "pvt_mc", tag_of(cell))
    os.makedirs(d, exist_ok=True)
    c = S.common_subs(s, d, 1.0, cell)
    c["NMC"] = str(MC_SAMPLES)
    text = open(os.path.join(S.BLOCK, "tb_mc.spice")).read()
    for k, v in c.items():
        text = text.replace(f"@{k}@", v)
    open(os.path.join(d, "tb_mc.spice"), "w").write(text)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    subprocess.run(["ngspice", "-b", "-o", "tb_mc.out", "tb_mc.spice"], cwd=d, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200,
                   env=dict(os.environ, OMP_NUM_THREADS="1"))
    out = open(os.path.join(d, "tb_mc.out"), errors="replace").read()
    num = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
    nom = re.findall(r"^vos_nom\s*=\s*" + num, out, re.M)
    ks = np.array([float(x) for x in re.findall(r"^vos_k\s*=\s*" + num, out, re.M)])
    return cell, (float(nom[0]) if nom else float("nan")), ks


def main():
    sel = json.load(open(os.path.join(S.BLOCK, "data", "sizing.json")))
    s = {k: sel[k] for k in S.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    alpha = float(sel["alpha"])
    ok_all = True

    def check(name, ok, msg):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}: {name}: {msg}")

    print(f"REPORT: PVT of {sel['tag']}{' with drawn S/D geometry' if SUFFIX else ''}: ideal bias {sel['i_f']*1e6:.4g} uA into one tail finger, constant over PVT; "
          f"alpha {alpha:.3f} (typical) for the ADC-input referral")
    cells = [(c, t, v) for c in CORNERS for t in TEMPS for v in VDDS]
    rows = []
    if "bench" in PHASES:
        jobs_l = [(tag_of(cell), s, lt, k, 1.0, cell, "pvt") for cell in cells for lt, k in LEVELS]
        jobs_n = [(tag_of(cell), s, cell, "pvt") for cell in cells]
        with ThreadPoolExecutor(max_workers=S.JOBS) as ex:
            fl = list(ex.map(S.spice_level, jobs_l))
            fn = list(ex.map(S.spice_noise, jobs_n))
        lv = {(t, lt): r for t, lt, r in fl}
        nz = {t: r for t, _, r in fn}
        for cell in cells:
            t = tag_of(cell)
            c4, pl, n = lv[(t, "c4")], lv[(t, "plat")], nz[t]
            rows.append(dict(tag=t, corner=cell[0], temp=cell[1], vdd=cell[2],
                             vtrip_off=pl["vtrip_v"] - cell[2] / 2,
                             delay_c4=c4["delay_dyn"], delay_plat=pl["delay_dyn"], delay_vbl=pl["delay_vbl"],
                             fall=max(c4["fall"], pl["fall"]), armed=min(c4["armed"], pl["armed"]) / cell[2],
                             p_avg=pl["p_avg"], noise=n["nz_own_vin"], gain=n["ota_gain_vv"], pole=n["ota_pole_hz"],
                             p_dec=n["op_i_vdd"] * cell[2]))
        keys = list(rows[0].keys())
        with open(os.path.join(S.BLOCK, "data", f"pvt{SUFFIX}.csv"), "w") as h:
            h.write(",".join(keys) + "\n")
            for r in rows:
                h.write(",".join(str(r[k]) if isinstance(r[k], str) else "%.6g" % r[k] for k in keys) + "\n")
        f = lambda k: np.array([r[k] for r in rows])
        dmax = np.fmax(f("delay_c4"), f("delay_plat"))
        nd = int(np.sum(np.isfinite(dmax) & (dmax <= S.DELAY_MAX)))
        w = int(np.nanargmax(np.where(np.isfinite(dmax), dmax, np.inf)))
        #- ADR 0015: at an IDEAL constant bias the 12.5 ns delay is reported; it is
        #- gated on the real bias generator (bias-gen, ADR 0017: <= 11.64 ns at 135 cells)
        print(f"REPORT: pvt_delay (ideal bias, not gated, ADR 0015): delay from the static trip <= 12.5 ns at "
              f"{nd}/{len(rows)} cells; range {np.nanmin(dmax)*1e9:.2f}..{np.nanmax(dmax)*1e9:.2f} ns, worst {rows[w]['tag']}")
        spread = np.abs(f("delay_c4") - f("delay_plat"))
        check("pvt_spread", np.all(spread <= S.LOWEND_SPREAD_MAX), f"level spread max {np.nanmax(spread)*1e9:.2f} ns (<= 5)")
        fall = f("fall")
        nf = int(np.sum(fall <= S.FALL_MAX))
        wf = int(np.nanargmax(fall))
        print(f"REPORT: pvt_fall (waived, ADR 0015): dout fall <= 6 ns at {nf}/{len(rows)} cells; max "
              f"{np.nanmax(fall)*1e9:.2f} ns at {rows[wf]['tag']}")
        check("pvt_armed", np.all(f("armed") >= 0.9), "dout high at TR at every cell")
        noise = f("noise")
        wn = int(np.nanargmax(noise))
        check("pvt_noise", np.all(noise < S.NOISE_MAX_V), f"noise at the pins max {np.nanmax(noise)*1e3:.3f} mV "
              f"at {rows[wn]['tag']} (< 1.2 mV)")
        print(f"pvt_delay_max_s = {np.nanmax(dmax):.6g}")
        print(f"pvt_delay_min_s = {np.nanmin(dmax):.6g}")
        print(f"pvt_fall_max_s = {np.nanmax(fall):.6g}")
        print(f"pvt_noise_max_v = {np.nanmax(noise):.6g}")
        print(f"pvt_noise_worst_cell = {rows[wn]['tag']}")
        print(f"pvt_power_dec_max_w = {np.nanmax(f('p_dec')):.6g}")
        print(f"pvt_power_avg_max_w = {np.nanmax(f('p_avg')):.6g}")
        print(f"pvt_trip_offset_range_v = {np.nanmin(f('vtrip_off')):.6g}..{np.nanmax(f('vtrip_off')):.6g}")
        print(f"pvt_delay_vbl_range_s = {np.nanmin(f('delay_vbl')):.6g}..{np.nanmax(f('delay_vbl')):.6g}")
        for r in sorted(rows, key=lambda r: -max(r["delay_c4"], r["delay_plat"]))[:5]:
            print(f"REPORT: slowest: {r['tag']} delay {max(r['delay_c4'], r['delay_plat'])*1e9:.2f} ns, fall "
                  f"{r['fall']*1e9:.2f} ns, gain {r['gain']:.1f}, noise {r['noise']*1e3:.3f} mV")
        for r in sorted(rows, key=lambda r: -r["fall"])[:3]:
            print(f"REPORT: slowest fall: {r['tag']} {r['fall']*1e9:.2f} ns")

    mrows = []
    if "mc" in PHASES:
        mcells = [(c.split(":")[0], float(c.split(":")[1]), float(c.split(":")[2])) for c in MC_CELLS]
        with ThreadPoolExecutor(max_workers=min(S.JOBS, len(mcells))) as ex:
            res = list(ex.map(mc_cell, [(s, c) for c in mcells]))
        for cell, nom, ks in res:
            ks = ks[np.isfinite(ks)]
            sig = float(np.std(ks, ddof=1)) if ks.size > 2 else float("nan")
            mrows.append(dict(tag=tag_of(cell), n=ks.size, vos_nom=nom, vos_mean=float(np.mean(ks)) if ks.size else np.nan,
                              sigma_v=sig, sigma_lsb=sig / alpha / S.LSB))
            print(f"REPORT: MC {tag_of(cell)}: {ks.size} samples, sigma(Vos) {sig*1e3:.2f} mV = {sig/alpha/S.LSB:.3f} LSB, "
                  f"mean {np.mean(ks)*1e3:+.2f} mV")
        with open(os.path.join(S.BLOCK, "data", f"mc_pvt{SUFFIX}.csv"), "w") as h:
            h.write("tag,n,vos_nom,vos_mean,sigma_v,sigma_lsb\n")
            for r in mrows:
                h.write("%s,%d,%.6g,%.6g,%.6g,%.6g\n" % (r["tag"], r["n"], r["vos_nom"], r["vos_mean"], r["sigma_v"], r["sigma_lsb"]))
        sl = np.array([r["sigma_lsb"] for r in mrows])
        print(f"mc_pvt_sigma_max_lsb = {np.nanmax(sl):.6g}")
        print(f"mc_pvt_sigma_min_lsb = {np.nanmin(sl):.6g}")
        check("pvt_mc", all(r["n"] >= 0.9 * MC_SAMPLES for r in mrows),
              f"Monte Carlo complete (>= 90 % of {MC_SAMPLES} samples crossed) at {len(mrows)} corner cells")
        print(f"REPORT: pvt_sigma (not gated, ADR 0015: the 4/3 LSB contract is replaced by the signal-independence "
              f"gate, PHASES=lin): sigma(Vos) at the ADC input {np.nanmin(sl):.2f}..{np.nanmax(sl):.2f} LSB over "
              f"{len(mrows)} corner cells")

    if "plot" in PHASES and rows:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
        cols = {"typical": "#2a78d6", "ss": "#eb6834", "ff": "#1baf7a", "sf": "#4a3aa7", "fs": "#e87ba4"}
        x = np.arange(len(rows))
        for ax, (k, sc, lab, gate) in zip(axs, (("delay_plat", 1e9, "delay from trip [ns]", 12.5),
                                                ("fall", 1e9, "dout fall [ns]", 6.0),
                                                ("noise", 1e3, "noise at pins [mV]", 1.2))):
            for i, r in enumerate(rows):
                v = max(r["delay_c4"], r["delay_plat"]) if k == "delay_plat" else r[k]
                ax.scatter(i, v * sc, c=cols[r["corner"]], s=16)
            ax.axhline(gate, c="k", ls="--", lw=1)
            ax.set_xticks(x[::9]); ax.set_xticklabels([rows[i]["corner"] for i in x[::9]])
            ax.set_ylabel(lab); ax.grid(alpha=0.3)
            ax.set_ylim(0, gate * 1.15)
        axs[0].set_title("45 cells: corner x {0,27,85} C x {3.0,3.3,3.6} V", fontsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(S.BLOCK, "assets", f"pvt_summary{SUFFIX}.png"), dpi=140)
        print("INFO: wrote assets/pvt_summary.png")

    print("PASS: pvt_v3 complete" if ok_all else "FAIL: at least one PVT check failed")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
