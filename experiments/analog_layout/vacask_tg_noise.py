"""Write the VACASK seed-sweep netlist for the GF180 TG sampling cell and evaluate it.

Usage (inside the container, see vacask.sh):
  python3 vacask_tg_noise.py write  <out.sim> [N]   -> netlist with 1 noiseless + N noisy transients
  python3 vacask_tg_noise.py eval   <dir> [N]       -> spread of the sampled hold voltage vs kT/C
"""
import sys, glob
import numpy as np

HEAD = """GF180 TG sampling cell, sampled-noise experiment (VACASK transient noise)

include "gf180_vacask_common.lib"
include "design.lib"
include "mos_tt.lib"
include "mimcap_tt.lib"

model v vsource

vdd (vdd 0) v dc=3.3
vin (in 0) v type="sine" sinedc=1.2 ampl=0.6 freq=5e6
vclk (sample 0) v type="pulse" val0=0 val1=3.3 delay=5n rise=100p fall=100p width=20n period=100n
vclkb (sample_b 0) v type="pulse" val0=3.3 val1=0 delay=5n rise=100p fall=100p width=20n period=100n
xswn (in sample hold 0) nfet_03v3 l=0.28u w=10u nf=10
xswp (in sample_b hold vdd) pfet_03v3 l=0.28u w=20u nf=10
xchold (hold 0) gf180_default_mod_c c=1p    // ideal 1 pF (converted MIM subckt params are not overridable yet)
rleak (hold 0) gf180_default_mod_r r=1e12
"""

def write(out, n):
    lines = [HEAD, "control", "  analysis ref tran stop=60n step=5p maxstep=50p"]
    for i in range(1, n + 1):
        lines.append(f"  analysis n{i} tran stop=60n step=5p maxstep=50p noisefmax=2e9 noisefmin=1e4 noiseseed={i}")
    lines += ["  save v(hold)", "endc", ""]
    open(out, "w").write("\n".join(lines))

def held(f):
    from rawfile import rawread
    p = rawread(f).get(); return np.interp(50e-9, p["time"], p["hold"])

def evaluate(d, n):
    ref = held(f"{d}/ref.raw")
    vals = np.array([held(f"{d}/n{i}.raw") for i in range(1, n + 1)])
    ktc = np.sqrt(1.380649e-23 * 300 / 1e-12)
    print(f"noiseless held value      : {ref*1e3:.4f} mV")
    print(f"noisy runs N={n:<3d} mean      : {vals.mean()*1e3:.4f} mV  (mean-ref {(vals.mean()-ref)*1e6:+.1f} uV)")
    print(f"sampled-noise std         : {vals.std(ddof=1)*1e6:.1f} uV rms")
    print(f"kT/C (1 pF, 300 K)        : {ktc*1e6:.1f} uV rms  -> ratio {vals.std(ddof=1)/ktc:.2f}")

if __name__ == "__main__":
    cmd = sys.argv[1]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    write(sys.argv[2], n) if cmd == "write" else evaluate(sys.argv[2], n)
