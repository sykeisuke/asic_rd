#!/usr/bin/env python3
"""One picture per flow step, drawn from that step's own OpenROAD database.

    openroad -python -exit scripts/render_steps.py [RUN_DIR]

RUN_DIR defaults to librelane/runs/chip_top. Run inside the container
(scripts/build.sh renders). For every step below it opens the step's
`chip_top.odb` (what OpenROAD itself left after that step, not a
re-creation), draws it as SVG and converts the SVG to PNG (cairosvg):

    01_template_padring     after OpenROAD.PadRing: the template's 1x0p5 ring
    02_chip_top_wiring      after Odb.ManualMacroPlacement: pads labelled by
                            the macro pin their chip_top.sv net reaches,
                            straight fly lines pad -> macro pin
    04a_floorplan_macros    after OpenROAD.TapEndcapInsertion: die, core,
                            rows, both macros, the ID macros
    04b_power_grid          after OpenROAD.GeneratePDN: core ring, straps,
                            AVDD / AVSS / analog special wiring
    04c_placement_cts       after OpenROAD.CTS: standard cells, clock cells red
    04d_routing             after OpenROAD.DetailedRouting: every routed
                            signal wire, coloured by metal
    05a_analog_routes_zoom  after OpenROAD.GeneratePDN, zoomed: the drawn
                            west analog pad wires (analog_routes.tcl)
    05b_supply_straps_zoom  same database, zoomed: the drawn AVDD / AVSS /
                            DVDD / DVSS straps (power_routes.tcl)

Prints `render_steps_missing = N` (steps whose database was not found)
and writes work/render/windows.json, the zoom windows in um, which
scripts/render_gds.py re-uses on the final GDS.
"""

import glob
import json
import os
import sys

import odb

HERE = os.getcwd()
RUN = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
    else os.path.join(HERE, "librelane", "runs", "chip_top")
OUT = os.path.join(HERE, "renders")

#- colours: pads by function, wires by metal, nets by supply
PADC = {"signal_out": "#9aa0a6", "signal_in": "#80868b", "analog": "#e8710a",
        "vdd": "#d93025", "vss": "#1a73e8", "dvdd": "#f28b82", "dvss": "#8ab4f8",
        "avdd": "#a50e0e", "brk": "#202124", "cor": "#5f6368", "fill": "#e8eaed"}
PADNAME = {"signal_out": "digital I/O (bi_24t)", "signal_in": "digital input (in_c / in_s)",
           "analog": "analog (bi_a / asig_5p0)", "vdd": "core VDD", "vss": "core VSS",
           "dvdd": "I/O DVDD", "dvss": "I/O DVSS", "avdd": "AVDD (re-typed vdd)",
           "brk": "rail break (brk5)", "cor": "corner", "fill": "filler"}
METALC = {"Metal1": "#4c8bf5", "Metal2": "#e8710a", "Metal3": "#1e8e3e",
          "Metal4": "#a142f4", "Metal5": "#8b5a2b"}
NETC = {"VDD": "#d93025", "VSS": "#1a73e8", "AVDD": "#a50e0e", "analog": "#e8710a"}


# ------------------------------------------------------------------ database
def step_odb(pattern):
    hits = sorted(glob.glob(os.path.join(RUN, pattern, "chip_top.odb")))
    return hits[-1] if hits else None


def load(path):
    db = odb.dbDatabase.create()
    odb.read_db(db, path)
    return db.getChip().getBlock()


class Chip:
    def __init__(self, block):
        self.b = block
        self.u = float(block.getDbUnitsPerMicron())
        d, c = block.getDieArea(), block.getCoreArea()
        self.die = self.box(d)
        self.core = self.box(c)

    def box(self, r):
        return (r.xMin() / self.u, r.yMin() / self.u, r.xMax() / self.u, r.yMax() / self.u)

    def pads(self):
        """(instance, kind, bbox um, cell) for every pad-ring cell."""
        out = []
        for i in self.b.getInsts():
            m = i.getMaster()
            if not m.isPad() and "ocd_io" not in m.getName():
                continue
            cell = m.getName().split("__")[-1]
            nets = {it.getMTerm().getName(): it.getNet().getName()
                    for it in i.getITerms() if it.getNet()}
            if cell.startswith("fill"):
                kind = "fill"
            elif cell == "cor":
                kind = "cor"
            elif cell.startswith("brk"):
                kind = "brk"
            elif cell in ("bi_a", "asig_5p0"):
                kind = "analog"
            elif cell in ("in_c", "in_s"):
                kind = "signal_in"
            elif cell == "bi_24t":
                kind = "signal_out"
            elif cell == "vdd":
                kind = "avdd" if nets.get("VDD") == "AVDD" else "vdd"
            elif cell in ("vss", "dvdd", "dvss"):
                kind = cell
            else:
                kind = "fill"
            out.append((i, kind, self.box(i.getBBox()), cell))
        return out

    def macros(self):
        return [(i, self.box(i.getBBox())) for i in self.b.getInsts()
                if i.getMaster().isBlock()]

    def side(self, bb):
        x0, y0, x1, y1 = self.die
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        d = {"W": cx - x0, "E": x1 - cx, "S": cy - y0, "N": y1 - cy}
        return min(d, key=d.get)

    def reach(self, inst, maxdepth=6):
        """Macro pins a pad is wired to, read back from the synthesised
        netlist (what chip_top.sv / chip_core.sv describe). The walk follows
        signal direction, so a shared net (acquire gating every S0) does
        not leak into its neighbours:

        - forward from the pad's Y (pad -> core): through each cell input
          on the net to that cell's outputs, until a macro input;
        - backward from the pad's A (core -> pad): to the net's driver,
          through its inputs, until a macro output;
        - ASIG5V (VIN) is a direct analog net: its macro pin is a hit.

        Tie cells and pads stop the walk. bi_a's ANA is not in the netlist
        (its liberty lacks the pin): those pads reach nothing here and are
        connected by analog_routes.tcl in step 5."""
        hits, seen = [], set()

        def walk(net, forward, dep):
            if net is None or net.getId() in seen or dep > maxdepth or \
                    net.getSigType() in ("POWER", "GROUND"):
                return
            seen.add(net.getId())
            for it in net.getITerms():
                j = it.getInst()
                if j.getId() == inst.getId():
                    continue
                m = j.getMaster()
                if forward and not it.isInputSignal():
                    continue
                if not forward and not it.isOutputSignal():
                    continue
                if m.isBlock():
                    hits.append((j, it))
                    continue
                if m.isPad() or "tie" in m.getName().lower():
                    continue
                for jt in j.getITerms():
                    if (jt.isOutputSignal() if forward else jt.isInputSignal()):
                        walk(jt.getNet(), forward, dep + 1)

        for it in inst.getITerms():
            n, t = it.getNet(), it.getMTerm().getName()
            if n is None:
                continue
            if t == "Y":
                walk(n, True, 0)
            elif t == "A":
                walk(n, False, 0)
            elif t == "ASIG5V":
                hits += [(x.getInst(), x) for x in n.getITerms()
                         if x.getInst().getMaster().isBlock()]
        return hits

    def special_boxes(self, net):
        for sw in net.getSWires():
            for w in sw.getWires():
                if w.isVia():
                    continue
                yield w.getTechLayer().getName(), self.box(w)

    def wires(self, net):
        """Routed segments of a signal net: (layer, x0, y0, x1, y1) um."""
        w = net.getWire()
        if w is None:
            return
        dec = odb.dbWireDecoder()
        dec.begin(w)
        prev, layer = None, None
        D = odb.dbWireDecoder
        while True:
            op = dec.next()
            if op == D.END_DECODE:
                break
            if op in (D.PATH, D.JUNCTION, D.SHORT, D.VWIRE):
                prev = None
                layer = dec.getLayer().getName()
            elif op in (D.POINT, D.POINT_EXT):
                x, y = dec.getPoint()[:2]
                if prev is not None and (x, y) != prev:
                    yield layer, prev[0] / self.u, prev[1] / self.u, x / self.u, y / self.u
                prev = (x, y)
            elif op in (D.VIA, D.TECH_VIA):
                layer = dec.getLayer().getName()


# ----------------------------------------------------------------------- SVG
class Svg:
    def __init__(self, win, width_px, title, subtitle):
        self.win = win
        x0, y0, x1, y1 = win
        self.s = width_px / (x1 - x0)
        self.top = 74
        self.w = width_px
        self.h = (y1 - y0) * self.s
        self.o = []
        self.legend = {}
        self.title, self.subtitle = title, subtitle

    def X(self, x): return (x - self.win[0]) * self.s

    def Y(self, y): return self.top + (self.win[3] - y) * self.s

    def rect(self, bb, fill="none", stroke="none", sw=1, op=1.0, dash=None, minpx=0):
        x0, y0, x1, y1 = bb
        w, h = max((x1 - x0) * self.s, minpx), max((y1 - y0) * self.s, minpx)
        cx, cy = self.X((x0 + x1) / 2), self.Y((y0 + y1) / 2)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<rect x="{cx - w / 2:.2f}" y="{cy - h / 2:.2f}" width="{w:.2f}" '
                      f'height="{h:.2f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" '
                      f'stroke-width="{sw}"{d}/>')

    def line(self, x0, y0, x1, y1, color, sw=1.0, op=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<line x1="{self.X(x0):.2f}" y1="{self.Y(y0):.2f}" x2="{self.X(x1):.2f}" '
                      f'y2="{self.Y(y1):.2f}" stroke="{color}" stroke-width="{sw}" '
                      f'stroke-opacity="{op}"{d}/>')

    def text(self, x, y, s, size=11, anchor="start", rot=0, color="#202124", weight="normal"):
        X, Y = self.X(x), self.Y(y)
        t = f' transform="rotate({rot} {X:.1f} {Y:.1f})"' if rot else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.o.append(f'<text x="{X:.1f}" y="{Y:.1f}" font-size="{size}" text-anchor="{anchor}" '
                      f'fill="{color}" font-weight="{weight}"{t}>{s}</text>')

    def key(self, name, color):
        self.legend[name] = color

    def write(self, name):
        lines, lx, ly = [], 16, self.top + self.h + 24
        for n, c in self.legend.items():
            wpx = 28 + 7 * len(n)
            if lx + wpx > self.w - 10:
                lx, ly = 16, ly + 20
            lines.append(f'<rect x="{lx}" y="{ly - 11}" width="13" height="13" fill="{c}"/>'
                         f'<text x="{lx + 18}" y="{ly}" font-size="12">{n}</text>')
            lx += wpx
        H = ly + 14
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{H:.0f}" '
                f'viewBox="0 0 {self.w:.0f} {H:.0f}" font-family="Helvetica,Arial,sans-serif">',
                '<rect width="100%" height="100%" fill="white"/>',
                f'<text x="16" y="30" font-size="20" font-weight="bold">{self.title}</text>',
                f'<text x="16" y="54" font-size="13" fill="#5f6368">{self.subtitle}</text>',
                f'<clipPath id="c"><rect x="0" y="{self.top}" width="{self.w:.0f}" '
                f'height="{self.h:.0f}"/></clipPath><g clip-path="url(#c)">']
        svg = "\n".join(head + self.o + ["</g>"] + lines + ["</svg>"])
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w") as f:
            f.write(svg)
        try:
            import cairosvg
            cairosvg.svg2png(bytestring=svg.encode(), write_to=path[:-4] + ".png",
                             output_width=int(self.w * 1.5))
        except Exception as e:
            print(f"REPORT: render: no PNG for {name}: {e}")
        print(f"SVG: {path}")


# ------------------------------------------------------------------- drawing
def base(c, svg, pads=True, fill_pads=False, macros=True, label_macros=True):
    svg.rect(c.die, fill="#fafafa", stroke="#202124", sw=2)
    svg.rect(c.core, stroke="#9aa0a6", sw=1, dash="6,4")
    if pads:
        for i, kind, bb, cell in c.pads():
            if kind == "fill" and not fill_pads:
                continue
            svg.rect(bb, fill=PADC[kind], stroke="#5f6368" if kind != "fill" else "none", sw=0.4)
            svg.key(PADNAME[kind], PADC[kind])
    if macros:
        for i, bb in c.macros():
            n = i.getMaster().getName()
            if n == "asic_digital_top":
                svg.rect(bb, fill="#e6f4ea", stroke="#137333", sw=2)
                if label_macros:
                    svg.text((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, "digital top",
                             14, "middle", color="#137333", weight="bold")
            elif n == "wsa_analog_top":
                svg.rect(bb, fill="#e8f0fe", stroke="#1967d2", sw=2)
                if label_macros:
                    svg.text((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, "analog top",
                             14, "middle", color="#1967d2", weight="bold")
            else:
                svg.rect(bb, fill="#dadce0", stroke="#5f6368", sw=1)
                if label_macros:
                    svg.text((bb[0] + bb[2]) / 2, bb[3] + 8, n.replace("gf180mcu_ws_ip__", ""),
                             10, "middle", color="#5f6368")


def pad_label(c, svg, bb, s, size=10, color="#202124"):
    side = c.side(bb)
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    gap = 6 / svg.s
    if side == "W":
        svg.text(bb[2] + gap, cy - 3.5 / svg.s, s, size, "start", color=color)
    elif side == "E":
        svg.text(bb[0] - gap, cy - 3.5 / svg.s, s, size, "end", color=color)
    elif side == "S":
        svg.text(cx + 3.5 / svg.s, bb[3] + gap, s, size, "start", rot=-90, color=color)
    else:
        svg.text(cx + 3.5 / svg.s, bb[1] - gap, s, size, "end", rot=-90, color=color)


def supply_label(i, kind):
    return {"vdd": "VDD", "vss": "VSS", "dvdd": "DVDD", "dvss": "DVSS", "avdd": "AVDD"}.get(kind)


def draw_special(c, svg, nets=None, only_analog=False):
    for net in c.b.getNets():
        if not net.isSpecial():
            continue
        name = net.getName()
        st = net.getSigType()
        if st == "SIGNAL":
            col, key = NETC["analog"], "analog pad wire (drawn)"
        elif name == "AVDD":
            col, key = NETC["AVDD"], "AVDD (drawn)"
        elif st == "POWER":
            col, key = NETC["VDD"], "VDD grid / ring"
        elif st == "GROUND":
            col, key = NETC["VSS"], "VSS grid / ring"
        else:
            continue
        if only_analog and st not in ("SIGNAL",) and name != "AVDD":
            continue
        if nets is not None and name not in nets:
            continue
        drew = False
        for layer, bb in c.special_boxes(net):
            svg.rect(bb, fill=col, op=0.75 if st != "SIGNAL" else 1.0, minpx=0.8)
            drew = True
        if drew:
            svg.key(key, col)


def win_of(boxes, margin, aspect=1.0):
    """Bounding window of `boxes` plus a margin, widened (about its
    centre) to at least `aspect` = width / height, so a tall feature
    still makes a readable picture."""
    xs0, ys0, xs1, ys1 = zip(*boxes)
    x0, y0, x1, y1 = (min(xs0) - margin, min(ys0) - margin,
                      max(xs1) + margin, max(ys1) + margin)
    w, h = x1 - x0, y1 - y0
    if w < aspect * h:
        cx = (x0 + x1) / 2
        x0, x1 = cx - aspect * h / 2, cx + aspect * h / 2
    elif h < w / aspect / 3:
        cy = (y0 + y1) / 2
        y0, y1 = cy - w / aspect / 6, cy + w / aspect / 6
    return (x0, y0, x1, y1)


# -------------------------------------------------------------------- steps
def s01(path):
    c = Chip(load(path))
    svg = Svg(c.die, 1600, "Step 1 - wafer.space template: the 1x0p5 pad ring",
              f"die {c.die[2] - c.die[0]:.0f} x {c.die[3] - c.die[1]:.0f} um, core dashed; "
              "pad order from slot_1x0p5.yaml, placed by pad_cfg.tcl (OpenROAD.PadRing)")
    base(c, svg, fill_pads=True, macros=False)
    n = sum(1 for p in c.pads() if p[1] not in ("fill", "cor"))
    svg.text(c.die[0] + (c.die[2] - c.die[0]) / 2, c.die[1] + (c.die[3] - c.die[1]) / 2,
             f"{n} pad cells + corners + fillers; core empty", 16, "middle", color="#5f6368")
    svg.write("01_template_padring")


def s02(path):
    c = Chip(load(path))
    svg = Svg(c.die, 1600, "Step 2 - chip_top.sv / chip_core.sv: what each pad is wired to",
              "pads labelled with the macro pin their net reaches (read back from the synthesised "
              "netlist); straight fly lines = connections the router / drawn wires must make")
    base(c, svg)
    pins = {}
    for i, kind, bb, cell in c.pads():
        if kind in ("fill", "cor", "brk"):
            continue
        sup = supply_label(i, kind)
        if sup:
            pad_label(c, svg, bb, sup, 10, PADC[kind])
            continue
        hits = c.reach(i)
        names = sorted({it.getMTerm().getName() for j, it in hits})
        if not names:
            if kind == "analog":
                pad_label(c, svg, bb, i.getName().replace("\\", "").replace(".pad", "")
                          + ": ANA wired in step 5", 10, "#e8710a")
            else:
                pad_label(c, svg, bb, "(unused)", 9, "#9aa0a6")
            continue
        #- compare_high[0..3] -> compare_high[0..3], not four labels
        short = []
        for n in names:
            base_ = n.split("[")[0].rstrip("_0123456789") if "[" in n else n
            short.append(base_ + "[*]" if "[" in n and sum(1 for m in names if m.startswith(base_ + "[")) > 1 else n)
        short = list(dict.fromkeys(short))
        lab = ", ".join(short[:3]) + (f" +{len(short) - 3}" if len(short) > 3 else "")
        pad_label(c, svg, bb, lab, 10)
        pc = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
        for j, it in hits:
            ok, x, y = it.getAvgXY()
            if not ok:
                continue
            col = "#e8710a" if kind == "analog" else (
                "#1967d2" if j.getMaster().getName() == "wsa_analog_top" else "#137333")
            svg.line(pc[0], pc[1], x / c.u, y / c.u, col, 0.8, 0.55)
            pins[col] = 1
    svg.key("fly line to the digital top", "#137333")
    svg.key("fly line to the analog top (digital control)", "#1967d2")
    svg.key("fly line pad -> analog pin (drawn in step 5)", "#e8710a")
    svg.write("02_chip_top_wiring")


def s04a(path):
    c = Chip(load(path))
    svg = Svg(c.die, 1600, "Step 4a - LibreLane floorplan: macros placed, rows cut, taps",
              "macros.yaml places both hard macros and the five provider ID cells; "
              "FP_OBSTRUCTIONS keep rows out of the drawn-wire channels")
    base(c, svg)
    for r in c.b.getRows():
        svg.rect(c.box(r.getBBox()), fill="#fbbc04", op=0.10)
    svg.key("standard-cell rows", "#fde293")
    svg.write("04a_floorplan_macros")


def s04b(path):
    c = Chip(load(path))
    svg = Svg(c.die, 1600, "Step 4b - power grid (OpenROAD.GeneratePDN + pdn_cfg.tcl)",
              "core ring + Metal4/Metal5 straps; the AVDD/AVSS straps and analog pad wires "
              "are drawn by the two hook scripts inside this step")
    base(c, svg, label_macros=False)
    draw_special(c, svg)
    svg.write("04b_power_grid")


def std_cells(c, svg, clock_red=False):
    n = 0
    for i in c.b.getInsts():
        m = i.getMaster()
        if not m.isCore() or m.isFiller() or m.isEndCap():
            continue
        t = m.getType()
        if "WELLTAP" in t or "SPACER" in t or "ANTENNA" in t:
            continue
        if "fill" in m.getName() or "tap" in m.getName() or "endcap" in m.getName():
            continue
        isclk = clock_red and ("clkbuf" in m.getName() or "clkinv" in m.getName())
        svg.rect(c.box(i.getBBox()), fill="#d93025" if isclk else "#3c4043",
                 minpx=2.2 if isclk else 1.6)
        n += 1
    return n


def s04c(path):
    c = Chip(load(path))
    svg = Svg(c.die, 1600, "Step 4c - placement and clock tree (Yosys netlist, OpenROAD place + CTS)",
              "the chip_core glue cells (pad controls, test-mode muxes, tie cells, buffers), "
              "placed between the pads and the macros")
    base(c, svg)
    n = std_cells(c, svg, clock_red=True)
    svg.key(f"standard cell ({n})", "#3c4043")
    svg.key("clock buffer", "#d93025")
    svg.write("04c_placement_cts")


def s04d(path):
    c = Chip(load(path))
    svg = Svg(c.die, 1600, "Step 4d - detailed routing (OpenROAD.DetailedRouting)",
              "every routed chip-level signal wire, coloured by metal; macros are black boxes "
              "here (their insides come from their own GDS)")
    base(c, svg, label_macros=False)
    draw_special(c, svg, only_analog=True)
    n = 0
    for net in c.b.getNets():
        if net.isSpecial():
            continue
        for layer, x0, y0, x1, y1 in c.wires(net):
            svg.line(x0, y0, x1, y1, METALC.get(layer, "#000"), 0.7, 0.9)
            svg.key(layer, METALC.get(layer, "#000"))
            n += 1
    std_cells(c, svg)
    print(f"render_routed_segments = {n}")
    svg.write("04d_routing")


def analog_nets(c):
    return [n for n in c.b.getNets() if n.isSpecial() and n.getSigType() == "SIGNAL"]


def s05(path, windows):
    c = Chip(load(path))
    #- 5a: the drawn west analog wires
    boxes, nets = [], analog_nets(c)
    for n in nets:
        boxes += [bb for _, bb in c.special_boxes(n)]
    if not boxes:
        print("REPORT: render: no drawn analog wires in the PDN database")
        return False
    win = win_of(boxes, 25, 1.1)
    windows["analog_wires"] = win
    svg = Svg(win, 1600, "Step 5 - analog_routes.tcl: the drawn pad-to-macro analog wires",
              "Metal2 off the pad finger, Via2, Metal3 east, a Metal2 jog in each net's own column, "
              "Metal3 onto the macro's west pin; 1.2 um wide, no buffers, no router")
    base(c, svg, label_macros=False)
    for n in nets:
        for layer, bb in c.special_boxes(n):
            svg.rect(bb, fill=METALC.get(layer, "#000"), op=0.9, minpx=1.5)
            svg.key(f"{layer} (drawn)", METALC.get(layer, "#000"))
        pin = [it for it in n.getITerms() if it.getInst().getMaster().isBlock()]
        if pin:
            ok, x, y = pin[0].getAvgXY()
            if ok:
                svg.text(x / c.u + 3, y / c.u + 2, pin[0].getMTerm().getName(), 13,
                         "start", color="#1967d2", weight="bold")
    for i, kind, bb, cell in c.pads():
        if kind == "analog":
            pad_label(c, svg, bb, i.getName().replace("\\", "") + f" ({cell})", 12, "#e8710a")
    for i, bb in c.macros():
        if i.getMaster().getName() == "wsa_analog_top":
            svg.text(bb[0] + 6, bb[3] - 8, "analog top (west edge)", 13, color="#1967d2")
    svg.write("05a_analog_routes_zoom")
    #- 5b: the drawn supply straps (AVDD / AVSS from the north pads)
    boxes = []
    for n in c.b.getNets():
        if n.getName() == "AVDD":
            boxes += [bb for _, bb in c.special_boxes(n)]
    for i, bb in c.macros():
        if i.getMaster().getName() == "wsa_analog_top":
            boxes.append(bb)
    for i, kind, bb, cell in c.pads():
        if kind == "avdd":
            boxes.append(bb)
    win = win_of(boxes, 30, 0.9)
    windows["supply_straps"] = win
    svg = Svg(win, 1200, "Step 5 - power_routes.tcl: AVDD / AVSS / DVDD / DVSS straps",
              "drawn after pdngen: AVDD from its own north pad (rail-break cells either side), "
              "AVSS from the next pad, DVDD / DVSS up to the core grid")
    base(c, svg, label_macros=True)
    draw_special(c, svg)
    for i, kind, bb, cell in c.pads():
        if kind in ("avdd", "vss", "vdd", "brk"):
            pad_label(c, svg, bb, {"avdd": "AVDD pad", "vss": "VSS/AVSS pad",
                                   "vdd": "VDD pad", "brk": "brk5"}[kind], 11, "#202124")
    svg.write("05b_supply_straps_zoom")
    return True


STEPS = [("01_template_padring", "*-openroad-padring", s01),
         ("02_chip_top_wiring", "*-odb-manualmacroplacement", s02),
         ("04a_floorplan_macros", "*-openroad-tapendcapinsertion", s04a),
         ("04b_power_grid", "*-openroad-generatepdn", s04b),
         ("04c_placement_cts", "*-openroad-cts", s04c),
         ("04d_routing", "*-openroad-detailedrouting", s04d)]


def main():
    os.makedirs(OUT, exist_ok=True)
    missing = 0
    for name, pat, fn in STEPS:
        p = step_odb(pat)
        if p is None:
            print(f"REPORT: render: no database for {name} ({pat})")
            missing += 1
            continue
        fn(p)
    windows = {}
    p = step_odb("*-openroad-generatepdn")
    if p is None or not s05(p, windows):
        missing += 1
    os.makedirs(os.path.join(HERE, "work", "render"), exist_ok=True)
    with open(os.path.join(HERE, "work", "render", "windows.json"), "w") as f:
        json.dump(windows, f, indent=1)
    print(f"render_steps_missing = {missing}")


main()
