"""gm/Id sizing and design-space exploration for the PMOS-input 5T comparator.

    ./container.sh 'python3 size_p5t.py'          # sample, Pareto, select
    ./container.sh 'SIZING_EMIT=1 python3 size_p5t.py'   # also rewrite the netlist

Reads the pygmid tables built by `make gmid-lut`
(`simulations/gf180_gmid_lut/work/{n,p}fet_03v3.pkl`) by path; it never
copies them. Writes `data/p5t_pareto.csv`, `data/p5t_sizing.json` and
`work/cmp_p5t_8b.spice`, and prints one scalar per line so the run script
can reduce it.

Method is the repo's established one (`simulations/gf180_gmid_lut/pareto_dse.py`,
after Boris Murmann's CircuitInsights2026 example3): sample the design space
at random, evaluate every sample analytically through pygmid lookups, filter
to the non-dominated set, then select by an explicit stated rule. Widths are
never design variables -- they are DERIVED as W = ID / ID_W.

WHAT IS BEING SIZED

    .subckt cmp inp inn dout clk vdd vss nbias pbias
      XINP  left inp tail vdd  pfet   <- inp is the HELD SIGNAL
      XINN  outa inn tail vdd  pfet   <- inn is the RAMP
      XLOADD left left vss vss nfet   <- mirror diode node
      XLOADM outa left vss vss nfet
      XTAIL  tail pbias vdd vdd pfet
      + 20 fF on outa and a two-inverter output buffer

The signal input's drain is the mirror diode node, not the high-impedance
output. That is already the low-kickback arrangement and it is kept: swapping
the inputs would put the full output swing behind the hold node's Cgd.

THE FOUR DESIGN VARIABLES PER DEVICE, AND WHAT EACH BUYS

  (gm/Id)_in   headroom. VSG falls as gm/Id rises, and at the 2.0 V top of
               the input range the tail's remaining headroom is
               VDD - VCM - VSG_in. This is the binding constraint of the
               whole topology.
  L_in         drift. See the offset model below: the level-dependent part
               of the offset is set by how much (gds/Id) of the input pair
               moves as its own VDS is dragged around by the common mode,
               and that is what a long channel flattens.
  (gm/Id)_load the mirror diode node's swing is 1/(gm/Id)_load, and that
               swing is one of the two things Cgd of the signal input
               couples onto the hold capacitor.
  (gm/Id)_tail Vdsat_tail = 2/(gm/Id)_tail eats the headroom that (gm/Id)_in
               just bought.
  I_branch     everything. Width scales with it at fixed gm/Id, so power,
               kickback and speed all move together.

THE OFFSET MODEL (the reason this is a resize and not a new topology)

Balance at the trip point requires the mirror's output current to equal the
input pair's. Both legs are mismatched by the same voltage, (V_outa - V_left):
the mirror sees it across its two drains, and the input pair sees it across
theirs. Referring the resulting current error back through gm,

    V_os(VCM) = [ (gds/Id)_load + (gds/Id)_in(VCM) ] * (V_outa - V_left)
                / (gm/Id)_in

For a comparator shared by four cells, V_os itself is a single constant that
the required multi-point transfer-curve calibration removes. What does not
calibrate out is its DRIFT with the common mode, because the common mode is
the signal. Only one term moves: the input pair's own VDS is V_tail - V_drain
and V_tail follows VCM, so

    drift = [ (gds/Id)_in(VCM_hi) - (gds/Id)_in(VCM_lo) ]
            * (V_outa - V_left) / (gm/Id)_in

which is a level-dependent code offset, i.e. INL. Note that drift and delay
spread are the SAME budget written twice: a crossing-delay spread is just an
input-referred drift divided by the ramp slope, and
1.465 mV / 117.2 mV/us = 12.5 ns = 0.25 count exactly.

This model deliberately assumes the tail stays saturated. When it does not,
the real drift is several times worse -- which is exactly what the recorded
sizing does at 2.0 V. The headroom constraint below is what keeps the sizing
out of the regime where this model is optimistic, and ngspice remains the
authority on the number.

CALIBRATION, AND WHY THE KICKBACK PROXY HAS A FITTED CONSTANT

Kickback is charge injected onto the hold node through the signal input
device. Two paths carry it: Cgd onto the mirror diode node, which swings
1/(gm/Id)_load, and Cgs onto the tail node, which swings a comparable
fraction of 1/(gm/Id)_in as the pair steers. Both are proportional to W_in,
which is the lever. The absolute charge also depends on the large-signal
trajectory, which no small-signal table knows, so the model carries ONE
scalar KCAL, fixed by requiring it to reproduce the recorded sizing's
measured kickback. Relative comparisons across the design space are then
trustworthy; the absolute number is ngspice's to report, and the run script
prints predicted against measured for both sizings so the calibration is
visible and falsifiable rather than hidden.
"""

import json
import os
import sys

import numpy as np
from pygmid import Lookup as lk

# ---------------------------------------------------------------- conversion
VDD = 3.3
# The input range is a parameter, not a constant, because the whole binding
# mechanism traces back to it: headroom at the TOP of the range is what forces
# the input pair into weak inversion, weak inversion is what makes it wide,
# and width is what causes the kickback that binds. Narrowing the range buys
# headroom -- but it also shrinks the LSB, because 8 bits still has to fit in
# it, which tightens every voltage budget. The two effects pull opposite ways
# and the net is not obvious, so it is computed rather than argued.
#   VCM_HI=1.6 ./container.sh 'SIZING_NOWRITE=1 python3 size_p5t.py'
VCM_LO = float(os.environ.get("VCM_LO", 0.5))
VCM_HI = float(os.environ.get("VCM_HI", 2.0))
NBITS = 8
TCOUNT = 50e-9                      # frozen 20 MHz conversion clock
LSB = (VCM_HI - VCM_LO) / 2 ** NBITS
SLOPE = LSB / TCOUNT                # 117.2 mV/us over the default range
BUDGET_LSB = 0.25                   # each uncalibratable term gets a quarter
KICK_BUDGET = BUDGET_LSB * LSB      # 1.465 mV into CHOLD
SPREAD_BUDGET = BUDGET_LSB * TCOUNT # 12.5 ns of crossing-delay spread
DRIFT_BUDGET = BUDGET_LSB * LSB     # 1.465 mV over the common-mode range
CHOLD = 1e-12                       # the bench's hold capacitor
C_OUTA_FIXED = 20e-15               # COUTA in the netlist
C_BUF_IN = 12e-15                   # Cgg of the first inverter pair, approx
V_SWING_REF = 0.30                  # reference output excursion, delay proxy
HEADROOM_MARGIN = 0.20              # tail VDS above Vdsat at VCM_HI
KT = 1.380649e-23 * 300.0
GAMMA_N = 2.0 / 3.0                 # long-channel thermal noise factor

# Power budget: what the selected 8-bit comparator of the recorded study
# (`sfbuf`) spends. Matching it makes the comparison fair rather than
# flattering.
POWER_BUDGET = 0.42e-3

# Minimum first-stage gain. The two-inverter buffer contributes about 100 V/V,
# and the comparator must resolve a quarter LSB from the rail, so
# A_ota >= VDD / (0.25*LSB * A_buf).
A_BUF = 100.0
GAIN_MIN = VDD / (BUDGET_LSB * LSB * A_BUF)

# ------------------------------------------------- the sizing being replaced
REF = dict(
    l_in=0.5, w_in=40e-6, nf_in=10,
    l_load=0.5, w_load=20e-6, nf_load=10,
    l_tail=1.0, w_tail=20e-6, nf_tail=10,
    iref=50e-6,
)
REF_KICK_MEAS = 2.93e-3   # gf180_comparator_8bit RESULTS.md, 1 pF, worst level
REF_DRIFT_MEAS = 3.35e-3  # same source, over 0.5-2.0 V

ETA_TAIL = 0.7            # tail-node excursion as a fraction of 1/(gm/Id)_in

LUT_DIR = os.environ.get(
    "GMID_LUT_DIR", "/foss/designs/simulations/gf180_gmid_lut/work"
)

L_CHOICES_IN = np.array([0.4, 0.5, 0.6, 0.8, 1.0, 2.0, 3.0])
L_CHOICES_LOAD = np.array([0.5, 0.6, 0.8, 1.0, 2.0])
# The tail mirrors the testbench's diode-connected reference leg, so it
# shares that device's channel length -- a mirror whose two halves have
# different L is not a ratio, it is two different devices at one VGS.
L_REF = 1.0
W_REF = 20e-6
IREF_MIN, IREF_MAX = 1e-6, 100e-6

# Gate-area floors, in um^2. Random Vth mismatch goes as AVT/sqrt(W*L) and the
# gm/Id tables know nothing about it, so without a floor the optimiser buys
# every small-signal target with devices too small to match. These are sizing
# practice, not PDK data: no AVT from the PDK is used anywhere here and
# statistical mismatch stays an OPEN row in the verification matrix. The
# reported sigma below is parametric in AVT for that reason.
WL_MIN_IN = 4.0
WL_MIN_LOAD = 2.0
WL_MIN_TAIL = 10.0
AVT_ASSUMED = 6e-3      # V*um, an ASSUMPTION for reporting only

# pygmid takes an array for GM_ID but scalars for L/VDS/VSB, so lookups are
# grouped by (L, VDS bin, VSB bin). 50 mV bins; the tables are on a 25 mV grid.
VDS_BIN = 0.05
VSB_GRID = np.array([0.0, 0.2, 0.4])


def grouped(table, out, gm_id, L, vds, vsb):
    """Vectorised lookup: one pygmid call per distinct (L, VDS, VSB) group."""
    res = np.empty(gm_id.shape, dtype=np.float64)
    vds_b = np.round(np.clip(vds, 0.05, 3.3) / VDS_BIN) * VDS_BIN
    vsb_b = VSB_GRID[np.abs(np.asarray(vsb)[:, None] - VSB_GRID[None, :]).argmin(1)]
    key = (L * 1e4).astype(np.int64) * 10_000_000 \
        + (vds_b * 1e4).astype(np.int64) * 1000 \
        + (vsb_b * 1e4).astype(np.int64)
    for k in np.unique(key):
        m = key == k
        res[m] = np.asarray(
            table.look_up(
                out, GM_ID=gm_id[m], L=float(L[m][0]),
                VDS=float(vds_b[m][0]), VSB=float(vsb_b[m][0]),
            )
        ).ravel()
    return res


def grouped_at_vgs(table, out, vgs, L, vds, vsb):
    """Lookup for a device whose GATE VOLTAGE is imposed by a mirror.

    The tail is not free to sit at a chosen gm/Id: its VGS is whatever the
    diode-connected reference leg develops, so its current density, its gm/Id
    and its Vdsat all follow from that leg's geometry and current. Sampling
    gm/Id for the tail and deriving W from it -- which is right for every
    other device here -- silently invents a bias voltage the circuit does not
    have.
    """
    res = np.empty(np.shape(vgs), dtype=np.float64)
    vgs_b = np.round(np.clip(vgs, 0.0, 3.3) / 0.025) * 0.025
    vds_b = np.round(np.clip(vds, 0.05, 3.3) / VDS_BIN) * VDS_BIN
    key = (L * 1e4).astype(np.int64) * 10_000_000 \
        + (vgs_b * 1e4).astype(np.int64) * 1000 \
        + (vds_b * 1e4).astype(np.int64)
    for k in np.unique(key):
        m = key == k
        res[m] = np.asarray(
            table.look_up(out, VGS=float(vgs_b[m][0]), L=float(L[m][0]),
                          VDS=float(vds_b[m][0]), VSB=float(vsb))
        ).ravel()
    return res


def grouped_vgs(table, gm_id, L, vds, vsb):
    res = np.empty(gm_id.shape, dtype=np.float64)
    vds_b = np.round(np.clip(vds, 0.05, 3.3) / VDS_BIN) * VDS_BIN
    vsb_b = VSB_GRID[np.abs(np.asarray(vsb)[:, None] - VSB_GRID[None, :]).argmin(1)]
    key = (L * 1e4).astype(np.int64) * 10_000_000 \
        + (vds_b * 1e4).astype(np.int64) * 1000 \
        + (vsb_b * 1e4).astype(np.int64)
    for k in np.unique(key):
        m = key == k
        res[m] = np.asarray(
            table.look_upVGS(
                GM_ID=gm_id[m], L=float(L[m][0]),
                VDS=float(vds_b[m][0]), VSB=float(vsb_b[m][0]),
            )
        ).ravel()
    return res


def pareto_mask(costs):
    """Boolean mask of non-dominated rows; every column is minimised."""
    n = costs.shape[0]
    keep = np.ones(n, dtype=bool)
    order = np.argsort(costs[:, 0], kind="stable")
    for i in order:
        if not keep[i]:
            continue
        dominated = (
            np.all(costs <= costs[i], axis=1) & np.any(costs < costs[i], axis=1)
        )
        if np.any(dominated & keep):
            keep[i] = False
    return keep


def operating_point(pfet, nfet, gmid_in, l_in, gmid_load, l_load,
                    gmid_tail, l_tail, id_branch, vcm, well_tail=None):
    """Self-consistent bias solve at one common mode.

    V_left sets the input pair's drain, the input pair's VSG sets V_tail,
    and V_tail sets the input pair's own VSB and the tail's VDS. Three
    passes are enough; the coupling is weak.

    `well_tail` is a boolean per sample: True puts the input pair in its
    own n-well tied to the tail, so VSB = 0 and the body effect vanishes.
    False is the recorded connection, n-well on vdd, where VSB is the
    tail's own headroom and |Vth| rises by roughly 100 mV -- headroom the
    topology does not have to spare at the 2.0 V top of the range.
    """
    v_left = np.full_like(gmid_load, 0.75)
    vsg_in = np.full_like(gmid_in, 0.95)
    for _ in range(3):
        v_left = grouped_vgs(nfet, gmid_load, l_load, v_left, np.zeros_like(v_left))
        v_tail = vcm + vsg_in
        vsb_in = np.clip(VDD - v_tail, 0.0, 0.4)
        if well_tail is not None:
            vsb_in = np.where(well_tail, 0.0, vsb_in)
        vds_in = np.clip(v_tail - v_left, 0.05, 3.3)
        vsg_in = grouped_vgs(pfet, gmid_in, l_in, vds_in, vsb_in)
    v_tail = vcm + vsg_in
    vsb_in = np.clip(VDD - v_tail, 0.0, 0.4)
    if well_tail is not None:
        vsb_in = np.where(well_tail, 0.0, vsb_in)
    vds_in = np.clip(v_tail - v_left, 0.05, 3.3)
    return dict(v_left=v_left, vsg_in=vsg_in, v_tail=v_tail,
                vsb_in=vsb_in, vds_in=vds_in)


def inverter_trip(vthn, vthp, ratio):
    """First-order switching threshold of the buffer's first inverter.

    ratio is sqrt(beta_p/beta_n). V_outa settles here at the decision, so
    (V_outa - V_left) -- the voltage that drives the whole offset model --
    is partly a buffer sizing choice, not only an OTA one.
    """
    return (vthn + ratio * (VDD - vthp)) / (1.0 + ratio)


def snap_width(w_m):
    """Snap to a 0.1 um drawn grid and pick a finger count near 4 um/finger."""
    w_um = max(0.44, round(float(w_m) * 1e6, 1))
    nf = int(np.clip(round(w_um / 4.0), 1, 20))
    while w_um / nf < 0.22 and nf > 1:
        nf -= 1
    return round(w_um, 2), nf


def main():
    # PINNED. The selection is a random search, so it moves by a few per cent
    # with the sample count: 40000 samples put the minimax design's worst term
    # at 1.92x budget, 60000 at 1.85x. That difference is far inside the
    # model's error against measurement, and reproducibility is worth more
    # than chasing it, so both this script and run.sh use these numbers and
    # the committed netlists are the ones they produce. Override only to
    # explore; the drift check in run.sh will then tell you the committed
    # netlists no longer match, which is correct.
    points = int(os.environ.get("PARETO_POINTS", 40000))
    seed = int(os.environ.get("PARETO_SEED", 20260916))
    rng = np.random.default_rng(seed)

    pfet = lk(f"{LUT_DIR}/pfet_03v3.pkl")
    nfet = lk(f"{LUT_DIR}/nfet_03v3.pkl")

    vthn = float(np.asarray(nfet.look_up("VT", VGS=1.0, L=0.5, VDS=1.65, VSB=0.0)).ravel()[0])
    vthp = float(np.asarray(pfet.look_up("VT", VGS=1.0, L=0.5, VDS=1.65, VSB=0.0)).ravel()[0])

    print("INFO: --- PMOS 5T comparator, gm/Id sizing for 8 bits over 0.5-2.0 V ---")
    print(f"vcm_lo_v = {VCM_LO:.4g}")
    print(f"vcm_hi_v = {VCM_HI:.4g}")
    print(f"lsb_v = {LSB:.6g}")
    print(f"slope_v_per_s = {SLOPE:.6g}")
    print(f"kick_budget_v = {KICK_BUDGET:.6g}")
    print(f"drift_budget_v = {DRIFT_BUDGET:.6g}")
    print(f"gain_min = {GAIN_MIN:.4g}")
    print(f"vthn_v = {vthn:.4g}")
    print(f"vthp_v = {vthp:.4g}")

    # ------------------------------------------------ calibrate the proxies
    # One scalar, KCAL, fixed by the recorded sizing's measured kickback.
    ref = calibrate(pfet, nfet, vthn, vthp)
    kcal = REF_KICK_MEAS / ref["kick_raw"]
    # The drift model assumes a saturated tail and a small-signal gds
    # from the tables. Measured on the recorded sizing it is optimistic
    # by this factor; the same scalar is applied to every candidate.
    dcal = REF_DRIFT_MEAS / ref["drift"]
    print(f"ref_gmid_in = {ref['gmid_in']:.4g}")
    print(f"ref_gmid_load = {ref['gmid_load']:.4g}")
    print(f"ref_gmid_tail = {ref['gmid_tail']:.4g}")
    print(f"ref_vleft_v = {ref['v_left']:.4g}")
    print(f"ref_vtail_hi_v = {ref['v_tail_hi']:.4g}")
    print(f"ref_headroom_hi_v = {ref['headroom_hi']:.4g}")
    print(f"ref_vdsat_tail_v = {ref['vdsat_tail']:.4g}")
    print(f"ref_drift_pred_v = {ref['drift']:.4g}")
    print(f"ref_drift_meas_v = {REF_DRIFT_MEAS:.4g}")
    print(f"kick_calibration = {kcal:.4g}")
    print(f"drift_calibration = {dcal:.4g}")
    if ref["headroom_hi"] < ref["vdsat_tail"]:
        print(
            "REPORT: the recorded sizing's tail is out of saturation at "
            f"VCM=2.0 V: headroom {ref['headroom_hi']*1e3:.0f} mV against "
            f"Vdsat {ref['vdsat_tail']*1e3:.0f} mV. The analytic drift model "
            f"({ref['drift']*1e3:.2f} mV) is a lower bound there and the "
            f"measured {REF_DRIFT_MEAS*1e3:.2f} mV is the real number."
        )

    # ------------------------------------------------------ sample the space
    gmid_in = rng.uniform(7.0, 20.0, points)
    l_in = rng.choice(L_CHOICES_IN, points)
    gmid_load = rng.uniform(8.0, 26.0, points)
    l_load = rng.choice(L_CHOICES_LOAD, points)
    # gm/Id of the REFERENCE LEG. The tail inherits its VGS, so this one
    # variable fixes the tail's inversion level and therefore Vdsat_tail --
    # the headroom the whole topology lives or dies on. IREF is derived
    # from it, not chosen: IREF = ID_W(gm/Id, L_REF) * W_REF.
    gmid_tail = rng.uniform(6.0, 24.0, points)
    l_tail = np.full(points, L_REF)
    id_branch = 10 ** rng.uniform(np.log10(2e-6), np.log10(63e-6), points)
    # The one connectivity choice in the space: input-pair n-well on vdd
    # (the recorded connection, pure resize) or on the tail (no body
    # effect, ~160 mV of headroom back, one extra n-well of area).
    well_tail = rng.random(points) < 0.5
    inv_ratio = rng.uniform(0.40, 1.20, points)  # sqrt(beta_p/beta_n) of BUF1/2

    op_hi = operating_point(pfet, nfet, gmid_in, l_in, gmid_load, l_load,
                            gmid_tail, l_tail, id_branch, VCM_HI, well_tail)
    op_lo = operating_point(pfet, nfet, gmid_in, l_in, gmid_load, l_load,
                            gmid_tail, l_tail, id_branch, VCM_LO, well_tail)
    op_mid = operating_point(pfet, nfet, gmid_in, l_in, gmid_load, l_load,
                             gmid_tail, l_tail, id_branch, 0.5 * (VCM_LO + VCM_HI), well_tail)

    v_left = op_mid["v_left"]
    v_outa = inverter_trip(vthn, vthp, inv_ratio)
    dv_mirror = v_outa - v_left

    # Headroom at the top of the range is the binding constraint.
    headroom = VDD - op_hi["v_tail"]
    vdsat_tail = 2.0 / gmid_tail

    # Widths are derived, never sampled.
    w_in = id_branch / grouped(pfet, "ID_W", gmid_in, l_in,
                               op_mid["vds_in"], op_mid["vsb_in"])
    w_load = id_branch / grouped(nfet, "ID_W", gmid_load, l_load,
                                 v_left, np.zeros_like(v_left))
    # Reference leg: diode-connected, so VDS = VSG. Two passes converge.
    vsg_ref = np.full(points, 1.0)
    for _ in range(3):
        vsg_ref = grouped_vgs(pfet, gmid_tail, l_tail, vsg_ref,
                              np.zeros_like(vsg_ref))
    idw_ref = grouped(pfet, "ID_W", gmid_tail, l_tail, vsg_ref,
                      np.zeros_like(vsg_ref))
    iref = idw_ref * W_REF
    # Tail width is the mirror ratio, nothing else.
    w_tail = W_REF * (2.0 * id_branch) / iref
    # And the current it actually delivers at the top of the range, where
    # its own VDS is only `headroom`. The recorded sizing loses 6 % here;
    # this is the prediction the AC bench's id_tail measures directly.
    idw_tail_hi = grouped_at_vgs(pfet, "ID_W", vsg_ref, l_tail,
                                 np.clip(headroom, 0.05, 3.3), 0.0)
    tail_sag = 1.0 - np.clip(idw_tail_hi / idw_ref, 0.0, 1.0)

    # Offset drift: only the input pair's (gds/Id) moves with the common mode.
    gds_id_in_hi = gmid_in / grouped(pfet, "GM_GDS", gmid_in, l_in,
                                     op_hi["vds_in"], op_hi["vsb_in"])
    gds_id_in_lo = gmid_in / grouped(pfet, "GM_GDS", gmid_in, l_in,
                                     op_lo["vds_in"], op_lo["vsb_in"])
    gds_id_in_mid = gmid_in / grouped(pfet, "GM_GDS", gmid_in, l_in,
                                      op_mid["vds_in"], op_mid["vsb_in"])
    gds_id_load = gmid_load / grouped(nfet, "GM_GDS", gmid_load, l_load,
                                      v_left, np.zeros_like(v_left))

    drift_raw = np.abs(gds_id_in_hi - gds_id_in_lo) * np.abs(dv_mirror) / gmid_in
    drift = dcal * drift_raw
    offset_static = (gds_id_in_mid + gds_id_load) * np.abs(dv_mirror) / gmid_in
    gain_ota = gmid_in / (gds_id_in_mid + gds_id_load)

    # Kickback: both coupling paths scale with W_in.
    cgd_w = grouped(pfet, "CGD_W", gmid_in, l_in, op_mid["vds_in"], op_mid["vsb_in"])
    cgs_w = grouped(pfet, "CGS_W", gmid_in, l_in, op_mid["vds_in"], op_mid["vsb_in"])
    kick_raw = w_in * (cgd_w / gmid_load + ETA_TAIL * cgs_w / gmid_in) / CHOLD
    kick = kcal * kick_raw

    # Crossing-delay spread, modelled rather than proxied.
    #
    # The first version of this used C_out/gm, the repo's established
    # gm-limited proxy. That is the UNITY-GAIN time constant and it is the
    # wrong one: the node that decides is high impedance, so its time
    # constant is C_out/gds = A_ota * C_out/gm -- larger by the whole DC
    # gain. The design that proxy selected measured a 133 ns delay spread
    # against a 12.5 ns budget, because its real tau was 176 ns while the
    # proxy reported 6.4 ns. Both terms below are what the measurement says
    # actually sets the spread:
    #
    #   drift/SLOPE   the input-referred offset drift, as a time
    #   |tau_hi-tau_lo|  the output node's own time constant moving with the
    #                 common mode, because gds_in does
    #
    # Adding them is conservative: the two are correlated through gds_in, so
    # the sum over-predicts. Validation against three measured designs is in
    # RESULTS.md, and being conservative here only makes the selection safer.
    cdd_w_in = grouped(pfet, "CDD_W", gmid_in, l_in, op_mid["vds_in"], op_mid["vsb_in"])
    cdd_w_ld = grouped(nfet, "CDD_W", gmid_load, l_load, v_left, np.zeros_like(v_left))
    c_outa = w_in * cdd_w_in + w_load * cdd_w_ld + C_OUTA_FIXED + C_BUF_IN
    gm_in = gmid_in * id_branch
    gds_out_hi = (gds_id_in_hi + gds_id_load) * id_branch
    gds_out_lo = (gds_id_in_lo + gds_id_load) * id_branch
    gds_out_mid = (gds_id_in_mid + gds_id_load) * id_branch
    tau_hi = c_outa / gds_out_hi
    tau_lo = c_outa / gds_out_lo
    tau_mid = c_outa / gds_out_mid
    slew = c_outa * V_SWING_REF / (2.0 * id_branch)

    power = VDD * 2.0 * id_branch
    delay_spread = drift / SLOPE + np.abs(tau_hi - tau_lo)

    # Input-referred thermal noise. Integrating the input pair's and the
    # load's white noise over the output node's own bandwidth collapses to
    # a kT/C form, which is why C_outa appears and gm does not: raising gm
    # widens the band by as much as it lowers the density. Flicker is not
    # in this estimate; ngspice .noise in tb_noise.spice is the authority.
    vn_in = np.sqrt(2.0 * GAMMA_N * KT / c_outa
                    * (1.0 + gmid_load / gmid_in))

    # Constraints, kept as named parts so the tool can say WHICH one is
    # binding. A design-space explorer that only reports "0 feasible" has
    # told you nothing: the whole question is which physical limit you are
    # up against, and that is answered by counting how many samples pass
    # every constraint except one.
    cons = {
        "headroom": headroom >= vdsat_tail + HEADROOM_MARGIN,
        "gain": gain_ota >= GAIN_MIN,
        "kickback": kick <= KICK_BUDGET,
        "trip_drift": drift <= DRIFT_BUDGET,
        "delay_spread": delay_spread <= SPREAD_BUDGET,
        "tau_out": tau_mid <= 4.0 * TCOUNT,
        "slew": slew <= 0.5 * TCOUNT,
        "noise": vn_in <= BUDGET_LSB * LSB,
        "power": power <= POWER_BUDGET,
        "iref_range": (iref >= IREF_MIN) & (iref <= IREF_MAX),
        "tail_sag": tail_sag <= 0.02,
        "widths": ((w_in >= 1e-6) & (w_in <= 200e-6)
                   & (w_load >= 0.5e-6) & (w_load <= 200e-6)
                   & (w_tail >= 1e-6) & (w_tail <= 200e-6)),
        "gate_area": ((w_in * 1e6 * l_in >= WL_MIN_IN)
                      & (w_load * 1e6 * l_load >= WL_MIN_LOAD)
                      & (w_tail * 1e6 * l_tail >= WL_MIN_TAIL)),
        "buffer_pmos": 4.0 * inv_ratio ** 2 * 4.0 >= 1.0,
        "outa_window": (v_outa > v_left + 0.15) & (v_outa < VDD - 0.6),
    }
    feasible = np.ones(points, dtype=bool)
    for m in cons.values():
        feasible &= m
    for name, m in sorted(cons.items()):
        others = np.ones(points, dtype=bool)
        for k, v in cons.items():
            if k != name:
                others &= v
        print(f"pass_{name} = {int(m.sum())}")
        print(f"relaxing_{name} = {int(others.sum())}")

    print(f"samples = {points}")
    print(f"feasible = {int(feasible.sum())}")

    # Normalised violation of the three budgeted terms. A design scoring 1.0
    # sits exactly on budget; the minimax pick is the one whose WORST term is
    # least bad, which is the right fallback because the budget is a set of
    # simultaneous requirements and not a weighted sum.
    viol = np.maximum.reduce([
        kick / KICK_BUDGET, drift / DRIFT_BUDGET, delay_spread / SPREAD_BUDGET
    ])
    buildable = cons["headroom"] & cons["widths"] & cons["gate_area"] \
        & cons["power"] & cons["iref_range"] & cons["tail_sag"] \
        & cons["gain"] & cons["outa_window"] & cons["buffer_pmos"]
    if not np.any(buildable):
        print("FAIL: no sample satisfies even the buildability constraints")
        return 1
    bi_all = np.flatnonzero(buildable)[np.argmin(viol[buildable])]
    # Tie-break, stated so it can be argued with: tying the input pair's
    # n-well to the tail is a connectivity change to a recorded design, so it
    # has to EARN its place. If the best geometry-and-bias-only design comes
    # within 10 % of the best design overall on the worst budget term, the
    # smaller change wins. Ten per cent is inside this model's demonstrated
    # error against measurement, so a difference smaller than that is not a
    # result.
    pure_ok = buildable & ~well_tail
    bi = bi_all
    if np.any(pure_ok):
        bi_pure = np.flatnonzero(pure_ok)[np.argmin(viol[pure_ok])]
        print(f"minimax_all_ratio = {viol[bi_all]:.4g}")
        print(f"minimax_geometry_only_ratio = {viol[bi_pure]:.4g}")
        if viol[bi_pure] <= 1.10 * viol[bi_all]:
            bi = bi_pure
            print("REPORT: the best geometry-and-bias-only design is within "
                  "10 % of the best design overall on its worst budget term, "
                  "so the n-well tie is not taken: it would be a connectivity "
                  "change bought with a difference smaller than the model's "
                  "own error")
    print(f"minimax_worst_term_ratio = {viol[bi]:.4g}")
    print(f"minimax_kick_ratio = {kick[bi]/KICK_BUDGET:.4g}")
    print(f"minimax_drift_ratio = {drift[bi]/DRIFT_BUDGET:.4g}")
    print(f"minimax_spread_ratio = {delay_spread[bi]/SPREAD_BUDGET:.4g}")

    fallback = feasible.sum() < 20
    if fallback:
        print("REPORT: the budget is not simultaneously reachable anywhere in "
              "the sampled space; falling back to the design whose worst "
              f"budget term is least bad ({viol[bi]:.2f}x budget). This is a "
              "statement about the topology, not about the search.")
        feasible = np.zeros(points, dtype=bool)
        feasible[bi] = True
        # keep a neighbourhood so the frontier plot still has a cloud
        near = np.flatnonzero(buildable & (viol <= max(1.0, viol[bi] * 1.5)))
        feasible[near] = True
        print(f"fallback_pool = {int(feasible.sum())}")

    # Four objectives, all minimised. Kickback and drift are on the axes and
    # not merely inside the feasible set: if they are only constraints, every
    # non-dominated point sits hard against the budget line and nothing is
    # left over for the corners, the layout and the model's own error.
    costs = np.column_stack([
        power[feasible], kick[feasible], delay_spread[feasible]
    ])
    front = pareto_mask(costs)
    print(f"pareto_points = {int(front.sum())}")

    # ------------------------------------------------------------- selection
    # Stated rule: among non-dominated feasible designs, take the fastest
    # (smallest delay proxy) that holds BOTH uncalibratable terms at or below
    # half their budget. Half, not all of it, because the model is pre-layout,
    # typical-corner and analytic, and the terms it omits only ever add.
    idx_f = np.flatnonzero(feasible)
    idx_front = idx_f[front]
    margin = (kick[idx_front] <= 0.5 * KICK_BUDGET) & \
             (drift[idx_front] <= 0.5 * DRIFT_BUDGET)
    # Preference order, stated so it can be argued with: a pure resize
    # (n-well on vdd, only geometry changed) at half budget beats a
    # well-tied one, because it is the smaller change to a recorded design.
    pure = margin & ~well_tail[idx_front]
    if np.any(pure):
        pool = idx_front[pure]
    elif np.any(margin):
        pool = idx_front[margin]
        print("REPORT: no pure resize (n-well on vdd) holds both "
              "uncalibratable terms at half budget; the selected design "
              "ties the input pair's n-well to the tail, which is one "
              "connectivity change beyond sizing")
    else:
        pool = idx_front
        print("REPORT: no frontier point holds both terms at half budget; "
              "selecting from the full frontier instead")
    best = pool[np.argmin(delay_spread[pool])]
    if fallback:
        best = bi
    # Report the best each well option can do, so the choice between them is
    # visible as numbers rather than asserted. "Best" here is the same rule:
    # fastest frontier point holding both uncalibratable terms at half budget.
    for tag, want in (("pure_resize", False), ("well_tied", True)):
        cand = idx_front[margin & (well_tail[idx_front] == want)]
        if cand.size:
            b = cand[np.argmin(delay_spread[cand])]
            print(f"best_{tag}_kick_v = {kick[b]:.6g}")
            print(f"best_{tag}_drift_v = {drift[b]:.6g}")
            print(f"best_{tag}_delay_spread_s = {delay_spread[b]:.6g}")
            print(f"best_{tag}_power_w = {power[b]:.6g}")
            print(f"best_{tag}_id_branch_a = {id_branch[b]:.6g}")
        else:
            print(f"REPORT: no {tag} design on the frontier holds both "
                  "uncalibratable terms at half budget")
    print(f"feasible_pure_resize = {int((feasible & ~well_tail).sum())}")
    print(f"feasible_well_tied = {int((feasible & well_tail).sum())}")

    def record(best):
        return dict(
            gmid_in=float(gmid_in[best]), l_in=float(l_in[best]),
            gmid_load=float(gmid_load[best]), l_load=float(l_load[best]),
            gmid_tail=float(gmid_tail[best]), l_tail=float(l_tail[best]),
            well_tail=bool(well_tail[best]),
            id_branch=float(id_branch[best]), inv_ratio=float(inv_ratio[best]),
            w_in=float(w_in[best]), w_load=float(w_load[best]), w_tail=float(w_tail[best]),
            v_left=float(v_left[best]), v_outa=float(v_outa[best]),
            v_tail_hi=float(op_hi["v_tail"][best]), headroom=float(headroom[best]),
            vdsat_tail=float(vdsat_tail[best]), gain_ota=float(gain_ota[best]),
            kick=float(kick[best]), drift=float(drift[best]),
            offset_static=float(offset_static[best]),
            delay_spread=float(delay_spread[best]), tau_mid=float(tau_mid[best]),
            slew=float(slew[best]), power=float(power[best]),
            vn_in=float(vn_in[best]), iref=float(iref[best]),
            wl_in=float(w_in[best] * 1e6 * l_in[best]),
            wl_load=float(w_load[best] * 1e6 * l_load[best]),
            tail_sag=float(tail_sag[best]), vsg_ref=float(vsg_ref[best]),
            c_outa=float(c_outa[best]),
        )
    

    sel = record(best)
    def finish(sel):
        win, nfin = snap_width(sel["w_in"])
        wld, nfld = snap_width(sel["w_load"])
        wtl, nftl = snap_width(sel["w_tail"])
        sel.update(
            w_in_um=win, nf_in=nfin, w_load_um=wld, nf_load=nfld,
            w_tail_um=wtl, nf_tail=nftl,
            tail_ratio=(2.0 * sel["id_branch"]) / sel["iref"],
            lsb_v=LSB, kick_budget_v=KICK_BUDGET, drift_budget_v=DRIFT_BUDGET,
            kick_calibration=kcal, drift_calibration=dcal,
            seed=seed, points=points,
        )
        return sel

    finish(sel)
    win, nfin = sel["w_in_um"], sel["nf_in"]
    wld, nfld = sel["w_load_um"], sel["nf_load"]
    wtl, nftl = sel["w_tail_um"], sel["nf_tail"]
    # The tail mirrors a 50 uA reference leg of L=1u W=20u nf=10, so the drawn
    # tail width sets the ratio rather than the absolute current.

    for k in ("gmid_in", "l_in", "gmid_load", "l_load", "gmid_tail", "l_tail",
              "inv_ratio", "gain_ota", "v_left", "v_outa", "v_tail_hi",
              "headroom", "vdsat_tail", "offset_static", "c_outa"):
        print(f"sel_{k} = {sel[k]:.6g}")
    print(f"sel_id_branch_a = {sel['id_branch']:.6g}")
    print(f"sel_w_in_um = {win}")
    print(f"sel_nf_in = {nfin}")
    print(f"sel_w_load_um = {wld}")
    print(f"sel_nf_load = {nfld}")
    print(f"sel_w_tail_um = {wtl}")
    print(f"sel_nf_tail = {nftl}")
    print(f"sel_kick_pred_v = {sel['kick']:.6g}")
    print(f"sel_drift_pred_v = {sel['drift']:.6g}")
    print(f"sel_delay_spread_pred_s = {sel['delay_spread']:.6g}")
    print(f"sel_tau_out_s = {sel['tau_mid']:.6g}")
    print(f"sel_slew_s = {sel['slew']:.6g}")
    print(f"sel_power_w = {sel['power']:.6g}")
    print(f"sel_vn_in_pred_v = {sel['vn_in']:.6g}")
    print(f"sel_vn_in_pred_lsb = {sel['vn_in']/LSB:.4g}")
    print(f"sel_kick_pred_lsb = {sel['kick']/LSB:.4g}")
    print(f"sel_drift_pred_lsb = {sel['drift']/LSB:.4g}")
    print(f"w_in_shrink_vs_ref = {REF['w_in']*1e6/win:.4g}")
    print(f"sel_well_tie = {'tail' if sel['well_tail'] else 'vdd'}")
    print(f"sel_iref_a = {sel['iref']:.6g}")
    print(f"sel_vsg_ref_v = {sel['vsg_ref']:.4g}")
    print(f"sel_tail_sag_pred = {sel['tail_sag']:.4g}")
    print(f"sel_tail_ratio = {sel['tail_ratio']:.4g}")
    print(f"sel_wl_in_um2 = {sel['wl_in']:.4g}")
    print(f"sel_wl_load_um2 = {sel['wl_load']:.4g}")
    sig_in = AVT_ASSUMED / np.sqrt(sel["wl_in"])
    sig_ld = AVT_ASSUMED / np.sqrt(sel["wl_load"])
    sig_os = np.sqrt(2.0) * np.sqrt(
        sig_in ** 2 + (sig_ld * sel["gmid_load"] / sel["gmid_in"]) ** 2)
    print(f"sel_sigma_vos_assumed_v = {sig_os:.6g}")
    print(f"sel_sigma_vos_assumed_lsb = {sig_os/LSB:.4g}")
    print("REPORT: sigma(Vos) above assumes AVT = "
          f"{AVT_ASSUMED*1e3:.0f} mV.um for both device types. That is an "
          "assumption for scale, not a PDK number; Monte Carlo mismatch "
          "remains an OPEN row.")

    # ------------------------------------------------------------- artefacts
    os.makedirs("data", exist_ok=True)
    os.makedirs("work", exist_ok=True)
    nowrite = os.environ.get("SIZING_NOWRITE") == "1"
    keep = feasible.copy()
    keep[::10] = True          # deterministic 1-in-10 of the infeasible cloud
    keep[idx_front] = True
    for path, rows in ([] if nowrite else
                       (("data/p5t_pareto.csv", np.flatnonzero(keep)),
                        ("work/p5t_pareto_full.csv", np.arange(points)))):
     with open(path, "w") as f:
        f.write(
            "gmid_in,l_in_um,gmid_load,l_load_um,gmid_tail,l_tail_um,"
            "id_branch_a,w_in_um,w_load_um,w_tail_um,gain_ota,vsg_in_v,"
            "vdsat_tail_v,headroom_v,vleft_dc_v,kick_mv,delay_proxy_s,tau_out_s,"
            "power_w,vn_in_v,iref_a,tail_sag,well_tail,feasible,on_front,chosen\n"
        )
        on_front = np.zeros(points, dtype=int)
        on_front[idx_front] = 1
        for i in rows:
            f.write(
                f"{gmid_in[i]:.4f},{l_in[i]},{gmid_load[i]:.4f},{l_load[i]},"
                f"{gmid_tail[i]:.4f},{l_tail[i]},{id_branch[i]:.6g},"
                f"{w_in[i]*1e6:.6g},{w_load[i]*1e6:.6g},{w_tail[i]*1e6:.6g},"
                f"{gain_ota[i]:.5g},{op_mid['vsg_in'][i]:.4g},"
                f"{vdsat_tail[i]:.4g},{headroom[i]:.4g},{v_left[i]:.4g},"
                f"{kick[i]*1e3:.6g},{delay_spread[i]:.6g},{tau_mid[i]:.6g},{power[i]:.6g},"
                f"{vn_in[i]:.6g},{iref[i]:.6g},{tail_sag[i]:.4g},{int(well_tail[i])},"
                f"{int(feasible[i])},{on_front[i]},{int(i == best)}\n"
            )
     print(f"INFO: wrote {path}")

    designs = [("cmp_p5t_8b", sel, "data/p5t_sizing.json")]

    # The best design that changes GEOMETRY ONLY, kept whether or not it holds
    # the half-budget margin. The question "what does resizing alone buy?" is
    # the one that was actually asked, and it deserves a measured answer rather
    # than an analytic claim that it is not enough.
    other = ~well_tail[bi]
    alt_pool = np.flatnonzero(buildable & (well_tail == other))
    alt_front = (alt_pool[np.argmin(viol[alt_pool])][None]
                 if fallback and alt_pool.size
                 else idx_front[well_tail[idx_front] == other])
    if alt_front.size:
        bp = alt_front[np.argmin(delay_spread[alt_front])]
        sel_pure = finish(record(bp))
        designs.append(("cmp_p5t_8b_alt", sel_pure, "data/p5t_sizing_alt.json"))
        print(f"alt_delay_spread_pred_s = {sel_pure['delay_spread']:.6g}")
        print(f"alt_tau_out_s = {sel_pure['tau_mid']:.6g}")
        print(f"alt_kick_pred_v = {sel_pure['kick']:.6g}")
        print(f"alt_drift_pred_v = {sel_pure['drift']:.6g}")
        print(f"alt_id_branch_a = {sel_pure['id_branch']:.6g}")
        print(f"alt_iref_a = {sel_pure['iref']:.6g}")
        print(f"alt_w_in_um = {sel_pure['w_in_um']}")
        print(f"alt_headroom_v = {sel_pure['headroom']:.4g}")
        print(f"alt_well_tie = {'tail' if sel_pure['well_tail'] else 'vdd'}")
        print(f"alt_kick_ratio = {sel_pure['kick']/KICK_BUDGET:.4g}")
        print(f"alt_drift_ratio = {sel_pure['drift']/DRIFT_BUDGET:.4g}")
        print(f"alt_spread_ratio = {sel_pure['delay_spread']/SPREAD_BUDGET:.4g}")

    for name, d, jpath in ([] if nowrite else designs):
        netlist = emit_netlist(d)
        with open(f"work/{name}.spice", "w") as f:
            f.write(netlist)
        with open(jpath, "w") as f:
            json.dump(d, f, indent=2, sort_keys=True)
        if os.environ.get("SIZING_EMIT") == "1":
            with open(f"{name}.spice", "w") as f:
                f.write(netlist)
            print(f"INFO: emitted {name}.spice")

    print("PASS: gm/Id Pareto extracted and a sizing selected")
    return 0


def calibrate(pfet, nfet, vthn, vthp):
    """Evaluate the recorded sizing through the same models, for calibration."""
    one = np.ones(1)
    id_b = one * (REF["iref"] / 2.0)
    l_in = one * REF["l_in"]
    l_load = one * REF["l_load"]
    l_tail = one * REF["l_tail"]

    # Invert W = ID/ID_W for the gm/Id each recorded device actually runs at.
    def gmid_from_idw(table, target_idw, L, vds, vsb, lo, hi):
        g = np.linspace(lo, hi, 400)
        idw = np.asarray(
            table.look_up("ID_W", GM_ID=g, L=float(L), VDS=float(vds), VSB=float(vsb))
        ).ravel()
        order = np.argsort(idw)
        return float(np.interp(target_idw, idw[order], g[order]))

    v_left = 0.75
    vsg_in = 1.0
    for _ in range(4):
        gmid_load = gmid_from_idw(nfet, REF["iref"] / 2.0 / REF["w_load"],
                                  REF["l_load"], v_left, 0.0, 4.0, 26.0)
        v_left = float(np.asarray(nfet.look_upVGS(
            GM_ID=np.array([gmid_load]), L=REF["l_load"], VDS=v_left, VSB=0.0
        )).ravel()[0])
        v_tail_mid = 1.25 + vsg_in
        vsb = float(np.clip(VDD - v_tail_mid, 0.0, 0.4))
        vds_in = float(np.clip(v_tail_mid - v_left, 0.05, 3.3))
        gmid_in = gmid_from_idw(pfet, REF["iref"] / 2.0 / REF["w_in"],
                                REF["l_in"], vds_in, vsb, 4.0, 26.0)
        vsg_in = float(np.asarray(pfet.look_upVGS(
            GM_ID=np.array([gmid_in]), L=REF["l_in"], VDS=vds_in, VSB=vsb
        )).ravel()[0])

    v_tail_hi = VCM_HI + vsg_in
    headroom_hi = VDD - v_tail_hi
    gmid_tail = gmid_from_idw(pfet, REF["iref"] / REF["w_tail"], REF["l_tail"],
                              max(headroom_hi, 0.05), 0.0, 4.0, 22.0)
    vdsat_tail = 2.0 / gmid_tail

    # BUF1/BUF2 of the recorded netlist: Wn=4u, Wp=8u at L=0.28u.
    ratio = float(np.sqrt((8.0 / 4.0) * 0.25))   # beta_p/beta_n with mu_p/mu_n ~ 1/4
    v_outa = inverter_trip(vthn, vthp, ratio)
    dv = v_outa - v_left

    def at(vcm):
        vt = vcm + vsg_in
        return (float(np.clip(vt - v_left, 0.05, 3.3)),
                float(np.clip(VDD - vt, 0.0, 0.4)))

    vds_hi, vsb_hi = at(VCM_HI)
    vds_lo, vsb_lo = at(VCM_LO)
    gg = lambda vds, vsb: float(np.asarray(pfet.look_up(
        "GM_GDS", GM_ID=np.array([gmid_in]), L=REF["l_in"], VDS=vds, VSB=vsb
    )).ravel()[0])
    drift = abs(gmid_in / gg(vds_hi, vsb_hi) - gmid_in / gg(vds_lo, vsb_lo)) \
        * abs(dv) / gmid_in

    vds_mid, vsb_mid = at(1.25)
    cgd_w = float(np.asarray(pfet.look_up(
        "CGD_W", GM_ID=np.array([gmid_in]), L=REF["l_in"], VDS=vds_mid, VSB=vsb_mid
    )).ravel()[0])
    cgs_w = float(np.asarray(pfet.look_up(
        "CGS_W", GM_ID=np.array([gmid_in]), L=REF["l_in"], VDS=vds_mid, VSB=vsb_mid
    )).ravel()[0])
    kick_raw = REF["w_in"] * (cgd_w / gmid_load + ETA_TAIL * cgs_w / gmid_in) / CHOLD

    return dict(gmid_in=gmid_in, gmid_load=gmid_load, gmid_tail=gmid_tail,
                v_left=v_left, vsg_in=vsg_in, v_tail_hi=v_tail_hi,
                headroom_hi=headroom_hi, vdsat_tail=vdsat_tail,
                v_outa=v_outa, drift=drift, kick_raw=kick_raw)


def emit_netlist(s):
    """Write the resized subcircuit. Same devices, same nodes, same ports."""
    # Buffer first inverter, skewed to put its threshold nearer V_left so the
    # (V_outa - V_left) that drives the offset model is smaller. ratio is
    # sqrt(beta_p/beta_n); with mu_p/mu_n ~ 1/4, Wp/Wn = 4 * ratio^2.
    wn1 = 4.0
    wp1 = max(0.44, round(4.0 * s["inv_ratio"] ** 2 * wn1, 2))
    wn2, wp2 = 8.0, 16.0
    bulk = 'tail' if s['well_tail'] else 'vdd'
    welltext = (
        'input pair n-well tied to the tail: VSB = 0, no body effect, which\n*   buys back about 160 mV of |VSG| and therefore of tail headroom at the\n*   2.0 V top of the range. Costs one separate n-well and its capacitance\n*   on the tail node.'
        if s['well_tail'] else
        'input pair n-well on vdd, as recorded: a pure resize, no\n*   connectivity change.')
    return f"""* Resized P5T -- PMOS-input 5T comparator sized for 8 bits over 0.5-2.0 V.
*
* GENERATED by size_p5t.py (seed {s['seed']}, {s['points']} samples). Do not
* hand-edit: run.sh regenerates it into work/ and fails if this file differs.
* To change the sizing, change the sizing script.
*
* Same topology, same internal node names and same port list as
* cmp_p5t_ref.spice, so one bench measures both. Only geometry and the tail
* mirror ratio changed.
*
* gm/Id operating point chosen from the Pareto front:
*   input pair  gm/Id {s['gmid_in']:.2f} S/A, L {s['l_in']} um -> W {s['w_in_um']} um, nf {s['nf_in']}
*   mirror load gm/Id {s['gmid_load']:.2f} S/A, L {s['l_load']} um -> W {s['w_load_um']} um, nf {s['nf_load']}
*   tail        gm/Id {s['gmid_tail']:.2f} S/A, L {s['l_tail']} um -> W {s['w_tail_um']} um, nf {s['nf_tail']}
*   branch current {s['id_branch']*1e6:.2f} uA, OTA gain {s['gain_ota']:.1f} V/V
*   BIAS: this sizing REQUIRES IREF = {s['iref']*1e6:.2f} uA into the testbench's
*   L=1u W=20u reference leg. The tail inherits that leg's VSG, so IREF is
*   what sets Vdsat_tail = {s['vdsat_tail']*1e3:.0f} mV and hence the headroom at 2.0 V.
*   Running this netlist at the recorded 50 uA puts the tail back in triode.
*   V_left {s['v_left']:.3f} V, V_outa {s['v_outa']:.3f} V, tail headroom at
*   VCM=2.0 V is {s['headroom']*1e3:.0f} mV against Vdsat {s['vdsat_tail']*1e3:.0f} mV
*   {welltext}
* Predicted: kickback {s['kick']*1e3:.3f} mV into 1 pF, drift {s['drift']*1e3:.3f} mV.
* Budget is 1.465 mV on each. ngspice is the authority, not these predictions.
.subckt cmp inp inn dout clk vdd vss nbias pbias
XINP left inp tail {bulk} pfet_03v3 L={s['l_in']}u W={{{s['w_in_um']}u*(1+WMIS)}} nf={s['nf_in']} m=1
XINN outa inn tail {bulk} pfet_03v3 L={s['l_in']}u W={s['w_in_um']}u nf={s['nf_in']} m=1
XLOADD left left vss vss nfet_03v3 L={s['l_load']}u W={s['w_load_um']}u nf={s['nf_load']} m=1
XLOADM outa left vss vss nfet_03v3 L={s['l_load']}u W={s['w_load_um']}u nf={s['nf_load']} m=1
XTAIL tail pbias vdd vdd pfet_03v3 L={s['l_tail']}u W={s['w_tail_um']}u nf={s['nf_tail']} m=1
COUTA outa vss 20f
XBUF1 outb outa vss vss nfet_03v3 L=0.28u W={wn1}u nf=4 m=1
XBUF2 outb outa vdd vdd pfet_03v3 L=0.28u W={wp1}u nf=1 m=1
XBUF3 dout outb vss vss nfet_03v3 L=0.28u W={wn2}u nf=4 m=1
XBUF4 dout outb vdd vdd pfet_03v3 L=0.28u W={wp2}u nf=4 m=1
.ends cmp
"""


if __name__ == "__main__":
    sys.exit(main())
