"""Probe: DRC-check individual gf180mcu plugin cells in isolation."""
import sys, gdsfactory as gf, gf180mcu
PDK = gf180mcu.PDK; PDK.activate()
which = sys.argv[1] if len(sys.argv) > 1 else "cap"
if which == "cap":
    c = PDK.get_component("cap_mim", mim_option="B", metal_level="M4", lc=22.4, wc=22.4)
elif which == "capA":
    c = PDK.get_component("cap_mim", mim_option="A", metal_level="M4", lc=22.4, wc=22.4)
elif which == "nfet":
    c = PDK.get_component("nfet", l_gate=0.28, w_gate=2.0, volt="3.3V", bulk="Bulk Tie")
elif which == "pfet":
    c = PDK.get_component("pfet", l_gate=0.28, w_gate=4.0, volt="3.3V", bulk="Bulk Tie")
if which in ("cap","capA","nfet","pfet"):
    c.write_gds(f"work/probe_{which}.gds"); print("wrote", f"work/probe_{which}.gds")
if which == "capM5":
    c = PDK.get_component("cap_mim", mim_option="B", metal_level="M5", lc=22.4, wc=22.4)
    c.write_gds("work/probe_capM5.gds"); print("wrote")
elif which == "capM3":
    c = PDK.get_component("cap_mim", mim_option="B", metal_level="M3", lc=22.4, wc=22.4)
    c.write_gds("work/probe_capM3.gds"); print("wrote")
elif which == "nfet_nobulk":
    c = PDK.get_component("nfet", l_gate=0.28, w_gate=2.0, volt="3.3V", bulk="None")
    c.write_gds("work/probe_nfet_nobulk.gds"); print("wrote")
if which == "rst":
    from fet_fix import nfet_fixed
    c = nfet_fixed(w_gate=1.0, l_gate=0.5, nf=5, gate_side="top")
    c.write_gds("work/probe_rst.gds"); print("wrote", dict(c.info))
