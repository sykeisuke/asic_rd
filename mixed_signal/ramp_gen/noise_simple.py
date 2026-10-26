"""Frequency-domain noise of the simple ramp (ramp_simple), the same method as
noise_bench.py for ramp_gen, so the two breakdowns compare term for term.

    python3 noise_simple.py

The current source XPS charges C directly. Its drain is the ramp, so its
operating point moves with the ramp (V_SD 2.8 -> 1.2 V) and its noise is not
strictly stationary. The bench holds vramp at mid-ramp (1.3 V, the average
operating point) and the current noise is integrated with the same exact
kernel. Because the drain voltage moves, this is the mid-point approximation;
the noise varies little over that range in saturation. Contributions: the
ramp's bias_gen (through XPS), XPS itself, and the reset kT/C frozen on the
capacitor at the release (kT/C_total). Nothing else is on the slope path: no
OTA, no virtual ground. The vrlo reference is ideal and noiseless here; a
real one adds its noise 1:1.

Writes data/noise_simple_breakdown.csv; prints simple_noise_* lines.
"""
import json
import os
import re
import subprocess

import numpy as np

from noise_bench import read_ascii_raw, contributions, name_of, kernel_var, CODES, LSB, TCOUNT, K_B, T_K, F_LO

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work", "noise_simple")
DATA = os.path.join(BLOCK, "data")
DECK = """.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/data/bias_gen_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ref/bias_gen/bias_gen.spice
.include /foss/designs/mixed_signal/ramp_gen/data/ramp_simple_params.spice
.include /foss/designs/mixed_signal/ramp_gen/ramp_simple.spice
VDD_SOURCE vdd 0 DC 3.3 AC 1
VRLO vrlo 0 0.5
VRST rst 0 0
VF vramp 0 1.3
HI iout 0 VF 1
XBIAS vdd 0 pbias nbias bias_gen
XRG vramp rst vrlo pbias vdd 0 ramp_simple
.options gmin=1e-15
.control
set num_threads=1
op
echo "op_ips = $&@m.xrg.xps.m0[id]"
noise v(iout) VDD_SOURCE dec 20 0.1 1G 1
setplot noise1
set filetype=ascii
write noise_s.raw
quit
.endc
.end
"""


def main():
    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, "bench.spice"), "w").write(DECK)
    r = subprocess.run(["ngspice", "-b", "bench.spice"], cwd=WORK, capture_output=True, text=True)
    m = re.search(r"op_ips = (\S+)", r.stdout)
    print("simple_noise_op_ips = %s" % (m.group(1) if m else "nan"))
    raw = read_ascii_raw(os.path.join(WORK, "noise_s.raw"))
    f = raw["frequency"]
    sz = json.load(open(os.path.join(DATA, "sizing_simple.json")))["predicted"]
    c_tot = sz["c"] + 41e-15            # + the 4-cell load the bench carries
    rows = []
    for path, kinds in contributions(raw).items():
        d = name_of(path)
        g = "bias_gen" if d.startswith("xbias.") else ("ramp_chain" if d == "xrg.xps" else None)
        if g is None:
            continue
        for kind, s in kinds.items():
            if np.max(s) <= 0:
                continue
            lab = "thermal" if kind in ("id", "r", "rd", "rs", "rg") else ("flicker" if kind == "1overf" else kind)
            for k in CODES:
                rows.append((g, d, lab, k, kernel_var(f, s, (k + 0.5) * TCOUNT, F_LO) / c_tot ** 2))
    for k in CODES:
        rows.append(("ramp_reset", "xrg.xrst", "kTC", k, K_B * T_K / c_tot))
    with open(os.path.join(DATA, "noise_simple_breakdown.csv"), "w") as fo:
        fo.write("group,device,kind,code,var_v2,rms_lsb\n")
        for g, d, lab, k, var in rows:
            fo.write("%s,%s,%s,%d,%.6e,%.6e\n" % (g, d, lab, k, var, np.sqrt(var) / LSB))
    for k in CODES:
        tot = {}
        for g in ("bias_gen", "ramp_chain", "ramp_reset"):
            tot[g] = sum(r[4] for r in rows if r[0] == g and r[3] == k)
            print("simple_noise_%s_c%d_lsb = %.5f" % (g, k, np.sqrt(tot[g]) / LSB))
        own = tot["ramp_chain"] + tot["ramp_reset"]
        print("simple_noise_ramp_own_c%d_lsb = %.5f" % (k, np.sqrt(own) / LSB))
        print("simple_noise_ramp_total_c%d_lsb = %.5f" % (k, np.sqrt(own + tot["bias_gen"]) / LSB))
    for g, d, lab, k, var in sorted([r for r in rows if r[3] == 255], key=lambda r: -r[4])[:5]:
        print("REPORT: simple c255 contributor %s %s %s %.4f LSB" % (g, d, lab, np.sqrt(var) / LSB))


if __name__ == "__main__":
    main()
