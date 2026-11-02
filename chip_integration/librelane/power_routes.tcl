# The analog macro's four supply straps, drawn after pdngen (pdn_cfg.tcl
# wraps pdngen to source this file on the finished grid).
#
#   avdd  avdd_pad (template bidir[45], VDD pin = AVDD) -> macro avdd pin
#         pad Metal2 fingers -> 10 um Metal2 drop -> Via2/Via3/Via4 stack
#         above the core ring -> Metal5 east -> Via4 -> Metal4 down onto
#         the pin. Never touches the core ring or the VDD grid: it crosses
#         the ring's Metal3 side and the core Metal5 straps without vias,
#         in a Metal4 column the core grid is kept out of (PDN_OBSTRUCTIONS).
#   avss  avss_pad (template bidir[44]) -> macro avss pin
#         pad Metal2 fingers -> Metal2 drop -> Via2 -> Metal3 east above
#         the ring -> Via3 -> Metal4 down onto the pin. AVSS is VSS (the
#         pad ring's VSS rail is continuous, brk5 included, and the core
#         ring's connect_to_pads lands on this pad too); the strap is its
#         own return path from the pad to the macro.
#   dvss  macro dvss pin -> Metal4 up to the first core VSS Metal5 strap
#         above the macro -> Via4.
#   dvdd  macro dvdd pin -> Metal4 up to the first core VDD Metal5 strap
#         above the macro -> Via4.
#
# All straps are 10 um wide, the width of the macro's supply pins. It stops
# the step when a pin, a pad or a Metal5 strap is not where expected.

set pr_block [ord::get_db_block]
set pr_tech [[ord::get_db] getTech]
foreach l {Metal2 Metal3 Metal4 Metal5} { set pr_l($l) [$pr_tech findLayer $l] }
foreach v {Via2 Via3 Via4} {
    set pr_v($v) [$pr_tech findVia ${v}_4X4H_HH_DEFAULT]
    if { $pr_v($v) eq "NULL" } { error "power_routes: no ${v}_4X4H_HH_DEFAULT in the tech" }
}

#- 4x4-cut via blocks tiled over a rectangle (um); block pitch 2.48 keeps
#- 0.36 um between the blocks' cuts, the large-array via spacing
proc pr_vias {sw via x0 y0 x1 y1} {
    set p 2.48
    set m 1.3
    set nx [expr {max(1, int(floor(($x1 - $x0 - 2 * $m) / $p)) + 1)}]
    set ny [expr {max(1, int(floor(($y1 - $y0 - 2 * $m) / $p)) + 1)}]
    set cx [expr {($x0 + $x1) / 2.0 - ($nx - 1) * $p / 2.0}]
    set cy [expr {($y0 + $y1) / 2.0 - ($ny - 1) * $p / 2.0}]
    for {set i 0} {$i < $nx} {incr i} {
        for {set j 0} {$j < $ny} {incr j} {
            ar_via $sw $via [expr {$cx + $i * $p}] [expr {$cy + $j * $p}]
        }
    }
    return [expr {$nx * $ny}]
}

proc pr_rects {iterm layer} {
    set out {}
    foreach pair [$iterm getGeometries] {
        lassign $pair l r
        if { [$l getName] eq $layer } {
            lappend out [list [ar_f [$r xMin]] [ar_f [$r yMin]] [ar_f [$r xMax]] [ar_f [$r yMax]]]
        }
    }
    return $out
}

proc pr_bbox {rects} {
    set b {1e9 1e9 -1e9 -1e9}
    foreach r $rects {
        set b [list [expr {min([lindex $b 0], [lindex $r 0])}] [expr {min([lindex $b 1], [lindex $r 1])}] \
                    [expr {max([lindex $b 2], [lindex $r 2])}] [expr {max([lindex $b 3], [lindex $r 3])}]]
    }
    return $b
}

#- the lowest Metal5 shape of `net` above y, covering x0..x1 (um)
proc pr_m5_above {net y x0 x1} {
    set best {}
    foreach sw [$net getSWires] {
        foreach s [$sw getWires] {
            if { [$s isVia] || [[$s getTechLayer] getName] ne "Metal5" } { continue }
            set b [list [ar_f [$s xMin]] [ar_f [$s yMin]] [ar_f [$s xMax]] [ar_f [$s yMax]]]
            if { [lindex $b 1] < $y || [lindex $b 0] > $x0 || [lindex $b 2] < $x1 } { continue }
            if { [lindex $b 3] - [lindex $b 1] > 20 } { continue }
            if { $best eq {} || [lindex $b 1] < [lindex $best 1] } { set best $b }
        }
    }
    return $best
}

set pr_macro {}
set pr_avdd_pad [$pr_block findInst avdd_pad]
set pr_avss_pad [$pr_block findInst avss_pad]
set pr_breaks 0
foreach i [$pr_block getInsts] {
    if { [[$i getMaster] getName] eq "wsa_analog_top" } { set pr_macro $i }
    if { [[$i getMaster] getName] eq "gf180mcu_ocd_io__brk5" } { incr pr_breaks }
}
if { $pr_macro eq {} || $pr_avdd_pad eq "NULL" || $pr_avss_pad eq "NULL" } {
    error "power_routes: analog macro or AVDD pads missing"
}
puts "ws_avdd_rail_breaks = $pr_breaks"

set pr_net(VDD) [$pr_block findNet VDD]
set pr_net(VSS) [$pr_block findNet VSS]
set pr_net(AVDD) [$pr_block findNet AVDD]
if { $pr_net(AVDD) eq "NULL" } { error "power_routes: no AVDD net" }

#- the macro's supply pins on their nets (Odb.SetPowerConnections already
#- did this from chip_core.sv; check, and connect if not)
set pr_pins {dvdd VDD dvss VSS avdd AVDD avss VSS}
foreach {p n} $pr_pins {
    set it [$pr_macro findITerm $p]
    if { $it eq "NULL" } { error "power_routes: macro pin $p missing" }
    if { [$it getNet] eq "NULL" } { $it connect $pr_net($n) }
    if { [[$it getNet] getName] ne $n } {
        error "power_routes: macro pin $p is on [[$it getNet] getName], not $n"
    }
    set pr_pin($p) [pr_bbox [pr_rects $it Metal4]]
}
set it [$pr_avdd_pad findITerm VDD]
if { [$it getNet] eq "NULL" || [[$it getNet] getName] ne "AVDD" } {
    error "power_routes: avdd_pad VDD is not on AVDD"
}

set pr_n 0
#- dvss, dvdd: up to the first core strap of their net above the macro
foreach {p n} {dvss VSS dvdd VDD} {
    lassign $pr_pin($p) x0 y0 x1 y1
    set m5 [pr_m5_above $pr_net($n) $y1 $x0 $x1]
    if { $m5 eq {} } { error "power_routes: no $n Metal5 strap above the $p pin" }
    set sw [odb::dbSWire_create $pr_net($n) ROUTED]
    ar_box $sw $pr_l(Metal4) $x0 [expr {$y1 - 4.0}] $x1 [lindex $m5 3]
    set k [pr_vias $sw $pr_v(Via4) $x0 [lindex $m5 1] $x1 [lindex $m5 3]]
    puts "\[INFO\] ws: $p strap Metal4 x [format %.2f $x0]-[format %.2f $x1] up to $n Metal5 at y [lindex $m5 1], $k Via4 blocks"
    incr pr_n
}

#- avdd, avss from their pads. The core ring (VDD inside, VSS outside,
#- 25 um each) fills all but 12 um between the core and the north pads,
#- so the straps drop on Metal2 under both ring sides and turn east
#- inside the core, in the band between the ring and the last core Metal5
#- strap pair that FP_OBSTRUCTIONS keeps free of rows (um)
set core_top [ar_f [[$pr_block getCoreArea] yMax]]
foreach {p padinst padpin net ylo yhi topl} [list \
        avdd $pr_avdd_pad VDD  AVDD [expr {$core_top - 30.0}] [expr {$core_top - 20.0}] Metal5 \
        avss $pr_avss_pad VSS  VSS  [expr {$core_top - 15.0}] [expr {$core_top - 5.0}]  Metal3] {
    set fingers [pr_rects [$padinst findITerm $padpin] Metal2]
    if { $fingers eq {} } { error "power_routes: $p pad has no Metal2 pin" }
    lassign [pr_bbox $fingers] fx0 fy0 fx1 fy1
    #- north pads face south: the fingers' lower edge is the pad edge
    set edge $fy0
    if { $yhi > $edge - 3.0 } { error "power_routes: no room between ring and $p pad" }
    set xc [expr {round(($fx0 + $fx1) / 2.0)}]
    set xa [expr {$xc - 5.0}]
    set xb [expr {$xc + 5.0}]
    lassign $pr_pin($p) px0 py0 px1 py1
    set sw [odb::dbSWire_create $pr_net($net) ROUTED]
    #- onto the fingers: a wide Metal2 that stays 0.7 um below the pad's
    #- inner Metal2, plus each finger's own column, never past the finger
    #- (the vss cell's fingers are 2.48 um, the vdd cell's 4.66 um; a
    #- column past a finger overlaps the pad's Metal2 obstruction, which
    #- Magic's extraction reports as an illegal overlap)
    ar_box $sw $pr_l(Metal2) $xa $ylo $xb [expr {$edge + 0.9}]
    foreach f $fingers {
        set a [expr {max($xa, [lindex $f 0])}]
        set b [expr {min($xb, [lindex $f 2])}]
        if { $b - $a >= 0.5 } { ar_box $sw $pr_l(Metal2) $a $edge $b [lindex $f 3] }
    }
    set k [pr_vias $sw $pr_v(Via2) $xa $ylo $xb $yhi]
    if { $topl eq "Metal5" } {
        ar_box $sw $pr_l(Metal3) $xa $ylo $xb $yhi
        incr k [pr_vias $sw $pr_v(Via3) $xa $ylo $xb $yhi]
        ar_box $sw $pr_l(Metal4) $xa $ylo $xb $yhi
        incr k [pr_vias $sw $pr_v(Via4) $xa $ylo $xb $yhi]
        ar_box $sw $pr_l(Metal5) $xa $ylo $px1 $yhi
        incr k [pr_vias $sw $pr_v(Via4) $px0 $ylo $px1 $yhi]
    } else {
        ar_box $sw $pr_l(Metal3) $xa $ylo $px1 $yhi
        incr k [pr_vias $sw $pr_v(Via3) $px0 $ylo $px1 $yhi]
    }
    ar_box $sw $pr_l(Metal4) $px0 [expr {$py1 - 4.0}] $px1 $yhi
    puts "\[INFO\] ws: $p strap from pad x [format %.1f $xa]-[format %.1f $xb] ($topl at y [format %.1f $ylo]) down Metal4 x [format %.2f $px0]-[format %.2f $px1] onto the pin, $k via blocks"
    incr pr_n
}
puts "ws_supply_straps = $pr_n"
