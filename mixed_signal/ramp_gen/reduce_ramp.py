"""Reduce one tb_ramp.spice run (ramp.csv in the case directory) to scalars.

    python3 reduce_ramp.py <case_dir> [tag]

Prints `name = value` lines (prefixed with the tag when given). The ramp is
sampled at every count boundary t_k = TR + k TCOUNT, k = 0..276 (256 codes
plus the 20-count overrun):

  slope_err_pct   best-fit slope over k = 8..256 against SLOPE, percent
  offset_lsb      best-fit value at k = 0 minus VR_LO, LSB
  inl_lsb         max |residual| from that line over k = 8..256, LSB
  inl_end_lsb     the same against the end-point line (k = 8 and k = 256)
  start_dev_lsb_k residual at k = 0, 1, 2, 4, 6 (the start transient)
  start_settle_k  first k after which |residual| stays below 0.05 LSB
  vx_* / vx_span  the virtual ground at TR, TR + 25, 50, 100, 200, 500 ns,
                  1, 3 us, and its total excursion over k = 8..256, mV
  kick_*          the S1-connection kick: peak, residual at TR, the time it
                  takes from TCONN to stay within 0.3 mV (0.05 LSB) of the
                  pre-kick reset level
  rec_ns          after the second reset edge: time until vramp stays within
                  1 mV of its reset level (the next conversion's track phase)
"""
import os
import sys

import numpy as np

case = sys.argv[1]
tag = sys.argv[2] + "_" if len(sys.argv) > 2 else ""

VR_LO, LSB, TCOUNT = 0.5, 1.5 / 256, 50e-9
SLOPE = LSB / TCOUNT
T0 = 1e-6
TS, TCONN, TR = T0 + 300e-9, T0 + 310e-9, T0 + 400e-9
TE = TR + 256 * TCOUNT
TRST2 = TE + 20 * TCOUNT + 50e-9

d = np.loadtxt(os.path.join(case, "ramp.csv"), skiprows=1)
t, vr, vx, rst = d[:, 0], d[:, 1], d[:, 2], d[:, 3]


def at(x, tt):
    return np.interp(tt, t, x)


def out(name, val, fmt="%.6g"):
    print(("%s%s = " + fmt) % (tag, name, val))


k = np.arange(0, 277)
vk = at(vr, TR + k * TCOUNT)
fit = (k >= 8) & (k <= 256)
p = np.polyfit(k[fit], vk[fit], 1)
res = (vk - np.polyval(p, k)) / LSB
out("slope_err_pct", (p[0] / TCOUNT / SLOPE - 1) * 100)
out("offset_lsb", (p[1] - VR_LO) / LSB)
out("inl_lsb", np.max(np.abs(res[fit])))
pe = np.polyfit([8, 256], [vk[8], vk[256]], 1)
out("inl_end_lsb", np.max(np.abs((vk[fit] - np.polyval(pe, k[fit])) / LSB)))
out("inl_ovr_lsb", np.max(np.abs(res[256:277])))
for kk in (0, 1, 2, 4, 6):
    out("start_dev_lsb_%d" % kk, res[kk])
bad = np.where(np.abs(res[:257]) > 0.05)[0]
out("start_settle_k", (bad.max() + 1) if bad.size else 0, "%d")
out("vr_te", vk[256])
for name, dt in (("tr", 0), ("25n", 25e-9), ("50n", 50e-9), ("100n", 100e-9), ("200n", 200e-9),
                 ("500n", 500e-9), ("1u", 1e-6), ("3u", 3e-6)):
    out("vx_%s_mv" % name, (at(vx, TR + dt) - VR_LO) * 1e3)
vxk = at(vx, TR + k[fit] * TCOUNT)
out("vx_span_mv", (vxk.max() - vxk.min()) * 1e3)

# the S1-connection kick: reference = the reset level just before TCONN
vref = at(vr, TCONN - 2e-9)
w = (t >= TCONN) & (t <= TR)
dev = vr[w] - vref
out("kick_peak_mv", dev[np.argmax(np.abs(dev))] * 1e3)
out("kick_res_tr_mv", (at(vr, TR - 0.5e-9) - vref) * 1e3)
outside = np.where(np.abs(dev) > 0.3e-3)[0]
out("kick_settle_ns", ((t[w][outside[-1]] - TCONN) * 1e9) if outside.size else 0.0)

# recovery after the second reset
vend = vr[-1]
w2 = t >= TRST2
o2 = np.where(np.abs(vr[w2] - vend) > 1e-3)[0]
out("rec_ns", ((t[w2][o2[-1]] - TRST2) * 1e9) if o2.size else 0.0)
out("rec_level_mv", (vend - VR_LO) * 1e3)
np.savetxt(os.path.join(case, "residual.csv"), np.column_stack([k, vk, res]),
           delimiter=",", header="k,vramp,res_lsb", comments="")
