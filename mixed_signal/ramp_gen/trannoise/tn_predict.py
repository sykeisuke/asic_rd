"""Frequency-domain prediction of the transient-noise groups, from VACASK's
own small-signal noise analysis of the same netlist.

    python3 tn_predict.py <snap_dir> <fmin> <fmax>     (from trannoise/, container)
    -> work/predict.json, prints name = value lines

Same two benches as ../noise_bench.py, in VACASK:
  I  vx held at 0.5 V through a noiseless 1 ohm sense resistor; the noise
     across it is the slope-current noise S_I(f) into the virtual ground, per
     instance and per source (bias_gen and XPS / XND / XNS kept);
  V  the ramp-mode loop with the DC-only path LDC (1e15 H) + VOP; the noise
     at vramp, per instance (the OTA's: XM1..XM7, XRST, XRZ kept).

The transient generator does not reproduce the PSD below noisefmin: white
sources are white up to ~noisefmax; flicker is a sum of Lorentzians from
noisefmax down to noisefmin (tran_extraoct = 0 in the benches), which is
flat below noisefmin at about C_PLATEAU x S_flicker(noisefmin) (0.88 for
octave-spaced corners, see predict_var). The prediction uses exactly that
generated spectrum, and repeats the flicker plateau at 0.5x and 1.5x as its
uncertainty. The kernel for code k at t = TR + k TCOUNT (the ramp released
at TR):

  ramp-only (b): var = int S_I,chain |K_t|^2 / C_INT^2 + int S_v,ota + kT / C_INT
  bias-only (c): var = int S_I,bias |K_t|^2 / C_INT^2
  |K_t(f)|^2 = sin^2(pi f t) / (pi f)^2
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tn_netlist import Translator  # noqa: E402

WORK = os.path.join(HERE, "work")
LSB = 1.5 / 256
TCOUNT = 50e-9
KS = (4, 64, 128, 192, 255)
KT = 1.380649e-23 * 300.15
C_PLATEAU = 0.88

HEAD = """{title}

ground 0
include "models.inc"
include "{net}"
load "resistor.osdi"
load "capacitor.osdi"
load "inductor.osdi"
model resistor resistor
model capacitor capacitor
model inductor inductor
model vsource vsource
vdd (vdd 0) vsource dc=3.3
vrlo (vrlo 0) vsource dc=0.5
vrst (rst 0) vsource dc=0
xbias (vdd 0 pbias nbias) bias_gen
xrg (vramp rst vrlo pbias vdd 0 vx vxg) ramp_gen_lb
cl (vramp 0) capacitor c=41f
"""
BENCH_I = HEAD + """vxs (vxs 0) vsource dc=0.5
rs (vx vxs) resistor r=1 noisy=0
vxg (vxg 0) vsource dc=0.5
control
  var mm=0
  options temp=27 tnom=27 gmin=1e-15
  save full
  analysis ni noise out=["vx", "vxs"] in="vdd" from=0.1 to=1e9 mode="dec" points=20
endc
"""
BENCH_V = HEAD + """vsh (vxg vx) vsource dc=0
ldc (vramp nl) inductor l=1e15
vop (nl vx) vsource dc=0.75
control
  var mm=0
  options temp=27 tnom=27 gmin=1e-15
  save full
  analysis nv noise out="vramp" in="vdd" from=0.1 to=1e9 mode="dec" points=20
endc
"""


def lb_netlist(tr, nd_ac_ground=False):
    """The translator's netlist plus ramp_gen_lb: vx and XM1's gate as ports.
    nd_ac_ground: a 1 F capacitor on the slope chain's gate node nd, so that
    in bench V the bias generator reaches vramp only through the OTA's own
    pbias devices (XM7 tail, XM6 load), not through the slope current, which
    bench I and the kernel already account for."""
    txt = tr.emit(set())
    m = re.search(r"subckt ramp_gen \(vramp rst vrlo pbias vdd vss\)\n(.*?)\nends\n", txt, re.S)
    body = m.group(1).replace("  xm1 (d1 vx tail vdd)", "  xm1 (d1 vxg tail vdd)")
    if "xm1 (d1 vxg tail vdd)" not in body:
        raise SystemExit("FAIL: tn_predict: could not break the loop at XM1's gate")
    if nd_ac_ground:
        body += "\n  cnd (nd vss) capacitor c=1"
    return txt + "subckt ramp_gen_lb (vramp rst vrlo pbias vdd vss vx vxg)\n" + body + "\nends\n"


def run(name, deck):
    d = os.path.join(WORK, "predict")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".sim"), "w").write(deck)
    if not os.path.exists(os.path.join(d, "models.inc")):
        os.symlink("../models.inc", os.path.join(d, "models.inc"))
    r = subprocess.run(["vacask", name + ".sim"], cwd=d, capture_output=True, text=True)
    from rawfile import rawread
    raw = os.path.join(d, ("ni" if name == "bench_i" else "nv") + ".raw")
    if not os.path.exists(raw):
        raise SystemExit("FAIL: tn_predict: %s produced no raw file\n%s" % (name, r.stdout[-1500:]))
    p = rawread(raw).get()
    f = np.asarray(p["frequency"]).real
    contrib = {}
    for n in p.names:
        m = re.match(r"^n\((.+),(.+)\)$", n)
        if m:
            contrib[(m.group(1), m.group(2))] = np.abs(np.asarray(p[n]).real)
    return f, contrib


def is_flicker(src):
    return "flick" in src.lower() or "1/f" in src


def gen_psd(f, s, flicker, fmin, fmax, cpl):
    """The PSD the SDE generator actually produces for one source."""
    if flicker:
        sf = np.interp(np.log(fmin), np.log(f), s)
        out = np.where(f >= fmin, s, cpl * sf)
    else:
        out = s.copy()
    return np.where(f <= fmax, out, 0.0)


def band_gen(f, s, flicker, fmin, fmax, cpl):
    """Variance of a stationary noise at vramp as the generator makes it:
    the bench spectrum over [fmin, fmax], plus the band below fmin at the
    level of fmin (flicker: the Lorentzian plateau, cpl x S(fmin); white:
    S(fmin)). Below fmin bench V's own spectrum is not used: its 1e15 H DC
    path resonates with C_INT near 2.5 Hz, an artefact of the linearisation
    (the real loop is closed through reset every conversion)."""
    w = (f >= fmin) & (f <= fmax)
    sf = np.interp(np.log(fmin), np.log(f), s)
    return np.trapezoid(s[w], f[w]) + (cpl if flicker else 1.0) * sf * fmin


def kernel(f, s, t):
    k = (np.sin(np.pi * f * t) / (np.pi * f)) ** 2
    return np.trapezoid(s * k, f)


def main():
    snap, fmin, fmax = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    tr = Translator(snap)
    sz = json.load(open(os.path.join(HERE, "..", "data", "sizing.json")))["predicted"]
    c_int = sz["c_int"]
    net = os.path.join(WORK, "predict", "net_lb.inc")
    os.makedirs(os.path.dirname(net), exist_ok=True)
    open(net, "w").write(lb_netlist(tr))
    open(os.path.join(WORK, "predict", "net_lb_v.inc"), "w").write(lb_netlist(tr, nd_ac_ground=True))
    fi, ci = run("bench_i", BENCH_I.format(title="ramp_gen slope-current noise (VACASK)", net="net_lb.inc"))
    fv, cv = run("bench_v", BENCH_V.format(title="ramp_gen OTA output noise (VACASK)", net="net_lb_v.inc"))
    ff = np.logspace(np.log10(fmin) - 4, np.log10(fmax), 8000)

    def interp(f, s):
        return np.exp(np.interp(np.log(ff), np.log(f), np.log(np.maximum(s, 1e-80))))

    def is_chain(inst):
        return any(inst.startswith("xrg:" + d + ":") or inst == "xrg:" + d for d in ("xps", "xnd", "xns"))

    def is_bias(inst):
        return inst.startswith("xbias:")

    def is_ota(inst):
        return inst.startswith("xrg:") and not is_chain(inst)

    out = {"fmin": fmin, "fmax": fmax, "c_int": c_int, "c_plateau": C_PLATEAU}
    for cpl, tag in ((C_PLATEAU, ""), (0.5 * C_PLATEAU, "_lo"), (1.5 * C_PLATEAU, "_hi")):
        for grp, sel in (("ramp", is_chain), ("bias", is_bias)):
            for k in KS:
                t = k * TCOUNT
                var = 0.0
                for (inst, src), s in ci.items():
                    if sel(inst):
                        var += kernel(ff, gen_psd(ff, interp(fi, s), is_flicker(src), fmin, fmax, cpl), t)
                var /= c_int ** 2
                # stationary noise at vramp: the OTA's own devices (ramp), and the
                # bias generator through the OTA's pbias devices (bias)
                sel_v = is_ota if grp == "ramp" else is_bias
                for (inst, src), s in cv.items():
                    if sel_v(inst):
                        var += band_gen(ff, interp(fv, s), is_flicker(src), fmin, fmax, cpl)
                if grp == "ramp":
                    for (inst, src), s in []:
                            var += np.trapezoid(gen_psd(ff, interp(fv, s), is_flicker(src), fmin, fmax, cpl), ff)
                    var += KT / c_int
                out["pred_%s_k%d_lsb%s" % (grp, k, tag)] = float(np.sqrt(var) / LSB)
    # the same at the lead's ngspice PSDs (data/noise_psd.csv), for the record
    psd = os.path.join(HERE, "..", "data", "noise_psd.csv")
    if os.path.exists(psd):
        head = open(psd).readline().strip().split(",")
        d = np.loadtxt(psd, skiprows=1, delimiter=",")
        fn = d[:, 0]
        for grp in ("ramp", "bias"):
            for k in KS:
                t = k * TCOUNT
                var = 0.0
                for i, n in enumerate(head[1:], 1):
                    if n.startswith("ota:"):
                        dev, kind = n.split(":")[1], n.split(":")[2]
                        if grp == "ramp":
                            var += band_gen(ff, interp(fn, d[:, i]), kind == "flicker", fmin, fmax, C_PLATEAU)
                        continue
                    dev, kind = n.split(":")
                    g = "bias" if dev.startswith("xbias.") else "ramp"
                    if g == grp:
                        var += kernel(ff, gen_psd(ff, interp(fn, d[:, i]), kind == "flicker", fmin, fmax, C_PLATEAU), t) / c_int ** 2
                if grp == "ramp":
                    var += KT / c_int
                out["pred_ngspice_%s_k%d_lsb" % (grp, k)] = float(np.sqrt(var) / LSB)
        fl_n = sum(np.interp(1e3, fn, d[:, i]) for i, n in enumerate(head[1:], 1)
                   if not n.startswith("ota:") and n.endswith(":flicker"))
        out["ngspice_flicker_1k_A2"] = float(fl_n)
    # VACASK vs ngspice flicker of the slope chain, as a ratio of the 1 kHz densities
    fl_v = sum(np.interp(1e3, fi, s) for (inst, src), s in ci.items() if (is_chain(inst) or is_bias(inst)) and is_flicker(src))
    out["vacask_flicker_1k_A2"] = float(fl_v)
    if out.get("ngspice_flicker_1k_A2"):
        out["flicker_vacask_over_ngspice"] = float(fl_v / out["ngspice_flicker_1k_A2"])
    out["n_sources_i"] = len(ci)
    out["n_sources_v"] = len(cv)
    out["source_names"] = sorted({src for (_, src) in list(ci) + list(cv)})
    json.dump(out, open(os.path.join(WORK, "predict.json"), "w"), indent=1)
    for k, v in out.items():
        if isinstance(v, float):
            print("tn_%s = %.5g" % (k, v))
    print("REPORT: VACASK noise source names: %s" % ",".join(out["source_names"]))


if __name__ == "__main__":
    main()
