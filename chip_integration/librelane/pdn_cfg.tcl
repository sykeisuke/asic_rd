# From wafer-space/gf180mcu-project-template librelane/pdn/pdn_cfg.tcl
# at 0de7e394337a1f7f5303ac7a3681bf2481b58176: core grid, core ring and
# the default macro grid unchanged; the SRAM grids removed (no SRAM),
# and two project scripts hooked around pdngen:
#
#   analog_routes.tcl  BEFORE pdngen: the four west analog pad wires,
#                      drawn as fixed special wiring (ADR 0009 item 4);
#   power_routes.tcl   AFTER pdngen, reading the grid it built: the
#                      AVDD rail break cells, the AVDD/AVSS straps from
#                      the north pads and the analog macro's DVDD/DVSS
#                      straps, and the digital macro's Metal5 hook-up.
#
# Copyright 2025 LibreLane Contributors
# Adapted from OpenLane, Copyright 2020-2022 Efabless Corporation
# Licensed under the Apache License, Version 2.0.

source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_global_connections.tcl

#- LibreLane sources this file inside a proc: anything the hook needs
#- later is kept in a global
set ::ws_pdn_dir [file dirname [file normalize [info script]]]

source [file join $::ws_pdn_dir analog_routes.tcl]

#- pdn.tcl calls `pdngen` right after this file; wrap it once so the
#- power routes run on the finished grid, in the same step and database
if { [info commands ::ws_pdngen_orig] eq "" } {
    rename ::pdngen ::ws_pdngen_orig
    proc ::pdngen {args} {
        ::ws_pdngen_orig {*}$args
        source [file join $::ws_pdn_dir power_routes.tcl]
    }
}

set_global_connections

set secondary []
foreach vdd $::env(VDD_NETS) gnd $::env(GND_NETS) {
    if { $vdd != $::env(VDD_NET)} {
        lappend secondary $vdd
        set db_net [[ord::get_db_block] findNet $vdd]
        if {$db_net == "NULL"} {
            set net [odb::dbNet_create [ord::get_db_block] $vdd]
            $net setSpecial
            $net setSigType "POWER"
        }
    }
    if { $gnd != $::env(GND_NET)} {
        lappend secondary $gnd
        set db_net [[ord::get_db_block] findNet $gnd]
        if {$db_net == "NULL"} {
            set net [odb::dbNet_create [ord::get_db_block] $gnd]
            $net setSpecial
            $net setSigType "GROUND"
        }
    }
}

set_voltage_domain -name CORE -power $::env(VDD_NET) -ground $::env(GND_NET) \
    -secondary_power $secondary

define_pdn_grid \
    -name stdcell_grid \
    -starts_with POWER \
    -voltage_domain CORE

add_pdn_stripe \
    -grid stdcell_grid \
    -layer $::env(PDN_VERTICAL_LAYER) \
    -width $::env(PDN_VWIDTH) \
    -pitch $::env(PDN_VPITCH) \
    -offset $::env(PDN_VOFFSET) \
    -spacing $::env(PDN_VSPACING) \
    -starts_with POWER \
    -extend_to_core_ring

add_pdn_stripe \
    -grid stdcell_grid \
    -layer $::env(PDN_HORIZONTAL_LAYER) \
    -width $::env(PDN_HWIDTH) \
    -pitch $::env(PDN_HPITCH) \
    -offset $::env(PDN_HOFFSET) \
    -spacing $::env(PDN_HSPACING) \
    -starts_with POWER \
    -extend_to_core_ring

add_pdn_connect \
    -grid stdcell_grid \
    -layers "$::env(PDN_VERTICAL_LAYER) $::env(PDN_HORIZONTAL_LAYER)"

add_pdn_stripe \
    -grid stdcell_grid \
    -layer $::env(PDN_RAIL_LAYER) \
    -width $::env(PDN_RAIL_WIDTH) \
    -followpins

add_pdn_connect \
    -grid stdcell_grid \
    -layers "$::env(PDN_RAIL_LAYER) $::env(PDN_VERTICAL_LAYER)"

add_pdn_ring \
    -grid stdcell_grid \
    -layers "$::env(PDN_CORE_VERTICAL_LAYER) $::env(PDN_CORE_HORIZONTAL_LAYER)" \
    -widths "$::env(PDN_CORE_RING_VWIDTH) $::env(PDN_CORE_RING_HWIDTH)" \
    -spacings "$::env(PDN_CORE_RING_VSPACING) $::env(PDN_CORE_RING_HSPACING)" \
    -core_offset "$::env(PDN_CORE_RING_VOFFSET) $::env(PDN_CORE_RING_HOFFSET)" \
    -connect_to_pads \
    -connect_to_pad_layers $::env(PDN_CORE_RING_CONNECT_TO_PAD_LAYERS)

add_pdn_connect \
    -grid stdcell_grid \
    -layers "$::env(PDN_CORE_VERTICAL_LAYER) $::env(PDN_CORE_HORIZONTAL_LAYER)"
add_pdn_connect \
    -grid stdcell_grid \
    -layers "$::env(PDN_CORE_VERTICAL_LAYER) Metal2"
add_pdn_connect \
    -grid stdcell_grid \
    -layers "$::env(PDN_CORE_HORIZONTAL_LAYER) Metal2"

# Macro grid for the digital top only (the template's is -default). The
# analog macro is in no grid: its LEF obstructs Metal1..Metal5 (MIMs on
# Metal4/Metal5), and any macro grid over it stops pdngen (measured:
# PDN-0006 "dvss on Metal4 is blocked by obstructions on Metal5", with
# or without global connections on its pins). The core grid is cut by
# its obstructions; power_routes.tcl wires its supply pins.
define_pdn_grid \
    -macro \
    -instances i_chip_core.u_digital \
    -name macro \
    -starts_with POWER \
    -halo "$::env(PDN_HORIZONTAL_HALO) $::env(PDN_VERTICAL_HALO)"

add_pdn_connect \
    -grid macro \
    -layers "$::env(PDN_VERTICAL_LAYER) $::env(PDN_HORIZONTAL_LAYER)"
