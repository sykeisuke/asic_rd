"""Verification of midref (midref.spice): midref_v2's divider and ONE
midref_buf, whose output is both VREF (every cell's S2 level) and VBL (every
comparator's inp). The benches are midref_v2's with the second buffer
removed; what the shared node changes is measured, not assumed.

  op     operating point at 45 PVT cells (5 corners x 0/27/85 C x 3.0/3.3/3.6 V)
         and at 0.69x / 1.77x bias (typical): follower, bias and output-diode
         headroom >= 0, |VDD/2 error| <= 50 mV
  opdev  the buffer at the bench bias (typical / 27 C / 3.3 V, ideal i_f):
         Id, gm/Id, Vgs, Vds, Vdsat, Vth of every MOS, and PDK-model replicas
         of the divider resistors and the MIM capacitors (R, C) -> the values
         written on the xschem drawings (data/op_devices.csv, op_passives.csv)
  kick   the unit cell's S2 event, both charge directions, at all 45 cells:
         the node back within 1/2 LSB in <= 250 ns and at TS; also at 0.69x and
         1.77x bias (typical). v2's VBL-crosstalk gate has no object: one node
  noise  VBL(decision) - VREF(TS) at the ADC input <= 0.080 LSB (typical, and
         at the corner cells ss/85/3.0, ff/0/3.6). One node: the noise below
         ~1/T_DEC is common to the sample and the decision and cancels. The
         same spectra give what two buffers on one tap would read (reported)
  cmp    the node as S2 level AND threshold of comparator (typical):
         trip shift from the buffer's dynamics <= 0.05 LSB against an ideal
         node; node within 1/4 LSB in the 200 ns before the trip; a
         neighbour's S2 closing on the node during the hold (both charge
         directions, the bound on any neighbour event) moves the trip by
         <= 1/4 LSB, at a mid code and close to the trip point (low code);
         whether dout falsely falls during the hold is REPORTED
  mc     the output under the PDK local mismatch, 200 draws (typical), run
         twice with the same seed (reproducible): VBL - VREF = 0 by
         construction (one node, no pedestal from the reference); the VDD/2
         offset |mean| + 3 sigma <= 50 mV, the VDD/2 error bound
  mchr   the buffer under mismatch at ff/85 C/3.6 V and ss/0 C/3.0 V (the
         ends of the FVF window), 200 draws each: |mean| + 3 sigma of the
         output error <= 50 mV; the share of draws with a follower out of
         saturation is REPORTED

    ./container.sh 'python3 verify_v3.py'            all phases
    ./container.sh 'PHASES="op kick" python3 verify_v3.py'

Prints one PASS:/FAIL: line per gate and `name = value` metrics.
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import bench as S

BLOCK = S.BLOCK
NET = os.path.join(BLOCK, os.environ.get("NETLIST", "midref.spice"))
PHASES = os.environ.get("PHASES", "op opdev kick noise cmp mc mchr").split()
N_MC = int(os.environ.get("N_MC", "200"))
CELLS = [(c, t, v) for c in S.CORNERS for t in S.TEMPS for v in S.VDD_SET]
SEED_BASE = 20261007
bad = []


def verdict(ok, text):
    print(("PASS: " if ok else "FAIL: ") + text)
    if not ok:
        bad.append(text)


def rundir(name):
    d = os.path.join(S.WORK, "verify", name)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, ".spiceinit"), "w").write("set num_threads=1\n")
    open(os.path.join(d, "dut.spice"), "w").write(open(NET).read())
    return d


def phase_op(i_f):
    jobs = [(c, t, 1.0) for c in S.CORNERS for t in S.TEMPS] + [("typical", 27, S.BIAS_LO), ("typical", 27, S.BIAS_HI)]

    def one(j):
        c, t, bs = j
        d = rundir(f"op_{c}_{t}_{bs:g}")
        open(os.path.join(d, "op.spice"), "w").write(S.fill("tb_op.spice", dict(
            CORNER=c, MIMCORNER=c if c in ("ff", "ss") else "typical", TEMP=t, IF="%.6g" % (i_f * bs),
            TAG=f"{c} {t} {bs:g}")))
        txt = S.ngspice(d, "op.spice")
        return [(m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4)),
                 [float(x) for x in m.group(5).split()])
                for m in re.finditer(r"^OP (\S+) (\S+) (\S+) (\S+) (.*)$", txt, re.M)]
    with ThreadPoolExecutor(S.JOBS) as ex:
        rows = [r for rr in ex.map(one, jobs) for r in rr]
    nom = [r for r in rows if r[2] == 1.0]
    if not nom:
        verdict(False, "op: ngspice solved no PVT cell")
        return None
    A = np.array([r[4] for r in rows])
    N = np.array([r[4] for r in nom])
    verdict(len(nom) == 45, f"op: {len(nom)} of 45 PVT cells solved (+ {len(rows) - len(nom)} bias-span points)")
    names = ("followers M1/M4", "IB sources XMIB/XMIT", "output diodes M2/M5")
    for (a, b), nm in zip(((0, 1), (2, 3), (4, 5)), names):
        k = int(np.argmin(np.minimum(A[:, a], A[:, b])))
        verdict(np.min(A[:, [a, b]]) >= 0, f"op headroom {nm}: worst |vds| - |vdsat| {np.min(A[:, [a, b]]):+.3f} V "
                f"at {rows[k][0]}/{rows[k][1]:g} C/{rows[k][3]:g} V/{rows[k][2]:g}x bias")
    k = int(np.argmin(np.minimum(A[:, 6], A[:, 7])))
    print(f"REPORT: shunts M3/M6 (allowed into triode) worst {np.min(A[:, [6, 7]]):+.3f} V at "
          f"{rows[k][0]}/{rows[k][1]:g} C/{rows[k][3]:g} V/{rows[k][2]:g}x")
    k = int(np.argmax(np.abs(N[:, 8])))
    verdict(np.max(np.abs(N[:, 8])) <= S.VERR_MAX, f"op VDD/2 error of the one output (VREF = VBL): worst "
            f"{N[k, 8] * 1e3:+.2f} mV at {nom[k][0]}/{nom[k][1]:g} C/{nom[k][3]:g} V (bound {S.VERR_MAX * 1e3:.0f} mV)")
    typ = [r for r in rows if r[0] == "typical" and r[1] == 27 and r[2] == 1.0 and r[3] == 3.3][0]
    print(f"op_err_typ_mv = {typ[4][8] * 1e3:.3f}")
    print(f"op_err_worst_mv = {N[k, 8] * 1e3:.3f}")
    print(f"op_isup_typ_ua = {typ[4][9] * 1e6:.3f}")
    print(f"op_power_typ_uw = {typ[4][9] * 3.3e6:.2f}")
    print(f"op_isup_max_ua = {np.max(N[:, 9]) * 1e6:.3f}")
    print(f"op_hr_f_min_v = {np.min(A[:, [0, 1]]):.4f}")
    print(f"REPORT: op power {typ[4][9] * 3.3e6:.1f} uW at typical/27 C/3.3 V for the whole reference "
          f"(divider + one buffer + the ideal ib); midref_v2 used two buffers on one divider")
    return float(np.max(np.abs(N[:, 8])))


OPDEV_FREQ = 1e6        # Hz, the AC point at which a MIM replica's C is read


def phase_opdev(i_f):
    """The buffer and its divider (midref) at the bench bias, typical /
    27 C / 3.3 V, the ideal i_f into ib: Id, gm, gm/Id, Vgs, Vds, Vdsat, Vth of
    every MOS (BSIM4 instance m0 inside the PDK subcircuit; [id], [gm] include
    m), and PDK-model replicas, unconnected to the buffer, of the divider
    resistors (R = 1.65 V / I) and the MIM capacitors (C from the AC current at
    OPDEV_FREQ, bias 0 V). Written to data/op_devices.csv / op_passives.csv
    for the schematic annotation."""
    net = open(NET).read()
    sub = {}
    for name in ("midref_div", "midref_buf"):
        m = re.search(r"^\.subckt %s .*?^\.ends" % name, net, re.M | re.S)
        sub[name] = [ln.split() for ln in m.group(0).splitlines()[1:-1] if ln.strip() and not ln.startswith("*")]
    devs, res, caps = [], [], []
    for t in sub["midref_buf"] + sub["midref_div"]:
        kv = dict(x.split("=", 1) for x in t if "=" in x)
        model = [x for x in t[1:] if "=" not in x][-1]
        if model.startswith(("nfet", "pfet")):
            devs.append((t[0].lower(), model, int(kv.get("m", 1))))
        elif model.startswith("ppolyf"):
            res.append((t[0], model, kv["r_width"], kv["r_length"]))
        elif model.startswith("cap_mim"):
            caps.append((t[0], model, kv["c_width"], kv["c_length"]))
    rep = []
    for nm, model, w, l in res:
        rep.append(f"VR{nm} r{nm} 0 1.65\nXR{nm}R r{nm} 0 0 {model} r_width={w} r_length={l}")
    for nm, model, w, l in caps:
        rep.append(f"VC{nm} c{nm} 0 dc 0 ac 1\nXC{nm}R c{nm} 0 {model} c_width={w} c_length={l}")
    lets, fields = [], []
    for name, _, _ in devs:
        for q in ("id", "gm", "vgs", "vds", "vdsat", "vth"):
            lets.append(f"let {name}_{q} = @m.xb.xb.{name}.m0[{q}]")
            fields.append(f"$&{name}_{q}")
    rl = "\n".join(f"let r_{nm.lower()} = 1.65 / abs(i(vr{nm.lower()}))" for nm, _, _, _ in res)
    cl = "\n".join(f"let c_{nm.lower()} = abs(imag(i(vc{nm.lower()}))) / (2 * pi * {OPDEV_FREQ:g})" for nm, _, _, _ in caps)
    deck = ("* midref device operating point at the bench bias\n"
            ".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice\n"
            ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical\n"
            ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical\n"
            ".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical\n"
            f".temp 27\n.include dut.spice\nVDD_SOURCE vdd 0 3.3\nIREF vdd ib {i_f:.6g}\nXB out ib vdd 0 midref\n"
            + "\n".join(rep) + "\n.control\nset num_threads=1\nop\n" + "\n".join(lets) + "\n" + rl + "\n"
            + "let vout = v(out)\nlet vtap = v(xb.vin)\nlet vp = v(xb.xb.p)\nlet vn = v(xb.xb.n)\nlet isup = -i(VDD_SOURCE)\n"
            + "echo \"OPDEV " + " ".join(fields) + "\"\n"
            + "echo \"OPRES " + " ".join(f"$&r_{nm.lower()}" for nm, _, _, _ in res) + " $&vout $&vtap $&vp $&vn $&isup\"\n"
            + f"ac lin 1 {OPDEV_FREQ:g} {OPDEV_FREQ:g}\n" + cl + "\n"
            + "echo \"OPCAP " + " ".join(f"$&c_{nm.lower()}" for nm, _, _, _ in caps) + "\"\nquit\n.endc\n.end\n")
    d = rundir("opdev")
    open(os.path.join(d, "opdev.spice"), "w").write(deck)
    txt = S.ngspice(d, "opdev.spice")
    m1 = re.search(r"^OPDEV (.*)$", txt, re.M)
    m2 = re.search(r"^OPRES (.*)$", txt, re.M)
    m3 = re.search(r"^OPCAP (.*)$", txt, re.M)
    if not (m1 and m2 and m3):
        verdict(False, "opdev: device operating point not solved")
        return
    v = [float(x) for x in m1.group(1).split()]
    rows = []
    for k, (name, model, mm) in enumerate(devs):
        idv, gm, vgs, vds, vdsat, vth = v[6 * k:6 * k + 6]
        rows.append(dict(dev=name, model=model, m=mm, id=abs(idv), gm=abs(gm),
                         gmid=abs(gm) / abs(idv) if idv else float("nan"),
                         vgs=abs(vgs), vds=abs(vds), vdsat=abs(vdsat), vth=abs(vth)))
    with open(os.path.join(S.DATA, "op_devices.csv"), "w") as h:
        h.write("dev,model,m,id,gm,gmid,vgs,vds,vdsat,vth\n")
        for r in rows:
            h.write(f"{r['dev']},{r['model']},{r['m']}," + ",".join("%.6g" % r[q] for q in
                    ("id", "gm", "gmid", "vgs", "vds", "vdsat", "vth")) + "\n")
    rv = [float(x) for x in m2.group(1).split()]
    cv = [float(x) for x in m3.group(1).split()]
    nodes = dict(zip(("v_out", "v_tap", "v_p", "v_n", "i_vdd"), rv[len(res):]))
    with open(os.path.join(S.DATA, "op_passives.csv"), "w") as h:
        h.write("name,model,value,unit,note\n")
        for (nm, model, _, _), r in zip(res, rv):
            h.write(f"{nm},{model},{r:.6g},ohm,replica at 1.65 V\n")
        for (nm, model, _, _), c in zip(caps, cv):
            h.write(f"{nm},{model},{c:.6g},F,replica AC at {OPDEV_FREQ:g} Hz\n")
        for k, x in nodes.items():
            h.write(f"{k},,{x:.6g},{'A,supply current of the buffer + its divider incl. the ideal ib' if k == 'i_vdd' else 'V,node'}\n")
    print(f"opdev_isup_ua = {nodes['i_vdd'] * 1e6:.3f}")
    for r in rows:
        print(f"opdev_{r['dev']}_id_ua = {r['id'] * 1e6:.4f}")
        print(f"opdev_{r['dev']}_gmid = {r['gmid']:.3f}")
    for (nm, _, _, _), r in zip(res, rv):
        print(f"opdev_r_{nm.lower()}_kohm = {r / 1e3:.3f}")
    for (nm, _, _, _), c in zip(caps, cv):
        print(f"opdev_c_{nm.lower()}_ff = {c * 1e15:.2f}")
    g = {r["dev"]: r for r in rows}
    print(f"REPORT: opdev (typical/27 C/3.3 V, ideal ib {i_f * 1e6:.3f} uA): M1 {g['xm1']['id'] * 1e6:.2f} uA gm/Id "
          f"{g['xm1']['gmid']:.2f}, M4 {g['xm4']['id'] * 1e6:.2f} uA gm/Id {g['xm4']['gmid']:.2f}, M3 "
          f"{g['xm3']['id'] * 1e6:.2f} uA, M6 {g['xm6']['id'] * 1e6:.2f} uA; "
          + ", ".join(f"{nm} {r / 1e3:.1f} kohm" for (nm, _, _, _), r in zip(res, rv)) + "; "
          + ", ".join(f"{nm} {c * 1e15:.1f} fF" for (nm, _, _, _), c in zip(caps, cv))
          + " [M, ngspice; data/op_devices.csv, data/op_passives.csv]")
    verdict(len(rows) == len(devs) and all(np.isfinite(r["gmid"]) for r in rows),
            f"opdev: {len(rows)} MOS, {len(res)} resistors and {len(caps)} MIM caps read at the bench bias")


def kick_subs(i_f, cell, prefix="k"):
    c, t, v = cell
    return dict(S.cell_subs(cell), IF="%.6g" % i_f, P=prefix,
                TOP1="%.4f" % (v / 2 + 1.34), TOP2="%.4f" % (v / 2 + 0.10))


def phase_kick(i_f):
    jobs = [(cell, 1.0) for cell in CELLS] + [(("typical", 27, 3.3), S.BIAS_LO), (("typical", 27, 3.3), S.BIAS_HI)]

    def one(j):
        cell, bs = j
        d = rundir("kick_%s_%g_%g_%g" % (cell + (bs,)))
        open(os.path.join(d, "kick.spice"), "w").write(S.fill("tb_kick.spice", kick_subs(i_f * bs, cell)))
        return cell, bs, S.grab(S.ngspice(d, "kick.spice"))
    with ThreadPoolExecutor(S.JOBS) as ex:
        res = list(ex.map(one, jobs))
    worst_ts, worst_rr, nok, rows = 0.0, 0.0, 0, []
    for cell, bs, r in res:
        ok = True
        for c in (1, 2):
            pk = r.get(f"k_c{c}_pkr_mv", np.nan)
            ts = r.get(f"k_c{c}_tsr_ns", 0.0 if pk == pk and pk < S.EPS * 1e3 else np.nan)
            rr = max(r.get(f"k_c{c}_rr250_mv", np.nan), r.get(f"k_c{c}_rr300_mv", np.nan))
            q = abs(r.get(f"k_c{c}_qk_fc", 0.0))
            ok &= ts <= S.TS_MAX * 1e9 and rr <= S.EPS * 1e3 and q >= 50
            worst_ts, worst_rr = max(worst_ts, np.nan_to_num(ts, nan=1e9)), max(worst_rr, np.nan_to_num(rr, nan=1e9))
            rows.append(dict(corner=cell[0], temp=cell[1], vdd=cell[2], bias=bs, case=c, pk_mv=pk, ts_ns=ts,
                             rr_mv=rr, q_fc=r.get(f"k_c{c}_qk_fc", np.nan)))
        nok += ok
    verdict(nok == len(jobs), f"kick: {nok} of {len(jobs)} cells (45 PVT + 0.69x/1.77x bias) hold both S2 cases: "
            f"worst return to 1/2 LSB {worst_ts:.0f} ns (limit {S.TS_MAX * 1e9:.0f}), worst residual "
            f"{worst_rr:.3f} mV at 250/300 ns (limit {S.EPS * 1e3:.2f})")
    print(f"kick_ts_worst_ns = {worst_ts:.1f}")
    print(f"kick_pk_worst_mv = {max(x['pk_mv'] for x in rows):.3f}")
    typ = [x for x in rows if x["corner"] == "typical" and x["temp"] == 27 and x["vdd"] == 3.3 and x["bias"] == 1.0]
    for x in typ:
        print(f"kick_typ_c{x['case']}_ts_ns = {x['ts_ns']:.1f}")
        print(f"kick_typ_c{x['case']}_pk_mv = {x['pk_mv']:.3f}")
        print(f"kick_typ_c{x['case']}_q_fc = {x['q_fc']:.1f}")
    json.dump(rows, open(os.path.join(S.DATA, "verify_kick.json"), "w"), indent=1, default=float)


def phase_noise(i_f):
    cells = [("typical", 27, 3.3), ("ss", 85, 3.0), ("ff", 0, 3.6)]
    for c, t, v in cells:
        d = rundir(f"noise_{c}_{t}_{v:g}")
        txt = S.fill("tb_noise.spice", dict(IF="%.6g" % i_f))
        txt = txt.replace("sm141064.ngspice typical", f"sm141064.ngspice {c}") \
                 .replace("mimcap_typical", "mimcap_" + (c if c in ("ff", "ss") else "typical")) \
                 .replace("VDD_SOURCE vdd 0 3.3", f".temp {t}\nVDD_SOURCE vdd 0 {v:g}")
        open(os.path.join(d, "noise.spice"), "w").write(txt)
        S.ngspice(d, "noise.spice")
        r = S.noise_from_files(d)
        tag = f"{c}_{t}_{v:g}".replace(".", "p")
        if not r:
            verdict(False, f"noise {c}/{t} C/{v:g} V: ngspice produced no spectra")
            continue
        verdict(r["nz_lsb"] <= S.NOISE_MAX_LSB, f"noise {c}/{t} C/{v:g} V: VBL(decision) - VREF(TS) on the one node "
                f"{r['nz_lsb']:.4f} LSB at the ADC input (allocation {S.NOISE_MAX_LSB}); two buffers on one tap "
                f"(midref_v2's wiring, same spectra) {r['nz_two_lsb']:.4f} LSB; output {r['nz_out_uv']:.1f} uV rms "
                f"10 Hz-1 GHz, of which the divider {r['nz_tap_out_uv']:.1f} uV")
        print(f"noise_{tag}_lsb = {r['nz_lsb']:.5f}")
        print(f"noise_{tag}_two_lsb = {r['nz_two_lsb']:.5f}")
        print(f"noise_{tag}_out_uv = {r['nz_out_uv']:.2f}")


# the cmp runs: (name, vdrop, src, agg); vdrop 0.15 V = trip 33.6 LSB into the ramp,
# 0.012 V = 2 LSB (the comparator close to its trip point through the hold)
CMP_RUNS = [("a", 0.15, 1, 0), ("b", 0.15, 0, 0), ("c1", 0.15, 1, 1), ("c2", 0.15, 1, 2),
            ("lo_a", 0.012, 1, 0), ("lo_c1", 0.012, 1, 1), ("lo_c2", 0.012, 1, 2)]


def cmp_deck(i_f, vdrop, src, agg, v0):
    top = {0: S.VDD / 2 + 1.34, 1: S.VDD / 2 + 1.34, 2: S.VDD / 2 + 0.10}[agg]
    vfe = {0: 2.0, 1: 2.0, 2: 0.5}[agg]
    return S.fill("tb_cmp.spice", dict(IF="%.6g" % i_f, VDROP="%g" % vdrop, SRC_B=2 * src, SRC_I=2 * (1 - src),
                                       V0="%.9g" % v0, AGGON=1 if agg else 0, TOPA0="%.4f" % top, VFEA1="%g" % vfe))


def phase_cmp(i_f):
    def run(name, vdrop, src, agg, v0):
        d = rundir("cmp_" + name)
        open(os.path.join(d, "cmp.spice"), "w").write(cmp_deck(i_f, vdrop, src, agg, v0))
        return name, S.grab(S.ngspice(d, "cmp.spice"))
    a = run("a", 0.15, 1, 0, S.VDD / 2)[1]
    if "cmp_v0_v" not in a:
        verdict(False, "cmp: the buffer run produced no measures")
        return
    v0 = a["cmp_v0_v"]
    with ThreadPoolExecutor(S.JOBS) as ex:
        r = dict(ex.map(lambda x: run(*x, v0), [x for x in CMP_RUNS if x[0] != "a"]))
    r["a"] = a
    need = [n for n, *_ in CMP_RUNS if "cmp_td_ns" not in r.get(n, {})]
    if need:
        verdict(False, "cmp: no decision in run(s) " + " ".join(need))
        return
    td = {n: r[n]["cmp_td_ns"] for n in r}
    dt = (td["a"] - td["b"]) / 50.0
    verdict(abs(dt) <= S.CMP_DT_MAX, "decision on the shared node: dout falls at %.2f ns on the buffer, %.2f ns on an "
            "ideal node at the same level; trip shift %+.4f LSB (limit %.2f)" % (td["a"], td["b"], dt, S.CMP_DT_MAX))
    verdict(r["a"]["cmp_pkpre_uv"] <= S.LSB / 4 * 1e6, "decision: node within %.1f uV of its level in the 200 ns "
            "before the trip (limit %.0f uV = 1/4 LSB); %.1f uV over the conversion" % (
                r["a"]["cmp_pkpre_uv"], S.LSB / 4 * 1e6, r["a"]["cmp_pkall_uv"]))
    print(f"cmp_dt_lsb = {dt:.5g}")
    print(f"cmp_pkpre_uv = {r['a']['cmp_pkpre_uv']:.5g}")
    print(f"cmp_pkall_uv = {r['a']['cmp_pkall_uv']:.5g}")
    for lvl, base in (("mid code (33.6 LSB)", "a"), ("low code (2 LSB)", "lo_a")):
        pre = "" if base == "a" else "lo_"
        sh = [(td[pre + c] - td[base]) / 50.0 for c in ("c1", "c2")]
        worst = max(abs(x) for x in sh)
        verdict(worst <= S.XT_MAX_LSB, "hold, %s: a neighbour's S2 closing on the node 50 ns into the hold moves "
                "the trip by %+.4f / %+.4f LSB (sinking / sourcing case; limit %.2f LSB)" % (lvl, sh[0], sh[1], S.XT_MAX_LSB))
        for c in ("c1", "c2"):
            x = r[pre + c]
            print(f"REPORT: hold {lvl} {c}: node peak {x['cmp_pkhold_mv']:.2f} mV over the hold, lowest dout "
                  f"{x['cmp_doutmin_v']:.3f} V ({'FALSE dout fall during the hold' if x['cmp_doutmin_v'] < 1.65 else 'no false decision'})")
            print(f"cmp_hold_{pre}{c}_shift_lsb = {(td[pre + c] - td[base]) / 50.0:.5g}")
            print(f"cmp_hold_{pre}{c}_pk_mv = {x['cmp_pkhold_mv']:.4g}")
            print(f"cmp_hold_{pre}{c}_doutmin_v = {x['cmp_doutmin_v']:.4g}")


def mc_draws(tpl, tag, subs, pat):
    """N_MC + 1 runs of a one-draw template: draw 0 mismatch-free, draw k with
    seed SEED_BASE + k. Returns rows in draw order (k, values...)."""
    def one(k):
        d = rundir(f"{tag}_{k}")
        open(os.path.join(d, "mc.spice"), "w").write(S.fill(tpl, dict(subs, MM=0 if k == 0 else 1,
                                                                        SEED=SEED_BASE + k, K=k)))
        m = re.search(pat, S.ngspice(d, "mc.spice"), re.M)
        return [float(x) for x in m.groups()] if m else None
    with ThreadPoolExecutor(S.JOBS) as ex:
        rows = list(ex.map(one, range(N_MC + 1)))
    return np.array([r for r in rows if r is not None])


def phase_mc(i_f, err_pvt):
    out = []
    for run in (1, 2):
        out.append(mc_draws("tb_mc.spice", f"mc{run}", dict(
            CORNER="typical", MIMCORNER="typical", TEMP=27, VDD="3.3", IF="%.6g" % i_f), r"^MC (\S+) (\S+)$"))
    a, b = out
    verdict(a.shape[0] == N_MC + 1, f"mc: {a.shape[0] - 1} of {N_MC} draws solved")
    same = a.shape == b.shape and np.allclose(a, b, atol=1e-9)
    verdict(same, "mc: a second run with the same seeds reproduces every draw (.options seed per draw)")
    verdict(a.shape[0] > 2 and np.std(a[1:, 1]) > 0, "mc: the draws differ from each other (mismatch is applied)")
    if a.shape[0] < 3:
        return
    e = a[1:, 1]
    sig, mu = float(np.std(e, ddof=1)), float(np.mean(e))
    verdict(abs(mu) + 3 * sig <= S.VERR_MAX, f"mc: VDD/2 offset of the one output, sigma {sig * 1e3:.3f} mV, mean "
            f"{mu * 1e3:+.3f} mV, |mean| + 3 sigma {(abs(mu) + 3 * sig) * 1e3:.2f} mV (bound {S.VERR_MAX * 1e3:.0f} mV); "
            f"VBL - VREF = 0 in every draw (one node: no reference pedestal; midref_v2's two buffers had sqrt(2) x this)")
    if err_pvt is not None:
        print(f"REPORT: mc: worst PVT VDD/2 error {err_pvt * 1e3:.2f} mV + 3 sigma {3 * sig * 1e3:.2f} mV = "
              f"{(err_pvt + 3 * sig) * 1e3:.2f} mV against the {S.VERR_MAX * 1e3:.0f} mV bound")
    print(f"mc_sigma_out_mv = {sig * 1e3:.4f}")
    print(f"mc_mean_out_mv = {mu * 1e3:.4f}")
    print(f"mc_sigma_v2pair_lsb = {np.sqrt(2) * sig / S.ALPHA / S.LSB:.4f}")
    np.savetxt(os.path.join(S.DATA, "mc_typ.csv"), a, delimiter=",", header="k,vout_err_v", comments="")


def phase_mchr(i_f):
    for c, t, v in (("ff", 85, 3.6), ("ss", 0, 3.0)):
        a = mc_draws("tb_mchr.spice", f"mchr_{c}_{t}", dict(
            CORNER=c, MIMCORNER=c, TEMP=t, VDD="%g" % v, IF="%.6g" % i_f), r"^HR (\S+) (\S+) (\S+) (\S+)$")
        if a.shape[0] < 3:
            verdict(False, f"mc headroom {c}/{t} C/{v:g} V: ngspice produced no draws")
            continue
        h = np.minimum(a[1:, 1], a[1:, 2])
        nbad = int(np.sum(h < 0))
        print(f"REPORT: mc {c}/{t} C/{v:g} V: followers saturated in {h.size - nbad} of {h.size} mismatch draws; "
              f"worst headroom {h.min():+.3f} V (M1 {a[1:, 1].min():+.3f}, M4 {a[1:, 2].min():+.3f}), nominal "
              f"{min(a[0, 1], a[0, 2]):+.3f} V, sigma {np.std(h, ddof=1) * 1e3:.1f} mV")
        e = a[1:, 3]
        se, mu = float(np.std(e, ddof=1)), float(np.mean(e))
        verdict(abs(mu) + 3 * se <= S.VERR_MAX, f"mc {c}/{t} C/{v:g} V: output error sigma {se * 1e3:.3f} mV, mean "
                f"{mu * 1e3:+.2f} mV, |mean| + 3 sigma {(abs(mu) + 3 * se) * 1e3:.2f} mV (bound {S.VERR_MAX * 1e3:.0f} mV), "
                f"worst draw {np.max(np.abs(e)) * 1e3:.2f} mV")
        print(f"mchr_{c}_hr_min_v = {h.min():.4f}")
        print(f"mchr_{c}_triode_draws = {nbad}")
        print(f"mchr_{c}_sigma_out_mv = {se * 1e3:.4f}")


def main():
    i_f = S.I_F
    print(f"REPORT: verifying {os.path.basename(NET)}: one midref_buf on midref_div, its output = VREF = VBL; "
          f"i_f {i_f * 1e6:.4g} uA (midref_v2's sizing, data/sizing_v2.json)")
    err_pvt = None
    if "op" in PHASES:
        print("REPORT: phase op")
        err_pvt = phase_op(i_f)
    for ph, fn in (("opdev", lambda: phase_opdev(i_f)), ("kick", lambda: phase_kick(i_f)),
                   ("noise", lambda: phase_noise(i_f)), ("cmp", lambda: phase_cmp(i_f)),
                   ("mc", lambda: phase_mc(i_f, err_pvt)), ("mchr", lambda: phase_mchr(i_f))):
        if ph in PHASES:
            print(f"REPORT: phase {ph}")
            fn()
    print(f"verify_fail_count = {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
