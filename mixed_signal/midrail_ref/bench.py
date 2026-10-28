"""Constants and bench helpers of midref (verify_v3.py, midref_sch.py).

The values are midref_v2's (../midrail_ref_bkp/midrail_ref_v2/size_v2.py), which this block
re-uses device for device; only the bench helpers that verify needs are kept
here, so the folder is self-contained (no table, no search).

Labels: [U] user, [C] contract (../Analog_top_bkp/unit_cell_bps/CONTRACT.md), [B] noise
budget (../Analog_top_bkp/unit_cell_noise/NOISE_BUDGET.md), [M] measured (run named),
[P] PDK, [D] derived, [A] assumed.
"""
import json
import os
import re
import subprocess

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
DATA = os.path.join(BLOCK, "data")
JOBS = int(os.environ.get("JOBS", "12"))

VDD = 3.3
VDD_SET = (3.0, 3.3, 3.6)                      # [C] +/-10 % supply
CORNERS = ("typical", "ff", "ss", "sf", "fs")
TEMPS = (0, 27, 85)
LSB = 1.5 / 256                                # [C] 5.859 mV
ALPHA = 0.761                                  # [M] comparator in the cell (its header)
EPS = LSB / 2                                  # [C] VREF back within 1/2 LSB
TS_MAX = 250e-9                                # [C] 300 ns to TS minus 50 ns kept
NOISE_MAX_LSB = 0.080                          # [B] item 6, VREF + VBL at the ADC input
T_DEC = (0.1e-6, 12.9e-6)                      # [C] decision after TS: TR - TS .. TE - TS
F_CMP = 22.3373e6                              # [M] comparator OTA pole (its data/sizing.json, ngspice)
VERR_MAX = 0.050                               # [A] |VDD/2 error| (v2 README s.1): moves only the
                                               #     comparator common mode, which is the plate level too
CMP_DT_MAX = 0.05                              # [C] decision: trip shift from the buffer's dynamics
XT_MAX_LSB = 0.25                              # [C] v2's VBL-crosstalk bound (1/4 LSB), now applied to
                                               #     the held cell's trip under a neighbour's S2 kick
BIAS_LO, BIAS_HI = 0.69, 1.77                  # [M] ../bias_gen_bkp/bias_gen PVT current span

# the design's bias current, from midref_v2's sizing record (copied as data/sizing_v2.json)
I_F = float(json.load(open(os.path.join(DATA, "sizing_v2.json")))["design"]["i_f"])


def fill(tpl, subs):
    t = open(os.path.join(BLOCK, tpl)).read()
    for k, v in subs.items():
        t = t.replace("@" + k + "@", str(v))
    left = re.findall(r"@[A-Z_0-9]+@", t)
    assert not left, (tpl, left)
    return t


def ngspice(d, deck, timeout=900):
    log = os.path.join(d, deck.replace(".spice", ".log"))
    try:
        subprocess.run(["ngspice", "-b", deck], cwd=d, stdout=open(log, "w"), stderr=subprocess.STDOUT,
                       timeout=timeout)
    except subprocess.TimeoutExpired:
        return ""
    return open(log, errors="replace").read()


NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def grab(txt):
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"^([a-z][a-z_0-9]*) = (" + NUM + r")\s*$", txt, re.M)}


def cell_subs(cell):
    c, t, v = cell
    return dict(CORNER=c, MIMCORNER=c if c in ("ff", "ss") else "typical", TEMP=t, VDD="%g" % v)


def read_xy(path):
    try:
        a = np.loadtxt(path)
    except Exception:
        return None
    return a if a.ndim == 2 and a.shape[0] > 10 else None


def noise_from_files(d):
    """VBL(t_dec) - VREF(TS) from ONE node's output noise. VREF and VBL are the
    same node: VREF is sampled in full at TS (through S2, ~500 MHz), VBL is
    seen through comparator's OTA pole F_CMP and averaged over the decision
    time T_DEC after TS, so the noise below ~1/T_DEC is common to both and
    cancels:  S_out (1 + |H_c|^2 - 2 Re(H_c A)).
    Also returned, from the same spectra, what TWO independent buffers on one
    shared tap gave (midref_v2's case): device noise 1 + |H_c|^2, the tap's
    share as above."""
    out = read_xy(os.path.join(d, "nz_out.txt"))
    tap = read_xy(os.path.join(d, "nz_tap.txt"))
    ac = read_xy(os.path.join(d, "ac.txt"))
    if out is None or tap is None or ac is None:
        return {}
    out = out[np.isfinite(out).all(1)]
    tap, ac = tap[np.isfinite(tap).all(1)], ac[np.isfinite(ac).all(1)]
    f = out[:, 0]
    s_out = out[:, 1] ** 2
    s_tapn = np.interp(f, tap[:, 0], tap[:, 1] ** 2)
    ratio2 = np.interp(f, ac[:, 0], (ac[:, 1] / np.maximum(ac[:, 2], 1e-30)) ** 2)
    s_tap_out = np.minimum(np.nan_to_num(s_tapn * ratio2, nan=0.0, posinf=0.0), s_out)
    s_dev = s_out - s_tap_out
    hc = 1.0 / (1.0 + 1j * f / F_CMP)
    w = 2 * np.pi * f
    t1, t2 = T_DEC
    avg = (np.exp(-1j * w * t1) - np.exp(-1j * w * t2)) / (1j * w * (t2 - t1))
    k_ind = 1.0 + np.abs(hc) ** 2
    k_sh = 1.0 + np.abs(hc) ** 2 - 2.0 * np.real(hc * avg)
    v_one = np.trapezoid(s_out * k_sh, f)
    v_two = np.trapezoid(s_dev * k_ind, f) + np.trapezoid(s_tap_out * k_sh, f)
    return dict(nz_out_uv=float(np.sqrt(np.trapezoid(s_out, f)) * 1e6),
                nz_tap_out_uv=float(np.sqrt(np.trapezoid(s_tap_out, f)) * 1e6),
                nz_lsb=float(np.sqrt(v_one) / ALPHA / LSB),
                nz_two_lsb=float(np.sqrt(v_two) / ALPHA / LSB))
