"""Sandbox: transmission-gate sampling cell layout with gdsfactory + gf180mcu.

Exploration branch keisuke/analog-explore (not for main until reviewed).
Devices follow the Tape-out 1 baseline: 3.3 V TG switch (NMOS + PMOS),
1 pF MIM hold capacitor. Placement only for now; routing is the next step.

Run inside the pinned container:  experiments/analog_layout/run.sh experiments/analog_layout/sampling_cell.py
"""
import gdsfactory as gf
import gf180mcu
from mim_cap import mim_cap_b

PDK = gf180mcu.PDK
PDK.activate()

# --- device sizing (edit freely) -------------------------------------------
L_GATE = 0.28          # um, minimum for 3.3 V devices
W_NMOS = 2.0           # um
W_PMOS = 4.0           # um, ~2x NMOS for balanced TG on-resistance
MIM_OPTION = "B"       # gf180mcuD = MIM option B (Metal4/FuseTop/Metal5); see mim_cap.py
MIM_SIDE = 22.4        # um; ~2 fF/um^2 -> 22.4^2 * 2 fF ≈ 1.0 pF (check DRM value)


@gf.cell
def sampling_cell_tg(w_nmos: float = W_NMOS, w_pmos: float = W_PMOS,
                     mim_side: float = MIM_SIDE, l_gate: float = L_GATE) -> gf.Component:
    """Parametric TG sampling cell. gdsfactory caches one layout per distinct
    argument set and derives a unique cell name from the arguments."""
    c = gf.Component()

    nmos = c << PDK.get_component("nfet", l_gate=l_gate, w_gate=w_nmos,
                                  volt="3.3V", bulk="Bulk Tie")
    pmos = c << PDK.get_component("pfet", l_gate=l_gate, w_gate=w_pmos,
                                  volt="3.3V", bulk="Bulk Tie")
    # Layer-drawn MIM-B cap (Metal4 / FuseTop / Via4 / Metal5): the plugin's cap_mim
    # is MIM-A only and fails the gf180mcuD deck. See mim_cap.py.
    chold = c << mim_cap_b(w=mim_side, l=mim_side)

    # Coarse placement: TG devices side by side, hold cap to the right.
    pmos.dmovex(nmos.dxmax - pmos.dxmin + 2.0)
    chold.dmovex(pmos.dxmax - chold.dxmin + 3.0)
    chold.dmovey(nmos.dymin - chold.dymin)

    c.info["w_nmos_um"] = w_nmos
    c.info["w_pmos_um"] = w_pmos
    c.info["mim_side_um"] = mim_side
    return c


if __name__ == "__main__":
    comp = sampling_cell_tg()
    out = "work/sampling_cell_tg.gds"
    comp.write_gds(out)
    bb = comp.dbbox()
    print(f"wrote {out}")
    print(f"bbox: {bb.width():.2f} x {bb.height():.2f} um")
    print("ports:", [p.name for p in comp.ports])
