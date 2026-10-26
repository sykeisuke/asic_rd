"""Reduce probe_models.sim: output noise of the normal vs the quiet devices."""
import numpy as np
from rawfile import rawread


def tot(name):
    p = rawread(name + ".raw").get()
    keys = [k for k in p.names if k.lower() not in ("frequency",)]
    onk = [k for k in keys if "onoise" in k.lower()]
    k = onk[0] if onk else None
    if k is None:
        # sum of the per-instance contributions
        s = sum(np.abs(np.asarray(p[x])) for x in keys if x.lower().startswith("n("))
        return np.asarray(p["frequency"]), s, keys
    return np.asarray(p["frequency"]), np.abs(np.asarray(p[k])), keys


ok = True
for norm, quiet, dev in (("nn", "nq", "nfet"), ("pn", "pq", "pfet")):
    f, sn, kn = tot(norm)
    _, sq, kq = tot(quiet)
    r = float(np.max(sq / np.maximum(sn, 1e-99)))
    print("tn_probe_%s_normal_at_1k = %.4g" % (dev, float(np.interp(1e3, f, sn))))
    print("tn_probe_%s_quiet_over_normal_max = %.4g" % (dev, r))
    good = float(np.min(sn)) > 0 and r < 1e-6
    ok &= good
    print("%s: %s_03v3_q is silent (max quiet/normal %.2g) and %s_03v3 is not (keys: %s)"
          % ("PASS" if good else "FAIL", dev, r, dev, ",".join(kn[:6])))
