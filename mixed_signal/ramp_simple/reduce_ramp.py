"""Reduce one tb_ramp.py run (ramp.csv + case.json + the measure echoes) to scalars.

    python3 reduce_ramp.py <dir> [tag]         -> `tag_name = value` lines

The ramp is sampled at the count boundaries t_k = TR + k TCOUNT, k = 0..259.
The conversion window is k = K_LO .. 255, the valid codes (K_LO = 9, the
pre-roll, when the reset level is the pre-roll level; 0 on vrlo_ref's 0.5 V
level; ADR 0025):

  slope_err_pct    best-fit slope over the window against SLOPE, percent
  offset_lsb       best-fit value at k = 0 minus the reset level, LSB
  inl_lsb          max |residual| from that line over the window, LSB
  inl_end_lsb      the same against the end-point line of the window
  inl_ovr_lsb      max |residual| after the window (to the end of the ramp)
  start_dev_lsb_k  residual at k = 0, 1, 2, 4 (the start transient)
  start_settle_k   first k after which |residual| stays below 0.05 LSB
  drop_tr_lsb      vramp - vrlo just before the release (I x Ron + what S1 left), LSB
  kick_peak_mv, kick_res_tr_mv, kick_settle_ns   the S1 charge at TCONN: peak, what is
                   left at TR against the pre-kick level, time to stay within 0.05 LSB
  rec_ns, rec_level_mv   after the end-of-ramp reset: time until vramp stays within
                   0.05 LSB of its final level; final level minus the reset level
  kick3_lsb        (KICK3 runs) residual change from counts 90..99 to 210..219: what
                   three injected decision kicks leave on the ramp
  vr_255_v         vramp at count 255, the end of the valid codes (SPEC R3/R4)
  vr_top_v         vramp at the end of the ramp
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_common as rs  # noqa: E402

case = sys.argv[1]
tag = sys.argv[2] + "_" if len(sys.argv) > 2 else ""
C = json.load(open(os.path.join(case, "case.json")))
LSB, T = rs.LSB, rs.TCOUNT
TR, TE, TRST2, TCONN = C["tr"], C["te"], C["trst2"], C["tconn"]
K_LO = int(C["k_lo"])
d = np.loadtxt(os.path.join(case, "ramp.csv"), skiprows=1)
t, vr, vrlo, rst = d[:, 0], d[:, 1], d[:, 2], d[:, 3]


def at(x, tt):
    return np.interp(tt, t, x)


def out(name, val, fmt="%.6g"):
    print(("%s%s = " + fmt) % (tag, name, val))


k = np.arange(0, rs.NCNT + 1)
vk = at(vr, TR + k * T)
lo, hi = K_LO + (0 if K_LO else 4), rs.NVALID
fit = (k >= lo) & (k <= hi)
p = np.polyfit(k[fit], vk[fit], 1)
res = (vk - np.polyval(p, k)) / LSB
level = at(vrlo, TR - 0.5e-9)
out("slope_err_pct", (p[0] / T / rs.SLOPE - 1) * 100)
out("offset_lsb", (p[1] - level) / LSB)
out("inl_lsb", np.max(np.abs(res[fit])))
pe = np.polyfit([lo, hi], [vk[lo], vk[hi]], 1)
out("inl_end_lsb", np.max(np.abs((vk[fit] - np.polyval(pe, k[fit])) / LSB)))
out("inl_ovr_lsb", np.max(np.abs(res[hi:rs.NCNT + 1])))
# the start transient, against a LOCAL line (the first 40 counts after K_LO + 4), so
# that the bow of the whole ramp does not enter it
ks = (k >= K_LO + 4) & (k <= K_LO + 44)
ps = np.polyfit(k[ks], vk[ks], 1)
res_s = (vk - np.polyval(ps, k)) / LSB
for kk in (0, 1, 2, 4):
    out("start_dev_lsb_%d" % kk, res_s[kk])
bad = np.where(np.abs(res_s[:K_LO + 45]) > 0.05)[0]
out("start_settle_k", (bad.max() + 1) if bad.size else 0, "%d")
out("ideal_dev_te_lsb", (vk[hi] - (level + hi * LSB)) / LSB)
out("drop_tr_lsb", (at(vr, TR - 0.5e-9) - level) / LSB)
out("vr_te_v", vk[hi])
out("vr_255_v", vk[rs.NVALID])
out("vr_top_v", vk[rs.NCNT])
# the S1 charge at TCONN
vref = at(vr, TCONN - 2e-9)
w = (t >= TCONN) & (t <= TR)
dev = vr[w] - vref
out("kick_peak_mv", (dev[np.argmax(np.abs(dev))] if dev.size else 0.0) * 1e3)
out("kick_res_tr_mv", (at(vr, TR - 0.5e-9) - vref) * 1e3)
outside = np.where(np.abs(dev) > 0.05 * LSB)[0]
out("kick_settle_ns", ((t[w][outside[-1]] - TCONN) * 1e9) if outside.size else 0.0)
# recovery after the end-of-ramp reset
vend = vr[-1]
w2 = t >= TRST2
o2 = np.where(np.abs(vr[w2] - vend) > 0.05 * LSB)[0]
out("rec_ns", ((t[w2][o2[-1]] - TRST2) * 1e9) if o2.size else 0.0)
out("rec_level_mv", (vend - at(vrlo, t[-1])) * 1e3)
out("vrlo_pk_mv", (np.max(vrlo[w2]) - level) * 1e3)
if C.get("kick3"):
    out("kick3_lsb", np.mean(res[210:220]) - np.mean(res[90:100]))
np.savetxt(os.path.join(case, "residual.csv"), np.column_stack([k, vk, res]),
           delimiter=",", header="k,vramp,res_lsb", comments="")
