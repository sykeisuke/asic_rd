"""Stage this folder's VACASK benches for the comparator (run inside the container).

    python3 stage_vacask.py             builds work/va/ (run-pvt.sh then runs `sh vacask.sh` there)
    python3 stage_vacask.py collect     copies the stage's results into data/ and assets/

The VACASK benches (vacask.sh: vmodels vmc tn tnpvt, with trannoise.py and
vacask_lib/) were written for the 10-device core with the plate on inn. Their
templates now carry the comparator's own hookup, checked here to be present
exactly once per template:
        xdut (inn inp dout clk vdd 0 nbias pbias) comparator
i.e. the bench net `inn` (the moving node: the ramp, the MC sweep, the PSD
bench's feedback node, the plate in the cell) drives the comparator's inp, and
the bench net `inp` (the held level = VREF) drives its inn. Every bench-side
name, measurement and reduction (trip of the swept node, dout's falling edge,
noise referred to vinp) stays as it was, and dout falls at the decision.

The stimulus constants are the sizing record's (data/sizing.json: ideal
1.931 uA, alpha 0.761 for the pin slope and the LSB referral, LSB 1.5/256),
so the pin-referred results compare one to one with the 10-device record
runs/comparator-pvt/20261106T142531Z. The transient-noise gate is 1.2 mV at
the pins. tnpvt picks the worst-noise cell of data/pvt.csv (pvt.py).

The stage lives in work/va/; the folder's own files are not changed.
"""
import os
import shutil
import sys

BLOCK = os.path.dirname(os.path.abspath(__file__))
BASE = BLOCK
STAGE = os.path.join(BLOCK, "work", "va")
HOOK = "xdut (inn inp dout clk vdd 0 nbias pbias) comparator"
TEMPLATES = ("tb_mc.sim.tmpl", "tb_tn_psd.sim.tmpl", "tb_tn_ramp.sim.tmpl", "tb_noise.sim.tmpl")


def fail(msg):
    print("FAIL: stage_vacask: " + msg)
    sys.exit(1)


def stage():
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    for d in ("", "vacask_lib", "data", "assets", "work"):
        os.makedirs(os.path.join(STAGE, d), exist_ok=True)
    for f in ("vacask.sh", "trannoise.py", "check-trannoise.awk", "tb_vacask_devcheck.spice"):
        shutil.copy(os.path.join(BASE, f), os.path.join(STAGE, f))
    for f in os.listdir(os.path.join(BASE, "vacask_lib")):
        p = os.path.join(BASE, "vacask_lib", f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(STAGE, "vacask_lib", f))
    for t in TEMPLATES:
        n = open(os.path.join(STAGE, "vacask_lib", t)).read().count(HOOK)
        if n != 1:
            fail(f"{t}: expected exactly one {HOOK!r}, found {n}")
    shutil.copy(os.path.join(BLOCK, "comparator.spice"), os.path.join(STAGE, "comparator.spice"))
    shutil.copy(os.path.join(BASE, "data", "sizing.json"), os.path.join(STAGE, "data", "sizing.json"))
    pvt = os.path.join(BLOCK, "data", "pvt.csv")
    if os.path.exists(pvt):
        shutil.copy(pvt, os.path.join(STAGE, "data", "pvt.csv"))
    else:
        print("REPORT: stage_vacask: no data/pvt.csv (bench phase not run): tnpvt is skipped")
    print(f"INFO: VACASK stage built in work/va: comparator, hookup '{HOOK}' in {len(TEMPLATES)} templates")
    return 0


def collect():
    pairs = (("data/vmc.csv", "data/pvt_vmc.csv"),
             ("data/trannoise_summary.json", "data/pvt_trannoise_summary.json"),
             ("data/pvt_trannoise.txt", "data/pvt_trannoise_worst.txt"))
    for a, b in pairs:
        src = os.path.join(STAGE, a)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(BLOCK, b))
    for d, _, fs in os.walk(os.path.join(STAGE, "data")):
        for f in fs:
            if f.startswith("trannoise_summary_") and f.endswith(".json"):
                shutil.copy(os.path.join(d, f), os.path.join(BLOCK, "data", "pvt_" + f))
    for f in os.listdir(os.path.join(STAGE, "assets")):
        if f.endswith(".png"):
            shutil.copy(os.path.join(STAGE, "assets", f), os.path.join(BLOCK, "assets", "pvt_" + f))
    return 0


if __name__ == "__main__":
    sys.exit(collect() if sys.argv[1:] == ["collect"] else stage())
