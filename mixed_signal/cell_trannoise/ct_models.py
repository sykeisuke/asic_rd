"""VACASK model include for the cell_trannoise benches (as
../Analog_top_bkp/Analog_top_v4/trannoise/at_models.py, writing into this block's work/).

    python3 ct_models.py            (container, from this block) -> work/models.inc

1. The GF180 3.3 V BSIM4 wrappers nfet_03v3 / pfet_03v3 (typical), converted by
   ../Analog_top_bkp/Analog_top_v4/trannoise/gf180_vacask.py, read BY PATH (binunit kept, every
   bin coefficient written explicitly, bins on total W as ngspice does, nfs for
   the finger expansion). That converter's drain currents were gated against
   ngspice within 0.13 % at ten v4 geometries including the dfxtn_2 devices.
2. Quiet copies nfet_03v3_q / pfet_03v3_q: the same subcircuits with every bin's
   model card carrying ntnoi=0 (channel thermal noise) and noia=noib=noic=0
   (flicker). The PDK cards have rdsmod, rgatemod, rbodymod, igcmod and igbmod
   all 0, so no other BSIM4 noise source exists.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
CONV = os.path.join(HERE, "gf180_vacask.py")


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
    with open(os.path.join(WORK, "models.inc"), "w") as f:
        f.write(txt.rstrip("\n") + "\n\n" + "\n".join(quiet))
    print("ct_models_bins_quieted = %d" % nmod)
    print("PASS: work/models.inc: nfet_03v3, pfet_03v3 and their quiet copies (%d model cards)" % nmod)


if __name__ == "__main__":
    main()
