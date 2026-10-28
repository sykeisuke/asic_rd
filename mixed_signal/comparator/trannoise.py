"""Comparator noise characterized by VACASK transient noise.

The small-signal noise analysis integrates a stationary PSD over an
assumed band (the OTA's own band). The comparator does not see a stationary
small signal: under the attenuated ramp its output rests near the tail, is
pulled down as the top plate approaches VBL, and slews through the starved
inverter's trip about 90 ns after the ideal crossing. What the conversion
actually suffers is the spread of the instant at which dout falls. This
script measures that directly, with every device noise source injecting in
the time domain, and first checks the transient-noise engine against the
small-signal noise analysis at the same bias.

    python3 trannoise.py gen 1     ramp benches + small-signal half of the PSD benches
    python3 trannoise.py gen 2     transient half of the PSD benches (needs the _ss op)
    python3 trannoise.py reduce    measurements on stdout, data/trannoise_summary.json,
                                   assets/comparator_trannoise*.png

Cases (typical, 27 C, 3.3 V, comparator.spice at inp = VBL = VCM_DEC; the ramp
on inn at alpha x the 117.19 kV/s conversion slope):

    psd_hi       the AC-noise bias point in the time domain, noisefmax 200 MHz:
                 Welch PSD of v(outa) / |A|^2 against the noise analysis
    psd_lo       the same at noisefmax 5 MHz and a 40 ms record: the flicker region
                 (both PSD benches at noise scale PSD_SCALE = 0.03, see below)
    r_1p65       the attenuated 8-bit ramp against inp = 1.65 V: N conversions in
                 one record, crossing jitter
    r_1p65_q     the same with noisescale = 0: the numerical floor
    r_1p65_f1g   noisefmax 1 GHz: independence of the generator bandwidth

Run as the `tn` phase of run.sh (typical) or from pvt.py (TN_SUFFIX corner
mode); this is not a standalone flow.
"""
import json
import os
import sys

import numpy as np

BLOCK = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BLOCK, "assets")

# A PVT corner of the characterization (pvt.py): TN_SUFFIX names the
# case set and keeps its work directory, summary and figures apart from the
# nominal record; TN_CORNER / TN_TEMP / TN_VDD / TN_IREF set the cell (IREF
# is bias_gen's measured current there). In corner mode only the conversion
# benches and the small-signal half of psd_hi (the AC reference the ramp
# figures are compared with) run: the PSD engine gates are a property of the
# simulator and stay with the nominal record. Unset, nothing changes.
TN_SUFFIX = os.environ.get("TN_SUFFIX", "")
CORNER_MODE = TN_SUFFIX != ""
WORK = os.path.join(BLOCK, "work", "tn" + ("_" + TN_SUFFIX if CORNER_MODE else ""))

VDD = float(os.environ.get("TN_VDD", "3.3"))
TEMP = float(os.environ.get("TN_TEMP", "27"))
CORNER = os.environ.get("TN_CORNER", "typical")
TCOUNT = 50e-9
LSB = 1.5 / 256                         # 8 bits over 0.5 .. 2.0 V
SLOPE = LSB / TCOUNT                    # 117187.5 V/s, one LSB per count
F_WIN = 1.0 / (2 * np.pi * TCOUNT)      # the AC "decision window" band edge
NOISE_BUDGET = LSB / 4                  # the recipe's noise budget, 1.465 mV rms
SEED0 = 20260924

N_CONV = int(os.environ.get("TN_CONV", "800"))
N_CONV_F1G = int(os.environ.get("TN_CONV_F1G", "300"))
FMAX = 200e6
FMIN = 1e3
UNDER = 30e-3                           # ramp starts this far below the level
T_LOW = 600e-9                          # ramp held low: comparator recovers
T_FALL = 5e-9
T_WIDTH = 10e-9
SKIP = 3                                # first conversions dropped (start-up)
PSD_HI_T = float(os.environ.get("TN_PSD_HI_T", "400e-6"))
PSD_LO_T = float(os.environ.get("TN_PSD_LO_T", "40e-3"))
# Bands over which the time-domain PSD is compared with the noise analysis:
# inside the resolved range of each record (>= 5 Welch bins above the
# segment resolution, <= fmax / 5 below the generator edge).
BAND_HI = (100e3, 20e6)
BAND_LO = (1e3, 300e3)
SEG_HI = 40e-6
SEG_LO = 4e-3
# Noise scale of the two PSD benches (VACASK noisescale: every source's
# AMPLITUDE x s, so the PSD is divided by s^2 here). The bench parks the
# comparator at its own crossing, with dout = inp through the _ss inductor
# loop, so the starved second stage sits at its trip. That holds the
# whole circuit at the point the noise analysis linearises.
#
# cmp_lp carried 35 fF on outa (COUTA + the clamp well). The simplified
# comparator carries about 16 fF and has 11.7 mV rms on outa. That is far
# beyond the starved stage's linear window, so at s = 1 dout spends 15 % of
# the record between 10 and 90 % of VDD and toggles 1460 times in 380 us,
# and the comparison is no longer small signal: x1.199 in 100 kHz-20 MHz.
#
# Measured with ablation/tn_diag.py on that record, band ratio
# against noise scale:
#   s = 0.3   x0.865
#   s = 0.1   x0.905
#   s = 0.03  x0.968, dout linear 100 % of the time
#   s = 0.01  x0.996
# The engine and the models agree once the bench is small signal, so
# these two benches run at s = 0.03. The conversion benches (r_*) are the
# real large-signal case and stay at s = 1.
PSD_SCALE = float(os.environ.get("TN_PSD_SCALE", "0.03"))

INK, INK2, MUTED, GRID, SURF = "#1f2328", "#57606a", "#8c959f", "#d8dee4", "#ffffff"
BLUE, ORANGE, GREEN, AMBER, PINK = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"


# comparator.spice (data/sizing.json) decides at ONE common mode, inp = VBL = VCM_DEC, and the ramp
# reaches inn through the top-plate attenuation alpha = C_S/(C_S + C_top), so
# the slope at the pins is alpha x SLOPE and a pin-referred sigma is divided
# by alpha at the ADC input. The level set is that one common mode.
SIZING_JSON = os.environ.get("SIZING_JSON", "data/sizing.json")
DUT_NAME = "comparator"


def sizing():
    with open(os.path.join(BLOCK, SIZING_JSON), encoding="utf-8") as h:
        return json.load(h)


def iref():
    if os.environ.get("TN_IREF"):
        return float(os.environ["TN_IREF"])
    return float(sizing()["iref"])


def refp_line():
    """v3's bias reference: one tail finger, diode-connected (data/sizing.json)."""
    s = sizing()
    return "xrefp (pbias pbias vddb vddb) pfet_03v3 l=%gu w=%gu nf=1 m=1" % (s["l_b"], s["w_fp"] * 1e6)


ALPHA = float(sizing()["alpha"])
NOM_LEVEL = float(os.environ.get("VCM_DEC", "1.65"))
LEVELS = [NOM_LEVEL]
NOM_K = ALPHA                           # conversion slope at the pins / SLOPE


def tag_of(level):
    return "r_" + ("%g" % level).replace(".", "p")


NOM = tag_of(NOM_LEVEL)
STEM = "comparator_trannoise"
SUMMARY = "trannoise_summary.json"
if CORNER_MODE:
    STEM = STEM + "_" + TN_SUFFIX
    SUMMARY = SUMMARY.replace(".json", "_" + TN_SUFFIX + ".json")


def ramp_case(tag, level, k=1.0, fmax=FMAX, nscale=1.0, nconv=None, seed=0):
    # k is relative to the nominal PIN slope (NOM_K x SLOPE)
    slope = k * NOM_K * SLOPE
    over = max(30e-3, slope * 300e-9)   # past the level by more than the delay
    rise = (UNDER + over) / slope
    period = rise + T_WIDTH + T_FALL + T_LOW
    n = nconv or N_CONV
    return {"kind": "ramp", "tag": tag, "level": level, "k": k, "slope": slope,
            "vlo": level - UNDER, "vhi": level + over, "tdelay": T_LOW,
            "trise": rise, "twidth": T_WIDTH, "tfall": T_FALL, "tper": period,
            "tstop": T_LOW + n * period, "nconv": n, "fmax": fmax, "fmin": FMIN,
            "nscale": nscale, "seed": SEED0 + seed}


def cases():
    cs = [
        {"kind": "psd", "tag": "psd_hi", "vcm": NOM_LEVEL, "tstop": PSD_HI_T, "tran": True,
         "fmax": FMAX, "fmin": FMIN, "seed": SEED0 + 100},
        {"kind": "psd", "tag": "psd_lo", "vcm": NOM_LEVEL, "tstop": PSD_LO_T, "tran": True,
         "fmax": 5e6, "fmin": 10.0, "seed": SEED0 + 101},
    ]
    if CORNER_MODE:
        cs = [dict(cs[0], tran=False)]   # the AC reference only (see TN_SUFFIX)
    cs.append(ramp_case(NOM, NOM_LEVEL, seed=2))
    cs.append(ramp_case(NOM + "_q", NOM_LEVEL, nscale=0.0, nconv=40, seed=2))
    cs.append(ramp_case(NOM + "_f1g", NOM_LEVEL, fmax=1e9, nconv=N_CONV_F1G, seed=6))
    return cs


def nodeset(vcm):
    return ('{"inn", %.9g, "dout", %.9g, "xdut:outa", 0.85, "xdut:left", 0.6, '
            '"xdut:tail", %.9g, "xdut:outb", 3.3}' % (vcm, vcm, vcm + 0.9))


def raw(name):
    from rawfile import rawread
    return rawread(os.path.join(WORK, name + ".raw")).get()


# ----------------------------------------------------------------- generate
def gen(phase):
    """phase 1: ramp benches and the small-signal half of the PSD benches;
    phase 2 (after phase 1's _ss runs): the transient half of the PSD
    benches, inn biased at the _ss operating point."""
    os.makedirs(WORK, exist_ok=True)
    if phase == 1:
        for f in os.listdir(WORK):
            if f.endswith((".sim", ".raw", ".vlog")):
                os.remove(os.path.join(WORK, f))
    only = os.environ.get("TN_ONLY", "").split()
    templates = {}
    for kind, name in (("ramp", "tb_tn_ramp.sim.tmpl"), ("psd", "tb_tn_psd.sim.tmpl")):
        with open(os.path.join(BLOCK, "vacask_lib", name), encoding="utf-8") as h:
            templates[kind] = h.read()
    out = []
    for c in cases():
        if only and c["tag"] not in only:
            continue
        out.append(c)
        subs = {"@TAG@": c["tag"], "@CORNER@": CORNER, "@TEMP@": "%g" % TEMP,
                "@VDD@": "%g" % VDD, "@IREF@": "%.9e" % iref(), "@REFP@": refp_line(), "@CLOAD@": "10f"}
        if c["kind"] == "ramp":
            if phase != 1:
                continue
            subs.update({"@TSTOP@": "%.9e" % c["tstop"], "@FMAX@": "%.6e" % c["fmax"],
                         "@FMIN@": "%.6e" % c["fmin"], "@SEED@": "%d" % c["seed"],
                         "@VLEVEL@": "%.9g" % c["level"], "@VLO@": "%.9g" % c["vlo"],
                         "@VHI@": "%.9g" % c["vhi"], "@TDELAY@": "%.9e" % c["tdelay"],
                         "@TRISE@": "%.9e" % c["trise"], "@TWIDTH@": "%.9e" % c["twidth"],
                         "@TFALL@": "%.9e" % c["tfall"], "@TPER@": "%.9e" % c["tper"],
                         "@NSCALE@": "%g" % c["nscale"]})
            name = c["tag"]
        else:
            subs["@VCM@"] = "%.9g" % c["vcm"]
            if phase == 1:
                subs["@INNBIAS@"] = "cinn (inn 0) capacitor c=1\nlfb (dout inn) inductor l=1T"
                subs["@ANALYSES@"] = "\n".join([
                    '  analysis op_%s op nodeset=%s store="bias"' % (c["tag"], nodeset(c["vcm"])),
                    "  save v('xdut:outa')",
                    '  analysis ac_%s ac nodeset="bias" from=1 to=10G mode="dec" points=40' % c["tag"],
                    '  analysis nz_%s noise nodeset="bias" out="xdut:outa" in="vinp" '
                    'from=1 to=10G mode="dec" points=40' % c["tag"]])
                name = c["tag"] + "_ss"
            else:
                if not c["tran"]:
                    continue
                v_inn = float(np.real(np.asarray(raw("op_" + c["tag"])["inn"]))[0])
                c["v_inn"] = v_inn
                subs["@INNBIAS@"] = "vinn (inn 0) vsource dc=%.12g" % v_inn
                subs["@ANALYSES@"] = (
                    '  analysis tn_%s tran stop=%.9e step=10p noisemode="sde" '
                    'noisefmax=%.6e noisefmin=%.6e noiseseed=%d'
                    % (c["tag"], c["tstop"], c["fmax"], c["fmin"], c["seed"])
                    + (" noisescale=%g" % PSD_SCALE if PSD_SCALE != 1.0 else ""))
                name = c["tag"]
        text = templates[c["kind"]]
        for key, value in subs.items():
            text = text.replace(key, value)
        with open(os.path.join(WORK, name + ".sim"), "w", encoding="utf-8") as h:
            h.write(text)
        if name == c["tag"]:
            print("gen %s: stop %.4g s, noisefmax %.3g Hz, about %.3g steps"
                  % (name, c["tstop"], c["fmax"], c["tstop"] * 12 * c["fmax"]))
    if phase == 1 or os.path.exists(os.path.join(WORK, "cases.json")):
        with open(os.path.join(WORK, "cases.json"), "w", encoding="utf-8") as h:
            json.dump(out, h, indent=1)
    return 0


# ------------------------------------------------------------ small signal
trapz = getattr(np, "trapezoid", None) or np.trapz


def band_rms(f, psd, lo, hi):
    m = (f >= lo) & (f <= hi)
    return float(np.sqrt(trapz(psd[m], f[m])))


def small_signal(tag):
    nz, ac = raw("nz_" + tag), raw("ac_" + tag)
    f = np.real(np.asarray(nz["frequency"]))
    onoise = np.real(np.asarray(nz["onoise"]))
    inoise = onoise / np.real(np.asarray(nz["gain"]))
    fa = np.real(np.asarray(ac["frequency"]))
    ga = np.abs(np.asarray(ac["xdut:outa"]))
    a0 = float(ga[0])
    gdb = 20 * np.log10(ga)
    ugbw = float(np.interp(0.0, gdb[::-1], fa[::-1]))
    pole = float(np.interp(gdb[0] - 3.0, gdb[::-1], fa[::-1]))
    sig_outa = float(np.sqrt(trapz(onoise, f)))
    return {"f": f, "inoise": inoise, "onoise": onoise, "fa": fa, "ga": ga,
            "a0": a0, "ugbw": ugbw, "pole": pole, "sig_outa": sig_outa,
            "win": band_rms(f, inoise, 1.0, F_WIN),
            "own": sig_outa / a0,
            "floor_1meg": float(np.sqrt(np.interp(1e6, f, inoise))),
            "v_inn": float(np.real(np.asarray(raw("op_" + tag)["inn"]))[0]),
            "v_outa": float(np.real(np.asarray(raw("op_" + tag)["xdut:outa"]))[0])}


def welch(x, fs, nseg):
    """One-sided PSD (V^2/Hz), Hann window, 50 % overlap, linear detrend."""
    w = np.hanning(nseg)
    step = nseg // 2
    starts = range(0, x.size - nseg + 1, step)
    acc = np.zeros(nseg // 2 + 1)
    tt = np.arange(nseg)
    k = 0
    for s in starts:
        seg = x[s:s + nseg]
        seg = seg - np.polyval(np.polyfit(tt, seg, 1), tt)
        acc += np.abs(np.fft.rfft(seg * w)) ** 2
        k += 1
    psd = 2.0 * acc / (k * fs * np.sum(w ** 2))
    return np.fft.rfftfreq(nseg, 1.0 / fs), psd, k


def reduce_psd(c, ss):
    d = raw("tn_" + c["tag"])
    t = np.asarray(d["time"])
    v = np.asarray(d["xdut:outa"])
    h = 1.0 / (12 * c["fmax"])
    t0 = 0.05 * c["tstop"]
    grid = np.arange(t0, t[-1], h)
    vg = np.interp(grid, t, v)
    seg = SEG_HI if c["tag"] == "psd_hi" else SEG_LO
    f, s_out, k = welch(vg, 1.0 / h, int(round(seg / h)))
    f, s_out = f[1:], s_out[1:]
    gain = np.exp(np.interp(np.log(f), np.log(ss["fa"]), np.log(ss["ga"])))
    s_in = s_out / gain ** 2 / PSD_SCALE ** 2
    s_ac = np.exp(np.interp(np.log(f), np.log(ss["f"]), np.log(ss["inoise"])))
    lo, hi = BAND_HI if c["tag"] == "psd_hi" else BAND_LO
    tn_rms = band_rms(f, s_in, lo, hi)
    ac_rms = band_rms(f, s_ac, lo, hi)
    return {"f": f, "s_in": s_in, "segments": k, "band": (lo, hi),
            "tn_rms": tn_rms, "ac_rms": ac_rms, "ratio": tn_rms / ac_rms,
            "mean_outa": float(vg.mean()), "t": grid, "v": vg}


# --------------------------------------------------------------- the ramp
def reduce_ramp(c, keep_waves=False):
    d = raw(c["tag"])
    t = np.asarray(d["time"])
    dout = np.asarray(d["dout"])
    outa = np.asarray(d["xdut:outa"])
    thr = VDD / 2
    n = c["nconv"]
    t_start = c["tdelay"] + c["tper"] * np.arange(n)
    t_ideal = t_start + (c["level"] - c["vlo"]) / c["slope"]
    t_end = t_start + c["trise"] + c["twidth"]
    lo_i = np.searchsorted(t, t_start)
    hi_i = np.searchsorted(t, t_end)
    delay = np.full(n, np.nan)
    slew = np.full(n, np.nan)
    extra = 0
    waves = []
    for k in range(n):
        a, b = lo_i[k], min(hi_i[k], t.size - 1)
        seg = dout[a:b + 1]
        falls = np.nonzero((seg[:-1] >= thr) & (seg[1:] < thr))[0]
        if falls.size == 0:
            continue
        extra += falls.size - 1
        i = a + falls[0]
        tc = t[i] + (thr - dout[i]) * (t[i + 1] - t[i]) / (dout[i + 1] - dout[i])
        delay[k] = tc - t_ideal[k]
        ta, tb = tc - 1e-9, tc + 1e-9
        slew[k] = (np.interp(tb, t, outa) - np.interp(ta, t, outa)) / (tb - ta)
        if keep_waves and SKIP <= k < SKIP + 80:
            tw = np.arange(-20e-9, 170e-9, 0.25e-9)
            waves.append((np.interp(t_ideal[k] + tw, t, outa), np.interp(t_ideal[k] + tw, t, dout)))
    found = int(np.isfinite(delay).sum())
    dl = delay[SKIP:]
    dl = dl[np.isfinite(dl)]
    m = dl.size
    sig_t = float(np.std(dl, ddof=1))
    sig_fast_t = float(np.std(np.diff(dl), ddof=1) / np.sqrt(2))
    vtrip = c["slope"] * (dl - dl.mean())
    # code flicker: P(code != its mode) averaged over the clock phase
    ph = np.linspace(0, 1, 200, endpoint=False)
    pflip = []
    for p in ph:
        codes = np.floor(dl / TCOUNT + p)
        _, counts = np.unique(codes, return_counts=True)
        pflip.append(1.0 - counts.max() / codes.size)
    r = {"tag": c["tag"], "level": c["level"], "k": c["k"], "slope": c["slope"],
         "nconv": n, "found": found, "used": m, "extra_crossings": extra,
         "delay_mean": float(dl.mean()), "delay_pp": float(dl.max() - dl.min()),
         "sig_t": sig_t, "sig_v": c["slope"] * sig_t,
         "sig_v_ci": c["slope"] * sig_t * 1.96 / np.sqrt(2 * (m - 1)),
         "sig_fast_v": c["slope"] * sig_fast_t,
         "sig_slow_v": c["slope"] * float(np.sqrt(max(sig_t ** 2 - sig_fast_t ** 2, 0.0))),
         "slew": float(np.nanmean(np.abs(slew[SKIP:]))),
         "p_code_flip": float(np.mean(pflip)),
         "delays": dl, "vtrip": vtrip,
         "record_s": c["tstop"], "fmax": c["fmax"], "nscale": c["nscale"]}
    if keep_waves:
        r["waves"] = waves
    return r


# ------------------------------------------------------------------ reduce
def reduce():
    with open(os.path.join(WORK, "cases.json"), encoding="utf-8") as h:
        cs = {c["tag"]: c for c in json.load(h)}
    out = []

    def put(key, value, fmt="%.6g"):
        out.append(("%s = " + fmt) % (key, value))

    ss = {}
    for tag, lvl in (("ac_0p5", 0.5), ("psd_hi", NOM_LEVEL), ("ac_2p0", 2.0)):
        if tag in cs:
            ss[lvl] = small_signal(tag)
    for lvl, s in ss.items():
        p = "ac_%s" % ("%g" % lvl).replace(".", "p")
        put(p + "_gain_vv", s["a0"])
        put(p + "_pole_hz", s["pole"])
        put(p + "_ugbw_hz", s["ugbw"])
        put(p + "_win_uv", s["win"] * 1e6)
        put(p + "_own_uv", s["own"] * 1e6)
        put(p + "_sig_outa_mv", s["sig_outa"] * 1e3)
        put(p + "_floor_1meg_nv", s["floor_1meg"] * 1e9)
        put(p + "_vos_mv", (s["v_inn"] - lvl) * 1e3)
        put(p + "_v_outa", s["v_outa"])

    psd = {}
    for tag in ("psd_hi", "psd_lo"):
        if tag in cs and cs[tag].get("tran", True):
            psd[tag] = r = reduce_psd(cs[tag], ss[NOM_LEVEL])
            put(tag + "_segments", r["segments"], "%d")
            put(tag + "_noisescale", PSD_SCALE)
            put(tag + "_band_lo_hz", r["band"][0])
            put(tag + "_band_hi_hz", r["band"][1])
            put(tag + "_tn_uv", r["tn_rms"] * 1e6)
            put(tag + "_ac_uv", r["ac_rms"] * 1e6)
            put(tag + "_ratio", r["ratio"])
            put(tag + "_outa_shift_mv", (r["mean_outa"] - ss[NOM_LEVEL]["v_outa"]) * 1e3)

    ramps = {}
    for tag, c in cs.items():
        if c["kind"] != "ramp":
            continue
        ramps[tag] = r = reduce_ramp(c, keep_waves=tag in (NOM, NOM + "_q"))
        put(tag + "_found", r["found"], "%d")
        put(tag + "_nconv", r["nconv"], "%d")
        put(tag + "_used", r["used"], "%d")
        put(tag + "_extra_crossings", r["extra_crossings"], "%d")
        put(tag + "_delay_ns", r["delay_mean"] * 1e9)
        put(tag + "_delay_pp_ns", r["delay_pp"] * 1e9)
        put(tag + "_sigma_t_ps", r["sig_t"] * 1e12)
        put(tag + "_sigma_uv", r["sig_v"] * 1e6)
        put(tag + "_sigma_ci95_uv", r["sig_v_ci"] * 1e6)
        put(tag + "_sigma_lsb", r["sig_v"] / LSB)
        put(tag + "_sigma_in_lsb", r["sig_v"] / (ALPHA * LSB))   # at the ADC input
        put(tag + "_sigma_fast_uv", r["sig_fast_v"] * 1e6)
        put(tag + "_sigma_slow_uv", r["sig_slow_v"] * 1e6)
        put(tag + "_slew_v_per_us", r["slew"] * 1e-6)
        put(tag + "_p_code_flip", r["p_code_flip"])
        s = ss.get(r["level"], ss.get(NOM_LEVEL))
        r["pred_slew"] = r["slope"] * s["sig_outa"] / r["slew"]
        put(tag + "_ac_slew_pred_uv", r["pred_slew"] * 1e6)
        if r["nscale"] > 0:
            put(tag + "_over_ac_win", r["sig_v"] / s["win"])
            put(tag + "_over_ac_own", r["sig_v"] / s["own"])
            put(tag + "_over_ac_slew", r["sig_v"] / r["pred_slew"])
            put(tag + "_over_budget", r["sig_v"] / (NOISE_BUDGET * ALPHA))
            if r["sig_fast_v"] > 0 and r["k"] == 1.0:
                # the bandwidth a white floor would need to give the fast part
                put(tag + "_enbw_fast_mhz", (r["sig_fast_v"] / s["floor_1meg"]) ** 2 * 1e-6)
    if NOM + "_q" in ramps and NOM in ramps:
        put("floor_over_noise", ramps[NOM + "_q"]["sig_v"] / ramps[NOM]["sig_v"])
        put("quiet_vs_noisy_delay_ns",
            (ramps[NOM]["delay_mean"] - ramps[NOM + "_q"]["delay_mean"]) * 1e9)
    if NOM + "_f1g" in ramps and NOM in ramps:
        a, b = ramps[NOM + "_f1g"], ramps[NOM]
        put("fmax_ratio", a["sig_v"] / b["sig_v"])
        put("fmax_ratio_tol", 3 * np.hypot(1 / np.sqrt(2 * (a["used"] - 1)),
                                           1 / np.sqrt(2 * (b["used"] - 1))))
    noisy = [r for r in ramps.values() if r["nscale"] > 0 and r["k"] == 1.0 and r["fmax"] == FMAX]
    if noisy:
        put("worst_sigma_uv", max(r["sig_v"] for r in noisy) * 1e6)
        put("worst_sigma_lsb", max(r["sig_v"] for r in noisy) / (ALPHA * LSB))
    # the budget is 1/4 LSB at the ADC input, alpha x that at the pins
    put("noise_budget_uv", NOISE_BUDGET * ALPHA * 1e6)
    put("alpha", ALPHA)
    put("pin_slope_v_per_s", NOM_K * SLOPE)
    for line in out:
        print(line)

    summary = {line.split(" = ")[0]: float(line.split(" = ")[1]) for line in out}
    with open(os.path.join(BLOCK, "data", SUMMARY), "w", encoding="utf-8") as h:
        json.dump(summary, h, indent=1, sort_keys=True)
    if not CORNER_MODE:
        plot_psd(ss, psd)
    plot_ramp(ss, ramps)
    for r in ramps.values():
        os.remove(os.path.join(WORK, r["tag"] + ".raw"))   # 50-100 MB each
    return 0


# -------------------------------------------------------------------- plots
def tidy(ax, title, xlabel, ylabel):
    ax.set_facecolor(SURF)
    ax.set_title(title, fontsize=10, color=INK, loc="left", pad=6)
    ax.set_xlabel(xlabel, fontsize=9, color=INK2)
    ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    ax.grid(True, which="major", color=GRID, linewidth=0.7)
    ax.tick_params(labelsize=8, colors=INK2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def legend(ax, **kw):
    kw.setdefault("fontsize", 7.5)
    leg = ax.legend(frameon=False, **kw)
    for text in leg.get_texts():
        text.set_color(INK2)


def plot_psd(ss, psd):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    s = ss[NOM_LEVEL]
    fig = plt.figure(figsize=(11, 7.6), dpi=170)
    fig.patch.set_facecolor(SURF)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.6, 1.0], width_ratios=[1.7, 1.0],
                          left=0.07, right=0.98, top=0.83, bottom=0.08, hspace=0.38, wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    ar = fig.add_subplot(gs[1, 0], sharex=ax)
    at = fig.add_subplot(gs[:, 1])

    m = (s["f"] >= 10) & (s["f"] <= 1e9)
    ax.loglog(s["f"][m], np.sqrt(s["inoise"][m]) * 1e9, color=INK, lw=2.0, zorder=4,
              label="VACASK noise analysis (small signal, AC)")
    colors = {"psd_hi": BLUE, "psd_lo": ORANGE}
    names = {"psd_hi": "transient noise, fmax 200 MHz, %d x %g us segments",
             "psd_lo": "transient noise, fmax 5 MHz, %d x %g ms segments"}
    for tag, r in psd.items():
        lo, hi = r["band"]
        seg = SEG_HI * 1e6 if tag == "psd_hi" else SEG_LO * 1e3
        mm = (r["f"] >= lo / 3) & (r["f"] <= hi * 3)
        ax.loglog(r["f"][mm], np.sqrt(r["s_in"][mm]) * 1e9, color=colors[tag], lw=0.6,
                  alpha=0.35, zorder=2)
        eb = np.logspace(np.log10(r["f"][mm][0]), np.log10(r["f"][mm][-1]), 40)
        fb, sb = [], []
        for a, b in zip(eb[:-1], eb[1:]):
            qq = (r["f"] >= a) & (r["f"] < b)
            if qq.sum() >= 1:
                fb.append(np.sqrt(a * b))
                sb.append(np.sqrt(np.mean(r["s_in"][qq])) * 1e9)
        ax.loglog(fb, sb, "o-", color=colors[tag], lw=1.4, ms=3.5, zorder=3,
                  label=names[tag] % (r["segments"], seg) + " (log-binned; raw faint)")
        ax.axvspan(lo, hi, color=colors[tag], alpha=0.06, lw=0)
        # ratio in log bins
        edges = np.logspace(np.log10(lo), np.log10(hi), 15)
        fc, rat = [], []
        s_ac = np.exp(np.interp(np.log(r["f"]), np.log(s["f"]), np.log(s["inoise"])))
        for a, b in zip(edges[:-1], edges[1:]):
            q = (r["f"] >= a) & (r["f"] < b)
            if q.sum() >= 2:
                fc.append(np.sqrt(a * b))
                rat.append(np.sqrt(np.mean(r["s_in"][q]) / np.mean(s_ac[q])))
        ar.semilogx(fc, rat, "o-", color=colors[tag], ms=4.5, lw=1.2,
                    label="%s: band rms %.1f uV vs AC %.1f uV (x%.3f)"
                    % (tag, r["tn_rms"] * 1e6, r["ac_rms"] * 1e6, r["ratio"]))
    ax.axvline(F_WIN, color=MUTED, lw=0.9, ls="--")
    ax.text(F_WIN * 1.1, 3e3, "decision window\nedge 3.18 MHz", fontsize=7.5, color=MUTED, va="top")
    ax.axvline(s["pole"], color=MUTED, lw=0.9, ls=":")
    ax.text(s["pole"] * 0.9, 3e3, "OTA pole\n%.2f MHz" % (s["pole"] * 1e-6), fontsize=7.5,
            color=MUTED, va="top", ha="right")
    ax.set_xlim(100, 1e9)
    ax.set_ylim(5, 5e3)
    tidy(ax, "Input-referred noise density at the crossing bias, VCM = %g V" % NOM_LEVEL,
         "", "input-referred noise  (nV/rtHz)")
    legend(ax, loc="lower left")
    ar.axhspan(0.9, 1.1, color=GRID, alpha=0.5, lw=0)
    ar.axhline(1.0, color=INK, lw=1.0)
    ar.set_ylim(0.6, 1.4)
    tidy(ar, "Transient / AC, rms over log bins (shaded: +-10 %)", "frequency  (Hz)",
         "density ratio")
    legend(ar, loc="lower left")

    if "psd_hi" in psd:
        r = psd["psd_hi"]
        n = int(round(20e-6 / (r["t"][1] - r["t"][0])))
        tt = (r["t"][:n] - r["t"][0]) * 1e6
        vin = (r["v"][:n] - r["v"].mean()) / s["a0"] * 1e6
        at.plot(vin, tt, color=BLUE, lw=0.5)
        sd = np.std((r["v"] - r["v"].mean()) / s["a0"]) * 1e6
        for x in (-sd, sd):
            at.axvline(x, color=ORANGE, lw=1.2, ls="--")
        at.text(sd * 1.05, tt[-1] * 0.98, "+-1 sigma\n%.0f uV" % sd, color=ORANGE, fontsize=8, va="top")
        at.invert_yaxis()
        tidy(at, "v(outa) / A0, first 20 us of the record", "input-referred  (uV)", "time  (us)")

    fig.text(0.07, 0.965, "Transient-noise engine against the small-signal noise analysis",
             fontsize=14, color=INK, va="top")
    fig.text(0.07, 0.925,
             "%s, typical 27 C 3.3 V. Same bias as the AC noise bench (OTA parked at its crossing, "
             "A0 = %.1f V/V); every device noise source injecting in time.\nWelch PSD of v(outa) "
             "divided by |A(f)|^2 from the AC analysis at the same operating point."
             % (DUT_NAME, s["a0"]), fontsize=8.5, color=INK2, va="top", linespacing=1.5)
    path = os.path.join(ASSETS, STEM + "_psd.png")
    fig.savefig(path, facecolor=SURF)
    print("REPORT: wrote %s" % path)


def plot_ramp(ss, ramps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    nom = ramps[NOM]
    q = ramps.get(NOM + "_q")
    fig = plt.figure(figsize=(13, 10.4), dpi=160)
    fig.patch.set_facecolor(SURF)
    gs = fig.add_gridspec(3, 3, left=0.06, right=0.985, top=0.875, bottom=0.06,
                          hspace=0.5, wspace=0.34)

    # (a) the decision edge, 80 conversions overlaid
    ax = fig.add_subplot(gs[0, 0:2])
    tw = np.arange(-20e-9, 170e-9, 0.25e-9) * 1e9
    ax2 = ax.twinx()
    for o, dd in nom["waves"]:
        ax.plot(tw, o, color=BLUE, lw=0.4, alpha=0.35)
        ax2.plot(tw, dd, color=ORANGE, lw=0.4, alpha=0.35)
    if q is not None and q.get("waves"):
        o, dd = q["waves"][0]
        ax.plot(tw, o, color=INK, lw=1.2, ls="--", label="v(outa), noise off")
        ax2.plot(tw, dd, color=INK, lw=1.2, ls=":", label="dout, noise off")
    ax.plot([], [], color=BLUE, lw=1.5, label="v(outa), 80 noisy conversions")
    ax.plot([], [], color=ORANGE, lw=1.5, label="dout, 80 noisy conversions")
    ax.axvline(0, color=MUTED, lw=0.9)
    ax.text(1, 0.12, "ramp = held level", color=MUTED, fontsize=7.5)
    tidy(ax, "(a) The decision at %g V: time from the ideal crossing" % NOM_LEVEL, "t - t_ideal  (ns)",
         "v(outa)  (V)")
    ax2.set_ylabel("dout  (V)", fontsize=9, color=INK2)
    ax2.tick_params(labelsize=8, colors=INK2)
    ax2.spines["top"].set_visible(False)
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)
    legend(ax, loc="center left")
    # inset: zoom at the dout edge
    ins = ax.inset_axes([0.56, 0.42, 0.22, 0.5])
    for o, dd in nom["waves"]:
        ins.plot(tw, dd, color=ORANGE, lw=0.5, alpha=0.5)
    if q is not None and q.get("waves"):
        ins.plot(tw, q["waves"][0][1], color=INK, lw=1.0, ls=":")
    c0 = nom["delay_mean"] * 1e9
    ins.set_xlim(c0 - 4 * nom["sig_t"] * 1e9 - 1, c0 + 4 * nom["sig_t"] * 1e9 + 1)
    ins.set_ylim(0.8, 2.5)
    ins.tick_params(labelsize=6.5, colors=INK2)
    ins.set_title("dout edge, zoom", fontsize=7.5, color=INK2)
    ins.axhline(VDD / 2, color=MUTED, lw=0.6)

    # (b) trip-voltage histogram
    ah = fig.add_subplot(gs[0, 2])
    v = nom["vtrip"] * 1e6
    sd = nom["sig_v"] * 1e6
    bins = np.linspace(-4.5 * sd, 4.5 * sd, 41)
    ah.hist(v, bins=bins, density=True, color=BLUE, alpha=0.8, edgecolor=SURF, lw=0.5,
            label="%d conversions" % v.size)
    xs = np.linspace(bins[0], bins[-1], 300)
    ah.plot(xs, np.exp(-0.5 * (xs / sd) ** 2) / (sd * np.sqrt(2 * np.pi)), color=INK, lw=1.6,
            label="Gaussian, sigma %.1f uV" % sd)
    ah.set_ylim(0, 1.5 / (sd * np.sqrt(2 * np.pi)))
    tidy(ah, "(b) Trip point spread at %g V" % NOM_LEVEL, "slope x (delay - mean)  (uV)", "density")
    legend(ah, loc="upper left")

    # (c) S-curve
    asx = fig.add_subplot(gs[1, 0])
    vs = np.sort(v)
    pr = (np.arange(vs.size) + 0.5) / vs.size
    from math import erf
    xs = np.linspace(-4 * sd, 4 * sd, 300)
    asx.plot(xs, [0.5 * (1 + erf(x / (sd * np.sqrt(2)))) for x in xs], color=INK, lw=1.6,
             label="Gaussian CDF, sigma %.1f uV" % sd)
    asx.plot(vs, pr, ".", color=BLUE, ms=2.5, label="simulated")
    lsb_uv = LSB * 1e6
    asx.text(0.98, 0.04, "1/4 LSB noise budget = %.0f uV rms at the pins,\n%.0fx the measured sigma"
             % (ALPHA * lsb_uv / 4, ALPHA * lsb_uv / 4 / sd),
             ha="right", fontsize=7.5, color=GREEN, transform=asx.transAxes)
    asx.set_xlim(-4 * sd, 4 * sd)
    tidy(asx, "(c) S-curve: P(dout has fallen) vs ramp overdrive", "overdrive about the mean trip  (uV)",
         "probability")
    legend(asx, loc="upper left")

    # (d) sigma per level vs AC predictions
    ad = fig.add_subplot(gs[1, 1])
    lv = [r for r in sorted(ramps.values(), key=lambda r: r["level"])
          if r["k"] == 1.0 and r["nscale"] > 0 and r["fmax"] == FMAX]
    x = np.array([r["level"] for r in lv])
    ad.errorbar(x, [r["sig_v"] * 1e6 for r in lv], yerr=[r["sig_v_ci"] * 1e6 for r in lv],
                fmt="o", color=BLUE, ms=7, capsize=4, zorder=5, label="transient noise, total")
    ad.plot(x, [r["sig_fast_v"] * 1e6 for r in lv], "s", color=GREEN, ms=6, zorder=5,
            label="transient, conversion-to-conversion")
    ad.plot(x, [ss[r["level"]]["win"] * 1e6 for r in lv], "--", color=ORANGE, lw=1.5,
            marker="^", label="AC: 1 Hz - 3.18 MHz window")
    ad.plot(x, [ss[r["level"]]["own"] * 1e6 for r in lv], "--", color=AMBER, lw=1.5,
            marker="v", label="AC: OTA own band")
    ad.plot(x, [r["pred_slew"] * 1e6 for r in lv], ":", color=PINK, lw=1.8, marker="D",
            label="AC: sigma(outa) / outa slew")
    if q is not None:
        ad.plot([NOM_LEVEL], [q["sig_v"] * 1e6], "x", color=INK, ms=8, label="noise off (numerical floor)")
    ad.set_ylim(0, None)
    ad.set_xticks(x)
    tidy(ad, "(d) Input-referred noise per level, 8-bit ramp", "held level  (V)", "sigma  (uV rms)")
    ad.set_ylim(0, 150)
    legend(ad, loc="lower center", ncol=2, fontsize=6.8)

    # (e) sigma vs slope
    ae = fig.add_subplot(gs[1, 2])
    sl = [r for r in sorted(ramps.values(), key=lambda r: r["k"])
          if r["level"] == NOM_LEVEL and r["nscale"] > 0 and r["fmax"] == FMAX]
    k = np.array([r["k"] for r in sl])
    ae.errorbar(k, [r["sig_v"] * 1e6 for r in sl], yerr=[r["sig_v_ci"] * 1e6 for r in sl],
                fmt="o-", color=BLUE, ms=7, capsize=4, label="transient noise, total")
    ae.plot(k, [r["sig_fast_v"] * 1e6 for r in sl], "s-", color=GREEN, ms=6,
            label="transient, conversion-to-conversion")
    ae.plot(k, [r["pred_slew"] * 1e6 for r in sl], "D:", color=PINK, ms=5,
            label="AC: sigma(outa) / outa slew")
    ae.axhline(ss[NOM_LEVEL]["win"] * 1e6, color=ORANGE, ls="--", lw=1.5, label="AC: 3.18 MHz window")
    ae.axhline(ss[NOM_LEVEL]["own"] * 1e6, color=AMBER, ls="--", lw=1.5, label="AC: own band")
    if NOM + "_f1g" in ramps:
        f1 = ramps[NOM + "_f1g"]
        ae.errorbar([1.0], [f1["sig_v"] * 1e6], yerr=[f1["sig_v_ci"] * 1e6], fmt="*", color=INK,
                    ms=10, capsize=3, label="noisefmax 1 GHz")
    ae.set_xscale("log")
    ae.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ae.set_xticks(k)
    ae.set_xticklabels(["%gx" % v for v in k])
    ae.set_ylim(0, None)
    tidy(ae, "(e) Noise vs ramp slope at %g V" % NOM_LEVEL, "ramp slope / nominal pin slope",
         "sigma  (uV rms)")
    ae.set_ylim(0, 230)
    legend(ae, loc="upper left", fontsize=6.8)

    # (f) delay trace over the record
    af = fig.add_subplot(gs[2, 0:2])
    for tag, col in ((tag_of(0.5), GREEN), (NOM, BLUE), (tag_of(2.0), ORANGE)):
        if tag in ramps:
            r = ramps[tag]
            af.plot(np.arange(r["delays"].size), (r["delays"] - r["delays"].mean()) * r["slope"] * 1e6,
                    color=col, lw=0.6, label="%g V: sigma %.1f uV, delay %.1f ns"
                    % (r["level"], r["sig_v"] * 1e6, r["delay_mean"] * 1e9))
    if q is not None:
        af.plot(np.arange(q["delays"].size), (q["delays"] - q["delays"].mean()) * q["slope"] * 1e6,
                color=INK, lw=1.4, label="%g V, noise off: sigma %.2f uV" % (NOM_LEVEL, q["sig_v"] * 1e6))
    tidy(af, "(f) Trip point, conversion by conversion (%.2f us per conversion)" % (nom["record_s"] / nom["nconv"] * 1e6),
         "conversion index", "trip - mean  (uV)")
    legend(af, loc="upper right", ncol=2)

    # (g) table
    ag = fig.add_subplot(gs[2, 2])
    ag.axis("off")
    rows = [("",) + tuple("%g V" % l for l in LEVELS)]
    by = {r["level"]: r for r in lv}

    def row(label, fn):
        rows.append((label,) + tuple(fn(by[l]) if l in by else "-" for l in LEVELS))
    row("tran sigma (uV)", lambda r: "%.1f" % (r["sig_v"] * 1e6))
    row("  in LSB at the ADC input", lambda r: "%.4f" % (r["sig_v"] / (ALPHA * LSB)))
    row("  jitter (ps)", lambda r: "%.0f" % (r["sig_t"] * 1e12))
    row("conv-to-conv (uV)", lambda r: "%.1f" % (r["sig_fast_v"] * 1e6))
    row("AC window (uV)", lambda r: "%.1f" % (ss[r["level"]]["win"] * 1e6))
    row("AC own band (uV)", lambda r: "%.1f" % (ss[r["level"]]["own"] * 1e6))
    row("AC noise/slew (uV)", lambda r: "%.1f" % (r["pred_slew"] * 1e6))
    row("tran / AC window", lambda r: "%.2f" % (r["sig_v"] / ss[r["level"]]["win"]))
    row("P(code flip)", lambda r: "%.4f" % r["p_code_flip"])
    row("budget 1/4 LSB (pins)", lambda r: "%.0f uV" % (NOISE_BUDGET * ALPHA * 1e6))
    tb = ag.table(cellText=rows, loc="center", cellLoc="right",
                  colWidths=[0.40] + [0.6 / len(LEVELS)] * len(LEVELS))
    tb.auto_set_font_size(False)
    tb.set_fontsize(7.8)
    for (i, j), cell in tb.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_text_props(color=INK if i == 0 or j == 0 else INK2)
        if i == 0:
            cell.set_facecolor("#f6f8fa")
    tb.scale(1, 1.32)
    ag.set_title("(g) Summary, typical 27 C 3.3 V", fontsize=10, color=INK, loc="left", pad=22)

    fig.text(0.06, 0.975, "Comparator noise under the 8-bit ramp: VACASK transient noise",
             fontsize=15, color=INK, va="top")
    fig.text(0.06, 0.94,
             "%s (PMOS 5T + starved inverter + output inverter), ideal held level on inp, sawtooth at %.2f kV/s%s on inn, "
             "all device noise on (thermal + flicker, SDE, "
             "noisefmax 200 MHz).\n%d conversions per level in one record. sigma = ramp slope x std(dout "
             "crossing instant); conversion-to-conversion = std of successive differences / sqrt 2."
             % (DUT_NAME, NOM_K * SLOPE * 1e-3,
                (" (alpha %.3f x the 117.19 kV/s conversion slope: the ramp as the top plate passes it; "
                 "1 LSB = %.2f mV at the pins)" % (ALPHA, ALPHA * LSB * 1e3)),
                nom["nconv"]), fontsize=8.5, color=INK2, va="top", linespacing=1.5)
    path = os.path.join(ASSETS, STEM + ".png")
    fig.savefig(path, facecolor=SURF)
    print("REPORT: wrote %s" % path)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "gen":
        sys.exit(gen(int(sys.argv[2]) if len(sys.argv) > 2 else 1))
    if mode == "reduce":
        sys.exit(reduce())
    print("usage: trannoise.py gen 1|2 | reduce")
    sys.exit(2)
