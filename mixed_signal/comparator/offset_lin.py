"""Is the comparator's offset signal-independent? Per mismatched cell, in the
cell's charge path (ngspice).

    ./container.sh 'python3 -u offset_lin.py'          (run-pvt.sh phase `lin`)

The user accepted the 1.8-2.2 LSB offset spread on 2026-10-07 on the
condition that it is signal-independent: a constant per cell that the
pedestal calibration removes. Two things could make it signal-dependent:
  - the bench sees the ramp through the top plate, and the OTA's lag, its Cgd
    charge on the floating plate and its recovery all depend on how long
    and how far the input has been below VBL, which grows with the level
  - mismatch could change the slope of those effects from cell to cell.
So for every Monte Carlo sample the SAME mismatch draw (one rndseed, one
netlist, so one draw order) is run at four levels, 4.5 / 40.5 / 128.5 /
250.5 LSB, in tb_sel.spice (the 54.52 fF MIM, ideal S2, the ramp at the
8-bit slope, dout into 10 fF). The code offset of the sample at a level is
delay_vbl / TCOUNT in counts = LSB (t(dout falls) - t(top crosses VBL)).

GATE: per sample, max - min of the code offset over the four levels
<= 0.1 LSB (SPEC item 10's level spread, 0.1 count), at every sample and
every cell. REPORTED: the spread of the level-mean code offset over the
samples (it should equal sigma(Vos)/alpha in LSB plus the delay's own
spread), and the nominal (mismatch-off) level dependence.
Writes data/offset_lin.csv.
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import size_v3 as S  # noqa: E402

CELLS = os.environ.get("LIN_CELLS", "typical:27:3.3 ss:85:3.0 ff:85:3.6").split()
N = int(os.environ.get("LIN_SAMPLES", 30))
LEVELS = (4.5, 40.5, 128.5, 250.5)
SEED0 = 20261007
GATE_LSB = 0.1
# the bench runs this long past the ideal crossing: 28 counts, beyond the
# 19-count overrun, so a late cell is still seen (tb_sel stops 8 counts after)
WINDOW = 28 * 50e-9


def run(job):
    s, cell, k, lvl = job
    tag = "%s_%g_%g" % cell
    d = os.path.join(S.BLOCK, "work", "lin", tag, "k%03d_l%g" % (k, lvl))
    os.makedirs(d, exist_ok=True)
    c = S.common_subs(s, d, 1.0, cell)
    vin = S.VR_LO + lvl * S.LSB
    c.update(VIN="%.9g" % vin, TSTOP="%.6g" % (400e-9 + lvl * S.TCOUNT + WINDOW), VTRIP=c["VCM"])
    text = open(os.path.join(S.BLOCK, "tb_sel.spice")).read()
    for key, v in c.items():
        text = text.replace(f"@{key}@", v)
    # mismatch on (k > 0) with one seed per sample: the same draw at every level
    text = text.replace(".include %s\n" % c["DUT"], ".include %s\n.param sw_stat_mismatch=%d\n.options seed=%d\n"
                        % (c["DUT"], 1 if k else 0, SEED0 + k))
    open(os.path.join(d, "tb.spice"), "w").write(text)
    # the agauss() draws happen when the netlist is parsed, so the seed goes in
    # .spiceinit, read before parsing: the same draw at every level of a sample
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\nset rndseed=%d\n" % (SEED0 + k))
    subprocess.run(["ngspice", "-b", "-o", "tb.out", "tb.spice"], cwd=d, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800,
                   env=dict(os.environ, OMP_NUM_THREADS="1"))
    out = open(os.path.join(d, "tb.out"), errors="replace").read() if os.path.exists(os.path.join(d, "tb.out")) else ""
    blk = out.split("RESULT_BEGIN")[-1].split("RESULT_END")[0] if "RESULT_BEGIN" in out else ""
    return tag, k, lvl, S.grab(blk, "delay_vbl"), S.grab(blk, "armed")


def main():
    sel = json.load(open(os.path.join(S.BLOCK, "data", "sizing.json")))
    s = {k: sel[k] for k in S.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    cells = [(c.split(":")[0], float(c.split(":")[1]), float(c.split(":")[2])) for c in CELLS]
    jobs = [(s, cell, k, lvl) for cell in cells for k in range(N + 1) for lvl in LEVELS]
    print(f"REPORT: offset signal-independence: {len(cells)} cells x ({N} mismatch samples + nominal) x levels "
          f"{', '.join('%g' % l for l in LEVELS)} LSB = {len(jobs)} transients")
    with ThreadPoolExecutor(max_workers=S.JOBS) as ex:
        res = list(ex.map(run, jobs))
    with open(os.path.join(S.BLOCK, "data", "offset_lin.csv"), "w") as h:
        h.write("cell,sample,level_lsb,delay_vbl_s,code_offset_lsb,armed\n")
        for tag, k, lvl, dv, arm in res:
            h.write("%s,%d,%g,%.6g,%.6g,%.4g\n" % (tag, k, lvl, dv, dv / S.TCOUNT, arm))
    ok_all = True
    for cell in cells:
        tag = "%s_%g_%g" % cell
        m = {}
        for t, k, lvl, dv, arm in res:
            if t == tag:
                m.setdefault(k, {})[lvl] = dv / S.TCOUNT
        nom = m.get(0, {})
        nom_spread = (max(nom.values()) - min(nom.values())) if len(nom) == len(LEVELS) else float("nan")
        spreads, means, dead, unmeasured = [], [], [], []
        for k in range(1, N + 1):
            v = {l: m.get(k, {}).get(l, float("nan")) for l in LEVELS}
            upper = [v[l] for l in LEVELS[1:]]
            if not all(np.isfinite(upper)):
                unmeasured.append(k)            # no decision inside the window at a level >= 40.5 LSB
                continue
            if not np.isfinite(v[LEVELS[0]]):
                # already tripped when the ramp starts: offset below -4.5 LSB (the
                # dead zone the ramp pre-roll covers), not a level dependence
                dead.append((k, float(np.mean(upper))))
            got = [x for x in v.values() if np.isfinite(x)]
            spreads.append(max(got) - min(got))
            means.append(float(np.mean(got)))
        spreads, means = np.array(spreads), np.array(means)
        worst = float(spreads.max()) if spreads.size else float("nan")
        good = not unmeasured and worst <= GATE_LSB
        ok_all &= bool(good)
        t = tag.replace(".", "p")
        print(f"lin_{t}_worst_level_spread_lsb = {worst:.6g}")
        print(f"lin_{t}_mean_level_spread_lsb = {float(np.mean(spreads)) if spreads.size else float('nan'):.6g}")
        print(f"lin_{t}_nominal_level_spread_lsb = {nom_spread:.6g}")
        print(f"lin_{t}_code_offset_sigma_lsb = {float(np.std(means, ddof=1)) if means.size > 2 else float('nan'):.6g}")
        print(f"lin_{t}_code_offset_mean_lsb = {float(np.mean(means)):.6g}")
        print(f"lin_{t}_code_offset_min_lsb = {float(np.min(means)):.6g}")
        print(f"lin_{t}_code_offset_max_lsb = {float(np.max(means)):.6g}")
        print(f"lin_{t}_dead_zone_samples = {len(dead)}")
        print(f"{'PASS' if good else 'FAIL'}: offset signal-independence at {tag}: over {spreads.size}/{N} mismatch samples, "
              f"the code offset moves at most {worst:.4f} LSB (mean {np.mean(spreads):.4f}) across the levels "
              f"4.5..250.5 LSB (gate {GATE_LSB} LSB); nominal {nom_spread:.4f} LSB"
              + (f"; {len(unmeasured)} samples with no decision in the window ({unmeasured})" if unmeasured else ""))
        print(f"REPORT: code offset at {tag} over the samples: mean {np.mean(means):+.2f}, sigma {np.std(means, ddof=1):.2f}, "
              f"range {np.min(means):+.2f}..{np.max(means):+.2f} LSB; {len(dead)} samples already tripped at 4.5 LSB "
              f"(offset below -4.5 LSB: {', '.join('%+.2f' % o for _, o in dead) or 'none'}), covered by the ramp pre-roll")
    print("PASS: offset_lin complete" if ok_all else "FAIL: offset is level-dependent somewhere, or a sample did not decide")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
