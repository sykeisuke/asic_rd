"""bias_gen verification (ngspice). Every gate prints one PASS:/FAIL: line.

    ./container.sh 'PHASES="op opdev startup mc noise cmp xtalk midref" python3 -u verify_bg.py'

Phases
  op       135 cells (5 MOS corners x 0/27/85 C x 3.0/3.3/3.6 V x res_typ/ss/ff):
           every output into its consumer's diode, saturation of every matched
           device, startup node, bleeder current; the comparator output against
           comparator's per-cell requirement x (1 + 3 sigma)
  opdev    one cell (typical / 27 C / res_typical / 3.3 V, consumer diodes as
           loads): Id, gm/Id, Vgs, Vds, Vdsat, Vth of every MOS, and PDK-model
           replicas of the resistor string and the MIM decaps (R, C) -> the
           values written on the xschem drawing (data/op_devices.csv,
           data/op_passives.csv)
  startup  100 ns / 10 us / 1 ms supply ramps and a forced dead state at the
           45 MOS cells x 3 resistor corners; the kick-less control stays dead
  mc       200 local-mismatch draws at typical (one draw per process, seed
           BASE + k; draw 0 mismatch-free), twice for reproducibility: sigma of
           the comparator output (all four), the core, ramp, midref
  noise    voltage noise on the ramp's mirror line: this generator's iramp into
           the ramp's diode vs the old bias_gen's pbias line (the ramp's current
           noise source in ramp_gen RESULTS), and the old ramp-noise share scaled
  cmp      comparator (drawn S/D geometry) with its local diode on icmp0 of
           this generator: delay from the static trip at 4.5 and 40.5 LSB <= 12.5 ns
           at all 135 cells (comparator's own benches, read by path)
  xtalk    four comparator on this generator; three aggressors decide 1 LSB
           before the victim: victim decision shift <= 0.1 LSB (comparator_updt
           SPEC item 20), typical and two corners
  midref   midref_v2 (shared divider, two buffers) on ivref / ivbl: follower,
           IB-source and output-diode headroom and VDD/2 error at 135 cells
           (midrail_ref_v2's tb_op), and its S2-kick bench at the low- and
           high-current cells (midrail_ref_v2's tb_kick)

Results: data/verify_*.csv / .json. The simulators are the authority.
"""
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bg  # noqa: E402

PHASES = os.environ.get("PHASES", "op opdev startup mc noise cmp xtalk midref").split()
JOBS = int(os.environ.get("JOBS", "12"))
N_MC = int(os.environ.get("N_MC", "200"))
SEED_BASE = 20261007
N_SIGMA = 3.0
HR_MIN = 0.05                     # V, |vds| - |vdsat| of every matched device [A]
SU_MAX = 0.3                      # V, startup node while running: kick off [A]
BLEED_MAX = 1.0e-6                # A, bleeder current, any cell [A]
XTALK_MAX_LSB = 0.1               # [C] comparator_updt SPEC item 20
LSB_T = 50e-9                     # one count
TRAPZ = getattr(np, "trapezoid", None) or np.trapz
DATA = os.path.join(bg.BLOCK, "data")
WORK = os.path.join(bg.BLOCK, "work", "verify")
GEN = os.path.join(bg.BLOCK, "bias_gen.spice")
CMP_BLOCK = os.path.join(bg.BLOCK, "..", "comparator")
MR_BLOCK = os.path.join(bg.BLOCK, "ref", "midrail_ref_v2")
OLD_BG = os.path.join(bg.BLOCK, "ref", "bias_gen_v1")

SIZ = json.load(open(os.path.join(DATA, "sizing.json")))
for _k in ("K", "na", "npm", "nc", "nr", "nm", "nbl", "rseg"):
    SIZ[_k] = int(SIZ[_k])
CELLS = [(c, t, rc) for c in bg.CORNERS for t in bg.TEMPS for rc in bg.RCORNERS]


def verdict(ok, text):
    print(("PASS: " if ok else "FAIL: ") + text)
    return ok


def rundir(*parts):
    d = os.path.join(WORK, *parts)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, ".spiceinit"), "w") as h:     # one OpenMP thread (ngspice-num-threads trap)
        h.write("set num_threads=1\n")
    return d


def pmap(fn, jobs):
    with ThreadPoolExecutor(JOBS) as ex:
        return list(ex.map(fn, jobs))


def tag(c, t, rc, v=None):
    return f"{c}/{t:g}C/{rc.replace('res_', 'r')}" + (f"/{v:g}V" if v is not None else "")


# ------------------------------------------------------------------ op
def op_rows():
    def one(j):
        c, t, rc = j
        return bg.parse_op(bg.run(rundir("op", f"{c}_{t:g}_{rc}"), bg.op_deck(SIZ, (c, t), rc, GEN)), SIZ)
    return [r for rr in pmap(one, CELLS) for r in rr]


def phase_op():
    rows = op_rows()
    verdict(len(rows) == 135, f"op: {len(rows)} of 135 cells solved")
    if not rows:
        return None
    req = bg.bias_req()
    typ = [r for r in rows if r["corner"] == "typical" and r["temp"] == 27 and r["rcorner"] == "res_typical"
           and r["vdd"] == 3.3][0]
    print(f"op_icmp_typ_ua = {typ['ic'] * 1e6:.4f}")
    print(f"op_scale_cmp_typ = {typ['ic'] / bg.I_CMP_NOM:.4f}")
    print(f"op_iramp_typ_ua = {typ['ir'] * 1e6:.4f}")
    print(f"op_imr_typ_ua = {typ['iv'] * 1e6:.4f}")
    print(f"op_scale_mr_typ = {typ['iv'] / bg.I_MR_NOM:.4f}")
    print(f"op_icore_typ_ua = {typ['icore'] * 1e6:.4f}")
    gen_i = typ["isup"] - typ["ic"] * 0       # supply current of the generator incl. what it delivers
    print(f"op_isup_typ_ua = {typ['isup'] * 1e6:.3f}")
    # generator's own consumption: supply minus the source currents it delivers to midref
    own = typ["isup"] - 2 * typ["iv"]
    print(f"op_own_power_typ_uw = {own * 3.3e6:.2f}")
    print(f"REPORT: typical: comparator sink {typ['ic'] * 1e6:.4f} uA ({typ['ic'] / bg.I_CMP_NOM:.3f} x 1.931), "
          f"ramp {typ['ir'] * 1e6:.4f} uA ({100 * (typ['ir'] / bg.I_RAMP_NOM - 1):+.2f} % of 3.1314), midref "
          f"{typ['iv'] * 1e6:.3f} uA ({typ['iv'] / bg.I_MR_NOM:.3f} x 12.36), core {typ['icore'] * 1e6:.3f} uA; "
          f"supply {typ['isup'] * 1e6:.2f} uA incl. the {2 * typ['iv'] * 1e6:.2f} uA sourced into the midref diodes")
    for key, nom, name in (("ic", typ["ic"], "comparator"), ("ir", bg.I_RAMP_NOM, "ramp"), ("iv", bg.I_MR_NOM, "midref")):
        m = np.array([r[key] / nom for r in rows])
        k1, k2 = int(np.argmin(m)), int(np.argmax(m))
        print(f"REPORT: {name} output over 135 cells: {m.min():.3f} .. {m.max():.3f} x "
              f"{'typical' if key == 'ic' else 'nominal'} (low {tag(rows[k1]['corner'], rows[k1]['temp'], rows[k1]['rcorner'], rows[k1]['vdd'])}, "
              f"high {tag(rows[k2]['corner'], rows[k2]['temp'], rows[k2]['rcorner'], rows[k2]['vdd'])})")
        print(f"op_{key}_span_lo = {m.min():.4f}")
        print(f"op_{key}_span_hi = {m.max():.4f}")
    # line regulation at typical
    t3 = sorted([r for r in rows if r["corner"] == "typical" and r["temp"] == 27 and r["rcorner"] == "res_typical"],
                key=lambda r: r["vdd"])
    lr = (t3[-1]["ic"] - t3[0]["ic"]) / t3[1]["ic"] / 0.6
    print(f"op_line_reg_pct_per_v = {100 * lr:.2f}")
    print(f"REPORT: line regulation of the comparator output, 3.0 -> 3.6 V at typical: {100 * lr:.2f} %/V")
    hr = min(rows, key=lambda r: r["hr_min"])
    verdict(hr["hr_min"] >= HR_MIN, f"op headroom: every matched device saturated by >= {HR_MIN * 1e3:.0f} mV at 135 cells: "
            f"worst {hr['hr_min'] * 1e3:+.0f} mV ({hr['hr_dev']} at {tag(hr['corner'], hr['temp'], hr['rcorner'], hr['vdd'])})")
    su = max(rows, key=lambda r: r["vsu"])
    verdict(su["vsu"] <= SU_MAX, f"op startup node while running <= {SU_MAX * 1e3:.0f} mV: worst {su['vsu'] * 1e3:.1f} mV "
            f"({tag(su['corner'], su['temp'], su['rcorner'], su['vdd'])})")
    bl = max(rows, key=lambda r: r["ibl"])
    verdict(bl["ibl"] <= BLEED_MAX, f"op bleeder current <= {BLEED_MAX * 1e9:.0f} nA: worst {bl['ibl'] * 1e9:.1f} nA "
            f"({tag(bl['corner'], bl['temp'], bl['rcorner'], bl['vdd'])})")
    print(f"op_bleed_max_na = {bl['ibl'] * 1e9:.2f}")
    # the comparator requirement, nominal (mismatch-free) and with the 3-sigma margin
    marg = []
    for r in rows:
        q = req[(r["corner"], r["temp"], r["vdd"])]
        marg.append((r["ic"] / bg.I_CMP_NOM / q, r))
    marg.sort(key=lambda z: z[0])
    w, r = marg[0]
    verdict(w >= 1.0, f"op comparator current >= comparator's requirement at all 135 cells (mismatch-free): worst "
            f"delivered/required {w:.3f} at {tag(r['corner'], r['temp'], r['rcorner'], r['vdd'])}")
    print(f"op_cmp_margin_min = {w:.4f}")
    with open(os.path.join(DATA, "verify_op.csv"), "w") as h:
        keys = ["corner", "temp", "rcorner", "vdd"] + list(bg.OP_COLS) + ["hr_min", "hr_dev"]
        h.write(",".join(keys) + "\n")
        for x in rows:
            h.write(",".join(str(x[k]) if isinstance(x[k], str) else "%.6g" % x[k] for k in keys) + "\n")
    return dict(margin_min=w, rows=rows)


# ------------------------------------------------------------------ opdev
OPDEV_FREQ = 1e6                  # Hz, the AC point at which a MIM replica's C is read


def opdev_deck():
    """typical / 27 C / res_typical / 3.3 V, every consumer diode as load: Id,
    gm, gm/Id, Vgs, Vds, Vdsat, Vth of every generator MOS (the BSIM4 instance
    m0 inside the PDK subcircuit; [id] and [gm] include m), plus PDK-model
    replicas of the resistor string and of each MIM decap, unconnected to the
    generator: R = 0.1 V / I, one strip and the whole string; C from the AC
    current at OPDEV_FREQ (bias 0 V)."""
    devs, res, caps = [], [], []
    for ln in open(GEN):
        t = ln.split()
        if not t or not t[0].upper().startswith("X"):
            continue
        kv = dict(x.split("=", 1) for x in t if "=" in x)
        model = [x for x in t[1:] if "=" not in x][-1]
        if model.startswith(("nfet", "pfet")):
            devs.append((t[0].lower(), model, int(kv.get("m", 1))))
        elif model.startswith("ppolyf"):
            res.append((t[0], model, kv["r_width"], kv["r_length"]))
        elif model.startswith("cap_mim"):
            caps.append((t[0], model, kv["c_width"], kv["c_length"]))
    rep = []
    # resistor replicas: one strip, and the string of all strips as drawn (bulk at 0 like vss)
    m0 = res[0]
    rep.append(f"VRS1 rs1 0 0.1\nXRS1 rs1 0 0 {m0[1]} r_width={m0[2]} r_length={m0[3]}")
    rep.append("VRSS rss0 0 0.1")
    for k, (nm, model, w, l) in enumerate(res):
        nxt = "0" if k == len(res) - 1 else f"rss{k + 1}"
        rep.append(f"XRS{nm} rss{k} {nxt} 0 {model} r_width={w} r_length={l}")
    for nm, model, w, l in caps:
        rep.append(f"VC{nm} c{nm} 0 dc 0 ac 1\nXC{nm}R c{nm} 0 {model} c_width={w} c_length={l}")
    lets, fields = [], []
    for name, _, _ in devs:
        for q in ("id", "gm", "vgs", "vds", "vdsat", "vth"):
            lets.append(f"let {name}_{q} = @m.xg.{name}.m0[{q}]")
            fields.append(f"$&{name}_{q}")
    caplets = "\n".join(f"let c_{nm.lower()} = abs(imag(i(vc{nm.lower()}))) / (2 * pi * {OPDEV_FREQ:g})" for nm, _, _, _ in caps)
    capecho = " ".join(f"$&c_{nm.lower()}" for nm, _, _, _ in caps)
    deck = ("* bias_gen device operating point at the bench bias\n"
            + bg.NGSPICE_HEAD.format(corner="typical", rcorner="res_typical", mim="typical")
            + f".temp 27\n.include {GEN}\nVDD vdd 0 3.3\n"
            + "XG vdd 0 icmp0 icmp1 icmp2 icmp3 iramp ivref ivbl bias_gen\n"
            + bg.consumer_loads() + "\n".join(rep) + "\n"
            + ".control\nset num_threads=1\nop\n" + "\n".join(lets) + "\n"
            + "let r_strip = 0.1 / abs(i(vrs1))\nlet r_string = 0.1 / abs(i(vrss))\n"
            + "let vns = v(xg.ns)\nlet vnb = v(xg.nb)\nlet vpb = v(xg.pb)\n"
            + "let ioc = abs(i(vmc0))\nlet ior = abs(i(vmr))\nlet iov = abs(i(vmv))\nlet isup = -i(vdd)\n"
            + "echo \"OPOUT $&ioc $&ior $&iov $&isup\"\n"
            + "echo \"OPDEV " + " ".join(fields) + "\"\n"
            + "echo \"OPRES $&r_strip $&r_string $&vns $&vnb $&vpb\"\n"
            + f"ac lin 1 {OPDEV_FREQ:g} {OPDEV_FREQ:g}\n" + caplets + "\n"
            + f"echo \"OPCAP {capecho}\"\nquit\n.endc\n.end\n")
    return deck, devs, res, caps


def phase_opdev():
    """Per-device operating point at the block's own bench bias, written to
    data/op_devices.csv / op_passives.csv for the schematic annotation."""
    deck, devs, res, caps = opdev_deck()
    txt = bg.run(rundir("opdev"), deck, "opdev.spice")
    m1 = re.search(r"^OPDEV (.*)$", txt, re.M)
    m2 = re.search(r"^OPRES (.*)$", txt, re.M)
    m3 = re.search(r"^OPCAP (.*)$", txt, re.M)
    m4 = re.search(r"^OPOUT (.*)$", txt, re.M)
    if not (m1 and m2 and m3 and m4):
        verdict(False, f"opdev: device operating point not solved; ngspice: {bg.first_error(txt)}")
        return None
    v = [float(x) for x in m1.group(1).split()]
    rows = []
    for k, (name, model, m) in enumerate(devs):
        idv, gm, vgs, vds, vdsat, vth = v[6 * k:6 * k + 6]
        rows.append(dict(dev=name, model=model, m=m, id=abs(idv), gm=abs(gm),
                         gmid=abs(gm) / abs(idv) if idv else float("nan"),
                         vgs=abs(vgs), vds=abs(vds), vdsat=abs(vdsat), vth=abs(vth)))
    with open(os.path.join(DATA, "op_devices.csv"), "w") as h:
        h.write("dev,model,m,id,gm,gmid,vgs,vds,vdsat,vth\n")
        for r in rows:
            h.write(f"{r['dev']},{r['model']},{r['m']}," + ",".join("%.6g" % r[q] for q in
                    ("id", "gm", "gmid", "vgs", "vds", "vdsat", "vth")) + "\n")
    r_strip, r_string, vns, vnb, vpb = [float(x) for x in m2.group(1).split()]
    cv = [float(x) for x in m3.group(1).split()]
    with open(os.path.join(DATA, "op_passives.csv"), "w") as h:
        h.write("name,model,value,unit,note\n")
        h.write(f"{res[0][0]},{res[0][1]},{r_strip:.6g},ohm,one strip (replica)\n")
        h.write(f"XR_string,{res[0][1]},{r_string:.6g},ohm,{len(res)} strips in series (replica)\n")
        for (nm, model, _, _), c in zip(caps, cv):
            h.write(f"{nm},{model},{c:.6g},F,replica AC at {OPDEV_FREQ:g} Hz\n")
        h.write(f"v_ns,,{vns:.6g},V,node\nv_nb,,{vnb:.6g},V,node\nv_pb,,{vpb:.6g},V,node\n")
        ioc, ior, iov, isup = [float(x) for x in m4.group(1).split()]
        h.write(f"i_icmp,,{ioc:.6g},A,port icmp0 (each of icmp0..3) into its diode\n"
                f"i_iramp,,{ior:.6g},A,port iramp into the ramp diode\n"
                f"i_ivref,,{iov:.6g},A,port ivref (= ivbl) into the midref diode\n"
                f"i_vdd,,{isup:.6g},A,supply current incl. the sourced midref currents\n")
    for r in rows:
        print(f"opdev_{r['dev']}_id_ua = {r['id'] * 1e6:.4f}")
        print(f"opdev_{r['dev']}_gmid = {r['gmid']:.3f}")
    print(f"opdev_icmp_ua = {ioc * 1e6:.4f}")
    print(f"opdev_iramp_ua = {ior * 1e6:.4f}")
    print(f"opdev_ivref_ua = {iov * 1e6:.4f}")
    print(f"opdev_isup_ua = {isup * 1e6:.3f}")
    print(f"opdev_r_strip_kohm = {r_strip / 1e3:.4f}")
    print(f"opdev_r_string_kohm = {r_string / 1e3:.4f}")
    for (nm, _, _, _), c in zip(caps, cv):
        print(f"opdev_c_{nm.lower()}_ff = {c * 1e15:.2f}")
    core = {r["dev"]: r for r in rows}
    print(f"REPORT: opdev (typical/27 C/res_typical/3.3 V, consumer diodes as loads): XMN1 {core['xmn1']['id'] * 1e6:.3f} uA "
          f"gm/Id {core['xmn1']['gmid']:.2f}, XMN2 {core['xmn2']['id'] * 1e6:.3f} uA gm/Id {core['xmn2']['gmid']:.2f}, "
          f"XMP2 gm/Id {core['xmp2']['gmid']:.2f}; R string {r_string / 1e3:.3f} kohm ({len(res)} x {r_strip / 1e3:.3f}); "
          + ", ".join(f"{nm} {c * 1e15:.1f} fF" for (nm, _, _, _), c in zip(caps, cv))
          + " [M, ngspice; data/op_devices.csv, data/op_passives.csv]")
    verdict(len(rows) == len(devs) and all(np.isfinite(r["gmid"]) for r in rows),
            f"opdev: {len(rows)} MOS, {len(res)} resistor strips and {len(caps)} MIM caps read at the bench bias")
    return rows


# ------------------------------------------------------------------ startup
def startup_deck(c, t, rc, case, dut):
    """case: ramp100n | ramp10u | ramp1m | dead | dead_nokick. One START line:
    final core current, final comparator output, final su, the time the core
    first reaches 90 % of its final value (from the release / the supply's end)."""
    vfin = 3.3
    if case.startswith("ramp"):
        tr = {"ramp100n": 100e-9, "ramp10u": 10e-6, "ramp1m": 1e-3}[case]
        vsrc = f"VDD vdd 0 PWL(0 0 {tr:g} {vfin})"
        hold = ""
        t0, tstop = tr, tr + max(20e-6, 0.2 * tr)
        name = "bias_gen_v2x" if True else ""
    else:
        vsrc = f"VDD vdd 0 {vfin}"
        # force the dead state (pb at vdd, nb at 0) through switches released at 10 us
        hold = ("VHC hc 0 PWL(0 1 10u 1 10.01u 0)\nSHP vdd pb hc 0 swh\nSHN nb 0 hc 0 swh\n"
                ".model swh sw vt=0.5 vh=0.1 ron=10 roff=1e15\n")
        t0, tstop = 10e-6, 60e-6
        name = "bias_gen_v2x"
    step = (tstop - 0) / 4000
    return (f"* bias_gen startup {case}\n" + bg.NGSPICE_HEAD.format(corner=c, rcorner=rc, mim=bg.mimcorner(c))
            + f".temp {t:g}\n.include {dut}\n{vsrc}\n{hold}"
            + f"XG vdd 0 icmp0 icmp1 icmp2 icmp3 iramp ivref ivbl nb pb su {name}\n" + bg.consumer_loads()
            + ".save all @m.xg.xmn1.m0[id]\n"
            + ".control\nset num_threads=1\n"
            + f"tran {step:g} {tstop:g} 0 {step:g} uic\n"
            + f"meas tran icf find @m.xg.xmn1.m0[id] at={tstop:g}\n"
            + f"meas tran icmpf find i(vmc0) at={tstop:g}\n"
            + f"meas tran suf find v(su) at={tstop:g}\n"
            + "echo \"START $&icf $&icmpf $&suf\"\n"
            + "let i90 = 0.9 * icf\n"
            + "meas tran t90 when @m.xg.xmn1.m0[id]=$&i90 rise=1\n"
            + "let tup = t90 - " + f"{t0:g}\n"
            + "echo \"T90 $&tup\"\nquit\n.endc\n.end\n")


def phase_startup(op):
    d0 = rundir("startup")
    dut = os.path.join(d0, "gen_x.spice")
    dutnk = os.path.join(d0, "gen_x_nokick.spice")
    open(dut, "w").write(bg.netlist(SIZ, "bias_gen_v2x", export=True))
    open(dutnk, "w").write(bg.netlist(SIZ, "bias_gen_v2x", export=True, kick=False))
    opref = {(r["corner"], r["temp"], r["rcorner"]): r for r in op["rows"] if r["vdd"] == 3.3} if op else {}
    cases = ("ramp100n", "ramp10u", "ramp1m", "dead")
    jobs = [(c, t, rc, k) for c, t, rc in CELLS for k in cases]
    jobs += [(c, t, rc, "dead_nokick") for c, t, rc in CELLS if c == "typical" and rc == "res_typical"]

    def one(j):
        c, t, rc, k = j
        txt = bg.run(rundir("startup", f"{c}_{t:g}_{rc}_{k}"),
                     startup_deck(c, t, rc, k, dutnk if k == "dead_nokick" else dut), timeout=900)
        m = re.search(r"^START (\S+) (\S+) (\S+)", txt, re.M)
        vals = [float(x) for x in m.groups()] if m else [np.nan] * 3
        m2 = re.search(r"^T90 (\S+)", txt, re.M)
        vals.append(float(m2.group(1)) if m2 else np.nan)
        if not m:
            print(f"REPORT: startup {tag(c, t, rc)} {k}: no result; ngspice: {bg.first_error(txt)}")
        return (c, t, rc, k, *vals)
    res = pmap(one, jobs)
    bad, worst_t = [], 0.0
    for c, t, rc, k, icf, icmpf, suf, tup in res:
        if k == "dead_nokick":
            continue
        ref = opref.get((c, t, rc))
        ok = ref is not None and np.isfinite(icf) and abs(icf / ref["icore"] - 1) <= 0.01 and suf <= SU_MAX
        if not ok:
            bad.append(f"{tag(c, t, rc)} {k}")
        elif np.isfinite(tup):
            worst_t = max(worst_t, tup)
    n = len([r for r in res if r[3] != "dead_nokick"])
    verdict(not bad, f"startup: {n - len(bad)} of {n} runs (45 MOS cells x 3 res corners x 100 ns / 10 us / 1 ms ramps "
            f"and a forced dead state) end on the operating point within 1 % with the startup node low"
            + (f"; failing: {', '.join(bad[:6])}" if bad else ""))
    print(f"startup_worst_t90_us = {worst_t * 1e6:.3f}")
    print(f"REPORT: slowest return to 90 % of the core current after the supply or the release: {worst_t * 1e6:.2f} us")
    nk = [r for r in res if r[3] == "dead_nokick"]
    dead = all(np.isfinite(r[4]) and r[4] < 1e-9 for r in nk)
    verdict(dead and len(nk) == 3, f"startup control: without the kick device the forced dead state stays dead "
            f"({len(nk)} typical cells, core current <= {max(r[4] for r in nk) * 1e9 if nk else float('nan'):.2g} nA), "
            "so the recovery above is the startup circuit's doing")
    with open(os.path.join(DATA, "verify_startup.csv"), "w") as h:
        h.write("corner,temp,rcorner,case,icore,icmp,su,t90\n")
        for r in res:
            h.write(",".join(str(x) if isinstance(x, str) else "%.6g" % x for x in r) + "\n")


# ------------------------------------------------------------------ mc
def mc_deck(k, mm):
    return ("* bias_gen local mismatch, one draw\n"
            + bg.NGSPICE_HEAD.format(corner="typical", rcorner="res_typical", mim="typical")
            + f".include {GEN}\n.param sw_stat_mismatch={mm}\n.temp 27\n.options seed={SEED_BASE + k}\n"
            + "VDD vdd 0 3.3\nXG vdd 0 icmp0 icmp1 icmp2 icmp3 iramp ivref ivbl bias_gen\n" + bg.consumer_loads()
            + ".control\nset num_threads=1\nop\n"
            + "let a0 = i(vmc0)\nlet a1 = i(vmc1)\nlet a2 = i(vmc2)\nlet a3 = i(vmc3)\nlet a4 = i(vmr)\n"
            + "let a5 = i(vmv)\nlet a6 = i(vmb)\nlet a7 = @m.xg.xmn1.m0[id]\n"
            + f"echo \"MC {k} $&a0 $&a1 $&a2 $&a3 $&a4 $&a5 $&a6 $&a7\"\n"
            + "quit\n.endc\n.end\n")


def mc_run(tagname):
    def one(k):
        txt = bg.run(rundir("mc", tagname, f"d{k:03d}"), mc_deck(k, 0 if k == 0 else 1))
        m = re.search(r"^MC\s+%d\s+(.*)$" % k, txt, re.M)
        return [abs(float(x)) for x in m.group(1).split()] if m else None
    return pmap(one, range(N_MC + 1))


def phase_mc(op):
    a = mc_run("a")
    b = mc_run("b")
    ok = [x for x in a if x is not None]
    verdict(len(ok) == N_MC + 1, f"mc: {len(ok)} of {N_MC + 1} draws solved")
    same = all(x is not None and y is not None and np.allclose(x, y, rtol=1e-9) for x, y in zip(a, b))
    verdict(same, "mc: a second run with the same seeds reproduces every draw (.options seed per draw)")
    A = np.array([x for x in a[1:] if x is not None])
    nom = np.array(a[0])
    rel = A / nom - 1.0
    s_cmp = float(np.std(rel[:, 0:4]))
    s_core = float(np.std(rel[:, 7]))
    s_pair = float(np.std(rel[:, 0] - rel[:, 1]) / np.sqrt(2))
    s_ramp = float(np.std(rel[:, 4]))
    s_mr = float(np.std(rel[:, 5:7]))
    print(f"mc_sigma_cmp_pct = {100 * s_cmp:.3f}")
    print(f"mc_sigma_core_pct = {100 * s_core:.3f}")
    print(f"mc_sigma_cmp_local_pct = {100 * s_pair:.3f}")
    print(f"mc_sigma_ramp_pct = {100 * s_ramp:.3f}")
    print(f"mc_sigma_midref_pct = {100 * s_mr:.3f}")
    print(f"REPORT: mismatch (typical, {len(A)} draws): comparator output sigma {100 * s_cmp:.2f} % (Pelgrom prediction "
          f"{100 * SIZ['sig_tot']:.2f} %), of which common (core) {100 * s_core:.2f} % (predicted {100 * SIZ['sig_core']:.2f} %) "
          f"and per-output {100 * s_pair:.2f} % (predicted {100 * SIZ['sig_out']:.2f} %); ramp {100 * s_ramp:.2f} %, midref {100 * s_mr:.2f} %")
    if op:
        req = bg.bias_req()
        worst = min((r["ic"] / bg.I_CMP_NOM / req[(r["corner"], r["temp"], r["vdd"])], r) for r in op["rows"])
        need = 1 + N_SIGMA * s_cmp
        verdict(worst[0] >= need, f"mc + op: comparator current at -3 sigma (measured {100 * s_cmp:.2f} %) still meets the "
                f"requirement at every cell: worst delivered/required {worst[0]:.3f} >= {need:.3f} "
                f"({tag(worst[1]['corner'], worst[1]['temp'], worst[1]['rcorner'], worst[1]['vdd'])})")
    with open(os.path.join(DATA, "verify_mc.csv"), "w") as h:
        h.write("k,icmp0,icmp1,icmp2,icmp3,iramp,ivref,ivbl,icore\n")
        for k, x in enumerate(a):
            if x is not None:
                h.write(f"{k}," + ",".join("%.6g" % v for v in x) + "\n")


# ------------------------------------------------------------------ noise
def phase_noise():
    """Voltage noise on the ramp's mirror line (the gate the ramp's XM7/XM6/XPS see)."""
    d = rundir("noise")
    new = ("* new: iramp into the ramp's diode\n" + bg.NGSPICE_HEAD.format(corner="typical", rcorner="res_typical", mim="typical")
           + f".include {GEN}\n.temp 27\nVDD vdd 0 3.3 ac 1\nXG vdd 0 icmp0 icmp1 icmp2 icmp3 iramp ivref ivbl bias_gen\n"
           + bg.consumer_loads()
           + ".control\nset num_threads=1\nnoise v(lr) VDD dec 20 1 100meg\nsetplot noise1\n"
           + "wrdata nz_new.txt onoise_spectrum\nquit\n.endc\n.end\n")
    old = ("* old: bias_gen configuration S, the ramp mirrors its pbias line\n"
           + bg.NGSPICE_HEAD.format(corner="typical", rcorner="res_typical", mim="typical")
           + f".include {OLD_BG}/data/bias_gen_params.spice\n.include {OLD_BG}/bias_gen.spice\n.temp 27\n"
           + "VDD vdd 0 3.3 ac 1\nXB vdd 0 pbias nbias bias_gen_v1\n"
           + ".control\nset num_threads=1\nnoise v(pbias) VDD dec 20 1 100meg\nsetplot noise1\n"
           + "wrdata nz_old.txt onoise_spectrum\nquit\n.endc\n.end\n")
    bg.run(d, new, "new.spice")
    bg.run(d, old, "old.spice")
    try:
        fn = np.loadtxt(os.path.join(d, "nz_new.txt"))
        fo = np.loadtxt(os.path.join(d, "nz_old.txt"))
    except (OSError, ValueError):
        verdict(False, "noise: ngspice produced no spectra")
        return
    f = fn[:, 0]
    sn, so = fn[:, 1], np.interp(f, fo[:, 0], fo[:, 1])
    for fx in (10, 1e3, 1e5, 1e6):
        k = int(np.argmin(abs(f - fx)))
        print(f"noise_ratio_{int(fx)}hz = {sn[k] / so[k]:.3f}")
    # the ramp integrates its slope current over the 12.8 us conversion: weight by the band 1 Hz .. 1 / (2 pi 12.8 us)
    band = f <= 1.0 / (2 * np.pi * 12.8e-6)
    vn = np.sqrt(TRAPZ(sn[band] ** 2, f[band]))
    vo = np.sqrt(TRAPZ(so[band] ** 2, f[band]))
    print(f"noise_line_new_uv = {vn * 1e6:.3f}")
    print(f"noise_line_old_uv = {vo * 1e6:.3f}")
    # the old ramp result: bias_gen group rms at code 255 (ramp_gen data/noise_breakdown.csv)
    old_lsb = 0.0
    p = os.path.join(bg.BLOCK, "..", "ramp_gen", "data", "noise_breakdown.csv")
    if os.path.exists(p):
        with open(p) as h:
            keys = h.readline().strip().split(",")
            for line in h:
                r = dict(zip(keys, line.strip().split(",")))
                if r["group"] == "bias_gen" and r["code"] == "255":
                    old_lsb += float(r["rms_lsb"]) ** 2
        old_lsb = np.sqrt(old_lsb)
    est = old_lsb * vn / vo if vo > 0 else np.nan
    print(f"noise_ramp_bias_old_lsb = {old_lsb:.4f}")
    print(f"noise_ramp_bias_est_lsb = {est:.4f}")
    lim = 0.9 * bg.RAMP_BIAS_NOISE_ALLOC_LSB
    verdict(est <= lim, f"noise: ramp-bias share at code 255 {est:.4f} LSB (old share x line-noise ratio) <= {lim:.3f} LSB "
            f"(allocation {bg.RAMP_BIAS_NOISE_ALLOC_LSB} LSB, NOISE_BUDGET row 4, less 10 % for the VACASK / analysis "
            f"ratio 0.087 / 0.079)")
    print(f"REPORT: ramp mirror-line noise, 1 Hz .. 12.4 kHz: {vn * 1e6:.2f} uV rms with this generator vs {vo * 1e6:.2f} uV "
          f"on the old bias_gen pbias line (x{vn / vo:.2f}); the old bias_gen share of the ramp noise at code 255 was "
          f"{old_lsb:.4f} LSB (ramp_gen data/noise_breakdown.csv), scaled {est:.4f} LSB [M, scaled, not re-run through "
          f"the ramp's kernel]")
    np.savetxt(os.path.join(DATA, "verify_noise.csv"), np.column_stack([f, sn, so]), delimiter=",",
               header="f_hz,new_v_rthz,old_v_rthz", comments="")


# ------------------------------------------------------------------ comparator
def gen_lines(rc, vdd_node, out0, out_names=None, mim=None):
    """The generator + every other consumer's diode, as lines for a foreign bench."""
    kind, L, wf, nf = bg.CMP_DIODE
    outs = out_names or [out0, "gc1", "gc2", "gc3"]
    lines = [f".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_{mim}"] if mim else []
    lines += [f".lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice {rc}", f".include {GEN}",
             f"XG {vdd_node} 0 {' '.join(outs)} glr glv glb bias_gen"]
    for n in outs:
        if n.startswith("gc"):
            lines.append(bg.mos(f"XGD{n}", n, n, vdd_node, vdd_node, kind, L, wf, nf))
    k2, L2, w2, n2 = bg.RAMP_DIODE
    lines.append(bg.mos("XGDR", "glr", "glr", vdd_node, vdd_node, k2, L2, w2, n2))
    k3, L3, w3, n3 = bg.MR_DIODE
    lines.append(bg.mos("XGDV", "glv", "glv", "0", "0", k3, L3, w3, n3))
    lines.append(bg.mos("XGDB", "glb", "glb", "0", "0", k3, L3, w3, n3))
    return "\n".join(lines)


def cmp_module():
    sys.path.insert(0, os.path.abspath(CMP_BLOCK))
    os.environ["DUT_GEOM"] = "1"            # the drawn S/D geometry (bias_req.py's geom case)
    import size_v3 as S3                     # read by path, never modified
    return S3


def phase_cmp():
    S3 = cmp_module()
    sel = json.load(open(os.path.join(CMP_BLOCK, "data", "sizing.json")))
    s = {k: sel[k] for k in S3.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    levels = (("c4", 4.5), ("plat", 40.5))

    def one(j):
        c, t, rc, v = j
        d = rundir("cmp", f"{c}_{t:g}_{rc}_{v:g}")
        subs = S3.common_subs(s, d, 0.0, (c, t, v))
        subs["IREF"] = "0"
        # the generator goes into the included DUT file, not into @REFP@: the templates name
        # @REFP@ in a header comment, where a multi-line value would leak out as live cards
        cmp_net = open(subs["DUT"]).read()
        for name, mim in (("dut_dc.spice", bg.mimcorner(c)), ("dut_tr.spice", None)):   # tb_sel_dc loads no MIM models
            with open(os.path.join(d, name), "w") as h:
                h.write(cmp_net + "\n" + gen_lines(rc, "vddb", "pbias", mim=mim) + "\n")
        subs["DUT"] = os.path.join(d, "dut_dc.spice")
        vtrip = S3.grab(S3.run_deck(d, "tb_sel_dc.spice", subs, 180), "vtrip")
        if not np.isfinite(vtrip) and (c, t, rc, v) == ("typical", 27.0, "res_typical", 3.3):
            p = os.path.join(d, "tb_sel_dc.out")
            txt = open(p, errors="replace").read() if os.path.exists(p) else ""
            print(f"REPORT: cmp typical DC bench gave no trip; ngspice: {bg.first_error(txt)}")
        subs["DUT"] = os.path.join(d, "dut_tr.spice")
        out = {}
        for lt, k in levels:
            if not np.isfinite(vtrip):
                out[lt] = dict(delay_dyn=np.nan, fall=np.nan, p_avg=np.nan, armed=np.nan)
                continue
            dd = rundir("cmp", f"{c}_{t:g}_{rc}_{v:g}", lt)
            sub2 = dict(subs, DUT=subs["DUT"], VIN="%.9g" % (S3.VR_LO + k * S3.LSB),
                        TSTOP="%.6g" % (400e-9 + k * S3.TCOUNT + 400e-9), VTRIP="%.6f" % vtrip)
            blk = S3.run_deck(dd, "tb_sel.spice", sub2, 600)
            out[lt] = {key: S3.grab(blk, key) for key in ("delay_dyn", "fall", "p_avg", "armed")}
        return j, out
    jobs = [(c, t, rc, v) for c, t, rc in CELLS for v in bg.VDDS]
    res = pmap(one, jobs)
    worst, bad, rows = (0.0, None), [], []
    for j, out in res:
        dl = max(out["c4"]["delay_dyn"], out["plat"]["delay_dyn"])
        rows.append((*j, out["c4"]["delay_dyn"], out["plat"]["delay_dyn"], out["plat"]["fall"], out["plat"]["p_avg"]))
        if not (np.isfinite(dl) and dl <= S3.DELAY_MAX):
            bad.append(tag(j[0], j[1], j[2], j[3]) + (f" {dl * 1e9:.2f} ns" if np.isfinite(dl) else " no crossing"))
        if np.isfinite(dl) and dl > worst[0]:
            worst = (dl, j)
    verdict(not bad, f"cmp: comparator (drawn S/D geometry) on this generator: delay from the static trip <= "
            f"{S3.DELAY_MAX * 1e9:.1f} ns at 4.5 and 40.5 LSB at {len(res) - len(bad)} of {len(res)} cells; worst "
            f"{worst[0] * 1e9:.2f} ns" + (f" at {tag(*worst[1])}" if worst[1] else "")
            + (f"; failing: {', '.join(bad[:6])}" if bad else ""))
    print(f"cmp_delay_worst_ns = {worst[0] * 1e9:.3f}")
    P = np.array([r[7] for r in rows])
    F = np.array([r[6] for r in rows])
    print(f"cmp_power_max_uw = {np.nanmax(P) * 1e6:.2f}")
    print(f"cmp_fall_max_ns = {np.nanmax(F) * 1e9:.2f}")
    typ = [r for r in rows if r[0] == "typical" and r[1] == 27 and r[2] == "res_typical" and r[3] == 3.3][0]
    print(f"cmp_delay_typ_ns = {max(typ[4], typ[5]) * 1e9:.3f}")
    print(f"cmp_power_typ_uw = {typ[7] * 1e6:.2f}")
    print(f"REPORT: comparator on this generator: typical delay {max(typ[4], typ[5]) * 1e9:.2f} ns, average power during "
          f"the conversion {typ[7] * 1e6:.1f} uW; over 135 cells up to {np.nanmax(P) * 1e6:.1f} uW, dout fall up to "
          f"{np.nanmax(F) * 1e9:.2f} ns (waived over PVT by ADR 0015)")
    with open(os.path.join(DATA, "verify_cmp.csv"), "w") as h:
        h.write("corner,temp,rcorner,vdd,delay_c4,delay_plat,fall,p_avg\n")
        for r in rows:
            h.write(",".join(str(x) if isinstance(x, str) else "%.6g" % x for x in r) + "\n")


# ------------------------------------------------------------------ crosstalk
XT_DECK = """* four comparator on bias_gen: victim 0 at level K, aggressors 1..3
* (case a) one LSB lower, so they decide one count before the victim, or
* (case q) quiet: their input above the ramp's end, no decision in the window.
{head}.temp {temp:g}
.include {dut}
.include {gen}
.param VDD={vdd:g}
.param LSB=0.005859375
.param SLOPE='LSB/50n'
.options savecurrents reltol=1e-4 gmin=1e-15
VDD_SOURCE vdd 0 {{VDD}}
VVBL vbl 0 {{VDD/2}}
VVREF vref 0 {{VDD/2}}
VS2 s2 0 PWL(0 1 300n 1 300.1n 0)
.model swideal sw vt=0.5 vh=0.1 ron=100 roff=1e16
VCLK clk 0 0
XG vdd 0 pb0 pb1 pb2 pb3 glr glv glb bias_gen
{diodes}
{cells}
.control
set num_threads=1
tran 0.25n {tstop:g} 0 0.5n
let half = {vdd:g} / 2
meas tran t0 when v(dout0)=$&half fall=1 td=400n
meas tran pbx max v(pb0) from=400n to={tstop:g}
meas tran pbn min v(pb0) from=400n to={tstop:g}
echo "XT $&t0 $&pbx $&pbn"
quit
.endc
.end
"""


def phase_xtalk():
    S3 = cmp_module()
    sel = json.load(open(os.path.join(CMP_BLOCK, "data", "sizing.json")))
    s = {k: sel[k] for k in S3.VARS}
    for k in ("nf_in", "nf_ld", "nf_tail", "nf_st"):
        s[k] = int(s[k])
    d0 = rundir("xtalk")
    dut = os.path.join(d0, "cmp_dut.spice")
    open(dut, "w").write(S3.subckt(s))
    kind, L, wf, nf = bg.CMP_DIODE
    k2, L2, w2, n2 = bg.RAMP_DIODE
    k3, L3, w3, n3 = bg.MR_DIODE
    diodes = "\n".join([bg.mos(f"XRP{i}", f"pb{i}", f"pb{i}", "vdd", "vdd", kind, L, wf, nf) for i in range(4)]
                       + [bg.mos("XGDR", "glr", "glr", "vdd", "vdd", k2, L2, w2, n2),
                          bg.mos("XGDV", "glv", "glv", "0", "0", k3, L3, w3, n3),
                          bg.mos("XGDB", "glb", "glb", "0", "0", k3, L3, w3, n3)])
    lvl = 40.5

    def cells(case):
        out = []
        for i in range(4):
            k = lvl if i == 0 else (lvl - 1 if case == "a" else 300)
            vin = 0.5 + k * 1.5 / 256
            out += [f"S2_{i} vref top{i} s2 0 swideal",
                    f"XCS{i} top{i} bot{i} cap_mim_2f0_m4m5_noshield c_width=5u c_length=5u",
                    f"RLK{i} top{i} 0 1e15",
                    f"VBOT{i} bot{i} 0 PWL(0 {vin:.6f} 310n {vin:.6f} 310.1n 0.5 400n 0.5 14.4u {0.5 + 14e-6 * 1.5 / 256 / 50e-9:.6f})",
                    f"XDUT{i} vbl top{i} dout{i} clk vdd 0 0 pb{i} cmp",
                    f"CL{i} dout{i} 0 10f"]
        return "\n".join(out)

    jobs = [(c, t, v, rc, case) for c, t, v, rc in (("typical", 27, 3.3, "res_typical"), ("ss", 85, 3.0, "res_ss"),
                                                     ("ff", 0, 3.6, "res_ff")) for case in ("a", "q")]

    def one(j):
        c, t, v, rc, case = j
        txt = XT_DECK.format(head=bg.NGSPICE_HEAD.format(corner=c, rcorner=rc, mim=bg.mimcorner(c)), temp=t, dut=dut,
                             gen=GEN, vdd=v, diodes=diodes, cells=cells(case), tstop=400e-9 + (lvl + 4) * 50e-9)
        out = bg.run(rundir("xtalk", f"{c}_{t:g}_{v:g}_{case}"), txt, timeout=1800)
        m = re.search(r"^XT (\S+) (\S+) (\S+)", out, re.M)
        return j, [float(x) for x in m.groups()] if m else [np.nan] * 3
    res = {j: r for j, r in pmap(one, jobs)}
    worst = 0.0
    ok = True
    for c, t, v, rc in (("typical", 27, 3.3, "res_typical"), ("ss", 85, 3.0, "res_ss"), ("ff", 0, 3.6, "res_ff")):
        ta, tq = res[(c, t, v, rc, "a")][0], res[(c, t, v, rc, "q")][0]
        sh = (ta - tq) / LSB_T
        ok &= np.isfinite(sh) and abs(sh) <= XTALK_MAX_LSB
        worst = max(worst, abs(sh)) if np.isfinite(sh) else np.inf
        print(f"REPORT: crosstalk at {c}/{t:g} C/{v:g} V/{rc}: victim decision moves {sh:+.4f} LSB when three aggressors "
              f"decide 1 LSB earlier (victim dout falls at {ta * 1e9:.4f} ns vs {tq * 1e9:.4f} ns quiet); victim local pbias excursion {1e3 * (res[(c, t, v, rc, 'a')][1] - res[(c, t, v, rc, 'q')][1]):+.3f} mV")
    print(f"xtalk_worst_lsb = {worst:.4f}")
    verdict(ok, f"xtalk: three aggressors deciding 1 LSB before the victim move it by <= {XTALK_MAX_LSB} LSB at three "
            f"corners: worst {worst:.4f} LSB (shared-pbias bias_gen: -0.165 LSB recorded)")


# ------------------------------------------------------------------ midref
def mr_module():
    sys.path.insert(0, os.path.abspath(MR_BLOCK))
    import size_v2 as S2                     # read by path, never modified
    return S2


def phase_midref(op):
    S2 = mr_module()
    des = json.load(open(os.path.join(MR_BLOCK, "data", "sizing.json")))["design"]
    share = des["share"] > 0.5
    net = open(os.path.join(MR_BLOCK, "midref_v2.spice")).read()

    # operating point: tb_op with the ideal IREF replaced by this generator's ivref
    def one(j):
        c, t, rc = j
        d = rundir("mr_op", f"{c}_{t:g}_{rc}")
        open(os.path.join(d, "dut.spice"), "w").write(net)
        txt = S2.fill("tb_op.spice", dict(CORNER=c, MIMCORNER=bg.mimcorner(c), TEMP=t, IF="0", TAG=f"{c} {t:g} {rc}"))
        txt = txt.replace("res_typical", rc).replace(
            "IREF vdd ib 0", f".include {GEN}\nXG vdd 0 gc0 gc1 gc2 gc3 glr ib glb bias_gen\n" + gen_diodes())
        open(os.path.join(d, "op.spice"), "w").write(txt)
        out = S2.ngspice(d, "op.spice")
        return [(m.group(1), float(m.group(2)), m.group(3), float(m.group(4)), [float(x) for x in m.group(5).split()])
                for m in re.finditer(r"^OP (\S+) (\S+) (\S+) (\S+) (.*)$", out, re.M)]
    rows = [r for rr in pmap(one, CELLS) for r in rr]
    verdict(len(rows) == 135, f"midref op: {len(rows)} of 135 cells solved")
    if rows:
        A = np.array([r[4] for r in rows])
        for (a, b), nm in zip(((0, 1), (2, 3), (4, 5)), ("followers M1/M4", "IB sources XMIB/XMIT", "output diodes M2/M5")):
            k = int(np.argmin(np.minimum(A[:, a], A[:, b])))
            verdict(np.min(A[:, [a, b]]) >= 0, f"midref op headroom {nm} on this generator: worst |vds| - |vdsat| "
                    f"{np.min(A[:, [a, b]]):+.3f} V at {rows[k][0]}/{rows[k][1]:g} C/{rows[k][2]}/{rows[k][3]:g} V")
        k = int(np.argmax(np.abs(A[:, 8])))
        verdict(np.max(np.abs(A[:, 8])) <= S2.VERR_MAX, f"midref op VDD/2 error on this generator: worst "
                f"{A[k, 8] * 1e3:+.2f} mV at {rows[k][0]}/{rows[k][1]:g} C/{rows[k][2]}/{rows[k][3]:g} V "
                f"(bound {S2.VERR_MAX * 1e3:.0f} mV)")
        print(f"midref_hr_f_min_v = {np.min(A[:, [0, 1]]):.4f}")

    # S2 kick at the cells where this generator's midref current is lowest and highest
    cells = [("ss", 0, 3.0, "res_ss"), ("typical", 27, 3.3, "res_typical"), ("ff", 85, 3.6, "res_ff"),
             ("ff", 85, 3.0, "res_ff"), ("ss", 0, 3.6, "res_ss")]

    def kick(j):
        c, t, v, rc = j
        d = rundir("mr_kick", f"{c}_{t:g}_{v:g}_{rc}")
        open(os.path.join(d, "dut.spice"), "w").write(net)
        subs = S2.kick_subs(0.0, share, "k", (c, t, v))
        subs["IF"] = "0"
        subs["BUFS"] = (S2.bufs(share) + f"\n.include {GEN}\nXG vdd 0 gc0 gc1 gc2 gc3 glr ibr ibb bias_gen\n"
                        + gen_diodes(mr=False))
        txt = S2.fill("tb_kick.spice", subs).replace("res_typical", rc)
        txt = txt.replace("IREFR vdd ibr 0\n", "").replace("IREFB vdd ibb 0\n", "")
        open(os.path.join(d, "kick.spice"), "w").write(txt)
        return j, S2.grab(S2.ngspice(d, "kick.spice"))
    res = pmap(kick, cells)
    nok, wts, wxt = 0, 0.0, 0.0
    for j, r in res:
        good = True
        for cc in (1, 2):
            pk = r.get(f"k_c{cc}_pkr_mv", np.nan)
            ts = r.get(f"k_c{cc}_tsr_ns", 0.0 if pk == pk and pk < S2.EPS * 1e3 else np.nan)
            rr = max(r.get(f"k_c{cc}_rr250_mv", np.nan), r.get(f"k_c{cc}_rr300_mv", np.nan))
            xt = r.get(f"k_c{cc}_rb250_uv", np.nan)
            q = abs(r.get(f"k_c{cc}_qk_fc", 0.0))
            good &= ts <= S2.TS_MAX * 1e9 and rr <= S2.EPS * 1e3 and xt <= S2.LSB / 4 * 1e6 and q >= 50
            wts = max(wts, np.nan_to_num(ts, nan=1e9))
            wxt = max(wxt, np.nan_to_num(xt, nan=1e9))
        nok += good
    verdict(nok == len(cells), f"midref kick on this generator: {nok} of {len(cells)} extreme-current cells hold both S2 "
            f"cases (midrail_ref_v2 gates): worst return to 1/2 LSB {wts:.0f} ns (limit {S2.TS_MAX * 1e9:.0f}), worst VBL "
            f"crosstalk {wxt:.1f} uV")
    print(f"midref_kick_ts_worst_ns = {wts:.1f}")


def gen_diodes(mr=True):
    """Diodes on the generator outputs not used by a midref bench (comparators, ramp, the other buffer)."""
    kind, L, wf, nf = bg.CMP_DIODE
    out = [bg.mos(f"XGD{i}", f"gc{i}", f"gc{i}", "vdd", "vdd", kind, L, wf, nf) for i in range(4)]
    k2, L2, w2, n2 = bg.RAMP_DIODE
    out.append(bg.mos("XGDR", "glr", "glr", "vdd", "vdd", k2, L2, w2, n2))
    if mr:
        k3, L3, w3, n3 = bg.MR_DIODE
        out.append(bg.mos("XGDB", "glb", "glb", "0", "0", k3, L3, w3, n3))
    return "\n".join(out) + "\n"


def main():
    os.makedirs(WORK, exist_ok=True)
    print(f"REPORT: verifying bias_gen.spice: L {SIZ['L']:g} um, finger W {SIZ['wf']:g} um, K {SIZ['K']}, "
          f"core {SIZ['na']}+{SIZ['K'] * SIZ['na']} NMOS / {SIZ['npm']}+{SIZ['npm']} PMOS fingers, sinks {SIZ['nc']} x 4 + "
          f"{SIZ['nr']}, sources {SIZ['nm']} x 2")
    op = phase_op() if "op" in PHASES else None
    if "opdev" in PHASES:
        phase_opdev()
    if "startup" in PHASES:
        phase_startup(op or {"rows": op_rows()})
    if "mc" in PHASES:
        phase_mc(op)
    if "noise" in PHASES:
        phase_noise()
    if "cmp" in PHASES:
        phase_cmp()
    if "xtalk" in PHASES:
        phase_xtalk()
    if "midref" in PHASES:
        phase_midref(op)
    return 0


if __name__ == "__main__":
    sys.exit(main())
