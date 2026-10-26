"""Reduce one VACASK noise run (tb_noise.sim.tmpl) to one CSV row.

    python3 vacask_lib/noise_reduce.py work <filetag> <celltag> <corner> <temp> <vdd> <vcm> >> work/vnoise_sweep.csv

Reads work/nz_<filetag>.raw (onoise PSD, power gain, per-instance n(...)) and
work/ac_<filetag>.raw (OTA gain vs frequency); <filetag> is the cell tag plus
the level with dots replaced by p (VACASK identifiers cannot carry dots),
<celltag> is corner_temp_vdd as in the ngspice CSVs. Prints:

    tag,corner,temp,vdd,common_mode_v,nz_win_v,nz_ref_v,nz_ugb_v,gain_vv,
    pole_hz,ugbw_hz,flk_share,top_contributor,top_share,spot_100,spot_1meg

  spot_100, spot_1meg  input-referred density (V/sqrt(Hz)) at 100 Hz and 1 MHz

  nz_win   input-referred rms over 1 Hz .. 1/(2 pi 50 ns) = 3.18 MHz, the
           decision window (the ngspice deck's nz_win_vin)
  nz_ref   output noise integrated over the whole sweep, referred through
           the DC gain: the OTA's own-bandwidth figure (ngspice's nz_ref_vin)
  nz_ugb   input-referred rms out to the OTA unity-gain frequency, the
           pessimistic bound (ngspice's nz_ugb_vin)
  flk_share  fraction of the decision-window noise POWER below 100 kHz
  top_contributor  the instance with the largest output-noise contribution
           at 100 kHz, and its share of the total there

Input-referred PSD is onoise/gain, gain being VACASK's power gain from the
input source to the output node. Integration is trapezoidal in linear
frequency on the log-spaced sweep, which is what ngspice's inoise_total does.
"""
import os
import sys

import numpy as np
from rawfile import rawread

TCOUNT = 50e-9
F_WIN = 1.0 / (2.0 * np.pi * TCOUNT)
F_FLK = 100e3
trapz = getattr(np, "trapezoid", None) or np.trapz   # numpy 2 renamed it


def integrate(f, psd, fmax):
    m = f <= fmax
    ff, pp = f[m], psd[m]
    if ff.size < 2:
        return float("nan")
    if ff[-1] < fmax and m.sum() < f.size:
        # add the interpolated end point so the band edge is exact
        j = m.sum()
        pe = np.interp(fmax, f[j - 1:j + 1], psd[j - 1:j + 1])
        ff, pp = np.append(ff, fmax), np.append(pp, pe)
    return float(np.sqrt(trapz(pp, ff)))


def main():
    wd, ftag, tag, corner, temp, vdd, vcm = sys.argv[1:8]
    nz = rawread(os.path.join(wd, f"nz_{ftag}.raw")).get()
    ac = rawread(os.path.join(wd, f"ac_{ftag}.raw")).get()
    f = np.real(np.asarray(nz["frequency"]))
    onoise = np.real(np.asarray(nz["onoise"]))
    gain = np.real(np.asarray(nz["gain"]))
    inoise = onoise / gain
    fa = np.real(np.asarray(ac["frequency"]))
    ga = np.abs(np.asarray(ac["xdut:outa"]))
    a0 = float(ga[0])
    # The inductor-closed bias loop has an unphysical DC solution (output
    # railed, no gain) that VACASK's solver lands on at a few PVT cells even
    # with the nodeset. It is unmistakable: OTA gain below 5 where the
    # physical solution has 60-110. Such a cell is marked, not reported as
    # a noise number; the checker counts the marks and the ngspice sweep
    # covers the cell.
    if a0 < 5.0:
        print(f"{tag},{corner},{temp},{vdd},{vcm},nan,nan,nan,{a0:.5g},nan,nan,nan,op_unphysical,nan,nan,nan")
        return 0
    gdb = 20 * np.log10(ga)
    ugbw = float(np.interp(0.0, gdb[::-1], fa[::-1])) if gdb[-1] < 0 < gdb[0] else float("nan")
    pole = float(np.interp(20 * np.log10(a0) - 3.0, gdb[::-1], fa[::-1]))
    nz_win = integrate(f, inoise, F_WIN)
    nz_ugb = integrate(f, inoise, ugbw) if np.isfinite(ugbw) else float("nan")
    nz_ref = float(np.sqrt(trapz(onoise, f))) / a0
    p_flk = integrate(f, inoise, F_FLK) ** 2
    flk_share = p_flk / nz_win ** 2 if nz_win > 0 else float("nan")
    # contributions at 100 kHz
    k = int(np.argmin(np.abs(f - F_FLK)))
    contrib = {n: float(np.real(nz[n][k])) for n in nz.names if n.startswith("n(")}
    top, share = "none", float("nan")
    if contrib:
        top = max(contrib, key=contrib.get)
        share = contrib[top] / onoise[k] if onoise[k] > 0 else float("nan")
    spot100 = float(np.sqrt(np.interp(100.0, f, inoise)))
    spot1m = float(np.sqrt(np.interp(1e6, f, inoise)))
    print(f"{tag},{corner},{temp},{vdd},{vcm},{nz_win:.6e},{nz_ref:.6e},{nz_ugb:.6e},"
          f"{a0:.5g},{pole:.5g},{ugbw:.5g},{flk_share:.4f},{top},{share:.4f},{spot100:.4e},{spot1m:.4e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
