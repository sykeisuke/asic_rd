"""COPY of ../../comparator/vacask_lib/gf180_vacask.py with ONE addition (Analog_top,
2026-10-08): the wrapper parameter nfs (default 1). An instance with w = W/nf, nf = 1,
nfs = nf is nf parallel single-finger devices ($mfactor = m nfs) BINNED ON THE TOTAL
WIDTH w nfs, as ngspice bins the drawn nf-finger device. at_netlist.py uses it because
VACASK's bsim4 flicker grows with nf (probe_flk.py). With nfs = 1 nothing changes.

Convert the GF180 3.3 V BSIM4 models from the PDK's ngspice library into a
VACASK include file, one corner at a time.

    ./container.sh 'python3 vacask_lib/gf180_vacask.py typical work/gf180_03v3_typical.inc'
    ./container.sh 'FNOICOR=1 python3 vacask_lib/gf180_vacask.py ss work/gf180_03v3_ss_fnoi.inc'

WHY THIS EXISTS. VACASK ships an ngspice-to-VACASK converter (`ng2vc.py`),
and it crashes on `sm141064.ngspice` (KeyError 'origline' while collecting
masters, VACASK 764f693). The model file is also 46 000 lines for all of
the devices in the PDK, while this block needs exactly two: `nfet_03v3` and
`pfet_03v3`. So this script converts those two, deliberately and readably,
and nothing else. It reads the PDK by path and writes only under work/.

WHAT IT REPRODUCES, AND HOW IT IS CHECKED

  bins       The PDK carries 16 BSIM4 bins per device and corner, selected
             on drawn L and W (lmin <= L < lmax, wmin <= W < wmax). ngspice
             46 with its default `wnflag=0` bins on the TOTAL width, not the
             per-finger width -- measured with `show` in tb_bin_probe.spice
             (W=30u nf=8 lands in the 10-100 um bin). The VACASK wrapper
             applies the same rule with an @if chain, so the two simulators
             pick the same bin for the same instance line. Note that binning
             on total width is the repository's ngspice convention, not
             necessarily the foundry's intent; both simulators here agree with
             each other, which is what the cross-check needs.

  mismatch   The PDK's `fets_mm` wrapper draws two agauss() numbers per
             device: a threshold shift (delvto) and a mobility factor (mulu0),
             both scaled by 1/sqrt(Leff*Weff) and gated by sw_stat_mismatch.
             VACASK's bsim4 module exposes `delvto` as a MODEL parameter and
             has no `mulu0`, so the wrapper here defines the bin model INSIDE
             the wrapper subcircuit -- one model per wrapper instance -- with
             `delvto` set to the draw and u0, lu0, wu0, pu0 all multiplied by
             the same (1 - mis_k). Scaling all four binning terms together is
             what multiplying the effective u0 means. The gate is the circuit
             variable `mm` (0 or 1), which every bench sets with `var`.
             VACASK's agauss() has the same (nom, avar, sigma) signature as
             ngspice's, and draws per subcircuit instance inside an `mc` loop.

  noise      noia/noib/noic are the only model parameters written as
             expressions in the PDK (a flicker-noise corner switch,
             `fnoicor`). They are evaluated here for FNOICOR (default 0,
             as-extracted) and written as numbers.

  version    The PDK models are BSIM4 v4.5 (`level=54 version=4.5`); VACASK's
             module is BSIM4 v4.8. Every parameter the PDK sets is checked
             against the module's parameter list (obtained by running VACASK
             on a probe netlist, not from a hard-coded table). Anything the
             module does not know is dropped and REPORTED. Whether the v4.8
             equations then reproduce ngspice's v4.5 operating point is not
             assumed: run.sh's `models` phase simulates the same devices in
             both and gates on the difference (tb_vacask_devcheck.*).

Prints `name = value` scalars and REPORT lines for the run script to reduce.
"""
import os
import re
import subprocess
import sys
import tempfile

PDK_SPICE = "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.spice"
SECTION = {"typical": "t", "ff": "f", "ss": "s", "fs": "fs", "sf": "sf"}
DEVICES = (("nfet_03v3", "nmos", 1), ("pfet_03v3", "pmos", -1))
NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")
# `level=54` is ngspice's model-selector and means nothing to the module.
# Everything else is passed through -- including `binunit=2`, which tells
# BSIM4 that the lvth0/wvth0/pvth0-style bin coefficients are per micrometre.
# The first version of this script dropped binunit as "bin bookkeeping" and
# every bin coefficient was then applied 1e6 times too strongly: drain
# currents disagreed with ngspice by up to 7x. The devcheck caught it.
DROP_ALWAYS = {"level"}


def read_sections(path):
    body, cur = {}, None
    with open(path) as f:
        for line in f:
            s = line.rstrip("\n")
            m = re.match(r"^\.lib\s+(\S+)\s*$", s)
            if m:
                cur = m.group(1)
                body[cur] = []
                continue
            if s.startswith(".endl"):
                cur = None
                continue
            if cur is not None:
                body[cur].append(s)
    return body


def parse_models(lines):
    out, cur = [], None
    for s in lines:
        m = re.match(r"^\.model\s+(\S+)\s+(\S+)", s)
        if m:
            cur = dict(name=m.group(1), type=m.group(2), params=[])
            out.append(cur)
            continue
        if cur is not None and s.startswith("+"):
            for tok in s[1:].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    cur["params"].append((k.lower(), v.strip("'")))
        elif cur is not None:
            cur = None
    return out


def parse_wrapper_params(lines, dev):
    """par_vth, par_k, par_l, par_w of the `fets_mm` wrapper for `dev`."""
    vals, inside = {}, False
    for s in lines:
        if re.match(rf"^\.subckt\s+{dev}\s", s):
            inside = True
            continue
        if inside and s.startswith(".ends"):
            break
        if inside:
            m = re.match(r"^\.param\s+(par_vth|par_k|par_l|par_w)=(\S+)", s)
            if m:
                vals[m.group(1)] = float(m.group(2))
    missing = {"par_vth", "par_k", "par_l", "par_w"} - set(vals)
    if missing:
        raise SystemExit(f"FAIL: fets_mm wrapper for {dev} lacks {sorted(missing)}")
    return vals


def noise_corner_values(lines, fnoicor):
    vals = {}
    for s in lines:
        m = re.match(r"^\.param\s+(\w+)='(.*)'\s*$", s)
        if m:
            expr = m.group(2).replace("==", "==")
            vals[m.group(1)] = float(eval(expr, {"__builtins__": {}}, {"fnoicor": fnoicor}))
    return vals


def osdi_model_params():
    """Ask VACASK which model parameters its bsim4 module has."""
    probe = (
        "bsim4 parameter probe\nground 0\nload \"bsim4v8.osdi\"\nload \"resistor.osdi\"\n"
        "model resistor resistor\nmodel vsource vsource\n"
        "v1 (in 0) vsource dc=1\nr1 (in 0) resistor r=1k\n"
        "control\n  print device(\"bsim4\")\nendc\n"
    )
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "probe.sim")
        with open(p, "w") as f:
            f.write(probe)
        out = subprocess.run(["vacask", "--no-output", p], cwd=d,
                             capture_output=True, text=True).stdout
    names, section = set(), None
    for line in out.splitlines():
        if "Model parameters:" in line:
            section = "model"
            continue
        if "Instance parameters:" in line:
            section = "inst"
            continue
        m = re.match(r"^\s*id=\d+:\s+([^:]+):", line)
        if m and section == "model":
            names.add(m.group(1).strip())
    if not names:
        raise SystemExit("FAIL: could not read the bsim4 module parameter list from VACASK")
    return names


def fmt(v):
    return v if NUM.match(v) else repr(float(v))


def main():
    corner = sys.argv[1] if len(sys.argv) > 1 else "typical"
    out_path = sys.argv[2] if len(sys.argv) > 2 else f"work/gf180_03v3_{corner}.inc"
    fnoicor = int(os.environ.get("FNOICOR", "0"))
    if corner not in SECTION:
        raise SystemExit(f"FAIL: unknown corner {corner}; one of {sorted(SECTION)}")

    body = read_sections(PDK_SPICE)
    known = osdi_model_params()
    noise = noise_corner_values(body["noise_corner"], fnoicor)
    dropped = set()
    lines = [
        f"// GF180MCU {corner} corner, nfet_03v3 and pfet_03v3, for VACASK.",
        f"// GENERATED by vacask_lib/gf180_vacask.py from {PDK_SPICE}",
        f"// (Ciel f6eeac7dad085ffcc829ccfd721f7b4ce39edcf7), fnoicor={fnoicor}.",
        "// The bench must define the circuit variable `mm` (1 = mismatch on).",
        'load "bsim4v8.osdi"',
        "",
    ]
    nbins = {}
    for dev, mtype, tsign in DEVICES:
        sec = f"{dev}_{SECTION[corner]}"
        models = [m for m in parse_models(body[sec]) if m["type"] == mtype]
        if not models:
            raise SystemExit(f"FAIL: no {mtype} models in section {sec}")
        wp = parse_wrapper_params(body["fets_mm"], dev)
        nbins[dev] = len(models)
        lines += [
            f"subckt {dev} (d g s b)",
            "parameters w=10u l=0.28u nf=1 m=1 ad=0 as=0 pd=0 ps=0 nrd=0 nrs=0 sa=0 sb=0 sd=0 par=1 nfs=1",
            f"parameters par_vth={wp['par_vth']} par_k={wp['par_k']} par_l={wp['par_l']} par_w={wp['par_w']}",
            "parameters par_leff=l-par_l par_weff=par*(w-par_w)",
            "parameters p_sqrtarea=sqrt(par_leff*par_weff)",
            "parameters var_k=0.7071*par_k*1e-06/p_sqrtarea var_vth=0.7071*par_vth*1e-06/p_sqrtarea",
            "parameters mis_k=agauss(0,var_k,1)*mm mis_vth=agauss(0,var_vth,1)*mm",
            "parameters kmul=1-mis_k",
        ]
        # Bin coefficients the PDK omits in some bins (it leaves out every
        # W- and P- coefficient in the 10-100 um bins). ngspice takes 0 for
        # a missing coefficient; the VA module may not, so every coefficient
        # that any bin of this device names is written explicitly in every
        # bin, as 0 when the PDK omits it.
        all_names = set()
        for m in models:
            all_names.update(k for k, _ in m["params"])
        bin_coeffs = sorted(k for k in all_names
                            if k[:1] in "lwp" and k[1:] in all_names and k in known)
        first = True
        for m in models:
            p = dict(m["params"])
            present = set(p)
            cond = (f"l>={p['lmin']} && l<{p['lmax']} && w*nfs>={p['wmin']} && w*nfs<{p['wmax']}")
            lines.append(("@if " if first else "@elseif ") + cond)
            first = False
            toks = [f"type={tsign}"]
            for k, v in m["params"]:
                if k in DROP_ALWAYS:
                    continue
                if k not in known:
                    dropped.add(k)
                    continue
                if k in ("noia", "noib", "noic"):
                    v = repr(noise[f"{dev}_{k}"])
                if k in ("u0", "lu0", "wu0", "pu0"):
                    toks.append(f"{k}={fmt(v)}*kmul")
                else:
                    toks.append(f"{k}={fmt(v)}")
            for k in bin_coeffs:
                if k not in present:
                    toks.append(f"{k}=0*kmul" if k in ("lu0", "wu0", "pu0") else f"{k}=0")
            toks.append("delvto=mis_vth")
            # one model per wrapper instance, so the mismatch draw is per device
            lines.append(f"  model mdl bsim4 {' '.join(toks)}")
            lines.append("  m0 (d g s b) mdl w=w l=l nf=nf ad=ad as=as pd=pd ps=ps "
                         "nrd=nrd nrs=nrs sa=sa sb=sb sd=sd $mfactor=m*nfs")
        lines.append("@else")
        lines.append(f"  m0 (d g s b) {dev}_no_bin_for_this_geometry w=w l=l")
        lines.append("@end")
        lines.append("ends")
        lines.append("")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"vacask_models_corner_{corner} = 1")
    print(f"vacask_models_nbins_nfet = {nbins['nfet_03v3']}")
    print(f"vacask_models_nbins_pfet = {nbins['pfet_03v3']}")
    print(f"vacask_models_dropped_params = {len(dropped)}")
    if dropped:
        print("REPORT: PDK BSIM4 v4.5 parameters not known to VACASK's bsim4 v4.8 module, "
              f"dropped from {corner}: {' '.join(sorted(dropped))}")
    print(f"INFO: wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
