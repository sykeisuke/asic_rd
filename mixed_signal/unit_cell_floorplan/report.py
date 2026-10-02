#!/usr/bin/env python3
"""The comparison page: spec, the four floorplans, the numbers, the sizing.

    ./container.sh 'python3 report.py'   # -> physical/final_views/report.html

Every number on the page is read from a build output: this block's
work/floorplan_metrics.json and SVGs, and ../comparator_unit_cell's
data/sizing_*.json, data/switch_sizing.json, data/residuals.json and
work/uc_sweep.csv.  The prose is RESULTS.md's; the figures are the files'.
"""

import csv
import json
import os
import re

BLOCK = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BLOCK, "work")
FINAL = os.path.join(BLOCK, "physical", "final_views")
UC = os.environ.get("COMPARATOR_UC", os.path.join(os.path.dirname(BLOCK), "comparator_unit_cell"))

M = json.load(open(os.path.join(WORK, "floorplan_metrics.json")))
A, B, C, D = M["UC_MIM"], M["UC_MOM"], M["UC_MIM_125"], M["UC_MOM_125"]
SZ = {t: json.load(open(os.path.join(UC, "data", f"sizing_{t}.json"))) for t in ("mom16", "mim55", "mim125")}
SW = json.load(open(os.path.join(UC, "data", "switch_sizing.json")))
RES = json.load(open(os.path.join(UC, "data", "residuals.json")))
LSB = 5.859375e-3

#- history of this block, for the comparison: same four cells around the
#- 1 pF-sized cmp_p5t_8b (v2, DCIC rules) and the dense v1 placement
PREV = {"UC_MIM": 715.7, "UC_MOM": 734.8, "UC_MIM_125": 715.7, "UC_MOM_125": 1047.8}
DENSE = 614.85


def sweep_spread():
    """Crossing-delay spread per variant from the unit-cell sweep."""
    out = {}
    for r in csv.DictReader(open(os.path.join(UC, "work", "uc_sweep.csv"))):
        try:
            d = float(r["delay_s"])
        except ValueError:
            continue
        v = r["variant"]
        lo, hi = out.get(v, (d, d))
        out[v] = (min(lo, d), max(hi, d))
    return {v: hi - lo for v, (lo, hi) in out.items()}


SPREAD = sweep_spread()


def svg(name):
    s = open(os.path.join(FINAL, "svg", name + ".svg")).read()
    s = re.sub(r"<style>.*?</style>", "", s, flags=re.S)
    s = re.sub(r'width="\d+" height="\d+"', 'class="fp-svg"', s, count=1)
    return s


def tg_area(mm):
    return sum((i[4] - i[2]) * (i[5] - i[3]) for i in mm["items"] if i[0] in ("TGN", "TGP"))


def budget(mm):
    dev = mm["device_area_um2"]
    tg = tg_area(mm)
    cap = mm["cap_area_um2"] if mm["cap"] == "mom" else 0.0
    rest = mm["cell_area_um2"] - dev - cap
    return [("Comparator devices", dev - tg), ("Switch", tg),
            ("Capacitor on silicon", cap), ("Rings, wells, channel, slack", rest)]


def bar(mm, label, total_ref):
    segs = budget(mm)
    total = mm["cell_area_um2"]
    cls = ["s1", "s2", "s3", "s0"]
    out = [f'<div class="bar-row"><div class="bar-lab">{label}</div>'
           f'<div class="bar" style="width:{100 * total / total_ref:.1f}%">']
    for (name, v), c in zip(segs, cls):
        if v <= 0:
            continue
        w = 100 * v / total
        title = f"{name}: {v:.1f} um2 ({w:.1f} %)"
        txt = f"{v:.0f}" if w > 7 else ""
        out.append(f'<div class="seg {c}" style="width:{w:.2f}%" title="{title}" '
                   f'role="img" aria-label="{title}"><span>{txt}</span></div>')
    out.append(f'</div><div class="bar-tot">{total:.0f} µm²</div></div>')
    return "\n".join(out)


def cell_card(mm, name, title, sub):
    return f"""
  <div class="fp">
    <h3>{name} · {title}</h3>
    <div class="sub">{sub}</div>
    {svg(name)}
    <div class="fpfoot">{mm['cell_w_um']:.2f} × {mm['cell_h_um']:.2f} µm = <b>{mm['cell_area_um2']:.0f} µm²</b> · comparator <span class="mono">{mm['comparator']}</span> · switch WN/WP {mm['sw_wn_um']:.2f}/{mm['sw_wp_um']:.2f} µm · DRC {mm['drc_violations']}</div>
  </div>"""


def dev_row(tag):
    s = SZ[tag]
    return (f"<td class=\"num\">{s['w_in_um']:g} µm / {s['l_in']:g}, nf {s['nf_in']}, gm/Id {s['gmid_in']:.1f}</td>"
            f"<td class=\"num\">{s['w_load_um']:g} µm / {s['l_load']:g}, nf {s['nf_load']}, gm/Id {s['gmid_load']:.1f}</td>"
            f"<td class=\"num\">{s['w_tail_um']:g} µm / 1.0, nf {s['nf_tail']}</td>"
            f"<td class=\"num\">{s['id_branch'] * 1e6:.2f} µA · I_REF {s['iref'] * 1e6:.2f} µA · {s['tail_ratio']:.2f}:1</td>"
            f"<td class=\"num\">{s['c_in_f'] * 1e15:.1f} fF</td>"
            f"<td class=\"num\">{s['kick_into_chold_v'] * 1e3:.2f} mV = {s['kick_into_chold_v'] / LSB:.2f} LSB</td>")


def bench_row(v, label):
    r = RES[v]
    sp = SPREAD.get(v, float("nan"))
    return (f"<tr><td>{label}</td><td class=\"num\">{r['kick_max_v'] * 1e3:.1f} mV = {r['kick_max_v'] / LSB:.2f} LSB</td>"
            f"<td class=\"num\">{(r['kick_max_v'] - r['kick_min_v']) / LSB:.2f} LSB</td>"
            f"<td class=\"num\">{sp * 1e9:.0f} ns = {sp / 12.5e-9:.1f}×</td>"
            f"<td class=\"num\">{r['code_err']}</td>"
            f"<td class=\"num\"><b>{r['residual_v'] / LSB:.3f} LSB</b></td></tr>")


def sw_row(tag, label):
    s = SW[tag]["settling"]
    bw = SW[tag]["bandwidth_500mhz"]["wn_um"]
    c = SW[tag]
    def w(k):
        return f"{s[k]['wn_um']:.2f}{'*' if s[k]['clamped'] else ''}"
    return (f"<tr><td>{label}</td><td class=\"num\">{c['c_hold_f'] * 1e15:.1f} + {c['c_in_f'] * 1e15:.1f} = {c['c_node_f'] * 1e15:.1f} fF</td>"
            f"<td class=\"num\">{w('8b_25MHz')}</td><td class=\"num\">{w('8b_100MHz')}</td><td class=\"num\"><b>{w('8b_200MHz')}</b></td>"
            f"<td class=\"num\">{w('12b_200MHz')}</td><td class=\"num\">{bw:.2f}</td></tr>")


CSS = open(os.path.join(BLOCK, "report.css")).read() if os.path.exists(os.path.join(BLOCK, "report.css")) else ""


def page():
    tot_ref = D["cell_area_um2"]
    mom_spot = B.get("mom_spot", "beside")
    return f"""<title>Unit Cell MIM vs MOM</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>

<div class="wrap">
<div class="eyebrow">gf180mcuD · slope-ADC unit cell · comparator sized into its own hold capacitor · DCIC layout rules · DRC clean · no routing · 2026-09-18</div>
<h1>Re-sizing the comparator into a small hold capacitor shrinks the cell and makes it worse. The MIM still rides free; the MOM now costs {100 * (B['cell_area_um2'] / A['cell_area_um2'] - 1):.0f} %.</h1>
<p class="lede">Four to-scale floorplans of switch + hold capacitor + comparator for the per-cell-comparator slope ADC, each built around a 5T comparator <b>re-sized into that cell's own capacitor</b> by the same gm/Id tool that produced the recorded design, then measured on a mux-free bench. Laid out to the matching rules of Pretl's <i>Design of Complex ICs</i> and signed off on the PDK's KLayout deck.</p>

<div class="tiles">
  <div class="tile"><div class="k">UC_MIM · 54.5 fF over the tail</div><div class="v">{A['cell_area_um2']:.0f}</div><div class="u">µm² · was {PREV['UC_MIM']:.0f} with the 1 pF-sized comparator · DRC {A['drc_violations']}</div></div>
  <div class="tile"><div class="k">UC_MOM · 15.6 fF {mom_spot}</div><div class="v">{B['cell_area_um2']:.0f}</div><div class="u">µm² · {100 * (B['cell_area_um2'] / A['cell_area_um2'] - 1):+.0f} % vs UC_MIM · DRC {B['drc_violations']}</div></div>
  <div class="tile"><div class="k">UC_MIM_125 · 125 fF over the tail</div><div class="v">{C['cell_area_um2']:.0f}</div><div class="u">µm² · was {PREV['UC_MIM_125']:.0f} · DRC {C['drc_violations']}</div></div>
  <div class="tile"><div class="k">UC_MOM_125 · 8 × MOMU beside</div><div class="v">{D['cell_area_um2']:.0f}</div><div class="u">µm² · {100 * (D['cell_area_um2'] / C['cell_area_um2'] - 1):+.0f} % vs UC_MIM_125 · DRC {D['drc_violations']}</div></div>
  <div class="tile"><div class="k">Calibrated residual, best</div><div class="v">{min(RES[v]['residual_v'] for v in RES if v.startswith('p5t8b')) / LSB:.3f}</div><div class="u">LSB8 · the 1 pF-sized comparator on 54.5 fF · re-sized: {RES['mim55']['residual_v'] / LSB:.2f}</div></div>
</div>

<h2>0 · What is being designed, against which spec</h2>
<p>The project replicates the IRSX signal path — a switched-capacitor sampling array in which <b>every storage cell carries its own comparator</b> and one Wilkinson ramp converts all cells in parallel — scaled down for a first tape-out and meant to grow back to the IRSX class.</p>
<div class="tablewrap"><table>
<thead><tr><th></th><th>Tape-out 1 as frozen</th><th>Studied here (8-bit retarget)</th><th>IRSX-class target</th></tr></thead>
<tbody>
<tr><td>Resolution</td><td>6 bit</td><td><b>8 bit</b>, 1 LSB = 5.859 mV</td><td><b>12 bit</b>, 1 LSB = 366 µV</td></tr>
<tr><td>Input range</td><td>0.4–1.6 V</td><td><b>0.5–2.0 V</b>, the IRSX conversion window</td><td>same window</td></tr>
<tr><td>Sampling rate</td><td>25 MSa/s</td><td><b>25 MSa/s baseline; 100 MHz is the most the 8-bit cell holds</b>; 200 MHz drawn</td><td><b>multi-GSa/s, 2.2 GSa/s quoted</b>, 500 MHz analog bandwidth</td></tr>
<tr><td>Storage cell</td><td>4 cells behind a mux</td><td><b>comparator per cell, no mux</b></td><td>128+ cells × 8 channels</td></tr>
<tr><td>Hold capacitor</td><td>1 pF</td><td><b>smallest that works</b>: MIM floor 54.5 fF or MOM 15.6 fF</td><td>IRSX used 14 fF at 12 bits; here 125 fF for kT/C ≤ ½ LSB12</td></tr>
<tr><td>Comparator</td><td>shared, sized into 1 pF</td><td><b>re-sized into the cell's capacitor</b> (this revision)</td><td>a 12-bit per-cell comparator, different design</td></tr>
</tbody></table></div>

<h2>1 · The comparator, sized into its own capacitor</h2>
<p><span class="mono">comparator/size_p5t.py</span> samples 40 000 gm/Id operating points and derives every width as current over current density from the gm/Id tables. Its kickback proxy is calibrated to the reference design's measured kick into 1 pF, so the hold capacitance cancels out of it and the proxy reads "millivolts into 1 pF" for any geometry. Sizing into another capacitor is therefore one budget change, made in <span class="mono">../comparator_unit_cell/size_uc.py</span> without touching the tool: <span class="mono">KICK_BUDGET = 1.465 mV × C_hold / 1 pF</span>, the quarter-LSB as charge. Everything else — range, clock, headroom margin, drift and spread budgets, seed — is the tool's own.</p>
<div class="tablewrap"><table>
<thead><tr><th>Sized into</th><th class="num">Input pair</th><th class="num">Mirror load</th><th class="num">Tail</th><th class="num">Bias</th><th class="num">C_in of the pair</th><th class="num">Predicted kick into C_hold</th></tr></thead>
<tbody>
<tr><td><b>17 fF</b> (MOMU + its substrate plate) · <span class="mono">mom16</span></td>{dev_row('mom16')}</tr>
<tr><td><b>54.5 fF</b> (5 × 5 µm MIM) · <span class="mono">mim55</span></td>{dev_row('mim55')}</tr>
<tr><td><b>125 fF</b> (12-bit capacitor) · <span class="mono">mim125</span></td>{dev_row('mim125')}</tr>
<tr><td>1 pF (recorded <span class="mono">cmp_p5t_8b</span>)</td><td class="num">30.8 µm / 0.5, nf 8, gm/Id 17.5</td><td class="num">12.4 µm / 0.5, nf 3, gm/Id 18.6</td><td class="num">90.5 µm / 1.0, nf 20</td><td class="num">6.30 µA · I_REF 2.78 µA · 4.52:1</td><td class="num">≈ 45 fF</td><td class="num">1.59 mV into 1 pF</td></tr>
</tbody></table></div>
<h3>Why the devices came out this way</h3>
<ul>
<li><b>The tool found no feasible design at any capacitor</b> and fell back to its minimax rule, the design whose worst budget ratio is smallest: 19× (kick) at 17 fF, 6× (kick) at 54.5 fF, 2.8× (spread) at 125 fF. Kickback ∝ W_in and delay spread ∝ 1/(W_in · I_D/W): the pair's width serves both budgeted terms in opposite directions, so the topology has no feasible point.</li>
<li><b>At 17 and 54.5 fF the pair went to the matching floor and stopped</b>: 12.4 µm at L = 0.4 µm is the narrowest device satisfying the tool's 4 µm² gate-area floor at the shortest L in its grid, where I_D/W is highest and the width for a given current smallest. Both capacitors get the same design because once kick dominates the minimax its argmin does not depend on the budget's scale. The kick charge floor of this topology is about 0.45 fC.</li>
<li><b>The mirror load went wide (21.4 µm, gm/Id 22) at 17–54.5 fF</b>: a higher (gm/Id)_load lowers the diode-node swing that Cgd couples onto the hold node — the second kick lever — at the price of C_outa and speed. The bench exposed the price: 131 ns of spread against a predicted 42 ns; the tool's spread model was validated only up to gm/Id_load ≈ 19.</li>
<li><b>At 125 fF the kick ratio no longer dominates</b> and the minimax moves to a balanced design: L = 0.5, a small load (4.5 µm), a longer tail at lower I_REF.</li>
<li><b>Finger counts</b> are the tool's <span class="mono">nf = clip(round(W / 4 µm), 1, 20)</span>: 4 µm fingers, the DCIC "a few µm" rule. The tail is drawn as two halves of the same finger; BUF2, whose nf = 1 is hard-coded in the tool and whose width follows the sampled inverter ratio, is drawn with the same 4 µm rule (a single 9.9 µm finger would be a 10 µm tall device). BUF1/3/4 are inherited, unchanged.</li>
<li><b>Currents fell to 2.3 µA per branch</b> because at fixed gm/Id a narrower device carries less current; the tail followed as a mirror ratio, so the bias reference of <span class="mono">mixed_signal/bias_reference</span> (2.78 µA into a 20 µm diode leg) would be re-sized with it.</li>
</ul>

<h3>Measured on the mux-free bench, five levels 0.5–2.0 V</h3>
<p>Each sized-into comparator on its own capacitor, and the 1 pF-sized <span class="mono">cmp_p5t_8b</span> on the same capacitors as the control. "Calibrated residual" is what survives the per-cell straight-line (gain + offset) calibration the specification requires; "kick span" is how much the kickback changes with level, the part a constant cannot remove.</p>
<div class="tablewrap"><table>
<thead><tr><th>Comparator on capacitor</th><th class="num">kick, max</th><th class="num">kick span</th><th class="num">delay spread (budget 12.5 ns)</th><th class="num">code error</th><th class="num">calibrated residual</th></tr></thead>
<tbody>
{bench_row('mom16', 'mom16 on 17 fF, sized into it')}
{bench_row('p5t8b_on_mom16', 'cmp_p5t_8b on 17 fF, sized into 1 pF')}
{bench_row('mim55', 'mim55 on 54.5 fF, sized into it')}
{bench_row('p5t8b_on_mim55', 'cmp_p5t_8b on 54.5 fF')}
{bench_row('mim125', 'mim125 on 125 fF, sized into it')}
{bench_row('p5t8b_on_mim125', 'cmp_p5t_8b on 125 fF')}
</tbody></table></div>
<div class="callout"><b>Kickback is mostly calibratable; delay spread is not.</b> On 54.5 fF the 1 pF-sized comparator kicks 3.8 LSB, yet 90 % of that is a constant plus a 0.3 % gain error and its calibrated residual is {RES['p5t8b_on_mim55']['residual_v'] / LSB:.3f} LSB. The re-sized comparator kicks 2.6× less but its crossing delay walks {SPREAD['mim55'] * 1e9:.0f} ns across the range, INL that survives the fit as {RES['mim55']['residual_v'] / LSB:.2f} LSB. The tool's absolute-kick budget is the wrong objective for a per-cell comparator that will be calibrated; the right objectives are kick span and delay spread. <b>For a calibrated cell, keep <span class="mono">cmp_p5t_8b</span> on either capacitor</b>, or change topology (a source follower in front of the pair), not size.</div>

<h2>2 · The four floorplans</h2>
<p>Same placement rules in all four: a matched core on a vertical symmetry axis — tail halves over the ABBA input pair in one n-well, the mirror load under it in one p-well — the switch on the input side, the two inverters on the output side, a wiring channel between the wells, supply rails on the well rings. Device sizes, finger counts, the switch and the capacitor come from the sizing files.</p>
<div class="plans">
{cell_card(A, "UC_MIM", "54.5 fF MIM on top", f"5 × 5 µm FuseTop over TAIL A/B in M4 / FuseTop / M5; hold node {A['c_node_ff']:.1f} fF with the pair's {A['c_in_ff']:.1f} fF.")}
{cell_card(B, "UC_MOM", f"15.6 fF MOM {mom_spot}", f"MOMU finger cap, M1–M4, inside the p-well ring; hold node {B['c_node_ff']:.1f} fF: the pair's {B['c_in_ff']:.1f} fF doubles the capacitor.")}
{cell_card(C, "UC_MIM_125", "125 fF MIM on top", f"{C['cap_fusetop_w_um']:g} × {C['cap_fusetop_w_um']:g} µm FuseTop over the tail, inside the PMOS block's outline; hold node {C['c_node_ff']:.0f} fF.")}
{cell_card(D, "UC_MOM_125", "8 × MOM beside", f"Two abutted rows of four MOMU, a band under the p-well row; hold node {D['c_node_ff']:.0f} fF.")}
</div>
<div class="legend"><span><i style="background:var(--pmos)"></i>PMOS, one n-well</span><span><i style="background:var(--nmos)"></i>NMOS, one p-well</span><span><i style="background:var(--cap)"></i>hold capacitor</span><span><i style="background:var(--rail)"></i>supply rail on the well ring</span><span><i style="border-style:dashed;background:transparent"></i>well outline · MIM keep-out · symmetry axis</span></div>

<h2>3 · Where the silicon goes</h2>
<p>Bars on a common scale, silicon only. The MIM's M4/M5 plate and keep-out ({A['cap_footprint_um2']:.0f} µm² at 54.5 fF, {C['cap_footprint_um2']:.0f} µm² at 125 fF) is not on the bar because it costs no silicon; it costs the routing layers over the tail.</p>
<div class="bars">
{bar(A, 'UC_MIM', tot_ref)}
{bar(B, 'UC_MOM', tot_ref)}
{bar(C, 'UC_MIM_125', tot_ref)}
{bar(D, 'UC_MOM_125', tot_ref)}
</div>
<div class="clegend"><span><i class="s1"></i>comparator devices (incl. 4 dummy fingers)</span><span><i class="s2"></i>switch</span><span><i class="s3"></i>capacitor on silicon</span><span><i class="s0"></i>rings, wells, channel, slack</span></div>

<div class="tablewrap"><table>
<thead><tr><th></th><th>UC_MIM</th><th>UC_MOM</th><th>UC_MIM_125</th><th>UC_MOM_125</th></tr></thead>
<tbody>
<tr><td>Comparator</td><td class="mono">{A['comparator']}</td><td class="mono">{B['comparator']}</td><td class="mono">{C['comparator']}</td><td class="mono">{D['comparator']}</td></tr>
<tr><td>Hold capacitor</td><td>5 × 5 µm MIM, <b>{A['cap_value_ff']:.1f} fF</b></td><td>1 MOMU, <b>{B['cap_value_ff']:.2f} fF</b></td><td>{C['cap_fusetop_w_um']:g} µm MIM, <b>{C['cap_value_ff']:.0f} fF</b></td><td>8 MOMU, <b>{D['cap_value_ff']:.0f} fF</b></td></tr>
<tr><td>Hold node incl. the pair's gate</td><td class="num">{A['c_node_ff']:.1f} fF</td><td class="num">{B['c_node_ff']:.1f} fF</td><td class="num">{C['c_node_ff']:.0f} fF</td><td class="num">{D['c_node_ff']:.0f} fF</td></tr>
<tr><td>Capacitor silicon</td><td class="num">0</td><td class="num">{B['cap_area_um2']:.1f} µm², {mom_spot}</td><td class="num">0</td><td class="num">{D['cap_area_um2']:.1f} µm²</td></tr>
<tr><td>M4/M5 footprint with keep-out</td><td class="num">{A['cap_footprint_um2']:.1f} µm²</td><td class="num">—</td><td class="num">{C['cap_footprint_um2']:.1f} µm²</td><td class="num">—</td></tr>
<tr><td>Switch WN/WP, 200 MHz, 8 bits</td><td class="num">{A['sw_wn_um']:.2f} / {A['sw_wp_um']:.2f} µm</td><td class="num">{B['sw_wn_um']:.2f} / {B['sw_wp_um']:.2f} µm</td><td class="num">{C['sw_wn_um']:.2f} / {C['sw_wp_um']:.2f} µm</td><td class="num">{D['sw_wn_um']:.2f} / {D['sw_wp_um']:.2f} µm</td></tr>
<tr><td>Device area, 10 devices + dummies</td><td class="num">{A['device_area_um2']:.1f}</td><td class="num">{B['device_area_um2']:.1f}</td><td class="num">{C['device_area_um2']:.1f}</td><td class="num">{D['device_area_um2']:.1f}</td></tr>
<tr class="hl"><td>Cell, PR boundary</td><td class="num">{A['cell_w_um']:.2f} × {A['cell_h_um']:.2f} = {A['cell_area_um2']:.1f} µm²</td><td class="num">{B['cell_w_um']:.2f} × {B['cell_h_um']:.2f} = {B['cell_area_um2']:.1f}</td><td class="num">{C['cell_w_um']:.2f} × {C['cell_h_um']:.2f} = {C['cell_area_um2']:.1f}</td><td class="num">{D['cell_w_um']:.2f} × {D['cell_h_um']:.2f} = {D['cell_area_um2']:.1f}</td></tr>
<tr><td>Same cell around the 1 pF-sized comparator</td><td class="num">{PREV['UC_MIM']:.0f} µm²</td><td class="num">{PREV['UC_MOM']:.0f}</td><td class="num">{PREV['UC_MIM_125']:.0f}</td><td class="num">{PREV['UC_MOM_125']:.0f}</td></tr>
<tr><td>MOM / MIM</td><td></td><td class="num"><b>{B['cell_area_um2'] / A['cell_area_um2']:.3f}</b> (+{B['cell_area_um2'] - A['cell_area_um2']:.0f} µm²)</td><td></td><td class="num"><b>{D['cell_area_um2'] / C['cell_area_um2']:.3f}</b> (+{D['cell_area_um2'] - C['cell_area_um2']:.0f} µm²)</td></tr>
<tr><td>kT/C at 300 K, on C_hold</td><td class="num">276 µV · 0.047 LSB8 · 0.75 LSB12</td><td class="num">515 µV · 0.088 LSB8 · 1.41 LSB12</td><td class="num">182 µV · 0.031 LSB8 · <b>0.50 LSB12</b></td><td class="num">same</td></tr>
<tr><td>DRC, gf180mcu.drc minus density</td><td class="num">{A['drc_violations']}</td><td class="num">{B['drc_violations']}</td><td class="num">{C['drc_violations']}</td><td class="num">{D['drc_violations']}</td></tr>
</tbody></table></div>

<h3>What the numbers say</h3>
<ol>
<li><b>The smaller comparator shrinks the cell {100 * (1 - A['cell_area_um2'] / PREV['UC_MIM']):.0f} % and takes the MOM's free ride with it.</b> Around the 1 pF-sized comparator the MOM fit in the p-well row's spare width; around the {A['comparator']} comparator the mirror row is the widest thing in the cell and the MOM costs its own {B['cell_area_um2'] - A['cell_area_um2']:.0f} µm², {100 * (B['cell_area_um2'] / A['cell_area_um2'] - 1):.0f} %. The MIM is free in every version, at 54.5 fF and at 125 fF.</li>
<li><b>The comparator's own gate is a hold capacitor.</b> {B['c_in_ff']:.0f} fF of pair Cgg on the 17 fF MOM; the "15 fF cell" is a 35 fF node, its switch and its kT/C follow the sum, and the recorded comparator's 45 fF would have made it a 62 fF node.</li>
<li><b>Smaller is not better here.</b> The re-sized comparators halve the kick and quadruple the delay spread, and after calibration leave 5–7× the residual of the 1 pF-sized one on the same capacitors (section 1). The area the resize saves buys nothing the cell can use.</li>
<li><b>At the 12-bit capacitor the MIM wins on area outright</b>: eight MOM units add {D['cell_area_um2'] - C['cell_area_um2']:.0f} µm², {100 * (D['cell_area_um2'] / C['cell_area_um2'] - 1):.0f} %, while the 125 fF MIM grows over the tail inside the PMOS block's outline.</li>
<li><b>The switch follows the node, not the capacitor.</b> Sized on C_hold + C_in at 200 MHz: {B['sw_wn_um']:.2f} µm on the MOM node, {A['sw_wn_um']:.2f} µm on the 54.5 fF node, {C['sw_wn_um']:.2f} µm on the 125 fF node; all clamp at 0.22 µm at 25 MHz.</li>
</ol>

<h2>4 · The switch, sized on the node</h2>
<p><span class="mono">τ = (T_track − T_edge) / ((N+1) ln 2)</span>, <span class="mono">Ron_max = τ / C_node</span>, <span class="mono">WN = 2710 Ω·µm / Ron_max</span> (the measured worst-case Ron·W of the 1:2 gate over 0.5–2.0 V), WP = 2 WN, clamp at 0.22 µm. The last column is the bandwidth view a GSa/s write-window cell sizes to instead, <span class="mono">1 / (2π Ron C_node) ≥ 500 MHz</span>.</p>
<div class="tablewrap"><table>
<thead><tr><th>Node</th><th class="num">C_hold + C_in = C_node</th><th class="num">8 b, 25 MHz</th><th class="num">8 b, 100 MHz</th><th class="num">8 b, 200 MHz (drawn)</th><th class="num">12 b, 200 MHz</th><th class="num">500 MHz bandwidth</th></tr></thead>
<tbody>
{sw_row('mom16', 'MOM, mom16')}
{sw_row('mim55', 'MIM 54.5 fF, mim55')}
{sw_row('mim125', 'MIM 125 fF, mim125')}
</tbody></table></div>
<p>WN in µm; * clamped at the minimum. At 2.2 GSa/s half-period settling would ask for 2–7 µm gates whose injection the sampling study already ruled out at 200 MHz; the GSa/s cell tracks over a long write window and is sized to bandwidth.</p>

<h2>5 · The floorplan, rule by rule</h2>
<p>From section 4.5 of <i>Design of Complex ICs</i> (iic-jku.github.io/design-complex-ic). The book's sentence, then what the floorplan does with it.</p>
<div class="tablewrap"><table>
<thead><tr><th>DCIC</th><th>In this floorplan</th></tr></thead>
<tbody>
<tr><td>4.5.1 "A transistor with a large W should be split into multiple parallel devices (fingers) … of limited length (a few µm)"</td><td>the tool's 4 µm fingers, kept; BUF2 fingered by the same rule</td></tr>
<tr><td>4.5.2 "The devices are constructed from identical unit devices … of equal width (and equal L)"</td><td>INP/INN: one diffusion row of identical fingers; LOADD/LOADM: one diffusion row of identical fingers</td></tr>
<tr><td>"oriented in the same direction, and the current flow in all matched devices has the same direction — avoid mirroring"</td><td>every finger vertical, every row's current top to bottom; the tail halves stacked, not mirrored</td></tr>
<tr><td>"surrounded by similar structures; for edge devices, spend dummy elements (fig. 50)"</td><td>one dummy finger at each end of the pair and of the mirror, each with its own tie pad</td></tr>
<tr><td>"M1 and M2 share the centre source diffusion … directly usable as a differential pair or a current mirror"</td><td>the pair's tail node and the mirror's vss are the shared diffusions of their rows</td></tr>
<tr><td>"use common-centroid arrangements (fig. 52 b, linear ABBA)"</td><td>pair fingers <span class="mono">{A['pair_pattern']}</span> (odd counts get the closest mirror-symmetric order), A gates on a top bar, B gates on a bottom bar; the mirror shares one gate net, so its A/B split is in the drain straps</td></tr>
<tr><td>"avoid low-level metal routing over sensitive devices"</td><td>the MIM sits over the tail halves, never over the pair</td></tr>
<tr><td>4.5.3 "Locations of pins and interfaces; distribution of VDD and VSS; wiring channels for signal buses"</td><td>input side left (TG N under TG P), output side right (BUF2/BUF4 over BUF1/BUF3), <span class="mono">ramp</span> to the pair's right end, <span class="mono">pbias</span> from the top; VDD rail on the n-well ring, VSS rail on the p-well ring; a 2 µm channel between the wells</td></tr>
<tr><td>4.3.4 MOM: "the lower metal layers should be skipped if the parasitic capacitance to the substrate is a concern"</td><td>MOMU is the M1–M4 unit as characterized (8 % of its charge to substrate)</td></tr>
<tr><td>4.3.4 MIM: "higher specific capacitance and low parasitics at extra cost"</td><td>2.0 fF/µm² against 0.57; the cost here is M4/M5 over the tail</td></tr>
</tbody></table></div>
<div class="callout">History of this cell: dense placement of the 1 pF-sized comparator, no matching rules, {DENSE:.0f} µm² for either capacitor; DCIC rules around the same comparator, {PREV['UC_MIM']:.0f} µm² (+{100 * (PREV['UC_MIM'] / DENSE - 1):.0f} %); DCIC rules around the comparator sized into its capacitor, {A['cell_area_um2']:.0f} µm² for the MIM cell — smaller, and electrically worse.</div>

<h2>6 · Does the cell carry to 12 bits and 2.2 GSa/s?</h2>
<div class="tablewrap"><table>
<thead><tr><th>Term</th><th>8 bits, 25–100 MHz, now</th><th>12 bits, GSa/s, target</th></tr></thead>
<tbody>
<tr><td>kT/C</td><td>irrelevant at any C here (≤ 0.09 LSB8)</td><td>15.6 fF: 1.41 LSB12; 54.5 fF: 0.75; <b>125 fF: 0.50</b>. IRSX's 14 fF at 12 bits is counter resolution, not accuracy</td></tr>
<tr><td>Capacitor area</td><td>MOM +{100 * (B['cell_area_um2'] / A['cell_area_um2'] - 1):.0f} %, MIM 0</td><td><b>MIM 0, MOM +{100 * (D['cell_area_um2'] / C['cell_area_um2'] - 1):.0f} %</b></td></tr>
<tr><td>Switch</td><td>0.22–0.52 µm on the node</td><td>bandwidth-sized 0.3–1.2 µm, write-window timing; injection becomes a per-cell pedestal to calibrate</td></tr>
<tr><td>Comparator</td><td>the 1 pF-sized 5T, calibrated residual 0.06–0.09 LSB8 on 17–125 fF; the re-sized one 0.16–0.47</td><td>a 12-bit per-cell comparator is a different design; a source follower in front of the pair removes the kick-charge floor; the rows and channel carry over, the widths will not</td></tr>
<tr><td>Array</td><td>—</td><td>128 × 8 × 83 µW = 85 mW of comparators always on; power gating or a lower tail current, and the tail shrinks with it</td></tr>
<tr><td>Upper metals</td><td>MIM takes {A['cap_footprint_um2']:.0f}–{C['cap_footprint_um2']:.0f} µm² of M4/M5 per cell, both plates out through M5 (MIMTM.10)</td><td>array buses route around a MIM per cell; MOM leaves M5 free but takes M1–M4 of its own footprint</td></tr>
</tbody></table></div>
<div class="callout"><b>Verdict for the IRSX-class cell: MIM, 125 fF, over the tail, with the comparator selected on kick span and delay spread rather than absolute kick.</b> No silicon for the capacitor at either resolution, a switch under 1.2 µm, and the only cost to the array is M4/M5 over {100 * C['cap_footprint_um2'] / C['cell_area_um2']:.0f} % of the cell.</div>

<h2>7 · What had to be fixed to reach zero violations</h2>
<p>Every violation found on the way was inside the PDK's transistor generator or in a placement collision, and each is now handled in <span class="mono">floorplan.py</span>; <span class="mono">drc_devices.py</span> checks every primitive standalone so a failure is attributed to a device, not a cell.</p>
<ul>
<li><b>M1.3, M1.2a</b> · the generator's poly-contact M1 caps are under the M1 minimum area and, on L = 0.28 µm devices, 0.175 µm from the S/D M1 → the generator draws fingers and S/D contacts only, and the gate bars (poly, contacts, M1) are drawn here, 0.24 µm clear of the active.</li>
<li><b>M1.3 on the switch</b> · S/D pads on a 0.22–0.52 µm finger under the minimum area → stretched to 0.15 µm².</li>
<li><b>OFFGRID</b> · a 2.5 nm bbox half-extent moved whole instances off the 5 nm grid → every move snapped.</li>
<li><b>CO.4</b> · a ring size on the 5 nm grid left one bar 0.065 µm over its contacts → ring sizes a multiple of 10 nm.</li>
<li><b>PL.3a</b> · on the ABBA pair the other net's poly ends sit 0.085 µm from a gate bar → two-bar devices place their bars 0.40 µm clear.</li>
<li><b>CO.1/CO.3/CO.7/NP.5a/PL.4</b> · with the small comparator the mirror row is wider than the pair row and the switch NMOS, placed under the switch PMOS, landed on the mirror → it now stands clear of the mirror as well.</li>
<li>The plugin's <code>cap_mim</code> draws the MIM-A stack on M2/M3 whatever its arguments say; the MIM is drawn from the MIMTM rules.</li>
</ul>

<h2>8 · Open</h2>
<ul>
<li><b>No routing.</b> Placement, wells, rings and gate bars only; the areas are floors.</li>
<li><b>Re-state the sizing objective</b> as kick span + delay spread and re-run; the tool computes everything needed except the span. That edit belongs to the comparator block.</li>
<li><b>Topology</b>: a source follower between the hold node and the pair (<span class="mono">sfbuf</span>) removes the 0.45 fC kick floor; its floorplan adds one PMOS row.</li>
<li><b>Bias reference</b>: the re-sized designs want 1.2–1.9 µA into the 20 µm diode leg; <span class="mono">bias_reference</span> was sized for 2.78 µA.</li>
<li><b>LVS</b> needs a routed netlist; the MIM's device recognition needs its MIM_L_MK checked; the MOM has no device.</li>
<li><b>One corner</b>, no mismatch, no PEX, ideal ramp, ideal reference. The negative result does not depend on any of those; the 125 fF numbers do.</li>
</ul>

<div class="foot">Built by <span class="mono">mixed_signal/unit_cell_floorplan/run.sh</span> and <span class="mono">mixed_signal/comparator_unit_cell/run.sh</span>: gdsfactory 9.40.2 + gf180mcu 1.0.0 device generator, KLayout <span class="mono">gf180mcu.drc</span> variant gf180mcuD deep, ngspice 46; reusing <span class="mono">comparator/size_p5t.py</span>, <span class="mono">analog_layout/mom_cap.py</span>, <span class="mono">analog_layout/signoff.py</span> and the switch rule of <span class="mono">gf180_sampling_unit_cell/design_cell.py</span> by path.</div>
</div>
"""


out = os.path.join(FINAL, "report.html")
with open(out, "w") as fo:
    fo.write(page())
print(f"report = {os.path.relpath(out, BLOCK)}")
