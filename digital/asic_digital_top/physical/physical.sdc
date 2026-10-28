create_clock -name conversion_clk -period 50.000 [get_ports clk]
set_false_path -from [get_ports rst_n]
# q[3:0] are the analog cells' latched flags (negative-edge flops on cnt_clk):
# synchronous data inputs with half a period of margin.
set_input_delay 5.000 -clock conversion_clk [get_ports {start shift_en q[0] q[1] q[2] q[3]}]
set_output_delay 5.000 -clock conversion_clk \
    [get_ports {s0[0] s0[1] s0[2] s0[3] s1[0] s1[1] s1[2] s1[3] s2[0] s2[1] s2[2] s2[3] ramp_rst serial_data data_ready conversion_busy conversion_done conversion_timeout[0] conversion_timeout[1] conversion_timeout[2] conversion_timeout[3]}]
# cnt_clk is the clock itself, forwarded to the analog macro.
set_false_path -to [get_ports cnt_clk]
