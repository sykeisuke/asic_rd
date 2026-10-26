#!/usr/bin/env python3
"""op_reduce.py -- reduce the op phase's ngspice measures to the in-macro
operating point. Reads work/op/ngspice.out (`name = value` echoes of tb_op.inc)
and the generated analog_top.spice (device sizes). Writes

  data/op_measures.txt   every op measure, `name = value`
  data/op_point.csv      one row per MOS x state: Id, gm, gds, gmbs, Vgs, Vds,
                         Vth, Vdsat, gm/Id, Vov = |Vgs| - |Vth|,
                         |Vds| - |Vdsat|, region, W/L/nf/m
  data/op_rc.csv         switch Ron (1 / sum gds while closed), resistors
                         (R = V / I), MIM capacitors (model readback and the PDK
                         formula)

Region: off if Vov <= 0 and |Id| < 1 pA; triode if |Vds| <= Vdsat (BSIM4
vdsat; "switch on" when |Vds| < 1 mV); else sat, with the inversion level by
gm/Id: weak > 20 /V, moderate 10..20, strong < 10. ngspice's BSIM4 reports
id, vgs, vds, vth, vdsat type-normalised (positive for a PMOS as well), so
Vov = Vgs - Vth for both types.
These are RECORDED (REPORT: lines, a few `op_*` scalars), not judged. Gated are
only the self-consistency checks that make the numbers trustworthy:
  * every measure present
  * KCL in bias_gen's core (|Id XMP2| = |Id XMN2|, one m=1 and one m=4
    device: id includes the multiplier) and in cell 0's comparator
    (|Id XTAIL| = |Id XINP| + |Id XINN|), within 0.1 %
  * the five series R of bias_gen carry one current within 0.1 %
  * every MIM's model capacitance equals the PDK formula within 0.01 %
"""
import csv
import datetime
import math
import os
import re
import sys

from check_equiv import flatten, parse
from op_devices import KCL_EXTRA, MIM, MOS, PARAMS, RES, STATES, SWITCHES, mim_formula

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "op", "ngspice.out")
fails = 0


def verdict(ok, text):
    global fails
    print(("PASS: " if ok else "FAIL: ") + "op: " + text)
    if not ok:
        fails += 1


def main():
    m = {}
    # ngspice pads a measure name to 20 columns: "op_x_trk_id =  1.2e-06" or "op_longer_name=  1.2e-06"
    for ln in open(OUT, errors="replace"):
        mm = re.match(r"^(op_\w+?)\s*=\s*(\S+)", ln)
        if mm:
            try:
                m[mm.group(1)] = float(mm.group(2))
            except ValueError:
                m[mm.group(1)] = float("nan")
    with open(os.path.join(HERE, "data", "op_measures.txt"), "w") as f:
        for k, v in m.items():
            f.write("%s = %.6e\n" % (k, v))
    need = (len(MOS) * len(STATES) * len(PARAMS) + 3 * len(RES) * len(STATES) + len(MIM)
            + len(KCL_EXTRA) * len(STATES))
    nan = [k for k, v in m.items() if math.isnan(v)]
    verdict(len(m) == need and not nan, "%d of %d operating-point measures present%s"
            % (len(m), need, (", non-numeric: " + " ".join(nan[:5])) if nan else ""))
    devs, _ = flatten(parse(os.path.join(HERE, "analog_top.spice")))
    rs = {}
    for ln in open(os.path.join(HERE, "..", "ramp_gen", "data", "ramp_simple_params.spice")):
        mm = re.match(r"\.param\s+(RS_\w+)=([\d.]+)(u?)", ln)
        if mm:
            rs[mm.group(1).lower()] = mm.group(2) + mm.group(3)

    def size(path):
        d = devs[path]["params"]
        def g(k):
            v = d.get(k, "?")
            return rs.get(v, v) if v.startswith("rs_") else v
        def um(v):
            try:
                return "%.4g" % (float(v) * 1e6)
            except ValueError:
                return v.rstrip("u")
        return um(g("w")), um(g("l")), g("nf"), d.get("m", "1"), devs[path]["model"]

    rows = []
    for key, path, blk, role, shown in MOS:
        w, l, nf, mult, model = size(path)
        sgn = 1   # ngspice's BSIM4 reports vgs, vds, vth, vdsat, id type-normalised (positive for a PMOS too)
        for st in STATES:
            g = lambda p: m.get("op_%s_%s_%s" % (key, st, p), float("nan"))
            idv, gm, gds = g("id"), g("gm"), g("gds")
            vov = sgn * (g("vgs") - g("vth"))
            hr = abs(g("vds")) - abs(g("vdsat"))
            gmid = gm / abs(idv) if abs(idv) > 0 else float("nan")
            if vov <= 0 and abs(idv) < 1e-12:
                reg = "off"                      # below threshold and no current (an open switch side)
            elif hr <= 0:
                reg = "triode" + (" (switch on)" if abs(g("vds")) < 1e-3 else "")
            else:
                inv = "weak" if gmid > 20 else ("moderate" if gmid >= 10 else "strong")
                reg = "sat " + inv
            rows.append(dict(key=key, state=st, device=path, block=blk, role=role, model=model, w_um=w, l_um=l,
                             nf=nf, m=mult, id=idv, gm=gm, gds=gds, gmbs=g("gmbs"), vgs=g("vgs"), vds=g("vds"),
                             vth=g("vth"), vdsat=g("vdsat"), gm_id=gmid, vov=vov, vds_vdsat=hr, region=reg,
                             shown=int(st == shown)))
    stamp = "generated %s UTC by op_reduce.py from work/op/ngspice.out (op phase)" % \
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    with open(os.path.join(HERE, "data", "op_point.csv"), "w", newline="") as f:
        f.write("# " + stamp + "\n")
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: ("%.6g" % v if isinstance(v, float) else v) for k, v in r.items()})
    byk = {(r["key"], r["state"]): r for r in rows}

    # ---- self-consistency
    for st in STATES:
        # pb: XMP2 (diode, m 1) sources what XMN2 (m 4) sinks at its DRAIN terminal: the channel current id
        # plus the drain-side substrate (impact ionisation) and GIDL currents, which bypass its source and R
        a = abs(byk[("bg_xmp2", st)]["id"])
        ch = abs(byk[("bg_xmn2", st)]["id"])
        ex = sum(m.get("op_kcl_%s_%s" % (k, st), float("nan")) for k, _ in KCL_EXTRA)
        b = ch + ex
        verdict(abs(a - b) <= 1e-3 * a, "%s: KCL at bias_gen_s pb: |Id XMP2| %.5g uA = XMN2 (m 4) id %.5g + isub + igidl "
                "%.4g nA = %.5g uA (%.3g %%; id alone %.3g %%)"
                % (st, a * 1e6, ch * 1e6, ex * 1e9, b * 1e6, 100 * (b - a) / a, 100 * (ch - a) / a))
        t = abs(byk[("c0_xtail", st)]["id"])
        p = abs(byk[("c0_xinp", st)]["id"]) + abs(byk[("c0_xinn", st)]["id"])
        verdict(abs(t - p) <= 1e-3 * t, "%s: KCL at cell 0 comparator tail: |Id XTAIL| %.5g uA = |Id XINP| + |Id XINN| %.5g uA"
                % (st, t * 1e6, p * 1e6))
    rc = []
    for name, keys, st in SWITCHES:
        g = sum(byk[(k, st)]["gds"] for k in keys)
        rc.append(dict(kind="ron", name=name, role="+".join(keys), state=st, value=1 / g, v="", i="", formula=""))
    ir = []
    for key, path, a, b, role in RES:
        for st in STATES:
            i = m.get("op_%s_%s_i" % (key, st), float("nan"))
            v = m.get("op_%s_%s_va" % (key, st), float("nan")) - m.get("op_%s_%s_vb" % (key, st), float("nan"))
            if st == "ramp":
                rc.append(dict(kind="res", name=path.split(".")[-1].upper() + " " + path.split(".")[0],
                               role=role, state=st, value=v / i, v=v, i=i, formula=""))
            if key.startswith("bg_xr") and st == "ramp":
                ir.append(i)
    verdict(max(ir) - min(ir) <= 1e-3 * abs(max(ir)),
            "ramp: the five bias_gen_s R carry one current, %.5g .. %.5g uA" % (min(ir) * 1e6, max(ir) * 1e6))
    worst = 0
    rsw = float(rs.get("rs_cw", "nan").rstrip("u")) * 1e-6     # RS_CW from ramp_simple_params.spice
    for key, path, w, l, role in MIM:
        if key == "rp_xcr":
            w = l = rsw
        c = m.get("op_cap_%s" % key, float("nan"))
        fo = mim_formula(w, l)
        worst = max(worst, abs(c / fo - 1))
        rc.append(dict(kind="cap", name=path.split(".")[-1].upper() + " " + path.split(".")[0], role=role,
                       state="", value=c, v="", i="", formula=fo))
    verdict(worst <= 1e-4, "every MIM's model capacitance equals the PDK formula 1.99e-3 A + 2.383e-10 P "
            "(sm141064_mim.ngspice, typical) within %.2g %%" % (worst * 100))
    with open(os.path.join(HERE, "data", "op_rc.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["kind", "name", "role", "state", "value", "v", "i", "formula"])
        wr.writeheader()
        for r in rc:
            wr.writerow({k: ("%.6g" % v if isinstance(v, float) else v) for k, v in r.items()})

    # ---- recorded: one REPORT line per device at its shown state, scalars for key devices
    for r in rows:
        if not r["shown"]:
            continue
        print("REPORT: op: %s %-22s %-5s Id %+.4g uA, gm %.4g uS, gm/Id %.1f /V, gds %.4g uS, Vgs %+.3f, Vds %+.3f, "
              "Vth %+.3f, Vov %+.0f mV, |Vds|-Vdsat %+.0f mV, %s (%s, W/L %s/%s nf %s m %s)"
              % (r["device"], r["role"][:22], r["state"], r["id"] * 1e6, r["gm"] * 1e6, r["gm_id"], r["gds"] * 1e6,
                 r["vgs"], r["vds"], r["vth"], r["vov"] * 1e3, r["vds_vdsat"] * 1e3, r["region"], r["model"],
                 r["w_um"], r["l_um"], r["nf"], r["m"]))
        if r["key"] in ("c0_xinp", "c0_xinn", "c0_xtail", "c0_xloadd", "c0_xrefp", "rp_xps", "rp_xrd", "bg_xmn1",
                        "bg_xmn2", "bg_xmp2", "bg_xoc0", "bg_xor", "bg_xov", "bg_xol", "vl_xmbn", "vl_xmk", "vl_xms", "vl_xm1", "vr_xm1", "vr_xm4", "vr_xm2", "vr_xm5"):
            print("op_%s_%s_id_ua = %.6g" % (r["key"], r["state"], r["id"] * 1e6))
            print("op_%s_%s_gm_id = %.6g" % (r["key"], r["state"], r["gm_id"]))
            print("op_%s_%s_vds_vdsat_mv = %.6g" % (r["key"], r["state"], r["vds_vdsat"] * 1e3))
    for r in rc:
        if r["kind"] == "ron":
            print("REPORT: op: Ron %s (%s, closed): %.5g kohm" % (r["name"], r["state"], r["value"] / 1e3))
        elif r["kind"] == "res":
            print("REPORT: op: R %s %s: %.6g kohm (V %.4f mV / I %.5g uA)" % (r["name"], r["role"], r["value"] / 1e3,
                                                                          r["v"] * 1e3, r["i"] * 1e6))
        else:
            print("REPORT: op: C %s %s: %.6g fF (formula %.6g fF)" % (r["name"], r["role"], r["value"] * 1e15,
                                                                   r["formula"] * 1e15))
        tag = re.sub(r"[^a-z0-9]+", "_", (r["kind"] + "_" + r["name"]).lower()).strip("_")
        print("op_%s = %.6g" % (tag, r["value"]))
    print("Data: /foss/designs/mixed_signal/Analog_top/data/op_point.csv")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
