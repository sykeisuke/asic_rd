"""Chip floorplan v2: Analog_top as one hard macro and the digital top, inside
the wafer.space 1x0p5 pad ring, digital on top. ../chip_floorplan_bkp/chip_floorplan (v4) is unchanged.

From v4: the v5 netlist (one VDD/2 buffer midref, VREF = VBL, bias_gen_s);
no vbl bus; pin names as the v5 netlist and the talk (VIN, CMP_OUT); every pin
carries a status, `core` (in the v5 netlist) or `planned` (spec s.7.3 test
access, no circuit yet; its area is reserved from proxy blocks).

    ./container.sh 'python3 floorplan.py'      (run.sh phase `plan`)

Nothing here is a layout. It is a to-scale area and placement plan:

- every analog block's area is computed from the devices in
  ../Analog_top/analog_top.spice with the project's MOS footprint rule
  and one layout factor measured on the only drawn, DRC-clean unit cell
  (../unit_cell_floorplan, UC_MIM);
- MIM capacitors (cap_mim_2f0_m4m5, Metal4/Metal5) are placed over the
  circuits: a block is as large as its devices or its MIMs, not the sum;
- the digital top is the bounding box of its GDS, measured by gds_probe.py;
- the pad ring is the template's slot_1x0p5.yaml with bidir[45:44]
  re-typed as the AVDD pair, as in the user's ring drawing.

Value tags: [P] PDK or project record, [M] measured in a recorded run,
[A] assumed here (each one is a floorplan choice, listed in the README).

Writes assets/chip_floorplan.svg, assets/analog_macro_floorplan.svg,
data/floorplan.json, and prints `name = value`, PASS/FAIL and REPORT lines.
"""
import json
import math
import os
import re
import shlex

HERE = os.path.dirname(os.path.abspath(__file__))
MS = os.path.dirname(HERE)
NETLIST = os.path.join(MS, "Analog_top", "analog_top.spice")
UC_CMP = os.path.join(HERE, "ref", "cmp_uc_mim55.spice")
PROBE = os.path.join(HERE, "data", "gds_probe.json")

# ---------------------------------------------------------------- slot [P]
# wafer-space/gf180mcu-project-template @ 0de7e394, librelane/slots/slot_1x0p5.yaml
DIE = (3932.0, 2531.0)
CORE = (442.0, 442.0, 3490.0, 2089.0)
# pad order as listed in the slot file; every side is listed in increasing
# coordinate (south/north west->east, east/west south->north), which is what
# the user's ring drawing shows (AVDD at the north-west, VDD/VSS[0] at the
# bottom of the west side)
SOUTH = ["clk", "rst_n", "bidir[0]", "bidir[1]", "dvss[0]", "dvdd[0]"] + \
        [f"bidir[{i}]" for i in range(2, 14)] + ["dvss[1]", "dvdd[1]"] + \
        [f"bidir[{i}]" for i in range(14, 18)]
EAST = ["dvss[2]", "dvdd[2]"] + [f"bidir[{i}]" for i in range(18, 26)] + ["dvss[3]", "dvdd[3]"]
NORTH = ["bidir[45]", "bidir[44]", "bidir[43]", "bidir[42]", "dvss[5]", "dvdd[5]"] + \
        [f"bidir[{i}]" for i in range(41, 29, -1)] + ["dvss[4]", "dvdd[4]"] + \
        [f"bidir[{i}]" for i in range(29, 25, -1)]
WEST = ["vss[0]", "vdd[0]", "inputs[3]", "inputs[2]", "inputs[1]", "inputs[0]",
        "analog[3]", "analog[2]", "analog[1]", "analog[0]", "dvss[6]", "dvdd[6]"]

# the user's ring: bidir[45:44] re-typed as the AVDD core supply pair (the
# 1x0p5 counterpart of the frozen 0p5x1 ring's bidir[43:42], WS-06); analog
# pads as drawn: analog[0..2] bi_a, analog[3] asig_5p0
RETYPE = {"bidir[45]": ("avdd", "AVDD"), "bidir[44]": ("avss", "AVSS")}
ANALOG_CELL = {"analog[0]": "bi_a", "analog[1]": "bi_a", "analog[2]": "bi_a", "analog[3]": "asig_5p0"}

# Analog_top pins on the four analog pads plus the AVDD pair, same pads as v4
# (VFE -> VIN, the v5 port name; COMP_TEST_OUT -> CMP_OUT, the talk's name).
# Order chosen so no pad wire crosses another and the two precision inputs get
# the shortest wires (README s.3).
ASSIGN = {
    "analog[3]": ("VIN", "sampling input -> 4 x S0 (vin bus)"),
    "analog[2]": ("EXT_RAMP", "external ramp in, replaces vramp (selected by RAMP_SEL)"),
    "analog[1]": ("AMON", "analog monitor out: buffer + 4:1 mux (vramp / vref / vrlo / replica plate), AMON_SEL[1:0]"),
    "analog[0]": ("CMP_OUT", "replica comparator + latch in standalone mode (CMP_SA_EN); not a signal cell"),
    "bidir[45]": ("AVDD", "analog 3.3 V, macro ring only"),
    "bidir[44]": ("AVSS", "analog ground (common on the COB)"),
}
# core: a port of the v5 netlist; planned: spec s.7.3 test access, no circuit yet
PIN_STATUS = {"VIN": "core", "EXT_RAMP": "planned", "AMON": "planned", "CMP_OUT": "planned",
              "AVDD": "core", "AVSS": "core", "RAMP_SEL": "planned", "AMON_SEL[0]": "planned",
              "AMON_SEL[1]": "planned", "CMP_SA_EN": "planned"}

# ------------------------------------------------------------ area model
FP_GAP, FP_END = 0.52, 0.44   # [P] comparator/size_v3.py: gate-gate strip, end strip
UC_PR_UM2 = 626.8             # [M] unit_cell_floorplan RESULTS.md: UC_MIM PR boundary, DRC 0
UC_SW = (0.52, 1.04, 0.28)    # [M] same record: UC_MIM switch WN / WP / L
UC_MIM_FP = 77.9              # [M] same record: 5 x 5 um MIM incl. keep-out, M4/M5
MIM_SIDE_UC = 5.0
MIM_KEEP = (math.sqrt(UC_MIM_FP) - MIM_SIDE_UC) / 2   # keep-out per side, from the record
R_PITCH = 1.4                 # [P] midrail_ref_v2/size_v2.py: HRES.2 width 1 + HRES.3 space 0.4
R_HEAD = 1.0                  # [A] contact head per strip end
K_RES = 1.5                   # [A] dummy strips + guard ring around a resistor array
BG_ROW = (205.12, 14.0)       # [M] bias_gen/data/floorplan.json footprint (2 rows + strips)
BG_PITCH = 1.42               # [M] same record, finger pitch

# ------------------------------------------------------- floorplan choices [A]
RING = 8.0        # macro AVDD/AVSS ring: 2 x 3 um metal + 2 x 1 um space
SP = 4.0          # block-to-block space (each block already carries its guard ring)
CELL_GAP = 4.0    # between cells: s0/s1/s2 control lines + guard
SPLIT = 2.0       # AVDD analog part to DVDD latch row in one cell
BUS_CH = None     # computed below from its tracks
TRACK = 0.56      # Metal2/Metal3 signal pitch [P] (0.28 width + 0.28 space)
AWIRE = 2.4       # analog bus: 1.2 um wire + 1.2 um space
CDM_STRIP = 50.0  # core-edge strip: CDM cells + one 5 um column per analog pad wire
WIRE_COL = 5.0    # pad-wire column pitch: 1.2 um wire + space + shield
CDM_BOX = (24.0, 30.0)  # per analog pad: 2 diodes (perimeter > 25 um) + poly R > 50 ohm
GAP_AD = 30.0     # analog macro to digital: halo + p+ tap ring + 22-signal channel
STRAP = 10.0      # AVDD / AVSS strap width from the north pads

SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6}


def num(s, env=None):
    s = s.strip().strip("'").strip("{}")
    m = re.fullmatch(r"([-+0-9.eE]+)(meg|[fpnumk])?", s)
    if m:
        return float(m.group(1)) * SI.get(m.group(2), 1.0)
    expr = re.sub(r"([0-9.]+)u", r"(\1e-6)", s)
    return float(eval(expr, {"__builtins__": {}}, env or {}))


def read_spice(path):
    lines = []
    for raw in open(path):
        raw = raw.rstrip("\n")
        if raw.startswith("+") and lines:
            lines[-1] += " " + raw[1:]
        else:
            lines.append(raw)
    subs, cur = {}, None
    for ln in lines:
        t = ln.strip()
        if not t or t.startswith("*"):
            continue
        low = t.lower()
        if low.startswith(".subckt"):
            cur = t.split()[1]
            subs[cur] = []
        elif low.startswith(".ends"):
            cur = None
        elif cur and t[0] in "xX":
            tok = shlex.split(t)
            params = {}
            pos = []
            for k in tok[1:]:
                if "=" in k:
                    a, b = k.split("=", 1)
                    params[a.lower()] = b
                else:
                    pos.append(k)
            subs[cur].append({"name": tok[0], "model": pos[-1], "nodes": pos[:-1], "p": params})
    return subs


def mos_fp(d, env=None):
    p = d["p"]
    w, L = num(p["w"], env) * 1e6, num(p["l"], env) * 1e6
    nf = int(num(p.get("nf", "1"), env))
    m = int(num(p.get("m", "1"), env))
    wf = w / nf
    return wf * (nf * L + (nf - 1) * FP_GAP + 2 * FP_END) * m


def mim_fp(d):
    w, l = num(d["p"]["c_width"]) * 1e6, num(d["p"]["c_length"]) * 1e6
    return (w + 2 * MIM_KEEP) * (l + 2 * MIM_KEEP), w, l


def res_fp(d):
    w, l = num(d["p"]["r_width"]) * 1e6, num(d["p"]["r_length"]) * 1e6
    return (R_PITCH + w - 1.0) * (l + 2 * R_HEAD)


def flatten(subs, cell, mult=1, out=None):
    """Leaf devices of `cell` with their multiplicity."""
    out = out if out is not None else []
    for d in subs.get(cell, []):
        if d["model"] in subs:
            flatten(subs, d["model"], mult, out)
        else:
            out.append((d, mult))
    return out


def tally(devs, sc):
    t = {"mos_fp": 0.0, "res_fp": 0.0, "mims": [], "sc": [], "n_mos": 0, "n_res": 0}
    for d, k in devs:
        mdl = d["model"]
        if mdl.endswith("fet_03v3"):
            t["mos_fp"] += k * mos_fp(d)
            t["n_mos"] += k
        elif mdl.startswith("ppolyf"):
            t["res_fp"] += k * res_fp(d)
            t["n_res"] += k
        elif mdl.startswith("cap_mim"):
            for _ in range(k):
                t["mims"].append(mim_fp(d))
        elif mdl.startswith("gf180mcu_as_sc"):
            name = mdl.split("__")[1]
            t["sc"] += [name] * k
        else:
            raise SystemExit(f"FAIL: unknown device model {mdl}")
    return t


def calibrate():
    """K = drawn UC_MIM PR boundary / project footprint of its devices."""
    subs = read_spice(UC_CMP)
    cell = next(iter(subs))
    fp = sum(mos_fp(d, {"WMIS": 0.0}) for d in subs[cell])
    wn, wp, L = UC_SW
    fp += (wn + wp) * (L + 2 * FP_END)
    return UC_PR_UM2 / fp, fp


class Box:
    def __init__(self, key, label, x, y, w, h, kind, note=""):
        self.key, self.label, self.x, self.y, self.w, self.h, self.kind, self.note = key, label, x, y, w, h, kind, note

    def r(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def d(self):
        return {"key": self.key, "label": self.label, "x": round(self.x, 2), "y": round(self.y, 2),
                "w": round(self.w, 2), "h": round(self.h, 2), "kind": self.kind, "note": self.note}


def overlap(a, b):
    ax0, ay0, ax1, ay1 = a.r()
    bx0, by0, bx1, by1 = b.r()
    return ax0 < bx1 - 1e-6 and bx0 < ax1 - 1e-6 and ay0 < by1 - 1e-6 and by0 < ay1 - 1e-6


def main():
    probe = json.load(open(PROBE))
    dig_w, dig_h = probe["digital"]["w_um"], probe["digital"]["h_um"]
    pad_w, pad_h = probe["pads"]["bi_24t"]["w_um"], probe["pads"]["bi_24t"]["h_um"]
    cor = probe["pads"]["cor"]["w_um"]
    ff_w, ff_h = probe["stdcell"]["dfxtn_2"]["w_um"], probe["stdcell"]["dfxtn_2"]["h_um"]

    K, uc_fp = calibrate()
    print(f"k_layout = {K:.3f}")
    print(f"uc_mim_device_fp_um2 = {uc_fp:.1f}")
    print(f"mim_keepout_um = {MIM_KEEP:.3f}")

    subs = read_spice(NETLIST)
    top = subs["analog_top"]
    groups = {}
    for d in top:
        groups.setdefault(d["model"], []).append(d)

    def block(model, count=1):
        t = tally(flatten(subs, model), None)
        dev = K * t["mos_fp"] + K_RES * t["res_fp"]
        mim = sum(m[0] for m in t["mims"])
        return t, dev, mim

    blk = {}
    for model in ["bias_gen_s", "midref_div", "midref_buf", "vrlo_ref", "ramp_simple_d", "atop_cell"]:
        t, dev, mim = block(model)
        blk[model] = {"t": t, "dev": dev, "mim": mim, "n": len(groups.get(model, []))}
        print(f"{model}_dev_um2 = {dev:.1f}")
        print(f"{model}_mim_um2 = {mim:.1f}")

    # ---- unit cell: analog part (MIM over the comparator tail) + its latch
    c = blk["atop_cell"]
    cell_w = max(ff_w, math.sqrt(c["mim"]))
    cell_ha = max(c["dev"] / cell_w, math.sqrt(c["mim"]))
    cell_h = cell_ha + SPLIT + ff_h
    print(f"cell_w_um = {cell_w:.2f}")
    print(f"cell_h_um = {cell_h:.2f}")

    # ---- bias_gen_s: the recorded two-row floorplan, unchanged in length.
    # bias_gen's rows hold 136 fingers each; the NMOS row (132 active + 4
    # dummies) sets the length. v2s drops XOB (44 PMOS fingers) and adds XOL
    # (6), so the PMOS row has room and the row stays 205.1 um [M].
    b = blk["bias_gen_s"]
    bg_w = BG_ROW[0] + 2 * SP
    bg_h = max(b["dev"] / bg_w, max(math.sqrt(m[0]) for m in b["t"]["mims"]))
    print(f"bias_gen_rowplan_um2 = {BG_ROW[0] * BG_ROW[1]:.1f}")

    # ---- vrlo_ref: MIM limited (3.47 pF + 1.02 pF), caps side by side over the devices
    v = blk["vrlo_ref"]
    vm = sorted(v["t"]["mims"], reverse=True)
    vr_w = sum(math.sqrt(m[0]) for m in vm)
    vr_h = max(max(math.sqrt(m[0]) for m in vm), v["dev"] / vr_w)

    # ---- ramp_simple_d: 4 pF MIM over the current source and reset switch
    rp = blk["ramp_simple_d"]
    rp_s = max(math.sqrt(rp["mim"]), math.sqrt(rp["dev"]))

    # ---- midref: the divider + ONE buffer (its MIM over it); its output is
    # both VREF (S2) and VBL (comparator inp)
    mb, md = blk["midref_buf"], blk["midref_div"]
    n_buf = mb["n"]
    print(f"midref_buffers = {n_buf}")
    mr_area = n_buf * max(mb["dev"], mb["mim"]) + max(md["dev"], md["mim"])

    # ---- reserved test zone (not designed): areas from proxy blocks
    #   replica comparator + latch = one unit cell; AMON = one midref_buf
    #   follower + a 4:1 TG mux (vramp / vref / vrlo / replica plate);
    #   EXT_RAMP = TG pair (W 10/20 um) + RAMP_SEL inverter; CMP_OUT driver =
    #   4-stage taper to 40/80 um (pad load)
    def tg(wn, wp, nf):
        return (wn + wp) / nf * (nf * 0.28 + (nf - 1) * FP_GAP + 2 * FP_END)
    t_mux = 4 * tg(1.0, 2.0, 1) + tg(10.0, 20.0, 10) + tg(0.44, 0.88, 1)
    t_drv = sum(tg(wn, 2 * wn, max(1, int(wn / 4))) for wn in (1.25, 5.0, 20.0, 40.0))
    test_area = cell_w * cell_h + max(mb["dev"], mb["mim"]) + K * (t_mux + t_drv)
    print(f"test_zone_reserved_um2 = {test_area:.1f}")

    # ---- the bus channel above the cells: vin, vramp, vref (wide, each beside
    # an AVSS shield; v5 has no vbl), 5 comparator bias lines (4 cells + the
    # replica), one space to the blocks
    n_bias = 5
    n_abus = 3
    bus_ch = n_abus * AWIRE + n_abus * TRACK + n_bias * TRACK + SP
    print(f"bus_channel_um = {bus_ch:.2f}")

    # ======================================== macro, local coordinates (um)
    # inside the AVDD/AVSS ring, south to north:
    #   band C: replica + 4 cells (latch row at the bottom, on DVDD), decap
    #   bus channel: vin, vramp, vref, ibias
    #   band B: test zone (west, on the pad side) | vrlo_ref | ramp | midref | decap
    #   band A: bias_gen_s, its two common-centroid rows as recorded
    # The comparator bias lines drop from band A to the bus channel in the
    # SP gap between the test zone and vrlo_ref.
    boxes = []
    x0, y0 = RING, RING
    bandB_h = max(vr_h, rp_s)
    yB = y0 + cell_h + bus_ch
    yA = yB + bandB_h + SP
    test_w = test_area / bandB_h
    tx = x0
    boxes.append(Box("test", "TEST (reserved)", tx, yB, test_w, bandB_h, "reserved",
                     "CMP_OUT driver, AMON follower + 4:1 mux, EXT_RAMP TG mux"))
    bx = tx + test_w + SP
    boxes.append(Box("vrlo", "vrlo_ref", bx, yB, vr_w, vr_h, "ref", "3.47 + 1.02 pF MIM over"))
    rx = bx + vr_w + SP
    boxes.append(Box("ramp", "ramp_simple_d", rx, yB, rp_s, rp_s, "ramp", "4 pF MIM over"))
    mx = rx + rp_s + SP
    mr_w = max(math.sqrt(mr_area), n_buf * math.sqrt(mb["mim"]))
    mr_h = mr_area / mr_w
    boxes.append(Box("midref", "midref", mx, yB, mr_w, mr_h, "ref", "div + 1 buffer"))
    boxes.append(Box("bg", "bias_gen_s", x0, yA, bg_w, bg_h, "bias", "2 rows, 2 x 1 pF MIM over"))
    inner_w = max(bg_w, mx + mr_w - x0)
    bandA_h = bg_h
    if mx + mr_w + SP < x0 + inner_w - 1.0:
        boxes.append(Box("decapB", "AVDD decap", mx + mr_w + SP, yB, x0 + inner_w - mx - mr_w - SP, bandB_h,
                         "decap", "MOS caps on AVDD"))
    # band C: replica at the west end, under the test zone that drives its pad
    cx = x0
    names = ["replica"] + [f"cell {i}" for i in range(4)]
    for i, nm in enumerate(names):
        k = "rep" if i == 0 else f"c{i - 1}"
        boxes.append(Box(k, nm, cx, y0, cell_w, cell_h, "reserved" if i == 0 else "cell",
                         "S0/S1/S2 + 54.5 fF MIM over comparator_d; dfxtn_2 row"))
        cx += cell_w + CELL_GAP
    cells_end = cx - CELL_GAP
    boxes.append(Box("decapC", "AVDD decap", cells_end + SP, y0, x0 + inner_w - cells_end - SP, cell_h,
                     "decap", "MOS caps on AVDD + substrate taps"))
    boxes.append(Box("bus", "bus channel", x0, y0 + cell_h, inner_w, bus_ch - SP,
                     "channel", "vin vramp vref ibias[4:0], AVSS shields"))
    inner_h = yA + bandA_h - y0
    mac_w, mac_h = inner_w + 2 * RING, inner_h + 2 * RING
    for bxx in boxes:
        if bxx.x + bxx.w > x0 + inner_w + 1e-6 or bxx.y + bxx.h > y0 + inner_h + 1e-6:
            print(f"FAIL: macro block {bxx.key} outside the macro")
    decap = sum(bb.w * bb.h for bb in boxes if bb.kind == "decap")
    print(f"macro_decap_um2 = {decap:.1f}")

    # pins on the macro's west edge (local y), all on the test zone / bus side
    pins_w = {
        "VIN": y0 + cell_h + (bus_ch - SP) * 0.5,
        "EXT_RAMP": yB + bandB_h * 0.2,
        "AMON": yB + bandB_h * 0.5,
        "CMP_OUT": yB + bandB_h * 0.8,
    }
    dig_pins = [f"S0[{i}]" for i in range(4)] + [f"S1[{i}]" for i in range(4)] + [f"S2[{i}]" for i in range(4)] + \
               ["RAMP_RST", "CNT_CLK"] + [f"Q[{i}]" for i in range(4)] + ["RAMP_SEL", "AMON_SEL[0]", "AMON_SEL[1]", "CMP_SA_EN"]

    mac_area = mac_w * mac_h
    print(f"macro_w_um = {mac_w:.2f}")
    print(f"macro_h_um = {mac_h:.2f}")
    print(f"macro_area_um2 = {mac_area:.1f}")
    sum_blocks = sum(bb.w * bb.h for bb in boxes if bb.kind not in ("channel", "decap"))
    print(f"macro_block_area_um2 = {sum_blocks:.1f}")
    print(f"macro_block_fill_pct = {100 * sum_blocks / mac_area:.1f}")

    # ======================================== chip, die coordinates (um)
    def side_positions(n, length):
        pitch = (length - 2 * cor) / n
        return [cor + pitch * (i + 0.5) for i in range(n)], pitch

    pads = []
    for side, lst in (("S", SOUTH), ("N", NORTH)):
        xs, pitch = side_positions(len(lst), DIE[0])
        for name, xc in zip(lst, xs):
            y = 0.0 if side == "S" else DIE[1] - pad_h
            pads.append({"name": name, "side": side, "x": xc - pad_w / 2, "y": y, "w": pad_w, "h": pad_h, "c": xc})
    for side, lst in (("W", WEST), ("E", EAST)):
        ys, pitch = side_positions(len(lst), DIE[1])
        for name, yc in zip(lst, ys):
            x = 0.0 if side == "W" else DIE[0] - pad_h
            pads.append({"name": name, "side": side, "x": x, "y": yc - pad_w / 2, "w": pad_h, "h": pad_w, "c": yc})
    for p in pads:
        n = p["name"]
        if n in RETYPE:
            p["type"], p["label"] = RETYPE[n]
        elif n.startswith("analog"):
            p["type"], p["label"] = ANALOG_CELL[n], n
        elif n.startswith("bidir"):
            p["type"], p["label"] = "bidir", n
        elif n.startswith("inputs") or n in ("clk", "rst_n"):
            p["type"], p["label"] = "input", n
        elif n.startswith("dv"):
            p["type"], p["label"] = "iopwr", n
        else:
            p["type"], p["label"] = "corepwr", n
        if n in ASSIGN:
            p["signal"], p["fn"] = ASSIGN[n]
    counts = {}
    for p in pads:
        counts[p["type"]] = counts.get(p["type"], 0) + 1
    for k in sorted(counts):
        print(f"pads_{k} = {counts[k]}")
    print(f"pads_total = {len(pads)}")
    padc = {p["name"]: p for p in pads}

    # analog macro: west edge after the CDM strip; VIN pin level with the VIN pad
    mac_x = CORE[0] + CDM_STRIP
    mac_y = padc["analog[3]"]["c"] - (pins_w["VIN"])
    dig_x = mac_x
    dig_y = mac_y - GAP_AD - dig_h
    chip = [
        Box("macro", "Analog_top (hard macro)", mac_x, mac_y, mac_w, mac_h, "analog"),
        Box("digital", "asic_digital_top (soft, region = its hardened outline)", dig_x, dig_y, dig_w, dig_h, "digital"),
    ]
    cdm = []
    for an in ("analog[0]", "analog[1]", "analog[2]", "analog[3]"):
        yc = padc[an]["c"]
        cdm.append(Box(f"cdm_{an}", "CDM", CORE[0] + 4, yc - CDM_BOX[1] / 2, CDM_BOX[0], CDM_BOX[1], "cdm"))
    chip += cdm

    ok = True
    for bb in chip:
        x0c, y0c, x1c, y1c = bb.r()
        if not (x0c >= CORE[0] - 1e-6 and y0c >= CORE[1] - 1e-6 and x1c <= CORE[2] + 1e-6 and y1c <= CORE[3] + 1e-6):
            ok = False
            print(f"FAIL: {bb.key} outside the core area")
    for i in range(len(chip)):
        for j in range(i + 1, len(chip)):
            if overlap(chip[i], chip[j]):
                ok = False
                print(f"FAIL: {chip[i].key} overlaps {chip[j].key}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if overlap(boxes[i], boxes[j]):
                ok = False
                print(f"FAIL: macro blocks {boxes[i].key} and {boxes[j].key} overlap")
    if ok:
        print("PASS: macro, digital region and CDM cells inside the 1x0p5 core, no overlaps")

    # analog pad wires: pad inner edge -> CDM -> macro pin (Manhattan length)
    # each wire drops in a column of its own; the higher the pad, the further
    # east its column, which is what keeps order-preserving L-routes apart
    wires = {}
    for i, (an, pin) in enumerate((("analog[3]", "VIN"), ("analog[2]", "EXT_RAMP"), ("analog[1]", "AMON"),
                                   ("analog[0]", "CMP_OUT"))):
        p = padc[an]
        ys, ye = p["c"], mac_y + pins_w[pin]
        jx = CORE[0] + 4 + CDM_BOX[0] + WIRE_COL * (i + 1)
        if abs(ys - ye) < 1e-6:
            pts = [(p["x"] + p["w"], ys), (mac_x, ye)]
        else:
            pts = [(p["x"] + p["w"], ys), (jx, ys), (jx, ye), (mac_x, ye)]
        L = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))
        wires[pin] = {"pad": an, "pts": pts, "len_um": L}
        print(f"wire_{pin.lower()}_um = {L:.0f}")
        if jx >= mac_x - 1.0:
            print(f"FAIL: {pin} wire column at x = {jx:.1f} reaches the macro")
    # AVDD / AVSS straps from the north pads: down to just inside the core
    # edge, then east over the empty core, then down onto the macro's ring
    # AVDD (the western pad) turns east lower and lands west of AVSS, so the
    # two never cross; both land on the east part of the north ring, clear of
    # the pad-wire columns
    straps = {}
    for pn, lab, yk, xt in (("bidir[45]", "AVDD", CORE[3] - 35.0, mac_x + mac_w - 2 * STRAP - 25.0),
                            ("bidir[44]", "AVSS", CORE[3] - 15.0, mac_x + mac_w - STRAP - 6.0)):
        p = padc[pn]
        xs = p["c"]
        ytop = DIE[1] - pad_h
        pts = [(xs, ytop), (xs, yk), (xt, yk), (xt, mac_y + mac_h)]
        L = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))
        straps[lab] = {"pad": pn, "pts": pts, "len_um": L}
        print(f"strap_{lab.lower()}_um = {L:.0f}")

    def segs(pts):
        return [(a, b) for a, b in zip(pts, pts[1:])]

    def cross(s, u):
        (a, b), (c, d) = s, u
        if a[0] == b[0] and c[1] == d[1]:       # s vertical, u horizontal
            x, y = a[0], c[1]
            return min(c[0], d[0]) < x < max(c[0], d[0]) and min(a[1], b[1]) < y < max(a[1], b[1])
        if a[1] == b[1] and c[0] == d[0]:
            return cross(u, s)
        if a[0] == b[0] == c[0] == d[0]:        # collinear verticals sharing length
            return min(max(a[1], b[1]), max(c[1], d[1])) - max(min(a[1], b[1]), min(c[1], d[1])) > 1e-6
        if a[1] == b[1] == c[1] == d[1]:
            return min(max(a[0], b[0]), max(c[0], d[0])) - max(min(a[0], b[0]), min(c[0], d[0])) > 1e-6
        return False
    routes = {**{k: v["pts"] for k, v in wires.items()}, **{k: v["pts"] for k, v in straps.items()}}
    nx = 0
    keys = list(routes)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            for s in segs(routes[keys[i]]):
                for u in segs(routes[keys[j]]):
                    if cross(s, u):
                        nx += 1
                        print(f"REPORT: route {keys[i]} crosses or overlaps {keys[j]}")
    print(f"route_crossings = {nx}")
    if nx == 0:
        print("PASS: the four analog pad wires and the AVDD/AVSS straps neither cross nor overlap")
    else:
        print("FAIL: analog pad wires / supply straps cross")

    core_area = (CORE[2] - CORE[0]) * (CORE[3] - CORE[1])
    die_area = DIE[0] * DIE[1]
    cdm_area = sum(b.w * b.h for b in cdm)
    print(f"core_area_um2 = {core_area:.0f}")
    print(f"digital_region_w_um = {dig_w}")
    print(f"digital_region_h_um = {dig_h}")
    print(f"analog_area_um2 = {mac_area + cdm_area:.1f}")
    print(f"digital_area_um2 = {dig_w * dig_h:.1f}")
    print(f"analog_core_pct = {100 * (mac_area + cdm_area) / core_area:.3f}")
    print(f"digital_core_pct = {100 * dig_w * dig_h / core_area:.3f}")
    print(f"free_core_pct = {100 * (1 - (mac_area + cdm_area + dig_w * dig_h) / core_area):.2f}")
    print(f"REPORT: core {CORE[2]-CORE[0]:.0f} x {CORE[3]-CORE[1]:.0f} um; analog macro {mac_w:.1f} x {mac_h:.1f} um; "
          f"digital {dig_w} x {dig_h} um ({probe['digital']['gds']})")

    out = {
        "slot": "1x0p5", "die": DIE, "core": CORE, "pad_cell": [pad_w, pad_h], "corner": cor,
        "k_layout": K, "mim_keep_um": MIM_KEEP,
        "blocks": {k: {"dev_um2": round(v["dev"], 1), "mim_um2": round(v["mim"], 1),
                       "n_mos": v["t"]["n_mos"], "n_res": v["t"]["n_res"], "n_mim": len(v["t"]["mims"]),
                       "instances": v["n"]} for k, v in blk.items()},
        "macro": {"w": mac_w, "h": mac_h, "x": mac_x, "y": mac_y, "boxes": [b.d() for b in boxes],
                  "pins_west": pins_w, "pins_south": dig_pins,
                  "pin_status": {p: PIN_STATUS.get(p, "core") for p in list(pins_w) + dig_pins + ["AVDD", "AVSS"]},
                  "pin_fn": {v[0]: v[1] for v in ASSIGN.values()}},
        "netlist": os.path.relpath(NETLIST, MS),
        "chip": [b.d() for b in chip], "pads": pads, "wires": wires, "straps": straps,
        "digital": probe["digital"],
        "areas": {"core": core_area, "die": die_area, "analog": mac_area + cdm_area, "digital": dig_w * dig_h,
                  "macro": mac_area, "cdm": cdm_area},
        "cell": {"w": cell_w, "h": cell_h, "ha": cell_ha, "latch": [ff_w, ff_h]},
        "test_area": test_area, "bus_ch": bus_ch,
    }
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    with open(os.path.join(HERE, "data", "floorplan.json"), "w") as f:
        json.dump(out, f, indent=1)

    if os.environ.get("NODRAW"):
        return
    import draw
    draw.chip_svg(out, os.path.join(HERE, "assets", "chip_floorplan.svg"))
    draw.macro_svg(out, os.path.join(HERE, "assets", "analog_macro_floorplan.svg"))
    print("Measurements: mixed_signal/chip_floorplan/data/floorplan.json")
    print("Artifact: mixed_signal/chip_floorplan/assets/chip_floorplan.svg")
    print("Artifact: mixed_signal/chip_floorplan/assets/analog_macro_floorplan.svg")


if __name__ == "__main__":
    main()
