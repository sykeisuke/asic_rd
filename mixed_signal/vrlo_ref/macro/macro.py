"""macro.py -- vrlo_ref inside the analog macro (ref_analog_top/analog_top.spice,
typical), against the ideal 0.5 V source it replaces. Four ngspice runs:

  one-record  Analog_top's own functional bench tb_analog_top.spice (read from
              there, not copied): as is (ideal VVRLO) and with VVRLO replaced
              by vrlo_ref on its ideal bias current
  two-record  tb_macro2.spice: record 1, the end-of-ramp reset, record 2 with
              the same inputs, again ideal and real

Gates (README.md s.1):
  pedestal    one record: the input-referred error of each cell's trip
              (err_d_k, continuous count from dout) moves by the same amount
              in all four cells when vrlo becomes real: spread of
              err_d_k(real) - err_d_k(ideal) over the cells <= 0.05 LSB (a
              level-dependent part would be the S1 kicks left on vrlo at TR)
  codes       |code_k(real) - code_k(ideal)| <= 1 (the common shift may move
              a code boundary; the calibration removes it)
  repeat      two records: record 2 - record 1 of each cell's continuous trip
              count, real minus ideal, <= 0.05 LSB (the reset dump and the
              S1 charge leave nothing for the next record)
Reported: the common shift (vrlo's pedestal), dump peak, ideal-source
record-to-record difference, codes.

    ./container.sh 'python3 macro/macro.py'     (run.sh phase macro)
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import vr  # noqa: E402

AT = "/foss/designs/mixed_signal/vrlo_ref/macro/ref_analog_top"
NET = os.path.join(vr.BLOCK, "vrlo_ref.spice")
INC = ".include /foss/designs/mixed_signal/vrlo_ref/vrlo_ref.spice"
IDEAL = "VVRLO vrlo 0 {VR_LO}"
# The timeline requirement this block sets (README.md s.1): the ramp is released
# TGAP = 300 ns after the last S1 closes, not 100 ns as in Analog_top's
# tb_params.inc. Each run gets a local copy of tb_params.inc with that one line
# changed; Analog_top's own files are not touched.
PARAMS = "/foss/designs/mixed_signal/vrlo_ref/macro/ref_analog_top/tb_params.inc"
TR_OLD, TR_NEW = ".param TR='TS3+100n'", ".param TR='TS3+300n'"
bad = []
BENCHES = os.environ.get("BENCHES", "one two").split()


def verdict(ok, text):
    print(("PASS: " if ok else "FAIL: ") + text)
    if not ok:
        bad.append(text)


def real_src(ib):
    return f"IBVRLO avdd ibvrlo PWL(0 0 {{TPWR}} {ib:.6g})\nXVRLO vrlo ibvrlo avdd 0 vrlo_ref"


# The S1 charge each cell pushes through the ideal VVRLO when its bottom plate
# joins vramp (S1_k closes at TS_k + 2 TNOV): the integral over 48 ns (3.4
# XRST x 4 pF time constants, before the next cell's S1) less the DC ramp
# current. Run again with every input at VR_LO ("ideal0"), the difference is
# the signal-dependent charge, and C_sig,k = dQ_k / (VIN_k - VR_LO) is what the
# block benches model as CEQ (vr.C_EQ must not be smaller). The rest (Q at
# VR_LO: S1's own injection, plate parasitics) is the same every record.
KICK_MEAS = "".join(
    f".measure tran ivr_pre{k} AVG i(VVRLO) FROM={{TS{k}+2*TNOV-3n}} TO={{TS{k}+2*TNOV-0.5n}}\n"
    f".measure tran qvr{k} INTEG i(VVRLO) FROM={{TS{k}+2*TNOV}} TO={{TS{k}+2*TNOV+48n}}\n"
    f".measure tran qs1_{k} PARAM='qvr{k}-ivr_pre{k}*48n'\n"
    f".measure tran ceq{k} PARAM='qs1_{k}/(VIN{k}-VR_LO)'\n" for k in range(4))


def one_record(kind, ib):
    """kind: ideal / real, or ideal0 / real0 with every input at 4.5 LSB (at VR_LO itself the
    comparators sit at their trip point and never cross: not a valid reference)."""
    t = open(os.path.join(AT, "tb_analog_top.spice")).read()
    assert IDEAL in t, "tb_analog_top.spice no longer carries the ideal VVRLO line"
    if kind.endswith("0"):
        t, n = re.subn(r"^VVIN vin 0 .*$", "VVIN vin 0 {VR_LO+4.5*LSB}", t, flags=re.M)
        assert n == 1, "tb_analog_top.spice: no single VVIN line"
    if kind.startswith("ideal"):
        t = re.sub(r"^\.end\s*$", KICK_MEAS + ".end", t, flags=re.M)
    if kind.startswith("real"):
        t = t.replace(IDEAL, real_src(ib))
        t = t.replace(".include /foss/designs/mixed_signal/vrlo_ref/macro/ref_analog_top/analog_top.spice",
                      ".include /foss/designs/mixed_signal/vrlo_ref/macro/ref_analog_top/analog_top.spice\n" + INC)
    return t


def two_record(kind, ib):
    t = open(os.path.join(HERE, "tb_macro2.spice")).read()
    return t.replace("@INCLUDE@", INC if kind == "real" else "").replace("@VRLO@", real_src(ib) if kind == "real" else IDEAL)


def run(job):
    bench, kind, ib = job
    d = vr.rundir("macro", f"{bench}_{kind}")
    deck = one_record(kind, ib) if bench == "one" else two_record(kind, ib)
    prm = open(os.path.join(AT, "tb_params.inc")).read()
    assert TR_OLD in prm and PARAMS in deck, "tb_params.inc / its include changed"
    open(os.path.join(d, "tb_params_gap.inc"), "w").write(prm.replace(TR_OLD, TR_NEW))
    open(os.path.join(d, "tb.spice"), "w").write(deck.replace(PARAMS, "tb_params_gap.inc"))
    log = vr.ngspice(d, "tb.spice", timeout=3600)
    # simulator errors, as Analog_top/func.sh reports them (the log itself is never read)
    lines = log.splitlines()
    hits = [i for i, x in enumerate(lines)
            if re.search(r"(^| )(error|fatal)|undefined|cannot compute|timestep too small", x, re.I)][:2]
    for i in hits:
        for ln in lines[i:i + 2]:
            print(f"REPORT: macro {bench}/{kind}: ngspice: {ln.strip()[:160]}")
    return job[:2], vr.grab(log)


def main():
    ib = json.load(open(os.path.join(vr.DATA, "sizing.json")))["design"]["IB"] * 1e-6
    kinds = dict(one=("ideal", "real", "ideal0", "real0"), two=("ideal", "real"))
    jobs = [(b, k, ib) for b in BENCHES for k in kinds[b]]
    with ThreadPoolExecutor(6) as ex:
        R = dict(ex.map(run, jobs))
    oi, orl, ti, tr = (R.get(x, {}) for x in (("one", "ideal"), ("one", "real"), ("two", "ideal"), ("two", "real")))
    oi0, orl0 = R.get(("one", "ideal0"), {}), R.get(("one", "real0"), {})
    out = {}
    # ---- one record
    need = [f"err_d{k}" for k in range(4)] + [f"code{k}" for k in range(4)]
    if "one" not in BENCHES:
        pass
    elif all(n in oi and n in orl for n in need):
        de = np.array([orl[f"err_d{k}"] - oi[f"err_d{k}"] for k in range(4)])
        verdict(de.max() - de.min() <= 0.05, "pedestal: err_d(real) - err_d(ideal) %s LSB over the four cells, "
                "spread %.4f LSB (<= 0.05); the common shift %+.4f LSB is vrlo's pedestal" % (
                    "/".join("%+.4f" % x for x in de), de.max() - de.min(), de.mean()))
        dc = [int(orl[f"code{k}"] - oi[f"code{k}"]) for k in range(4)]
        verdict(max(abs(x) for x in dc) <= 1, "codes: ideal %s, real %s (each within 1)" % (
            "/".join("%d" % oi[f"code{k}"] for k in range(4)), "/".join("%d" % orl[f"code{k}"] for k in range(4))))
        out.update(macro_shift_lsb=de.mean(), macro_spread_lsb=de.max() - de.min())
        q1 = np.array([oi.get(f"qs1_{k}", np.nan) for k in range(4)])
        q0 = np.array([oi0.get(f"qs1_{k}", np.nan) for k in range(4)])
        dv = np.array([oi.get(f"p_vin{k}", np.nan) - oi.get("p_vr_lo", np.nan) - 4.5 * oi.get("p_lsb", np.nan)
                       for k in range(4)])
        cs = (q1 - q0) / dv
        if np.all(np.isfinite(cs)):
            print("REPORT: S1 charge: signal-dependent C_sig per cell %s fF (charge at the inputs %s fC, all at "
                  "4.5 LSB %s fC); the block benches model %.0f fF x (vin - VR_LO), i.e. %s fC" % (
                      "/".join("%.2f" % (x * 1e15) for x in cs), "/".join("%.1f" % (x * 1e15) for x in q1),
                      "/".join("%.1f" % (x * 1e15) for x in q0), vr.C_EQ * 1e15,
                      "/".join("%.1f" % (vr.C_EQ * (x + 4.5 * vr.LSB) * 1e15) for x in dv)))
            out["macro_csig_max_ff"] = float(np.max(np.abs(cs))) * 1e15
            out["macro_dq_sum_fc"] = float(np.sum(q1 - q0)) * 1e15
        else:
            verdict(False, "S1 charge: the charge measures are missing from the ideal runs")
        a = [d.get("vramp_at_tr", np.nan) for d in (orl, orl0, oi, oi0)]
        kick = (a[0] - a[1]) - (a[2] - a[3])
        verdict(np.isfinite(kick) and abs(kick) <= vr.EPS, "kick: vramp at TR, inputs vs all at 4.5 LSB, real vrlo "
                "%+.4f mV, ideal %+.4f mV: the residual the regulator leaves %+.4f mV = %+.4f LSB (<= 0.05 LSB)" % (
                    (a[0] - a[1]) * 1e3, (a[2] - a[3]) * 1e3, kick * 1e3, kick / vr.LSB))
        out["macro_kick_lsb"] = kick / vr.LSB
        # the block benches' S1 model must be conservative: the same design at typical
        # on tb_tran (CEQ per cell, full-scale vs empty) leaves at least this residual
        rb = vr.tran_pair(os.path.join("macro", "block_typ"), open(NET).read(), ("typical", 27, vr.VDD), ib=ib)
        kb = abs(rb.get("kick", np.nan) - rb.get("kick_ideal", np.nan))
        verdict(np.isfinite(kb) and kb >= abs(kick), "S1 model: the block bench's kick increment at typical %.4f mV "
                ">= the macro's %.4f mV (the block gates are conservative by %.2fx)" % (
                    kb * 1e3, abs(kick) * 1e3, kb / max(abs(kick), 1e-12)))
        out["macro_block_kick_ratio"] = kb / max(abs(kick), 1e-12)
        for k in range(4):
            out[f"macro_code{k}_real"] = orl[f"code{k}"]
            out[f"macro_code{k}_ideal"] = oi[f"code{k}"]
        for n in ("vramp_at_tr", "vramp_at_ts0"):
            if n in oi and n in orl:
                out[f"macro_{n}_ideal"] = oi[n]
                out[f"macro_{n}_real"] = orl[n]
    else:
        verdict(False, "one record: measures missing (ideal %d, real %d of %d)" % (
            sum(n in oi for n in need), sum(n in orl for n in need), len(need)))
    # ---- two records
    need = [f"d{r}{k}" for r in "ab" for k in range(4)]
    if "two" not in BENCHES:
        pass
    elif all(n in ti and n in tr for n in need):
        ri = np.array([ti[f"db{k}"] - ti[f"da{k}"] for k in range(4)])
        rr = np.array([tr[f"db{k}"] - tr[f"da{k}"] for k in range(4)])
        verdict(np.max(np.abs(rr - ri)) <= 0.05, "repeat: record 2 - record 1 trip count, real %s LSB, ideal %s LSB; "
                "real - ideal worst %.4f LSB (<= 0.05)" % ("/".join("%+.4f" % x for x in rr),
                                                          "/".join("%+.4f" % x for x in ri), np.max(np.abs(rr - ri))))
        out.update(macro_rep_real_max_lsb=float(np.max(np.abs(rr))), macro_rep_ideal_max_lsb=float(np.max(np.abs(ri))),
                   macro_rep_diff_max_lsb=float(np.max(np.abs(rr - ri))))
        cb = ["%d/%d" % (tr.get(f"ca{k}", -1), tr.get(f"cb{k}", -1)) for k in range(4)]
        print("REPORT: two records, real vrlo: codes record 1/2 " + ", ".join(cb) + "; vramp before each release "
              "%.6f / %.6f V; dump peak on vrlo %.3f V (vramp %.4f V at the reset)" % (
                  tr.get("vramp_tr", np.nan), tr.get("vramp_tr2", np.nan), tr.get("vrlo_pk", np.nan),
                  tr.get("vramp_top", np.nan)))
        out.update(macro_vrlo_pk_v=tr.get("vrlo_pk", np.nan), macro_vramp_top_v=tr.get("vramp_top", np.nan))
    else:
        verdict(False, "two records: measures missing (ideal %d, real %d of %d)" % (
            sum(n in ti for n in need), sum(n in tr for n in need), len(need)))
    for k, v in out.items():
        print(f"{k} = {v:.6g}")
    json.dump(dict(one_ideal=oi, one_real=orl, two_ideal=ti, two_real=tr), open(os.path.join(vr.DATA, "macro.json"), "w"),
              indent=1)
    print(f"macro_fail_count = {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
