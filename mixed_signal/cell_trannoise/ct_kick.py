"""The clock-edge kick after a decision, from one ngspice run of the cell bench.

    python3 ct_kick.py <tag> <tb.raw> [PARAM=value ...]     -> `ct_kick_<tag>_<name> = value` lines

Finding (2026-10-27, read from the recorded VACASK waves): once a cell has
decided, the latch's NEXT RISING clock edge (the master takes the new D = 0)
glitches dout and pushes the floating plate `bot`, which then drifts for
~25 ns. Codes are not affected (the decision is taken); what matters for the
other cells is the net charge the event leaves on the shared ramp node.

Per run, everything is referred to t_edge = the first rising count-clock edge
after the decision td (dout's first fall through VDD/2 after TR):

  dec_mv      bot's deviation from its pre-decision line at t_edge - 1 ns (the decision kick)
  pk_mv       max deviation in [t_edge - 0.5 ns, t_edge + 3 ns] (the spike)
  drift_mv    deviation at t_edge + 25 ns minus at t_edge - 1 ns (what the edge leaves)
  dout_glitch_v   max of dout in the spike window (dout is low: a glitch is a rise)
  vramp_step_uv / _lsb   vramp's deviation from ITS pre-decision line at t_edge + 30 ns
                         minus at t_edge - 1 ns: the net charge seen by the other cells
  <node>_spike_mv, <node>_drift_mv   for the comparator's outa / outb / bst / tail and the
                         latch's master input (a_853_68#) and output (a_1315_24#)
The line is fitted over [t_edge - 110 ns, t_edge - 45 ns], before the decision kick.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ct_common import load_params, overrides_from, records  # noqa: E402

NODES = {"outa": "xc:xcmp:outa", "outb": "xc:xcmp:outb", "bst": "xc:xcmp:bst", "tail": "xc:xcmp:tail",
         "ffin": "xc:xff:xff:a_853_68#", "ffm": "xc:xff:xff:a_1315_24#"}


def main():
    tag, raw = sys.argv[1], sys.argv[2]
    P = load_params(overrides_from(sys.argv[3:]))
    from rawfile import rawread
    p = rawread(raw).get()
    norm = {}
    for k in p.names:
        s = k.lower()
        if s.startswith("v(") and s.endswith(")"):
            s = s[2:-1]
        norm[s.replace(".", ":")] = k

    def find(name):
        if name not in norm:
            sys.exit("FAIL: ct_kick: %s not in the raw file (%s)" % (name, ",".join(p.names)))
        return np.asarray(np.real(p[norm[name]]))
    t = np.asarray(np.real(p["time"]))
    dout, clk, bot, vr = find("xc:dout"), find("clk"), find("xc:bot") - P["VMID"], find("vramp")
    half, T, LSB = P["VDD"] / 2, P["TCOUNT"], P["LSB"]
    n, t0, tr, te, ti = records(P)[0]
    w = (t >= tr) & (t <= te)
    j = np.where((dout[w][:-1] >= half) & (dout[w][1:] < half))[0]
    if not j.size:
        sys.exit("FAIL: ct_kick %s: no decision in the record" % tag)
    td = t[w][j[0]]
    tedge = tr + np.ceil((td - tr) / T + 1e-9) * T           # the clock rises at TR + k TCOUNT
    rises = np.where((clk[:-1] < half) & (clk[1:] >= half))[0]
    has_edge = bool(np.any(np.abs(t[rises] - tedge) < 1e-9)) if rises.size else False

    def line(x):
        g = np.linspace(tedge - 110e-9, tedge - 45e-9, 300)
        c = np.polyfit(g, np.interp(g, t, x), 1)
        return lambda tt: np.interp(tt, t, x) - np.polyval(c, tt)
    db, dv = line(bot), line(vr)
    sw = np.linspace(tedge - 0.5e-9, tedge + 3e-9, 701)
    out = [("td_minus_tr_ns", (td - tr) * 1e9), ("tedge_minus_td_ns", (tedge - td) * 1e9),
           ("edge_present", 1.0 if has_edge else 0.0),
           ("dec_mv", db(tedge - 1e-9) * 1e3), ("pk_mv", float(np.max(db(sw))) * 1e3),
           ("drift_mv", (db(tedge + 25e-9) - db(tedge - 1e-9)) * 1e3),
           ("dout_glitch_v", float(np.max(np.interp(sw, t, dout)))),
           ("vramp_step_uv", (dv(tedge + 30e-9) - dv(tedge - 1e-9)) * 1e6)]
    out.append(("vramp_step_lsb", out[-1][1] * 1e-6 / LSB))
    # the plate's time course from the decision itself (does the drift start at the
    # clock edge, or at a fixed delay after td?): the peak of the deviation and when
    g = np.linspace(td, td + 80e-9, 1601)
    dd = db(g)
    out += [("plate_max_mv", float(np.max(dd)) * 1e3), ("t_plate_max_minus_td_ns", float(g[np.argmax(dd)] - td) * 1e9),
            ("dev_td50_mv", db(td + 50e-9) * 1e3), ("dev_td80_mv", db(td + 80e-9) * 1e3)]
    for name, node in NODES.items():
        x = find(node)
        x0 = float(np.interp(tedge - 1e-9, t, x))
        out.append((name + "_spike_mv", float(np.max(np.abs(np.interp(sw, t, x) - x0))) * 1e3))
        out.append((name + "_drift_mv", (float(np.interp(tedge + 25e-9, t, x)) - x0) * 1e3))
    for k, v in out:
        print("ct_kick_%s_%s = %.6g" % (tag, k, v))


if __name__ == "__main__":
    main()
