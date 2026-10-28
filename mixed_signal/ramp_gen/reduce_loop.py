"""Reduce one tb_loop.spice run (loop.csv) to crossover, phase and gain margin.

    python3 reduce_loop.py <case_dir> <tag>

Prints <tag>_t_1k_db (loop gain at 1 kHz), <tag>_fc_hz (|T| = 1),
<tag>_pm_deg (180 + phase there, phase unwrapped from 1 kHz),
<tag>_gm_db (-|T| where the phase reaches -180, or 99 when it never does).
"""
import os
import sys

import numpy as np

case, tag = sys.argv[1], sys.argv[2]
d = np.loadtxt(os.path.join(case, "loop.csv"), skiprows=1)
f, mag, ph = d[:, 0], d[:, 1], d[:, 2]
ph = np.degrees(np.unwrap(np.radians(ph)))
ph = ph - 360 * np.round(ph[0] / 360)          # start within +-180
print("%s_t_1k_db = %.4g" % (tag, mag[0]))
i = np.where((mag[:-1] > 0) & (mag[1:] <= 0))[0]
if i.size:
    k = i[0]
    x = mag[k] / (mag[k] - mag[k + 1])
    fc = np.exp(np.log(f[k]) + x * (np.log(f[k + 1]) - np.log(f[k])))
    pc = ph[k] + x * (ph[k + 1] - ph[k])
    print("%s_fc_hz = %.5g" % (tag, fc))
    print("%s_pm_deg = %.4g" % (tag, 180 + pc))
else:
    print("%s_fc_hz = 0" % tag)
    print("%s_pm_deg = -999" % tag)
j = np.where((ph[:-1] > -180) & (ph[1:] <= -180))[0]
print("%s_gm_db = %.4g" % (tag, -mag[j[0]] if j.size else 99))
