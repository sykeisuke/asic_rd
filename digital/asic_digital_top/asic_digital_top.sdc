create_clock -name conversion_clk -period 50.000 [get_ports clk]
create_clock -name comparator_event -period 50.000 [get_ports compare_high]
set_clock_groups -asynchronous \
    -group [get_clocks conversion_clk] \
    -group [get_clocks comparator_event]
set_false_path -from [get_ports rst_n]
set_input_delay 5.000 -clock conversion_clk [get_ports {start shift_en}]
set_output_delay 5.000 -clock conversion_clk \
    [get_ports {mux_select ramp_reset bus_reset serial_data data_ready conversion_busy conversion_done active_cell}]
