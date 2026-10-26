"""Verification of the selected vrlo_ref (vrlo_ref.spice + data/sizing.json).
Requirements and their sources: vr.py and README.md s.1.

  op     reset-state operating point at 45 PVT cells (5 corners x 0/27/85 C x
         3.0/3.3/3.6 V) and at the bias / ramp-current spans (typical):
         tail, keep-alive, pair and g-diode in saturation (|vds| - |vdsat|
         >= 0); |vrlo - 5/33 AVDD| <= 1 LSB [A]. Shunt headroom reported.
  tran   tb_tran.spice (forced end of ramp) at the same cells, KS=1 and KS=0:
         start (vramp at T0 vs settled), kick (vramp at TR, full-scale vs
         empty cells), rec (reset level 1 us after the dump vs before), rep
         (vramp at TR, record 2 vs record 1), each <= 0.05 LSB [D];
         err <= 1 LSB [A]. Dump peak, power reported.
  loop   tb_loop.spice, loop gain in the reset and the ramp state at the same
         cells: phase margin >= 45 deg [A]; UGB reported.
  ramp   tb_tran.spice with the real 13.8 us ramp (no forcing) at typical,
         ss/0 C/3.0 V and ff/85 C/3.6 V: the tran gates again, and the forced
         bench's rec / rep agree with the real ramp's within 0.05 LSB
  noise  tb_noise.spice at typical, ss/85 C/3.0 V, ff/0 C/3.6 V: vrlo noise
         1 Hz - 1 GHz <= 0.04 LSB [A] (sampled at TR as the ramp start);
         vramp's and the supply transfer reported
  mc     tb_mc.spice, 200 draws at typical (one ngspice process per draw, seed
         BASE + k), the first 10 re-run with the same seeds (reproducible):
         sigma(vrlo) <= 1 LSB [A], mean reported

    ./container.sh 'python3 verify_vrlo.py'                     all phases
    ./container.sh 'PHASES="op tran" python3 verify_vrlo.py'

Prints one PASS:/FAIL: line per gate and `name = value` metrics.
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import vr

NET = os.path.join(vr.BLOCK, os.environ.get("NETLIST", "vrlo_ref.spice"))
PHASES = os.environ.get("PHASES", "op tran loop ramp noise mc").split()
N_MC = int(os.environ.get("N_MC", "200"))
SEED_BASE = 20261009
CELLS = [(c, t, v) for c in vr.CORNERS for t in vr.TEMPS for v in vr.VDD_SET]
SPANS = [(("typical", 27, vr.VDD), vr.IBS_SPAN[0], 1.0), (("typical", 27, vr.VDD), vr.IBS_SPAN[1], 1.0),
         (("typical", 27, vr.VDD), 1.0, vr.IRS_SPAN[0]), (("typical", 27, vr.VDD), 1.0, vr.IRS_SPAN[1])]
JOBS_ALL = [(c, 1.0, 1.0) for c in CELLS] + SPANS
bad = []


def verdict(ok, text):
    print(("PASS: " if ok else "FAIL: ") + text)
    if not ok:
        bad.append(text)


def jtag(j):
    (c, t, v), bs, rs = j
    return f"{c}/{t:g} C/{v:g} V" + ("" if (bs, rs) == (1.0, 1.0) else f"/bias {bs:g}x/iramp {rs:g}x")


def phase_op(txt, ib):
    temps = sorted({(c, t) for c, t, _ in CELLS})
    jobs = [(c, t, 1.0, 1.0) for c, t in temps] + [("typical", 27, b, r) for (_, b, r) in SPANS]

    def one(j):
        c, t, bs, rs = j
        d = vr.rundir("verify", f"op_{c}_{t}_{bs:g}_{rs:g}", dut=txt)
        open(os.path.join(d, "op.spice"), "w").write(vr.fill("tb_op.spice", dict(
            CORNER=c, MIMCORNER=vr.mimc(c), RESCORNER=vr.resc(c), TEMP=t, IB="%.6g" % (ib * bs),
            IRD="%.6g" % (vr.IRAMP_DIODE * rs), TAG=f"{c} {t} {bs:g} {rs:g}", RATIO="%.10f" % vr.RATIO)))
        out = vr.ngspice(d, "op.spice")
        return [(m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)),
                 [float(x) for x in m.group(6).split()])
                for m in re.finditer(r"^OP (\S+) (\S+) (\S+) (\S+) (\S+) (.*)$", out, re.M)]
    with ThreadPoolExecutor(vr.JOBS) as ex:
        rows = [r for rr in ex.map(one, jobs) for r in rr]
    nom = [r for r in rows if r[2] == 1.0 and r[3] == 1.0]
    span = [r for r in rows if not (r[2] == 1.0 and r[3] == 1.0) and r[4] == vr.VDD]
    use = nom + span
    verdict(len(nom) == 45 and len(span) == 4, f"op: {len(nom)} of 45 PVT cells and {len(span)} of 4 span points solved")
    if not use:
        return
    A = np.array([r[5] for r in use])
    names = ["tail XMT", "keep-alive XMK", "pair XM1", "pair XM2"]

    def where(k):
        r = use[k]
        return f"{r[0]}/{r[1]:g} C/{r[4]:g} V/bias {r[2]:g}x/iramp {r[3]:g}x"
    for i, nm in enumerate(names):
        k = int(np.argmin(A[:, i]))
        verdict(A[k, i] >= 0, f"op headroom {nm}: worst |vds| - |vdsat| {A[k, i]:+.3f} V at {where(k)}")
    k = int(np.argmin(A[:, 5]))
    verdict(A[k, 5] >= 0, f"op headroom g-node diode XM5: worst {A[k, 5]:+.3f} V at {where(k)}")
    k = int(np.argmin(A[:, 4]))
    print(f"REPORT: op: shunt XMS |vds| - |vdsat| worst {A[k, 4]:+.3f} V at {where(k)} (vrlo = 0.45-0.55 V; "
          f"triode only lowers the shunt's gm)")
    k = int(np.argmax(np.abs(A[:, 6])))
    verdict(abs(A[k, 6]) <= vr.VERR_MAX, f"op: |vrlo - 5/33 AVDD| worst {A[k, 6] * 1e3:+.2f} mV at {where(k)} "
            f"(bound {vr.VERR_MAX * 1e3:.2f} mV = {vr.VERR_MAX / vr.LSB:g} LSB)")
    typ = [r for r in nom if r[0] == "typical" and r[1] == 27 and r[4] == vr.VDD][0]
    print(f"op_err_typ_mv = {typ[5][6] * 1e3:.4f}")
    print(f"op_ireg_typ_ua = {typ[5][7] * 1e6:.3f}")
    print(f"op_power_typ_uw = {typ[5][7] * vr.VDD * 1e6:.2f}")
    print(f"op_ireg_max_ua = {np.max(A[:, 7]) * 1e6:.3f}")
    print(f"op_vg_typ_v = {typ[5][8]:.4f}")
    print(f"op_err_min_mv = {np.min(A[:, 6]) * 1e3:.3f}")
    print(f"op_err_max_mv = {np.max(A[:, 6]) * 1e3:.3f}")


def phase_tran(txt, ib, real=False):
    jobs = JOBS_ALL if not real else [(("typical", 27, 3.3), 1.0, 1.0), (("ss", 0, 3.0), 1.0, 1.0),
                                      (("ff", 85, 3.6), 1.0, 1.0)]
    name = "ramp" if real else "tran"

    def one(j):
        cell, bs, rs = j
        d0 = os.path.join("verify", name, "%s_%g_%g_%g_%g" % (cell + (bs, rs)))
        r = vr.tran_pair(d0, txt, cell, bs, rs, ib, real_ramp=real)
        return j, r, vr.tran_gates(r, cell[2])
    with ThreadPoolExecutor(vr.JOBS) as ex:
        res = list(ex.map(one, jobs))
    lim = dict(start=vr.EPS, kick=vr.EPS, rec=vr.EPS, rep=vr.EPS, err=vr.VERR_MAX)
    what = dict(start="start-up (vramp at T0 vs settled)", kick="S1 kick residual at TR (full-scale - empty cells)",
                rec="reset level 1 us after the dump vs before", rep="vramp at TR, record 2 - record 1",
                err="|vrlo - 5/33 AVDD|")
    rows = []
    for g in ("start", "kick", "rec", "rep", "err"):
        vals = [(x[2][g][1], x[0]) for x in res]
        nok = sum(1 for x in res if x[2][g][0])
        w = max(vals, key=lambda p: np.nan_to_num(p[0], nan=1e9))
        verdict(nok == len(res), f"{name} {g}: {what[g]}: {nok} of {len(res)} cells within {lim[g] * 1e3:.3f} mV; "
                f"worst {w[0] * 1e3:.4f} mV ({w[0] / vr.LSB:.4f} LSB) at {jtag(w[1])}")
        print(f"{name}_{g}_worst_mv = {w[0] * 1e3:.5f}")
    kt = max(res, key=lambda x: abs(x[1].get("kick", 0)))
    ki = max(res, key=lambda x: abs(x[1].get("kick_ideal", 0)))
    print(f"REPORT: {name}: total kick residual at TR (regulator + ramp_simple's reset switch) worst "
          f"{kt[1].get('kick', np.nan) * 1e3:+.4f} mV = {kt[1].get('kick', np.nan) / vr.LSB:+.4f} LSB at {jtag(kt[0])}; "
          f"with an ideal source (the switch alone) up to {ki[1].get('kick_ideal', np.nan) / vr.LSB:+.4f} LSB at "
          f"{jtag(ki[0])}")
    print(f"{name}_kick_total_worst_lsb = {abs(kt[1].get('kick', np.nan)) / vr.LSB:.5f}")
    print(f"{name}_kick_switch_worst_lsb = {abs(ki[1].get('kick_ideal', np.nan)) / vr.LSB:.5f}")
    pk = max(res, key=lambda x: x[1].get("vr_pk", 0))
    print(f"REPORT: {name}: dump peak on vrlo up to {pk[1].get('vr_pk', np.nan):.3f} V at {jtag(pk[0])}")
    print(f"{name}_vr_pk_max_v = {pk[1].get('vr_pk', np.nan):.4f}")
    p = [x[1].get("ireg_q", np.nan) * x[0][0][2] * 1e6 for x in res]
    print(f"{name}_power_max_uw = {np.nanmax(p):.2f}")
    for j, r, g in res:
        rows.append(dict(cell=jtag(j), **{k: v[1] for k, v in g.items()}, vr_pk=r.get("vr_pk"),
                         vp_q=r.get("vp_q"), vp_td=r.get("vp_td"), ireg_q=r.get("ireg_q"), ireg_r=r.get("ireg_r")))
    typ = [x for x in res if x[0] == (("typical", 27, 3.3), 1.0, 1.0)][0]
    for g in ("kick", "rec", "rep", "err"):
        print(f"{name}_typ_{g}_mv = {typ[2][g][1] * 1e3:.5f}")
    print(f"{name}_typ_vp_q_v = {typ[1].get('vp_q', np.nan):.6f}")
    if real:
        print(f"ramp_typ_vp_td_v = {typ[1].get('vp_td', np.nan):.4f}")
    json.dump(rows, open(os.path.join(vr.DATA, f"verify_{name}.json"), "w"), indent=1, default=float)
    return {jtag(j): r for j, r, _ in res}


def phase_ramp(txt, ib, forced):
    real = phase_tran(txt, ib, real=True)
    for k, r in real.items():
        f = forced.get(k) if forced else None
        if f is None:
            continue
        for g in ("rec", "rep"):
            a = (r.get("vp_q2" if g == "rec" else "vp_tr2", np.nan) - r.get("vp_q" if g == "rec" else "vp_tr", np.nan))
            b = (f.get("vp_q2" if g == "rec" else "vp_tr2", np.nan) - f.get("vp_q" if g == "rec" else "vp_tr", np.nan))
            verdict(abs(a - b) <= vr.EPS, f"ramp vs forced {g} at {k}: real ramp {a * 1e3:+.4f} mV, forced "
                    f"{b * 1e3:+.4f} mV (agree within {vr.EPS * 1e3:.3f} mV)")


def phase_loop(txt, ib):
    jobs = [(j, rst) for j in JOBS_ALL for rst in (1, 0)]

    def one(x):
        (cell, bs, rs), rst = x
        d0 = os.path.join("verify", "loop", "%s_%g_%g_%g_%g" % (cell + (bs, rs)))
        return x, vr.loop(d0, txt, cell, bs, rs, ib, rst)
    with ThreadPoolExecutor(vr.JOBS) as ex:
        res = list(ex.map(one, jobs))
    rows = []
    for rst, st in ((1, "reset"), (0, "ramp")):
        rr = [(x[0], r) for x, r in res if x[1] == rst]
        pms = [(r.get("pm_deg", np.nan), j) for j, r in rr]
        ugb = [r.get("ugb_hz", np.nan) for _, r in rr]
        w = min(pms, key=lambda p: np.nan_to_num(p[0], nan=-1e9))
        nok = sum(1 for p, _ in pms if np.isfinite(p) and p >= vr.PM_MIN)
        verdict(nok == len(pms), f"loop {st} state: phase margin >= {vr.PM_MIN:g} deg at {nok} of {len(pms)} cells; "
                f"worst {w[0]:.1f} deg at {jtag(w[1])}; UGB {np.nanmin(ugb) / 1e6:.2f}-{np.nanmax(ugb) / 1e6:.2f} MHz")
        print(f"loop_{st}_pm_min_deg = {w[0]:.2f}")
        print(f"loop_{st}_ugb_min_mhz = {np.nanmin(ugb) / 1e6:.3f}")
        t = [r for j, r in rr if j == (("typical", 27, 3.3), 1.0, 1.0)][0]
        print(f"loop_{st}_typ_pm_deg = {t.get('pm_deg', np.nan):.2f}")
        print(f"loop_{st}_typ_ugb_mhz = {t.get('ugb_hz', np.nan) / 1e6:.3f}")
        print(f"loop_{st}_typ_t0_db = {t.get('t0_db', np.nan):.2f}")
        rows += [dict(cell=jtag(j), state=st, pm=r.get("pm_deg"), ugb=r.get("ugb_hz"), t0=r.get("t0_db")) for j, r in rr]
    json.dump(rows, open(os.path.join(vr.DATA, "verify_loop.json"), "w"), indent=1, default=float)


def read_xy(p):
    try:
        a = np.loadtxt(p)
    except (OSError, ValueError):
        return None
    return a if a.ndim == 2 and a.shape[0] > 3 else None


def integ(f, s2, f1, f2):
    m = (f >= f1) & (f <= f2)
    trap = getattr(np, "trapezoid", None) or np.trapz   # numpy 2 renamed it
    return float(np.sqrt(trap(s2[m], f[m])))


def noise_run(txt, ib, cell, tag="noise"):
    """tb_noise at one cell: the spectra (vrlo, vramp, supply transfer) or None."""
    c, t, v = cell
    d = vr.rundir("verify", f"{tag}_{c}_{t}_{v:g}", dut=txt)
    open(os.path.join(d, "noise.spice"), "w").write(vr.fill("tb_noise.spice", dict(
        CORNER=c, MIMCORNER=vr.mimc(c), RESCORNER=vr.resc(c), TEMP=t, VDD="%g" % v, IB="%.6g" % ib,
        IRD="%.6g" % vr.IRAMP_DIODE, CEQ="%.4g" % vr.C_EQ)))
    vr.ngspice(d, "noise.spice")
    return tuple(read_xy(os.path.join(d, n)) for n in ("nz_vrlo.txt", "nz_vramp.txt", "psr.txt"))


def noise_lsb(txt, ib, cell, tag="noise"):
    a, _, _ = noise_run(txt, ib, cell, tag)
    return np.nan if a is None else integ(a[:, 0], a[:, 1] ** 2, 1, 1e9) / vr.LSB


def phase_noise(txt, ib):
    for c, t, v in (("typical", 27, 3.3), ("ss", 85, 3.0), ("ff", 0, 3.6)):
        a, b, p = noise_run(txt, ib, (c, t, v))
        tag = f"{c}_{t}_{v:g}".replace(".", "p")
        if a is None or b is None:
            verdict(False, f"noise {c}/{t} C/{v:g} V: ngspice produced no spectra")
            continue
        tot = integ(a[:, 0], a[:, 1] ** 2, 1, 1e9)
        low = integ(a[:, 0], a[:, 1] ** 2, 1, 1e3)
        ramp = integ(b[:, 0], b[:, 1] ** 2, 1, 1e9)
        verdict(tot / vr.LSB <= vr.NOISE_MAX_LSB, f"noise {c}/{t} C/{v:g} V: vrlo {tot * 1e6:.1f} uV rms 1 Hz-1 GHz = "
                f"{tot / vr.LSB:.4f} LSB (allocation {vr.NOISE_MAX_LSB}); below 1 kHz {low * 1e6:.1f} uV; at vramp "
                f"(incl. the reset switch and the ramp source) {ramp * 1e6:.1f} uV")
        print(f"noise_{tag}_lsb = {tot / vr.LSB:.5f}")
        print(f"noise_{tag}_uv = {tot * 1e6:.3f}")
        print(f"noise_{tag}_vramp_uv = {ramp * 1e6:.3f}")
        if p is not None and c == "typical":
            for fq in (10, 1e3, 1e5, 1e6, 1e7):
                print(f"psr_typ_{int(fq)}hz = {np.interp(fq, p[:, 0], p[:, 1]):.5f}")
            print(f"REPORT: noise: AVDD -> vrlo {np.interp(10, p[:, 0], p[:, 1]):.4f} at 10 Hz (5/33 = "
                  f"{vr.RATIO:.4f}: ratiometric by design), {np.interp(1e6, p[:, 0], p[:, 1]):.4f} at 1 MHz")


def mc_draws(txt, ib, tag, ks):
    def one(k):
        d = vr.rundir("verify", f"{tag}_{k}", dut=txt)
        open(os.path.join(d, "mc.spice"), "w").write(vr.fill("tb_mc.spice", dict(
            CORNER="typical", MIMCORNER="typical", RESCORNER="res_typical", TEMP=27, VDD="3.3", IB="%.6g" % ib,
            IRD="%.6g" % vr.IRAMP_DIODE, MM=0 if k == 0 else 1, SEED=SEED_BASE + k, K=k, RATIO="%.10f" % vr.RATIO)))
        m = re.search(r"^MC (\S+) (\S+) (\S+)$", vr.ngspice(d, "mc.spice"), re.M)
        return [float(x) for x in m.groups()] if m else None
    with ThreadPoolExecutor(vr.JOBS) as ex:
        rows = list(ex.map(one, ks))
    return np.array([r for r in rows if r is not None])


def phase_mc(txt, ib):
    a = mc_draws(txt, ib, "mc1", range(N_MC + 1))
    b = mc_draws(txt, ib, "mc2", range(11))
    verdict(a.shape[0] == N_MC + 1, f"mc: {a.shape[0] - 1} of {N_MC} draws solved")
    same = b.shape[0] == 11 and np.allclose(a[:11], b, atol=1e-9)
    verdict(same, "mc: draws 0-10 re-run with the same seeds reproduce exactly (.options seed per draw)")
    if a.shape[0] < 3:
        return
    verdict(np.std(a[1:, 1]) > 0, "mc: the draws differ from each other (mismatch is applied)")
    sig = float(np.std(a[1:, 1], ddof=1))
    verdict(sig / vr.LSB <= vr.SIGMA_MAX_LSB, f"mc: sigma(vrlo) {sig * 1e3:.3f} mV = {sig / vr.LSB:.3f} LSB (bound "
            f"{vr.SIGMA_MAX_LSB} LSB); mean error {np.mean(a[1:, 1]) * 1e3:+.3f} mV, nominal {a[0, 1] * 1e3:+.3f} mV; "
            f"vramp sigma {np.std(a[1:, 2], ddof=1) * 1e3:.3f} mV")
    print(f"mc_sigma_mv = {sig * 1e3:.4f}")
    print(f"mc_sigma_lsb = {sig / vr.LSB:.4f}")
    print(f"mc_mean_mv = {np.mean(a[1:, 1]) * 1e3:.4f}")
    np.savetxt(os.path.join(vr.DATA, "mc_typ.csv"), a, delimiter=",", header="k,vrlo_err_v,vramp_err_v", comments="")


def main():
    sz = json.load(open(os.path.join(vr.DATA, "sizing.json")))
    ib = sz["design"]["IB"] * 1e-6
    txt = open(NET).read()
    os.makedirs(vr.DATA, exist_ok=True)
    print(f"REPORT: verifying {os.path.basename(NET)}: IB {ib * 1e6:.4g} uA")
    forced = None
    for ph in ("op", "tran", "loop", "ramp", "noise", "mc"):
        if ph not in PHASES:
            continue
        print(f"REPORT: phase {ph}")
        try:
            run_phase(ph, txt, ib, forced)
        except Exception as e:  # noqa: BLE001
            verdict(False, f"verify: phase {ph} raised {type(e).__name__}: {e}")
    print(f"verify_fail_count = {len(bad)}")
    return 1 if bad else 0


FORCED = {}


def run_phase(ph, txt, ib, forced):
        if ph == "op":
            phase_op(txt, ib)
        elif ph == "tran":
            FORCED.update(phase_tran(txt, ib))
        elif ph == "loop":
            phase_loop(txt, ib)
        elif ph == "ramp":
            phase_ramp(txt, ib, FORCED)
        elif ph == "noise":
            phase_noise(txt, ib)
        elif ph == "mc":
            phase_mc(txt, ib)


if __name__ == "__main__":
    sys.exit(main())
