# Timing constraints for the digital-on-top chip. The shape follows the
# template's librelane/chip_top.sdc; the clocks are the digital top's
# (digital/asic_digital_top/physical/physical.sdc) moved to where they
# enter the core on this chip.
current_design $::env(DESIGN_NAME)
set_units -time ns

# Conversion clock, from the clk pad's core-side output.
create_clock -name conversion_clk -period $::env(CLOCK_PERIOD) \
    [get_pins {clk_pad/Y}]

# The comparator edge clocks the Gray capture registers
# (wilkinson_gray_counter, ADR 0003). It has two sources, selected by
# test_mode: the comparator macro's output and the ext_compare pad. They
# never run together, and neither is related to the conversion clock.
# Synchronous capture (2026-10-09): the comparator output and the
# ext_compare pad are latched with the conversion clock inside chip_core
# (stand-in for the latch in the analog cell), so they are plain data
# inputs; no comparator clocks.
set_false_path -from [get_pins {i_chip_core.u_cmp/dout}]

set conv [get_clocks conversion_clk]
set input_delay_value [expr $::env(CLOCK_PERIOD) * $::env(IO_DELAY_CONSTRAINT) / 100]
set output_delay_value [expr $::env(CLOCK_PERIOD) * $::env(IO_DELAY_CONSTRAINT) / 100]
puts "\[INFO] Setting output delay to: $output_delay_value"
puts "\[INFO] Setting input delay to: $input_delay_value"

set_max_fanout $::env(MAX_FANOUT_CONSTRAINT) [current_design]
if { [info exists ::env(MAX_TRANSITION_CONSTRAINT)] } {
    set_max_transition $::env(MAX_TRANSITION_CONSTRAINT) [current_design]
}
if { [info exists ::env(MAX_CAPACITANCE_CONSTRAINT)] } {
    set_max_capacitance $::env(MAX_CAPACITANCE_CONSTRAINT) [current_design]
}

# Reset is asynchronous.
set_false_path -from [get_ports {rst_n_PAD}]

# start, shift_en, test_mode are conversion-clock inputs. input_PAD[3]
# is ext_compare, a clock source, and gets no input delay.
set clk_core_input_ports [get_ports {input_PAD[0] input_PAD[1] input_PAD[2] input_PAD[3]}]
set_input_delay -min 0 -clock $conv $clk_core_input_ports
set_input_delay -max $input_delay_value -clock $conv $clk_core_input_ports

# Outputs, all on bidirectional pads
set clk_core_output_ports [get_ports {bidir_PAD[*]}]
set_output_delay $output_delay_value -clock $conv $clk_core_output_ports

# Output load
set cap_load [expr $::env(OUTPUT_CAP_LOAD) / 1000.0]
puts "\[INFO] Setting load to: $cap_load"
set_load $cap_load [all_outputs]

puts "\[INFO] Setting clock uncertainty to: $::env(CLOCK_UNCERTAINTY_CONSTRAINT)"
set_clock_uncertainty $::env(CLOCK_UNCERTAINTY_CONSTRAINT) [all_clocks]

puts "\[INFO] Setting clock transition to: $::env(CLOCK_TRANSITION_CONSTRAINT)"
set_clock_transition $::env(CLOCK_TRANSITION_CONSTRAINT) [all_clocks]

puts "\[INFO] Setting timing derate to: $::env(TIME_DERATING_CONSTRAINT)%"
set_timing_derate -early [expr 1-[expr $::env(TIME_DERATING_CONSTRAINT) / 100]]
set_timing_derate -late [expr 1+[expr $::env(TIME_DERATING_CONSTRAINT) / 100]]

if { [info exists ::env(OPENLANE_SDC_IDEAL_CLOCKS)] && $::env(OPENLANE_SDC_IDEAL_CLOCKS) } {
    unset_propagated_clock [all_clocks]
} else {
    set_propagated_clock [all_clocks]
}
