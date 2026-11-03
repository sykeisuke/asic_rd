# LibreLane 3.1.0.dev2 scripts/openroad/common/pad_cfg.tcl, copied
# unchanged except for the blocks marked "project change" (AVDD rail
# break cells); used through PAD_CFG in config.yaml.
#
# Copyright 2025 LibreLane Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

source $::env(SCRIPTS_DIR)/openroad/common/set_global_connections.tcl
set_global_connections

puts "\[INFO\] Generating padring…"

set block [ord::get_db_block]
set units [$block getDefUnits]

# Round a micrometer value to nanometer
proc round_um_nm {value} {
    return [expr double(round($value * 1000)) / 1000]
}

# Pad Placement Algorithm
#
# For all sides:
#
# 1. Sum up all pad widths for the side
# 2. If that value is larger than the side, throw an error
# 3. Subtract that value from the side width
# 4. Divide this value with the number of pads for this side + 1
# 5. Round this value to the minimum site width (this is the spacing between pads)
# 6. Multiply this value with the number of pads for this side minus one, subtract this value from the side width
# 7. Divide this value by two, this is the spacing from pads to corners
# 8. Throw an error if this spacing is not a multiple of the minimum site width

set DIE_HEIGHT [expr {[lindex $::env(DIE_AREA) 3] - [lindex $::env(DIE_AREA) 1]}]
set DIE_WIDTH [expr {[lindex $::env(DIE_AREA) 2] - [lindex $::env(DIE_AREA) 0]}]

# Get pad and corner site
set pad_site [pad::find_site $::env(PAD_SITE_NAME)]
set pad_corner_site [pad::find_site $::env(PAD_CORNER_SITE_NAME)]

if { $pad_site == "NULL" } {
    puts stderr "\[ERROR\] No pad site $::env(PAD_SITE_NAME) found."
    exit 1
}

if { $pad_corner_site == "NULL" } {
    puts stderr "\[ERROR\] No pad corner site $::env(PAD_CORNER_SITE_NAME) found."
    exit 1
}

if { [$pad_site getClass] != "PAD" } {
    puts stderr "\[ERROR\] Wrong class for pad site $::env(PAD_SITE_NAME): [$pad_site getClass] (expected PAD)."
    exit 1
}

if { [$pad_corner_site getClass] != "PAD" } {
    puts stderr "\[ERROR\] Wrong class for pad corner site $::env(PAD_CORNER_SITE_NAME): [$pad_corner_site getClass] (expected PAD)."
    exit 1
}

set pad_site_width [expr double([$pad_site getWidth]) / $units]
set pad_site_height [expr double([$pad_site getHeight]) / $units]

set pad_corner_site_width [expr double([$pad_corner_site getWidth]) / $units]
set pad_corner_site_height [expr double([$pad_corner_site getHeight]) / $units]

puts "\[INFO\] $::env(PAD_SITE_NAME): $pad_site_width μm by $pad_site_height μm"
puts "\[INFO\] $::env(PAD_CORNER_SITE_NAME): $pad_corner_site_width μm by $pad_corner_site_height μm"

# Make IO sites
make_io_sites \
    -horizontal_site $::env(PAD_SITE_NAME) \
    -vertical_site $::env(PAD_SITE_NAME) \
    -corner_site $::env(PAD_CORNER_SITE_NAME) \
    -offset $::env(PAD_EDGE_SPACING) \
    -rotation_horizontal $::env(PAD_ROTATION_HORIZONTAL) \
    -rotation_vertical $::env(PAD_ROTATION_VERTICAL) \
    -rotation_corner $::env(PAD_ROTATION_CORNER)

set sides {PAD_SOUTH PAD_EAST PAD_NORTH PAD_WEST}
set vertical_sides [list PAD_EAST PAD_WEST]
set horizontal_sides [list PAD_SOUTH PAD_NORTH]
set row_names [dict create PAD_SOUTH IO_SOUTH PAD_EAST IO_EAST PAD_NORTH IO_NORTH PAD_WEST IO_WEST]

foreach side $sides {
    puts "Placing pads for $side…"
    set sum_of_cell_widths 0
    
    foreach inst_name $::env($side) {
        if { [set inst [$block findInst $inst_name]] == "NULL" } {
            puts stderr "\[ERROR\] No instance $inst_name found."
            exit 1
        }
        set master_name [[$inst getMaster] getName]
        
        # Convert to micrometer
        set width  [expr [[$inst getMaster] getWidth] / $units]
        set height [expr [[$inst getMaster] getHeight] / $units]
        
        puts "$master_name: $width $height"
        incr sum_of_cell_widths $width
    }

    puts "The sum of cell widths for $side: $sum_of_cell_widths"
    
    # Get the available space for the side
    set side_width 0
    if {[lsearch -exact $horizontal_sides $side] >= 0} {
        set horizontal_side_width [expr ($DIE_WIDTH - $::env(PAD_EDGE_SPACING) * 2 - $pad_corner_site_width * 2)]
        puts "horizontal_side_width: $horizontal_side_width"
        set side_width $horizontal_side_width
    }
    if {[lsearch -exact $vertical_sides $side] >= 0} {
        set vertical_side_width [expr ($DIE_HEIGHT - $::env(PAD_EDGE_SPACING) * 2 - $pad_corner_site_height * 2)]
        puts "vertical_side_width: $vertical_side_width"
        set side_width $vertical_side_width
    }
    
    if {$sum_of_cell_widths > $side_width} {
        puts "\[Error\] Sum of cell widths for $side is larger than the width of this side."
        exit 1
    }

    set space_for_fill [expr $side_width - $sum_of_cell_widths]
    puts "space_for_fill: $space_for_fill"

    set space_between_pads [expr $space_for_fill / ([llength $::env($side)] + 1)]
    puts "space_between_pads: $space_between_pads"

    # Round to PAD_SPACING_MULTIPLE
    set space_between_pads_multiple [round_um_nm [expr floor($space_between_pads / $::env(PAD_SPACING_MULTIPLE)) * $::env(PAD_SPACING_MULTIPLE)]]
    puts "space_between_pads_multiple: $space_between_pads_multiple"

    # The spacing for the pads on the side (the remaining space)
    set space_side [round_um_nm [expr ($space_for_fill - $space_between_pads_multiple * ([llength $::env($side)] - 1)) / 2]]
    
    if { $space_side != [round_um_nm [expr floor($space_side / $pad_site_width) * $pad_site_width]] } {
        puts "\[Error\] The remaining area for the pads on the side ($space_side) is not divisible by the minimum site width (minimum filler: $pad_site_width)."
        exit 1
    }
    
    # Get the start position for each side
    set cur_pos 0.0
    if {[lsearch -exact $horizontal_sides $side] >= 0} {
        set cur_pos [expr $cur_pos + $space_side + $::env(PAD_EDGE_SPACING) + $pad_corner_site_width]
    }
    if {[lsearch -exact $vertical_sides $side] >= 0} {
        set cur_pos [expr $cur_pos + $space_side + $::env(PAD_EDGE_SPACING) + $pad_corner_site_height]
    }
    
    # For all instances
    foreach inst_name $::env($side) {
        if { [set inst [$block findInst $inst_name]] == "NULL" } {
            puts stderr "\[ERROR\] No instance $inst_name found."
            exit 1
        }
        set master_name [[$inst getMaster] getName]
        
        # Convert to micrometer
        set width  [expr [[$inst getMaster] getWidth] / $units]
        set height [expr [[$inst getMaster] getHeight] / $units]
        
        # Place the pads        
        place_pad -row [dict get $row_names $side] -location $cur_pos $inst_name -master $master_name
        
        # Increment current position
        set cur_pos [expr $cur_pos + $space_between_pads_multiple + $width]
    }
}

puts "\[INFO\] Placing corner cells…"

# Place corner cells
place_corners $::env(PAD_CORNER)

# --- project change: AVDD rail break (the only change to this file) ---
# Every gf180mcu_ocd_io cell carries the DVDD, DVSS, VDD and VSS rails on
# Metal5 edge to edge, so the re-typed avdd_pad (a gf180mcu_ocd_io__vdd
# whose VDD pin is AVDD) would abut its neighbours' VDD rail and short
# AVDD to the core VDD (measured: connect_by_abutment stops with
# PAD-0002 "IO_FILL_IO_NORTH_1_520/VDD (AVDD) and ..._530/VDD (VDD) are
# touching"). One gf180mcu_ocd_io__brk5 on each side of avdd_pad, placed
# before the fillers, breaks DVDD, DVSS and VDD and keeps VSS through
# (brk5 has only a VSS pin; AVSS is common with VSS by design). The
# pads themselves stay where the template puts them; the break cells
# take 5 um of the filler gap on each side.
set ws_avdd [$block findInst avdd_pad]
if { $ws_avdd ne "NULL" } {
    set ws_brk [[ord::get_db] findMaster gf180mcu_ocd_io__brk5]
    if { $ws_brk eq "NULL" } {
        puts stderr "\[ERROR\] gf180mcu_ocd_io__brk5 not found"
        exit 1
    }
    set ws_bb [$ws_avdd getBBox]
    set ws_w [expr {double([$ws_brk getWidth]) / $units}]
    foreach {ws_name ws_x} [list avdd_brk_w [expr {double([$ws_bb xMin]) / $units - $ws_w}] \
                                 avdd_brk_e [expr {double([$ws_bb xMax]) / $units}]] {
        odb::dbInst_create $block $ws_brk $ws_name
        place_pad -row IO_NORTH -location [round_um_nm $ws_x] $ws_name \
            -master gf180mcu_ocd_io__brk5
        set ws_q [[$block findInst $ws_name] getBBox]
        if { [$ws_q xMax] != [$ws_bb xMin] && [$ws_q xMin] != [$ws_bb xMax] } {
            puts stderr "\[ERROR\] $ws_name does not abut avdd_pad"
            exit 1
        }
        puts "\[INFO\] ws: AVDD rail break $ws_name at x [expr {double([$ws_q xMin]) / $units}]"
    }
}
# --- end of the project change ---

puts "\[INFO\] Placing filler cells…"

# Place filler cells
if {!$::env(PAD_TRIM_ROWS) || ($::env(PAD_NORTH) ne "")} { place_io_fill -row IO_NORTH {*}$::env(PAD_FILLERS) }
if {!$::env(PAD_TRIM_ROWS) || ($::env(PAD_SOUTH) ne "")} { place_io_fill -row IO_SOUTH {*}$::env(PAD_FILLERS) }
if {!$::env(PAD_TRIM_ROWS) || ($::env(PAD_WEST) ne "")} { place_io_fill -row IO_WEST {*}$::env(PAD_FILLERS) }
if {!$::env(PAD_TRIM_ROWS) || ($::env(PAD_EAST) ne "")} { place_io_fill -row IO_EAST {*}$::env(PAD_FILLERS) }

puts "\[INFO\] Deleting corner cells (if required)…"

# Delete corner cells if required
if {$::env(PAD_TRIM_ROWS) && ($::env(PAD_NORTH) eq "") && ($::env(PAD_WEST) eq "")} { odb::dbInst_destroy [$block findInst IO_CORNER_NORTH_WEST_INST] }
if {$::env(PAD_TRIM_ROWS) && ($::env(PAD_NORTH) eq "") && ($::env(PAD_EAST) eq "")} { odb::dbInst_destroy [$block findInst IO_CORNER_NORTH_EAST_INST] }
if {$::env(PAD_TRIM_ROWS) && ($::env(PAD_SOUTH) eq "") && ($::env(PAD_WEST) eq "")} { odb::dbInst_destroy [$block findInst IO_CORNER_SOUTH_WEST_INST] }
if {$::env(PAD_TRIM_ROWS) && ($::env(PAD_SOUTH) eq "") && ($::env(PAD_EAST) eq "")} { odb::dbInst_destroy [$block findInst IO_CORNER_SOUTH_EAST_INST] }

puts "\[INFO\] Connecting ring signals…"

# Connect the ring signals
connect_by_abutment

# --- project change: inside the two break cells, avdd_pad's DVDD and
# DVSS rail pieces touch nothing (the vdd cell has no device on them).
# Give them their own nets, so the netlist says what the layout is.
if { $ws_avdd ne "NULL" } {
    foreach {ws_t ws_n ws_sig} {DVDD AVDD_PAD_DVDD POWER DVSS AVDD_PAD_DVSS GROUND} {
        set ws_it [$ws_avdd findITerm $ws_t]
        set ws_net [odb::dbNet_create $block $ws_n]
        $ws_net setSpecial
        $ws_net setSigType $ws_sig
        $ws_it disconnect
        $ws_it connect $ws_net
    }
}
# --- end of the project change ---

# Place bondpads (if needed)
if { [info exists ::env(PAD_BONDPAD_NAME)] } {
    puts "\[INFO\] Placing bondpads…"
    
    foreach side $sides {
        foreach inst_name $::env($side) {
            if { [set inst [$block findInst $inst_name]] == "NULL" } {
                puts stderr "\[ERROR\] No instance $inst_name found."
                exit 1
            }
            set master_name [[$inst getMaster] getName]

            dict for {master_regex offset} $::env(PAD_BONDPAD_OFFSETS) {
                set offset_x [lindex $offset 0]
                set offset_y [lindex $offset 1]
                
                if {[regexp $master_regex $master_name match]} {
                    puts "\[INFO\] Placing bondpad $::env(PAD_BONDPAD_NAME) for $inst_name of type $master_name at offset ($offset_x, $offset_y)…"
                    place_bondpad -bond $::env(PAD_BONDPAD_NAME) $inst_name -offset [list $offset_x $offset_y]
                }
            }
        }
    }
}

# Place io terminals (if needed)
if { [info exists ::env(PAD_PLACE_IO_TERMINALS)] } {
    puts "\[INFO\] Placing I/O terminals…"
    
    foreach side $sides {
        foreach inst_name $::env($side) {
            if { [set inst [$block findInst $inst_name]] == "NULL" } {
                puts stderr "\[ERROR\] No instance $inst_name found."
                exit 1
            }
            set master_name [[$inst getMaster] getName]
    
            # Try to find the master in PAD_PLACE_IO_TERMINALS
            foreach master_pin $::env(PAD_PLACE_IO_TERMINALS) {
            
                # Split the master name and the pin name
                set parts [split $master_pin /]
                set check_master_name [lindex $parts 0]
                set pin_name [lindex $parts 1]
                
                # Found a match, place the terminal
                if {$master_name == $check_master_name} {
                    place_io_terminals $inst_name/$pin_name
                    break
                }
            }
        }
    }
}

# Remove io rows to avoid causing confusion with the other tools
puts "\[INFO\] Removing I/O rows…"
remove_io_rows

