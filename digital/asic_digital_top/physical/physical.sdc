create_clock -name conversion_clk -period 50.000 [get_ports clk]
set_false_path -from [get_ports rst_n]
# crossed[3:0] are synchronous flags from the analog cells (latched there
# with the conversion clock); ordinary data inputs.
set_input_delay 5.000 -clock conversion_clk [get_ports {start shift_en crossed[0] crossed[1] crossed[2] crossed[3]}]
set_output_delay 5.000 -clock conversion_clk \
    [get_ports {acquire ramp_connect ramp_reset serial_data data_ready conversion_busy conversion_done conversion_timeout[0] conversion_timeout[1] conversion_timeout[2] conversion_timeout[3]}]
