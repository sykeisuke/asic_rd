"""Shared by ct_bench.py, ct_extract.py and ct_reduce.py: tb_params.inc evaluated
in order, with overrides, and the record and clock-edge times derived from it.
(Adapted from ../cell_trannoise_bkp/cell_trannoise/tn_common.py: whole-count records, no phase walk.)"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS = os.path.join(HERE, "tb_params.inc")
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9, "t": 1e12}
NUM = r"(?<![\w.])((?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(meg|[fpnumkgt])(?![\w])"


def num(tok):
    m = re.match(r"^([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)(meg|[fpnumkgt])?$", tok.strip(), re.I)
    if not m:
        return None
    return float(m.group(1)) * SI.get((m.group(2) or "").lower(), 1.0)


def evaluate(expr, env):
    """A SPICE expression (suffixes, **, floor/ceil/min/max, names from env) -> float."""
    s = expr.strip().strip("{}'\"")
    v = num(s)
    if v is not None:
        return v
    s = re.sub(NUM, lambda q: repr(float(q.group(1)) * SI[q.group(2).lower()]), s, flags=re.I)

    def name(q):
        k = q.group(1)
        if k.lower() in ("floor", "ceil", "int", "abs", "sqrt", "min", "max"):
            return k.lower()
        if k.upper() not in env:
            raise KeyError("unknown parameter %r in %r" % (k, expr))
        return "env[%r]" % k.upper()
    s = re.sub(r"\b([A-Za-z_]\w*)\b", name, s)
    fns = {"floor": math.floor, "ceil": math.ceil, "int": int, "abs": abs, "sqrt": math.sqrt,
           "min": min, "max": max}
    return float(eval(s, {"__builtins__": {}, "env": env, **fns}))


def load_params(overrides=None, path=PARAMS):
    """Evaluate the .param lines in order; an override replaces a line's value
    where that line is (so everything after it follows)."""
    overrides = {k.upper(): float(v) for k, v in (overrides or {}).items()}
    env = {}
    for line in open(path):
        m = re.match(r"^\.param\s+(\w+)\s*=\s*(.+?)\s*$", line.strip(), re.I)
        if not m:
            continue
        k = m.group(1).upper()
        env[k] = overrides[k] if k in overrides else evaluate(m.group(2), env)
    unknown = set(overrides) - set(env)
    if unknown:
        raise KeyError("override of unknown parameters %s" % sorted(unknown))
    return env


def overrides_from(argv):
    out = {}
    for a in argv:
        k, v = a.split("=", 1)
        out[k] = num(v) if num(v) is not None else float(v)
    return out


def records(P):
    """[(n, t0, TR, TE, t_ideal)] for every record."""
    out = []
    for n in range(int(round(P["NREC"]))):
        t0 = P["TFIRST"] + n * P["PCONV"]
        tr = t0 + P["TRREL"]
        te = tr + P["NCNT"] * P["TCOUNT"]
        out.append((n, t0, tr, te, tr + (P["VIN"] - P["VR_LO"]) / P["SLOPE"]))
    return out


def fall_edge(P, k):
    """Midpoint of the k-th falling count-clock edge after TR, relative to TR
    (the clock rises at TR, falls TCOUNT/2 later; edges are TEDGE long)."""
    return P["TCOUNT"] / 2 + P["TEDGE"] / 2 + k * P["TCOUNT"]
