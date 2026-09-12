"""MIM-B capacitor for gf180mcuD (5LM, 11K top metal), drawn from layers.

Why: the gf180mcu plugin's cap_mim is MIM-A only (Metal2/Metal3/via2) and fails
the Run 3 DRC deck in a MIM-B process. In MIM-B the capacitor sits between
Metal4 (bottom plate) and Metal5 (top-plate terminal), with the FuseTop layer as
the top-plate electrode and Via4 as the only via allowed on the structure.

Rules implemented (GF180 DRM 10.4.2, deck mim_b.rb):
  MIMTM.1  Metal4 (bottom plate) to other Metal4 >= 1.2 um
  MIMTM.2  Metal4 encloses every Via4 near the cap by >= 0.4 um
  MIMTM.3  bottom plate (Metal4) encloses FuseTop by >= 0.6 um
  MIMTM.4  FuseTop encloses its Via4 by >= 0.4 um
  MIMTM.5  FuseTop to Via4 that lands on the bottom plate >= 0.4 um
  MIMTM.6  FuseTop to unrelated FuseTop >= 0.6 um
  MIMTM.7  CAP_MK marker encloses FuseTop (>= 0)
  MIMTM.8  25 um^2 <= FuseTop area <= 10,000 um^2
  MIMTM.9  Via4 on FuseTop spaced >= 0.5 um
  MIMTM.10 no Via3 may touch the bottom plate (connect it only upward via Via4)
Layer numbers and via4/metal rule values live in the CONFIG block below.

Run: experiments/analog_layout/run.sh experiments/analog_layout/mim_cap.py mim_cap
"""
import gdsfactory as gf
import gf180mcu

gf180mcu.PDK.activate()   # the container exports PDK=gf180mcuD, which gdsfactory would try to import

# ---------------- CONFIG (from the frozen PDK's gf180mcu.map / rule decks) -----------
LAYER = {
    "metal4": (46, 0), "via4": (41, 0), "metal5": (81, 0),
    "fusetop": (75, 0), "cap_mk": (117, 5),          # cap_mk: verify from map
}
VIA4_SIZE = 0.26          # um, V4 min size (verify)
VIA4_SPACE_PLATE = 0.50   # MIMTM.9 on FuseTop
VIA4_SPACE = 0.26         # generic via4 spacing (verify)
M5_ENC_VIA = 0.06         # Metal5 enclosure of Via4 (verify)
M5_MIN_W = 0.44           # MT.1 for 11K top metal
M5_MIN_S = 0.46           # MT.2a for 11K top metal
M4_ENC_VIA_CAP = 0.40     # MIMTM.2
BOT_OVER_TOP = 0.60       # MIMTM.3
FUSE_ENC_VIA = 0.40       # MIMTM.4
FUSE_TO_BOTVIA = 0.40     # MIMTM.5
CAP_DENSITY_FF_UM2 = 2.0  # approximate MIM-B density; calibrate against the PDK model

def _via_array(c, layer, x0, y0, x1, y1, size, space):
    """Fill the box (x0,y0)-(x1,y1) with a square via array; return count."""
    pitch = size + space
    eps = 1e-6
    nx = int((x1 - x0 - size + eps) // pitch) + 1
    ny = int((y1 - y0 - size + eps) // pitch) + 1
    if nx < 1 or ny < 1:
        return 0
    ax = (x1 - x0 - ((nx - 1) * pitch + size)) / 2  # center the array
    ay = (y1 - y0 - ((ny - 1) * pitch + size)) / 2
    for i in range(nx):
        for j in range(ny):
            xa = x0 + ax + i * pitch; ya = y0 + ay + j * pitch
            c.add_polygon([(xa, ya), (xa + size, ya), (xa + size, ya + size), (xa, ya + size)], layer=layer)
    return nx * ny

@gf.cell
def mim_cap_b(w: float = 22.4, l: float = 22.4, term_w: float = 1.0) -> gf.Component:
    """MIM-B capacitor. w x l is the FuseTop (top plate) size in um.
    Ports: 'top' (Metal5, right) and 'bot' (Metal5, left)."""
    c = gf.Component()
    M4, V4, M5, FT, MK = (LAYER[k] for k in ("metal4", "via4", "metal5", "fusetop", "cap_mk"))
    rect = lambda layer, x0, y0, x1, y1: c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)

    # Top plate (FuseTop) centered at origin; marker layer encloses it.
    rect(FT, -w/2, -l/2, w/2, l/2)
    rect(MK, -w/2, -l/2, w/2, l/2)

    # Bottom plate (Metal4): encloses FuseTop by BOT_OVER_TOP, extended to the left
    # to host the bottom-plate Via4 column at >= FUSE_TO_BOTVIA from FuseTop.
    n_bot_cols = 2
    bot_col_w = n_bot_cols * VIA4_SIZE + (n_bot_cols - 1) * VIA4_SPACE_PLATE + 2 * M4_ENC_VIA_CAP
    bx0 = -w/2 - FUSE_TO_BOTVIA - bot_col_w
    rect(M4, bx0, -l/2 - BOT_OVER_TOP, w/2 + BOT_OVER_TOP, l/2 + BOT_OVER_TOP)

    # Via4 sea on the top plate (inset FUSE_ENC_VIA, spacing MIMTM.9) + Metal5 top terminal.
    n_top = _via_array(c, V4, -w/2 + FUSE_ENC_VIA, -l/2 + FUSE_ENC_VIA, w/2 - FUSE_ENC_VIA, l/2 - FUSE_ENC_VIA,
                       VIA4_SIZE, VIA4_SPACE_PLATE)
    rect(M5, -w/2 + FUSE_ENC_VIA - M5_ENC_VIA, -l/2 + FUSE_ENC_VIA - M5_ENC_VIA,
             w/2 - FUSE_ENC_VIA + M5_ENC_VIA,  l/2 - FUSE_ENC_VIA + M5_ENC_VIA)
    # top terminal stub to the right edge of the cell
    rect(M5, w/2 - FUSE_ENC_VIA, -term_w/2, w/2 + BOT_OVER_TOP + 0.5, term_w/2)

    # Bottom-plate Via4 column (left), Metal4-enclosed, and its Metal5 terminal.
    vx0 = bx0 + M4_ENC_VIA_CAP; vx1 = bx0 + bot_col_w - M4_ENC_VIA_CAP
    vy0 = -l/2 - BOT_OVER_TOP + M4_ENC_VIA_CAP; vy1 = l/2 + BOT_OVER_TOP - M4_ENC_VIA_CAP
    n_bot = _via_array(c, V4, vx0, vy0, vx1, vy1, VIA4_SIZE, VIA4_SPACE_PLATE)
    rect(M5, vx0 - M5_ENC_VIA - 0.2, vy0 - M5_ENC_VIA, vx1 + M5_ENC_VIA, vy1 + M5_ENC_VIA)
    rect(M5, bx0 - 0.5, -term_w/2, vx1 + M5_ENC_VIA, term_w/2)

    c.add_port("top", center=(w/2 + BOT_OVER_TOP + 0.5, 0), width=term_w, orientation=0, layer=M5)
    c.add_port("bot", center=(bx0 - 0.5, 0), width=term_w, orientation=180, layer=M5)
    c.info.update(dict(fusetop_area_um2=w*l, cap_fF_est=w*l*CAP_DENSITY_FF_UM2, n_via_top=n_top, n_via_bot=n_bot))
    return c

if __name__ == "__main__":
    cap = mim_cap_b()
    b = cap.dbbox()
    print(f"mim_cap_b: FuseTop {cap.info['fusetop_area_um2']:.0f} um^2 ≈ {cap.info['cap_fF_est']/1000:.2f} pF (est.), "
          f"cell {b.width():.1f} x {b.height():.1f} um, vias top/bot {cap.info['n_via_top']}/{cap.info['n_via_bot']}")
    cap.write_gds("work/mim_cap.gds"); print("wrote work/mim_cap.gds")
