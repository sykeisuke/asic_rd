"""Place the held level so that the NOISELESS decision lands on a falling clock edge.

    python3 ct_align.py <tag> <pos_nominal> <al_run/r.csv>   -> appends "<tag> <pos> <k>" to work/align.txt

The noiseless VACASK run at the nominal mid-code gives dout's fall td (from TR).
The nearest falling count-clock edge is e_k = TCOUNT/2 + TEDGE/2 + k TCOUNT.
Moving VIN by dV moves the crossing by dV / SLOPE, so
    POS = POS_nominal + (e_k - td) / TCOUNT
puts the decision on e_k. With noise, q then falls on e_k (Clk, code k) when
dout has crossed VDD/2 before the latch samples, else on e_(k+1) (Clk+1, code k+1).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ct_common import load_params, fall_edge  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    tag, pos0, csv = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    P = load_params({"POS": pos0})
    r = np.atleast_1d(np.genfromtxt(csv, delimiter=",", names=True))
    td = float(np.nanmean(r["td"]))
    if not np.isfinite(td):
        sys.exit("FAIL: ct_align: %s: no decision in the noiseless run" % tag)
    T = P["TCOUNT"]
    k = int(round((td - fall_edge(P, 0)) / T))
    pos = pos0 + (fall_edge(P, k) - td) / T
    print("ct_align_%s_td_nominal_ns = %.4f" % (tag, td * 1e9))
    print("ct_align_%s_td_minus_ideal_ns = %.4f" % (tag, (td - float(np.nanmean(r["ti"]))) * 1e9))
    print("ct_align_%s_edge = %d" % (tag, k))
    print("ct_align_%s_pos = %.6f" % (tag, pos))
    print("ct_align_%s_shift_lsb = %+.4f" % (tag, pos - pos0))
    with open(os.path.join(HERE, "work", "align.txt"), "a") as f:
        f.write("%s %.6f %d\n" % (tag, pos, k))


if __name__ == "__main__":
    main()
