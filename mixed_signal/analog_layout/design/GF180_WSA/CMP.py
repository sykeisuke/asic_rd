"""Layout intent for CMP, the comparator of simulations/gf180_comparator.

A classic cicpy pycell: module-level hooks plus `data`.  Its only job
here is to put the gf180mcuD primitive provider on the design before
anything is placed -- cicpy.pdk.register_default_providers returns
without doing anything for a techlib that is not sky130, and providers
are consulted by LayoutCell.addInstance, which runs inside place().
"""

from cicpy_gf180 import register, tie_body

data = {}


#- Space between placed devices, in cicpy units (2000 = 1 um here; see
#- the unit note in tech/cic/gf180mcuD.tech).  The default is 0, which
#- abuts the guard rings of an NMOS and a PMOS -- every device carries
#- its own well and body tie, so they have to stand apart.
#-
#- 1.5 um, not the 0.6 um of NW.2a: that rule is for wells at EQUAL
#- potential, and nothing proves these are until the supply is routed.
#- KLayout applies NW.2b instead, 1.4 um for different potential, and
#- said so twice on CMP at 1.02 um.
PLACE_SPACE = 3000


def beforePlace(layout):
    register(layout.parent)
    layout.place_xspace = [PLACE_SPACE]
    layout.place_yspace = [PLACE_SPACE]
    #- No supply ring: the devices carry their own body ties and the
    #- two nets that would use a ring are the cell's ports.
    layout.noPowerRoute = True


def beforeRoute(layout):
    tie_body(layout)
    #- SIGNAL ROUTING IS NOT DONE.  The nine devices sit in one row and
    #- the straight connectivity routes cross: measured, M3 alone shorts
    #- outa to vss, left to outa and tail to vss, and splitting the nets
    #- over M3/M4/M5 still leaves two shorts and adds six violations.
    #- A cell this size wants a floorplan -- rows, channels and named
    #- corridors, which is what cicpy's SidecarCell exists for -- not a
    #- straight route per net.  Until that exists this cell is placed,
    #- body-tied and DRC clean, and its LVS says so.
