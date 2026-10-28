"""Size the comparison baseline ramp_simple.spice (current source + switch + C).

    python3 size_simple.py        writes data/ramp_simple_params.spice and
                                  data/sizing_simple.json; RS_OUT=<dir> elsewhere

Same rules as ramp_gen so the comparison is of topologies, not of effort:
  - C = 4.0 pF MIM (44.6 um square), the same capacitor; I = C_model x SLOPE
  - the current source is a pbias slave PMOS at L = 8 um: long for output
    impedance (the 1.6 V swing sits across it) and for flicker area; the
    earlier topology study (simulations/gf180_ramp_topology) found the plain
    source at L = 8 um the best of the uncascoded ones
  - reset switch: NMOS 0.5 / 0.28 um to vrlo, as XRST in ramp_gen
  - the width is bisected in an operating point with vramp forced to mid-ramp
    (1.3 V, where the source sits on average), then trimmed once on the slope
    of a transient of tb_ramp_simple.spice (a best line over counts 8-256)
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
LSB = 1.5 / 256
TCOUNT = 50e-9
SLOPE = LSB / TCOUNT
OUT = os.path.join(BLOCK, os.environ.get("RS_OUT", "data"))
HEAD = """.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
"""


def ng(deck, cwd=None):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(cwd or td, "d.spice")
        open(p, "w").write(deck)
        return subprocess.run(["ngspice", "-b", p], cwd=cwd or td, capture_output=True, text=True).stdout


def grab(out, key):
    for line in out.splitlines():
        if line.startswith(key + " = ") or line.startswith(key + " "):
            try:
                return float(line.split("=")[1].split()[0])
            except (IndexError, ValueError):
                pass
    sys.exit("FAIL: size_simple.py: no %s in the ngspice output\n%s" % (key, out[-1500:]))


p = {"RS_CW": 44.6e-6, "RS_LPS": 8e-6, "RS_WRST": 0.5e-6}
c = grab(ng(HEAD + "V1 a 0 DC 0.8 AC 1\nXC a 0 cap_mim_2f0_m4m5_noshield c_width=%g c_length=%g\n"
            ".control\nac lin 1 1k 1k\nlet cm = abs(imag(i(v1)))/(2*pi*1000)\necho \"cmim = $&cm\"\nquit\n.endc\n.end\n"
            % (p["RS_CW"], p["RS_CW"])), "cmim")
i_target = c * SLOPE


def fmt(k, v):
    return "%d" % v if k == "RS_NFPS" else "%.3fu" % (v * 1e6)


def write_params(path, q):
    with open(path, "w") as f:
        f.write("* Written by size_simple.py. Do not edit by hand; re-run the sizer.\n")
        for k in sorted(q):
            f.write(".param %s=%s\n" % (k, fmt(k, q[k])))


def op_current(q):
    with tempfile.TemporaryDirectory() as td:
        pp = os.path.join(td, "p.spice")
        write_params(pp, q)
        out = ng(HEAD + ".include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice\n"
                 ".include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice\n"
                 ".include %s\n.include /foss/designs/mixed_signal/ramp_gen/ramp_simple.spice\n"
                 "VDD vdd 0 3.3\nVRLO vrlo 0 0.5\nVRST rst 0 0\nVF vramp 0 1.3\n"
                 "XBIAS vdd 0 pbias nbias bias_gen\nXRG vramp rst vrlo pbias vdd 0 ramp_simple\n"
                 ".options gmin=1e-15\n.control\nop\necho \"ips = $&@m.xrg.xps.m0[id]\"\n"
                 "echo \"gm = $&@m.xrg.xps.m0[gm]\"\necho \"gds = $&@m.xrg.xps.m0[gds]\"\nquit\n.endc\n.end\n" % pp, td)
    return abs(grab(out, "ips")), abs(grab(out, "gm")), abs(grab(out, "gds"))


def bisect(target):
    lo, hi = 2e-6, 95e-6
    for _ in range(30):
        p["RS_WPS"] = 0.5 * (lo + hi)
        p["RS_NFPS"] = max(1, int(np.ceil(p["RS_WPS"] / 10e-6)))
        i, _, _ = op_current(p)
        lo, hi = (p["RS_WPS"], hi) if i < target else (lo, p["RS_WPS"])
    p["RS_WPS"] = round(0.5 * (lo + hi) * 1e8) / 1e8
    p["RS_NFPS"] = max(1, int(np.ceil(p["RS_WPS"] / 10e-6)))
    return op_current(p)


def tran_slope(q):
    """best-line slope over counts 8-256 of one tb_ramp_simple run"""
    with tempfile.TemporaryDirectory() as td:
        pp = os.path.join(td, "p.spice")
        write_params(pp, q)
        tb = open(os.path.join(BLOCK, "tb_ramp_simple.spice")).read().replace(
            "/foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice", pp)
        open(os.path.join(td, "tb.spice"), "w").write(tb)
        open(os.path.join(td, "case.spice"), "w").write(
            ".param NCELL=4\n.param VKICK=2.0\n.param VDDX=1\n.param TPRE=0\n")
        subprocess.run(["ngspice", "-b", "tb.spice"], cwd=td, capture_output=True, text=True)
        d = np.loadtxt(os.path.join(td, "ramp.csv"), skiprows=1)
    tr = 1.4e-6
    k = np.arange(8, 257)
    v = np.interp(tr + k * TCOUNT, d[:, 0], d[:, 1])
    return np.polyfit(k * TCOUNT, v, 1)[0]


i_op, gm, gds = bisect(i_target)
ratio = tran_slope(p) / SLOPE
i_op, gm, gds = bisect(i_target / ratio)
os.makedirs(OUT, exist_ok=True)
write_params(os.path.join(OUT, "ramp_simple_params.spice"), p)
pred = {"c": c, "i_target": i_target, "i_op_mid": i_op, "tran_trim": ratio,
        "gm_over_id": gm / i_op, "rout_mohm": 1e-6 / gds,
        # the first-order bow from the source's output conductance: I falls by
        # gds x 1.6 V across the ramp, a parabola of peak 1/8 of the end-point error
        "bow_pred_lsb": (gds * 1.6 / i_op) * 256 / 8}
json.dump({"params": {k: fmt(k, v) for k, v in p.items()}, "predicted": pred},
          open(os.path.join(OUT, "sizing_simple.json"), "w"), indent=1)
for k in sorted(pred):
    print("simple_size_%s = %.6g" % (k, pred[k]))
print("REPORT: simple ramp sized: C %.3f pF, I %.4f uA, XPS W %.2f um L 8 um, trim %.5f"
      % (c * 1e12, i_target * 1e6, p["RS_WPS"] * 1e6, ratio))
