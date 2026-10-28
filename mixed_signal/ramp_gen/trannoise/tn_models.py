"""VACASK model include for the ramp_gen transient-noise cross-check.

    python3 tn_models.py            (container, from trannoise/) -> work/models.inc

1. The GF180 3.3 V BSIM4 wrappers nfet_03v3 / pfet_03v3 (typical), converted
   by ../ref/comparator_lp/vacask_lib/gf180_vacask.py, called by path.
2. Quiet copies nfet_03v3_q / pfet_03v3_q: the same subcircuits with every
   bin's model card carrying ntnoi=0 (channel thermal noise, tnoimod=0) and
   noia=noib=noic=0 (flicker, fnoimod=1). The PDK cards have rdsmod, rgatemod,
   rbodymod, igcmod and igbmod all 0, so no other BSIM4 noise source exists;
   probe_models.sim checks that the quiet device is silent and the normal one
   is not.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
CONV = os.path.join(HERE, "..", "ref", "comparator_lp", "vacask_lib", "gf180_vacask.py")


def main():
    os.makedirs(WORK, exist_ok=True)
    base = os.path.join(WORK, "gf180_03v3_typical.inc")
    r = subprocess.run([sys.executable, CONV, "typical", base], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(base):
        sys.exit("FAIL: gf180_vacask.py did not write the model include\n" + r.stdout[-1500:] + r.stderr[-1500:])
    txt = open(base).read()
    blocks = re.findall(r"(subckt (nfet_03v3|pfet_03v3) \(d g s b\)\n.*?\nends\n)", txt, re.S)
    if len(blocks) != 2:
        sys.exit("FAIL: expected two wrapper subcircuits in %s, found %d" % (base, len(blocks)))
    quiet = []
    nmod = 0
    for blk, name in blocks:
        q = blk.replace("subckt %s (d g s b)" % name, "subckt %s_q (d g s b)" % name, 1)

        def fix(m):
            line = m.group(0)
            for k in ("ntnoi", "noia", "noib", "noic"):
                line, n = re.subn(r"\b%s=\S+" % k, "%s=0" % k, line)
                if n == 0:
                    line += " %s=0" % k
            return line
        q, n = re.subn(r"^  model mdl bsim4 .*$", fix, q, flags=re.M)
        nmod += n
        quiet.append("// quiet copy of %s: ntnoi=0 noia=noib=noic=0 in every bin\n" % name + q)
    out = os.path.join(WORK, "models.inc")
    with open(out, "w") as f:
        f.write(txt.rstrip("\n") + "\n\n" + "\n".join(quiet))
    print("tn_models_bins_quieted = %d" % nmod)
    print("PASS: work/models.inc: nfet_03v3, pfet_03v3 and their quiet copies (%d model cards)" % nmod)


if __name__ == "__main__":
    main()
