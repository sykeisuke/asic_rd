"""intent.py -- the design-intent currents written on the Analog_top drawings
(analog_top.sch, atop_cell.sch, comparator_d.sch, ramp_simple_d.sch,
bias_gen_s.sch), the one source for them; check_intent.py compares them with
the op record (data/op_point.csv) in the op phase.

Bias outputs: bias_gen_s as sized (ADR 0017). icmp_k = 1.68 x the
comparator's design bias I_B (../comparator/intent.py, 1.93 uA): the
factor that keeps its worst untrimmed corner above the comparator's delay
requirement. iramp comes from a sink of the same size, so it equals icmp.

Comparator in the macro: its design currents (the sizing record at 1.93 uA)
scaled to I_B = 3.25 uA: tail 33, pair / loads 16.5 each, starved inverter 16
uA*, output inverter 37 uA* (ngspice; not a sized current), * during tracking
(../comparator/intent.py). The op record sits ~10 % below in the tail
and pair (L 0.28 um channel-length modulation): check_intent.py reports the
deviation and fails only beyond the comparator's sanity bound CMP.TOL.
"""
import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "cmp_intent", os.path.join(_HERE, "..", "comparator", "intent.py"))
CMP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CMP)

TOL = 0.05                       # bias outputs: |op record / intent - 1| allowed (check_intent.py)
CMP_TOL = CMP.TOL                # comparator devices: sanity bound only (design vs ngspice)
K_CMP = 1.68                     # bias_gen_s comparator output / I_B (ADR 0017)

BIAS_UA = {                      # bias_gen_s outputs, design
    "icmp": 3.25,                # sink into each comparator's XREFP = K_CMP x 1.93
    "iramp": 3.25,               # sink into the ramp's XRD (same sink device as icmp)
    "ivref": 11.2,               # source into midref_buf ib (0.90 x its 12.36 uA bench bias)
    "ivrlo": 1.53,               # source into vrlo_ref ib (XOL: 6/44 of ivref)
}
assert abs(BIAS_UA["icmp"] / (K_CMP * CMP.I_B_UA) - 1) < 0.01
assert BIAS_UA["icmp"] == CMP.MACRO_I_B_UA, "the comparator sheet quotes CMP.MACRO_I_B_UA"

CMP_UA = dict(CMP.MACRO_UA)       # the one design allocation: ../comparator/intent.py MACRO_UA

# op_point.csv keys of the bias_gen_s output devices
BIAS_DEV = {"icmp": ["bg_xoc0", "bg_xoc1", "bg_xoc2", "bg_xoc3"], "iramp": ["bg_xor"],
            "ivref": ["bg_xov"], "ivrlo": ["bg_xol"]}


def cmp_marker(dev):
    """The text next to a comparator device on comparator_d.sch (= comparator.sch's)."""
    return CMP.marker(dev)
