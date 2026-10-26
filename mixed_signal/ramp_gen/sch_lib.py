"""A small library for drawing routed xschem schematics from Python.

Devices are placed at grid points; wires are lists of points (Manhattan
only); nets are named by a label at a wire end. xschem connects wires only at
their end points, so `write()` splits every segment at any wire end point,
instance pin or declared junction lying strictly inside it, and draws a
junction dot wherever three or more segment ends meet.

Pin geometry of the PDK symbols (symbol coordinates, y down):
  nfet_03v3 D (20,-30) G (-20,0) S (20,30) B (20,0)
  pfet_03v3 D (20,30)  G (-20,0) S (20,-30) B (20,0)
  cap_mim_2f0fF   first pin (0,-30), second (0,30)
  ppolyf_u        M (0,30) [first in @pinlist], P (0,-30), B (-20,0)
xschem rotation r (x, y relative to the origin): r=1 -> (-y, x), r=3 -> (y, -x).
"""


class Sheet:
    def __init__(self):
        self.wires, self.inst, self.texts, self.pins, self.junctions = [], [], [], [], []
        self.n = 0

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def par(v):
        v = str(v)
        return '"\\{%s\\}"' % v[1:-1] if v.startswith("{") else v

    @staticmethod
    def rot(px, py, r):
        return {0: (px, py), 1: (-py, px), 2: (-px, -py), 3: (py, -px)}[r]

    def W(self, *pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if x1 != x2 and y1 != y2:
                raise SystemExit("diagonal wire %s -> %s" % ((x1, y1), (x2, y2)))
            self.wires.append((x1, y1, x2, y2))

    def J(self, x, y):
        """a T junction in the middle of a straight wire: split there"""
        self.junctions.append((x, y))

    def T(self, s, x, y, size=0.35, layer=None):
        self.texts.append("T {%s} %d %d 0 0 %.2f %.2f %s" % (
            s, x, y, size, size, "{layer=%d}" % layer if layer is not None else "{}"))

    def lab(self, x, y, net, right=True):
        """net label with its pin at (x, y); text to the right (right=True) or left"""
        self.n += 1
        self.pins.append((x, y))
        self.inst.append("C {devices/lab_pin.sym} %d %d 0 %d {name=l%d sig_type=std_logic lab=%s}"
                         % (x, y, 1 if right else 0, self.n, net))

    def port(self, kind, x, y, net):
        self.inst.append("C {devices/%s.sym} %d %d 0 0 {name=p_%s lab=%s}" % (kind, x, y, net, net))

    # ---------------------------------------------------------------- devices
    def mos(self, kind, name, x, y, L, W, nf, m="1"):
        """returns dict of terminal coordinates d g s b"""
        self.inst.append("C {symbols/%s.sym} %d %d 0 0 {name=%s\nL=%s\nW=%s\nnf=%s\nm=%s\nmodel=%s\n"
                         "spiceprefix=\"\"\nformat=\"@name @pinlist @model L=@L W=@W nf=@nf m=@m\"}"
                         % (kind, x, y, name, self.par(L), self.par(W), self.par(nf), self.par(m), kind))
        dy = -30 if kind == "nfet_03v3" else 30
        t = {"d": (x + 20, y + dy), "g": (x - 20, y), "s": (x + 20, y - dy), "b": (x + 20, y)}
        self.pins += list(t.values())
        return t

    def mim(self, name, x, y, Wc, r=0):
        """returns (first, second) pin coordinates; first = the deck's first terminal"""
        self.inst.append("C {symbols/cap_mim_2f0fF.sym} %d %d %d 0 {name=%s W=%s L=%s "
                         "model=cap_mim_2f0_m4m5_noshield spiceprefix=\"\" m=1}"
                         % (x, y, r, name, self.par(Wc), self.par(Wc)))
        a = self.rot(0, -30, r); b = self.rot(0, 30, r)
        p = ((x + a[0], y + a[1]), (x + b[0], y + b[1]))
        self.pins += list(p)
        return p

    def res(self, name, x, y, W, L, r=0):
        """ppolyf_u; returns (first, second, body) = (M, P, B) coordinates"""
        self.inst.append("C {symbols/ppolyf_u.sym} %d %d %d 0 {name=%s\nW=%s\nL=%s\nmodel=ppolyf_u\n"
                         "spiceprefix=\"\"\nm=1}" % (x, y, r, name, self.par(W), self.par(L)))
        m_ = self.rot(0, 30, r); p_ = self.rot(0, -30, r); b_ = self.rot(-20, 0, r)
        p = ((x + m_[0], y + m_[1]), (x + p_[0], y + p_[1]), (x + b_[0], y + b_[1]))
        self.pins += list(p)
        return p

    # ---------------------------------------------------------------- output
    def write(self, path):
        ends = [(s[0], s[1]) for s in self.wires] + [(s[2], s[3]) for s in self.wires]
        points = ends + self.pins + self.junctions
        segs = []
        for x1, y1, x2, y2 in self.wires:
            cuts = {(x1, y1), (x2, y2)}
            for px, py in points:
                if x1 == x2 == px and min(y1, y2) < py < max(y1, y2):
                    cuts.add((px, py))
                elif y1 == y2 == py and min(x1, x2) < px < max(x1, x2):
                    cuts.add((px, py))
            pts = sorted(cuts)
            segs += [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]
        segs = sorted(set(segs))
        count = {}
        for s in segs:
            for p in ((s[0], s[1]), (s[2], s[3])):
                count[p] = count.get(p, 0) + 1
        out = ["v {xschem version=3.4.8RC file_version=1.2}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        out += ["N %d %d %d %d {}" % s for s in segs]
        out += self.texts + self.inst
        open(path, "w").write("\n".join(out) + "\n")
        return len(segs), sum(1 for c in count.values() if c >= 3)


def ramp_symbol(path, desc, template, label):
    """The pin-compatible ramp symbol both ramps use: ports vramp rst vrlo pbias vdd vss
    (the order of the B 5 lines sets @pinlist, = the subcircuit order)."""
    hdr = "v {xschem version=3.4.8RC file_version=1.2}\nG {}"
    sym = [hdr, 'K {type=subcircuit\nformat="@name @pinlist @symname"\ntemplate="name=%s"\n'
           'description="%s\nPins in the subcircuit order: vramp rst vrlo pbias vdd vss."\n}' % (template, desc),
           "V {}", "S {}", "E {}"]
    for x1, y1, x2, y2 in ((-100, -100, 100, -100), (100, -100, 100, 100), (100, 100, -100, 100),
                           (-100, 100, -100, -100)):
        sym.append("L 4 %d %d %d %d {}" % (x1, y1, x2, y2))
    for line in ("L 7 -50 40 30 -40 {}", "L 7 30 -40 30 40 {}", "L 7 30 40 50 40 {}", "L 7 -70 40 -50 40 {}"):
        sym.append(line)
    sym.append("L 4 100 0 120 0 {}")
    sym.append("B 5 117.5 -2.5 122.5 2.5 {name=vramp dir=out}")
    for p, y in (("rst", 0), ("vrlo", -60), ("pbias", 60)):
        sym.append("L 4 -120 %d -100 %d {}" % (y, y))
        sym.append("B 5 -122.5 %.1f -117.5 %.1f {name=%s dir=in}" % (y - 2.5, y + 2.5, p))
    sym.append("L 4 0 -120 0 -100 {}")
    sym.append("B 5 -2.5 -122.5 2.5 -117.5 {name=vdd dir=inout}")
    sym.append("L 4 0 100 0 120 {}")
    sym.append("B 5 -2.5 117.5 2.5 122.5 {name=vss dir=inout}")
    for p, x, y in (("vramp", 60, -6), ("rst", -94, -6), ("vrlo", -94, -66), ("pbias", -94, 54),
                    ("vdd", 6, -114), ("vss", 6, 104)):
        sym.append("T {%s} %d %d 0 0 0.2 0.2 {}" % (p, x, y))
    sym.append("T {@name} -100 -136 0 0 0.3 0.3 {}")
    sym.append("T {%s} -60 60 0 0 0.22 0.22 {layer=13}" % label)
    open(path, "w").write("\n".join(sym) + "\n")
