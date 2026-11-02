# The four west analog pad wires, drawn as fixed special wiring.
#
# Sourced by pdn_cfg.tcl, before pdngen: OpenROAD.GeneratePDN is the
# first step after OpenROAD.PadRing that runs a script of this project,
# and it runs before placement and routing, which then treat these wires
# as obstacles. Why they are drawn and not routed: ADR 0009 item 4 (the
# routers skip the special nets PadRing makes of analog pad terminals,
# and un-specialised they crashed detailed routing in the 0p5x1 chip).
# Drawn wires are also what an analog net wants: short, 1.2 um wide, no
# buffers, no router-inserted diodes.
#
#   pad                 cell      pad pin          macro pin (Metal3, west edge)
#   analog3_pad  VIN    asig_5p0  ASIG5V fingers   vin
#   analog[2]    EXT_RAMP bi_a    ANA finger       ext_ramp
#   analog[1]    AMON   bi_a      ANA finger       amon
#   analog[0]    CMP_OUT bi_a     ANA finger       cmp_out
#
# bi_a's ANA is not in the synthesised netlist (its liberty lacks the pin,
# chip_top.sv): this script connects ANA to the net of the macro pin it
# feeds, then marks every analog net special so no router touches it.
#
# Each wire: Metal2 over the pad's core-side finger, a Metal2 landing just
# outside the pad edge, Via2, Metal3 east at the finger's height to the
# net's own jog column, Via2, Metal2 north/south to the macro pin's
# height, Via2, Metal3 east onto the macro pin (1.5 um into it). A net
# whose finger is within 2 um of its pin's height skips the jog (VIN).
# Jog columns are at x = 476, 480, 484 um, inside the core strip west of
# the macros that FP_OBSTRUCTIONS keeps free of rows; the higher the pad,
# the further east its column, so no wire crosses another.
#
# It stops the step rather than draw anything else when an assumption
# fails (pads not on the west edge, a pin missing, no room).

set ar_block [ord::get_db_block]
set ar_tech [[ord::get_db] getTech]
set ar_m2 [$ar_tech findLayer Metal2]
set ar_m3 [$ar_tech findLayer Metal3]
set ar_v2 [$ar_tech findVia Via2_2X2_0_60_10_60_H_H]
if { $ar_v2 eq "NULL" } { error "analog_routes: no Via2_2X2_0_60_10_60_H_H in the tech" }

#- LibreLane sources the PDN script inside a proc, so helpers read the
#- database unit themselves
proc ar_um {v} {
    set dbu [[ord::get_db_block] getDbUnitsPerMicron]
    set g [[[ord::get_db] getTech] getManufacturingGrid]
    if { $g <= 0 } { set g 1 }
    return [expr {int(round($v * $dbu / double($g))) * $g}]
}
proc ar_f {v} {
    return [format %.3f [expr {$v / double([[ord::get_db_block] getDbUnitsPerMicron])}]]
}
proc ar_box {sw layer x0 y0 x1 y1} {
    odb::dbSBox_create $sw $layer [ar_um $x0] [ar_um $y0] [ar_um $x1] [ar_um $y1] STRIPE
}
proc ar_via {sw via x y} {
    odb::dbSBox_create $sw $via [ar_um $x] [ar_um $y] STRIPE
}

set ar_macro {}
foreach i [$ar_block getInsts] {
    if { [[$i getMaster] getName] eq "wsa_analog_top" } { set ar_macro $i }
}
if { $ar_macro eq {} } { error "analog_routes: no wsa_analog_top instance" }
set ar_dbu [$ar_block getDbUnitsPerMicron]
set ar_core [$ar_block getCoreArea]

#- pad instance -> macro pin, and the jog column (um)
set ar_plan {
    asig  3 vin      0
    bi_a  2 ext_ramp 476.0
    bi_a  1 amon     480.0
    bi_a  0 cmp_out  484.0
}
set ar_n 0
foreach {kind idx pinname xj} $ar_plan {
    #- the pad: names carry escaped brackets, so match by master and index
    set pad {}
    foreach i [$ar_block getInsts] {
        set m [[$i getMaster] getName]
        if { $kind eq "asig" && $m eq "gf180mcu_ocd_io__asig_5p0" } { set pad $i }
        if { $kind eq "bi_a" && $m eq "gf180mcu_ocd_io__bi_a" &&
             [regexp "analog\\\\?\\\[$idx\\\\?\\\]" [$i getName]] } { set pad $i }
    }
    if { $pad eq {} } { error "analog_routes: no $kind pad for analog\[$idx\]" }
    set padterm [expr {$kind eq "asig" ? "ASIG5V" : "ANA"}]
    set pit [$pad findITerm $padterm]
    set mit [$ar_macro findITerm $pinname]
    if { $pit eq "NULL" || $mit eq "NULL" } { error "analog_routes: $padterm or $pinname missing" }

    #- the net: the pad's (VIN: the bond-pad net) or the macro pin's
    set net [$pit getNet]
    if { $net eq "NULL" } { set net [$mit getNet] }
    if { $net eq "NULL" } { set net [odb::dbNet_create $ar_block "ana_$pinname"] }
    if { [$pit getNet] eq "NULL" } { $pit connect $net }
    if { [$mit getNet] eq "NULL" } { $mit connect $net }
    if { [$pit getNet] ne $net || [$mit getNet] ne $net } {
        error "analog_routes: $padterm and $pinname are on different nets"
    }
    $net setSpecial
    $net setSigType SIGNAL

    #- geometry, um
    set fingers {}
    foreach pair [$pit getGeometries] {
        lassign $pair layer r
        if { [$layer getName] eq "Metal2" } {
            lappend fingers [list [ar_f [$r xMin]] [ar_f [$r yMin]] [ar_f [$r xMax]] [ar_f [$r yMax]]]
        }
    }
    set pin {}
    foreach pair [$mit getGeometries] {
        lassign $pair layer r
        if { [$layer getName] eq "Metal3" } {
            set pin [list [ar_f [$r xMin]] [ar_f [$r yMin]] [ar_f [$r xMax]] [ar_f [$r yMax]]]
        }
    }
    if { $fingers eq {} || $pin eq {} } { error "analog_routes: no finger or pin shape for $pinname" }
    lassign $pin px0 py0 px1 py1
    set yp [expr {($py0 + $py1) / 2.0}]
    #- the finger nearest the pin's height
    set best {}
    foreach f $fingers {
        set yc [expr {([lindex $f 1] + [lindex $f 3]) / 2.0}]
        if { $best eq {} || abs($yc - $yp) < abs([lindex $best 4] - $yp) } {
            set best [concat $f $yc]
        }
    }
    lassign $best fx0 fy0 fx1 fy1 yf
    if { $fx1 > [ar_f [$ar_core xMin]] - 30 } {
        error "analog_routes: $pinname pad is not on the west edge"
    }
    if { $px0 < [ar_f [$ar_core xMin]] } { error "analog_routes: $pinname pin outside the core" }
    set xe [expr {round($fx1 * 100) / 100.0}]

    set sw [odb::dbSWire_create $net ROUTED]
    #- Metal2 over the finger, then a 1.2 um landing outside the pad
    ar_box $sw $ar_m2 [expr {$xe - 4.0}] $fy0 [expr {$xe + 0.6}] $fy1
    set xv [expr {$xe + 1.3}]
    if { abs($yp - $yf) < 2.0 } {
        #- no jog: the landing spans finger and pin heights
        ar_box $sw $ar_m2 [expr {$xe + 0.3}] [expr {min($yf, $yp) - 0.6}] \
            [expr {$xe + 2.3}] [expr {max($yf, $yp) + 0.6}]
        ar_via $sw $ar_v2 $xv $yp
        ar_box $sw $ar_m3 [expr {$xv - 0.5}] [expr {$yp - 0.6}] [expr {$px0 + 1.5}] [expr {$yp + 0.6}]
        puts "\[INFO\] ws: analog route [$net getName] ($pinname): straight at y [format %.2f $yp]"
    } else {
        if { $xj - 2.0 < [ar_f [$ar_core xMin]] || $xj + 2.0 > $px0 } {
            error "analog_routes: jog column $xj of $pinname is not between core edge and macro"
        }
        ar_box $sw $ar_m2 [expr {$xe + 0.3}] [expr {$yf - 0.6}] [expr {$xe + 2.3}] [expr {$yf + 0.6}]
        ar_via $sw $ar_v2 $xv $yf
        ar_box $sw $ar_m3 [expr {$xv - 0.5}] [expr {$yf - 0.6}] [expr {$xj + 0.6}] [expr {$yf + 0.6}]
        ar_via $sw $ar_v2 $xj $yf
        ar_box $sw $ar_m2 [expr {$xj - 0.6}] [expr {min($yf, $yp) - 0.6}] \
            [expr {$xj + 0.6}] [expr {max($yf, $yp) + 0.6}]
        ar_via $sw $ar_v2 $xj $yp
        ar_box $sw $ar_m3 [expr {$xj - 0.6}] [expr {$yp - 0.6}] [expr {$px0 + 1.5}] [expr {$yp + 0.6}]
        puts "\[INFO\] ws: analog route [$net getName] ($pinname): pad y [format %.2f $yf] -> jog x $xj -> pin y [format %.2f $yp]"
    }
    incr ar_n
}
puts "ws_analog_routes = $ar_n"
