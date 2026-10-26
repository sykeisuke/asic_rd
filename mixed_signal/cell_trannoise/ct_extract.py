"""Reduce one simulation of the cell bench (a VACASK tn.raw or the ngspice tb.raw)
to one row per record.

    python3 ct_extract.py <raw> <out.csv> [PARAM=value ...]

The overrides are the ones the run was made with (POS, NREC, TFIRST), so the
record times are the run's. Columns (times relative to the record's TR, s;
voltages V):

  n       record index
  ti      the ideal crossing, (VIN - VR_LO) / SLOPE
  td      dout's first falling VDD/2 crossing in [TR, TE] (the comparator's decision)
  nd      number of dout falling crossings in [TR, TE] (one expected)
  d0, q0  dout and q at TR (both high: armed, nothing decided yet)
  tq      q's first falling VDD/2 crossing in [TR, TE + 60 ns] (the latch output)
  nq      number of q falling crossings in that window (one expected)
  kq      index k of the falling clock edge that captured: the last edge midpoint
          TCOUNT/2 + TEDGE/2 + k TCOUNT before tq (= the code, floor(tq / TCOUNT))
  cq      tq minus that edge's midpoint (clock-to-q)
  tx      bot's first upward crossing of vref in [TR, TE] (raw, noise included)
  tm      bot - vref averaged over [TR - 40 ns, TR]: the frozen sample the ramp starts from
  at      d(bot)/d(vramp) over the 200 ns before the decision: alpha at the trip
  vr      vramp at ti minus VIN (the ramp's own error at the ideal crossing)
  slope   d(vramp)/dt over [ti - 200 ns, ti]
A second file <out>.waves.npz keeps q, dout, clk and bot - vref on a grid
relative to TR around the crossing (the figure), for the first NWAVE records.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ct_common import load_params, overrides_from, records, fall_edge  # noqa: E402

NWAVE = 48
WLO, WHI, WSTEP = -110e-9, 170e-9, 0.1e-9      # wave grid around POS x TCOUNT after TR


def finder(p):
    norm = {}
    for k in p.names:
        s = k.lower()
        if s.startswith("v(") and s.endswith(")"):
            s = s[2:-1]
        norm[s.replace(".", ":")] = k

    def find(name):
        if name not in norm:
            raise SystemExit("FAIL: ct_extract: %s not in the raw file (%s)" % (name, ",".join(p.names[:16])))
        return np.asarray(np.real(p[norm[name]]))
    return find


def falls(x, y, lvl):
    j = np.where((y[:-1] >= lvl) & (y[1:] < lvl))[0]
    return [x[i] + (y[i] - lvl) / (y[i] - y[i + 1]) * (x[i + 1] - x[i]) for i in j]


def main():
    raw, out = sys.argv[1], sys.argv[2]
    P = load_params(overrides_from(sys.argv[3:]))
    from rawfile import rawread
    p = rawread(raw).get()
    find = finder(p)
    t = np.asarray(np.real(p["time"]))
    dout, q, clk = find("xc:dout"), find("q"), find("clk")
    bot, vr = find("xc:bot") - P["VMID"], find("vramp")
    half, T = P["VDD"] / 2, P["TCOUNT"]
    e0 = fall_edge(P, 0)
    rows, waves = [], []
    grid = np.arange(WLO, WHI, WSTEP)
    for n, t0, tr, te, ti in records(P):
        if te + 60e-9 > t[-1]:
            break
        ti -= tr                                   # relative to TR, as every column
        w = (t >= tr) & (t <= te)
        fd = falls(t[w], dout[w], half)
        w2 = (t >= tr) & (t <= te + 60e-9)
        fq = falls(t[w2], q[w2], half)
        td = fd[0] - tr if fd else np.nan
        tq = fq[0] - tr if fq else np.nan
        if fq:
            kq = np.floor((tq - e0) / T)
            cq = tq - (e0 + kq * T)
        else:
            kq = cq = np.nan
        d0 = float(np.interp(tr, t, dout))
        q0 = float(np.interp(tr, t, q))
        db = bot[w]
        j = np.where((db[:-1] < 0) & (db[1:] >= 0))[0]
        tx = (t[w][j[0]] - db[j[0]] * (t[w][j[0] + 1] - t[w][j[0]]) / (db[j[0] + 1] - db[j[0]]) - tr) if j.size else np.nan
        tm = float(np.mean(np.interp(np.linspace(tr - 40e-9, tr, 401), t, bot)))
        at = np.nan
        if np.isfinite(td):
            g = np.linspace(tr + td - 210e-9, tr + td - 10e-9, 201)
            at = float(np.polyfit(np.interp(g, t, vr), np.interp(g, t, bot), 1)[0])
        gs = np.linspace(tr + ti - 200e-9, tr + ti, 201)
        slope = float(np.polyfit(gs, np.interp(gs, t, vr), 1)[0])
        vrr = float(np.interp(tr + ti, t, vr)) - P["VIN"]
        rows.append([n, ti, td, len(fd), d0, q0, tq, len(fq), kq, cq, tx, tm, at, vrr, slope])
        if len(waves) < NWAVE:
            g = tr + P["POS"] * T + grid
            waves.append(np.array([np.interp(g, t, x) for x in (q, dout, clk, bot)], dtype=np.float32))
    hdr = "n,ti,td,nd,d0,q0,tq,nq,kq,cq,tx,tm,at,vr,slope"
    np.savetxt(out, np.array(rows), delimiter=",", header=hdr, comments="", fmt="%.12g")
    np.savez_compressed(out + ".waves.npz", grid=(P["POS"] * T + grid).astype(np.float64),
                        waves=np.array(waves), names=np.array(["q", "dout", "clk", "bot_minus_vref"]))
    print("ct_extract_records = %d" % len(rows))


if __name__ == "__main__":
    main()
