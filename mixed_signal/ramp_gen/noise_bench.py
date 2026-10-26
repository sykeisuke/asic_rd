"""Frequency-domain noise characterization of the ramp, device by device.

    python3 noise_bench.py          (inside the container, from the block dir)

Writes data/noise_breakdown.csv (one row per contributor and code),
data/noise_psd.csv (the PSDs, for the figure) and prints name = value lines.

WHY THIS IS EXACT. The integrator holds every device that sets the slope
(XPS, XND, XNS, and the bias generator behind pbias) at a fixed operating
point for the whole conversion: vx never moves. Their noise is therefore
stationary, and a stationary current noise i_n integrated on C_INT from the
reset release (t = 0) gives a ramp error

    e(t) = (1/C_INT) int_0^t i_n dt'
    var e(t) = (1/C_INT^2) int S_I(f) [sin(pi f t)/(pi f)]^2 df    (one-sided S_I)

which is exact, flicker included, for any spectrum. The OTA's own noise is
also stationary (its input stage sits at the fixed virtual ground; its
output stage, which does move, is inside the loop gain), and appears at
vramp as a voltage noise v_n(t) with the closed-loop shape; its variance at
any instant is int S_v df from F_LO.

Three benches, all on work/ramp_gen_lb.spice (vx and XM1's gate as ports):
  I  vx held at VR_LO by an ideal source; S_I(f) of the current it delivers
     (H-source, 1 V/A). Every device's contribution is listed separately by
     ngspice; the ones that set the slope current are kept (bias_gen, XPS,
     XND, XNS). The OTA's contributions in this bench are an artefact of the
     forced vx and are dropped here.
  V  the real ramp-mode loop (vxg = vx), linearised at VOP with the DC-only
     path LDC (1e15 H, open above ~2.5 Hz). Output noise at vramp; the OTA
     devices (XM1..XM7, XRZ, XRST, XCC/XCI none) are kept, the current-chain
     devices dropped (bench I owns them, through the exact kernel).
  V2 bench V with the slope chain's gate node nd AC-grounded (1 F in a test-only
     copy): the ramp's bias generator also biases the OTA (XM7, XM6), and this
     is that second, stationary path to vramp; its bias_gen devices are kept.

Code k crosses at t = (k + 0.5) TCOUNT after the release. F_LO = 1 Hz
[assumed, as SPEC_BPS item 6]; the totals are also given from 100 Hz and
10 kHz. LSB = 5.859 mV; the ramp error is referred 1:1 to the ADC input
(the comparator compares vramp with vin through the charge balance).
"""
import os
import re
import subprocess

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work", "noise")
DATA = os.path.join(BLOCK, "data")
LSB = 1.5 / 256
TCOUNT = 50e-9
F_LO = float(os.environ.get("NOISE_FLO", "1"))
CODES = (4, 16, 64, 128, 192, 255)
K_B, T_K = 1.380649e-23, 300.15

HEAD = """.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice moscap_typical
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/work/ramp_gen_lb.spice
VDD_SOURCE vdd 0 DC 3.3 AC 1
VRLO vrlo 0 0.5
VRST rst 0 0
XBIAS vdd 0 pbias nbias bias_gen
XRG vramp rst vrlo pbias vdd 0 vx vxg ramp_gen_lb
CL vramp 0 41f
.options gmin=1e-15
"""
BENCH_I = HEAD + """VX vx 0 0.5
VXG vxg 0 0.5
HI iout 0 VX 1
.control
set num_threads=1
op
echo "op_ins = $&@m.xrg.xns.m0[id]"
noise v(iout) VDD_SOURCE dec 20 0.1 1G 1
setplot noise1
set filetype=ascii
write noise_i.raw
quit
.endc
.end
"""
BENCH_V = HEAD + """VSH vxg vx 0
LDC vramp nl 1e15
VOP_SRC nl vx {vop}
.control
set num_threads=1
op
echo "op_vramp = $&v(vramp)"
noise v(vramp) VDD_SOURCE dec 20 0.1 1G 1
setplot noise1
set filetype=ascii
write noise_v.raw
quit
.endc
.end
"""


def read_ascii_raw(path):
    """ngspice ascii rawfile -> {name: real array} (one plot)."""
    lines = open(path).read().splitlines()
    names, i = [], 0
    while not lines[i].startswith("Variables:"):
        i += 1
    nvar = int([l for l in lines[:i] if l.startswith("No. Variables:")][0].split(":")[1])
    for j in range(nvar):
        names.append(lines[i + 1 + j].split()[1])
    i += 1 + nvar
    while not lines[i].startswith("Values:"):
        i += 1
    vals = []
    toks = " ".join(lines[i + 1:]).split()
    # each point: index, then nvar values
    step = nvar + 1
    for p in range(len(toks) // step):
        vals.append([float(t.split(",")[0]) for t in toks[p * step + 1:(p + 1) * step]])
    arr = np.array(vals)
    return {n: arr[:, k] for k, n in enumerate(names)}


def contributions(raw):
    """Group the per-generator spectra by device: {device: {kind: S}}, S in units^2/Hz."""
    dev = {}
    for n, v in raw.items():
        m = re.match(r"^onoise\.(.+?)\.(id|1overf|rd|rs|rg|igs|igd|igb|rbpb|rbps|rbpd|rbdb|rbsb)$", n)
        if m:
            dev.setdefault(m.group(1), {})[m.group(2)] = v ** 2
            continue
        m = re.match(r"^onoise\.(r\..+)$", n)          # resistors: one generator (thermal [+ flicker])
        if m and not n.endswith("_spectrum"):
            dev.setdefault(m.group(1), {})["r"] = v ** 2
    return dev


def name_of(path):
    """m.xrg.xns.m0 -> xrg.xns ; r.xrg.xrz.r1 -> xrg.xrz"""
    p = path.split(".")
    return ".".join(p[1:-1]) if len(p) > 2 else path


def kernel_var(f, s, t, flo):
    ff = np.logspace(np.log10(flo), np.log10(f[-1]), 6000)
    si = np.exp(np.interp(np.log(ff), np.log(f), np.log(np.maximum(s, 1e-80))))
    k = (np.sin(np.pi * ff * t) / (np.pi * ff)) ** 2
    return np.trapezoid(si * k, ff)


def band_var(f, s, flo):
    ff = np.logspace(np.log10(flo), np.log10(f[-1]), 6000)
    si = np.exp(np.interp(np.log(ff), np.log(f), np.log(np.maximum(s, 1e-80))))
    return np.trapezoid(si, ff)


def run(deck, name):
    os.makedirs(WORK, exist_ok=True)
    p = os.path.join(WORK, name + ".spice")
    open(p, "w").write(deck)
    r = subprocess.run(["ngspice", "-b", p], cwd=WORK, capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r"^(op_[a-z0-9_]+) = (\S+)", line)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def group(dev):
    if dev.startswith("xbias."):
        return "bias_gen"
    if dev in ("xrg.xps", "xrg.xnd", "xrg.xns"):
        return "ramp_chain"
    return "ramp_ota"


V2_PSDS = []


def main():
    import json
    sz = json.load(open(os.path.join(DATA, "sizing.json")))["predicted"]
    c_int = sz["c_int"]
    opi = run(BENCH_I, "bench_i")
    rawi = read_ascii_raw(os.path.join(WORK, "noise_i.raw"))
    f = rawi["frequency"]
    devi = contributions(rawi)
    vop = 1.25
    opv = run(BENCH_V.replace("{vop}", "%.4f" % (vop - 0.5)), "bench_v")
    rawv = read_ascii_raw(os.path.join(WORK, "noise_v.raw"))
    fv = rawv["frequency"]
    devv = contributions(rawv)
    print("noise_op_ins = %.6g" % opi.get("op_ins", float("nan")))
    print("noise_op_vramp = %.6g" % opv.get("op_vramp", float("nan")))

    rows, psd_cols = [], {"f": f}
    totals = {}
    # current-chain + bias devices through the kernel (bench I)
    for path, kinds in devi.items():
        d = name_of(path)
        g = group(d)
        if g == "ramp_ota":
            continue
        for kind, s in kinds.items():
            if np.max(s) <= 0:
                continue
            lab = "thermal" if kind in ("id", "r", "rd", "rs", "rg") else ("flicker" if kind == "1overf" else kind)
            for k in CODES:
                t = (k + 0.5) * TCOUNT
                var = kernel_var(f, s, t, F_LO) / c_int ** 2
                rows.append((g, d, lab, k, var))
            psd_cols["%s:%s" % (d, lab)] = s
    # OTA devices, stationary at vramp (bench V)
    for path, kinds in devv.items():
        d = name_of(path)
        if group(d) != "ramp_ota":
            continue
        for kind, s in kinds.items():
            if np.max(s) <= 0:
                continue
            lab = "thermal" if kind in ("id", "r", "rd", "rs", "rg") else ("flicker" if kind == "1overf" else kind)
            var = band_var(fv, s, F_LO)
            for k in CODES:
                rows.append(("ramp_ota", d, lab, k, var))
            psd_cols["ota:%s:%s" % (d, lab)] = np.interp(f, fv, s)
    # bench V2: the ramp's own bias generator also biases the OTA (XM7 tail,
    # XM6 load), so its noise reaches vramp directly, stationary, besides the
    # slope path bench I owns. With the slope chain's gate node nd AC-grounded
    # (1 F, a test-only copy) the bias reaches vramp only through the OTA; its
    # devices' contributions there are this second path. (Found by the VACASK
    # cross-check, trannoise/: without it the bias figure at low codes is low.)
    lb = open(os.path.join(BLOCK, "work", "ramp_gen_lb.spice")).read()
    assert ".ends ramp_gen_lb" in lb
    open(os.path.join(BLOCK, "work", "ramp_gen_lb_nd.spice"), "w").write(
        lb.replace(".ends ramp_gen_lb", "CNDAC nd vss 1\n.ends ramp_gen_lb"))
    run(BENCH_V.replace("{vop}", "%.4f" % (vop - 0.5)).replace("work/ramp_gen_lb.spice", "work/ramp_gen_lb_nd.spice")
        .replace("noise_v.raw", "noise_v2.raw"), "bench_v2")
    rawv2 = read_ascii_raw(os.path.join(WORK, "noise_v2.raw"))
    fv2 = rawv2["frequency"]
    for path, kinds in contributions(rawv2).items():
        d = name_of(path)
        if group(d) != "bias_gen":
            continue
        for kind, s in kinds.items():
            if np.max(s) <= 0:
                continue
            lab = ("thermal" if kind in ("id", "r", "rd", "rs", "rg") else ("flicker" if kind == "1overf" else kind)) + " via OTA"
            var = band_var(fv2, s, F_LO)
            V2_PSDS.append((fv2, s))
            for k in CODES:
                rows.append(("bias_gen", d, lab, k, var))
    # reset kT/C frozen on C_INT at the release [derived]
    for k in CODES:
        rows.append(("ramp_reset", "xrg.xrst", "kTC", k, K_B * T_K / c_int))

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "noise_breakdown.csv"), "w") as fo:
        fo.write("group,device,kind,code,var_v2,rms_lsb\n")
        for g, d, lab, k, var in rows:
            fo.write("%s,%s,%s,%d,%.6e,%.6e\n" % (g, d, lab, k, var, np.sqrt(var) / LSB))
    names = list(psd_cols)
    np.savetxt(os.path.join(DATA, "noise_psd.csv"), np.column_stack([psd_cols[n] for n in names]),
               delimiter=",", header=",".join(names), comments="", fmt="%.6e")

    for k in CODES:
        for g in ("bias_gen", "ramp_chain", "ramp_ota", "ramp_reset"):
            v = sum(r[4] for r in rows if r[0] == g and r[3] == k)
            totals[(g, k)] = v
            print("noise_%s_c%d_lsb = %.5f" % (g, k, np.sqrt(v) / LSB))
        vr = sum(totals[(g, k)] for g in ("ramp_chain", "ramp_ota", "ramp_reset"))
        print("noise_ramp_own_c%d_lsb = %.5f" % (k, np.sqrt(vr) / LSB))
        print("noise_ramp_total_c%d_lsb = %.5f" % (k, np.sqrt(vr + totals[("bias_gen", k)]) / LSB))
    # the largest single contributors at the top code
    top = sorted([r for r in rows if r[3] == 255], key=lambda r: -r[4])[:8]
    for g, d, lab, k, var in top:
        print("REPORT: c255 contributor %s %s %s %.4f LSB" % (g, d, lab, np.sqrt(var) / LSB))
    # the low-frequency limit: totals from 100 Hz and 10 kHz at code 255
    for flo in (100.0, 1e4):
        v = 0.0
        for path, kinds in devi.items():
            d = name_of(path)
            if group(d) == "ramp_ota":
                continue
            for s in kinds.values():
                v += kernel_var(f, s, 255.5 * TCOUNT, flo) / c_int ** 2
        for path, kinds in devv.items():
            if group(name_of(path)) == "ramp_ota":
                for s in kinds.values():
                    v += band_var(fv, s, flo)
        for fq, s in V2_PSDS:
            v += band_var(fq, s, flo)
        print("noise_ramp_total_c255_flo%g_lsb = %.5f" % (flo, np.sqrt(v + K_B * T_K / c_int) / LSB))


if __name__ == "__main__":
    main()
