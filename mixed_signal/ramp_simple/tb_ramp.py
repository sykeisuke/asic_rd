"""Write one bench of the ramp alone: an ideal current source into vramp (the
I/C source's place), the real vrlo_ref (or an ideal VR_LO at the pre-roll
level), the cells as a load and as the S1 charge they dump at connection,
optionally three injected decision kicks.

    python3 tb_ramp.py <dir> [KEY=value ...]        -> <dir>/tb.spice, <dir>/case.json

  NCELL   4        cells on vramp (NCELL x C_CELL of load, NCELL x C_EQ_S1 x (VKICK - VR_LO) of charge)
  VKICK   2.0      the cells' input level for the S1 charge (<= VR_LO: no charge)
  VDDX    1.0      AVDD multiplier
  I       1.0      the ramp current as a multiple of the design current (data/sizing.json)
  VRLO    real     real vrlo_ref at its 7/55 AVDD tap (0.42 V), or ideal: an ideal source at VR_LO_TAP
  CORNER  typical  MOS corner; RCORNER res_typical; MIM typical / ss / ff; TEMP 27
  KICK3   0        1: three decision kicks of -Q_KICK at counts 100 / 150 / 200 after TR (R9)

Timeline (every edge 100 ps): AVDD up in TPWR; T0 = 3 us (vrlo_ref settled,
as the macro's T0); TCONN = T0 + 300 ns the S1 charge; TR = TCONN + 300 ns the
release (vrlo_ref R6); TE = TR + 259 counts (overflow + DRAIN); TRST2 = TE + 50 ns the reset;
TSTOP = TRST2 + 1.5 us (R11 recovery). Output: ramp.csv (time, vramp, vrlo,
rst, iramp) and the measures below. tb_ramp.sch draws the `level` case.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rs_common as rs  # noqa: E402

TPWR, T0 = 100e-9, 3e-6


def timeline():
    tconn = T0 + 300e-9
    tr = tconn + 300e-9
    te = tr + rs.NCNT * rs.TCOUNT
    trst2 = te + 50e-9
    return tconn, tr, te, trst2, trst2 + 1.5e-6


def main():
    d = sys.argv[1]
    kv = dict(a.split("=", 1) for a in sys.argv[2:])
    ncell = int(kv.get("NCELL", 4))
    vkick = float(kv.get("VKICK", 2.0))
    vddx = float(kv.get("VDDX", 1.0))
    ki = float(kv.get("I", 1.0))
    vrlo = kv.get("VRLO", "real")
    corner, rcorner, mim = kv.get("CORNER", "typical"), kv.get("RCORNER", "res_typical"), kv.get("MIM", "typical")
    temp = float(kv.get("TEMP", 27))
    kick3 = int(kv.get("KICK3", 0))
    vdd = rs.VDD * vddx
    i_ramp = ki * rs.design_current()
    vr_lo = rs.VR_LO_TAP if vrlo == "ideal" else rs.VR_LO_TAP * vddx
    T = rs.TCOUNT
    tconn, tr, te, trst2, tstop = timeline()
    qkick = ncell * rs.C_EQ_S1 * max(0.0, vkick - vr_lo)
    L = [rs.head(corner, rcorner, mim, temp),
         ".options reltol=1e-5 abstol=1e-13 vntol=1e-7 gmin=1e-15",
         ".include " + rs.NETLIST,
         "VDD_SOURCE vdd 0 PWL(0 0 %.4g %.6g %.6g %.6g)" % (TPWR, vdd, tstop, vdd),
         "VRST rst 0 PWL(0 0 %.4g %.6g %.9g %.6g %.9g 0 %.9g 0 %.9g %.6g)"
         % (TPWR, vdd, tr, vdd, tr + 100e-12, trst2, trst2 + 100e-12, vdd),
         "* the ramp current: an ideal source (the I/C source's place), up with the supply",
         "IRAMP vdd vramp_i PWL(0 0 %.4g %.6g)" % (TPWR, i_ramp), "VMR vramp_i vramp 0"]
    if vrlo == "real":
        L += [".include " + rs.VRLO_REF,
              "IBVRLO vdd ibvrlo PWL(0 0 %.4g %.6g)" % (TPWR, rs.I_VRLO),
              "XVRLO vrlo ibvrlo vdd 0 vrlo_ref"]
    else:
        L += ["VRLO vrlo 0 %.6f" % vr_lo]
    L += ["XRG vramp rst vrlo 0 ramp_simple",
          "CL vramp 0 %.6g" % (ncell * rs.C_CELL + 1e-15),
          "IKICK 0 vramp PULSE(0 %.6g %.9g 100p 100p 0.9n 1)" % (qkick / 1e-9, tconn)]
    if kick3:
        for j, k in enumerate((100, 150, 200)):
            L.append("IK%d vramp 0 PULSE(0 %.6g %.9g 100p 100p 0.9n 1)" % (j, rs.Q_KICK / 1e-9, tr + k * T))
    L += [".tran 0.2n %.9g 0 2n" % tstop,
          ".save v(vramp) v(vrlo) v(rst) i(vmr) i(vdd_source)",
          ".measure tran i_src_avg AVG i(vmr) FROM=%.9g TO=%.9g" % (tr, te),
          ".measure tran i_total AVG i(vdd_source) FROM=%.9g TO=%.9g" % (tr, te),
          ".measure tran vrlo_tr FIND v(vrlo) AT=%.9g" % tr,
          ".measure tran vrlo_pk MAX v(vrlo) FROM=%.9g TO=%.9g" % (trst2, tstop),
          ".control", "set num_threads=1", "set wr_singlescale", "set wr_vecnames", "run",
          "wrdata ramp.csv v(vramp) v(vrlo) v(rst) i(vmr)", "quit", ".endc", ".end", ""]
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "tb.spice"), "w").write("\n".join(L))
    json.dump({"ncell": ncell, "vkick": vkick, "vddx": vddx, "i_factor": ki, "i_ramp": i_ramp, "vrlo": vrlo,
               "corner": corner, "rcorner": rcorner, "mim": mim, "temp": temp, "kick3": kick3,
               "vr_lo": vr_lo, "vdd": vdd, "tconn": tconn, "tr": tr, "te": te, "trst2": trst2,
               "tstop": tstop, "qkick": qkick, "k_lo": rs.K_LO},
              open(os.path.join(d, "case.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
