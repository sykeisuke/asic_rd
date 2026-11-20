#!/usr/bin/env python3
"""pvt_bench.py -- write one functional bench per PVT cell for the `pvt` phase.

    python3 pvt_bench.py <cell> [<cell> ...]      cell = corner_temp_vdd, e.g. ss_85_3.0

For every cell, work/pvt/<cell>/ gets
  tb.spice        tb_analog_top.spice with the cell's model sections and the
                  two local includes below; nothing else changed
  tb_params.inc   tb_params.inc with VDD set and the LSB grid made ratiometric
  tb_measure.inc  tb_measure.inc with `.save all ...` replaced by the vectors
                  the measures and wrdata use (memory: `.save all` keeps every
                  node of ~650 devices + 344 standard cells), and `.temp`
  .spiceinit      set num_threads=1 (parallel ngspice)
  key             sha256 of the macro, the bench files and the cell: pvt.sh
                  re-uses a finished cell only while its key is unchanged
and prints `<cell> <key>` per line.

Corner convention (as ../vrlo_ref/vr.py): MOS corner = the .lib section;
resistor and MIM corners follow ss / ff (res_ss / mimcap_ss, res_ff /
mimcap_ff) and are typical for typical, sf and fs.

The LSB grid at VDD != 3.3 V: the ramp current is C x (5/33 AVDD) x f
(../ic_source) and the ramp starts at 7/55 AVDD (../vrlo_ref), the reference is
AVDD/2 (../midrail_ref): the converter is ratiometric, so the bench's grid
(LSB_GRID, VR_LO, the input levels at POS_k LSB above VR_LO) scales with
VDD / 3.3. At 3.3 V every number equals tb_params.inc's. With the 3.3 V grid in
volts, a 3.0 V supply would leave the top input above the ramp's end
(count 259 at 0.909 x the slope): a known property of a ratiometric ramp, not
a finding of this bench.
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONT = "/foss/designs/mixed_signal/Analog_top"      # the block inside the container
CORNERS = ("typical", "ss", "ff", "sf", "fs")

# the vectors the measures (tb_measure.inc) and the wrdata line read
NODES = ["avdd", "dvdd", "vin", "acq", "ramp_rst", "cnt_clk", "xdut.pbias0", "xdut.pbias1", "xdut.pbias2",
         "xdut.pbias3", "xdut.pbias_r", "xdut.vmid", "xdut.vref", "xdut.vramp", "xdut.vrlo"]
for k in range(4):
    NODES += ["xdut.xc%d.bot" % k, "xdut.xc%d.top" % k, "xdut.xc%d.dout" % k, "q%d" % k,
              "xdut.s0_%d" % k, "xdut.s1_%d" % k, "xdut.s2_%d" % k,
              # ADR 0031: the four-inverter yardstick and the cell's complements
              "xdut.xseq.xg%d.n1" % k, "xdut.xseq.xg%d.a1" % k, "xdut.xc%d.s0b" % k, "xdut.xc%d.s1b" % k]
CURRENTS = ["vavdd", "vdvdd"] + ["v.xdut.vm%s" % b for b in ("bg", "ref", "vrlo", "ramp", "c0", "c1", "c2", "c3")]
DEVS = ["@m.xdut.xbg.%s.m0[id]" % d for d in ("xoc0", "xoc1", "xoc2", "xoc3", "xor", "xov", "xol", "xmn1")]


def parse(cell):
    c, t, v = cell.split("_")
    if c not in CORNERS:
        raise SystemExit("pvt_bench: unknown corner %s" % c)
    return c, float(t), float(v)


def sub1(text, old, new):
    if text.count(old) != 1:
        raise SystemExit("pvt_bench: expected one %r" % old)
    return text.replace(old, new)


def main(cells):
    tb = open(os.path.join(HERE, "tb_analog_top.spice")).read()
    par = open(os.path.join(HERE, "tb_params.inc")).read()
    mea = open(os.path.join(HERE, "tb_measure.inc")).read()
    mac = open(os.path.join(HERE, "analog_top.spice"), "rb").read()
    for cell in cells:
        c, temp, vdd = parse(cell)
        rc = {"ss": "res_ss", "ff": "res_ff"}.get(c, "res_typical")
        mc = {"ss": "mimcap_ss", "ff": "mimcap_ff"}.get(c, "mimcap_typical")
        d = os.path.join(HERE, "work", "pvt", cell)
        os.makedirs(d, exist_ok=True)
        cd = CONT + "/work/pvt/" + cell
        t = tb
        t = sub1(t, "sm141064.ngspice typical\n", "sm141064.ngspice %s\n" % c)
        t = sub1(t, "sm141064.ngspice res_typical\n", "sm141064.ngspice %s\n" % rc)
        t = sub1(t, "sm141064.ngspice mimcap_typical\n", "sm141064.ngspice %s\n" % mc)
        t = sub1(t, ".include %s/tb_params.inc\n" % CONT, ".include %s/tb_params.inc\n.temp %g\n" % (cd, temp))
        t = sub1(t, ".include %s/tb_measure.inc\n" % CONT, ".include %s/tb_measure.inc\n" % cd)
        p = sub1(par, ".param VDD=3.3\n", ".param VDD=%g\n" % vdd)
        p = sub1(p, ".param LSB_GRID=6.701613m\n", ".param LSB_GRID='6.701613m*VDD/3.3'\n")
        # `.save all @m...` and its `+` continuation lines -> the named vectors
        m = re.sub(r"^\.save all [^\n]*\n(\+[^\n]*\n)*",
                   lambda _: ".save " + " ".join("v(%s)" % n for n in NODES) + "\n.save "
                   + " ".join("i(%s)" % i for i in CURRENTS) + "\n.save " + " ".join(DEVS) + "\n",
                   mea, count=1, flags=re.M)
        if m == mea:
            raise SystemExit("pvt_bench: no .save all line in tb_measure.inc")
        files = {"tb.spice": t, "tb_params.inc": p, "tb_measure.inc": m, ".spiceinit": "set num_threads=1\n"}
        h = hashlib.sha256(mac)
        for name in sorted(files):
            h.update(name.encode())
            h.update(files[name].encode())
        key = h.hexdigest()[:16]
        for name, s in files.items():
            with open(os.path.join(d, name), "w") as f:
                f.write(s)
        with open(os.path.join(d, "key"), "w") as f:
            f.write(key + "\n")
        print(cell, key)


if __name__ == "__main__":
    main(sys.argv[1:])
