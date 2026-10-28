"""Inspect the GF180 3.3 V BSIM4 model sections before converting them.

    ./container.sh 'python3 vacask_lib/inspect_models.py'

Prints, for each corner section of nfet_03v3 / pfet_03v3: the bin windows
(lmin/lmax/wmin/wmax), how many parameters each bin carries, every parameter
value that is not a plain number (those need a `parameters` line on the
VACASK side), and the set of parameter names -- so the converter can be
checked against the OSDI module's parameter list before anything is trusted.
"""
import re
import sys

PDK = "/foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.spice"
NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")


def sections(path):
    cur = None
    body = {}
    with open(path) as f:
        for line in f:
            s = line.rstrip("\n")
            m = re.match(r"^\.lib\s+(\S+)\s*$", s)
            if m:
                cur = m.group(1)
                body[cur] = []
                continue
            if re.match(r"^\.endl", s):
                cur = None
                continue
            if cur is not None:
                body[cur].append(s)
    return body


def models(lines):
    out = []
    cur = None
    for s in lines:
        m = re.match(r"^\.model\s+(\S+)\s+(\S+)", s)
        if m:
            cur = dict(name=m.group(1), type=m.group(2), params=[])
            out.append(cur)
            continue
        if cur is not None and s.startswith("+"):
            for tok in s[1:].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    cur["params"].append((k.lower(), v))
        elif cur is not None and not s.startswith("+"):
            cur = None
    return out


def main():
    body = sections(PDK)
    names = set()
    for dev in ("nfet_03v3", "pfet_03v3"):
        for corner in ("t", "f", "s", "fs", "sf"):
            sec = f"{dev}_{corner}"
            ms = models(body[sec])
            print(f"section {sec}: {len(ms)} bins")
            for m in ms:
                p = dict(m["params"])
                nonnum = sorted(k for k, v in m["params"] if not NUM.match(v))
                if corner == "t":
                    print(f"  {m['name']:14s} {m['type']} L[{p.get('lmin')},{p.get('lmax')}] "
                          f"W[{p.get('wmin')},{p.get('wmax')}] nparams={len(m['params'])} "
                          f"nonnum={nonnum}")
                names.update(k for k, _ in m["params"])
        # the wrapper subckt and any .param in the section
        extra = [s for s in body[f"{dev}_t"] if s.startswith(".param") or s.startswith(".subckt") or s.startswith("x") or s.startswith("m")]
        print(f"  non-model lines in {dev}_t: {len(extra)}")
        for s in extra[:20]:
            print("   ", s[:140])
    print(f"distinct parameter names across both devices: {len(names)}")
    print(" ".join(sorted(names)))
    nc = [s for s in body["noise_corner"] if "03v3" in s]
    print("noise_corner 03v3 lines:")
    for s in nc:
        print("   ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
