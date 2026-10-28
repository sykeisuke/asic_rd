"""Verification of the selected comparator in ngspice (typical, 27 C, 3.3 V,
ideal bias current into one tail finger). Prints one name = value line per
measurement and one PASS/FAIL line per acceptance check (run.sh turns them
into metrics.json).

    ./container.sh 'python3 verify_v3.py'

Checks (DESIGN_RECIPE.md s.1):
  netlist   comparator.spice is what data/sizing.json generates
  delay     delay from the static trip <= 12.5 ns at 4.5 / 40.5 / 128.5 / 250.5 LSB
  spread    max - min of those four <= 5 ns (0.1 count)
  fall      dout 10-90 % <= 6 ns into 10 fF, armed at TR
  noise     input-referred at the pins, 1 kHz .. own band, < 1.2 mV
  mc        the ngspice Monte Carlo completes (>= 90 % of N_MC samples cross)
Reported: delay at bias_gen's 0.69x / 1.77x current ends, the VBL-referenced
delay, mean supply power from TCONN to the crossing, and sigma(Vos) at the ADC
input. sigma(Vos) is not gated: ADR 0015 replaced the 4/3 LSB contract by the
signal-independence gate (comparator-pvt PHASES=lin). SIGMA_GATE=<LSB> restores
a sigma gate for a study.
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import size_v3 as S  # noqa: E402

LEVELS = (("c4", 4.5, 1.0), ("plat", 40.5, 1.0), ("mid", 128.5, 1.0), ("top", 250.5, 1.0),
          ("plo", 40.5, S.BIAS_SCALE_LO), ("phi", 40.5, S.BIAS_SCALE_HI))
GATED = ("c4", "plat", "mid", "top")
N_MC = int(os.environ.get("N_MC", 100))
SIGMA_GATE = float(os.environ["SIGMA_GATE"]) if os.environ.get("SIGMA_GATE") else None


def mc(s):
    d = os.path.join(S.BLOCK, "work", "verify", "mc")
    os.makedirs(d, exist_ok=True)
    c = S.common_subs(s, d)
    c["NMC"] = str(N_MC)
    with open(os.path.join(S.BLOCK, "tb_mc.spice")) as h:
        text = h.read()
    for k, v in c.items():
        text = text.replace(f"@{k}@", v)
    with open(os.path.join(d, "tb_mc.spice"), "w") as h:
        h.write(text)
    with open(os.path.join(d, ".spiceinit"), "w") as h:
        h.write("set num_threads=1\n")
    import subprocess
    subprocess.run(["ngspice", "-b", "-o", "tb_mc.out", "tb_mc.spice"], cwd=d, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=7200,
                   env=dict(os.environ, OMP_NUM_THREADS="1"))
    out = open(os.path.join(d, "tb_mc.out"), errors="replace").read()
    nom = re.findall(r"^vos_nom\s*=\s*([-+0-9.eE]+)", out, re.M)
    ks = [float(x) for x in re.findall(r"^vos_k\s*=\s*([-+0-9.eE]+)", out, re.M)]
    return (float(nom[0]) if nom else float("nan")), np.array(ks)


def main():
    s = json.load(open(os.path.join(S.BLOCK, "data", "sizing.json")))
    design = {k: s[k] for k in S.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        design[k] = int(design[k])
    ok_all = True

    def check(name, ok, msg):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}: {name}: {msg}")

    net = open(os.path.join(S.BLOCK, "comparator.spice")).read()
    body = net[net.index(".subckt"):]
    check("netlist", body.strip() == S.subckt(design).strip(), "comparator.spice matches data/sizing.json")

    jobs = [("final", design, lt, k, sc) for lt, k, sc in LEVELS]
    with ThreadPoolExecutor(max_workers=S.JOBS) as ex:
        f_lv = [ex.submit(S.spice_level, j) for j in jobs]
        f_nz = ex.submit(S.spice_noise, ("final", design))
        f_mc = ex.submit(mc, design)
        lv = {lt: r for _, lt, r in (f.result() for f in f_lv)}
        nz = f_nz.result()[2]
        vos_nom, vos = f_mc.result()

    for lt, k, sc in LEVELS:
        r = lv[lt]
        for key in ("delay_dyn", "delay_vbl", "fall", "armed", "p_avg", "vtrip_v"):
            print(f"{lt}_{key} = {r[key]:.6g}")
    dd = np.array([lv[lt]["delay_dyn"] for lt in GATED])
    fl = np.array([lv[lt]["fall"] for lt in GATED + ("plo", "phi")])
    check("delay", np.all(np.isfinite(dd)) and dd.max() <= S.DELAY_MAX,
          f"delay from the static trip {dd.min()*1e9:.2f}..{dd.max()*1e9:.2f} ns over 4.5-250.5 LSB "
          f"(<= {S.DELAY_MAX*1e9:.1f} ns)")
    check("spread", np.ptp(dd) <= S.LOWEND_SPREAD_MAX, f"level spread {np.ptp(dd)*1e9:.2f} ns (<= 5 ns)")
    check("fall", np.all(np.isfinite(fl[:4])) and fl[:4].max() <= S.FALL_MAX,
          f"dout fall {fl[:4].max()*1e9:.2f} ns worst into {S.C_LOAD_DOUT*1e15:.0f} fF (<= 6 ns)")
    check("armed", min(lv[lt]["armed"] for lt in GATED) >= 0.9 * S.VDD, "dout high at TR at every level")
    print(f"REPORT: bias 0.69x / 1.77x (bias_gen PVT ends, not gated with the ideal source): delay "
          f"{lv['plo']['delay_dyn']*1e9:.2f} / {lv['phi']['delay_dyn']*1e9:.2f} ns, fall "
          f"{lv['plo']['fall']*1e9:.2f} / {lv['phi']['fall']*1e9:.2f} ns")
    print(f"REPORT: delay from VBL (offset included) {lv['plat']['delay_vbl']*1e9:.2f} ns at 40.5 LSB")

    for k, v in nz.items():
        print(f"{k} = {v:.6g}")
    check("noise", np.isfinite(nz["nz_own_vin"]) and nz["nz_own_vin"] < S.NOISE_MAX_V,
          f"{nz['nz_own_vin']*1e3:.3f} mV rms at the pins, 1 kHz .. own band (< 1.2 mV); "
          f"{nz['nz_own_vin']/s['alpha']/S.LSB:.3f} LSB at the ADC input")

    vos = vos[np.isfinite(vos)]
    sig = float(np.std(vos, ddof=1)) if vos.size > 2 else float("nan")
    sig_lsb = sig / s["alpha"] / S.LSB
    print(f"mc_samples = {vos.size}")
    print(f"mc_vos_nominal_v = {vos_nom:.6g}")
    print(f"mc_vos_mean_v = {float(np.mean(vos)) if vos.size else float('nan'):.6g}")
    print(f"mc_sigma_vos_v = {sig:.6g}")
    print(f"mc_sigma_in_lsb = {sig_lsb:.6g}")
    print(f"model_sigma_in_lsb = {s['sigma_in_lsb']:.6g}")
    check("mc", vos.size >= 0.9 * N_MC, f"{vos.size} of {N_MC} Monte Carlo samples crossed")
    print(f"REPORT: sigma(Vos) {sig*1e3:.2f} mV at the pins = {sig_lsb:.3f} LSB at the ADC input "
          f"(alpha {s['alpha']:.3f}), {vos.size} samples; not gated (ADR 0015)")
    if SIGMA_GATE is not None:
        check("sigma", sig_lsb <= SIGMA_GATE, f"sigma(Vos) {sig_lsb:.3f} LSB <= {SIGMA_GATE:.3f} LSB (SIGMA_GATE)")
    print(f"power_model_worst_w = {s['power']:.6g}")
    print(f"area_footprint_um2 = {s['area']:.6g}")
    print(f"area_gate_um2 = {s['gate_area']:.6g}")
    print("PASS: verification complete" if ok_all else "FAIL: at least one check failed")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
