"""GF180MCU primitive layout provider for cicpy.

cicpy ships one primitive provider, `cicpy.pdk.sky130`, and
`register_default_providers()` returns without doing anything unless the
techlib name starts with "sky130".  This module is the gf180mcuD
equivalent: it generates a Magic layout for every `nfet_03v3` /
`pfet_03v3` instance in the SPICE netlist by calling the PDK's own
device generator, then gives the resulting cell the four terminal ports
cicpy's router needs.

Two things here are not in the sky130 provider and are the reason this
file exists.

MAGIC'S GF180 DEVICE GENERATOR DOES NOT STRAP ANYTHING.  `gencell
gf180mcu::nfet_03v3 ... nf 4` draws four transistors sharing a diffusion
and five contact columns, and ties none of them together -- extracting
that cell gives four separate devices on four separate nets, not one
device with four fingers.  A primitive handed to cicpy has to present
one rectangle per terminal, so this module adds the straps: the gate
contacts are joined by an M1 bar in the poly-contact band, and the
alternating source/drain columns are joined by two M2 bars running over
the diffusion with a via1 down into each column.  Everything it paints
is checked by `make cicpy-layout`, which runs Magic DRC over the
generated primitives.

UNITS.  Coordinates in a gf180mcuD `.mag` file are 5 nm each (measured:
the gate of a `w=2 l=0.5` device is 100 x 400 file units).  cicpy's
reader computes `file/magscale*100` and gf180 writes `magscale 1 10`, so
one cicpy unit is 0.5 nm here, not 1 A.  That is also why the tech file
uses `gamma: 20`.  `U_PER_UM` and `CIC_PER_FILE` below are the only two
places that conversion is written down.
"""

import json
import logging
import os
import re
import subprocess

from cicpy.pdk.sky130 import PrimitiveLayoutProvider
from cicpy.eda.magicdesign import MagicFile
import cicpy as cic

MAGIC_RC = "/foss/pdks/gf180mcuD/libs.tech/magic/gf180mcuD.magicrc"

#- .mag file units per micrometre, and cicpy units per .mag file unit
U_PER_UM = 200
CIC_PER_FILE = 10

#- gf180mcuD design rules, in .mag file units (micrometre * U_PER_UM)
M1_WIDTH = 46          # M1.1   0.23 um
M1_SPACE = 46          # M1.2a  0.23 um
M2_WIDTH = 56          # M2.1   0.28 um
M2_SPACE = 56          # M2.2a  0.28 um
V1_SIZE = 52           # V1.1   0.26 um
V1_M1_ENC = 8          # V1.3  M1 encloses via1 by 0.04 um; the column
V1_M2_ENC = 8          # V1.4  and the bar are long, so the 0.06 um on two
                       #       opposite sides comes from their own length
V1_WIDE_ENC = 12       # V1.3i/V1.4i 0.06 um, needed on two opposite sides
M2_MIN_AREA = 5776     # M2.3  0.1444 um^2, in (5 nm)^2 units

#- How far Magic's own M1 overhangs a contact tile sideways
M1_STUB = 11

#- MagicPrinter writes `magscale 1 2` and rounds to it, so the finest
#- placement cicpy can express in this technology is 5 file units, 25 nm.
#- A primitive whose bounding box is not a multiple of that puts every
#- instance of it off grid, so the box is rounded outwards.
GRID_FILE = 5

#- Percent of the diffusion the source/drain contact covers.  At the
#- default 100 the contact's M1 cap comes within 0.175 um of the poly
#- contact's M1, so Magic's own device fails M1.2a at L = 0.28 (measured:
#- 9 violations on a w=1.5 l=0.28 nf=2 device, 0 at diffcov 90).  The
#- 10 percent of contact area this costs is worth a DRC-clean primitive.
DIFFCOV = 90

#- Magic insets the source/drain contact from the diffusion edge by this
#- much at each end, so a finger is always taller than its contact.
CONTACT_INSET = 26

#- A device whose finger is too short for two M2 straps plus their
#- spacing cannot be built this way; say so instead of drawing a short.
MIN_FINGER_UNITS = ((2 * (V1_SIZE + 2 * V1_M2_ENC) + M2_SPACE) * 100
                    // DIFFCOV + CONTACT_INSET)


class Gf180PrimitiveError(Exception):
    pass


def _rects(text, section):
    """Every `rect` in one `<< section >>` of a .mag file."""
    m = re.search(r"^<< %s >>$(.*?)^<< " % re.escape(section), text,
                  re.M | re.S)
    if m is None:
        return []
    out = []
    for line in m.group(1).splitlines():
        f = re.match(r"^rect\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*$",
                     line.strip())
        if f:
            out.append(tuple(int(v) for v in f.groups()))
    return out


def _floor(v):
    return (v // GRID_FILE) * GRID_FILE


def _ceil(v):
    return -((-v) // GRID_FILE) * GRID_FILE


def _all_rects(text):
    """Every rectangle the cell draws, checkpaint excluded.

    checkpaint is Magic's own bookkeeping of what still needs checking,
    not geometry, and it is much larger than the cell.
    """
    out, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^<< (\S+) >>$", line)
        if m:
            cur = m.group(1)
            continue
        f = re.match(r"^rect\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*$",
                     line.strip())
        if f and cur not in (None, "checkpaint", "labels", "properties"):
            out.append(tuple(int(v) for v in f.groups()))
    return out


def _columns(rects):
    """Contact rectangles merged into x-sorted columns.

    A contact column is one `rect` per column in every device Magic has
    drawn so far, but merging by overlapping x keeps that from being an
    assumption.
    """
    cols = []
    for x1, y1, x2, y2 in sorted(rects):
        if cols and x1 <= cols[-1][1]:
            c = cols[-1]
            cols[-1] = [min(c[0], x1), max(c[1], x2),
                        min(c[2], y1), max(c[3], y2)]
        else:
            cols.append([x1, x2, y1, y2])
    return cols


class Gf180MagicPrimitiveProvider(PrimitiveLayoutProvider):

    #- The subckt terminal order of the gf180mcuD ngspice devices
    SUPPORTED_PORTS = {
        "nfet_03v3": ["D", "G", "S", "B"],
        "pfet_03v3": ["D", "G", "S", "B"],
    }

    #- (source/drain contact type, guard-ring contact type)
    CONTACTS = {
        "nfet_03v3": ("ndiffc", "psubdiffcont"),
        "pfet_03v3": ("pdiffc", "nsubdiffcont"),
    }

    def __init__(self, techlib="gf180mcuD", magic_rc=MAGIC_RC):
        super().__init__(techlib)
        self.magic_rc = magic_rc
        self.log = logging.getLogger("Gf180Primitive")

    def supports(self, design, subckt_name):
        return (subckt_name in self.SUPPORTED_PORTS
                and os.path.exists(self.magic_rc))

    def canonical_port_order(self, subckt_name):
        return list(self.SUPPORTED_PORTS.get(subckt_name, []))

    # -- parameters -------------------------------------------------

    def _spice_value(self, instance, key, default):
        if not instance.hasProperty(key):
            return default
        v = instance.getPropertyString(key).strip().strip("'\"")
        m = re.match(r"^([-+0-9.eE]+)\s*([a-zA-Z]*)$", v)
        if m is None:
            raise Gf180PrimitiveError(f"cannot read {key}={v}")
        scale = {"": 1.0, "u": 1e-6, "n": 1e-9, "p": 1e-12,
                 "m": 1e-3, "meg": 1e6, "k": 1e3}
        s = m.group(2).lower()
        if s not in scale:
            raise Gf180PrimitiveError(f"unknown suffix in {key}={v}")
        return float(m.group(1)) * scale[s]

    def _params(self, subckt_name, instance):
        """SPICE W/L/nf/m as the micrometre gencell arguments.

        BSIM counts `nf` fingers across the TOTAL width `W`, so the
        width Magic has to draw per finger is W/nf.  Getting this
        backwards makes a device nf times too wide and is invisible
        until LVS.
        """
        w = self._spice_value(instance, "W", 1e-6)
        length = self._spice_value(instance, "L", 0.28e-6)
        nf = int(round(self._spice_value(instance, "nf", 1)))
        m = int(round(self._spice_value(instance, "m", 1)))
        if nf < 1:
            raise Gf180PrimitiveError(f"nf={nf} is not a finger count")
        if m != 1:
            raise Gf180PrimitiveError(
                f"m={m}: the source/drain strap below alternates across "
                f"one device's columns and has not been shown to be "
                f"right across a Magic m-repeat. Write the netlist with "
                f"parallel instances instead.")
        wf_um = w / nf * 1e6
        l_um = length * 1e6
        if wf_um * U_PER_UM < MIN_FINGER_UNITS:
            raise Gf180PrimitiveError(
                f"finger width {wf_um:.3f} um is under the "
                f"{MIN_FINGER_UNITS / U_PER_UM:.3f} um that two M2 "
                f"source/drain straps need; use fewer fingers")
        return wf_um, l_um, nf, m

    def _cell_name(self, subckt_name, wf_um, l_um, nf):
        def tag(v):
            return ("%g" % v).replace(".", "p").replace("-", "m")
        kind = "N" if subckt_name.startswith("n") else "P"
        return f"{kind}FET03V3_W{tag(wf_um)}_L{tag(l_um)}_NF{nf}"

    # -- generation -------------------------------------------------

    def _gencell(self, cache_dir, cell_name, subckt_name,
                 wf_um, l_um, nf, m):
        """Magic draws the device; we name the file.

        `magic::gencell` names the cell it creates itself (a random
        suffix), so the cell is loaded and saved under the name cicpy
        will reference.  A .mag carries no cell name of its own -- the
        file name is the cell name -- so this is a rename, not a copy.
        """
        tcl = "\n".join([
            "crashbackups stop",
            f"magic::gencell gf180mcu::{subckt_name} TMPDEV"
            f" w {wf_um} l {l_um} nf {nf} m {m} diffcov {DIFFCOV}",
            "load [cellname list self] -silent",
            f"save {cell_name}",
            "quit -noprompt",
        ]) + "\n"
        r = subprocess.run(
            ["magic", "-noconsole", "-dnull", "-rcfile", self.magic_rc],
            input=tcl, text=True, cwd=cache_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        path = os.path.join(cache_dir, cell_name + ".mag")
        if not os.path.exists(path):
            raise Gf180PrimitiveError(
                f"magic did not write {cell_name}.mag: {r.stdout[-2000:]}")
        return path

    def _strap(self, path, subckt_name):
        """Tie the gates, and the two alternating source/drain column sets.

        The vertical budget inside Magic's guard ring is what decides
        every number here, so it is worth writing down.  Measured on the
        generator's own output, with the diffusion half-height h:

            h            diffusion edge
            h - 13       source/drain contact end
            h - 2        the contact's own M1 cap
            h + 33 .. 79 the poly contact band
            h + 127..173 the guard ring's top M1 bar

        A via1 is 0.26 um and needs 0.04 um of M1 around it, so any M1
        that takes one is 0.34 um -- 68 units -- tall.  There is no
        68-unit band between the contact caps and the guard ring bar, so
        the guard ring's top and bottom M1 bars are dropped and the gate
        bar takes their room; the ring's left and right contact columns
        still tie the body, through the diffusion ring that joins them.

        Returns the four terminal rectangles in .mag file units as
        (layer, x1, y1, x2, y2).
        """
        sdtype, guardtype = self.CONTACTS[subckt_name]
        text = open(path).read()

        bb = re.search(r"FIXED_BBOX\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)",
                       text)
        if bb is None:
            raise Gf180PrimitiveError(f"{path} has no FIXED_BBOX")
        bx1, by1, bx2, by2 = (int(v) for v in bb.groups())
        #- FIXED_BBOX IS NOT THE CELL'S EXTENT.  Magic writes the box it
        #- intends cells to abut on, and the well runs 0.29 um outside it
        #- on every side; cicpy spaces instances by their box, so two
        #- devices 1 um apart have wells 0.42 um apart and fail NW.2a.
        #- The box published here is everything the cell actually draws.
        for x1, y1, x2, y2 in _all_rects(text):
            bx1, by1 = min(bx1, x1), min(by1, y1)
            bx2, by2 = max(bx2, x2), max(by2, y2)
        bx1, by1 = _floor(bx1), _floor(by1)
        bx2, by2 = _ceil(bx2), _ceil(by2)
        text = text.replace(bb.group(0),
                            "FIXED_BBOX %d %d %d %d" % (bx1, by1, bx2, by2))
        with open(path, "w") as fo:
            fo.write(text)

        cols = _columns(_rects(text, sdtype))
        gate = [r for r in _rects(text, "polycontact") if r[3] > 0]
        guard = _rects(text, guardtype)
        m1 = _rects(text, "metal1")
        if len(cols) < 2 or not gate or not guard:
            raise Gf180PrimitiveError(
                f"{os.path.basename(path)}: expected {sdtype}, polycontact "
                f"and {guardtype} geometry, found "
                f"{len(cols)}/{len(gate)}/{len(guard)} shapes")

        cy1 = max(c[2] for c in cols)
        cy2 = min(c[3] for c in cols)
        gband = min(r[1] for r in gate)
        guard_y2 = max(r[3] for r in guard)
        guard_w = max(r[2] - r[0] for r in guard)
        gl = min(guard, key=lambda r: r[0])
        guard_out1 = gl[0]
        guard_in1 = gl[2]
        guard_in2 = max(guard, key=lambda r: r[2])[0]

        #- DROP the guard ring's top and bottom M1 bars, and nothing
        #- else.  They are the only M1 wider than a contact column that
        #- sits outside the ring's own contacts, and the gate bar needs
        #- their room.  The 0.055 um slivers beside each poly contact
        #- look like scrap and are not: they are what satisfies the
        #- contact's side surround, and dropping them turned a clean
        #- W2/L0.5/nf4 device into 24 violations.
        def _is_ring_bar(r):
            return ((r[1] >= guard_y2 or r[3] <= -guard_y2)
                    and (r[2] - r[0]) > guard_w)
        keep = [r for r in m1 if not _is_ring_bar(r)]
        if len(keep) == len(m1):
            raise Gf180PrimitiveError(
                f"{os.path.basename(path)}: no guard ring M1 bar to drop, "
                f"the generator's geometry is not what this code measured")

        add_m1, add_m2, add_v1 = [], [], []

        #- GATE.  One M1 bar per poly-contact band.  It starts inside
        #- the band so it clears the contact caps below, and the band's
        #- own M1 stubs keep providing the contact's side surround.
        #- as wide as the ring allows, because a bar only as wide as the
        #- poly contacts fails M1.3 minimum area on a one-finger device --
        #- except on the left, where a lane is kept clear for the body
        #- landing below.
        gx1 = guard_in1 + 2 * M1_SPACE
        gx2 = guard_in2 - M1_SPACE
        cap_y2 = cy2 + M1_STUB
        gy1 = max(gband + V1_M1_ENC, cap_y2 + M1_SPACE)
        gy2 = gy1 + V1_SIZE + 2 * V1_M1_ENC
        if gy1 >= max(r[3] for r in gate):
            raise Gf180PrimitiveError(
                "no M1 room between the contact caps and the poly contact")
        if gy2 > by2:
            raise Gf180PrimitiveError("gate bar does not fit in the cell")
        add_m1 += [(gx1, gy1, gx2, gy2), (gx1, -gy2, gx2, -gy1)]

        #- SOURCE / DRAIN.  The two M2 bars stay far enough below the
        #- poly-contact band for the gate's M2 tab to come up between
        #- them and the cell edge.
        bar_h = V1_SIZE + 2 * V1_M2_ENC
        sy2 = min(cy2, gband - V1_SIZE)
        sy1 = sy2 - bar_h
        dy1 = max(cy1, -(gband - V1_SIZE))
        dy2 = dy1 + bar_h
        if sy1 - dy2 < M2_SPACE:
            raise Gf180PrimitiveError(
                f"finger too short: the two M2 straps would be "
                f"{sy1 - dy2} units apart, {M2_SPACE} is the minimum")

        #- The column M1 is one contact wide and a via1 is wider, so
        #- each via gets a pad.  A pad narrower than the column plus two
        #- M1 spacings would leave a notch, so the step is exactly one
        #- spacing on each side.
        pad_half = (guard_w + 2 * M1_SPACE) // 2
        for c in cols:
            cx = (c[0] + c[1]) // 2
            room = min(cx - M1_SPACE - guard_in1,
                       guard_in2 - M1_SPACE - cx)
            pad_half = min(pad_half, room)
        if pad_half < V1_SIZE // 2 + V1_M1_ENC:
            raise Gf180PrimitiveError(
                "no room beside the guard ring for a via1 landing pad")

        term = {}
        for parity, (y1, y2) in ((0, (sy1, sy2)), (1, (dy1, dy2))):
            chosen = [c for i, c in enumerate(cols) if i % 2 == parity]
            if not chosen:
                continue
            #- Source leaves left, drain leaves right, both on their own
            #- bar, so the cell presents them at the boundary instead of
            #- inside a ring the router cannot cross.
            x1 = bx1 if parity == 0 else min(c[0] for c in chosen) - pad_half
            x2 = max(c[1] for c in chosen) + pad_half if parity == 0 else bx2
            add_m2.append((x1, y1, x2, y2))
            term[parity] = ("M2", x1, y1, x2, y2)
            vy1 = (y1 + y2 - V1_SIZE) // 2
            for c in chosen:
                cx = (c[0] + c[1]) // 2
                add_v1.append((cx - V1_SIZE // 2, vy1,
                               cx + V1_SIZE // 2, vy1 + V1_SIZE))
                add_m1.append((cx - pad_half, y1, cx + pad_half, y2))

        #- GATE ESCAPE.  A via1 in the top gate bar and an M2 tab to the
        #- top edge of the cell.
        tab = V1_SIZE // 2 + V1_M2_ENC
        vy = (gy1 + gy2 - V1_SIZE) // 2
        add_v1.append((-V1_SIZE // 2, vy, V1_SIZE // 2, vy + V1_SIZE))
        add_m2.append((-tab, gy1, tab, by2))
        #- the WHOLE tab is the port.  Taking only the part above the
        #- gate bar leaves a landing shorter than M2 minimum width on a
        #- small device, and the route inherits that width (measured:
        #- a 0.20 um M3 branch, M3.1).
        g_rect = ("M2", -tab, gy1, tab, by2)

        #- BULK.  The ring is 0.23 um of M1, narrower than a via1, so the
        #- body has no M2 landing of its own and the router has to bridge
        #- M1 to M2 inside the cell -- which it does not: measured, every
        #- supply net stayed open across five route types, and three of
        #- them added violations.  So the cell brings the body up itself:
        #- the ring is widened in the lane kept clear beside the gate bar,
        #- and one via1 and an M2 tab take it to the edge.
        patch_x2 = guard_in1 + M1_SPACE
        tab_x1 = min(bx1, guard_out1)
        add_m1.append((guard_out1, gy1, patch_x2, gy2))
        #- The via sits where the M1 patch and the M2 tab both have room
        #- to give it the 0.06 um on two opposite sides that V1.3i and
        #- V1.4i want; that is the x direction, so it is centred there.
        pcx = (guard_out1 + patch_x2) // 2
        pcy = (gy1 + gy2) // 2
        if patch_x2 - guard_out1 < V1_SIZE + 2 * V1_WIDE_ENC:
            raise Gf180PrimitiveError("no room for the body via landing")
        add_v1.append((pcx - V1_SIZE // 2, pcy - V1_SIZE // 2,
                       pcx + V1_SIZE // 2, pcy + V1_SIZE // 2))
        #- The tab runs up to the top of the cell: at the gate bar's own
        #- height it is 0.124 um^2 and fails M2.3.
        if (patch_x2 - tab_x1) * (by2 - gy1) < M2_MIN_AREA:
            raise Gf180PrimitiveError(
                "body tab is under the M2.3 minimum area")
        add_m2.append((tab_x1, gy1, patch_x2, by2))
        b_rect = ("M2", tab_x1, gy1, patch_x2, by2)

        self._write(path, keep + add_m1, add_m2, add_v1)

        return {"G": g_rect, "B": b_rect,
                "S": term.get(0, term.get(1)),
                "D": term.get(1, term.get(0))}

    def _write(self, path, m1, m2, v1):
        """Replace the painted metal of a generated primitive.

        A .mag is a list of `<< layer >>` blocks of rectangles, so
        rewriting the metal1 block and adding metal2 and via1 is the
        same edit Magic would make by erasing and painting; it merges
        overlapping tiles on the next read.
        """
        text = open(path).read()
        text = re.sub(r"^<< metal1 >>$.*?(?=^<< )", "", text,
                      count=1, flags=re.M | re.S)
        block = ""
        for layer, rects in (("metal1", m1), ("metal2", m2), ("via1", v1)):
            if not rects:
                continue
            block += f"<< {layer} >>\n"
            for r in rects:
                block += "rect %d %d %d %d\n" % tuple(r)
        i = (text.rindex("<< properties >>") if "<< properties >>" in text
             else text.rindex("<< end >>"))
        with open(path, "w") as fo:
            fo.write(text[:i] + block + text[i:])

    # -- cicpy entry point ------------------------------------------

    def generate(self, design, subckt_name, instance):
        cache_dir = getattr(design, "primitive_cache_dir", "")
        if not cache_dir:
            return None
        os.makedirs(cache_dir, exist_ok=True)

        wf_um, l_um, nf, m = self._params(subckt_name, instance)
        cell_name = self._cell_name(subckt_name, wf_um, l_um, nf)
        path = os.path.join(cache_dir, cell_name + ".mag")

        if cell_name in design.maglib:
            return design.maglib[cell_name].getLayoutCell()

        #- The strap REPLACES the generator's metal, so it can only run
        #- on a file this code just drew.  The terminals it worked out
        #- are written beside the .mag and read back on a rebuild.
        portfile = os.path.join(cache_dir, cell_name + ".ports.json")
        if not os.path.exists(path) or not os.path.exists(portfile):
            self.log.info(f"gencell {cell_name} "
                          f"(w={wf_um} l={l_um} nf={nf})")
            self._gencell(cache_dir, cell_name, subckt_name,
                          wf_um, l_um, nf, m)
            ports = self._strap(path, subckt_name)
            with open(portfile, "w") as fo:
                json.dump(ports, fo, indent=4)
        else:
            with open(portfile) as fi:
                ports = json.load(fi)

        mf = MagicFile(path, design)
        design.maglib[cell_name] = mf
        lcell = mf.getLayoutCell()
        if lcell is None:
            raise Gf180PrimitiveError(f"cicpy could not read {path}")
        lcell.name = cell_name
        lcell.parent = design
        lcell.libpath = cache_dir

        #- MagicFile normalises a library cell to the origin; the port
        #- rectangles were measured on the file, so they move with it.
        sx, sy = getattr(lcell, "libshift", (0, 0))
        for name, r in ports.items():
            if r is None:
                continue
            layer, x1, y1, x2, y2 = r
            #- A PORT IS A LANDING AREA, so it is snapped INWARDS to the
            #- grid cicpy can write.  The metal underneath keeps the
            #- coordinates Magic drew it on; only what the router is
            #- told about moves, and it moves to somewhere the metal
            #- already is.
            gx1 = _ceil((x1 * CIC_PER_FILE - sx) // CIC_PER_FILE)
            gy1 = _ceil((y1 * CIC_PER_FILE - sy) // CIC_PER_FILE)
            gx2 = _floor((x2 * CIC_PER_FILE - sx) // CIC_PER_FILE)
            gy2 = _floor((y2 * CIC_PER_FILE - sy) // CIC_PER_FILE)
            if gx2 <= gx1 or gy2 <= gy1:
                raise Gf180PrimitiveError(
                    f"port {name} is smaller than the "
                    f"{GRID_FILE * 5} nm grid cicpy can write")
            rect = cic.Rect(layer)
            rect.setPoint1(gx1 * CIC_PER_FILE, gy1 * CIC_PER_FILE)
            rect.setPoint2(gx2 * CIC_PER_FILE, gy2 * CIC_PER_FILE)
            #- NOT updatePort: it only creates a port when the cell has a
            #- subckt naming it, and a cell read from a .mag has none, so
            #- it returns having done nothing and the device comes out
            #- with no terminals at all.  This is what the magic reader
            #- does for an flabel.
            lcell.add(cic.Port(name, routeLayer=layer, rect=rect))
        return lcell


def tie_body(layout):
    """Join a device's body to its own source or drain where the netlist
    says they are one net.

    Only the netlist knows: `XTAIL tail vbias vss vss` ties them, and
    `XINP left vin tail vss` must not, so the primitive cannot decide and
    the router will not -- `addConnectivityRoute` matched nothing when a
    net's only two rectangles were in the same instance, and every route
    type left the supply nets in three pieces.

    Both terminals are M2 at the left of the cell, one above the other,
    so the tie is one rectangle over their shared x.
    """
    tied = 0
    for inst in list(layout.children):
        ckt = getattr(inst, "subcktInstance", None)
        if ckt is None or len(getattr(ckt, "nodes", [])) != 4:
            continue
        ports = {}
        for child in inst.children:
            name = getattr(child, "childName", None)
            if name:
                ports[name] = child
        #- nodes are d g s b, the order canonical_port_order publishes
        partner = {2: "S", 0: "D"}
        pin = next((partner[i] for i in (2, 0)
                    if ckt.nodes[i] == ckt.nodes[3]), None)
        if pin is None or pin not in ports or "B" not in ports:
            continue
        a, b = ports[pin], ports["B"]
        x1, x2 = max(a.x1, b.x1), min(a.x2, b.x2)
        if x2 <= x1:
            log = logging.getLogger("Gf180Primitive")
            log.warning(f"{inst.instanceName}: {pin} and B do not overlap "
                        f"in x, body left to the router")
            continue
        r = cic.Rect("M2")
        r.setPoint1(x1, min(a.y1, b.y1))
        r.setPoint2(x2, max(a.y2, b.y2))
        r.net = ckt.nodes[3]
        layout.add(r)
        tied += 1
    logging.getLogger("Gf180Primitive").info(
        f"tie_body: {tied} device bodies tied to their own terminal")
    return tied


def patch_magic_scale():
    """Make cicpy's Magic writer use the gf180mcuD grid.

    MagicPrinter writes `magscale 1 2` and rounds coordinates to
    `angstrom/50`.  Both numbers are the sky130 scale.  In gf180mcuD one
    Magic internal unit is 5 nm and cicpy's reader always returns
    internal*10, so `/50` quantises everything cicpy writes to 25 nm --
    which cannot express a 0.26 um via1 (V1.1) at all: it comes out
    0.25 um and fails minimum width.

    Writing `magscale 1 10` and rounding to `angstrom/10` makes one
    written unit one internal unit, so the output lands exactly on the
    5 nm manufacturing grid and a 0.26 um via is 0.26 um.

    This is a patch to a pinned tool, so it is narrow, idempotent, and
    announces itself in the log.
    """
    from cicpy.printer.magicprinter import MagicPrinter
    if getattr(MagicPrinter, "_gf180_scale", False):
        return
    MagicPrinter.toMicron = lambda self, angstrom: int(
        round(angstrom / CIC_PER_FILE))
    _open = MagicPrinter.openCellFile

    def openCellFile(self, filename):
        _open(self, filename)
        write = self.fcell.write

        def scaled(text):
            return write(text.replace("magscale 1 2\n", "magscale 1 10\n"))
        self.fcell.write = scaled

    MagicPrinter.openCellFile = openCellFile
    MagicPrinter._gf180_scale = True
    logging.getLogger("Gf180Primitive").info(
        "MagicPrinter rescaled to the gf180mcuD 5 nm grid")


def register(design):
    """Register the gf180 provider on a MagicDesign.

    cicpy's own `register_default_providers` returns early for any
    techlib that is not sky130, so a pycell calls this from
    `beforePlace`: providers are consulted by `LayoutCell.addInstance`,
    which runs inside `place()`, after that hook.
    """
    for p in getattr(design, "primitiveProviders", []):
        if isinstance(p, Gf180MagicPrimitiveProvider):
            return p
    patch_magic_scale()
    p = Gf180MagicPrimitiveProvider()
    design.registerPrimitiveProvider(p)
    return p
