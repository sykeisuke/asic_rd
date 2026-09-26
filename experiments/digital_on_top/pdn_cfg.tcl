# Copy of LibreLane's default pdn_cfg.tcl (scripts/openroad/common/pdn_cfg.tcl)
# plus a macro grid for the comparator hard macro: two Metal4 straps laid over
# its vertical Metal3 vdd/vss bars (same technique as the template's SRAM PDN).
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_global_connections.tcl
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

set arg_list [list]
if { $::env(PDN_ENABLE_PINS) } {
    lappend arg_list -pins "$::env(PDN_VERTICAL_LAYER) $::env(PDN_HORIZONTAL_LAYER)"
}
define_pdn_grid -name stdcell_grid -starts_with POWER -voltage_domain CORE {*}$arg_list
set arg_list [list]
append_if_equals arg_list PDN_EXTEND_TO "core_ring" -extend_to_core_ring
append_if_equals arg_list PDN_EXTEND_TO "boundary" -extend_to_boundary
add_pdn_stripe -grid stdcell_grid -layer $::env(PDN_VERTICAL_LAYER) \
    -width $::env(PDN_VWIDTH) -pitch $::env(PDN_VPITCH) -offset $::env(PDN_VOFFSET) \
    -spacing $::env(PDN_VSPACING) -starts_with POWER {*}$arg_list
add_pdn_stripe -grid stdcell_grid -layer $::env(PDN_HORIZONTAL_LAYER) \
    -width $::env(PDN_HWIDTH) -pitch $::env(PDN_HPITCH) -offset $::env(PDN_HOFFSET) \
    -spacing $::env(PDN_HSPACING) -starts_with POWER {*}$arg_list
add_pdn_connect -grid stdcell_grid -layers "$::env(PDN_VERTICAL_LAYER) $::env(PDN_HORIZONTAL_LAYER)"
if { $::env(PDN_ENABLE_RAILS) == 1 } {
    add_pdn_stripe -grid stdcell_grid -layer $::env(PDN_RAIL_LAYER) -width $::env(PDN_RAIL_WIDTH) -followpins
    add_pdn_connect -grid stdcell_grid -layers "$::env(PDN_RAIL_LAYER) $::env(PDN_VERTICAL_LAYER)"
}

# --- comparator hard macro ------------------------------------------------
# LEF pin bars (after ORIGIN): vdd x = 4.09..4.47, vss x = 4.85..5.23 (Metal3,
# vertical). Two 0.44 um Metal4 straps centred on them (-offset is the strap centreline, measured from the macro edge); pdngen drops Via3
# arrays where Metal4 overlaps the Metal3 bars.
define_pdn_grid -macro -instances cmp0 -name cmp_macro -starts_with POWER \
    -halo "$::env(PDN_HORIZONTAL_HALO) $::env(PDN_VERTICAL_HALO)"
add_pdn_stripe -grid cmp_macro -layer Metal4 -width 0.44 -offset 4.28 -pitch 100 -spacing 0.28 \
    -starts_with POWER -number_of_straps 1
add_pdn_stripe -grid cmp_macro -layer Metal4 -width 0.44 -offset 5.04 -pitch 100 -spacing 0.28 \
    -starts_with GROUND -number_of_straps 1
add_pdn_connect -grid cmp_macro -layers "Metal4 Metal3"
add_pdn_connect -grid cmp_macro -layers "$::env(PDN_VERTICAL_LAYER) $::env(PDN_HORIZONTAL_LAYER)"
