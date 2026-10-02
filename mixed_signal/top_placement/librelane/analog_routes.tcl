# Pad-to-macro analog wiring, drawn as fixed special routes.
#
# Sourced by pdn_cfg.tcl: OpenROAD.GeneratePDN is the first step after
# OpenROAD.PadRing that runs a script of this project's, and it runs
# before placement and routing, which then treat these wires as
# obstacles.
#
# Why not let the router do it. PadRing's place_io_terminals marks every
# asig_5p0/ASIG5V net special, with its top-level terminal on the Metal5
# bond pad, and the routers skip special nets: the first full run had
# the five analog nets unrouted (Netgen: 5 extra layout nets). Clearing
# the flag made detailed routing abort inside the flow three runs out of
# three (frAccessPoint index out of range after "Post process initialize
# RPin region query"), with the terminal on the bond pad or moved onto a
# Metal2 finger, on 22 threads or 1 -- while the same step re-run on its
# own from the saved config and state routed all five with 0 DRC errors.
# The analog nets therefore stay special, as the template leaves them,
# and are drawn here: short, wide, no buffers, no router-inserted diodes,
# which is also how an analog net should be wired.
#
# Each net: pad Metal2 finger -> Metal2 south past the core ring (Metal3
# on this edge) -> Via2 -> Metal3 jog at its own height between the
# macro tops and the core edge -> Via2 -> Metal2 south to the macro edge
# -> Via2 onto the macro's Metal3 pin stub. Jogs are the only Metal3 and
# each net has its own height, so no two nets' same-layer shapes meet.
#
# Assumes what slot_0p5x1.yaml and macros.yaml give: analog pads on the
# north edge, the macros' signal pins on their north edges below them.
# It stops the step rather than draw anything else.

set ar_block [ord::get_db_block]
set ar_tech [[ord::get_db] getTech]
set ar_dbu [$ar_block getDbUnitsPerMicron]
set ar_m2 [$ar_tech findLayer Metal2]
set ar_m3 [$ar_tech findLayer Metal3]
set ar_via [$ar_tech findVia Via2_2X2_0_60_10_60_V_H]
set ar_core [$ar_block getCoreArea]

#- LibreLane sources the PDN script inside a proc, so nothing set here
#- is global: the helper reads the database unit itself (measured: a
#- $::ar_dbu here failed the step with "no such variable")
proc ar_um {v} {
    set dbu [[ord::get_db_block] getDbUnitsPerMicron]
    return [expr {int(round($v * $dbu / 10.0)) * 10}]
}
proc ar_snap {v} { return [expr {int(round($v / 10.0)) * 10}] }

set ar_w2 [ar_um 0.6]            ;# half of a 1.2 um wire
set ar_k 0
foreach net [$ar_block getNets] {
    if { ![$net isSpecial] || [$net getSigType] != "SIGNAL" } { continue }
    set fingers {}
    set pin {}
    foreach iterm [$net getITerms] {
        set is_pad [string match "PAD*" [[[$iterm getInst] getMaster] getType]]
        foreach pair [$iterm getGeometries] {
            lassign $pair layer r
            set box [list [$r xMin] [$r yMin] [$r xMax] [$r yMax]]
            if { $is_pad && [$layer getName] == "Metal2" } {
                lappend fingers $box
            } elseif { !$is_pad && [$layer getName] == "Metal3" } {
                #- the pin shape reaching highest: the stub at the
                #- macro's north edge
                if { $pin == {} || [lindex $box 3] > [lindex $pin 3] } { set pin $box }
            }
        }
    }
    #- pad-only nets (the spare analog pad) have nothing to wire
    if { $fingers == {} || $pin == {} } { continue }

    set xp [ar_snap [expr {([lindex $pin 0] + [lindex $pin 2]) / 2}]]
    set ytop [lindex $pin 3]
    #- Which finger, and whether to jog. If the pin's x lies within a
    #- finger (with room for the 1.2 um wire), the wire drops straight
    #- down that finger's x: no jog, no jog vias. Otherwise the nearest
    #- finger at least 2 um from the pin, so the two jog Via2 arrays
    #- (1.56 um of Metal2 each) cannot overlap -- measured: a finger
    #- 0.4 um from the pin (analog_PAD[3]) left two overlapping arrays,
    #- 4 x V2.1 + 4 x V2.2a in gf180mcu.drc and 4 Via2 XOR differences.
    set straight 0
    set best {}
    foreach f $fingers {
        if { $xp - $ar_w2 >= [lindex $f 0] && $xp + $ar_w2 <= [lindex $f 2] } {
            set straight 1
            set best [list $xp [lindex $f 1]]
            break
        }
    }
    if { !$straight } {
        foreach f $fingers {
            set c [expr {([lindex $f 0] + [lindex $f 2]) / 2}]
            if { abs($c - $xp) < [ar_um 2.0] } { continue }
            if { $best == {} || abs($c - $xp) < abs([lindex $best 0] - $xp) } {
                set best [list $c [lindex $f 1]]
            }
        }
    }
    if { $best == {} } { error "analog_routes: no usable finger for [$net getName]" }
    lassign $best xf yf
    set xf [ar_snap $xf]
    if { $yf <= [$ar_core yMax] } {
        error "analog_routes: [$net getName] pad is not on the north edge"
    }
    set yj [expr {[$ar_core yMax] - [ar_um [expr {6.0 + 5.0 * $ar_k}]]}]
    set yland [expr {$ytop - [ar_um 1.0]}]
    if { $yj - $ytop < [ar_um 3.0] } {
        error "analog_routes: no room for the jog of [$net getName]"
    }
    incr ar_k

    set sw [odb::dbSWire_create $net ROUTED]
    if { $straight } {
        #- one Metal2 drop from the finger to the pin, one via
        odb::dbSBox_create $sw $ar_m2 [expr {$xp - $ar_w2}] [expr {$yland - $ar_w2}] \
            [expr {$xp + $ar_w2}] [expr {$yf + [ar_um 1.5]}] STRIPE
        odb::dbSBox_create $sw $ar_via $xp $yland STRIPE
        puts "\[INFO] analog route [$net getName]: straight at x=[expr {$xp / double($ar_dbu)}]"
        continue
    }
    #- down from the finger (1.5 um into it) past the ring
    odb::dbSBox_create $sw $ar_m2 [expr {$xf - $ar_w2}] [expr {$yj - $ar_w2}] \
        [expr {$xf + $ar_w2}] [expr {$yf + [ar_um 1.5]}] STRIPE
    odb::dbSBox_create $sw $ar_via $xf $yj STRIPE
    #- the jog
    set xa [expr {min($xf, $xp)}]
    set xb [expr {max($xf, $xp)}]
    odb::dbSBox_create $sw $ar_m3 [expr {$xa - $ar_w2}] [expr {$yj - $ar_w2}] \
        [expr {$xb + $ar_w2}] [expr {$yj + $ar_w2}] STRIPE
    odb::dbSBox_create $sw $ar_via $xp $yj STRIPE
    #- down to the macro edge, and onto its pin 1 um inside it
    odb::dbSBox_create $sw $ar_m2 [expr {$xp - $ar_w2}] [expr {$yland - $ar_w2}] \
        [expr {$xp + $ar_w2}] [expr {$yj + $ar_w2}] STRIPE
    odb::dbSBox_create $sw $ar_via $xp $yland STRIPE
    puts "\[INFO] analog route [$net getName]: pad x=[expr {$xf / double($ar_dbu)}] ->\
          jog y=[expr {$yj / double($ar_dbu)}] -> pin x=[expr {$xp / double($ar_dbu)}]"
}
puts "\[INFO] analog routes drawn: $ar_k"
